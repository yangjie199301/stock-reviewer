# Python 编程规范

> 本文档用于指导 **AI Agent** 和开发者编写风格一致的 Python 代码。
> 基于 PEP 8，结合本项目实际需求做了补充和取舍。

---

## 1. 代码格式

### 1.1 缩进

- 使用 **4 空格** 缩进，禁止使用 Tab
- 续行使用括号内隐式换行或悬挂缩进（悬挂缩进额外缩进一层）

```python
# 正确：括号内隐式换行
def long_function_name(
    param_one, param_two, param_three,
    param_four,
):
    pass

# 正确：悬挂缩进
result = some_function(
    arg1, arg2,
    arg3,
)

# 错误：悬挂缩进不缩进
result = some_function(
    arg1, arg2,
    arg3,
)
```

### 1.2 行长

- **最大行长 120 字符**（PEP 8 建议 79，本项目放宽到 120）
- 超过时优先在运算符前换行

```python
# 正确：运算符前换行
total = (variable_one + variable_two + variable_three
         - variable_four)
```

### 1.3 空行

| 场景 | 空行数 |
|------|--------|
| 顶级函数/类之间 | 2 个空行 |
| 类内部方法之间 | 1 个空行 |
| 函数内逻辑段落 | 1 个空行（适度使用） |
| 文件末尾 | 1 个空行 |

```python
import os
import sys


def top_level_function():
    """顶级函数前需要 2 个空行。"""
    pass


class MyClass:
    """类定义前需要 2 个空行。"""

    def method_one(self):
        pass

    def method_two(self):
        """方法之间 1 个空行。"""
        pass
```

### 1.4 空格

- 赋值、比较、算术运算符两侧各 1 个空格
- 函数参数默认值 `=` 两侧不加空格
- 切片冒号两侧不加空格
- 括号内紧贴括号不加空格

```python
# 正确
x = 1
y = x + 2
result = func(a=1, b=2)
items[0:5]
range(10)

# 错误
x=1
y = x+2
result = func(a = 1, b = 2)
items[0 : 5]
range( 10 )
```

---

## 2. 命名规范

### 2.1 规则总表

| 类别 | 风格 | 示例 |
|------|------|------|
| 变量/函数/方法 | `snake_case` | `stock_code`, `fetch_daily_quotes()` |
| 私有函数/变量 | 前缀 `_` | `_latest_trade_date()`, `_cache` |
| 常量 | `UPPER_SNAKE_CASE` | `DB_PATH`, `REQUEST_TIMEOUT` |
| 类 | `PascalCase` | `StockDataFetcher`, `DatabaseManager` |
| 异常类 | `PascalCase` + `Error` 后缀 | `FetchError`, `DatabaseError` |
| 模块名 | `snake_case` 短文件名 | `data_fetcher.py` |
| 类型变量 | `PascalCase` | `T`, `ResultType` |
| 枚举成员 | `UPPER_SNAKE_CASE` | `class Market(Enum): SH = "sh"` |

### 2.2 命名原则

- **变量名要自解释**，禁止单字母命名（循环索引 `i`, `j` 除外）
- 布尔变量用 `is_`, `has_`, `should_` 前缀：`is_ready`, `has_error`
- 函数名用动词开头：`fetch_*`, `parse_*`, `validate_*`, `update_*`
- 避免与标准库/内置函数重名（如 `list`, `dict`, `type`）

```python
# 正确
stock_pool = ["000001", "000002"]
is_market_open = True

# 错误
lst = ["000001", "000002"]
flag = True
```

---

## 3. 类型注解

- **所有函数参数和返回值必须加类型注解**
- 使用标准库 `typing` 中的泛型类型

```python
from typing import Optional, List, Dict, Tuple


def fetch_daily_quotes(
    stock_codes: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> int:
    """拉取日线行情，返回插入行数。"""
    ...
```

**简化规则：**
- 简单类型直接使用：`str`, `int`, `float`, `bool`, `None`
- 容器类型使用泛型：`List[str]`, `Dict[str, int]`, `Optional[str]`
- 返回 `None` 时注解为 `-> None`
- 不需要对 `self` 和 `cls` 加注解

---

## 4. 文档字符串 (Docstring)

### 4.1 风格

使用 Google 风格：

```python
def fetch_lhb_details(trade_date: str) -> int:
    """获取指定交易日的龙虎榜明细。

    Args:
        trade_date: 交易日，格式 "YYYYMMDD"。

    Returns:
        写入数据库的行数。若接口无数据返回 0。

    Raises:
        ConnectionError: 数据源不可达时抛出。
    """
```

### 4.2 规则

- **所有公开函数/方法必须写 docstring**
- 私有函数（`_` 前缀）可以省略，但如果逻辑复杂也应添加
- docstring 使用 `"""` 三引号，内容与引号在同一行
- 一行 docstring 直接收尾：`"""简要描述。"""`
- 多行 docstring：首行简要描述 → 空行 → 详细描述 → Args → Returns → Raises
- 描述用中文

