---
name: testpoints-to-automation
description: >
  将 test_data/testpoints/{模块}/testpoints_*.md 测试点清单分层映射并落地为 pytest 自动化（API / DB / Integration / E2E）。
  适用于“如何把测试用例自动化”“根据测试点生成自动化”“落地 API/UI E2E/DB 断言”“从测试点清单生成 pytest 用例”。
  项目目录与工具类约定见 ai-test-adm-project-overview；本 Skill 侧重分层决策与工作流，不绑定某一业务域。
---

# 测试点清单转自动化

## 使用场景

当用户已有 `test_data/testpoints/{模块}/testpoints_*.md`，希望将测试点转为自动化时，按本 Skill 执行。

**分层与优先级决策**在本 Skill；**目录结构、ApiClient、fixture、标记约定**见 `ai-test-adm-project-overview`。

## 核心原则

不要把测试点逐条等价转换成 UI 自动化。先按**可验证层级**分类，再选实现方式：

| 测试点特征（抽象） | 推荐自动化层级 | 说明 |
|---|---|---|
| 单接口 CRUD、列表、筛选、参数/必填/权限校验 | `api` | 契约与业务码即可覆盖 |
| 写操作后的落库、关联、状态、计数、审计字段 | `api` + `db` | 响应成功不足以证明持久化正确 |
| 多步骤、跨模块/跨实体、上下游状态传递 | `integration` | 用 API 串联闭环，避免用浏览器跑纯 HTTP |
| 仅浏览器可验证的交互与展示（弹窗、禁用态、预填、可见性） | `e2e` | 少量 P0 主路径即可 |
| 外部系统、定时/批处理、难以稳定造数 | `api`/`db` + Mock 或 `manual` | 评估稳定性后再自动化 |
| 需求/接口/表结构标注「待确认」 | `blocked` | 先列阻塞项，不臆造路径与断言 |

**Integration 判定（通用）**：测试点描述中出现「先 A 再 B」「依赖上一步返回值」「跨模块列表展示聚合结果」等，且步骤 ≥2 个写操作或 1 写 + 1 跨模块读，优先 `integration` 而非拆成互不关联的孤立 `api` 用例。

**E2E 判定（通用）**：仅当缺少稳定 API、或必须验证 DOM/前端路由/前端校验/UI 状态时选 `e2e`；若 API 已能证明同一业务结论，不要重复做 UI。

## 标准工作流

1. 读取测试点清单，优先 `P0`，再补 `P1`。
2. 为每条标注层级：`api`、`db`、`integration`、`e2e`、`manual`、`blocked`（可多选，如 `api+db`）。
3. 输出**自动化映射表**（见下节），与用户确认后再写代码。
4. `api`：对照 Apifox/OpenAPI/接口文档，生成 `tests/api/test_[module].py`。
5. 写操作：补 `@pytest.mark.db` 断言；需要时更新 `test_data/sql/{模块}/baseline.sql`、`cleanup.sql`。
6. `integration`：生成 `tests/integration/[模块]/test_[flow].py`，步骤与测试点主链路一致。
7. `e2e`：仅 P0 主路径，Page Object + `test_*_e2e.py`。
8. 测试点编号写入函数名、docstring 或注释，便于追溯。
9. 运行 pytest；失败按 `prompts/07_defect_analysis.md` 分析。

## 测试点分层输出模板

先输出映射表，再写代码。`模块`、`场景`、`目标文件` 均来自**当前**测试点清单，勿套用其他需求的命名：

```markdown
| 测试点编号 | 优先级 | 模块 | 场景 | 自动化层级 | 目标文件 | 备注 |
|---|---|---|---|---|---|---|
| TC001 | P0 | [模块]-[功能] | [一句话场景] | api+db | tests/api/test_[module].py | 依赖：创建接口、表 [table] |
```

## 项目约定（ai_test_adm）

落地到本仓库时使用以下路径（细节以 project-overview 为准）：

| 层级 | 目标位置 |
|---|---|
| API | `tests/api/{模块}/test_*.py` |
| Integration | `tests/integration/{模块}/test_*.py` |
| UI E2E | `tests/pages/*.py` + `tests/integration/{模块}/test_*_e2e.py` |
| 测试数据 | `test_data/sql/{模块}/baseline.sql`、`cleanup.sql` |
| 公共能力 | `tests/conftest.py`、`tests/utils/api_client.py` |

