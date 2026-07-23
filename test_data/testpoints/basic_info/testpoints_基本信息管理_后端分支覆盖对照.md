# 基本信息管理 — 后端 Controller/Service 分支覆盖对照

> **代码范围**：`apple_cmp_api` 所列 5 Controller + 7 Service  
> **测试对照**：`ai_test_adm/tests/api/basic_info/test_basic_info_*.py`（账户/产品/关系/列表契约）  
> **生成日期**：2026-05-21  
> **图例**：`[已覆盖]` = 存在对应用例且能走到该分支；`[⚠️ 未覆盖]` = 无对应用例或仅 skip 占位

---

## 一、OrgManagementController

### getList
- [getList]
  - ├── 分支1: `export === 1` → 创建 `ExportCenter` 异步任务，返回离线下载提示 `[已覆盖]`（`test_basic_info_management.test_导出开关为1` / `test_basic_info_accounts` 间接）
  - └── 分支2: `export !== 1` → 调 `OrgManagementService::getList` 返回分页 JSON `[已覆盖]`（`test_正常获取账户列表_JSON分页`、TC003/004/005/006）

### filterOptions / parentOrgList / verifyOrgId / checkCompany / add / edit
- [filterOptions]
  - └── 无 if/else（直调 `AppManagementService::filterOptions`）`[⚠️ 未覆盖]`（无独立用例）
- [parentOrgList]
  - └── 无分支 `[⚠️ 未覆盖]`
- [verifyOrgId]
  - └── 无分支（校验失败走 Laravel validate）`[已覆盖]` 负例 TC210；正例 TC011 `[已覆盖]`
- [checkCompany]
  - └── 无分支（透传 Service）`[⚠️ 未覆盖]`（`test_basic_info_blocked_skips` skip）
- [add]
  - └── 无分支（透传 Service）`[已覆盖]` TC007/TC045；负例 TC201–207/209
- [edit]
  - └── 无分支 `[已覆盖]` TC017；负例 TC212/213

---

## 二、OrgManagementService

### getList
- [getList]
  - ├── 分支1: `export === 1` → 全量查询 + `format`，无分页 `[部分覆盖]`（仅 Controller 层 export=1 任务，未断言导出文件内容）
  - └── 分支2: `export !== 1` → 分页 `forPage` + total `[已覆盖]`

### verifyOrgId
- [verifyOrgId]
  - ├── 分支1: `tb_apple_org` 已存在该 `org_id` → `TipException('账户已存在')` `[已覆盖]`（TC011 skip 路径：已存在 org）
  - ├── 分支2: **其后代码不可达**（146 行 `return fetchOrgFromAcl` 后仍有 dead code：本地命中返回 valid）`[⚠️ 未覆盖]`
  - └── 分支3: `fetchOrgFromAcl` → 当前 **Mock 固定返回**，未走真实 ACL `[部分覆盖]`（TC011 在 Mock 下通过，非 TC210 真实失败）

### checkCompany
- [checkCompany]
  - ├── 分支1: `is_overseas === true` → `QichachaService::checkOverseas` `[⚠️ 未覆盖]`
  - └── 分支2: `is_overseas === false` → `checkDomestic` → **抛「企查查接入待文档」** `[⚠️ 未覆盖]`（blocked skip TC008/208）

### add
- [add]
  - ├── 分支1: `tb_apple_org` 无行 → `parent_org_id` 空 → `TipException` `[⚠️ 未覆盖]`
  - ├── 分支2: `tb_apple_org` 无行 → 调 `fetchOrgFromAcl` 插入主表 `[部分覆盖]`（依赖 Mock ACL）
  - ├── 分支3: `apple_org_ext` 未删重复 → `TipException org_id_duplicate` `[部分覆盖]`（TC211 未专门断言）
  - ├── 分支4: ext 软删行存在 `is_delete=0` → 重复 `[⚠️ 未覆盖]`
  - ├── 分支5: ext 软删行 `is_delete=1` → update 复活 `[⚠️ 未覆盖]`
  - ├── 分支6: ext 不存在 → `insertGetId` `[已覆盖]`（TC007）
  - ├── 分支7: `syncManagers(..., isAdd=true)` 全量覆盖负责人 `[已覆盖]`（TC007 含 yy/auth）
  - └── 分支8: `syncToAccountBase` try/catch 失败仅打日志 `[⚠️ 未覆盖]`

