# 测试数据 SQL（阶段三产物）

按**业务模块**分子目录存放 `baseline.sql` / `cleanup.sql` 配对脚本，与 `tests/api/{模块}/`、`test_data/testpoints/{模块}/` 目录名对齐。

## 目录约定

```text
test_data/sql/
├── README.md
├── shared/                    # 通用示例（load_baseline fixture 默认加载）
│   ├── baseline.sql           # MySQL：cmp_apple_market 等
│   └── cleanup.sql
└── basic_info/                # 基本信息管理（PolarDB 扩展表）
    ├── baseline.sql           # apple_org_ext、apple_app_ext、apple_app_org_attr
    ├── cleanup.sql
    └── notes.sql              # FLOW 环境变量说明（非 pytest 自动加载）
```

## 目标库

| 目录 | 连接 | 说明 |
|------|------|------|
| `shared/` | MySQL（`.env` 中 `DB_*`） | `pytest` 的 `load_baseline` fixture 自动执行 |
| `basic_info/` | PolarDB（`POLAR_*`） | 手动或在 Polar 测试库执行；`adam_id` fixture 风格一致 |

**禁止在生产库执行。**

## 常用操作

```bash
# MySQL 测试库（与 load_baseline 一致）
mysql -h $DB_HOST -u $DB_USER -p $DB_NAME < test_data/sql/shared/baseline.sql
mysql -h $DB_HOST -u $DB_USER -p $DB_NAME < test_data/sql/shared/cleanup.sql

# PolarDB 测试库（基本信息扩展表）
mysql -h $POLAR_DB_HOST ... < test_data/sql/basic_info/baseline.sql
mysql -h $POLAR_DB_HOST ... < test_data/sql/basic_info/cleanup.sql
```

新增模块时创建 `test_data/sql/{模块目录}/baseline.sql` + `cleanup.sql`，并在 `tests/conftest.py` 或模块 fixture 中引用路径。
