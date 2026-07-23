# 集成 / E2E 自动化（pytest）

按**业务模块**分子目录存放用例，与 `tests/api/`（单接口）、`tests/pages/`（Page Object）区分。

## 用例类型

| 类型 | 命名 | 说明 |
|------|------|------|
| HTTP 集成流 | `test_*_flow.py` | 多接口串联（ApiClient + Cookie），标记 `@pytest.mark.integration` |
| 浏览器 E2E | `test_*_e2e.py` | Playwright 主路径，标记 `@pytest.mark.e2e` |

## 目录约定

```text
tests/integration/
├── README.md
├── basic_info/              # 基本信息管理
│   ├── test_basic_info_management_flow.py   # TC401–408 等 HTTP 流程
│   └── test_basic_info_management_e2e.py    # 浏览器 E2E
├── competitor/              # 竞品分析
│   └── test_competitor_e2e.py
└── _examples/               # 流程模板，默认不参与全量收集
    └── test_flow_example.py
```

新增模块时创建 `tests/integration/{模块名}/test_*.py` 即可。

## 常用命令

在仓库根目录 `ai_test_adm/` 下执行：

```bash
# 全量集成（不含 _examples）
pytest tests/integration/ -v

# 仅 HTTP 集成流
pytest tests/integration/ -v -m integration

# 仅浏览器 E2E
pytest tests/integration/ -v -m e2e

# 单模块
pytest tests/integration/basic_info/ -v

# 单文件
pytest tests/integration/basic_info/test_basic_info_management_flow.py -v

# 仅跑示例模板
pytest tests/integration/_examples/ -v
```

## 环境

- **HTTP 流程**：`BASE_URL`、`LOGIN_*`、`BASIC_INFO_FLOW_*` 等（与 API 用例相同），见 [`.env`](../../.env)。
- **浏览器 E2E**：另需 `PLAYWRIGHT_BASE_URL`（前端 SPA 地址），Cookie 域名须与其一致。
