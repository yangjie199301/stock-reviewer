"""领域实体定义。

每个实体对应一张数据库表，使用 dataclass 避免 ORM 依赖。
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DailyQuote:
    """日线行情。"""
    code: str             # 股票代码
    name: str             # 股票名称
    date: date            # 交易日期
    open: float           # 开盘价
    high: float           # 最高价
    low: float            # 最低价
    close: float          # 收盘价
    volume: int           # 成交量（股）
    amount: float         # 成交额（元）
    change_pct: float     # 涨跌幅（%）
    turnover_rate: float  # 换手率（%）


@dataclass
class LHBDetail:
    """龙虎榜详情。"""
    code: str                    # 股票代码
    name: str                    # 股票名称
    date: date                   # 上榜日期
    close: float                 # 收盘价
    change_pct: float            # 涨跌幅（%）
    net_buy_amount: float        # 龙虎榜净买额（元）
    buy_amount: float            # 龙虎榜买入额（元）
    sell_amount: float           # 龙虎榜卖出额（元）
    total_amount: float          # 龙虎榜成交额（元）
    reason: str                  # 上榜原因
    turnover_rate: float         # 换手率（%）


@dataclass
class FundFlow:
    """个股资金流向。"""
    code: str                         # 股票代码
    name: str                         # 股票名称
    date: date                        # 交易日期
    main_net_inflow: float            # 主力净流入（元）
    retail_net_inflow: float          # 散户净流入（元）
    main_net_inflow_pct: float        # 主力净流入占比（%）


@dataclass
class NorthFund:
    """北向资金（沪/深股通）。"""
    date: date                         # 交易日期
    sh_net_inflow: float               # 沪股通净流入（元）
    sz_net_inflow: float               # 深股通净流入（元）
    total_net_inflow: float            # 合计净流入（元）


@dataclass
class BoardDaily:
    """板块行情。"""
    board_name: str       # 板块名称
    board_type: str       # 板块类型：industry / concept
    date: date            # 交易日期
    change_pct: float     # 涨跌幅（%）
    up_count: int         # 上涨家数
    down_count: int       # 下跌家数
    leader_code: str = ""       # 领涨股代码
    leader_name: str = ""       # 领涨股名称


@dataclass
class Policy:
    """政策资讯。"""
    title: str                    # 标题
    url: str                      # 链接
    publish_date: date            # 发布日期
    source: str                   # 来源
    summary: str = ""             # 摘要
    keywords: str = ""            # 匹配到的关键词（逗号分隔）


@dataclass
class ResearchReport:
    """券商研报。"""
    title: str                    # 研报标题
    stock_code: str               # 股票代码
    stock_name: str               # 股票名称
    institution: str              # 机构名称
    publish_date: date            # 发布日期
    summary: str = ""             # 摘要
    rating: str = ""              # 评级
    keywords: str = ""            # 匹配关键词


@dataclass
class FinancialReport:
    """基本面财报。"""
    code: str                    # 股票代码
    name: str                    # 股票名称
    report_date: date            # 报告期（如 2025-12-31 表示年报）
    report_type: str             # 报告类型：Q1 / Q2(中报) / Q3 / Q4(年报)
    revenue: float = 0.0         # 营业收入（元）
    net_profit: float = 0.0      # 净利润（元）
    total_assets: float = 0.0    # 总资产（元）
    total_liabilities: float = 0.0  # 总负债（元）
    equity: float = 0.0          # 净资产（元）
    roe: float = 0.0             # ROE（%）
    gross_margin: float = 0.0    # 毛利率（%）


@dataclass
class DataMeta:
    """数据更新元信息。

    记录每只股票（或每张表）的最新数据日期，用于增量判断。
    """
    table_name: str        # 表名
    code: str              # 股票代码（全局性数据用 __global__）
    latest_date: date      # 已存在的最新数据日期
