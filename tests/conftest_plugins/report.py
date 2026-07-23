"""pytest-html 报告增强：HTTP 记录、断言步骤、失败详情渲染。"""
import json
import pytest

_http_calls: list = []


def record_http_call(method: str, url: str, request_body, status_code: int, response_body: str) -> None:
    """在测试辅助函数中调用，将一次 HTTP 交互追加到当前用例的记录列表。"""
    _http_calls.append({
        "method": method,
        "url": url,
        "req_body": request_body,
        "status": status_code,
        "resp_body": response_body,
    })


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    try:
        from pytest_html import extras as html_extras
    except ImportError:
        return

    extra = list(getattr(report, "extras", None) or [])

    # ── 结果徽章 ──
    badge_color = {"passed": "#28a745", "failed": "#dc3545", "skipped": "#6c757d"}.get(report.outcome, "#999")
    badge_html = (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:4px;'
        f'background:{badge_color};color:#fff;font-weight:bold;font-size:13px;">'
        f'{report.outcome.upper()}</span>'
    )
    extra.append(html_extras.html(badge_html))

    # ── docstring ──
    doc = item.function.__doc__
    if doc:
        doc_html = (
            f'<div style="margin:6px 0;padding:6px 10px;background:#f8f9fa;'
            f'border-left:3px solid #6c757d;color:#333;font-size:12px;">'
            f'<b>用例说明：</b>{doc.strip()}</div>'
        )
        extra.append(html_extras.html(doc_html))

    # ── HTTP 请求/响应详情 ──
    if _http_calls:
        rows = ""
        for i, call_info in enumerate(_http_calls, 1):
            try:
                resp_pretty = json.dumps(json.loads(call_info["resp_body"]), ensure_ascii=False, indent=2)[:2000]
            except Exception:
                resp_pretty = (call_info["resp_body"] or "")[:2000]

            req_display = ""
            if call_info["req_body"]:
                try:
                    req_display = json.dumps(call_info["req_body"], ensure_ascii=False, indent=2)
                except Exception:
                    req_display = str(call_info["req_body"])

            status_color = "#28a745" if 200 <= call_info["status"] < 300 else "#dc3545"
            rows += f"""
            <tr>
              <td style="padding:4px 8px;color:#555;">#{i}</td>
              <td style="padding:4px 8px;font-weight:bold;">{call_info['method']}</td>
              <td style="padding:4px 8px;word-break:break-all;">{call_info['url']}</td>
              <td style="padding:4px 8px;color:{status_color};font-weight:bold;">{call_info['status']}</td>
            </tr>
            <tr>
              <td colspan="4" style="padding:4px 8px;">
                {"<b>请求体：</b><pre style='margin:2px 0;background:#f4f4f4;padding:6px;font-size:11px;overflow-x:auto;'>" + req_display + "</pre>" if req_display else ""}
                <b>响应：</b>
                <pre style="margin:2px 0;background:#f4f4f4;padding:6px;font-size:11px;overflow-x:auto;">{resp_pretty}</pre>
              </td>
            </tr>"""

        table_html = f"""
        <div style="margin-top:8px;">
          <b style="font-size:13px;">HTTP 请求详情（共 {len(_http_calls)} 次调用）</b>
          <table style="width:100%;border-collapse:collapse;margin-top:4px;
                        border:1px solid #dee2e6;font-size:12px;">
            <thead>
              <tr style="background:#e9ecef;">
                <th style="padding:4px 8px;text-align:left;">#</th>
                <th style="padding:4px 8px;text-align:left;">Method</th>
                <th style="padding:4px 8px;text-align:left;">URL</th>
                <th style="padding:4px 8px;text-align:left;">Status</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""
        extra.append(html_extras.html(table_html))

    # ── 断言步骤明细 ──
    test_module = getattr(item, "module", None)
    steps = list(getattr(test_module, "_assert_steps", []))
    if steps:
        rows = ""
        for i, s in enumerate(steps, 1):
            icon = "✅" if s["passed"] else "❌"
            bg = "#f0fff4" if s["passed"] else "#fff0f0"
            border = "#28a745" if s["passed"] else "#dc3545"
            detail = f"<br><small style='color:#888;'>{s['detail']}</small>" if s.get("detail") else ""
            rows += (
                f'<tr style="background:{bg};">'
                f'<td style="padding:3px 8px;text-align:center;">{i}</td>'
                f'<td style="padding:3px 8px;border-left:3px solid {border};">'
                f'{icon}&nbsp;{s["desc"]}{detail}</td></tr>'
            )
        steps_html = (
            f'<div style="margin-top:8px;">'
            f'<b style="font-size:13px;">断言步骤（{len(steps)} 步，'
            f'通过 {sum(1 for s in steps if s["passed"])} / 失败 {sum(1 for s in steps if not s["passed"])}）</b>'
            f'<table style="width:100%;border-collapse:collapse;margin-top:4px;'
            f'border:1px solid #dee2e6;font-size:12px;">'
            f'<thead><tr style="background:#e9ecef;">'
            f'<th style="padding:3px 8px;width:36px;">#</th>'
            f'<th style="padding:3px 8px;text-align:left;">断言描述</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
        )
        extra.append(html_extras.html(steps_html))
        test_module._assert_steps.clear()

    # ── 失败详情 ──
    if report.outcome == "failed" and report.longrepr:
        err_text = str(report.longrepr)[-1500:]
        err_html = (
            f'<div style="margin-top:8px;">'
            f'<b style="color:#dc3545;">断言失败详情：</b>'
            f'<pre style="background:#fff0f0;padding:8px;font-size:11px;'
            f'border-left:3px solid #dc3545;overflow-x:auto;">{err_text}</pre></div>'
        )
        extra.append(html_extras.html(err_html))

    report.extras = extra
    _http_calls.clear()
