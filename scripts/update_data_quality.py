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


def fetch_stock_names(target_file: Path) -> bool:
    """从 akshare 抓取 A 股名称映射并保存到 CSV。"""
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        df.to_csv(target_file, index=False, encoding="utf-8-sig")
        print(f"股票名称映射表已保存：{target_file}（{len(df)} 只）")
        return True
    except Exception as e:
        print(f"akshare 抓取名称失败：{e}")
        return False


def build_manual_names(target_file: Path):
    """如果 akshare 抓取失败，创建基础名称映射。"""
    conn = sqlite3.connect(str(DB_PATH))
    codes = conn.execute("SELECT DISTINCT code FROM daily_quotes ORDER BY code").fetchall()
    conn.close()

    manual = {
        "000001": "上证指数", "000002": "上证A股", "000003": "上证B股",
        "000016": "上证50", "000300": "沪深300", "000688": "科创50",
        "399001": "深证成指", "399006": "创业板指", "399005": "中小板指",
        "880001": "上证指数(全)", "880002": "上证A股(全)", "880003": "上证B(全)",
        "880004": "深证成指(全)", "880005": "深证综指(全)",
    }
    with open(target_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name"])
        for code, name in manual.items():
            writer.writerow([code, name])
        known = set(manual.keys())
        for (code,) in codes:
            if code not in known:
                writer.writerow([code, ""])
    print(f"基础名称映射已保存：{target_file}")


def ensure_names_csv() -> bool:
    """确保股票名称映射文件存在。"""
    if NAMES_CSV.exists() and NAMES_CSV.stat().st_size > 100:
        return True
    print("正在下载股票名称数据...")
    if fetch_stock_names(NAMES_CSV):
        return True
    print("akshare 下载失败，创建基础名称映射...")
    build_manual_names(NAMES_CSV)
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
