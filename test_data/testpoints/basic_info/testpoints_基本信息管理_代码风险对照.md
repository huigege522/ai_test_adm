# 基本信息管理 — 测试点 vs 后端代码风险对照

> **对照范围**：`testpoints_基本信息管理.md`（V3.24.0.0.0）  
> **代码范围**：`apple_cmp_api` 下 5 个 Controller + 7 个 Service（见文首清单）  
> **生成日期**：2026-05-21  
> **说明**：仅基于当前仓库静态阅读；定时任务/前端逻辑若在其他仓库需另行核对。

---

## 一、需求中有但代码未实现（漏实现）

### 1.1 账户管理

⚠️ **风险**：国内主体企查查工商全称校验未接入。`QichachaService::checkDomestic()` 直接 `throw TipException('企查查接入待文档，暂未实现')`；`OrgManagementService::add()` 也未在提交前调用校验。  
**关联 TC**：TC008、TC208、TC229  
**建议验证**：调用 `POST org/checkCompany`（`is_overseas=false`）应失败；添加账户时不走企查查也能入库则确认漏实现。

⚠️ **风险**：海外主体客户名称「非空 + 唯一性」未在添加流程落地。`checkOverseas()` 仅校验英文格式，未查库去重；`add()` 不调用 `checkCompany`。  
**关联 TC**：TC009  
**建议验证**：用同一海外客户名连续添加两个不同 `org_id` 账户，观察是否都能成功（预期应拦截第二次）。

⚠️ **风险**：集团名称 ERP 每 5 分钟自动同步、字段不可编辑——后端无同步任务/接口，`bloc_name` 仅为 `add` 可选入参。  
**关联 TC**：TC016、TC320  
**建议验证**：查定时任务/ERP 集成仓库；添加账户不传 `bloc_name` 时列表是否长期为空。

⚠️ **风险**：添加账户「必须先校验 ORGID 再提交」无后端强制。`add()` 只校验 ext 重复与 ACL 拉数（且 ACL 当前为 Mock），不校验前端是否点过「校验」。  
**关联 TC**：TC303  
**建议验证**：跳过 `verifyOrgId`，直接 `POST org/add` 带合法新 `org_id`，看是否仍能入库。

⚠️ **风险**：`verifyOrgId` 真实 ACL 校验被 Mock 替代。`OrgManagementService::fetchOrgFromAcl()` 在 `return` 后写死测试数据，下方 `AppleAds::getUserAcl` 为死代码。  
**关联 TC**：TC011、TC210  
**建议验证**：对无效/未授权 `org_id` 调 `verifyOrgId`，若仍返回固定「6448880」类数据则属严重漏实现。

⚠️ **风险**：代理二代「有效性校验」（TC340 待确认）未实现，仅 `max:50` 长度校验，无白名单/格式规则。  
**关联 TC**：TC340、TC048  
**建议验证**：提交任意 50 字以内乱码作 `agent_2nd_label`，观察是否一律成功。

### 1.2 产品管理

⚠️ **风险**：产品单条编辑不支持「客户政策」。`AppManagementController::editableRules()` 无 `customer_policy`；需求 6.2.3 列出的可编辑项包含客户政策。  
**关联 TC**：TC026  
**建议验证**：`POST app/edit` 传 `customer_policy`，查库 `apple_app_ext` 是否无该列或未更新（客户政策在 `apple_org_ext` 层）。

⚠️ **风险**：新入库产品「产品大类/类型/题材/玩法/美术风格」库表虽有 `default('未分配')`，但 `add()` 经 `buildExtData` 未写入这些字段，依赖列表 `format()` 空值展示兜底，与「入库即默认未分配」可能不一致。  
**关联 TC**：TC027、TC306  
**建议验证**：添加产品后直接查 PolarDB `apple_app_ext` 五字段是 `未分配` 还是 `NULL`。

### 1.3 关系管理

⚠️ **风险**：关系管理「编辑」能力整体缺失。路由仅有 `list/add/delete`，无 `edit`；`AppRelationManagementController` 无编辑方法。  
**关联 TC**：TC035、TC223、TC235、TC332  
**建议验证**：Apifox/路由表确认无 `apple-relation/edit`；前端若保留编辑按钮则为纯前端或未接后端。

⚠️ **风险**：关系列表「备注」字段未实现。表 `apple_app_org_attr` 无 `remark` 列，`getList`/`format` 也未返回备注。  
**关联 TC**：TC031  
**建议验证**：调 `POST apple-relation/list`，核对响应 JSON 是否含 `remark`。

