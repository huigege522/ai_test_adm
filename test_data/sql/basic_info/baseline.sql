-- ============================================================
-- basic_info/baseline.sql — Apple CMP 基本信息扩展表测试数据
-- 表：apple_org_ext、apple_app_ext、apple_app_org_attr
-- 生成日期：2026-05-15
--
-- 【执行目标库 — PolarDB 测试库】
--   - 业务上与 MySQL 并存：大盘等表在 MySQL（见 baseline.sql）；本脚本仅覆盖存放在 PolarDB 的扩展表。
--   - 与 pytest「polar_db_*」fixture 使用同一套连接：
--     见项目根目录 .env 中 POLAR_DB_HOST / POLAR_DB_PORT / POLAR_DB_NAME / POLAR_DB_USER / POLAR_DB_PASSWORD
--   - 脚本内不写 USE：请在客户端连上上述 PolarDB 实例后，选中 POLAR_DB_NAME 再执行（团队库名可能不同，勿硬编码）。
--
-- 说明：
--   1. 测试主键 id 范围：700001～702099（不与 test_data/sql/shared/baseline.sql 中 900xxx 冲突）
--   2. org_id / adam_id 与业务唯一键对应，见各组注释
--   3. 时间字段统一使用 NOW()、DATE_ADD(NOW(), INTERVAL …) 等相对时间
--   4. 字段名按常见 DDL 推断；若实际表结构与本文不一致请微调列名
--   5. 禁止在生产库执行
--   6. 配合 basic_info/cleanup.sql 使用（同样在 PolarDB 测试库执行）
-- ============================================================

SET NAMES utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- 【一】apple_org_ext — 基准数据（5 条，常见业务场景）
-- ═══════════════════════════════════════════════════════════

-- 场景1：直客 + 预付 + OAuth 创建来源 + 公司名较短
INSERT INTO apple_org_ext (
  id, org_id, bloc_id, bloc_name, customer_id, company_name, plat_username,
  status, is_delete, account_mtime, operator_id, operator_name, operator_mtime,
  attribution_type, attribution_mtime, updated_at,
  customer_type, settle_type, customer_policy, agent_type, agent_2nd_label,
  create_source, remark,
  creator_uid, creator_name, modifier_uid, modifier_name, created_at
) VALUES (
  700001, 710001, 5001, '集团A', 'CUST-710001', '上海某某科技有限公司', 'plat_user_001',
  0, 0, NOW(), 90001, '运营张三', DATE_ADD(NOW(), INTERVAL 1 HOUR),
  1, NOW(), NOW(),
  1, 1, '标准政策A', NULL, NULL,
  1, '基准-直客预付OAuth',
  10001, '管理员', 10001, '管理员', NOW()
);

-- 场景2：代理 + 垫付 + 美元户代理 + 手动添加
INSERT INTO apple_org_ext (
  id, org_id, bloc_id, bloc_name, customer_id, company_name, plat_username,
  status, is_delete, account_mtime, operator_id, operator_name, operator_mtime,
  attribution_type, attribution_mtime, updated_at,
  customer_type, settle_type, customer_policy, agent_type, agent_2nd_label,
  create_source, remark,
  creator_uid, creator_name, modifier_uid, modifier_name, created_at
) VALUES (
  700002, 710002, 5001, '集团A', 'CUST-710002', '北京代理工作室有限公司', 'plat_user_002',
  1, 0, DATE_SUB(NOW(), INTERVAL 3 DAY), 90002, '运营李四', NOW(),
  2, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW(),
  2, 2, '代理政策B', 1, '二代标签-华北',
  2, '基准-代理垫付美元户',
  10002, '管理员', 10002, '管理员', DATE_SUB(NOW(), INTERVAL 7 DAY)
);

-- 场景3：OAuth 客户类型 + 人民币户 + 归因 Adjust
INSERT INTO apple_org_ext (
  id, org_id, bloc_id, bloc_name, customer_id, company_name, plat_username,
  status, is_delete, account_mtime, operator_id, operator_name, operator_mtime,
  attribution_type, attribution_mtime, updated_at,
  customer_type, settle_type, customer_policy, agent_type, agent_2nd_label,
  create_source, remark,
  creator_uid, creator_name, modifier_uid, modifier_name, created_at
) VALUES (
  700003, 710003, 5002, '集团B', 'CUST-710003', '深圳创新互动网络技术有限公司', 'plat_user_003',
  2, 0, NOW(), NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 YEAR),
  2, NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY),
  3, 1, NULL, 2, NULL,
  1, '基准-OAuth人民币Adjust',
  NULL, NULL, NULL, NULL, NOW()
);

