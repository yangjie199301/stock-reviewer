"""数据质量修复脚本。

使用方式：
    python scripts/update_data_quality.py
"""
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DB_PATH = Path(__file__).parent.parent / "data" / "quant_data.db"
NAMES_CSV = Path(__file__).parent / "stock_names.csv"


def fetch_all_names(target_file: Path):
    """从多个 akshare 接口抓取全市场代码名称映射。

    数据源覆盖：
      - A 股      : stock_info_a_code_name()
      - 指数      : stock_zh_index_spot()
      - 基金/ETF  : fund_name_em()
      - 可转债    : bond_zh_cov_spot_em()
    """
    import akshare as ak

    all_names: dict[str, str] = {}

    # ── 1. A 股 ──
    try:
        df = ak.stock_info_a_code_name()
        for _, row in df.iterrows():
            code = str(row["code"]).strip().zfill(6)
            name = str(row["name"]).strip()
            if name and name != "nan":
                all_names[code] = name
        print(f"  A 股: {sum(1 for c in all_names if c[:2] in ('00','30','60','68'))} 只")
    except Exception as e:
        print(f"  A 股抓取失败: {e}")

    # ── 2. 指数（中证指数公司，覆盖 000/399/880/931 等）──
    try:
        df = ak.index_all_cni()
        for _, row in df.iterrows():
            code = str(row["指数代码"]).strip().zfill(6)
            name = str(row["指数简称"]).strip()
            if name and name != "nan" and code not in all_names:
                all_names[code] = name
        print(f"  指数: ~{sum(1 for c in all_names if c[:2] in ('00','39','88','93'))} 只")
    except Exception as e:
        print(f"  指数抓取失败: {e}")

    # ── 3. 基金/ETF（天天基金，覆盖 51/15/50/56 等）──
    try:
        df = ak.fund_name_em()
        for _, row in df.iterrows():
            code = str(row["基金代码"]).strip().zfill(6)
            name = str(row["基金简称"]).strip()
            if name and name != "nan" and code not in all_names:
                all_names[code] = name
        print(f"  基金: ~{sum(1 for c in all_names if c[:2] in ('51','15','50','56','58','52'))} 只")
    except Exception as e:
        print(f"  基金抓取失败: {e}")

    # ── 4. 全市场实时行情（含 A/B 股，覆盖 20/90 开头 B 股）──
    try:
        df = ak.stock_zh_a_spot_em()
        for _, row in df.iterrows():
            code = str(row["代码"]).strip().zfill(6)
            name = str(row["名称"]).strip()
            if name and name != "nan" and code not in all_names:
                all_names[code] = name
        print(f"  A+B 股: 总计 {sum(1 for c in all_names if c[:2] in ('00','30','60','68','20','90'))} 只")
    except Exception as e:
        print(f"  实时行情抓取失败: {e}")

    # ── 5. 北交所 ──
    try:
        df = ak.stock_info_bj_name_code()
        for _, row in df.iterrows():
            code = str(row["code"]).strip().zfill(6)
            name = str(row["name"]).strip()
            if name and name != "nan" and code not in all_names:
                all_names[code] = name
        print(f"  北交所: ~{sum(1 for c in all_names if c[:2] in ('83','87','92'))} 只")
    except Exception as e:
        # 备用接口
        try:
            df = ak.stock_bj_a_spot_em()
            for _, row in df.iterrows():
                code = str(row["代码"]).strip().zfill(6)
                name = str(row["名称"]).strip()
                if name and name != "nan" and code not in all_names:
                    all_names[code] = name
            print(f"  北交所(备用): ~{sum(1 for c in all_names if c[:2] in ('83','87','92'))} 只")
        except Exception as e2:
            print(f"  北交所抓取失败: {e}")

    # ── 6. 可转债 ──
    try:
        df = ak.bond_zh_hs_cov_spot()
        for _, row in df.iterrows():
            symbol = str(row["symbol"]).strip()
            if symbol.startswith("sh") or symbol.startswith("sz"):
                code = symbol[2:].zfill(6)
            else:
                code = str(row.get("code", "")).strip().zfill(6)
            name = str(row["name"]).strip()
            if name and name != "nan" and code not in all_names:
                all_names[code] = name
        print(f"  可转债: ~{sum(1 for c in all_names if c[:2] in ('12','11'))} 只")
    except Exception as e:
        print(f"  可转债抓取失败: {e}")

    # 写入 CSV
    with open(target_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name"])
        for code in sorted(all_names.keys()):
            writer.writerow([code, all_names[code]])
    print(f"\n全市场名称映射已保存：{target_file}（共 {len(all_names)} 只）")


def ensure_names_csv() -> bool:
    """确保股票名称映射文件存在且完整。"""
    # 检查现有文件是否来自完整的多源抓取（文件头包含完整标记）
    if NAMES_CSV.exists():
        with open(NAMES_CSV, encoding="utf-8-sig") as f:
            lines = f.readlines()
        # 如果已有 10000+ 条，认为足够完整
        if len(lines) > 8000:
            print(f"名称映射表已存在：{len(lines)-1} 条")
            return True

    print("正在从多数据源抓取全市场名称...")
    fetch_all_names(NAMES_CSV)
    return True


def update_stock_names():
    """用临时表批量更新股票名称。"""
    print("\n=== 更新股票名称 ===")
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    cur = conn.cursor()

    # 创建临时名称表并导入 CSV
    cur.execute("DROP TABLE IF EXISTS _tmp_names")
    cur.execute("CREATE TABLE _tmp_names (code TEXT PRIMARY KEY, name TEXT)")

    count = 0
    with open(NAMES_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["code"].strip().zfill(6)
            name = row.get("name", "").strip()
            if name:
                cur.execute("INSERT INTO _tmp_names VALUES (?,?)", (code, name))
                count += 1
    conn.commit()
    print(f"临时表已加载 {count} 条名称映射")

    # 更新名称
    cur.execute("""
        UPDATE daily_quotes SET name = (
            SELECT name FROM _tmp_names
            WHERE _tmp_names.code = daily_quotes.code
        )
        WHERE name='' AND code IN (SELECT code FROM _tmp_names)
    """)
    conn.commit()
    updated = cur.rowcount

    filled = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE name!=''").fetchone()[0]
    print(f"名称更新完成：共更新 {updated:,} 条，现有名称记录 {filled:,} 条")

    cur.execute("DROP TABLE IF EXISTS _tmp_names")
    conn.commit()
    conn.close()


def calc_change_pct():
    """用 SQL 窗口函数计算涨跌幅。"""
    print("\n=== 计算涨跌幅 ===")
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    cur = conn.cursor()

    # 使用可更新的 CTE + 窗口函数
    # SQLite 不支持直接 UPDATE FROM，用逐 code 方式但批量提交
    codes = cur.execute("SELECT DISTINCT code FROM daily_quotes").fetchall()
    total = len(codes)
    print(f"共 {total} 只股票")

    updated = 0
    batch_count = 0

    for idx, (code,) in enumerate(codes, 1):
        rows = cur.execute(
            "SELECT rowid, close FROM daily_quotes WHERE code=? ORDER BY date",
            (code,)
        ).fetchall()

        changes = 0
        for i in range(1, len(rows)):
            prev_close = rows[i - 1][1]
            cur_close = rows[i][1]
            if prev_close and prev_close > 0:
                pct = round((cur_close - prev_close) / prev_close * 100, 2)
                cur.execute(
                    "UPDATE daily_quotes SET change_pct=? WHERE rowid=?",
                    (pct, rows[i][0])
                )
                changes += 1

        updated += changes
        if changes > 0:
            batch_count += 1

        if idx % 1000 == 0:
            conn.commit()
            print(f"  进度：{idx}/{total} 只, 已计算 {updated:,} 条")

    conn.commit()
    nonzero = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE change_pct!=0").fetchone()[0]
    print(f"涨跌幅计算完成：共更新 {updated:,} 条（{batch_count} 只涉及多条记录）")
    print(f"现有非零涨跌幅记录：{nonzero:,} 条")
    conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-names", action="store_true")
    parser.add_argument("--skip-change", action="store_true")
    args = parser.parse_args()

    if not args.skip_names:
        ensure_names_csv()
        update_stock_names()

    if not args.skip_change:
        calc_change_pct()

    print("\n全部完成！")