### 1.4 新客标识（核心业务缺口）

⚠️ **风险**：新客状态机自动流转未作用于新表 `apple_app_ext`。`UpdateAppStatusCommand`（`script:app_info_update`）仍更新旧表 `cmp_app_info` 及旧枚举 1–6，Console 中无 `apple_app_ext`/`new_customer_badge` 新枚举（10/20/30/40/50）的更新逻辑。  
**关联 TC**：TC037–TC039、TC056–TC058、TC117–TC119、TC127–TC128、TC238、TC313–TC319、TC336–TC339  
**建议验证**：新产品写入 `apple_app_ext.new_customer_badge=50` 后跑定时脚本，看新表字段是否仍不变；对比 `cmp_app_info` 是否被旧脚本改掉。

⚠️ **风险**：季度第 6 周媒体清单强制覆盖、优先级状态机、全新客禁止自动设置等规则在指定 Service/Controller 中无实现（需独立脚本或数据组任务，本批文件未发现）。  
**关联 TC**：TC039、TC057、TC318、TC319、TC336–TC338  
**建议验证**：全库搜「媒体清单」「Net New」「new_customer_badge」定时任务；构造满足条件产品观察 7 天内 badge 是否被自动改为 10（全新客）。

⚠️ **风险**：手动设置「全新客」后「90 天 15% 返点倒计时」无后端记录/计算逻辑（无专用字段、无事件写入）。  
**关联 TC**：TC039_1、TC058、TC128  
**建议验证**：编辑接口将 badge 改为 10 后查库及返点相关表是否有倒计时起始时间；若无则仅为前端展示或未做。

⚠️ **风险**：满 1k 美金时间按币种 UTC/UTC+8、每 2 小时更新——新链路未实现；旧脚本写 `cmp_app_info.full_1k_time`，与产品列表读的 `apple_app_ext.full_1k_time` 可能脱节。  
**关联 TC**：TC308、TC309、TC230  
**建议验证**：制造达标消耗后对比两表 `full_1k_time`；列表展示与脚本更新是否同源。

### 1.5 跨模块 / 前端专属（后端无对应）

⚠️ **风险**：添加账户成功「二次确认跳转产品页、仅预填账户 ID/名称」、弹窗字段裁剪、取消按钮等属前端交互，本批 PHP 无专门 API。  
**关联 TC**：TC014、TC022、TC053、TC054、TC061、TC062  
**建议验证**：E2E 或前端仓库；接口层无法覆盖。

---

## 二、代码中有但需求未提及的逻辑分支（隐藏逻辑）

⚠️ **风险**：`OrgManagementService::verifyOrgId()` 在 `tb_apple_org` 已存在 `org_id` 时直接抛「账户已存在」，未区分「仅主表有记录、ext 未建」场景；与注释中 `already_added` 设计不一致（下方死代码曾打算返回 `source=local`）。  
**建议验证**：ACL 预写入 `tb_apple_org` 但未 `add` ext 时调 `verifyOrgId`，是否误拦合法添加。

⚠️ **风险**：账户列表 `org_id` 筛选用 `LIKE '%id%'` 模糊匹配，需求 TC005 要求精确筛选唯一记录。  
**建议验证**：筛选用完整 `org_id` 与含其子串的另一 ID，对比返回条数。

⚠️ **风险**：账户/产品/关系列表排序均为 `orderByDesc('o.id'|'a.id'|'t.id')`，非需求所述「创建时间倒序」。  
**关联 TC**：TC002、TC020、TC341  
**建议验证**：连续新增两条记录，看列表是否按 id 而非 `created_at`/`ctime` 排序。

⚠️ **风险**：OAuth 授权 `AppleAdsController::handleAuthorization` 含大量隐藏副作用：撤销旧授权日志、按 `superOrgId` 写 `tb_apple_manage_mapping` 默认出价/预算、调数据组 ADM token 接口、`JutouService::batchAuthorize` 失败被空 `catch` 吞掉。  
**关联 TC**：TC040、TC304  
**建议验证**：OAuth 回调后查 mapping 表、聚投授权、账户列表 `create_source`；断网聚投时是否仍显示授权成功。

⚠️ **风险**：`upsertFromOAuth` 若 `apple_org_ext` 已存在则直接 `return`，不更新负责人/客户名/授权时间，重复授权可能列表信息陈旧。  
**建议验证**：同一 `org_id` 二次 OAuth，对比 `created_at`/负责人是否刷新。

