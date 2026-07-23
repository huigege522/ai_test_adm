# Prompts 总览：AI 辅助测试

---

## 日常路径（80% 场景只用这一个）

**`main.md`** — 需求 → 测试点 + pytest 用例 + 断言，一步到位。

```
拿到需求 → 粘贴需求 + main.md → 得到 pytest 文件 → pytest tests/api/[模块]/ -v
```

---

## 按需取用（急救包）

| 场景 | Prompt | 说明 |
|------|--------|------|
| 需求 → 可运行用例 | `main.md` | **首选**，合并了测试点提取 + 用例生成 + 断言 |
| 接口文档不全，读代码补分支 | `03_code_to_cases.md` | 白盒分支覆盖 |
| 造数据库测试数据 | `04_db_schema_to_testdata.md` | baseline.sql + fixture |
| 浏览器 E2E 主路径 | `06_e2e_ui_flow.md` | Playwright P0 交互闭环 |
| 用例挂了要定位 | `07_defect_analysis.md` | 根因分析 + 回归建议 |

---

## 已归档

`01_req_to_testpoints`、`02_apifox_to_cases`、`05_assert_generation` 已合并到 `main.md`，原文件移至 `_archive/`。

---

## 常用命令

```bash
# API 测试
pytest tests/api/ -v

# 冒烟测试
pytest tests/ -m smoke -v

# UI E2E
pytest tests/integration/ -v -m e2e

# 并行 + HTML 报告
pytest tests/ -n auto -v --html=reports/report.html --self-contained-html
```
