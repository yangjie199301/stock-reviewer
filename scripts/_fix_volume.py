"""修复所有 negative volume 的 int32 溢出问题"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "quant_data.db"
conn = sqlite3.connect(str(DB))
cur = conn.cursor()

# 统计负值
neg_count = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE volume < 0").fetchone()[0]
neg_codes = cur.execute("SELECT DISTINCT code FROM daily_quotes WHERE volume < 0 ORDER BY code").fetchall()
print(f"负数 volume 记录数: {neg_count:,}")
print(f"涉及股票数: {len(neg_codes)}")
print(f"涉及代码: {[c[0] for c in neg_codes[:20]]}{'...' if len(neg_codes)>20 else ''}")

# 修复
cur.execute("UPDATE daily_quotes SET volume = volume + 4294967296 WHERE volume < 0")
conn.commit()
fixed = cur.rowcount
print(f"已修复: {fixed:,} 条")

# 二次验证
remaining = cur.execute("SELECT COUNT(*) FROM daily_quotes WHERE volume < 0").fetchone()[0]
print(f"剩余负数: {remaining}")
conn.close()
