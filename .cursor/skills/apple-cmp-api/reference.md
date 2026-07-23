# apple_cmp_api — 速查

在仓库根目录执行的检索示例（按需替换关键词）。

```bash
rg "apple_campaign_third_report" app/
rg "tb_apple_af_campaign" app/
rg "getRecordList" routes/api.php app/Http/Controllers/Asa/
rg "tb_td_sys_operation_log" app/
rg "applyFilters" app/Services/SmartAds/KeywordService.php
```

## 关键路径（文件）

- `routes/api.php`
- `app/Services/SmartAds/KeywordService.php`
- `app/Services/Asa/TaskMonitorService.php`
- `app/Services/Asa/AsaLogService.php`
- `app/Services/Panel/QueryBuilderService.php`
- `app/Services/DataInsight/Support/InsightFieldRegistry.php`
- `app/Models/Doris/DorisDb.php`（连接名常量/切换逻辑；**勿**把凭据抄进文档）
- `config/database.php`（`doris_jutou`）