### edit
- [edit]
  - ├── 分支1: ext 不存在 → `org_ext_not_found` `[⚠️ 未覆盖]`
  - ├── 分支2: 更新 ext 字段 `[已覆盖]` TC017
  - ├── 分支3: 请求含 `yy_uids` 和/或 `auth_uids` → `syncManagers` 局部更新 `[部分覆盖]`（编辑用例未断言负责人）
  - └── 分支4: 未传负责人字段 → 不同步 `[⚠️ 未覆盖]`

### upsertFromOAuth
- [upsertFromOAuth]
  - ├── 分支1: `org_id` 空 → return `[⚠️ 未覆盖]`
  - ├── try 分支2: 主表已存在 → update / 不存在 → insert `[⚠️ 未覆盖]`（OAuth 全流程 skip TC040）
  - ├── 分支3: ext 已存在 → return 不插入 `[⚠️ 未覆盖]`
  - ├── 分支4: ext 不存在 → insert OAuth 行 `[⚠️ 未覆盖]`
  - └── catch: 仅 warning 日志 `[⚠️ 未覆盖]`

### syncManagers（private）
- [syncManagers]
  - ├── 分支1: `isAdd` → 软删该 org 全部运营/授权 `[部分覆盖]`
  - ├── 分支2: `yyUids !== null` → 处理运营桶 `[已覆盖]`
  - ├── 分支3: `authUids !== null` → 处理授权桶 `[已覆盖]`
  - ├── 分支4: `!isAdd` → 按 type 软删再写入 `[⚠️ 未覆盖]`
  - ├── 分支5: `uid <= 0` → continue `[⚠️ 未覆盖]`
  - ├── 分支6: 用户记录 exists → update is_delete=0 / else insert `[⚠️ 未覆盖]`
  - ├── 分支7: 运营桶 → 写 `operator_name` + `setYyOperationTime`（firstOp 有值）`[⚠️ 未覆盖]`
  - └── 分支8: 授权桶 → 写 `plat_username` `[⚠️ 未覆盖]`

### fetchOrgFromAcl
- [fetchOrgFromAcl]
  - ├── 分支1: **TODO Mock 直接 return**（真实 ACL 不可达）`[部分覆盖]`
  - ├── 分支2: ACL 失败或空 → `org_id_invalid` `[⚠️ 未覆盖]`（TC210 在 Mock 下无法触发）
  - └── 分支3: 遍历 ACL 匹配 orgId `[⚠️ 未覆盖]`

### baseQuery（筛选）
- [baseQuery]
  - ├── `bloc_search` 非空 → like `[已覆盖]` TC003
  - ├── `company_search` 非空 → like `[已覆盖]` TC004
  - ├── `org_id` 非空 → like `[已覆盖]` TC005
  - ├── `org_name` 非空 → like `[已覆盖]` TC060
  - ├── `customer_type` 非空 → 等值 `[部分覆盖]`
  - └── `agent_2nd_label` 非空 → 等值 `[⚠️ 未覆盖]`

### prefetchManagers / format
- [prefetchManagers]
  - ├── `orgIds` 空 → 空 map `[⚠️ 未覆盖]`
  - └── 非空 → 分 type 聚合 + cmp_user 名 `[已覆盖]`（列表含 yy_users_name）
- [format]
  - └── 枚举映射（customer_type/settle/create_source 等）`[已覆盖]` TC006

---

## 三、AppManagementController

### getList
- [getList]
  - ├── 分支1: `export === 1` → 异步导出任务 `[已覆盖]`（`test_TC019_导出开关为1`）
  - └── 分支2: 列表 JSON `[已覆盖]` TC019

### verifyAdamId / add / edit / batchEdit
- [verifyAdamId]
  - └── 无分支 `[已覆盖]` TC023；负例 adam 缺失/无效
- [add]
  - └── 无分支 `[已覆盖]` TC024/添加成功；负例 TC214–220
- [edit]
  - └── 无分支 `[已覆盖]` TC026
- [batchEdit]
  - └── 无分支 `[⚠️ 未覆盖]`（`PATH_APP_BATCH_EDIT` 已映射但无 pytest）

---

## 四、AppManagementService

