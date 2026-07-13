"""运行脚本：导入通达信日线数据到 SQLite。

使用方式：
  1. 打开 https://www.tdx.com.cn/article/vipdata.html
  2. 点击下载"沪深京日线数据完整包"，保存 hsjday.zip
  3. 将 hsjday.zip 解压到 data/imports/ 目录
  4. 运行此脚本

解压后目录结构：
  data/imports/hsjday/sh/lday/*.day
  data/imports/hsjday/sz/lday/*.day

也支持直接放通达信导出的 CSV 文件到 data/imports/ 下。
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