```python
# 单行
def is_market_open() -> bool:
    """检查当前是否为交易时间。"""

# 多行
def update_all(date: Optional[str] = None) -> Dict[str, any]:
    """全量更新所有数据。

    按顺序执行：骨架(日线) → 血液(龙虎榜/资金流) → 大脑(政策/研报) → 皮肤(论坛)。
    每步独立 try-except，失败记录日志并继续。

    Args:
        date: 交易日，默认当天。

    Returns:
        包含各项更新结果的字典：
        {"daily_quotes": 100, "lhb": 20, ...}
    """
```

---

## 5. Import 规范

### 5.1 分组顺序

每个分组之间空一行，分组内部按字母序排列：

```python
# 1. 标准库
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

# 2. 第三方库
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 3. 本项目模块
from data_fetcher import update_all
```

### 5.2 导入规则

- **禁止使用 `from module import *`**
- 优先导入具体对象而非模块：`from typing import List` 而非 `import typing`
- 仅在模块名足够长时使用 `as` 别名：`import pandas as pd`

---

## 6. 错误处理

### 6.1 基本原则

- 使用**特定异常类**，禁止裸 `except:`
- 异常粒度适中：一个 try 包一个可能出错的操作，而非整段代码
- 需要清理资源时用 `try-finally` 或 `with` 语句

```python
# 正确
try:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(sql)
except sqlite3.DatabaseError as e:
    logger.error("数据库操作失败: %s", e)
    raise
finally:
    conn.close()

# 错误：裸 except，捕获范围过大
try:
    result = risky_operation()
except:
    pass

# 错误：异常吞没
try:
    result = risky_operation()
except Exception:
    pass
```

### 6.2 日志错误

```python
logger.error("描述性消息: %s", error_var)   # 正确：延迟格式化
logger.error(f"描述性消息: {error_var}")     # 错误：提前格式化，浪费性能
```

### 6.3 函数调用异常

```python
# 推荐：在 update_all 中每步独立 try 隔离故障
try:
    count = fetch_daily_quotes()
except Exception as e:
    logger.error("日线行情失败: %s", e)
    count = 0  # 降级处理
```

---

## 7. 函数设计原则

### 7.1 职责

- **一个函数只做一件事**
- 函数名应当准确描述其行为：`fetch_daily_quotes_akshare` 好于 `get_data`
- 函数参数不超过 5 个，超过时考虑用 `**kwargs` 或数据类

### 7.2 返回值

- 失败时不返回 `None` 或错误码，而是**抛出异常**
- 正常时返回有意义的值（如影响行数、布尔结果），无返回值时返回 `None`

```python
# 正确：异常传递给调用方处理
def fetch_data() -> pd.DataFrame:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()

# 错误：返回 None 表示错误
def fetch_data() -> Optional[pd.DataFrame]:
    try:
        resp = requests.get(url, timeout=15)
        return resp.json()
    except Exception:
        return None
```

---

## 8. 项目特有约定

### 8.1 数据库操作

- 使用 `get_db_connection()` 统一获取连接，不直接 `sqlite3.connect`
- 写操作后及时 `conn.commit()`，用 `try-finally` 确保 `conn.close()`
- 批量插入使用 `executemany()` 或循环内 `execute()` + 统一 `commit()`

### 8.2 重试装饰器

```python
@retry_on_failure(max_retries=3, delay=15)
def fetch_north_fund(trade_date: str) -> int:
    """重试 3 次，间隔 15 秒。"""
```

重试装饰器仅用于**外部接口调用**，不用于数据库写入。

### 8.3 配置常量

- 项目中所有的魔数（magic number）和字符串常量必须定义为模块级常量
- 常量在文件顶部集中定义

```python
# 文件顶部
DB_PATH = "quant_data.db"
REQUEST_TIMEOUT = 15
DEFAULT_STOCK_POOL = ["000001", "000002"]
```

---

## 9. Lint 配置

项目根目录创建 `pyproject.toml`，配置 ruff 或 pylint：

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]
ignore = ["E501"]  # 行长度由 line-length 控制

[tool.ruff.format]
quote-style = "double"
```

**提交前检查：** 代码应当通过 ruff 检查（**零 error**），warning 应尽量少。

---

## 10. 总结核对清单

Agent 提交 Python 代码前检查：

- [ ] 缩进使用 4 空格，无 Tab
- [ ] 行长度不超过 120 字符
- [ ] 命名符合 snake_case / PascalCase / UPPER_SNAKE_CASE
- [ ] 所有公开函数有类型注解 + docstring
- [ ] Import 按标准库 → 第三方 → 本项目分组排序
- [ ] 无裸 `except:`，无 `from xxx import *`
- [ ] 无调试残留（print, breakpoint, pdb）
- [ ] 常量集中定义在文件顶部
- [ ] 数据库连接使用统一的 `get_db_connection()`
