"""通达信数据导入器。

支持两种数据来源：
  1. 通达信日线数据完整包（.day 二进制格式）— 推荐
     下载地址：https://data.tdx.com.cn/vipdoc/hsjday.zip
     解压后将 hsjday/ 目录放入 data/imports/ 即可

  2. 通达信导出的 CSV/TXT 文件
     支持批量导出格式（含代码列）和单只股票格式

使用方式：
    from stock_reviewer.infrastructure.adapters.tdx_importer import TdxImporter
    importer = TdxImporter()
    result = importer.import_all()          # 扫描 data/imports/ 目录
    result = importer.import_file("path")   # 导入单个文件
"""

import csv
import struct
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from stock_reviewer.core.logging import logger

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
from stock_reviewer.domain.entities.models import DailyQuote
from stock_reviewer.infrastructure.database.repositories.sqlite_repositories import (
    SqliteDailyQuoteRepository,
    SqliteDataMetaRepository,
)

# ── .day 二进制文件格式 ──────────────────────────────────
# 每条记录 32 字节，8 个 int32 little-endian：
#   date(int)  open*100(int)  high*100(int)  low*100(int)
#   close*100(int)  amount(int)  volume(int)  reserved(int)
_DAY_RECORD_SIZE = 32
_DAY_STRUCT = struct.Struct("<iiiiiiii")  # 8 个 int32 LE

# 文件名前缀 → 交易所
_EXCHANGE_PREFIX = {"sh": "sh", "sz": "sz", "bj": "bj"}

# ── CSV 列名映射 ────────────────────────────────────────
_COLUMN_ALIASES: dict = {
    "代码": "code",
    "code": "code",
    "名称": "name",
    "name": "name",
    "date": "date",
    "日期": "date",
    "开盘": "open",
    "开盘价": "open",
    "open": "open",
    "最高": "high",
    "最高价": "high",
    "high": "high",
    "最低": "low",
    "最低价": "low",
    "low": "low",
    "收盘": "close",
    "收盘价": "close",
    "close": "close",
    "成交量": "volume",
    "volume": "volume",
    "成交额": "amount",
    "amount": "amount",
    "成交金额": "amount",
    "涨跌幅": "change_pct",
    "涨跌": "change_pct",
    "change_pct": "change_pct",
    "换手率": "turnover_rate",
    "turnover_rate": "turnover_rate",
}


