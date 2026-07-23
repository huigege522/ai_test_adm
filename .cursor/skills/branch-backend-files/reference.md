# 分支 / 模块 → 后端 + 前端静态映射

路径相对于 **wanka 仓库根**。前后端**分支名分开**执行；`git diff` 无结果时用 `--module` + `--layer`。

---

## 命令速查

```bash
# 后端（apple_cmp_api 分支名）
python scripts/resolve_branch_backend.py --backend-branch <api分支>
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer backend

# 前端（apple_cmp_web 分支名，通常与 api 不同）
python scripts/resolve_branch_backend.py --frontend-branch <web分支>
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer frontend

# 已知两端分支名
python scripts/resolve_branch_backend.py --backend-branch <api> --frontend-branch <web>
```

---

## 基本信息管理（V3.24.x）

### 后端（apple_cmp_api）

| 角色 | 路径 |
|------|------|
| Controller | `apple_cmp_api/app/Http/Controllers/Asa/OrgManagementController.php` |
| Service | `apple_cmp_api/app/Services/Asa/OrgManagementService.php` |
| Controller | `apple_cmp_api/app/Http/Controllers/Asa/AppManagementController.php` |
| Service | `apple_cmp_api/app/Services/Asa/AppManagementService.php` |
| Controller | `apple_cmp_api/app/Http/Controllers/Asa/AppRelationManagementController.php` |
| Service | `apple_cmp_api/app/Services/Asa/AppRelationManagementService.php` |

**后端分支名关键词**：`基本信息`、`basic-info`、`org-management`、`app-management`

### 前端（apple_cmp_web）

| 角色 | 路径 | 说明 |
|------|------|------|
| 路由入口 | `apple_cmp_web/src/router/index.js` | `productManagement` → `productManagementNew` |
| API | `apple_cmp_web/src/api/manageCenter.js` | `org/*`、`app/*`、`apple-relation/*` |
| 壳层 Tab | `apple_cmp_web/src/views/managementCenter/productManagementNew/index.vue` | 三 Tab |
| 字典 | `.../productManagementNew/shared/dictHelper.js` | filterOptions |
| 账户 | `.../account/index.vue`、`AccountDialog.vue` | 6.1 |
| 产品 | `.../product/index.vue`、`ProductDialog.vue`、`ProductExtraEditDialog.vue` | 6.2 |
| 关系 | `.../accountAndProduct/index.vue`、`RelationDialog.vue` | 6.3 |

**旧版**：`apple_cmp_web/src/views/managementCenter/productManagement/index.vue`

**前端分支名关键词**：`productManagement`、`web-basic-info`、`management-center`

### 自动化（ai_test_adm，随 `--layer frontend`）

| 角色 | 路径 |
|------|------|
| Page Object | `ai_test_adm/tests/pages/basic_info_management_page.py` |
| E2E | `ai_test_adm/tests/integration/basic_info/test_basic_info_management_e2e.py` |

**E2E 路由**：`/managementCenter/productManagement`

---

## 竞品分析（示例）

### 后端

`AsaSovController.php` / `AsaSovService.php` — 使用 `--backend-branch` 或 `--layer backend`

### 自动化

`ai_test_adm/tests/api/test_asa_aso_competitor.py` — 无独立前端表时可只跑后端

---

## 扩展新模块

在 `scripts/resolve_branch_backend.py` 的 `MODULE_ALIASES` 中分别维护 `controllers`/`services` 与 `frontend`，并更新本节表格。
