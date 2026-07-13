"""数据质量检查脚本。

检查所有已导入数据的字段缺失情况，输出统计报告。
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "quant_data.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

total = cur.execute("SELECT COUNT(*) FROM daily_quotes").fetchone()[0]
stocks = cur.execute("SELECT COUNT(DISTINCT code) FROM daily_quotes").fetchone()[0]
print(f"总记录数: {total:,}")
print(f"总股票数: {stocks:,}")

# 1. name 缺失
name_empty = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE name=''").fetchone()[0]
name_filled = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE name!=''").fetchone()[0]
print(f"\n--- 股票名称 ---")
print(f"  有名称: {name_filled:,} ({name_filled/total*100:.1f}%)")
print(f"  名称为空: {name_empty:,} ({name_empty/total*100:.1f}%)")
stocks_with_name = cur.execute("SELECT COUNT(DISTINCT code) FROM daily_quotes WHERE name!=''").fetchone()[0]
stocks_no_name = cur.execute("SELECT COUNT(DISTINCT code) FROM daily_quotes WHERE name=''").fetchone()[0]
print(f"  有名称的股票数: {stocks_with_name:,}")
print(f"  无名称的股票数: {stocks_no_name:,}")

# 2. change_pct 缺失
cp_zero = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE change_pct=0").fetchone()[0]
cp_nonzero = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE change_pct!=0").fetchone()[0]
print(f"\n--- 涨跌幅 change_pct ---")
print(f"  有值: {cp_nonzero:,} ({cp_nonzero/total*100:.1f}%)")
print(f"  为 0（即缺失）: {cp_zero:,} ({cp_zero/total*100:.1f}%)")

# 3. turnover_rate 缺失
tr_zero = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE turnover_rate=0").fetchone()[0]
tr_nonzero = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE turnover_rate!=0").fetchone()[0]
print(f"\n--- 换手率 turnover_rate ---")
print(f"  有值: {tr_nonzero:,} ({tr_nonzero/total*100:.1f}%)")
print(f"  为 0（即缺失）: {tr_zero:,} ({tr_zero/total*100:.1f}%)")

# 4. 日线记录数分布
print(f"\n--- 各股票日线记录数分布 ---")
dist = cur.execute("""
    SELECT bucket, COUNT(*) FROM (
        SELECT CASE
            WHEN cnt < 60 THEN '<60天'
            WHEN cnt < 250 THEN '60-250天'
            WHEN cnt < 1000 THEN '250-1000天'
            ELSE '>1000天'
        END AS bucket
        FROM (SELECT COUNT(*) AS cnt FROM daily_quotes GROUP BY code)
    ) GROUP BY bucket ORDER BY bucket
""").fetchall()
for bucket, cnt in dist:
    print(f"  {bucket}: {cnt:,} 只")

# 5. 数据时间范围
min_date, max_date = cur.execute("SELECT MIN(date), MAX(date) FROM daily_quotes").fetchone()
print(f"\n--- 时间范围 ---")
print(f"  最早: {min_date}")
print(f"  最晚: {max_date}")

# 6. 近60天数据记录数
cutoff = str(int(max_date[:4])*10000 + int(max_date[5:7])*100 + int(max_date[8:10]) - 60)
cutoff_iso = f"{cutoff[:4]}-{cutoff[4:6]}-{cutoff[6:8]}"
recent = cur.execute(
    "SELECT COUNT(*) FROM daily_quotes WHERE date >= ?", (cutoff_iso,)
).fetchone()[0]
recent_stocks = cur.execute(
    "SELECT COUNT(DISTINCT code) FROM daily_quotes WHERE date >= ?", (cutoff_iso,)
).fetchone()[0]
print(f"\n--- 近60天（>= {cutoff_iso}） ---")
print(f"  记录数: {recent:,}")
print(f"  股票数: {recent_stocks:,}")

# 7. 成交量/额样本检查（找出可能的单位问题）
print(f"\n--- 成交量/额最大值（TOP 5） ---")
samples = cur.execute("""
    SELECT code, date, volume, amount FROM daily_quotes 
    ORDER BY amount DESC LIMIT 5
""").fetchall()
for code, dt, vol, amt in samples:
    print(f"  {code} {dt}: 成交量={vol:,}, 成交额={amt/1e8:.2f}亿")

# 8. 最近交易日活跃股票数
last_date = cur.execute("SELECT MAX(date) FROM daily_quotes").fetchone()[0]
active = cur.execute(
    "SELECT COUNT(*) FROM daily_quotes WHERE date=?", (last_date,)
).fetchone()[0]
print(f"\n--- 最近交易日 ({last_date}) ---")
print(f"  有交易的股票数: {active:,}")

conn.close()