class TdxImporter:
    """通达信数据导入器。"""

    def __init__(self, import_dir: Optional[str] = None):
        self.import_dir = Path(import_dir or str(_PROJECT_ROOT / "data" / "imports"))
        self.quote_repo = SqliteDailyQuoteRepository()
        self.meta_repo = SqliteDataMetaRepository()

    # ══════════════════════════════════════════════════════
    # 公共 API
    # ══════════════════════════════════════════════════════

    def import_all(self) -> dict:
        """扫描导入目录，导入所有文件。

        Returns:
            {"total_files": N, "imported": N, "skipped": N, "failed": [files]}
        """
        if not self.import_dir.exists():
            logger.warning("导入目录不存在: %s", self.import_dir)
            return {"total_files": 0, "imported": 0, "skipped": 0, "failed": []}

        # 收集所有可导入文件
        files = self._collect_files()
        if not files:
            logger.info("导入目录中无可导入文件: %s", self.import_dir)
            return {"total_files": 0, "imported": 0, "skipped": 0, "failed": []}

        logger.info("发现 %d 个可导入文件", len(files))

        result = {"total_files": len(files), "imported": 0, "skipped": 0, "failed": []}
        for file_path in files:
            try:
                imported = self._import_single_file(file_path)
                if imported > 0:
                    result["imported"] += imported
                else:
                    result["skipped"] += 1
            except Exception as e:
                logger.error("导入文件失败 %s: %s", file_path.name, e)
                result["failed"].append(str(file_path.relative_to(self.import_dir)))

        logger.info(
            "导入完成: %d 文件, %d 条记录, %d 跳过, %d 失败",
            result["total_files"],
            result["imported"],
            result["skipped"],
            len(result["failed"]),
        )
        return result

    def import_file(self, file_path: str) -> int:
        """导入单个文件。

        Args:
            file_path: 文件路径。

        Returns:
            导入的记录数。
        """
        return self._import_single_file(Path(file_path))

    # ══════════════════════════════════════════════════════
    # 文件收集
    # ══════════════════════════════════════════════════════

    def _collect_files(self) -> List[Path]:
        """递归扫描导入目录，收集所有可导入文件。"""
        # .day 文件在 hsjday/sh/lday/ 或 hsjday/sz/lday/ 等子目录下
        if (self.import_dir / "sh" / "lday").exists():
            # 直接是 vipdoc 结构
            base = self.import_dir
        elif (self.import_dir / "hsjday" / "sh" / "lday").exists():
            # 是 hsjday 压缩包解压后的结构
            base = self.import_dir / "hsjday"
        else:
            base = self.import_dir

        files: List[Path] = []

        # 扫描 .day 文件（递归）
        for pattern in ("**/*.day",):
            for f in sorted(base.glob(pattern)):
                if self._is_valid_day_file(f):
                    files.append(f)

        # 扫描 CSV/TXT 文件（仅顶层目录）
        for pattern in ("*.csv", "*.txt"):
            for f in sorted(self.import_dir.glob(pattern)):
                if f not in files:
                    files.append(f)

        return files

    def _is_valid_day_file(self, path: Path) -> bool:
        """检查文件名是否为有效的通达信日线格式。"""
        name = path.stem  # 去掉 .day 后缀
        if len(name) < 8:
            return False
        prefix = name[:2].lower()
        return prefix in _EXCHANGE_PREFIX and name[2:].isdigit()

    # ══════════════════════════════════════════════════════
    # 导入单文件
    # ══════════════════════════════════════════════════════

    def _import_single_file(self, file_path: Path) -> int:
        """导入单个文件并写入数据库。"""
        if file_path.suffix.lower() == ".day":
            records = self._parse_day_file(file_path)
        else:
            records = self._parse_csv_file(file_path)

        if not records:
            return 0

        written = self.quote_repo.batch_upsert(records)
        logger.info(
            "导入 %s: %d 条 → 写入 %d 条",
            file_path.name,
            len(records),
            written,
        )
        return written

    # ══════════════════════════════════════════════════════
    # .day 二进制解析
    # ══════════════════════════════════════════════════════

    def _parse_day_file(self, file_path: Path) -> List[DailyQuote]:
        """解析通达信 .day 日线二进制文件。"""
        code = self._extract_code_from_filename(file_path.stem)
        if not code:
            return []

        try:
            data = file_path.read_bytes()
        except OSError as e:
            logger.error("读取 .day 文件失败 %s: %s", file_path.name, e)
            return []

        records: List[DailyQuote] = []
        pos = 0
        while pos + _DAY_RECORD_SIZE <= len(data):
            try:
                raw = _DAY_STRUCT.unpack_from(data, pos)
            except struct.error as e:
                logger.warning("解析 .day 记录失败 %s @ %d: %s", file_path.name, pos, e)
                break

            date_int, open100, high100, low100, close100, amount, volume, _ = raw

            # 成交量 int32 溢出处理（指数类成交量巨大）
            if volume < 0:
                volume += 2**32

            # 校验
            if date_int < 19900101 or date_int > 21000101:
                pos += _DAY_RECORD_SIZE
                continue
            if any(v <= 0 for v in (open100, high100, low100, close100)):
                pos += _DAY_RECORD_SIZE
                continue

            try:
                parsed_date = datetime.strptime(str(date_int), "%Y%m%d").date()
            except ValueError:
                pos += _DAY_RECORD_SIZE
                continue

            records.append(
                DailyQuote(
                    code=code,
                    name="",
                    date=parsed_date,
                    open=open100 / 100.0,
                    high=high100 / 100.0,
                    low=low100 / 100.0,
                    close=close100 / 100.0,
                    volume=volume,
                    amount=float(amount),
                    change_pct=0.0,
                    turnover_rate=0.0,
                )
            )
            pos += _DAY_RECORD_SIZE

        return records

    def _extract_code_from_filename(self, stem: str) -> str:
        """从文件名提取股票代码。

        sh600001.day → 600001
        sz000001.day → 000001
        """
        prefix = stem[:2].lower()
        if prefix not in _EXCHANGE_PREFIX:
            return ""
        return stem[2:].zfill(6)

    # ══════════════════════════════════════════════════════
    # CSV 解析
    # ══════════════════════════════════════════════════════

    def _parse_csv_file(self, file_path: Path) -> List[DailyQuote]:
        """解析 CSV 文件为 DailyQuote 列表。"""
        lines = self._read_csv_lines(file_path)
        if not lines:
            return []

        header = [h.strip().strip("\ufeff") for h in lines[0]]
        col_map = self._map_csv_columns(header)
        if not col_map:
            logger.warning("无法识别 CSV 列名: %s (%s)", file_path.name, header)
            return []

        has_code_col = "code" in col_map
        records: List[DailyQuote] = []
        for row in lines[1:]:
            try:
                record = self._csv_row_to_daily_quote(row, col_map, has_code_col)
                if record:
                    records.append(record)
            except (ValueError, IndexError) as e:
                logger.debug("跳过无效行 %s: %s", file_path.name, e)
                continue

        return records

    def _read_csv_lines(self, file_path: Path) -> List[List[str]]:
        """读取 CSV 行列表，自动检测编码。"""
        if not file_path.exists():
            logger.warning("文件不存在: %s", file_path)
            return []

        for encoding in ("utf-8-sig", "gbk", "gb18030"):
            try:
                with open(file_path, encoding=encoding) as f:
                    reader = csv.reader(f)
                    return [row for row in reader if row and row[0].strip()]
            except (UnicodeDecodeError, OSError):
                continue
        logger.error("无法读取文件 %s（所有编码尝试失败）", file_path.name)
        return []

    def _map_csv_columns(self, header: List[str]) -> dict:
        """将 CSV 列名映射为 DailyQuote 字段。"""
        col_map: dict = {}
        for idx, col_name in enumerate(header):
            col_lower = col_name.strip().lower()
            mapped = _COLUMN_ALIASES.get(col_name.strip()) or _COLUMN_ALIASES.get(
                col_lower
            )
            if mapped:
                col_map[mapped] = idx

        required = ("date", "open", "high", "low", "close", "volume", "amount")
        missing = [r for r in required if r not in col_map]
        if missing:
            logger.warning("CSV 缺少必要字段: %s", missing)
            return {}
        return col_map

    def _csv_row_to_daily_quote(
        self, row: List[str], col_map: dict, has_code_col: bool
    ) -> Optional[DailyQuote]:
        """将一行 CSV 数据解析为 DailyQuote。"""
        try:
            code = row[col_map["code"]].strip().zfill(6) if has_code_col else ""

            parsed_date = self._parse_date_str(row[col_map["date"]].strip())
            if not parsed_date:
                return None

            return DailyQuote(
                code=code,
                name=row[col_map.get("name", -1)].strip()
                if "name" in col_map
                else "",
                date=parsed_date,
                open=float(row[col_map["open"]]),
                high=float(row[col_map["high"]]),
                low=float(row[col_map["low"]]),
                close=float(row[col_map["close"]]),
                volume=int(float(row[col_map["volume"]])),
                amount=float(row[col_map["amount"]]),
                change_pct=float(row[col_map.get("change_pct", -1)])
                if "change_pct" in col_map
                else 0.0,
                turnover_rate=float(row[col_map.get("turnover_rate", -1)])
                if "turnover_rate" in col_map
                else 0.0,
            )
        except (ValueError, IndexError) as e:
            logger.debug("解析 CSV 行失败: %s", e)
            return None

    def _parse_date_str(self, raw: str) -> Optional[date]:
        """尝试多种格式解析日期字符串。"""
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None


def run_import(import_dir: Optional[str] = None) -> dict:
    """便捷入口：创建导入器并运行。"""
    importer = TdxImporter(import_dir)
    return importer.import_all()