## API 用例约定

使用 `tests/utils/api_client.py` 的 `ApiClient`：

```python
import pytest
from tests.utils.api_client import ApiClient

client = ApiClient()


class TestEntityCreate:

    @pytest.mark.smoke
    def test_TC001_创建实体_某可选字段为空(self):
        """TC001：[测试点原文或摘要]。"""
        payload = {
            # TODO: 按接口定义补齐字段名与合法默认值
        }

        resp = client.post("/api/xxx/entity/create", json=payload)

        client.assert_status(resp, 200)
        client.assert_business_code(resp, "code", 0)
        client.assert_field_exists(resp, "data")
```

要求：

- 每个接口（或资源）一个 `Test*` 类。
- P0：`@pytest.mark.smoke`；异常：`@pytest.mark.negative`；边界：`@pytest.mark.boundary` + `parametrize`；回归：`@pytest.mark.regression`。
- 函数名保留 `TCxxx`。
- 路径、字段名、业务码以接口文档为准；未知用 `TODO`。

## DB 断言约定

写操作在响应断言之外，优先增加 DB 校验：

```python
@pytest.mark.db
def test_TC001_创建后数据库记录正确(self, db_cursor):
    """TC001：验证主表记录及关键字段/关联是否符合预期。"""
    resp = client.post("/api/xxx/entity/create", json=payload)
    client.assert_status(resp, 200)

    entity_id = resp.json()["data"]["entityId"]  # TODO: 按实际响应字段
    db_cursor.execute(
        "SELECT * FROM entity_table WHERE id = %s",
        (entity_id,),
    )
    row = db_cursor.fetchone()

    assert row is not None
    # TODO: 按测试点断言字段值、关联表、状态枚举等
```

表结构未知时：向用户索要 DDL，或从代码/SQL/阶段三产出读取后再生成；禁止臆造表名与列名。

## Integration 流程约定

用于**同一业务主链路**的多步闭环。流程名与步骤完全来自当前测试点，例如（仅作格式示意，非固定业务）：

```text
创建主数据 → 创建/绑定从属数据 → 触发查询或状态变更 → 断言聚合结果或侧效
```

- 文件：`tests/integration/[模块]/test_[flow].py`
- 仍使用 `ApiClient`；不要把纯 HTTP 多步流程写成 Playwright E2E。

## UI E2E 约定

仅挑选少量必须浏览器验证的 P0 路径，例如：

- 页面可访问、关键列表/字段可见
- 表单项展示/隐藏、校验提示
- 路由跳转后预填、按钮禁用态
- 无对应 API 或 API 无法覆盖的前端逻辑

结构：

```text
tests/pages/[module]_page.py
tests/integration/[module]/test_[module]_e2e.py
```

Page Object 继承 `tests/pages/base_page.py`。定位器优先级：`data-testid` → `role`/`aria` → 稳定文本 → CSS；避免脆弱 XPath 与序号定位。

## 推荐落地顺序

1. P0 `api`：单接口增删改查、必填与权限。
2. P0 `db`：写操作持久化与关键关联。
3. P0 `integration`：跨模块/多步主链路。
4. 3～5 条 P0 `e2e`：UI 独有验证点。
5. P1/P2 按回归价值逐步补齐。

## 常用命令

```bash
pytest tests/api/test_[module].py -v
pytest tests/ -m smoke -v
pytest tests/ -m "negative or boundary" -v
pytest tests/integration/ -v
pytest tests/integration/ -v -m e2e
pytest tests/ --html=reports/report.html --self-contained-html
```

## 输出要求

用户要求「转自动化」时，优先输出：

1. 自动化分层映射表（每条测试点一行，层级与理由）。
2. 建议新增/修改的文件清单。
3. 第一批建议落地的 P0 用例及依赖。
4. **信息缺口清单**：接口路径、请求/响应字段、表结构、前端入口 URL、账号权限、Mock 策略。
5. 信息充分后再生成代码。

不要臆造接口路径、表名、选择器；未知项用 `TODO` 或标为 `blocked`。业务域名词（实体名、模块名、表名）只从当前 `testpoints_*.md` 或用户提供的文档中提取。
