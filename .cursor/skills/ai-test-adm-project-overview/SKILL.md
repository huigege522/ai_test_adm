---
name: ai-test-adm-project-overview
description: >
  AI辅助测试框架 ai_test_adm 完整指南 — 6阶段工作流、Prompt模板、pytest基础设施、
  MySQL/PolarDB/Playwright、ApiClient、HTML报告增强。适用于在 ai_test_adm 项目中
  编写/审查/执行测试、新增模块测试、或理解框架设计时加载。项目速览 / repo overview / where things live.
disable-model-invocation: true
---

# ai_test_adm — AI 辅助测试框架完整指南

## 项目概览

`ai_test_adm`（AI-Assisted Testing for Admin）是一个**AI 辅助接口+UI测试框架**，
目标系统为 Apple CMP（Competitive Mobile Platform）管理后台 (`https://adm.gm825.net`)。
核心功能涵盖 ASA/ASO 竞品信息分析（关键词探索、数据分析图表、分页关键词列表、探索历史）。

| 维度 | 说明 |
|------|------|
| 项目路径 | `D:\wanka\ai_test_adm\` |
| 技术栈 | Cursor AI + Apifox + pytest + MySQL + PolarDB + Playwright |
| 被测系统 | `https://adm.gm825.net` (Apple CMP 管理后台) |
| 用例数 | ~80+ 条测试函数，分布在 5 个测试文件中 |
| 代码量 | 测试代码 ~3200 行，基础设施 ~600 行 |

---

## 核心创新：6 阶段 AI 辅助测试工作流

框架的最大价值在于将测试工程过程分解为 **6 个标准化阶段**，每个阶段配有结构化 Prompt 模板，
AI 按模板生成测试资产，形成可复制、可推广的"AI + 测试工程"协作范式。

### 阶段总览

| 阶段 | Prompt 文件 | 输入 | 输出 | 一句话 |
|------|------------|------|------|--------|
| 一 | `01_req_to_testpoints.md` | 需求文档/PRD | `test_data/testpoints/{模块}/testpoints_*.md` | 需求 → 测试点清单 |
| 二-A | `02_apifox_to_cases.md` | Apifox 接口定义 | `tests/api/{模块}/test_*.py` | 接口定义 → API 用例 |
| 二-B | `03_code_to_cases.md` | Service/Controller 源码 | 追加分支用例 | 代码分析 → 未覆盖分支 |
| 三 | `04_db_schema_to_testdata.md` | MySQL CREATE TABLE | `test_data/sql/{模块}/*.sql` + fixture | Schema → 测试数据 |
| 四 | `05_assert_generation.md` | 用例骨架 + 响应结构 | HTTP/DB/Schema 断言 | 完善断言 |
| 五 | `06_e2e_ui_flow.md` | 测试点 P0 + 路由 | `tests/pages/` + `test_*_e2e.py` | UI 端到端 |
| 六 | `07_defect_analysis.md` | 失败日志、变更 | 根因、回归清单 | 缺陷分析 |

### 推荐执行顺序

```
收到需求
  └→ [阶段一] 提取测试点清单
       ├→ [阶段二-A/二-B] API 与分支用例
       │     └→ [阶段三] 测试数据 + fixture
       │          └→ [阶段四] 完善 API 断言 → 执行 pytest
       └→ [阶段五]（可并行）UI E2E：圈 P0 路径 → Page/用例 → pytest -m e2e
                └→ 失败或变更 → [阶段六] 根因与回归 → 更新用例/测试点
```

### 分工原则

- **API/分支（阶段二～四）**：侧重契约、参数、边界、权限、错误码、代码分支
- **UI E2E（阶段五）**：侧重浏览器主路径、登录态、路由、关键交互闭环
- **同一个业务现象**：API 证明后端契约，E2E 证明用户能点通

### 极简路径（约 80% 场景）