### getList
- [getList]
  - ├── 分支1: `resolveAdamIdSet` 非 null 且空集 → 空列表 `[⚠️ 未覆盖]`（筛选组合无结果）
  - ├── 分支2: `export === 1` → 全量 `[部分覆盖]`
  - └── 分支3: 分页列表 `[已覆盖]`

### verifyAdamId
- [verifyAdamId]
  - ├── 分支1: `org` 不存在 → `valid=false, org_id_invalid` `[部分覆盖]`
  - ├── 分支2: `currency === RMB` → iTunes `cc=cn` / 否则 `us` `[⚠️ 未覆盖]`（未断言币种分支）
  - ├── 分支3: `lookupItunesApp` 返回 null → invalid `[已覆盖]`（`test_不存在Adam`）
  - └── 分支4: 命中 → `already_added` 查 ext `[已覆盖]` TC023

### lookupItunesApp（private）
- [lookupItunesApp]
  - ├── 分支1: adam_id 非 6–13 位数字 → null `[⚠️ 未覆盖]`
  - ├── try: HTTP 非 ok → null `[⚠️ 未覆盖]`
  - ├── try: results 空 → null `[⚠️ 未覆盖]`
  - ├── try: 解析 secondary_genre 循环 `[已覆盖]`（成功路径）
  - └── catch: 打日志返回 null `[⚠️ 未覆盖]`

### add
- [add]
  - ├── 分支1: `verifyAdamId` invalid → TipException `[部分覆盖]`
  - ├── 分支2: `already_added` → duplicate `[⚠️ 未覆盖]`
  - ├── 分支3: `orgRow` 不存在 → org_id_invalid `[⚠️ 未覆盖]`
  - ├── 分支4: `upsertAppleApp` `[已覆盖]`
  - ├── 分支5: `new_customer_badge` 空 → 默认 INACTIVE(50) `[⚠️ 未覆盖]`（TC037）
  - ├── 分支6: `customer_attribute` 数组 → `upsertAppOrgAttrs`（可空）`[已覆盖]` TC024
  - └── 分支7: `attribution_type` 非空 → `syncAttributionToMmpAuth` `[部分覆盖]`（TC025 skip）

### upsertAppleApp / upsertRelation / upsertAppOrgAttrs
- [upsertAppleApp]
  - ├── exists → update `[⚠️ 未覆盖]`
  - ├── 不存在 → insert；catch 并发 update `[⚠️ 未覆盖]`
- [upsertRelation]
  - ├── exists → return `[⚠️ 未覆盖]`
  - └── insert；catch 吞异常 `[⚠️ 未覆盖]`
- [upsertAppOrgAttrs]
  - ├── attr 非法 → continue（静默跳过）`[⚠️ 未覆盖]`
  - ├── row 存在 → 复活 `[⚠️ 未覆盖]`
  - └── row 不存在 → insert `[已覆盖]`（随 add）

### edit
- [edit]
  - ├── 分支1: ext 不存在 → not_data `[⚠️ 未覆盖]`
  - ├── 分支2: `buildExtData` 空 → 直接返回 `[⚠️ 未覆盖]`
  - ├── 分支3: 有更新字段 → update ext `[已覆盖]` TC026
  - └── 分支4: 传 `attribution_type` → 对每个 relation org 同步 MMP `[⚠️ 未覆盖]`

### batchEdit
- [batchEdit]
  - ├── 分支1: `adam_ids` 空 → not_data `[⚠️ 未覆盖]`
  - ├── 分支2: 无字段可更新 → `affected:0` `[⚠️ 未覆盖]`
  - ├── 分支3: 部分 adam 无 ext 但在 tb_apple_app → 批量 insert ext `[⚠️ 未覆盖]`
  - ├── 分支4: denied（app 表也无）→ not_data `[⚠️ 未覆盖]`
  - ├── 分支5: update 已有 ext `[⚠️ 未覆盖]`
  - └── 分支6: 含 attribution_type → 多 org 同步 MMP `[⚠️ 未覆盖]`

### buildExtData / syncAttributionToMmpAuth
- [buildExtData]
  - ├── 列未传 → continue `[部分覆盖]`
  - ├── 值 null/'' → continue `[⚠️ 未覆盖]`
  - ├── `apple_direct_manager` 非空 → 写 name 清 uid `[⚠️ 未覆盖]`
  - └── `isCreate` → 写 creator `[已覆盖]`（add 路径）
