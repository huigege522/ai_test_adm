# -*- coding: utf-8 -*-
"""
根据 Git 分支名列出变更的后端 Controller/Service 或前端 apple_cmp_web 文件，输出 Cursor @ 路径。

前后端分支名通常不同，请分别指定：
  python scripts/resolve_branch_backend.py --backend-branch <api分支>
  python scripts/resolve_branch_backend.py --frontend-branch <web分支>
  python scripts/resolve_branch_backend.py --backend-branch <api> --frontend-branch <web>

模块静态映射：
  python scripts/resolve_branch_backend.py --module 基本信息管理 --layer backend
  python scripts/resolve_branch_backend.py --module 基本信息管理 --layer frontend

仓库根默认为 ai_test_adm 的上级（含 apple_cmp_api/、apple_cmp_web/）。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 模块别名 → 静态映射（git diff 无结果时使用）
MODULE_ALIASES: dict[str, dict] = {
    "基本信息管理": {
        "controllers": [
            "apple_cmp_api/app/Http/Controllers/Asa/OrgManagementController.php",
            "apple_cmp_api/app/Http/Controllers/Asa/AppManagementController.php",
            "apple_cmp_api/app/Http/Controllers/Asa/AppRelationManagementController.php",
        ],
        "services": [
            "apple_cmp_api/app/Services/Asa/OrgManagementService.php",
            "apple_cmp_api/app/Services/Asa/AppManagementService.php",
            "apple_cmp_api/app/Services/Asa/AppRelationManagementService.php",
        ],
        "frontend": {
            "api": [
                "apple_cmp_web/src/api/manageCenter.js",
            ],
            "views": [
                "apple_cmp_web/src/views/managementCenter/productManagementNew/index.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/shared/dictHelper.js",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/account/index.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/account/AccountDialog.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/product/index.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/product/ProductDialog.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/product/ProductExtraEditDialog.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/accountAndProduct/index.vue",
                "apple_cmp_web/src/views/managementCenter/productManagementNew/accountAndProduct/RelationDialog.vue",
            ],
            "router": [
                "apple_cmp_web/src/router/index.js",
            ],
            "e2e": [
                "ai_test_adm/tests/pages/basic_info_management_page.py",
                "ai_test_adm/tests/integration/basic_info/test_basic_info_management_e2e.py",
            ],
        },
    },
    "竞品分析": {
        "controllers": [
            "apple_cmp_api/app/Http/Controllers/Asa/AsaSovController.php",
        ],
        "services": [
            "apple_cmp_api/app/Services/Asa/AsaSovService.php",
        ],
        "frontend": {
            "views": [],
            "api": [],
            "router": [],
            "e2e": [
                "ai_test_adm/tests/api/test_asa_aso_competitor.py",
            ],
        },
    },
}

FRONTEND_DIFF_PREFIXES = (
    "apple_cmp_web/src/views/",
    "apple_cmp_web/src/api/",
    "apple_cmp_web/src/router/",
)
FRONTEND_EXTENSIONS = (".vue", ".js", ".ts", ".tsx")


def _run_git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "git failed").strip())
    return r.stdout.strip()


def _resolve_base(base: str | None, cwd: Path) -> str:
    if base:
        return base
    for candidate in ("origin/main", "main", "master", "develop"):
        try:
            _run_git(["rev-parse", "--verify", candidate], cwd)
            return candidate
        except RuntimeError:
            continue
    return "HEAD~1"


def _branch_exists(branch: str, cwd: Path) -> bool:
    try:
        _run_git(["rev-parse", "--verify", branch], cwd)
        return True
    except RuntimeError:
        return False


def _changed_backend_paths(branch: str, base: str, cwd: Path) -> list[str]:
    out = _run_git(
        ["diff", f"{base}...{branch}", "--name-only", "--diff-filter=ACMR"],
        cwd,
    )
    paths = []
    for line in out.splitlines():
        p = line.strip().replace("\\", "/")
        if not p.endswith(".php"):
            continue
        if "/Http/Controllers/" in p or "/Services/" in p:
            paths.append(p)
    return paths


def _changed_frontend_paths(branch: str, base: str, cwd: Path) -> list[str]:
    out = _run_git(
        ["diff", f"{base}...{branch}", "--name-only", "--diff-filter=ACMR"],
        cwd,
    )
    paths = []
    for line in out.splitlines():
        p = line.strip().replace("\\", "/")
        if not p.endswith(FRONTEND_EXTENSIONS):
            continue
        if any(p.startswith(prefix) for prefix in FRONTEND_DIFF_PREFIXES):
            paths.append(p)
    return sorted(set(paths))


def _pair_controller_service(paths: list[str]) -> tuple[list[str], list[str]]:
    controllers = sorted(p for p in paths if "/Http/Controllers/" in p)
    services_set = {p for p in paths if "/Services/" in p and p.endswith("Service.php")}
    services: list[str] = []
    paired: set[str] = set()
    for c in controllers:
        stem = Path(c).stem.replace("Controller", "")
        guess = (
            c.replace("/Http/Controllers/", "/Services/")
            .replace("Controller.php", "Service.php")
        )
        if Path(guess).stem != f"{stem}Service":
            parts = c.split("/")
            guess = (
                "/".join(parts[:-1])
                .replace("Http/Controllers", "Services")
                + f"/{stem}Service.php"
            )
        svc = guess if guess in services_set else None
        if svc is None:
            for s in services_set:
                if Path(s).stem == f"{stem}Service":
                    svc = s
                    break
        if svc:
            services.append(svc)
            paired.add(svc)
    for s in sorted(services_set - paired):
        services.append(s)
    return controllers, services


def _flatten_frontend(fe: dict | None) -> dict[str, list[str]]:
    if not fe:
        return {"api": [], "views": [], "router": [], "e2e": []}
    return {
        "api": list(fe.get("api") or []),
        "views": list(fe.get("views") or []),
        "router": list(fe.get("router") or []),
        "e2e": list(fe.get("e2e") or []),
    }


def _normalize_branch(branch: str, cwd: Path) -> str | None:
    if _branch_exists(branch, cwd):
        return branch
    if not branch.startswith("origin/") and _branch_exists(f"origin/{branch}", cwd):
        return f"origin/{branch}"
    return None


def _classify_frontend_paths(paths: list[str]) -> dict[str, list[str]]:
    frontend: dict[str, list[str]] = {"api": [], "views": [], "router": [], "e2e": []}
    for p in paths:
        if "/src/api/" in p:
            frontend["api"].append(p)
        elif "/src/router/" in p:
            frontend["router"].append(p)
        elif "/src/views/" in p:
            frontend["views"].append(p)
    return frontend


def _format_backend_output(
    branch: str,
    base: str,
    source: str,
    controllers: list[str],
    services: list[str],
) -> str:
    lines = [
        f"## 后端分支 `{branch}`（对比 `{base}`，来源：{source}）",
        "",
        "### Controller（apple_cmp_api）",
    ]
    if controllers:
        lines.extend(f"- `@{p}`" for p in controllers)
    else:
        lines.append("- （无）")

    lines.extend(["", "### Service（apple_cmp_api）"])
    if services:
        lines.extend(f"- `@{p}`" for p in services)
    else:
        lines.append("- （无）")

    lines.extend(["", "### 复制到 Cursor（后端 / API 用例 / 交叉验证）", "", "```"])
    if controllers:
        lines.append("阅读以下 Controller：")
        lines.extend(f"@{p}" for p in controllers)
    if services:
        lines.append("阅读以下 Service：")
        lines.extend(f"@{p}" for p in services)
    lines.append("```")
    return "\n".join(lines)


def _format_frontend_output(
    branch: str,
    base: str,
    source: str,
    frontend: dict[str, list[str]],
    *,
    include_e2e: bool = True,
) -> str:
    api = frontend.get("api") or []
    views = frontend.get("views") or []
    router = frontend.get("router") or []
    e2e = frontend.get("e2e") or [] if include_e2e else []

    lines = [
        f"## 前端分支 `{branch}`（对比 `{base}`，来源：{source}）",
        "",
        "### API（apple_cmp_web）",
    ]
    lines.extend(f"- `@{p}`" for p in api) if api else lines.append("- （无）")

    lines.extend(["", "### 页面 / 组件（apple_cmp_web）"])
    lines.extend(f"- `@{p}`" for p in views) if views else lines.append("- （无）")

    lines.extend(["", "### 路由（apple_cmp_web）"])
    lines.extend(f"- `@{p}`" for p in router) if router else lines.append("- （无）")

    if e2e:
        lines.extend(["", "### E2E / Page Object（ai_test_adm）"])
        lines.extend(f"- `@{p}`" for p in e2e)

    lines.extend(["", "### 复制到 Cursor（前端 / 06 E2E / UI 交叉验证）", "", "```"])
    if api:
        lines.append("阅读以下前端 API 封装：")
        lines.extend(f"@{p}" for p in api)
    if views:
        lines.append("阅读以下前端页面/组件：")
        lines.extend(f"@{p}" for p in views)
    if router:
        lines.append("阅读以下路由配置：")
        lines.extend(f"@{p}" for p in router)
    for p in e2e:
        lines.append(f"@{p}")
    lines.append("```")
    return "\n".join(lines)


def _match_module_alias(name: str) -> str | None:
    for key in MODULE_ALIASES:
        if key in name or name in key:
            return key
        if key.replace("管理", "") in name:
            return key
    return None


def resolve_by_module(module: str, layer: str = "all") -> str | None:
    key = _match_module_alias(module)
    if not key:
        return None
    data = MODULE_ALIASES[key]
    source = f"静态映射「{key}」"
    parts: list[str] = []
    if layer in ("backend", "all"):
        parts.append(
            _format_backend_output(
                module, "模块别名", source, data["controllers"], data["services"]
            )
        )
    if layer in ("frontend", "all"):
        parts.append(
            _format_frontend_output(
                module, "模块别名", source, _flatten_frontend(data.get("frontend"))
            )
        )
    return "\n\n---\n\n".join(parts)


def _resolve_backend_from_branch(
    branch: str, base: str, cwd: Path, *, fallback_module: str | None
) -> str | None:
    ref = _normalize_branch(branch, cwd)
    if not ref:
        if fallback_module:
            return resolve_by_module(fallback_module, layer="backend")
        return None
    try:
        paths = _changed_backend_paths(ref, base, cwd)
    except RuntimeError:
        raise
    controllers, services = _pair_controller_service(paths)
    if not controllers and not services:
        if fallback_module:
            return resolve_by_module(fallback_module, layer="backend")
        return None
    return _format_backend_output(ref, base, "git diff", controllers, services)


def _resolve_frontend_from_branch(
    branch: str, base: str, cwd: Path, *, fallback_module: str | None
) -> str | None:
    ref = _normalize_branch(branch, cwd)
    if not ref:
        if fallback_module:
            return resolve_by_module(fallback_module, layer="frontend")
        return None
    try:
        paths = _changed_frontend_paths(ref, base, cwd)
    except RuntimeError:
        raise
    frontend = _classify_frontend_paths(paths)
    if fallback_module and not any(frontend.values()):
        static = _flatten_frontend(MODULE_ALIASES.get(fallback_module, {}).get("frontend"))
        frontend = {k: static[k] for k in frontend}
    if not any(frontend.values()):
        if fallback_module:
            return resolve_by_module(fallback_module, layer="frontend")
        return None
    if fallback_module:
        static = _flatten_frontend(MODULE_ALIASES[fallback_module].get("frontend"))
        if not frontend.get("e2e"):
            frontend["e2e"] = static.get("e2e") or []
    return _format_frontend_output(ref, base, "git diff", frontend)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="分别按后端/前端 Git 分支解析 @ 路径（分支名可不同）"
    )
    parser.add_argument(
        "branch",
        nargs="?",
        help="已废弃：请改用 --backend-branch（等同仅解析后端）",
    )
    parser.add_argument("--backend-branch", help="apple_cmp_api 对应分支名")
    parser.add_argument("--frontend-branch", help="apple_cmp_web 对应分支名")
    parser.add_argument("--base", help="对比基准（未指定分层 base 时共用）")
    parser.add_argument("--backend-base", help="后端 diff 基准分支")
    parser.add_argument("--frontend-base", help="前端 diff 基准分支")
    parser.add_argument("--module", help="模块别名，如 基本信息管理")
    parser.add_argument(
        "--layer",
        choices=("backend", "frontend", "all"),
        default="all",
        help="与 --module 联用：仅后端 / 仅前端 / 全部静态表（默认 all）",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=REPO_ROOT,
        help="monorepo 根（含 apple_cmp_api、apple_cmp_web）",
    )
    args = parser.parse_args()
    cwd = args.repo

    if args.module:
        text = resolve_by_module(args.module, args.layer)
        if text:
            print(text)
            return 0
        print(f"未知模块: {args.module}", file=sys.stderr)
        print("可用:", ", ".join(MODULE_ALIASES), file=sys.stderr)
        return 1

    backend_branch = args.backend_branch or args.branch
    frontend_branch = args.frontend_branch

    if not backend_branch and not frontend_branch:
        parser.print_help()
        print(
            "\n示例:\n"
            "  --backend-branch feature/api-basic-info\n"
            "  --frontend-branch feature/web-product-mgmt\n"
            "  --module 基本信息管理 --layer backend",
            file=sys.stderr,
        )
        return 1

    if args.branch and not args.backend_branch:
        print(
            "提示: 位置参数分支仅解析后端；前端请单独使用 --frontend-branch",
            file=sys.stderr,
        )

    backend_base = _resolve_base(args.backend_base or args.base, cwd)
    frontend_base = _resolve_base(args.frontend_base or args.base, cwd)

    outputs: list[str] = []
    exit_code = 0

    if backend_branch:
        alias = _match_module_alias(backend_branch)
        try:
            text = _resolve_backend_from_branch(
                backend_branch, backend_base, cwd, fallback_module=alias
            )
        except RuntimeError as e:
            print(f"后端 git diff 失败: {e}", file=sys.stderr)
            return 1
        if text:
            outputs.append(text)
        else:
            print(f"后端分支无映射变更: {backend_branch}", file=sys.stderr)
            print(
                "提示: --module 基本信息管理 --layer backend",
                file=sys.stderr,
            )
            exit_code = 1

    if frontend_branch:
        alias = _match_module_alias(frontend_branch)
        try:
            text = _resolve_frontend_from_branch(
                frontend_branch, frontend_base, cwd, fallback_module=alias
            )
        except RuntimeError as e:
            print(f"前端 git diff 失败: {e}", file=sys.stderr)
            return 1
        if text:
            outputs.append(text)
        else:
            print(f"前端分支无映射变更: {frontend_branch}", file=sys.stderr)
            print(
                "提示: --module 基本信息管理 --layer frontend",
                file=sys.stderr,
            )
            exit_code = 1 if not outputs else exit_code or 1

    if outputs:
        print("\n\n---\n\n".join(outputs))
        return 0

    return exit_code or 1


if __name__ == "__main__":
    sys.exit(main())