⚠️ **风险**：`OrgManagementService::add/edit` 双写 `cmp_apple_account_base`（MySQL），需求文档未描述该兜底同步。  
**建议验证**：仅 PolarDB 有 ext、MySQL base 无记录时，其他「公司/账户」老页面是否看不到新户。

⚠️ **风险**：`AppManagementService::format()` 产品级 `customer_attribute` 用 `array_unique` 合并多账户属性，**不保证**与「录入顺序」一致（需求要求顺序与录入一致）。  
**关联 TC**：TC327  
**建议验证**：按代投→自投顺序建关系，看列表拼接顺序是否稳定。

⚠️ **风险**：`format()` 中 `agent_type` 展示规则：有 `cmp_apple_ads_accounts.active` 即标「OAuth」，否则按币种分人民币户/美元户——与账户「客户类型」字段（直客/代理/oAuth）是两套逻辑。  
**建议验证**：非 OAuth 直客账户在 OAuth 授权表有脏数据时，产品列表代理户展示是否错误。

⚠️ **风险**：`AdPlanController::getAppSelector` 对 `org_id=20012942` 且 `search=6756870744` 硬编码返回固定 App，需求未提及。  
**建议验证**：该组合调接口是否绕过权限与关系表。

⚠️ **风险**：广告推广 App 下拉：OAuth 判定用 `cmp_apple_ads_accounts`，非 OAuth 用 `apple_app_org_attr`；与账户管理 `customer_type=3` 判定源不一致，可能出现「账户管理标 oAuth、广告下拉走关系表」分裂。  
**关联 TC**：TC311  
**建议验证**：仅 ext 标 oAuth、ads 表无 active 记录时，`getAppSelector` 走哪条分支。

⚠️ **风险**：`AppManagementService::batchEdit` 对仅有 `tb_apple_app`、无 `apple_app_ext` 的 `adam_id` 会**自动 insert** ext 行，需求 6.2.4 未描述该补建行为。  
**建议验证**：对从未「添加产品」仅有关系的产品做批量编辑，是否凭空产生 ext 记录。

⚠️ **风险**：`AppRelationManagementService::add` 软删记录可「复活」（`reviveIds`），需求只描述新增与删除。  
**建议验证**：删除关系后同组合再次添加，看是新增行还是复活旧 `id`。

⚠️ **风险**：`syncManagers` 写 `tb_td_company_user` 同时更新 `operator_name`/`plat_username` 拼接串，并调用 `CompanyUserService::setYyOperationTime` 写运营变更日志——需求仅提媒体账户绑定展示。  
**关联 TC**：TC015、TC312  
**建议验证**：添加账户后查 `tb_td_sub_account_yy_operation_log` 是否多写运营日志。

⚠️ **风险**：添加产品 `syncAttributionToMmpAuth` 会反写 `apple_org_ext.attribution_type`（账户级），添加产品文档未说明改账户归因字段。  
**建议验证**：添加产品选 MMP 后查 `apple_org_ext.attribution_type` 是否被产品级归因覆盖。

---

## 三、可能存在的边界条件未处理问题

### 3.1 校验与长度

⚠️ **风险**：`org_id`/`adam_id` Controller 为 `numeric`，未限制最大位数；需求 TC106/107、TC108/109 要求 100 字/101 字边界，数据库列为 `unsignedBigInteger`，超长数字可能在 JSON/前端先溢出。  
**建议验证**：101 位数字字符串调 `add`/`verify`，看校验错误是 Laravel numeric 还是业务提示。

⚠️ **风险**：客户名称 `max:200`、客户政策 `max:100`、代理二代 `max:50` 与 TC101–105、TC124–125 一致，但**无最小长度**后端约束（TC103/126 依赖前端或人工）。  
**建议验证**：客户名称 1 字符、代理二代 1 字符提交是否成功。

⚠️ **风险**：海外客户名 `checkOverseas` 允许字符集与需求「英文名称」可能不一致（含数字、标点）。  
**建议验证**：客户名含中文或 emoji 调 `checkCompany(is_overseas=true)`。

### 3.2 新客标识状态转换

