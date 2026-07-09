# Python Clean Architecture 项目结构规范

> 本文档定义基于 Clean Architecture 思想的 Python 项目目录结构、分层职责及依赖规则。
> 适用于任何 Python 应用，替换业务逻辑即可复用此骨架。

---

## 1. 架构总览

```
┌──────────────────────────────────────────────┐
│              interfaces/                      │  ─── 接口层
│   CLI / API / 定时任务 / 消息消费者            │     用户入口、外部通信
└──────────────────┬───────────────────────────┘
                   │ 调用
┌──────────────────▼───────────────────────────┐
│            application/                       │  ─── 应用层
│   Services / Use Cases                        │     用例编排、事务协调
└──────────────────┬───────────────────────────┘
                   │ 调用
┌──────────────────▼───────────────────────────┐
│               domain/                         │  ─── 领域层 (最核心)
│   Entities / Value Objects / Interfaces       │     业务实体、仓储抽象定义
└──────────────────┬───────────────────────────┘
                   │ 实现
┌──────────────────▼───────────────────────────┐
│          infrastructure/                      │  ─── 基础设施层
│   DB / 外部 API / 消息队列 / 文件系统          │     技术细节实现
└──────────────────────────────────────────────┘
```

### 依赖规则（严格单向）

```
domain          →  零外部依赖（纯 Python 标准库即可）
application     →  只能依赖 domain
infrastructure  →  实现 domain 中定义的接口
interfaces      →  依赖 application
```

**核心原则：** 内层（domain）不知道外层（infrastructure）的存在。外层依赖内层，而非相反。

### 为什么这样分层

| 层次           | 职责               | 变更原因        |
| -------------- | ------------------ | --------------- |
| domain         | 核心业务概念与规则 | 业务需求变化    |
| application    | 用例流程编排       | 业务流程变化    |
| infrastructure | 技术实现细节       | DB/API/框架升级 |
| interfaces     | 用户交互方式       | 接入渠道变化    |

**业务代码与技术代码解耦**——换数据库、换框架、加 API 接口，都不需要动 domain 和 application。

---

## 2. 目录结构

```
your-project/
│
├── src/
│   └── your_package/              # 主包，以项目命名
│       │
│       ├── domain/                 ═══ 领域层 ═══
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   └── *.py           # 领域实体 / 值对象 (dataclass)
│       │   │
│       │   ├── interfaces/        # 仓储 / 外部服务 抽象接口
│       │   │   ├── __init__.py
│       │   │   ├── repository.py  # 通用仓储接口 (可选)
│       │   │   └── *.py           # 按业务领域拆分
│       │   │
│       │   └── exceptions.py      # 领域异常定义
│       │
│       ├── application/           ═══ 应用层 ═══
│       │   ├── __init__.py
│       │   └── services/
│       │       ├── __init__.py
│       │       └── *.py           # 每个用例一个 Service
│       │
│       ├── infrastructure/        ═══ 基础设施层 ═══
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── connection.py  # 连接管理
│       │   │   ├── models.py      # ORM 模型 / 建表 DDL (可选)
│       │   │   └── repositories/  # 仓储实现
│       │   │       ├── __init__.py
│       │   │       └── *.py       # 如 sqlite_xxx_repo.py / mysql_xxx_repo.py
│       │   │
│       │   ├── external_services/ # 外部服务调用
│       │   │   ├── __init__.py
│       │   │   └── *.py           # API 客户端 / 第三方 SDK 封装
│       │   │
│       │   └── errors.py          # 基础设施异常定义
│       │
│       ├── interfaces/            ═══ 接口层 ═══
│       │   ├── __init__.py
│       │   ├── cli.py             # 命令行入口
│       │   ├── api/               # HTTP API (如 FastAPI)
│       │   │   ├── __init__.py
│       │   │   ├── routes.py
│       │   │   └── schemas.py     # 请求/响应模型
│       │   └── consumers/         # 消息消费者
│       │       ├── __init__.py
│       │       └── *.py
│       │
│       └── config/                ═══ 全局配置 ═══
│           ├── __init__.py
│           ├── settings.py        # 配置常量
│           └── logging_config.py  # 日志配置
│
├── tests/                          ═══ 测试 ═══
│   ├── __init__.py
│   ├── unit/                      # 单元测试 (mock 外部依赖)
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── test_entities.py
│   │   └── application/
│   │       ├── __init__.py
│   │       └── test_services.py
│   └── integration/               # 集成测试 (真实 DB/API)
│       ├── __init__.py
│       └── test_repositories.py
│
├── scripts/                        # 运维脚本 (数据迁移、备份、部署)
├── data/                           # 运行时数据文件 (CSV, JSON 等), gitignore
├── docs/                           # 项目文档
├── .gitignore
├── pyproject.toml                  # 项目元数据、依赖、工具配置
└── README.md
```

