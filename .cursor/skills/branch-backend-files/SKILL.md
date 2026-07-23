---
name: branch-backend-files
description: >
  Resolves separate Git branch names for backend (apple_cmp_api) and frontend (apple_cmp_web)
  to Controller/Service or Vue/API/router @ paths. Use when branch names differ, for 阶段二-B,
  06 E2E, 交叉验证, or testpoints vs code diff. Run --backend-branch and --frontend-branch
  independently; do not assume one branch covers both repos.
---

# 分支 → 后端 + 前端代码文件（分支名分开）

## 重要约定

**`apple_cmp_api` 与 `apple_cmp_web` 的分支名通常不一致。**  
必须分别向用户确认（或分别使用）后端分支、前端分支，**禁止**用同一个分支名默认 diff 两端。

| 仓库 | 参数 | 典型分支命名 |
|------|------|----------------|
| `apple_cmp_api` | `--backend-branch` | `feature/api-*`、`fix/org-*` |
| `apple_cmp_web` | `--frontend-branch` | `feature/web-*`、`fix/product-mgmt-*` |

## 目标

| 层级 | 项目 | 解析方式 |
|------|------|----------|
| 后端 Controller / Service | `apple_cmp_api` | **仅** `--backend-branch` 的 git diff |
| 前端 API / 页面 / 路由 | `apple_cmp_web` | **仅** `--frontend-branch` 的 git diff |
| E2E Page Object | `ai_test_adm` | 随前端静态表或 `--module --layer frontend` |

---

## 一、后端执行步骤（apple_cmp_api）

在 `ai_test_adm` 目录，使用**后端仓库分支名**：

```bash
# 1) git diff 解析 Controller / Service
python scripts/resolve_branch_backend.py --backend-branch <api分支名>

# 可选：单独指定对比基准
python scripts/resolve_branch_backend.py --backend-branch <api分支名> --backend-base origin/main

# 2) 无分支或 diff 为空时：模块静态表（仅后端）
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer backend
```

**Agent 动作**：只 @ 输出中的 Controller、Service；不要在此步骤附带前端路径。

---

## 二、前端执行步骤（apple_cmp_web）

使用**前端仓库分支名**（与上一节可完全不同）：

```bash
# 1) git diff 解析 views / api / router
python scripts/resolve_branch_backend.py --frontend-branch <web分支名>

# 可选：单独指定对比基准
python scripts/resolve_branch_backend.py --frontend-branch <web分支名> --frontend-base origin/main

# 2) 无分支或 diff 为空时：模块静态表（仅前端 + E2E）
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer frontend
```

**Agent 动作**：只 @ 输出中的 `apple_cmp_web` 与 E2E 路径；区分 **`productManagementNew`** 与旧版 `productManagement`。

---

## 三、一次跑齐两端（已知两个分支名时）

```bash
python scripts/resolve_branch_backend.py \
  --backend-branch <api分支名> \
  --frontend-branch <web分支名>
```

输出为两段，中间用 `---` 分隔：先**后端分支**块，再**前端分支**块。仍应分别复制到 Cursor，不要混为一个分支名。

---

## 四、模块静态映射（无分支 / diff 失败）

```bash
# 仅后端
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer backend

# 仅前端 + E2E
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer frontend

# 前后端静态表各一段（仍分节输出）
python scripts/resolve_branch_backend.py --module 基本信息管理 --layer all
```

---

## 解析规则

| 层级 | 优先级 1 | 优先级 2 |
|------|----------|----------|
| 后端 | `git diff`：`Http/Controllers`、`Services` `.php` | [reference.md](reference.md) `--layer backend` |
| 前端 | `git diff`：`apple_cmp_web/src/{views,api,router}/` | [reference.md](reference.md) `--layer frontend` |

- 后端分支 diff **不会**自动补全前端文件，反之亦然。
- `FooController` 尽量配对 `FooService`。

---

## 与 Prompt 衔接

| 场景 | 步骤 |
|------|------|
| [01 交叉验证](../../prompts/01_req_to_testpoints.md) | 先 `--backend-branch`，再 `--frontend-branch` |
| [03 分支用例](../../prompts/03_code_to_cases.md) | 后端树与前端交互分支分开列 |
| [06 E2E](../../prompts/06_e2e_ui_flow.md) | 仅第二节前端 + E2E |
| [07 缺陷分析](../../prompts/07_defect_analysis.md) | 按缺陷落点选后端或前端分支 |

---

## 禁止

- 不要假设「一个分支名」同时适用于 api 与 web
- 不要臆造未在 diff 或静态表中的路径
- 不要用已废弃的「单参数同时 diff 前后端」方式（位置参数仅等同 `--backend-branch`）

## 附加资源

- 静态路径表：[reference.md](reference.md)
