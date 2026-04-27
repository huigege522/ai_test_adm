-- ============================================================
-- baseline.sql — 基准测试数据
-- 说明：
--   1. 本文件由阶段三 Prompt（prompts/04_db_schema_to_testdata.md）生成
--   2. 所有测试数据以 test_ 前缀命名，便于识别和批量清理
--   3. 外键顺序：先插入主表，再插入从表
--   4. 禁止在生产库执行
--   5. 配合 cleanup.sql 使用（先 baseline 后 cleanup）
-- ============================================================

-- ─────────────────────────────────────────────
-- 示例：users 表基准数据
-- 请根据实际表结构替换，使用阶段三 Prompt 让 AI 生成
-- ─────────────────────────────────────────────

-- 标准普通用户
INSERT INTO users (id, username, password, email, status, created_at)
VALUES
  (9001, 'test_user_normal',  'hashed_pw_001', 'normal@test.com',  1, NOW()),
  (9002, 'test_user_admin',   'hashed_pw_002', 'admin@test.com',   1, NOW()),
  (9003, 'test_user_disabled','hashed_pw_003', 'disabled@test.com',0, NOW());

-- 边界值：用户名最大长度（假设 VARCHAR(50)）
INSERT INTO users (id, username, password, email, status, created_at)
VALUES
  (9004, REPEAT('a', 50), 'hashed_pw_004', 'maxlen@test.com', 1, NOW());

-- 特殊状态：已软删除
INSERT INTO users (id, username, password, email, status, deleted_at, created_at)
VALUES
  (9005, 'test_user_deleted', 'hashed_pw_005', 'deleted@test.com', 0, NOW(), NOW());

-- ─────────────────────────────────────────────
-- 使用说明：
-- 将以上 INSERT 语句替换为你的实际表结构和数据
-- 建议通过阶段三 Prompt 让 AI 基于真实 CREATE TABLE 语句重新生成
-- ─────────────────────────────────────────────