- [syncAttributionToMmpAuth]
  - ├── `plateMap` 无映射 → return `[⚠️ 未覆盖]`
  - ├── try 更新 org_ext attribution `[⚠️ 未覆盖]`
  - ├── CmpMmpAuth 存在 → update / else create `[部分覆盖]`
  - └── time_zone/start_date 可选覆盖 `[⚠️ 未覆盖]`

### resolveAdamIdSetByCrossFilters（private，筛选核心）
- [resolveAdamIdSetByCrossFilters]
  - ├── `org_search` → 交集空则 return [] `[部分覆盖]`（org_search 筛选未单测）
  - ├── ext 筛选 company/bloc/customer_type/policy `[部分覆盖]` TC003/004
  - ├── `customer_attribute` → attr 表反查 `[⚠️ 未覆盖]`（产品列表筛选项）
  - ├── `yy_uids` / `auth_uids` → 反查 org `[⚠️ 未覆盖]`
  - ├── 无任何反查约束 → return null `[已覆盖]`（默认列表）
  - └── orgIdSet + attr 交集 → 返回 adam 集 `[⚠️ 未覆盖]`

### format（列表聚合）
- [format]
  - ├── 空 rows → [] `[⚠️ 未覆盖]`
  - ├── 多 org 拼接 `org_name` 用 `/` `[已覆盖]` TC042
  - ├── 单 org `名称(id)` `[已覆盖]` TC041
  - ├── 多 customer_attribute `/` `[已覆盖]` TC044
  - └── OAuth org 标记等 `[⚠️ 未覆盖]`

### filterOptions
- [filterOptions]
  - └── 无业务分支（空 union 返回 []）`[⚠️ 未覆盖]`

---

## 五、AppRelationManagementController

### getList / add / delete
- [getList]
  - └── 无分支 `[已覆盖]` TC031
- [add]
  - └── 无分支 `[已覆盖]` TC034/310；负例 TC222/240
- [delete]
  - └── 无分支 `[已覆盖]` TC036

---

## 六、AppRelationManagementService

### getList
- [getList]
  - ├── 各筛选字段非空（adam_id/app_name/org_id/org_name/customer_type/customer_attribute）`[部分覆盖]`（仅列表无筛选用例）
  - └── 分页 orderByDesc id `[已覆盖]`

### add
- [add]
  - ├── `assertAdamIdExists` 失败 `[⚠️ 未覆盖]`
  - ├── `assertOrgIdExists` 失败 `[⚠️ 未覆盖]`
  - ├── `attrs` 空 → TipException `[已覆盖]`（客户属性必填）
  - ├── attr 非法值 → invalid `[⚠️ 未覆盖]`
  - ├── existing `is_delete=0` → hardConflict TipException `[已覆盖]` TC310
  - ├── existing `is_delete=1` → reviveIds `[⚠️ 未覆盖]`
  - ├── `upsertRelation` `[已覆盖]`
  - ├── revive 更新 `[⚠️ 未覆盖]`
  - └── newAttrs insert `[已覆盖]` TC034

### delete
- [delete]
  - ├── 行不存在或已删 → not_data `[⚠️ 未覆盖]`
  - └── 软删成功 `[已覆盖]` TC036

### upsertRelation（private）
- [upsertRelation]
  - ├── exists → return `[⚠️ 未覆盖]`
  - └── insert；catch 并发 `[⚠️ 未覆盖]`

### filterOptions
- [filterOptions]
  - ├── pairs 空 → app/org 列表空 `[⚠️ 未覆盖]`
  - └── 非空 → 构建下拉 `[⚠️ 未覆盖]`

---

## 七、AppleAdsController（与 6.1 OAuth 联动）

### redirectToApple
- [redirectToApple]
  - ├── `parentOrgId` 不在配置 → Exception `[⚠️ 未覆盖]`
  - └── 正常拼 OAuth URL `[⚠️ 未覆盖]`

### getUserId / getTeamId
- [getUserId]
  - ├── try 成功 → user.id `[⚠️ 未覆盖]`
  - └── catch → 0 `[⚠️ 未覆盖]`
- [getTeamId]
  - └── 同上 `[⚠️ 未覆盖]`

