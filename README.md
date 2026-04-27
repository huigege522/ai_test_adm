# AI 辅助测试框架 — ai_test_adm

技术栈：**Cursor AI + Apifox + pytest + MySQL**

---

## 项目结构

```
ai_test_adm/
├── prompts/                        # 五个阶段的 AI Prompt 模板（核心）
│   ├── 01_req_to_testpoints.md     # 阶段一：需求文档 → 测试点提取
│   ├── 02_apifox_to_cases.md       # 阶段二-A：Apifox → pytest 用例
│   ├── 03_code_to_cases.md         # 阶段二-B：代码库 → 分支覆盖用例
│   ├── 04_db_schema_to_testdata.md # 阶段三：MySQL Schema → 测试数据
│   ├── 05_assert_generation.md     # 阶段四：断言生成 & 执行命令
│   └── 06_defect_analysis.md       # 阶段五：缺陷分析 & 回归建议
│
├── tests/
│   ├── conftest.py                 # 全局 fixture：MySQL 连接、HTTP Session
│   ├── api/
│   │   └── test_example.py         # API 接口测试示例（用户模块参考模板）
│   ├── integration/
│   │   └── test_flow_example.py    # 端到端流程测试示例
│   └── utils/
│       └── api_client.py           # 封装 HTTP 请求 + 断言辅助方法
│
├── test_data/
│   ├── baseline.sql                # 基准测试数据（INSERT）
│   └── cleanup.sql                 # 数据清理（DELETE）
│
├── reports/                        # 测试报告输出目录（HTML/Allure）
├── .env.example                    # 环境变量模板
├── pytest.ini                      # pytest 配置
└── requirements.txt                # Python 依赖
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
copy .env.example .env
# 编辑 .env，填写真实的 BASE_URL、数据库连接、Token 等
```

### 3. 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 只运行冒烟测试（P0）
pytest tests/ -m smoke -v

# 并行运行（加速）
pytest tests/ -n auto -v

# 生成 HTML 报告
pytest tests/ --html=reports/report.html --self-contained-html
```

---

## 五阶段工作流（AI 辅助）

| 阶段 | 输入 | AI Prompt | 输出 |
|------|------|-----------|------|
| 一：测试点提取 | 需求文档 + 代码库 | `prompts/01_req_to_testpoints.md` | 结构化测试点清单 |
| 二-A：API 用例 | Apifox 接口文档 | `prompts/02_apifox_to_cases.md` | `tests/api/test_*.py` |
| 二-B：分支用例 | 代码库 | `prompts/03_code_to_cases.md` | 追加至 `tests/api/` |
| 三：测试数据 | MySQL Schema | `prompts/04_db_schema_to_testdata.md` | `test_data/*.sql` + fixture |
| 四：断言完善 | 已有用例骨架 | `prompts/05_assert_generation.md` | 完整断言 + 数据库验证 |
| 五：缺陷分析 | 失败用例 + 代码 | `prompts/06_defect_analysis.md` | 根因报告 + 回归清单 |

### 推荐工作顺序

```
收到需求
  └→ [阶段一] 提取测试点清单
       └→ [阶段二-A] Apifox → 批量生成 API 用例骨架
            └→ [阶段三] 数据库 Schema → 生成测试数据 + fixture
                 └→ [阶段四] 完善断言 → 可运行
                      └→ 执行 pytest → 发现失败
                           └→ [阶段五] AI 分析根因 → 提 Bug
                                └→ 需求变更 → [阶段五] 回归分析 → 更新用例
```

---

## 新增模块测试（标准步骤）

1. 打开 Cursor，@ 需求文档，使用 `prompts/01_req_to_testpoints.md` 生成测试点
2. 通过 Apifox MCP 或粘贴接口定义，使用 `prompts/02_apifox_to_cases.md` 生成 `tests/api/test_[模块名].py`
3. 导出 MySQL 建表语句，使用 `prompts/04_db_schema_to_testdata.md` 更新 `test_data/baseline.sql`
4. 使用 `prompts/05_assert_generation.md` 为用例补全断言
5. 运行 `pytest tests/api/test_[模块名].py -v` 验证

---

## 注意事项

- `.env` 文件不要提交到 Git（已在 .gitignore 中忽略）
- 测试数据使用 `test_` 前缀，测试库与生产库严格隔离
- `conftest.py` 中所有 fixture 使用 `scope="function"`，保证用例间数据独立
- AI 生成的用例需要人工审核业务逻辑是否准确
