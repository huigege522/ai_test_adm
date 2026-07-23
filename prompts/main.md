# 主 Prompt：需求 → 可运行 pytest 用例（一步到位）

**使用场景**：拿到需求文档后，粘贴此 Prompt + 需求内容，直接输出完整可运行的 pytest 文件。

**在 Cursor 中使用**：@ 需求文档 + 本 Prompt，或粘贴需求文本。

---

## ADM 响应约定（必读）

被测系统为 Apple CMP ADM（`BASE_URL`，如 `https://adm.gm825.net`）：

| 场景 | HTTP | 业务体 | 断言方式 |
|------|------|--------|----------|
| 成功 | 200 | `code: 0` | `assert_status(200)` + `assert_business_code(resp, "code", 0)` |
| 参数校验失败 | **200** | `code: -1`，`data.{字段}: ["validation.*"]` | `assert_validation_error(resp, "字段名")` |
| 无会话 | 401 或 200 | `code: -1`，message 含 Unauthorized | `assert_http_401_or_403(resp, expect_403=False)` |
| 低权限 | 200 或 401/403 | `code: -1`，message 含 Unauthorized | `assert_http_401_or_403(resp, expect_403=True)` |

**关键**：参数错误默认返回 HTTP 200 + code=-1，**不是** 400/422。

---

## Prompt 模板

```
你是一名资深测试工程师，熟悉 pytest、ApiClient 和 ADM 系统的响应约定。

请阅读以下需求文档，完成三件事：

## 第一步：提取测试点
按四个维度输出测试点清单（Markdown 表格）：
1. 【功能测试点】正向业务流程
2. 【边界值测试点】数值上下限、字符串长度、列表为空/满
3. 【异常测试点】错误输入、缺失必填、状态不允许、越权访问
4. 【业务规则测试点】约束条件、状态机转换

| 编号 | 维度 | 模块 | 测试点描述 | 优先级(P0/P1/P2) |
|------|------|------|-----------|-------------------|

## 第二步：生成完整 pytest 用例
参考测试点清单，生成可直接运行的 pytest 文件。

代码规范：
- 使用 tests/utils/api_client.py 中的 ApiClient 类
- 基本信息管理模块复用 tests/helpers/basic_info_http.py 中的断言
- 使用 @pytest.mark.parametrize 合并同类边界值用例
- 中文函数名，如 def test_正常获取列表(self)
- 文件顶部注明接口路径和模块名

覆盖场景（每个接口一个 TestClass）：
1. 正常场景：HTTP 200 + code=0 + 关键字段存在 + 类型正确
2. 参数缺失：逐字段缺失，assert_validation_error
3. 参数类型错误：合法 body 上只改一个字段，assert_validation_error
4. 边界值：超长字符串、枚举越界、空数组、极限数值
5. 越权：无 Cookie → assert_http_401_or_403(expect_403=False)
         低权限 → assert_http_401_or_403(expect_403=True)
6. 业务规则：从测试点清单的规则维度提取

## 第三步：补全断言
每个测试函数必须包含：
- HTTP 状态码断言
- 业务码断言（code=0 或 code=-1）
- 关键字段存在性 + 类型断言
- 数值范围断言（如 > 0）
- 写操作接口：增加 DB 断言验证数据落库

## 需求文档
---
[在此粘贴需求文档内容]
---

## 相关接口定义（可选）
---
[在此粘贴 Apifox 接口 JSON 或接口描述]
---

输出：先测试点清单，再完整 pytest 文件。
```

---

## 简化路径（80% 场景用这个就够了）

```
拿到需求 → 粘贴需求 + 本 Prompt → 得到 pytest 文件 → pytest tests/api/[模块]/ -v
                                                                ↓
                                                   挂了 → 用 07_defect_analysis.md
                                                   需要 UI → 用 06_e2e_ui_flow.md
```

## 其他 Prompt（按需取用）

| 场景 | Prompt |
|------|--------|
| 接口文档不全，需要读代码补分支用例 | `03_code_to_cases.md` |
| 需要造数据库测试数据 | `04_db_schema_to_testdata.md` |
| 浏览器 E2E 主路径 | `06_e2e_ui_flow.md` |
| 用例挂了要定位根因 | `07_defect_analysis.md` |

这些是"急救包"，日常不需要挨个跑。
