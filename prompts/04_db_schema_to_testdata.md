# 阶段三：MySQL Schema → 测试数据构造

**全景位置**：[00_README.md](00_README.md)。本阶段数据可同时服务 **阶段二～四的 API 用例** 与 **阶段五 UI E2E**（例如固定账号、列表必有数据）；纯 E2E 只读环境可跳过部分造数。

**使用场景**：获取到数据库建表语句后，让 AI 生成可复用的测试数据 SQL。  
**在 Cursor 中使用**：粘贴 CREATE TABLE 语句后使用 Prompt。

---

## 步骤 1：导出建表语句

在 MySQL 中执行：

```sql
-- 导出单表
SHOW CREATE TABLE 表名\G

-- 批量导出（推荐使用 mysqldump）
mysqldump -u root -p --no-data 数据库名 > schema.sql
```

---

## Prompt 模板

### 生成基准测试数据

```
以下是 MySQL 数据库表结构，请生成测试数据 SQL：

[粘贴 CREATE TABLE 语句，可多张表]

生成要求：
1. 【基准数据】每张核心表插入 3-5 条"干净"的正常数据，覆盖常见业务场景
2. 【边界值数据】为每个有约束的字段生成边界行：
   - VARCHAR(255)：生成 1 字符、254 字符、255 字符三条记录
   - INT 类型：生成最小值（如 0 或 1）和接近最大值的记录
   - NOT NULL 字段：确保插入数据完整
3. 【特殊状态数据】根据字段名推断并生成：
   - status 字段：覆盖所有可能枚举值
   - deleted_at / is_deleted：生成已删除的记录
   - expired_at：生成已过期和未过期的记录
4. 所有时间字段使用相对时间（NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY)）
5. 为每组数据加注释说明用途

输出为两个文件的内容：
A. baseline.sql —— INSERT 语句
B. cleanup.sql —— 对应的 DELETE 语句（按主键精确删除，不用 TRUNCATE）
```

---

## Prompt 模板

### 生成 pytest fixture（conftest.py 集成）

```
基于以上测试数据，为 tests/conftest.py 生成以下 pytest fixtures：

1. fixture: user_data  
   插入一个标准用户，返回包含 id/username/token 的字典，用例结束后删除

2. fixture: admin_user_data  
   插入一个管理员用户，返回同上

3. fixture: expired_data  
   插入一条 expired_at < NOW() 的记录，用于测试过期场景

要求：
- scope="function"，每个用例独立数据，测试后自动清理
- 使用 pymysql，连接配置从 .env 读取（已在 conftest.py 中定义 DB_CONFIG）
- 返回 dict，包含后续断言所需的所有字段值
- 在 fixture 内部捕获异常并打印，确保清理逻辑（finally 块）不遗漏
```

---

## 注意事项

- 测试数据使用 `test_` 前缀命名（如 username = 'test_user_001'），便于区分和批量清理
- 禁止在生产数据库执行，始终使用独立测试库
- 外键约束顺序：先插入主表数据，再插入从表数据；cleanup 反向删除

---

## 输出产物

- `test_data/sql/{模块目录}/baseline.sql`
- `test_data/sql/{模块目录}/cleanup.sql`（通用示例见 `shared/`）
- 追加至 `tests/conftest.py`

**阶段五（E2E）**：若用例依赖「列表非空、指定 ORG/产品存在」等，在本阶段 SQL 或 fixture 中写明前置数据，并在 [06_e2e_ui_flow.md](06_e2e_ui_flow.md) 的用例注释中引用对应数据标识，避免环境与用例脱节。