### 目录说明

| 目录       | 是否提交 git | 说明                 |
| ---------- | ------------ | -------------------- |
| `src/`     | ✅           | 源代码               |
| `tests/`   | ✅           | 测试代码             |
| `scripts/` | ✅           | 运维辅助脚本         |
| `docs/`    | ✅           | 文档                 |
| `data/`    | ❌           | 运行时生成的数据文件 |

---

## 3. 各层详细职责与编码约定

### 3.1 Domain 层 — 纯 Python，零外部依赖

**不允许 import 任何第三方库**（requests、pandas、SQLAlchemy 等），只允许使用 Python 标准库。

#### 3.1.1 Entities — 领域实体

- 使用 `@dataclass` 定义，纯数据容器
- 可包含**与自身数据相关**的简单校验和计算方法
- 不包含持久化、网络、IO 相关逻辑

```python
# domain/entities/user.py
from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    email: str

    def is_valid_email(self) -> bool:
        return "@" in self.email
```

#### 3.1.2 Interfaces — 仓储与外部服务接口

- 使用 `abc.ABC` + `@abstractmethod` 定义契约
- 命名体现用途，如 `UserRepository`、`PaymentGateway`
- 方法签名使用领域实体，不暴露技术细节

```python
# domain/interfaces/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.user import User


class UserRepository(ABC):
    """用户仓储接口。定义持久化契约，不关心具体实现。"""

    @abstractmethod
    def save(self, user: User) -> None:
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        ...

    @abstractmethod
    def find_all(self) -> List[User]:
        ...
```

#### 3.1.3 Exceptions — 领域异常

```python
# domain/exceptions.py
class DomainError(Exception):
    """所有领域异常的基类。"""
    pass


class EntityNotFoundError(DomainError):
    """实体未找到。"""
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(f"{entity_name} 未找到: {entity_id}")
        self.entity_name = entity_name
        self.entity_id = entity_id
```

---

### 3.2 Application 层 — 依赖 domain，不依赖 infrastructure

- 通过**依赖注入**接收 domain 接口的实例
- 编排业务流程，不包含技术实现
- 每个 Service 对应一个**用例**（Use Case）

```python
# application/services/user_service.py
from typing import List
from domain.entities.user import User
from domain.interfaces.user_repository import UserRepository


class UserService:
    """用户管理用例。"""

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def register(self, user_id: str, name: str, email: str) -> User:
        user = User(id=user_id, name=name, email=email)
        if not user.is_valid_email():
            raise ValueError("邮箱格式无效")
        self._repo.save(user)
        return user

    def list_all(self) -> List[User]:
        return self._repo.find_all()
```

**注意：** Service 只依赖接口，不依赖具体实现。`UserRepository` 是 domain 层定义的抽象，具体实现在 infrastructure 层。

---

### 3.3 Infrastructure 层 — 实现 domain 接口

- 实现 domain 层定义的所有接口
- 可依赖第三方库（数据库驱动、HTTP 客户端、SDK）
- 将技术异常转换为领域异常再抛向上一层

```python
# infrastructure/database/repositories/sqlite_user_repo.py
from typing import Optional, List
from domain.entities.user import User
from domain.interfaces.user_repository import UserRepository
from domain.exceptions import EntityNotFoundError


class SQLiteUserRepository(UserRepository):
    """SQLite 实现的用户仓储。"""

    def __init__(self, connection):
        self._conn = connection

    def save(self, user: User) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO users (id, name, email) VALUES (?, ?, ?)",
            (user.id, user.name, user.email),
        )
        self._conn.commit()

    def find_by_id(self, user_id: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            raise EntityNotFoundError("User", user_id)
        return User(id=row[0], name=row[1], email=row[2])
```

```python
# infrastructure/external_services/email_gateway.py
from domain.interfaces.user_repository import ...  # 依赖接口而非具体类


class SMTPEmailGateway:
    """SMTP 实现的邮件发送。"""
    ...
```

---

### 3.4 Interfaces 层 — 用户入口

- 负责**组装依赖**（依赖注入的起点）
- 将用户输入转为 Service 调用，将输出格式化为用户需要的格式
- 不含业务逻辑

