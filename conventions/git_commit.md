# Git 提交规范

> 本文档用于指导 **AI Agent** 和开发者遵循统一的 Git 提交规范。
> Agent 在执行 git commit 操作前必须完整阅读并遵守本文件的所有规则。

---

## 1. 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**规则：**

| 部分      | 要求                                                        |
| --------- | ----------------------------------------------------------- |
| `type`    | **必填**，见下方 type 列表                                  |
| `scope`   | **选填**，但推荐填写。不加 scope 时不带括号                 |
| `subject` | **必填**，中文描述，不超过 50 字，**句尾不加句号**          |
| `body`    | **选填**。需要细节说明时填写。使用无序列表 `- xxx` 分行列举 |
| `footer`  | **选填**。BREAKING CHANGE 或关联 issue                      |

**注意：**

- `type` 后必须跟**英文冒号 + 空格**
- `scope` 用英文括号包裹，与 type 之间**无空格**
- subject 首行与 body 之间**空一行**

---

## 2. type 类型

| type       | 说明     | 使用条件                                                  |
| ---------- | -------- | --------------------------------------------------------- |
| `feat`     | 新功能   | 新增函数、类、模块、接口                                  |
| `fix`      | 修复 bug | 修复逻辑错误、异常、数据错误                              |
| `docs`     | 文档     | 仅修改 .md 文件、注释，不涉及代码逻辑                     |
| `style`    | 格式     | 缩进、分号、空行、import 排序等，不影响运行逻辑           |
| `refactor` | 重构     | 重命名变量/函数、拆分模块、提取公共方法等，不改变外部行为 |
| `perf`     | 性能优化 | 减少耗时、降低内存占用等                                  |
| `test`     | 测试     | 新增或修改单元测试、集成测试                              |
| `chore`    | 杂项     | .gitignore、依赖管理、CI 配置等**不涉及业务代码**的变更   |
| `ci`       | CI/CD    | GitHub Actions、Jenkins pipeline 等                       |
| `revert`   | 回退     | 撤销之前的提交                                            |

**选择规则：** 一个 commit 如果同时包含 `feat` 和 `fix`，按 `feat` 算；如果同时包含 `feat` 和 `docs`（改代码同时改注释），按 `feat` 算。

---

## 3. scope 可选范围

本项目 scope 映射表：

| scope          | 对应文件/目录                             | 示例                                     |
| -------------- | ----------------------------------------- | ---------------------------------------- |
| `data-fetcher` | `data_fetcher.py` 及数据库相关            | `feat(data-fetcher): 添加龙虎榜抓取函数` |
| `conventions`  | `conventions/` 目录下的所有规约文档       | `docs(conventions): 补充代码风格规范`    |
| `config`       | `.gitignore`、`pyproject.toml` 等配置文件 | `chore(config): 添加 .gitignore`         |
| `deps`         | `requirements.txt` 依赖变更               | `chore(deps): 添加 akshare 依赖`         |
| `app`          | 主应用入口（如 `main.py`、app 模块）      | `feat(app): 添加定时调度功能`            |

如果不涉及以上任何范围，可不写 scope。

---

## 4. 提交前检查清单

Agent 在每次执行 `git commit` 前必须按顺序检查以下项目：

### 4.1 文件检查

- [ ] **不提交** 数据库文件（`*.db`）、数据文件（`*.csv`, `*.xlsx`）
- [ ] **不提交** 虚拟环境目录（`.venv/`, `venv/`, `env/`）
- [ ] **不提交** 编译产物（`__pycache__/`, `*.pyc`, `*.egg`）
- [ ] **不提交** IDE 配置（`.vscode/`, `.idea/`）
- [ ] **不提交** `.env`、`*.key` 等可能包含敏感信息的文件
- [ ] **不提交** 日志文件（`*.log`）
- [ ] **不提交** 操作系统文件（`.DS_Store`, `Thumbs.db`）

> 以上文件应已在 `.gitignore` 中声明。若发现未声明，则先更新 `.gitignore`。

### 4.2 变更检查

- [ ] 检查 `git status`，**只 add 与本次提交相关的文件**，禁止使用 `git add -A` 或 `git add .`
- [ ] 检查 `git diff --cached`，确认每处改动都是预期的
- [ ] 代码中**不得包含**调试用的 `print()`、`breakpoint()`、`import pdb`
- [ ] 代码中**不得包含**测试用的硬编码 token、密码、URL

### 4.3 提交粒度

- **一个 commit 只做一件事**。新功能和 bug 修复必须在不同 commit
- 如果修改涉及多个不相关文件，应拆分为多个 commit 分别提交
- 代码格式化（style）不应与功能修改混在同一个 commit

---

## 5. 提交流程（Agent 必须遵守）

> 本流程适用于 AI Agent 执行 git commit 操作。

### Step 1: 检查当前状态

```bash
git status
git diff
git log --oneline -5
```

分析当前变更，确定：

- 变更了哪些文件
- 变更的性质（feat/fix/docs/chore 等）
- 对应的 scope

### Step 2: 暂存文件

```bash
git add <file1> <file2> ...
```

**禁止：** `git add -A` / `git add .` / `git add --all`

**允许的例外：** 当新增/修改的文件超过 10 个且全部属于同一 scope 时，可使用带路径的 `git add <dir>/`。

### Step 3: 构造提交信息

1. 根据变更内容确定 type 和 scope
2. subject 用中文，50 字以内，句尾无句号
3. 需要细节时，在 body 中用 `- xxx` 分行列举
4. 描述 focus 在 **"为什么要改"** 而非 **"改了什么"**

### Step 4: 提交

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

- <detail 1>
- <detail 2>
EOF
)"
```

### Step 5: 验证

```bash
git status
```

确认工作区干净，commit 成功。

---

## 6. 提交信息示例

### 新增功能

```
feat(data-fetcher): 添加北向资金流入数据抓取

- 实现 fetch_north_fund() 函数
- 写入 north_fund_flow 表
- 支持 INSERT OR REPLACE 去重
```

### 修复 Bug

```
fix(data-fetcher): 修复 akshare 日线日期类型错误

akshare 返回的日期为 Timestamp 类型
入库前未调用 strftime 转换导致写入失败
```

### 配置文件变更

```
chore(config): 添加 .gitignore 及 conventions 目录
```

### 仅文档变更

```
docs(conventions): 补充 git 提交规范文档
```

### 重构

```
refactor(data-fetcher): 提取公共数据库连接函数

将散落在各抓取函数中的 sqlite3.connect 调用统一为 get_db_connection()
```

---

## 7. 分支命名规范

本项目使用简单分支策略：

| 分支          | 用途                                |
| ------------- | ----------------------------------- |
| `main`        | 主分支，保持稳定可运行              |
| `feat/<描述>` | 功能开发分支，如 `feat/lhb-module`  |
| `fix/<描述>`  | 修复分支，如 `fix/date-parse-error` |

功能完成后通过 merge 合并到 main，**禁止直接 push 到 main**。

---

## 8. Push 规则

- [ ] push 前确认当前分支**已提交所有变更**
- [ ] **禁止** `git push --force` / `git push --force-with-lease`，除非用户明确要求
- [ ] **禁止** push 到 `main` / `master` 分支
- [ ] 如果 push 失败（远程有新的变更），使用 `git pull --rebase` 而不是 force push
