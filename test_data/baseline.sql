-- ============================================================
-- baseline.sql — 基准测试数据
-- 表：cmp_apple_market（苹果大盘数据表）
-- 生成日期：2026-05-06
-- 说明：
--   1. 测试数据 ID 范围：900001 ~ 900035，不与生产数据冲突
--   2. 字符串显示字段（ttr/cpt/cr/cpa）模拟真实区间格式
--   3. decimal 字段保持 _min <= _avg <= _max 语义正确性
--   4. 禁止在生产库执行
--   5. 配合 cleanup.sql 使用
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- 【一】基准数据（5条）—— 覆盖常见业务场景
-- ─────────────────────────────────────────────────────────────

-- 场景1：一级分类 / 美国市场 / 游戏类 / 完整字段
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg,
   cpt_min, cpt_max, cpt_avg,
   cr_min,  cr_max,  cr_avg,
   cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd, android_cpd_min, android_cpd_max)
VALUES
  (900001, 'Games', 101, 1, 'United States', 'US', DATE_SUB(CURDATE(), INTERVAL 1 DAY),
   '2.50%-4.80%', '$0.35-$1.20', '48.00%-72.00%', '$1.50-$4.20',
   0.02500, 0.04800, 0.03500,
   0.35000, 1.20000, 0.65000,
   0.48000, 0.72000, 0.58000,
   1.50000, 4.20000, 2.80000,
   85.23000, 7.25000, '$0.18-$0.95', 0.18000, 0.95000);

-- 场景2：一级分类 / 中国市场 / 教育类 / 含安卓CPD数据
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg,
   cpt_min, cpt_max, cpt_avg,
   cr_min,  cr_max,  cr_avg,
   cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd, android_cpd_min, android_cpd_max)
VALUES
  (900002, 'Education', 102, 1, 'China', 'CN', DATE_SUB(CURDATE(), INTERVAL 7 DAY),
   '1.80%-3.60%', '¥2.10-¥7.50', '35.00%-60.00%', '¥8.00-¥25.00',
   0.01800, 0.03600, 0.02700,
   2.10000, 7.50000, 4.20000,
   0.35000, 0.60000, 0.46000,
   8.00000, 25.00000, 15.50000,
   72.10000, 7.10000, '¥1.20-¥4.80', 1.20000, 4.80000);

-- 场景3：二级分类 / 美国市场 / 动作游戏（子分类）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg,
   cpt_min, cpt_max, cpt_avg,
   cr_min,  cr_max,  cr_avg,
   cpa_min, cpa_max, cpa_avg,
   svi, rate)
VALUES
  (900003, 'Action Games', 201, 2, 'United States', 'US', DATE_SUB(CURDATE(), INTERVAL 1 DAY),
   '3.10%-5.50%', '$0.42-$1.65', '52.00%-78.00%', '$1.20-$3.80',
   0.03100, 0.05500, 0.04200,
   0.42000, 1.65000, 0.90000,
   0.52000, 0.78000, 0.63000,
   1.20000, 3.80000, 2.30000,
   91.50000, 7.25000);

-- 场景4：二级分类 / 英国市场 / 儿童教育（子分类）/ 30天前数据
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg,
   cpt_min, cpt_max, cpt_avg,
   cr_min,  cr_max,  cr_avg,
   cpa_min, cpa_max, cpa_avg,
   svi, rate)
VALUES
  (900004, 'Kids Education', 202, 2, 'United Kingdom', 'GB', DATE_SUB(CURDATE(), INTERVAL 30 DAY),
   '2.00%-4.20%', '£0.28-£0.95', '40.00%-65.00%', '£0.85-£2.60',
   0.02000, 0.04200, 0.03100,
   0.28000, 0.95000, 0.55000,
   0.40000, 0.65000, 0.51000,
   0.85000, 2.60000, 1.70000,
   68.30000, 8.05000);

-- 场景5：一级分类 / 日本市场 / 工具类 / 当月第一天
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg,
   cpt_min, cpt_max, cpt_avg,
   cr_min,  cr_max,  cr_avg,
   cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd, android_cpd_min, android_cpd_max)
