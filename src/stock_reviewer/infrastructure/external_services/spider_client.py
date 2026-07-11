"""爬虫基类。

封装模拟浏览器访问的通用逻辑。
各爬虫继承此类，实现各自的解析逻辑。
"""

import random
import time
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

from stock_reviewer.core.logging import logger


class BaseSpider:
    """爬虫基类，提供模拟浏览器访问能力。"""

    BASE_HEADERS: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.session = requests.Session()
        self.session.headers.update(self.BASE_HEADERS)
        self.min_delay = min_delay
        self.max_delay = max_delay

    def _rate_limit(self) -> None:
        """限频，随机延时。"""
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def _get(
        self,
        url: str,
        params: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Optional[BeautifulSoup]:
        """发送 GET 请求，返回 BeautifulSoup 对象。

        Args:
            url: 请求地址。
            params: 查询参数。
            timeout: 超时秒数。

        Returns:
            BeautifulSoup 对象，失败返回 None。
        """
        self._rate_limit()
        try:
            resp = self.session.get(url, params=params, timeout=timeout)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            logger.warning("请求 %s 返回状态码 %d", url, resp.status_code)
        except requests.RequestException as e:
            logger.error("请求 %s 失败: %s", url, e)
        return None
