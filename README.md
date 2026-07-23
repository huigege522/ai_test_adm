# AI 辅助测试框架 — ai_test_adm

技术栈：**Cursor AI + pytest + MySQL + Playwright（UI E2E）**

---

## 项目结构

```
ai_test_adm/
├── prompts/                         # AI Prompt 模板
│   ├── main.md                     # 【主 Prompt】需求 → 用例一步到位
│   ├── 03_code_to_cases.md         # 代码分支 → 补充用例（按需）
│   ├── 04_db_schema_to_testdata.md # Schema → 测试数据（按需）
│   ├── 06_e2e_ui_flow.md           # UI E2E（Playwright）（按需）
│   └── 07_defect_analysis.md       # 缺陷分析 & 回归（按需）
│
├── tests/
│   ├── conftest.py                 # 入口，引用 conftest_plugins/ 子模块
│   ├── conftest_plugins/
│   │   ├── db.py                   # DB fixtures（MySQL、PolarDB、adam_id）
│   │   ├── auth.py                 # Auth + Playwright fixtures
│   │   └── report.py               # pytest-html 报告增强
│   ├── utils/api_client.py         # HTTP 请求 + 断言封装
│   ├── helpers/                    # 模块级断言复用
│   ├── api/                        # API 测试用例
│   │   ├── _examples/              # 用例模板参考
│   │   └── basic_info/             # 基本信息管理模块
│   ├── integration/                # E2E 流程测试
│   └── pages/                      # Playwright Page Object
│
├── test_data/
│   ├── sql/                        # 数据库 baseline / cleanup 脚本
│   ├── testpoints/                 # 测试点清单（阶段一产物）
│   └── bug_tracker.md              # 缺陷追踪记录
│
├── reports/                        # 测试报告输出
├── .env.example                    # 环境变量模板
├── pytest.ini                      # pytest 配置
└── requirements.txt                # Python 依赖
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium   # 仅运行 UI E2E 时需要
```

### 2. 配置环境

```bash
copy .env.example .env
# 编辑 .env，填写真实的 BASE_URL、数据库连接、登录账号等
```

### 3. 运行测试

```bash
# API 测试
pytest tests/api/ -v

# 冒烟测试
pytest tests/ -m smoke -v

# UI E2E
pytest tests/integration/ -v -m e2e

# 并行 + HTML 报告
pytest tests/ -n auto -v --html=reports/report.html --self-contained-html
```

---

## 日常使用流程

### 主路径：一个 Prompt 搞定

```
拿到需求 → 粘贴需求 + prompts/main.md → AI 输出测试点清单 + pytest 文件
         → 保存到 tests/api/[模块]/ → pytest tests/api/[模块]/ -v
```

### 挂了怎么办

```
pytest 失败 → 粘贴失败日志 + prompts/07_defect_analysis.md + @ 代码 → AI 定位根因
```

### 需要测 UI 主路径

```
从测试点清单圈 P0 浏览器路径 → prompts/06_e2e_ui_flow.md → Playwright E2E 用例
```

---

## 新增模块测试（标准步骤）

1. @ 需求文档，使用 `prompts/main.md` 一键生成测试点 + 用例
2. 将生成的用例保存到 `tests/api/[模块名]/`
3. 运行 `pytest tests/api/[模块名]/ -v`
4. （可选）需要 UI 主路径时，使用 `prompts/06_e2e_ui_flow.md`

---

## 注意事项

- `.env` 不要提交到 Git（已在 .gitignore 中忽略）
- 测试库与生产库严格隔离
- `conftest` 中所有 fixture 使用 `scope="function"`，保证用例间数据独立
- AI 生成的用例需要人工审核业务逻辑是否准确
