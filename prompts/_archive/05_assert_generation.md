# 阶段四：断言生成 & 自动化脚本完善

**全景位置**：[00_README.md](00_README.md)。**本阶段默认面向 API/HTTP/DB/JSON Schema**（`ApiClient`、`db_cursor` 等）。**Playwright 页面断言**（`expect(locator)`）请用 **阶段五 [06_e2e_ui_flow.md](06_e2e_ui_flow.md) 模板 D**，避免与 HTTP 断言混在同一套模板里产生歧义。

**使用场景**：测试用例骨架已生成，需要 AI 补全完整断言逻辑（含数据库断言）。  
**在 Cursor 中使用**：@ 已有测试文件 + 接口文档，追问断言生成。

---

## Prompt 模板

### HTTP 响应断言生成

```
阅读 @[测试文件] 中还没有完整断言的测试函数（只有 assert_status 的），
结合以下接口响应结构，为每个函数补充完整断言：

接口响应结构（从 Apifox 复制）：
[粘贴接口响应 JSON 示例]

补充断言要求：
1. 响应字段存在性：response["data"] 中每个字段都要断言 exists
2. 字段类型：使用 isinstance(value, 期望类型) 断言
3. 字段值范围：数值型字段断言 > 0 或在合理范围内
4. 关键业务字段：如 orderId、userId 等 ID 类字段断言为非空字符串

使用 ApiClient 的 assert_field_exists 和 assert_json_field 方法，
避免重复写 resp.json()["key"]["subkey"] 这种硬编码。
```

---

## Prompt 模板

### 数据库变更断言生成

```
针对以下"写操作"接口（POST/PUT/DELETE），生成数据库验证断言：

接口：[POST /api/order/create]
数据库表：[orders 表，CREATE TABLE 语句如下]
[粘贴建表语句]

要求：
1. 接口调用成功后，立即查询数据库验证数据已写入
2. 断言数据库中的字段值与请求参数一致
3. 对于 DELETE 接口，断言记录已软删除（deleted_at IS NOT NULL）或已物理删除
4. 对于状态更新接口，断言 status 字段值已变更为期望值

生成的数据库断言写在 @pytest.mark.db 标记的单独测试函数中，
依赖 db_cursor fixture（已在 conftest.py 定义）。
```

---

## Prompt 模板

### JSON Schema 断言生成

```
为 [接口名] 的响应生成 jsonschema 格式的 Schema 验证：

接口响应示例：
[粘贴实际响应 JSON]

生成要求：
1. 为响应体生成完整的 JSON Schema（type、required、properties）
2. 对字符串字段添加 minLength/maxLength 约束
3. 对数值字段添加 minimum 约束
4. 生成对应的 test_响应schema验证 测试函数，使用 client.assert_schema(resp, schema)

将 Schema 定义放在测试文件顶部的常量中，如 USER_CREATE_SCHEMA = {...}
```

---

## 执行命令参考

```bash
# 基础运行
pytest tests/ -v

# 只运行冒烟测试
pytest tests/ -m smoke -v

# 并行运行（需要 pytest-xdist）
pytest tests/ -n auto -v

# 生成 HTML 报告
pytest tests/ --html=reports/report.html --self-contained-html

# 生成 Allure 报告
pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

---

## 输出产物

- **API / 流程 HTTP**：`tests/api/[模块名]/test_*.py`；多步纯 HTTP 见 `tests/integration/[模块名]/test_*_flow.py`（与 **浏览器 E2E** 不同，后者为 `test_*_e2e.py` + Playwright）。
- **浏览器 E2E**：不在本文件展开；使用 [06_e2e_ui_flow.md](06_e2e_ui_flow.md) 模板 D 更新 `tests/integration/[模块名]/test_*_e2e.py`。
