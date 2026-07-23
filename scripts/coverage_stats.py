# -*- coding: utf-8 -*-
"""统计 testpoints_基本信息管理.md 自动化覆盖情况。"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "test_data/testpoints/basic_info/testpoints_基本信息管理.md"

STATUSES = ("已覆盖", "部分覆盖", "skip占位", "未覆盖")


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    rows: list[dict] = []
    section = ""
    for line in md.splitlines():
        if line.startswith("## "):
            section = line.replace("## ", "").strip()
        if not line.startswith("| TC"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 10:
            continue
        tc = parts[1]
        if not re.match(r"TC\d", tc):
            continue
        cov = parts[-2]
        if cov not in STATUSES:
            continue
        rows.append(
            {
                "tc": tc,
                "section": section,
                "dim": parts[2],
                "prio": parts[5],
                "cov": cov,
            }
        )

    total = len(rows)
    by_cov = Counter(r["cov"] for r in rows)
    p0 = [r for r in rows if r["prio"] == "P0"]
    p0_cov = Counter(r["cov"] for r in p0)
    by_sec: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_sec[r["section"]][r["cov"]] += 1

    test_files = [
        p
        for p in (ROOT / "tests").rglob("*basic_info*")
        if p.is_file() and p.suffix == ".py"
    ]
    funcs = sum(
        len(re.findall(r"def test_", p.read_text(encoding="utf-8", errors="ignore")))
        for p in test_files
    )

    print("=" * 60)
    print("基本信息管理 · 自动化覆盖统计")
    print("数据源:", MD.relative_to(ROOT))
    print("=" * 60)

    print(f"\n【全量】测试点 {total} 条")
    for s in STATUSES:
        n = by_cov[s]
        pct = n / total * 100 if total else 0
        bar = "#" * int(pct / 2)
        print(f"  {s:8s} {n:3d} ({pct:5.1f}%) {bar}")

    traceable = by_cov["已覆盖"] + by_cov["部分覆盖"] + by_cov["skip占位"]
    runnable = by_cov["已覆盖"] + by_cov["部分覆盖"]
    print(f"\n  可追溯(含skip占位): {traceable} ({traceable/total*100:.1f}%)")
    print(f"  可执行(已+部分):     {runnable} ({runnable/total*100:.1f}%)")
    print(f"  完全未覆盖:         {by_cov['未覆盖']} ({by_cov['未覆盖']/total*100:.1f}%)")

    print(f"\n【P0】{len(p0)} 条")
    for s in STATUSES:
        n = p0_cov[s]
        pct = n / len(p0) * 100 if p0 else 0
        print(f"  {s:8s} {n:3d} ({pct:5.1f}%)")
    p0_run = p0_cov["已覆盖"] + p0_cov["部分覆盖"]
    print(f"  P0 可执行(已+部分): {p0_run} ({p0_run/len(p0)*100:.1f}%)")

    print("\n【按章节】")
    for sec in [
        "一、功能测试点",
        "二、边界值测试点",
        "三、异常测试点",
        "四、业务规则测试点",
        "五、集成（流程）测试点",
    ]:
        if sec not in by_sec:
            continue
        c = by_sec[sec]
        t = sum(c.values())
        ok = c["已覆盖"] + c["部分覆盖"]
        print(
            f"  {sec}: {t}条 | 可执行 {ok}({ok/t*100:.0f}%) "
            f"[已{c['已覆盖']} 部{c['部分覆盖']} skip{c['skip占位']} 未{c['未覆盖']}]"
        )

    print("\n【pytest 落地】")
    print(f"  文件数: {len(test_files)}")
    print(f"  test_* 函数: {funcs}")

    missing_p0 = [r["tc"] for r in p0 if r["cov"] == "未覆盖"]
    if missing_p0:
        print(f"\n【P0 未覆盖】{len(missing_p0)} 条:")
        print("  " + ", ".join(missing_p0))


if __name__ == "__main__":
    main()