```python
# interfaces/cli.py
from config.settings import DATABASE_PATH
from config.logging_config import setup_logging
from infrastructure.database.connection import get_connection
from infrastructure.database.repositories.sqlite_user_repo import SQLiteUserRepository
from application.services.user_service import UserService


def main():
    setup_logging()
    conn = get_connection(DATABASE_PATH)

    # 组装依赖
    user_repo = SQLiteUserRepository(conn)
    user_service = UserService(repo=user_repo)

    # 执行用例
    users = user_service.list_all()
    for u in users:
        print(f"{u.id}: {u.name} ({u.email})")
```

---

### 3.5 Config — 全局配置

- 所有可配置项集中管理
- 支持环境变量覆盖（适用于不同环境）

```python
# config/settings.py
import os

# 数据库
DATABASE_PATH = os.getenv("DATABASE_PATH", "app.db")

# 网络
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

# 业务
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
```

---

## 4. 依赖注入

本项目使用**手动依赖注入（Manual DI）**，不引入第三方 DI 框架。

### 组装规则

```
interfaces（入口）→ 创建 infrastructure 实例 → 注入 application Service → 调用
```

所有组装集中在 interfaces 层入口函数中，不要在 Service 内部 new 依赖对象。

### 测试中的 Mock

受益于依赖注入，测试时可以轻松替换为 Mock 实现：

```python
# tests/unit/application/test_user_service.py
from unittest.mock import Mock
from application.services.user_service import UserService


def test_register():
    mock_repo = Mock()
    service = UserService(repo=mock_repo)

    user = service.register("1", "Alice", "alice@example.com")

    assert user.name == "Alice"
    mock_repo.save.assert_called_once()
```

---

## 5. 跨层数据流转

### 调用链示例

```
CLI (用户执行 python -m your_package.interfaces.cli)
  │
  ▼
UserService.register(id, name, email)      # 应用层：编排
  │
  ├──► User(id, name, email)               # 领域层：创建实体
  │
  ├──► user.is_valid_email()               # 领域层：业务校验
  │
  └──► UserRepository.save(user)           # 领域层接口 → infra 实现
```

### 数据格式

| 层间                         | 数据格式                         | 说明               |
| ---------------------------- | -------------------------------- | ------------------ |
| interfaces → application     | Python 原生类型 (str, int, dict) | 入口处解析         |
| application → domain         | 领域实体                         | 创建或传入实体     |
| domain → infrastructure      | 领域实体                         | 接口参数使用实体   |
| infrastructure → application | 领域实体或异常                   | 仓储返回值也是实体 |

**禁止**：在 domain 或 application 中 import requests、pandas、SQLAlchemy 等技术库。

---

## 6. 异常处理

```
infrastructure 异常
      │
      ▼  捕获并转换
  领域异常 (domain/exceptions.py)
      │
      ▼  向上传播
  application 层 捕获并决策（重试 / 降级 / 终止）
      │
      ▼
  interfaces 层 格式化为用户友好的错误信息
```

```python
# infrastructure/database/repositories/sqlite_user_repo.py
import sqlite3
from domain.exceptions import EntityNotFoundError


def find_by_id(self, user_id: str) -> Optional[User]:
    try:
        row = self._conn.execute(...).fetchone()
    except sqlite3.DatabaseError as e:
        raise DatabaseOperationError(f"查询用户失败: {e}") from e
    if row is None:
        raise EntityNotFoundError("User", user_id)
    return User(...)
```

---

## 7. 适用场景

| 场景                | 推荐度     | 原因                              |
| ------------------- | ---------- | --------------------------------- |
| 中大型长期维护项目  | ⭐⭐⭐⭐⭐ | 层间解耦，多人协作不影响          |
| 多数据源/多输出渠道 | ⭐⭐⭐⭐⭐ | 切换 DB/API 只需改 infrastructure |
| 需要单元测试覆盖    | ⭐⭐⭐⭐⭐ | 依赖注入天然可 Mock               |
| 快速原型 / 脚本     | ⭐         | 引入过重，建议用单文件            |

如果你当前项目规模较小，可以从 domain + application 两层开始，等到需要切换 DB 或加 API 时再补充 infrastructure 和 interfaces 层。

---

## 8. 设计原则检查清单

- [ ] **依赖方向严格单向**：domain ← application ← infrastructure ← interfaces
- [ ] **domain 层零外部依赖**：不 import 任何第三方库
- [ ] **仓储接口定义在 domain**：而非 infrastructure
- [ ] **实体使用 dataclass**：纯数据容器，不含 IO 逻辑
- [ ] **Service 通过构造器注入依赖**：不直接在方法内 new 对象
- [ ] **配置集中管理**：不散落在各模块硬编码
- [ ] **基础设施异常不跨层泄漏**：转换为领域异常后再抛出
- [ ] **每层目录职责明确**：不跨层引用
