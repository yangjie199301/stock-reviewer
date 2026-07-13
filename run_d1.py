"""运行脚本：导入通达信日线数据到 SQLite。

使用方式（二选一）：

方式一（推荐）— 官方日线数据包：
  1. 下载 https://data.tdx.com.cn/vipdoc/hsjday.zip
  2. 解压后把 hsjday/ 整个目录放到 data/imports/ 下
  3. 运行此脚本

方式二 — 通达信手动导出 CSV：
  1. 在通达信中导出日线 CSV（系统 → 数据导出）
  2. 将 CSV 文件放入 data/imports/ 目录
  3. 运行此脚本

导出文件格式：
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
from stock_reviewer.infrastructure.adapters.tdx_importer import TdxImporter, download_latest_data


def main():
    # 初始化数据库
    init_database()
    logger.info("数据库初始化完成")

    # 尝试下载最新数据包（自动跳过如果已存在）
    logger.info("正在下载最新日线数据包...")
    if download_latest_data():
        logger.info("数据包下载完成")
    else:
        logger.info("下载失败或已跳过，尝试导入已有文件")

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
