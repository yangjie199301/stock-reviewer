# D1 — 数据管理 实施计划

> 目标：实现数据获取、存储、查询、整合四个模块的完整代码
> 参考规范：[project_structure.md](../../conventions/project_structure.md)、[python_style.md](../../conventions/python_style.md)

---

## 1. 整体架构（Clean Architecture）

```
src/
└── stock_reviewer/
    ├── domain/
    │   ├── entities/              # 数据实体：DailyQuote, LHBRecord 等
    │   └── repositories.py        # 仓库接口定义
    ├── infrastructure/
    │   ├── database/
    │   │   ├── connection.py      # SQLite 连接管理
    │   │   ├── schema.py          # 建表 DDL
    │   │   └── repositories/      # 各实体的仓库实现
    │   └── external_services/
    │       ├── akshare_client.py  # akshare 封装（重试、日志）
    │       └── spider_client.py   # 爬虫基类
    ├── application/
    │   └── data_collection/
    │       ├── daily_collector.py # 每日数据采集编排
    │       └── quarterly_collector.py # 季度（基本面）采集
    └── core/
        ├── config.py              # 配置（DB 路径、股票池等）
        └── logging.py             # 日志配置
```

---

## 2. 实现顺序（6 步）

| 步骤       | 内容                                             | 产出                   |
| ---------- | ------------------------------------------------ | ---------------------- |
| **Step 1** | core/config + logging                            | 配置加载、日志初始化   |
| **Step 2** | domain/entities + repositories 接口              | 数据实体定义、接口契约 |
| **Step 3** | infra/database（connection + schema + 仓库实现） | SQLite 建表 + CRUD     |
| **Step 4** | infra/external_services（akshare + 爬虫封装）    | 外部数据源调用层       |
| **Step 5** | application/collectors（每日 + 季度采集编排）    | 一键采集入口           |
| **Step 6** | 查询 + 整合模块                                  | 数据查询 API、整合组装 |

---

## 3. 数据库表设计（9 张表）

| 表名                | 对应数据       | 唯一键              | 说明                     |
| ------------------- | -------------- | ------------------- | ------------------------ |
| `daily_quotes`      | 日线行情       | (code, date)        | 开高低收量、换手率       |
| `lhb_details`       | 龙虎榜详情     | (code, date)        | 净买额、上榜原因         |
| `fund_flows`        | 个股资金流向   | (code, date)        | 主力净流入/出            |
| `north_funds`       | 北向资金       | date                | 沪/深股通净流入          |
| `board_daily`       | 板块行情       | (board_name, date)  | 行业/概念板块涨跌        |
| `policies`          | 政策资讯       | url_hash            | 国务院政策               |
| `research_reports`  | 券商研报       | url_hash            | 标题、摘要               |
| `financial_reports` | 基本面财报     | (code, report_date) | 三大报表指标             |
| `data_meta`         | 数据更新元信息 | (table_name, code)  | 记录每只股票最新更新日期 |

---

## 4. 关键设计决策

| 问题           | 决策                                                  |
| -------------- | ----------------------------------------------------- |
| **增量更新**   | 每天采集前先查 `data_meta` 表，只拉最新日期之后的数据 |
| **全市场覆盖** | 采集全 A 股，数据量大时支持分批次处理                 |
| **容错**       | 单只股票失败不中断整体流程，记录错误日志              |
| **去重**       | 使用 INSERT OR REPLACE / 唯一键冲突忽略               |
| **DB 路径**    | 默认 `./quant_data.db`，支持环境变量 `DB_PATH` 覆盖   |

---

## 5. 已确认的决定

- **初期测试范围：** 先跑前 100 只股票验证，确认无误后放开全市场
- **采集方式：** 串行执行，严格控制请求频率（每次请求后 sleep 0.5-2s 随机延时），防止被封
- **架构：** 按 Clean Architecture 从头新建，不依赖老的 `data_fetcher.py`