VALUES
  (900005, 'Utilities', 103, 1, 'Japan', 'JP', DATE_FORMAT(CURDATE(), '%Y-%m-01'),
   '1.50%-3.20%', '¥48-¥185', '38.00%-58.00%', '¥120-¥520',
   0.01500, 0.03200, 0.02300,
   48.00000, 185.00000, 98.50000,
   0.38000, 0.58000, 0.46000,
   120.00000, 520.00000, 280.00000,
   55.80000, 150.20000, '¥30-¥120', 30.00000, 120.00000);


-- ─────────────────────────────────────────────────────────────
-- 【二】边界值数据
-- ─────────────────────────────────────────────────────────────

-- ── category VARCHAR(50) 边界 ─────────────────────────────────

-- category 最小长度：1 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900011, 'A', NULL, 1, 'Test Market', 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- category 次最大长度：49 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900012, REPEAT('B', 49), NULL, 1, 'Test Market', 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- category 最大长度：50 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900013, REPEAT('C', 50), NULL, 1, 'Test Market', 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- ── marketplace VARCHAR(100) 边界 ────────────────────────────

-- marketplace 最小长度：1 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900014, 'TestCategory', NULL, 1, 'U', 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- marketplace 次最大长度：99 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900015, 'TestCategory', NULL, 1, REPEAT('M', 99), 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- marketplace 最大长度：100 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900016, 'TestCategory', NULL, 1, REPEAT('M', 100), 'US', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- ── country_code VARCHAR(15) 边界 ────────────────────────────

-- country_code 最小长度：1 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900017, 'TestCategory', NULL, 1, 'Test Market', 'X', CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- country_code 次最大长度：14 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900018, 'TestCategory', NULL, 1, 'Test Market', REPEAT('Z', 14), CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- country_code 最大长度：15 字符
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900019, 'TestCategory', NULL, 1, 'Test Market', REPEAT('Z', 15), CURDATE(),
   0.01000, 0.05000, 0.03000, 0.10000, 1.00000, 0.50000,
   0.30000, 0.70000, 0.50000, 0.50000, 5.00000, 2.50000);

-- ── DECIMAL(10,5) 边界值 ─────────────────────────────────────

-- 全部 decimal 字段取最小值：0.00000
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd_min, android_cpd_max)
VALUES
  (900020, 'BoundaryMin', NULL, 1, 'Test Market', 'US', CURDATE(),
   0.00000, 0.00000, 0.00000,
   0.00000, 0.00000, 0.00000,
   0.00000, 0.00000, 0.00000,
   0.00000, 0.00000, 0.00000,
   0.00000, 0.00000, 0.00000, 0.00000);

-- 全部 decimal 字段取最大值：99999.99999（DECIMAL(10,5) 上限）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd_min, android_cpd_max)
VALUES
  (900021, 'BoundaryMax', NULL, 1, 'Test Market', 'US', CURDATE(),
   99999.99999, 99999.99999, 99999.99999,
   99999.99999, 99999.99999, 99999.99999,
   99999.99999, 99999.99999, 99999.99999,
   99999.99999, 99999.99999, 99999.99999,
   99999.99999, 99999.99999, 99999.99999, 99999.99999);

-- ── time_period 时间边界 ─────────────────────────────────────

-- 历史数据：1 年前
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900022, 'Games', 101, 1, 'United States', 'US', DATE_SUB(CURDATE(), INTERVAL 365 DAY),
   0.02000, 0.04500, 0.03200, 0.30000, 1.10000, 0.60000,
   0.40000, 0.65000, 0.52000, 1.20000, 4.00000, 2.50000);

-- 当天数据：TODAY
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900023, 'Games', 101, 1, 'United States', 'US', CURDATE(),
   0.02500, 0.04800, 0.03500, 0.35000, 1.20000, 0.65000,
   0.48000, 0.72000, 0.58000, 1.50000, 4.20000, 2.80000);

-- 未来数据：明天（测试系统是否拒绝或如何展示未来日期）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900024, 'Games', 101, 1, 'United States', 'US', DATE_ADD(CURDATE(), INTERVAL 1 DAY),
   0.02500, 0.04800, 0.03500, 0.35000, 1.20000, 0.65000,
   0.48000, 0.72000, 0.58000, 1.50000, 4.20000, 2.80000);


-- ─────────────────────────────────────────────────────────────
-- 【三】特殊状态数据
-- ─────────────────────────────────────────────────────────────