不必一次跑满 01～07，常用最短路径：

1. **需求** → 用 `01` 拉测试点
2. **接口自动化** → 用 `02` 生成 `tests/api/`，直接 `pytest tests/api/`
3. **挂了** → 用 `07` 分析根因

**按需加餐：**
- `03`：文档不全，需要代码找未覆盖分支时
- `04`：需要 `test_data/sql/{模块}/baseline.sql`、写库断言或 E2E 依赖固定数据时
- `05`：用例只有骨架，要系统性补断言时
- `06`：需要浏览器 P0 主路径时

---

## 目录结构

```
ai_test_adm/
├── prompts/                          # 【核心】AI Prompt 模板
│   ├── 00_README.md                  # 阶段总览 + Mermaid 流程图 + 命令速查
│   ├── 01_req_to_testpoints.md       # 阶段一：需求 → 测试点（4维度）
│   ├── 02_apifox_to_cases.md         # 阶段二-A：Apifox → pytest 用例
│   ├── 03_code_to_cases.md           # 阶段二-B：代码分支分析 → 未覆盖用例
│   ├── 04_db_schema_to_testdata.md   # 阶段三：Schema → 测试数据 SQL + fixture
│   ├── 05_assert_generation.md       # 阶段四：断言补全（HTTP/DB/Schema）
│   ├── 06_e2e_ui_flow.md             # 阶段五：UI E2E（Playwright）
│   └── 07_defect_analysis.md         # 阶段六：缺陷根因 & 回归分析
│
├── tests/
│   ├── conftest.py                   # 全局 fixture（DB/认证/报告增强/Playwright）
│   ├── utils/api_client.py           # HTTP 封装 + 6 种断言辅助方法
│   ├── api/                          # 按模块分子目录，见 api/README.md
│   │   ├── basic_info/               # 基本信息管理 test_basic_info_*.py
│   │   └── _examples/                # 模板 test_example.py（默认不收集）
│   ├── integration/                  # 按模块分子目录，见 integration/README.md
│   │   ├── basic_info/               # HTTP 流程 + 浏览器 E2E
│   │   ├── competitor/               # 竞品分析 E2E
│   │   └── _examples/                # 流程模板（默认不收集）
│   └── pages/                        # Playwright Page Object
│
├── test_data/
│   ├── sql/                          # 数据库造数脚本，见 sql/README.md
│   │   ├── shared/                   # load_baseline 默认 baseline + cleanup
│   │   └── {模块}/                   # 如 basic_info/
│   ├── testpoints/                   # 阶段一产物（Markdown / Excel）
│   │   ├── basic_info/               # 测试点 Markdown / Excel
│   │   └── {模块}/                   # testpoints_*.md
│   └── bug_tracker.md                # （可选）缺陷记录
│
├── doc/                              # 辅助文档（如 req_text.txt）
├── reports/                          # HTML/Allure 报告输出目录
├── .env.example                      # 环境变量模板
├── pytest.ini                        # 6 个自定义 marker + 日志/报告配置
├── requirements.txt                  # 12 个依赖
├── README.md                         # 项目说明
└── ai_test_adm_评估报告.md            # 框架评估报告
```

---

## 分层架构

框架采用清晰的四层架构：

```
┌──────────────────────────────────────────┐
│  Prompt Layer (prompts/)                 │ ← AI 协作规范层（人类可读、AI 可执行）
├──────────────────────────────────────────┤
│  Test Case Layer (tests/api/, integration/)│ ← 测试逻辑层（按接口/流程组织）
├──────────────────────────────────────────┤
│  API Client Layer (tests/utils/)         │ ← 工具封装层（HTTP + 断言）
├──────────────────────────────────────────┤
│  Fixture Layer (tests/conftest.py)       │ ← 基础设施层（DB/认证/报告）
└──────────────────────────────────────────┘
```

---

## 基础设施详解