-- 场景4：独立集团、无 bloc_id、待完善客户政策
INSERT INTO apple_org_ext (
  id, org_id, bloc_id, bloc_name, customer_id, company_name, plat_username,
  status, is_delete, account_mtime, operator_id, operator_name, operator_mtime,
  attribution_type, attribution_mtime, updated_at,
  customer_type, settle_type, customer_policy, agent_type, agent_2nd_label,
  create_source, remark,
  creator_uid, creator_name, modifier_uid, modifier_name, created_at
) VALUES (
  700004, 710004, NULL, NULL, 'CUST-710004', '广州小而美互动科技有限公司', 'plat_user_004',
  3, 0, DATE_ADD(NOW(), INTERVAL 1 DAY), 90003, '运营王五', NOW(),
  0, DATE_SUB(NOW(), INTERVAL 500 DAY), NOW(),
  1, 2, '', NULL, '自由备注短语',
  2, '基准-无集团待完善',
  10003, '管理员', 10003, '管理员', NOW()
);

-- 场景5：冻结/异常类 status + 备注较长（未触达 200 上限）
INSERT INTO apple_org_ext (
  id, org_id, bloc_id, bloc_name, customer_id, company_name, plat_username,
  status, is_delete, account_mtime, operator_id, operator_name, operator_mtime,
  attribution_type, attribution_mtime, updated_at,
  customer_type, settle_type, customer_policy, agent_type, agent_2nd_label,
  create_source, remark,
  creator_uid, creator_name, modifier_uid, modifier_name, created_at
) VALUES (
  700005, 710005, 5003, '集团C', 'CUST-710005', '杭州某某文化创意有限公司', 'plat_user_005',
  4, 0, NOW(), 90004, '运营赵六', DATE_SUB(NOW(), INTERVAL 2 HOUR),
  3, NOW(), DATE_SUB(NOW(), INTERVAL 1 SECOND),
  2, 1, '政策C-特批', 3, 'OAuth代理混合',
  2, '基准-高 status 审计路径',
  10004, '管理员', 10004, '管理员', NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【二】apple_org_ext — VARCHAR(255) 边界（company_name：1 / 254 / 255 字符）
-- ═══════════════════════════════════════════════════════════

-- company_name 最小长度 1 字符
INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at,
  creator_uid, creator_name, created_at
) VALUES (
  700011, 710011, 'CUST-B-1', '甲', 'plat_v255_min',
  0, 0, NOW(), NOW(), NOW(), NOW(),
  1, '边界用例', NOW()
);

-- company_name 254 字符（最大长度-1）
INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at,
  creator_uid, creator_name, created_at
) VALUES (
  700012, 710012, 'CUST-B-254', REPEAT('乙', 254), 'plat_v255_254',
  0, 0, NOW(), NOW(), NOW(), NOW(),
  1, '边界用例', NOW()
);

-- company_name 255 字符（满长度）
INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at,
  creator_uid, creator_name, created_at
) VALUES (
  700013, 710013, 'CUST-B-255', REPEAT('丙', 255), 'plat_v255_max',
  0, 0, NOW(), NOW(), NOW(), NOW(),
  1, '边界用例', NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【三】apple_org_ext — status 多取值覆盖（业务若另有枚举请按实际替换）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at, created_at
) VALUES
  (700021, 710021, 'CUST-ST-0', '状态枚举行-status0', 'plat_s0', 0, 0, NOW(), NOW(), NOW(), NOW(), NOW()),
  (700022, 710022, 'CUST-ST-1', '状态枚举行-status1', 'plat_s1', 1, 0, NOW(), NOW(), NOW(), NOW(), NOW()),
  (700023, 710023, 'CUST-ST-2', '状态枚举行-status2', 'plat_s2', 2, 0, NOW(), NOW(), NOW(), NOW(), NOW()),
  (700024, 710024, 'CUST-ST-3', '状态枚举行-status3', 'plat_s3', 3, 0, NOW(), NOW(), NOW(), NOW(), NOW()),
  (700025, 710025, 'CUST-ST-4', '状态枚举行-status4', 'plat_s4', 4, 0, NOW(), NOW(), NOW(), NOW(), NOW());