⚠️ **风险**：`app/edit` 允许 `new_customer_badge` 任意在 `10,20,30,40,50` 间跳转，无状态机约束（如全新客→孵化中禁止、老客→全新客禁止）。  
**关联 TC**：TC228、TC339  
**建议验证**：当前为「全新客」的产品 POST 改为 40；「老客」改为 10，接口是否均 200。

⚠️ **风险**：`full_1k_time` 编辑接口接受任意整数时间戳，无业务校验（未来时间、与 badge 联动等）。  
**建议验证**：写入未来日期或 0，列表「新客基数截止日期」计算是否异常。

### 3.3 列表展示与空数据

⚠️ **风险**：`org_name` 拼接 `implode('/', ...)` 时若 `org_name` 为空仍可能产出 `(org_id)` 或连续 `/`；空账户关联时 `customer_attribute` 为空字符串拼接。  
**关联 TC**：TC231、TC232、TC043  
**建议验证**：构造 `org_name` 为空或仅关系的 product，看 `org_name`/`customer_attribute` 列是否出现 `+/()` 异常片段。

⚠️ **风险**：关系列表按 `customer_attribute` 筛选使用 `whereIn`，一条关系一行；同一账户+产品多属性在列表为多行——与需求「组合展示」一致，但删除仅按 `id` 删单属性行，需求未强调「删一行是否等于删组合」。  
**建议验证**：三属性各一行时删其中一行，其余属性是否仍显示。

### 3.4 并发与唯一性

⚠️ **风险**：`add` 产品/关系对并发依赖 DB 唯一键 + `catch` 静默吞异常，第二次可能返回非明确「重复」错误。  
**关联 TC**：TC321  
**建议验证**：并发双请求同 `adam_id`+`org_id`，抓响应文案与 DB 行数。

⚠️ **风险**：`verifyAdamId` 提示 `already_added` 仅查 `AppleAppExt::exists`，不区分「仅有 app 主表无 ext」边缘态。  
**建议验证**：仅 `tb_apple_app` 有记录时校验接口返回是否误报已添加。

### 3.5 权限与依赖

⚠️ **风险**：OAuth `handleAuthorization` 失败时 `DB::rollBack` 后抛通用异常，ADM 通知失败会阻断整段授权（需求未定义）。  
**建议验证**：Mock ADM 接口 500，看 OAuth 是否仍落库 ads 账户。

⚠️ **风险**：`iTunes lookup` 校验产品超时 10s 无重试，弱网边界 TC229 类体验依赖外部 API。  
**建议验证**：Mock iTunes 超时，看 `verifyAdamId`/`add` 错误提示是否友好。

⚠️ **风险**：`edit` 账户时 `yy_uids`/`auth_uids` 可为空数组（`nullable|array` 无 `min:1`），可能清空全部负责人。  
**建议验证**：编辑提交 `yy_uids:[]`，媒体账户绑定是否变为无人。

---

## 四、已实现且与需求基本一致（抽查备忘）


| 能力                   | 代码位置                                                         | 备注                  |
| -------------------- | ------------------------------------------------------------ | ------------------- |
| 客户属性非必填（产品添加）        | `AppManagementController::add` `customer_attribute` nullable | 与 TC024/217 一致      |
| 关系三元组唯一性             | `AppRelationManagementService::add`                          | TC310/406           |
| 批量编辑空字段不改            | `batchEdit` + `buildExtData`                                 | TC307               |
| 账户名称多账户 `/` 拼接       | `AppManagementService::format` `org_name`                    | TC041/042           |
| 非 OAuth 推广 App 来自关系表 | `ApplePromotionManageService::getAppSelectorFromRelation`    | TC311（OAuth 判定源见上文） |
| 列表导出                 | `ExportCenter` + `ExportExcelTask`                           | TC018/030           |
| 代理二代非必填              | `org/add` nullable                                           | TC045               |


---

## 五、建议优先处理的缺陷（按业务影响）

1. **P0**：`fetchOrgFromAcl` Mock + 企查查未接入 → 账户/校验核心不可用（TC008/011/210/303）。
2. **P0**：新客状态机仍写旧表 → 基本信息管理新客需求整体失效（TC313–339）。
3. **P1**：关系编辑与备注缺失（TC031/035）。
4. **P1**：`new_customer_badge` 无状态转换校验（TC228/339）。
5. **P2**：列表排序/精确筛选与需求不一致（TC002/005/341）。

---

**文档维护**：代码变更后请重新 diff 上述 Service/Controller，并同步更新本文件与 `testpoints_基本信息管理.md` 的「自动化是否覆盖」列。