# API 接口自动化（pytest）

按**业务模块**分子目录存放用例，与 [`tests/integration/`](../integration/README.md)（多步流程 / E2E）、`tests/pages/`（Page Object）区分。

## 目录约定

```text
tests/api/
├── README.md
├── basic_info/              # 基本信息管理（账户 / 产品 / 关系）
│   ├── test_basic_info_accounts.py
│   ├── test_basic_info_products.py
│   └── ...
└── _examples/               # 模板示例，默认不参与全量收集
    └── test_example.py
```

新增模块时创建 `tests/api/{模块名}/test_*.py` 即可。

## 常用命令

在仓库根目录 `ai_test_adm/` 下执行：

```bash
# 全量 API（不含 _examples）
pytest tests/api/ -v

# 单模块
pytest tests/api/basic_info/ -v

# 单文件
pytest tests/api/basic_info/test_basic_info_accounts.py -v

# Allure（结果目录见 pytest.ini）
pytest tests/api/basic_info/ -v --clean-alluredir
allure serve reports/allure-results

# 仅跑示例模板
pytest tests/api/_examples/ -v
```

或使用脚本：`powershell -File scripts/run_basic_info_allure.ps1`

## 环境

读取项目根目录 [`.env`](../../.env)（`BASE_URL`、`LOGIN_*`、`DB_*`、`POLAR_*`、`BASIC_INFO_FLOW_*` 等），详见 [`tests/conftest.py`](../conftest.py)。

测试点清单见 [`test_data/testpoints/`](../../test_data/testpoints/README.md)。