### handleAuthorization（核心，节选）
- [handleAuthorization]
  - ├── `state` 空 → TipException `[⚠️ 未覆盖]`
  - ├── decode 用户不存在 → Not Logged In `[⚠️ 未覆盖]`
  - ├── `getUserId` 为 0 → Not Logged In `[⚠️ 未覆盖]`
  - ├── parentOrgId 配置缺失 → Exception `[⚠️ 未覆盖]`
  - ├── token 请求 `failed` → Exception `[⚠️ 未覆盖]`
  - ├── 无 access_token → Exception `[⚠️ 未覆盖]`
  - ├── ACL `failed` → Exception `[⚠️ 未覆盖]`
  - ├── ACL http_code != 200 → Exception `[⚠️ 未覆盖]`
  - ├── try 事务：
  - │   ├── 有旧 active 账户 → 撤销 logs `[⚠️ 未覆盖]`
  - │   ├── 有 account → update revoked / res 失败抛错 `[⚠️ 未覆盖]`
  - │   ├── token updateOrCreate 失败 `[⚠️ 未覆盖]`
  - │   ├── foreach aclAccounts：
  - │   │   ├── 无 orgId/parentOrgId → continue `[⚠️ 未覆盖]`
  - │   │   ├── superDisplayName 有/无 → displayName 分支 `[⚠️ 未覆盖]`
  - │   │   ├── superCurrency 首次赋值 `[⚠️ 未覆盖]`
  - │   │   ├── accountId 空 → Exception `[⚠️ 未覆盖]`
  - │   │   ├── log create 失败 `[⚠️ 未覆盖]`
  - │   │   └── **upsertFromOAuth** 写入 6.1 可见 `[⚠️ 未覆盖]`（TC040 skip）
  - │   └── commit
  - ├── catch → rollBack `[⚠️ 未覆盖]`
  - ├── orgIds 非空 → Jutou batchAuthorize；**内层 catch 空吞** `[⚠️ 未覆盖]`
  - ├── `superOrgId` 非空：
  - │   ├── `superCurrency` 非空 → switch config id 1–7（含 RMB/非 RMB 出价）`[⚠️ 未覆盖]`
  - │   └── ADM 通知 POST success/fail `[⚠️ 未覆盖]`
  - └── redirect 账户授权页 `[⚠️ 未覆盖]`

### normalizeAclAccounts（private）
- [normalizeAclAccounts]
  - ├── orgId 空 → continue `[⚠️ 未覆盖]`
  - ├── parentOrgId null → 超管账号分支 `[⚠️ 未覆盖]`
  - ├── parentOrgId 0 → rootAclInfo `[⚠️ 未覆盖]`
  - ├── 子账号归并 superOrgId `[⚠️ 未覆盖]`
  - └── 仅 root → 补齐 normalized `[⚠️ 未覆盖]`

### getList（授权账户列表，非 6.1 但同 Controller）
- [getList]
  - ├── display_search / org_search / status / date 筛选 `[⚠️ 未覆盖]`
  - ├── 非 admin 且非 demon → 限制 user_id `[⚠️ 未覆盖]`
  - ├── date_sort 有/无 → 排序分支 `[⚠️ 未覆盖]`
  - ├── export → 全量 / 分页 `[⚠️ 未覆盖]`
  - └── 列表 role_names：Admin / API Campaign Manager / Read Only / 其他 `[⚠️ 未覆盖]`

---

## 八、AdPlanController（推广 APP 下拉 · TC311 联动）

### getAppSelector
- [getAppSelector]
  - ├── 分支1: 硬编码测试 `search=6756870744 & org_id=20012942` → 固定返回 `[⚠️ 未覆盖]`
  - ├── 分支2: `org_id` 不在用户授权列表 → 空数组 `[⚠️ 未覆盖]`
  - ├── 分支3: 调 `ApplePromotionManageService::getAppSelector`
  - │   ├── `!bool` → 空数组 `[⚠️ 未覆盖]`
  - │   └── 成功 → 返回 data `[⚠️ 未覆盖]`（无 test_basic_info_* 用例）
  - └── 分支4: （Service 内）OAuth vs 非 OAuth 见下节

---

## 九、ApplePromotionManageService::getAppSelector

