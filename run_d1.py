"""运行脚本：从通达信导出文件导入数据。

使用方式：
  1. 在通达信中导出数据（系统 → 数据导出 → 日线数据）
  2. 将导出的 CSV 文件放入 data/imports/ 目录
  3. 运行此脚本导入数据

导出文件格式（CSV，推荐批量导出）：
  代码,名称,日期,开盘,最高,最低,收盘,成交量,成交额
  000001,平安银行,2026-07-01,12.34,12.56,12.20,12.45,12345678,156789000
"""

# 不使用代理
import os
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "*"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from stock_reviewer.core.logging import logger
from stock_reviewer.infrastructure.database.schema import init_database
from stock_reviewer.infrastructure.adapters.tdx_importer import TdxImporter


def main():
    # 初始化数据库
    init_database()
    logger.info("数据库初始化完成")

    # 运行导入
    importer = TdxImporter()
    result = importer.import_all()

    print(f"\n导入完成：")
    print(f"  文件总数: {result.get('total_files', 0)}")
    print(f"  导入记录: {result.get('imported', 0)}")
    print(f"  跳过文件: {result.get('skipped', 0)}")
    if result.get("failed"):
        print(f"  失败文件: {', '.join(result['failed'])}")


if __name__ == "__main__":
    main()
