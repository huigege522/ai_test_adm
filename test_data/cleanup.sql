-- ============================================================
-- cleanup.sql — 测试数据清理
-- 表：cmp_apple_market（苹果大盘数据表）
-- 生成日期：2026-05-06
-- 说明：
--   1. 按主键精确删除，不使用 TRUNCATE（避免影响非测试数据）
--   2. 删除顺序与 baseline.sql 插入顺序一致（单表无外键依赖）
--   3. 覆盖 ID 范围：900001 ~ 900032
--   4. 本文件由 conftest.py 中 load_baseline fixture 自动执行
-- ============================================================

-- ── 基准数据（900001-900005） ────────────────────────────────
DELETE FROM cmp_apple_market WHERE id IN (900001, 900002, 900003, 900004, 900005);

-- ── 边界值：category VARCHAR(50)（900011-900013） ────────────
DELETE FROM cmp_apple_market WHERE id IN (900011, 900012, 900013);

-- ── 边界值：marketplace VARCHAR(100)（900014-900016） ─────────
DELETE FROM cmp_apple_market WHERE id IN (900014, 900015, 900016);

-- ── 边界值：country_code VARCHAR(15)（900017-900019） ─────────
DELETE FROM cmp_apple_market WHERE id IN (900017, 900018, 900019);

-- ── 边界值：DECIMAL(10,5) 最小/最大值（900020-900021） ───────
DELETE FROM cmp_apple_market WHERE id IN (900020, 900021);

-- ── 边界值：time_period 历史/当天/未来（900022-900024） ───────
DELETE FROM cmp_apple_market WHERE id IN (900022, 900023, 900024);

-- ── 特殊状态（900025-900032） ────────────────────────────────
DELETE FROM cmp_apple_market WHERE id IN (900025, 900026, 900027, 900028, 900029, 900030, 900031, 900032);

-- ── 兜底清理：批量删除全部测试 ID 范围（上面逐行失败时备用） ──
-- DELETE FROM cmp_apple_market WHERE id BETWEEN 900001 AND 900099;