-- type 枚举全覆盖：type=1（一级分类）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900025, 'TopCategory', 110, 1, 'Australia', 'AU', DATE_SUB(CURDATE(), INTERVAL 3 DAY),
   0.02200, 0.04100, 0.03100, 0.40000, 1.30000, 0.70000,
   0.42000, 0.68000, 0.54000, 1.60000, 4.50000, 2.90000);

-- type 枚举全覆盖：type=2（二级分类）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900026, 'SubCategory', 210, 2, 'Australia', 'AU', DATE_SUB(CURDATE(), INTERVAL 3 DAY),
   0.02800, 0.05200, 0.03900, 0.45000, 1.50000, 0.85000,
   0.50000, 0.75000, 0.61000, 1.80000, 5.00000, 3.20000);

-- NULL 可选字段：country_code=NULL + category_id=NULL（地区未知场景）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg,
   svi, rate)
VALUES
  (900027, 'Games', NULL, 1, 'Global', NULL, DATE_SUB(CURDATE(), INTERVAL 1 DAY),
   0.02500, 0.04800, 0.03500, 0.35000, 1.20000, 0.65000,
   0.48000, 0.72000, 0.58000, 1.50000, 4.20000, 2.80000,
   NULL, NULL);

-- NULL 可选字段：svi=NULL + rate=NULL（无汇率/搜索量数据）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900028, 'Education', 102, 2, 'Canada', 'CA', DATE_SUB(CURDATE(), INTERVAL 2 DAY),
   0.02000, 0.04000, 0.03000, 0.30000, 1.00000, 0.55000,
   0.40000, 0.65000, 0.51000, 1.30000, 3.80000, 2.40000);

-- NULL 可选字段：android_cpd 系列全为 NULL（纯 iOS 数据，无安卓对比）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg,
   svi, rate,
   android_cpd, android_cpd_min, android_cpd_max)
VALUES
  (900029, 'Finance', 104, 1, 'Germany', 'DE', DATE_SUB(CURDATE(), INTERVAL 5 DAY),
   0.01800, 0.03900, 0.02800, 0.50000, 1.80000, 1.00000,
   0.38000, 0.62000, 0.49000, 2.00000, 6.50000, 4.00000,
   78.50000, 7.90000,
   NULL, NULL, NULL);

-- 显示字段 ttr/cpt/cr/cpa 全为 NULL（仅数值字段有数据，前端展示降级场景）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900030, 'Entertainment', 105, 2, 'France', 'FR', DATE_SUB(CURDATE(), INTERVAL 4 DAY),
   NULL, NULL, NULL, NULL,
   0.02100, 0.04600, 0.03300, 0.38000, 1.40000, 0.75000,
   0.44000, 0.70000, 0.56000, 1.70000, 4.80000, 3.00000);

-- 含安卓 CPD 完整数据（iOS+Android 双平台对比场景）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr, cpt, cr, cpa,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg,
   svi, rate, android_cpd, android_cpd_min, android_cpd_max)
VALUES
  (900031, 'Social Networking', 106, 1, 'United States', 'US', DATE_SUB(CURDATE(), INTERVAL 2 DAY),
   '3.50%-6.20%', '$0.25-$0.88', '55.00%-80.00%', '$0.80-$2.50',
   0.03500, 0.06200, 0.04800,
   0.25000, 0.88000, 0.52000,
   0.55000, 0.80000, 0.66000,
   0.80000, 2.50000, 1.60000,
   95.20000, 7.25000, '$0.12-$0.65', 0.12000, 0.65000);

-- 极小值行：所有 decimal 使用业务上合理的极小正值（趋近零但非零）
INSERT INTO cmp_apple_market
  (id, category, category_id, type, marketplace, country_code, time_period,
   ttr_min, ttr_max, ttr_avg, cpt_min, cpt_max, cpt_avg,
   cr_min, cr_max, cr_avg, cpa_min, cpa_max, cpa_avg)
VALUES
  (900032, 'NearZeroTest', NULL, 1, 'Test Market', 'US', DATE_SUB(CURDATE(), INTERVAL 1 DAY),
   0.00001, 0.00002, 0.00001,
   0.00001, 0.00002, 0.00001,
   0.00001, 0.00002, 0.00001,
   0.00001, 0.00002, 0.00001);