### conftest.py 核心 Fixture

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `db_pool` | session | MySQL 连接池（会话级单连接模拟） |
| `db_conn` | function | 函数级事务隔离，结束自动回滚 |
| `db_cursor` | function | DictCursor，基于 db_conn |
| `load_baseline` | function | 执行 `test_data/sql/shared/baseline.sql` 插入 + `shared/cleanup.sql` 清理 |
| `polar_db_pool` | session | PolarDB 连接（未配置时自动 skip） |
| `polar_db_conn` | function | 函数级 PolarDB 事务 |
| `polar_db_cursor` | function | PolarDB DictCursor |
| `login_session` | session | 已完成认证的 Session（三级降级链） |
| `http_session` | session | 无认证的基础 Session |
| `playwright_browser` | session | Chromium 浏览器实例（headless） |
| `playwright_page` | function | 携带认证 Cookie 的 Page |
| `competitor_explore_page` | function | 竞品分析-探索页面对象 |

### 认证三级降级链

```python
# 优先级：
# 1. LOGIN_USERNAME + LOGIN_PASSWORD → POST /api/login/sub2 自动登录
# 2. AUTH_COOKIE → 直接注入 Cookie 请求头
# 3. 均未配置 → pytest.skip
```

测试环境验证码通过 `{"ticket": "1234", "randstr": "1234"}` 绕过。

### HTML 报告增强（pytest_runtest_makereport）

conftest.py 中的 `pytest_runtest_makereport` hook 自动生成结构化 HTML 报告，包含：

1. **结果徽章**：PASSED/FAILED/SKIPPED 彩色标签
2. **用例说明**：docstring 渲染为卡片
3. **HTTP 请求/响应详情表**：每次调用的 Method/URL/Status/请求体/响应 JSON
4. **断言步骤明细**：每步 PASS/FAIL 状态 + 详情（需在测试模块中维护 `_assert_steps` 列表）
5. **失败详情**：AssertionError 完整文本

### ApiClient 断言方法

| 方法 | 用途 |
|------|------|
| `assert_status(resp, expected)` | HTTP 状态码断言，错误信息含响应体前 500 字符 |
| `assert_business_code(resp, field, expected)` | 业务码字段断言（如 `"code"` = 0） |
| `assert_field_exists(resp, *fields)` | 可变参数，断言多个字段存在（支持点号路径） |
| `assert_json_field(resp, field, check_fn)` | 自定义 lambda 断言（支持 `data.list.0.name`） |
| `assert_schema(resp, schema)` | jsonschema 验证响应结构 |

---

## .env 配置项

```
BASE_URL                    # 被测系统地址
DB_HOST / PORT / NAME / USER / PWD  # MySQL 配置
POLAR_DB_HOST / PORT / NAME / USER / PWD  # PolarDB（可选）
LOGIN_USERNAME / PASSWORD   # 自动登录凭证
AUTH_COOKIE                 # 手动 Cookie（备用）
LOW_PERM_USERNAME / PASSWORD # 越权测试用低权限账号
REQUEST_TIMEOUT             # 请求超时（默认10秒）
```

---

## pytest.ini 自定义标记

| Marker | 用途 |
|--------|------|
| `smoke` | 冒烟测试，P0 核心流程 |
| `regression` | 回归测试 |
| `boundary` | 边界值测试 |
| `negative` | 异常/负向测试 |
| `db` | 需要数据库连接的测试 |
| `e2e` | E2E UI 自动化测试 |

---

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 配置环境
cp .env.example .env
# 编辑 .env 填写真实配置

# 运行全部测试
pytest tests/ -v

# 只运行冒烟测试（P0）
pytest tests/ -m smoke -v

# 并行运行
pytest tests/ -n auto -v

# 仅 UI E2E
pytest tests/integration/ -v -m e2e

# 生成 HTML 报告
pytest tests/ --html=reports/report.html --self-contained-html

