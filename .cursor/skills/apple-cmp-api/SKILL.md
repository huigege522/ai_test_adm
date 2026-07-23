---
name: apple-cmp-api
description: Navigates the apple_cmp_api Laravel 12 / PHP 8.2 backend for Apple Ads CMP (智能投放、ASA、数据面板、Doris 报表、托管与系统日志). Use when editing this repository, tracing API routes, report/SQL table names, permissions, or SmartAds/Asa/Panel/Mmp modules.
disable-model-invocation: true
---

# apple_cmp_api 项目上下文

（项目技能：`.cursor/skills/apple-cmp-api/`；若个人目录另有 `~/.cursor/skills/apple-cmp-api/`，改其中一处时请同步另一处以防漂移。）

本技能汇总仓库结构与高信号代码位置，避免每次从零扫全库。具体实现以代码为准；改表名或路由后应同步更新本文件。

## 技术栈

- Laravel 12，PHP ^8.2
- 多数据源：业务 MySQL（大量 `cmp_*` 表）、Doris 分析库（连接名 **`doris_jutou`**，见 `config/database.php`；Eloquent/查询入口常通过 `App\Models\Doris\DorisDb`）
- 权限：路由上 `middleware('per:...')` + `App\Services\Permission\PermissionService` 等
- 多语言：`resources/lang/`（如 `zh_CN`）

## 路由入口

- 主 API：`routes/api.php`（含重复分组，改路由注意是否两处都要改）
- 认证：多数业务在「登录 + Session」分组内；部分仅 `Authenticate`
- 权限中间件：`per:regulation`、`per:extension.view`、`per:monitoring.view`、`per:hosting` 等，以具体路由为准

## 按业务域找代码（Controllers → Services）

| 域 | 典型 Controller | 典型 Service / 说明 |
|----|-----------------|---------------------|
| 智能投放 / 拓词 / 竞价词 | `SmartAds/KeywordController`, `AsaKeywordController` | `App\Services\SmartAds\KeywordService`（词库列表筛选 `applyFilters`、`cmp_keyword_details`） |
| 实时 SOV 监控 | `AsaMonitor/AsaMonitorController` | `App\Models\AsaMonitor\AsaMonitorTask::createTask`；写系统日志 `SysOperationLogService` |
| 智能托管 / 自动出价 | `Asa/AutoBiddingController`, `Asa/TaskMonitorController` | `App\Services\Asa\TaskMonitorService`（如 `getTaskMonitorRecordList`） |
| 数据洞察 2.0 | `DataInsight/*` | `App\Services\DataInsight/*`、`InsightFieldRegistry` |
| 面板 / 指标 | `Panel/PanelController` | `App\Services\Panel\QueryBuilderService` |
| 广告管理 / Apple 投放 | `Ad/*`, `AdMange/*`, `ApplePromotionManageController` | `App\Services\Ad\*`、`AdMange\*` |
| MMP / 三方 | `Asa/MmpController` | `App\Services\Asa\MmpService` |
| 系统操作日志（ADM 列表） | `Asa/AsaLogController`（以实际路由为准） | `App\Services\Asa\AsaLogService::getList`，表 **`tb_td_sys_operation_log`** |

## Doris / 报表表名（易变，改需求时重点搜）

- **Campaign 三方日报（新表，Doris）**：`apple_campaign_third_report_utc`（UTC）、`apple_campaign_third_report_utc8`（ORTZ/UTC8 场景以代码分支为准）
- **仍可能存在的旧表名**（全库 `rg`）：`tb_apple_af_campaign_utc_daily_report`、`tb_apple_af_campaign_daily_report` — 见于 `QueryBuilderService::getReportQuery`（旧）、`Task/DataReports/*`、`DataDashboardService` 等路径；与 `getReportQueryNew` 等新路径并存
- **数据洞察三方源**：`App\Services\DataInsight\Support\InsightFieldRegistry` 中 `third_report` 与日/小时表映射
- **元数据拉数**：`App\Services\Task\Metadata\ReportDataService` 内 `af_daily` 等别名

## 托管 / 触发记录

- 自动出价触发列表：`AutoBiddingController::getRecordList` → `TaskMonitorService::getTaskMonitorRecordList(..., CmpTaskAlert::TYPE_2)`
- 返回字段 **`alert_name`** 对应库表 **`cmp_task_execute_log.alert_name`**（别名 `re`），非 `cmp_task_alert` 上同名字段

## 系统日志与数据权限

- `AsaLogService::getList`：按 `PermissionService::getAuthAccount` 得到 `org_id` 列表，并 **merge `999999`** 再 `whereIn('l.org_id', ...)` — 带 `org_id=999999` 的日志（如部分「实时 SOV 监控」写入）会对所有具备该可见性的用户展示
- 写入：`App\Services\Util\SysOperationLogService::addAll` → `tb_td_sys_operation_log`

## 应用 / 产品

- 团队应用库：`cmp_applications`（模型 `App\Models\Applications\Applications`），含 `team_id`、`app_id`
- 新增功能若涉及「仅可操作本团队已授权 App」，需在 Service 层显式校验；勿假设路由层已拦截

## 测试

- PHPUnit 配置：`phpunit.xml`；示例用例在 `tests/Unit`、`tests/Feature`，**覆盖有限**
- Doris/报表相关需求：通常需自备 SQL 联调或对生成 SQL 做断言，勿仅依赖现成用例
- 本仓库 `ai_test_adm` 的 API/DB 自动化见 `ai-test-adm-project-overview`、`testpoints-to-automation`；后端分支 diff 见 `branch-backend-files`

## 维护本技能

- 大改路由、 Doris 表名或权限模型后，在本文件更新对应小节
- 常用 `rg` 与路径清单见 [reference.md](reference.md)