-- ═══════════════════════════════════════════════════════════
-- 【四】apple_org_ext — 软删 is_delete=1（本表无 deleted_at 字段）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at, remark, created_at
) VALUES (
  700031, 710031, 'CUST-DEL-1', '已逻辑删除组织有限公司', 'plat_deleted',
  0, 1,
  NOW(), NOW(), NOW(), NOW(),
  '特殊状态-is_delete=1 占位', NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【五】apple_org_ext — 数值边界（operator_id：较小与较大 BIGINT）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  operator_id, account_mtime, operator_mtime, attribution_mtime, updated_at, created_at
) VALUES (
  700041, 710041, 'CUST-OP-MIN', '操作人ID偏小', 'plat_op_min',
  0, 0,
  0, NOW(), NOW(), NOW(), NOW(), NOW()
);

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  operator_id, account_mtime, operator_mtime, attribution_mtime, updated_at, created_at
) VALUES (
  700042, 710042, 'CUST-OP-MAX', '操作人ID极大占位', 'plat_op_max',
  0, 0,
  9223372036854775807, NOW(), NOW(), NOW(), NOW(), NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【六】apple_org_ext — 时间有效性感知（updated_at：过去 vs 未来一天）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at, remark, created_at
) VALUES (
  700051, 710051, 'CUST-T-PAST', '更新时间在过去', 'plat_t_past',
  0, 0, NOW(), NOW(), NOW(),
  DATE_SUB(NOW(), INTERVAL 30 DAY),
  '特殊状态-updated_at 早于 NOW', NOW()
);

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at, remark, created_at
) VALUES (
  700052, 710052, 'CUST-T-FUT', '更新时间在明天', 'plat_t_future',
  0, 0, NOW(), NOW(), NOW(),
  DATE_ADD(NOW(), INTERVAL 1 DAY),
  '特殊状态-updated_at 晚于 NOW（+1 天）', NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【七】apple_app_ext — 基准数据（5 条，display_status 1～5 各一条）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_app_ext (
  id, adam_id, display_status, region, new_customer_badge, full_1k_time,
  media_company_attribute, apple_direct_manager_uid, apple_direct_manager_name,
  own_genre_first, own_genre_second, own_genre_third,
  product_category, product_type, game_theme, game_play, art_style,
  attribution_type,
  creator_uid, creator_name, modifier_uid, modifier_name,
  ctime, mtime
) VALUES
(
  701001, 721001, 1, 1, 10, UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 10 DAY)),
  1, 200001, 'AM-张三',
  '手游', 'RPG', 'MMO',
  '网游', '内购', '仙侠', '副本', '国风',
  1,
  10001, '系统', 10001, '系统',
  NOW(), NOW()
),
(
  701002, 721002, 2, 2, 20, UNIX_TIMESTAMP(NOW()),
  2, 200002, 'AM-李四',
  '休闲', '益智', NULL,
  '休闲', '广告', '益智', '消除', '卡通',
  2,
  10001, '系统', 10001, '系统',
  NOW(), DATE_ADD(NOW(), INTERVAL 1 HOUR)
),
(
  701003, 721003, 3, 3, 30, NULL,
  1, NULL, NULL,
  NULL, NULL, NULL,
  '卡牌', '内购', '魔幻', '回合', '欧美卡通',
  3,
  NULL, NULL, NULL, NULL,
  DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()
),
(
  701004, 721004, 4, 4, 40, UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 400 DAY)),
  2, 200004, 'AM-王五',
  '应用', '工具', NULL,
  '应用', '订阅', '效率', '办公', '扁平',
  4,
  10002, '系统', 10002, '系统',
  NOW(), NOW()
),
(
  701005, 721005, 5, 5, 50, UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 2 DAY)),
  1, 200005, 'AM-赵六',
  '游戏', '竞技', 'MOBA',
  '网游', '竞技', 'MOBA', '5v5', '写实',
  5,
  10003, '系统', 10003, '系统',
  NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY)
);