# 生成 Allure 报告
pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results

# 单文件执行
pytest tests/api/test_keyword.py -v
```

---

## 新增模块测试（标准步骤）

1. @ 需求文档，使用 `prompts/01_req_to_testpoints.md` 生成测试点
2. 使用 `prompts/02_apifox_to_cases.md` 生成 `tests/api/test_[模块名].py`（可选 `03` 补分支）
3. 使用 `prompts/04_db_schema_to_testdata.md` 更新 `test_data/sql/{模块}/baseline.sql`（按需）
4. 使用 `prompts/05_assert_generation.md` 补全 **API** 断言
5. （可选）需要 **UI 主路径** 时，使用 `prompts/06_e2e_ui_flow.md` 落地 Playwright E2E
6. 运行 `pytest tests/api/[模块名]/ -v`；若有 E2E 再跑 `pytest tests/integration/ -v -m e2e`

---

## 代码约定

- 测试函数名用中文：`def test_正常创建用户(self)`
- 使用 `@pytest.mark.parametrize` 合并同类边界值/类型错误用例
- 每个 class 对应一个接口，命名如 `TestUserCreate`
- 在测试文件顶部注明接口路径和 Apifox 接口 ID
- 测试数据使用 `test_` 前缀，与生产数据隔离
- `.env` 不提交 Git（已在 .gitignore 忽略）
- `conftest.py` 中 fixture 使用 `scope="function"` 保证用例间数据独立
- AI 生成的用例需要人工审核业务逻辑

---

## 已知改进点

参考 `ai_test_adm_评估报告.md`：

| 问题 | 严重度 | 建议 |
|------|--------|------|
| 僵尸依赖（pytest-ordering, faker, jsonschema 未实际使用） | 低 | 落地使用或移除 |
| 单文件过大（`test_asa_aso_competitor.py` 1815行） | 中 | 按接口拆分为 4 个文件 |
| 全局状态并发风险（`_http_calls`、`_assert_steps` 模块级列表） | 中 | 改用 `request.node.stash` 或 thread-local |
| `_assert_param_error` 断言过于宽松 | 低 | 区分 400/422/业务错误 |
| 无 CI/CD 集成配置 | 中 | 添加 GitHub Actions 或 Jenkinsfile |
| 无失败重试机制 | 低 | 集成 pytest-rerunfailures |
| Prompt 模板缺少非功能测试维度 | 中 | 在 01 加入性能/安全/兼容性维度 |
| 集成测试覆盖不足 | 中 | 增加跨模块全链路 E2E 流程 |

---

## 依赖清单

```
pytest==8.3.5           # 核心测试框架
pytest-html==4.1.1      # HTML 报告（与 conftest 深度集成）
pytest-xdist==3.6.1     # 并行执行
pytest-ordering==0.6    # 用例排序（未实际使用）
requests==2.32.3        # HTTP 请求
pymysql==1.1.1          # MySQL 连接
python-dotenv==1.0.1    # 环境变量
allure-pytest==2.13.5   # Allure 报告（未完全集成）
faker==26.0.0           # 测试数据生成（未实际使用）
jsonschema==4.23.0      # Schema 验证（已集成，用例中未用）
playwright>=1.44.0      # 浏览器自动化
pytest-playwright>=0.4.3 # Playwright pytest 集成
```

---

## 注意事项

1. `.env` 文件不要提交到 Git
2. 测试数据使用 `test_` 前缀，测试库与生产库严格隔离
3. AI 生成的用例需要人工审核业务逻辑是否准确
4. 禁止在生产数据库执行 `test_data/sql/**/baseline.sql`
5. 外键约束顺序：先插入主表数据，再插入从表数据；cleanup 反向删除
6. Playwright 定位器优先使用 `data-testid`、稳定的 `aria`/`role`
7. 阅懂项目从 `prompts/00_README.md` 开始，按数字 `01` → `07` 浏览
