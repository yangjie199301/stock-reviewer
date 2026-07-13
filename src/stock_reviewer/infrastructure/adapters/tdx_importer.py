"""通达信数据导入器。

将通达信导出的 CSV/TXT 文件解析后写入 SQLite 数据库。

支持的文件格式（CSV，UTF-8/GBK 编码）：
  - 批量导出格式（推荐）：
    代码,名称,日期,开盘,最高,最低,收盘,成交量,成交额
    000001,平安银行,2026-07-01,12.34,12.56,12.20,12.45,12345678,156789000

  - 单只股票格式（来自个股 K 线导出）：
    日期,开盘,最高,最低,收盘,成交量,成交额
    2026-07-01,12.34,12.56,12.20,12.45,12345678,156789000

使用方式：
    from stock_reviewer.infrastructure.adapters.tdx_importer import TdxImporter
    importer = TdxImporter()
    result = importer.import_all()          # 扫描默认目录 data/imports/
    result = importer.import_file("path")   # 导入单个文件
"""

import csv
import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple
from stock_reviewer.core.logging import logger
from stock_reviewer.domain.entities.models import DailyQuote
from stock_reviewer.infrastructure.database.repositories.sqlite_repositories import (
    SqliteDailyQuoteRepository,
    SqliteDataMetaRepository,
)


# 通达信导出的列名映射（标准名 → DailyQuote 字段）
# 支持中英文列名
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
        self.import_dir = Path(import_dir or "data/imports")
        self.quote_repo = SqliteDailyQuoteRepository()
        self.meta_repo = SqliteDataMetaRepository()

    # ── 公共 API ──

    def import_all(self) -> dict:
        """扫描导入目录，导入所有文件。

        Returns:
            {"total_files": N, "imported": N, "skipped": N, "failed": [files]}
        """
        if not self.import_dir.exists():
            logger.warning("导入目录不存在: %s", self.import_dir)
            return {"total_files": 0, "imported": 0, "skipped": 0, "failed": []}

        files = sorted(self.import_dir.glob("*.csv")) + sorted(
            self.import_dir.glob("*.txt")
        )
        if not files:
            logger.warning("导入目录中无 CSV/TXT 文件: %s", self.import_dir)
            return {"total_files": 0, "imported": 0, "skipped": 0, "failed": []}

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
                result["failed"].append(file_path.name)

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

    # ── 内部方法 ──

    def _import_single_file(self, file_path: Path) -> int:
        """导入单个文件并写入数据库。"""
        records = self._parse_file(file_path)
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

    def _parse_file(self, file_path: Path) -> List[DailyQuote]:
        """解析文件内容为 DailyQuote 列表。"""
        # 尝试 UTF-8，失败则用 GBK
        lines = self._read_lines(file_path)
        if not lines:
            return []

        # 解析表头
        header = [h.strip().strip("\ufeff") for h in lines[0]]  # 去掉 BOM
        col_map = self._map_columns(header)
        if not col_map:
            logger.warning("无法识别文件列名: %s (%s)", file_path.name, header)
            return []

        has_code_col = "code" in col_map
        records: List[DailyQuote] = []

        for row in lines[1:]:
            try:
                record = self._row_to_daily_quote(row, col_map, has_code_col)
                if record:
                    records.append(record)
            except (ValueError, IndexError) as e:
                logger.debug("跳过无效行 %s: %s", file_path.name, e)
                continue

        return records

    def _read_lines(self, file_path: Path) -> List[List[str]]:
        """读取文件并返回 CSV 行列表。"""
        if not file_path.exists():
            logger.warning("文件不存在: %s", file_path)
            return []

        try:
            with open(file_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                return [row for row in reader if row and row[0].strip()]
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="gbk") as f:
                    reader = csv.reader(f)
                    return [row for row in reader if row and row[0].strip()]
            except Exception as e:
                logger.error("无法读取文件 %s: %s", file_path.name, e)
                return []
        except Exception as e:
            logger.error("无法读取文件 %s: %s", file_path.name, e)
            return []

    def _map_columns(self, header: List[str]) -> dict:
        """将文件列名映射为 DailyQuote 字段。

        Returns:
            {字段名: 列索引} 的映射字典，无法识别时返回空 dict。
        """
        col_map: dict = {}
        for idx, col_name in enumerate(header):
            col_lower = col_name.strip().lower()
            mapped = _COLUMN_ALIASES.get(col_name.strip()) or _COLUMN_ALIASES.get(
                col_lower
            )
            if mapped:
                col_map[mapped] = idx

        # 必须有的字段
        required = ("date", "open", "high", "low", "close", "volume", "amount")
        missing = [r for r in required if r not in col_map]
        if missing:
            logger.warning("缺少必要字段: %s", missing)
            return {}
        return col_map

    def _row_to_daily_quote(
        self, row: List[str], col_map: dict, has_code_col: bool
    ) -> Optional[DailyQuote]:
        """将一行 CSV 数据解析为 DailyQuote。"""
        try:
            code = row[col_map["code"]].strip().zfill(6) if has_code_col else ""

            raw_date = row[col_map["date"]].strip()
            parsed_date = self._parse_date(raw_date)
            if not parsed_date:
                return None

            return DailyQuote(
                code=code,
                name=row[col_map.get("name", -1)].strip() if "name" in col_map else "",
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
            logger.debug("解析行失败: %s", e)
            return None

    def _parse_date(self, raw: str) -> Optional[date]:
        """尝试多种格式解析日期。"""
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y%m%d",
            "%Y.%m.%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        logger.debug("无法解析日期: %s", raw)
        return None


def run_import(import_dir: Optional[str] = None) -> dict:
    """便捷入口：创建导入器并运行。"""
    importer = TdxImporter(import_dir)
    return importer.import_all()