- [getAppSelector]
  - ├── 分支1: `cmp_apple_ads_accounts` 无 active OAuth → `getAppSelectorFromRelation` `[⚠️ 未覆盖]`
  - └── 分支2: 存在 active OAuth 账户：
      - ├── org.currency==RMB 且 search 非空 → `returnOwnedApps=false` `[⚠️ 未覆盖]`
      - ├── `AppleAds::searchForIOSApps` 失败 → Result false `[⚠️ 未覆盖]`
      - ├── data 空 → 无匹配产品 `[⚠️ 未覆盖]`
      - └── 成功组装 list `[⚠️ 未覆盖]`

- [getAppSelectorFromRelation]（private）
  - ├── search 非空 → like app_name/adam_id `[⚠️ 未覆盖]`
  - ├── rows 空 → 无匹配 `[⚠️ 未覆盖]`
  - └── 有数据 → Result true `[⚠️ 未覆盖]`

---

## 十、QichachaService

- [checkDomestic]
  - └── 直接 `throw TipException('企查查接入待文档')` `[⚠️ 未覆盖]`（skip TC008/208）

- [checkOverseas]
  - ├── 名称为空 → valid false `[⚠️ 未覆盖]`
  - ├── 非英文字符 → valid false `[⚠️ 未覆盖]`
  - └── 通过格式校验 → valid true `[⚠️ 未覆盖]`（TC009 海外唯一性未测）

---

## 十一、ExportExcelTask

### run
- [run]
  - ├── try: exportRecord 不存在 → Exception `[⚠️ 未覆盖]`
  - ├── status !== STATUS_1 → Exception `[⚠️ 未覆盖]`
  - ├── performTask 成功 → return true `[⚠️ 未覆盖]`
  - └── catch → TaskException `[⚠️ 未覆盖]`

### performTask
- [performTask]
  - ├── match `MODULE_APP_MANAGEMENT` + sign：
  - │   ├── `APP_MANAGEMENT_ORG_LIST` → OrgManagementService::exportToFile `[部分覆盖]`（仅 API export=1 建任务，未测 worker）
  - │   ├── `APP_MANAGEMENT_APP_LIST` → AppManagementService::exportToFile `[部分覆盖]`
  - │   └── default → 无此任务 `[⚠️ 未覆盖]`
  - ├── 其他 module → 无此任务 `[⚠️ 未覆盖]`
  - ├── upload 无 link → Exception `[⚠️ 未覆盖]`
  - ├── unlink 本地文件 `[⚠️ 未覆盖]`
  - └── catch → saveTaskStatus 失败态 `[⚠️ 未覆盖]`

---

## 十二、AppleAds::getUserAcl

- [getUserAcl]
  - └── 无分支（HTTP GET 封装）`[⚠️ 未覆盖]`（生产路径被 OrgManagementService Mock 绕过）

---

## 十三、覆盖统计摘要

| 模块 | 大致已覆盖 | 明显缺口 |
|------|-----------|----------|
| 账户 list/增删改校验 | list、add、edit、verify 正/负例 | export 文件内容、checkCompany、parentOrgList、filterOptions、OAuth upsert、ACL 真失败、软删复活 |
| 产品 list/增删改 | list、verify、add、edit、展示格式 | **batchEdit**、筛选反查组合、already_added、MMP 同步、新客默认态 |
| 关系 list/增删 | list、add 多选、delete、重复拦截 | 软删复活、筛选、filterOptions |
| OAuth/广告下拉 | — | AppleAdsController 全链路、getAppSelector OAuth/关系分支 |
| 异步导出 worker | API 建任务 | ExportExcelTask performTask 全分支 |
| 企查查 | — | domestic + overseas 有效路径 |

---

## 十四、优先补测建议（⚠️ 未覆盖且业务风险高）

1. `OrgManagementService::verifyOrgId` 去掉 Mock 后覆盖 TC210 / TC211  
2. `app/batchEdit` 空字段不改、影响条数（TC028/029/307）  
3. `org/checkCompany` domestic/overseas（TC008/009/208）  
4. `AppRelationManagementService::add` 软删复活路径  
5. `ApplePromotionManageService::getAppSelector` 非 OAuth 走 `apple_app_org_attr`（TC311）  
6. `ExportExcelTask` 对 `APP_MANAGEMENT_*_LIST` 的集成测（导出文件列）

---

**文档标识**：`[后端] testpoints_基本信息管理_后端分支覆盖对照.md`
