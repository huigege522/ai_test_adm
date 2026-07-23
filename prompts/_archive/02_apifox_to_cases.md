# 阶段二-A：Apifox 接口文档 → pytest 测试用例生成

**全景位置**：[00_README.md](00_README.md)。本阶段产出 **API/HTTP** 用例；**浏览器主路径**由 **阶段五 [06_e2e_ui_flow.md](06_e2e_ui_flow.md)** 覆盖，二者互补：接口侧做参数、边界、权限与错误码，UI E2E 做 P0 交互闭环。

**使用场景**：从 Apifox 获取接口定义后，让 AI 批量生成覆盖全面的 pytest 用例。  
**在 Cursor 中使用**：通过 Apifox MCP 直接读取，或粘贴接口 JSON 定义。

---

## ADM 实测响应约定（生成用例前必读）

被测系统为 **Apple CMP ADM**（`BASE_URL`，如 `https://adm.gm825.net`）时，**不要默认** OpenAPI/REST 常见的「参数错误 = HTTP 400/422」。以**线上实测**为准：

| 场景 | 常见 HTTP | 业务体 | 断言方式 |
|------|-----------|--------|----------|
| 成功 | 200 | `code: 0` | `assert_status(200)` + `assert_business_code(resp, "code", 0)` |
| 参数缺失/类型/枚举/边界校验失败 | **200** | `code: -1`，`data.{字段}: ["validation.*"]` | **`assert_validation_error(resp, "字段名")`** |
| 无会话 | 401 或 200 | `code: -1`，`message` 含 Unauthorized | `assert_http_401_or_403(resp, expect_403=False)` |
| 低权限 | 200 或 401/403 | `code: -1`，`message` 含 Unauthorized | `assert_http_401_or_403(resp, expect_403=True)` |
| 导出 `export=1` | 200 + JSON | `code: 0` 提示离线下载中心，或 `code: -1` 防重 | 勿断言「非 JSON 文件流」；见 `test_basic_info_management.py` 导出用例 |

共享断言见 `tests/helpers/basic_info_http.py`：

- `assert_validation_error(resp, *fields)` — 负向参数/边界（**优先于** `assert_http_4xx`）
- `assert_http_401_or_403(resp, expect_403=...)` — 鉴权失败
- `assert_http_4xx` — 仅当**实测**确认为 400/422 时使用（ADM 基本信息管理模块极少）

生成用例时：**负向校验默认写 `assert_validation_error`**，并在 docstring 注明「实测 HTTP 200 + code=-1」。若 Apifox 仍写 422，以**运行环境实测**为准更新断言，而非照抄文档。

---

## 方式一：通过 Apifox MCP 直接读取（推荐）

```
@[接口文档]

参考以上接口文档，生成完整的 pytest 测试类

要求：
1. 【正常场景】HTTP 200 + 业务码 code=0 + 关键字段存在性断言
2. 【参数缺失/类型/边界非法】期望校验失败：HTTP 200 + code=-1 且 data 含对应字段错误；
   使用 assert_validation_error(resp, "字段名")，不要默认 assert_http_4xx
3. 【参数类型错误】在合法基线 body 上只改一个字段为错误类型，再 assert_validation_error
4. 【边界值场景】超长、枚举越界、空数组等 — 同上，按实测 assert_validation_error（个别非法类型可能 500，可 allow_500=True）
5. 【越权场景】无会话 → assert_http_401_or_403(expect_403=False)；低权限 → expect_403=True
6. 【导出 export=1】若实测为异步离线下载（JSON code=0 + 提示文案），勿断言 Content-Type 非 json

代码规范：
- 使用 tests/utils/api_client.py 中的 ApiClient 类
- 基本信息管理模块优先复用 tests/helpers/basic_info_http.py 中的断言与会话 fixture 模式
- 使用 @pytest.mark.parametrize 合并同类边界值用例
- 每个 class 对应一个接口或资源，命名如 TestOrgList
- 添加中文描述的函数名，如 def test_正常获取账户列表_JSON分页(self)
- 在文件顶部注明接口路径、Apifox 接口 ID（若有）、ADM 响应约定摘要

输出为完整可运行的 Python 文件内容。
生成文件保存至：tests/api/test_[模块名].py
```

---

## 方式二：粘贴接口定义（Apifox 导出的 JSON 或手工描述）

```
以下是接口定义，请生成完整的 pytest 测试用例：

接口名称：[接口名]
请求方法：[GET/POST/PUT/DELETE]
路径：[/api/xxx]
请求参数：
  - 参数名 | 类型 | 是否必填 | 说明 | 约束
  [逐行列出]
响应结构：
  成功：{"code": 0, "data": {...}, "message": "成功"}
  校验失败（ADM 实测）：{"code": -1, "message": "异常数据 validation.*", "data": {"字段": ["validation.*"]}}

生成要求同方式一，额外要求：
- 负向用例统一 assert_validation_error，并列出期望出现在 data 中的字段名
- 结合 test_data/sql/shared/baseline.sql 或 BASIC_INFO_FLOW_* 环境变量设计参数值
- 对于「创建/修改」类接口，可选追加 DB 断言（MySQL apple_*_ext / Polar 基准表），并说明是否写库
- 鉴权：低权限账号用 login_endpoint="sub" 登录（与页面一致），见 tests/conftest.py do_login
```

---

## 进阶：结合阶段一测试点补充业务场景

```
以下是阶段一生成的测试点清单（P0 和 P1 部分）：
[粘贴测试点清单相关行]

对照 [接口名] 的用例，检查哪些测试点尚未被覆盖，
为每个未覆盖的测试点新增一个 pytest 测试函数并追加到现有文件。
负向场景务必使用 assert_validation_error，勿沿用「期望 400/422」除非实测如此。
```

---

## 输出产物

生成文件保存至：`tests/api/test_[模块名].py`

参考实现（已与 ADM 实测对齐）：

- `tests/api/basic_info/test_basic_info_management.py` — 列表/导出/类型与边界
- `tests/api/basic_info/test_basic_info_accounts.py` — 账户校验与添加
- `tests/api/basic_info/test_basic_info_products.py` — 产品校验与添加
- `tests/api/basic_info/test_basic_info_relations.py` — 账户-产品关系

若同一模块需要 **UI 验证**，在阶段一测试点中圈 P0 后，另见 [06_e2e_ui_flow.md](06_e2e_ui_flow.md)（不写在本阶段的 API 文件里混用 Playwright，除非项目明确约定）。