-- ═══════════════════════════════════════════════════════════
-- 【八】apple_app_ext — VARCHAR(50) 边界（product_category：1 / 49 / 50）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_app_ext (
  id, adam_id, display_status, region, new_customer_badge, full_1k_time,
  product_category, product_type, game_theme, game_play, art_style,
  attribution_type, creator_uid, creator_name, ctime, mtime
) VALUES
(
  701011, 721011, 1, 1, 10, UNIX_TIMESTAMP(NOW()),
  '类', '未分配', '未分配', '未分配', '未分配',
  1, 1, '边界V50', NOW(), NOW()
),
(
  701012, 721012, 2, 2, 10, UNIX_TIMESTAMP(NOW()),
  REPEAT('类', 49), '未分配', '未分配', '未分配', '未分配',
  1, 1, '边界V49', NOW(), NOW()
),
(
  701013, 721013, 3, 3, 10, UNIX_TIMESTAMP(NOW()),
  REPEAT('类', 50), '未分配', '未分配', '未分配', '未分配',
  1, 1, '边界V50满', NOW(), NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【九】apple_app_ext — INT 边界（full_1k_time：0 与接近 INT 最大值）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_app_ext (
  id, adam_id, display_status, region, new_customer_badge, full_1k_time,
  product_category, product_type, game_theme, game_play, art_style,
  attribution_type, creator_uid, creator_name, ctime, mtime
) VALUES (
  701021, 721021, 1, 1, 40, 0,
  '未分配', '未分配', '未分配', '未分配', '未分配',
  1, 1, 'INT边界-min0', NOW(), NOW()
);

INSERT INTO apple_app_ext (
  id, adam_id, display_status, region, new_customer_badge, full_1k_time,
  product_category, product_type, game_theme, game_play, art_style,
  attribution_type, creator_uid, creator_name, ctime, mtime
) VALUES (
  701022, 721022, 2, 2, 40, 2147483647,
  '未分配', '未分配', '未分配', '未分配', '未分配',
  2, 1, 'INT边界-maxInt', NOW(), NOW()
);


-- ═══════════════════════════════════════════════════════════
-- 【十】apple_app_org_attr — 基准关联（5 条，customer_attribute 1/2/3 与组合场景）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_app_org_attr (
  id, adam_id, org_id, customer_attribute, is_delete,
  creator_uid, creator_name, modifier_uid, modifier_name,
  ctime, mtime
) VALUES
(702001, 721001, 710001, 1, 0, 10001, '系统', 10001, '系统', NOW(), NOW()),
(702002, 721002, 710002, 2, 0, 10001, '系统', 10001, '系统', NOW(), NOW()),
(702003, 721003, 710003, 3, 0, 10001, '系统', 10001, '系统', NOW(), NOW()),
(702004, 721004, 710004, 1, 0, 10002, '系统', 10002, '系统', DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
(702005, 721005, 710005, 2, 0, 10002, '系统', 10002, '系统', NOW(), DATE_ADD(NOW(), INTERVAL 30 MINUTE));


-- ═══════════════════════════════════════════════════════════
-- 【十一】apple_org_ext + apple_app_ext + apple_app_org_attr — 软删关联行（is_delete=1）
-- ═══════════════════════════════════════════════════════════

INSERT INTO apple_org_ext (
  id, org_id, customer_id, company_name, plat_username, status, is_delete,
  account_mtime, operator_mtime, attribution_mtime, updated_at, remark, created_at
) VALUES (
  700099, 710099, 'CUST-BRIDGE-DEL', '软删关联专用组织', 'plat_bridge_del',
  0, 0, NOW(), NOW(), NOW(), NOW(),
  '与 apple_app_org_attr 软删行配对', NOW()
);

INSERT INTO apple_app_ext (
  id, adam_id, display_status, region, new_customer_badge, full_1k_time,
  product_category, product_type, game_theme, game_play, art_style,
  attribution_type, creator_uid, creator_name, ctime, mtime
) VALUES (
  701099, 721099, 1, 1, 10, UNIX_TIMESTAMP(NOW()),
  '未分配', '未分配', '未分配', '未分配', '未分配',
  1, 1, '软删关联专用产品', NOW(), NOW()
);

INSERT INTO apple_app_org_attr (
  id, adam_id, org_id, customer_attribute, is_delete,
  creator_uid, creator_name, modifier_uid, modifier_name,
  ctime, mtime
) VALUES (
  702099, 721099, 710099, 1, 1,
  10001, '系统', 10001, '系统',
  NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY)
);
