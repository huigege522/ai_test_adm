# -*- coding: utf-8 -*-
"""同步 testpoints_基本信息管理.md 的「自动化是否覆盖」列。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "test_data/testpoints/basic_info/testpoints_基本信息管理.md"

OVERRIDE = {
    "TC041": "已覆盖",
    "TC042": "已覆盖",
    "TC044": "已覆盖",
    "TC033": "已覆盖",
    "TC212": "部分覆盖",
    "TC213": "部分覆盖",
    "TC305": "部分覆盖",
    "TC214": "已覆盖",
    "TC216": "已覆盖",
    "TC219": "已覆盖",
    "TC220": "已覆盖",
    "TC051": "部分覆盖",
    "TC024": "部分覆盖",
    "TC217": "已覆盖",
}


def main() -> None:
    content = MD_PATH.read_text(encoding="utf-8")
    test_files = list((ROOT / "tests").rglob("*basic_info*"))
    merged = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in test_files
    )
    blocked = (ROOT / "tests/api/basic_info/test_basic_info_blocked_skips.py").read_text(
        encoding="utf-8"
    )
    e2e = (
        ROOT / "tests/integration/basic_info/test_basic_info_management_e2e.py"
    ).read_text(encoding="utf-8")

    def classify(tc: str) -> str:
        if tc in OVERRIDE:
            return OVERRIDE[tc]
        base = tc.split("_")[0]
        if f"def test_{tc}" in blocked or (
            tc in blocked and "@pytest.mark.skip" in blocked
        ):
            return "skip占位"
        if re.search(rf"def test_\S*{re.escape(tc)}\S*\(", merged, re.I):
            if tc in e2e and re.search(
                rf"def test_\S*{re.escape(tc)}.*?\n.*?pytest\.skip",
                e2e,
                re.I | re.S,
            ):
                return "skip占位"
            return "已覆盖"
        if re.search(rf"def test_\S*{re.escape(base)}", merged, re.I) and base != tc:
            return "部分覆盖"
        if tc in merged:
            if re.search(rf'ids=.*{re.escape(tc)}', merged):
                return "已覆盖"
            return "部分覆盖"
        return "未覆盖"

    lines = content.splitlines()
    out: list[str] = []
    updated = 0
    for line in lines:
        m = re.match(r"\| (TC\d+(?:_\d+)?) \|", line)
        if m and "自动化是否覆盖" not in line and line.count("|") >= 9:
            tc = m.group(1)
            parts = line.split("|")
            if len(parts) >= 10:
                old = parts[-2].strip()
                new = classify(tc)
                if old != new:
                    parts[-2] = f" {new} "
                    updated += 1
                line = "|".join(parts)
        out.append(line)

    if "- 2026-05-21 —" not in content:
        patched: list[str] = []
        for line in out:
            patched.append(line)
            if line.strip().startswith("- 2026-05-20 —"):
                patched.append(
                    "- 2026-05-21 — 同步「自动化是否覆盖」列（对照 tests/**/test_basic_info*.py；"
                    "TC212/213 为 API 契约部分覆盖，UI 置灰见 E2E skip 占位）"
                )
        out = patched

    MD_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"updated rows: {updated}")


if __name__ == "__main__":
    main()
