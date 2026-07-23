# 阶段五：UI 端到端（Playwright）流程与 Prompt

**全景位置**：整条测试链路见 [00_README.md](00_README.md)（阶段一～六）。本阶段在**阶段一测试点**之后启动，通常与**阶段二～四（API、数据、HTTP 断言）并行或稍后**补齐，二者职责不同、互为补充。

**使用场景**：已有「测试点清单」或明确的 P0 用户路径，需要在本仓库中落地 **浏览器级 E2E**（Page Object、`playwright_page`、Cookie 登录、`-m e2e`）。

**在 Cursor 中使用**：@ [01_req_to_testpoints.md](01_req_to_testpoints.md) 产出的 `test_data/testpoints/{模块}/testpoints_*.md`（或粘贴 P0 行）+ 本文件 + 实际入口 URL / 定位说明。

---

## 与整条流程的关系（保证流程正确）

| 依赖 | 说明 |
|------|------|
| **阶段一** | 从测试点中圈定 **P0 UI 主路径**（1～3 条即可），避免与 API 用例逐条重复。 |
| **阶段二～三（可选）** | E2E 若依赖**固定列表数据 / 指定账号权限**，用 `test_data/sql/{模块}/baseline.sql` 或独立沙箱用户在阶段三准备；纯「只读冒烟」可仅依赖现网测试环境。 |
| **阶段四** | 面向 **ApiClient / HTTP / DB** 断言；**不替代**本阶段的 **Playwright `expect(locator)`**。 |
| **阶段六** | E2E 失败时，用缺陷分析 Prompt，并 @ `tests/integration/{模块}/test_*_e2e.py` + 截图/ trace。 |

**分工原则**：接口测 **参数、边界、权限、分支**；UI E2E 测 **登录态、路由、关键交互闭环**。同一业务现象：**API 证明后端契约**，**E2E 证明用户能点通**。

---

## UI E2E 标准流程（建议按序执行）

1. **环境**：`.env` 配置 `BASE_URL`，`LOGIN_USERNAME` / `LOGIN_PASSWORD` 或 `AUTH_COOKIE`（见 `.env.example`）；安装 `playwright`、`pytest-playwright`，执行 `playwright install`（CI 常用 `chromium`）。
2. **圈选范围**：从 `test_data/testpoints/{模块}/testpoints_*.md` 勾选 P0 **功能**类、且必须走浏览器的步骤（列表、弹窗、导出入口等）。
3. **故事化步骤**：写清「入口 URL → 每一步点击/输入 → 结束判定」（Toast、表格行、跳转 URL）。
4. **实施计划**：使用下方 **Prompt A**，产出文件清单与方法列表（不写实现代码）。
5. **骨架代码**：使用 **Prompt B** 生成 `tests/pages/*.py` + `conftest.py` 导航 fixture。
6. **用例骨架**：使用 **Prompt C** 生成 `tests/integration/{模块}/test_*_e2e.py`（步骤注释 + 占位断言）。
7. **补全与运行**：按真实 DOM 替换选择器，补全 `expect`；执行 `pytest tests/integration/ -v -m e2e`。

---

## 本仓库技术约定（生成代码时必须遵守）

1. **依赖**：见项目根目录 `requirements.txt`（含 `playwright`、`pytest-playwright`）。
2. **认证**：使用 `playwright_page` fixture；Cookie 来自 `login_session`（与 `tests/conftest.py` 一致）。
3. **目录**：
   - 页面对象：`tests/pages/<模块>_xxx_page.py`，继承 `BasePage`。
   - 用例：`tests/integration/<模块>/test_<模块>_e2e.py`，标记 `@pytest.mark.e2e`（可与 `smoke` / `regression` 组合）。
4. **入口 URL**：通过 `E2E_<模块>_URL` 或 `BASE_URL + 路径` 配置，避免硬编码环境域名。
5. **定位器**：优先 `data-testid`、稳定 `aria`/`role`；占位常量集中放在 Page 类顶部并注释「待对齐前端」。可用 `temp_get_locators.py` 辅助。
6. **参考实现**：`tests/integration/competitor/test_competitor_e2e.py`、`tests/pages/competitor_*_page.py`（定位器可能仍为占位，仅作结构参考）。

