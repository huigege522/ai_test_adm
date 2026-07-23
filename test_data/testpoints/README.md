# 测试点清单（阶段一产物）

按**业务模块**分子目录存放 Markdown / Excel 测试点，与 `tests/api/{模块}/`、`tests/integration/{模块}/` 目录名对齐。

## 目录约定

```text
test_data/testpoints/
├── README.md
├── basic_info/                              # 基本信息管理
│   ├── testpoints_基本信息管理.md            # 主清单（TC001…）
│   ├── testpoints_基本信息管理_后端分支覆盖对照.md
│   ├── testpoints_基本信息管理_代码风险对照.md
│   └── testpoints_基本信息管理_前端代码风险对照.md
└── {模块目录}/                              # 新模块按同样方式扩展
    └── testpoints_{模块显示名}.md
```

**模块目录名**建议与自动化一致：`basic_info`、`competitor` 等（英文 snake_case）。

## 常用操作

```bash
# 同步主清单「自动化是否覆盖」列（基本信息管理）
python scripts/update_testpoint_coverage.py

# 统计覆盖情况
python scripts/coverage_stats.py
```

## 与自动化对应关系

| 测试点清单 | API 用例 | 集成 / E2E |
|-----------|----------|------------|
| `basic_info/testpoints_基本信息管理.md` | `tests/api/basic_info/` | `tests/integration/basic_info/` |

生成新模块清单时，使用 `prompts/01_req_to_testpoints.md`，保存路径：

`test_data/testpoints/{模块目录}/testpoints_{模块显示名}.md`

造数 SQL 见 [`test_data/sql/`](../sql/README.md)。