---

## 实施前自检表

| 序号 | 检查项 |
|------|--------|
| 1 | P0 路径的起点 URL、结束判定是否写清 |
| 2 | 每步是否需要等待（接口、动画、轮询） |
| 3 | 前置数据：权限、ORG/产品 ID、列表空或非空 |
| 4 | 定位策略是否避免脆弱 XPath（如「第 3 个 div」） |
| 5 | 失败时是否有截图/trace 或 Allure 附件（见 `tests/utils/e2e_helpers.py`） |

---

## Prompt 模板 A：实施计划 + 文件清单（不写用例代码）

```
你是一名资深测试开发，熟悉 pytest 与 Playwright Page Object。

输入：
1. 模块名：[模块名]
2. P0 UI 主路径（来自测试点或手工）：[步骤 1→2→3…]
3. 入口 URL 规则：[完整 URL 或 BASE_URL + 路径；未定项列「待产品确认」]

请输出（Markdown）：
1. 建议新建/修改的文件路径（Page / conftest fixture / test_*_e2e.py）
2. 每个 Page 类的方法名列表（仅签名说明）
3. conftest 新 fixture 名称及依赖
4. 建议环境变量（如 E2E_xxx_URL）及默认值策略
5. 用例「标题级」列表（每行一条中文标题，无代码）
6. 风险与缓解：异步、第三方校验、权限、数据污染（各一条）

不要输出完整可运行测试代码。
```

---

## Prompt 模板 B：Page Object 骨架 + conftest 导航 fixture

```
你是一名资深测试开发。在 ai_test_adm 仓库中按现有风格新增 UI E2E 支撑代码。

@ tests/pages/base_page.py  @ tests/conftest.py（playwright_browser、playwright_page、competitor_explore_page）

任务：
1. 新增 tests/pages/[模块]_page.py：继承 BasePage；顶部 SELECTOR_* 常量（可占位）；实现 navigate_to_* 及业务方法（信息不足可用 raise NotImplementedError，docstring 说明意图）。
2. 在 tests/conftest.py 末尾增加 fixture [模块]_page(playwright_page)：从环境变量 [E2E_XXX_URL] 读入口，否则 BASE_URL + [默认相对路径]。

约束：不要编写 pytest 测试函数；不要改动无关 conftest 逻辑。
```

---

## Prompt 模板 C：E2E 用例骨架（步骤注释 + 占位断言）

```
基于以下 P0 路径，生成 tests/integration/[模块]/test_[模块]_e2e.py 骨架。

要求：@pytest.mark.e2e；注入 [模块]_page；每步仅中文注释 + pass 或 # TODO: expect(...)；docstring 对应测试点编号或用户故事。

P0 路径：
[粘贴步骤]

不要引入项目未使用的第三方库。
```

---

## Prompt 模板 D：为 E2E 补全 Playwright 断言（可选）

在 Page 方法就绪后，可结合阶段四思路**只针对页面可见结果**补断言（不要用 ApiClient 替代 UI 断言主体）。

```
阅读 tests/integration/[模块]/test_[模块]_e2e.py 与 tests/pages/[模块]_page.py。

为每个 TODO 补充 Playwright expect 断言：
- 可见性、文案、URL、表格行数、禁用态等
- 合理使用 timeout，避免拍脑袋 sleep

不要删除已有步骤注释；不要改变用例与阶段一测试点的对应关系。
```

（复杂失败场景仍走 [07_defect_analysis.md](07_defect_analysis.md)。）

---

## 运行与 CI

```bash
pytest tests/integration/ -v -m e2e
```

流水线建议：`playwright install chromium` 后执行；`conftest` 中浏览器 headless 与本地一致。

---

## 输出产物

| 产物 | 路径 |
|------|------|
| 页面对象 | `tests/pages/<模块>_*.py` |
| 导航 fixture | `tests/conftest.py` |
| E2E 用例 | `tests/integration/<模块>/test_<模块>_e2e.py` |
| 环境变量 | `.env` / `.env.example` 中的 `E2E_*_URL`（按需） |

**小结**：阶段一产出测试点 → 本阶段圈 P0 → A → B → C → 按需 D → 阶段六处理不稳定与回归。
