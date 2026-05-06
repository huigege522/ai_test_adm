"""
全局 pytest fixture：
  - db_conn        : MySQL 连接，function 级别，自动提交 + 自动回滚清理
  - db_cursor      : 基于 db_conn 的游标
  - load_baseline  : 执行 test_data/baseline.sql 插入基准数据
  - polar_db_conn  : PolarDB 连接（兼容 MySQL 协议），function 级别，自动回滚
  - polar_db_cursor: 基于 polar_db_conn 的游标
  - http_session   : requests.Session，携带 BASE_URL 与认证头
  - login_session  : requests.Session，通过 /api/login/sub2 自动登录后的已认证 Session

数据库说明：
  - MySQL   → DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD
  - PolarDB → POLAR_DB_HOST / POLAR_DB_PORT / POLAR_DB_NAME / POLAR_DB_USER / POLAR_DB_PASSWORD
  两套数据库均通过 PyMySQL 连接（PolarDB 兼容 MySQL 协议，无需额外驱动）。
  未配置 POLAR_DB_HOST 时，polar_db_pool 自动 skip，不影响仅使用 MySQL 的用例。

登录优先级：
  1. 若 LOGIN_USERNAME + LOGIN_PASSWORD 已配置 → 调用 /api/login/sub2 自动登录
  2. 若仅配置了 AUTH_COOKIE → 直接注入 Cookie 请求头
  3. 两者均未配置 → 抛出 pytest.skip，跳过需要认证的用例
"""
import os
import json
import logging
import pymysql
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL        = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
AUTH_TOKEN      = os.getenv("AUTH_TOKEN", "")
AUTH_COOKIE     = os.getenv("AUTH_COOKIE", "")
LOGIN_USERNAME  = os.getenv("LOGIN_USERNAME", "")
LOGIN_PASSWORD  = os.getenv("LOGIN_PASSWORD", "")
LOGIN_URL       = f"{BASE_URL}/api/login/sub2"

DB_CONFIG = {
    "host":        os.getenv("DB_HOST", "127.0.0.1"),
    "port":        int(os.getenv("DB_PORT", "3306")),
    "db":          os.getenv("DB_NAME", "test_db"),
    "user":        os.getenv("DB_USER", "root"),
    "password":    os.getenv("DB_PASSWORD", ""),
    "charset":     "utf8mb4",
    "autocommit":  False,
    "cursorclass": pymysql.cursors.DictCursor,
}

# PolarDB 兼容 MySQL 协议，直接使用 PyMySQL 连接；未配置 POLAR_DB_HOST 时为 None
POLAR_DB_CONFIG = {
    "host":        os.getenv("POLAR_DB_HOST", ""),
    "port":        int(os.getenv("POLAR_DB_PORT", "3306")),
    "db":          os.getenv("POLAR_DB_NAME", "test_db"),
    "user":        os.getenv("POLAR_DB_USER", "root"),
    "password":    os.getenv("POLAR_DB_PASSWORD", ""),
    "charset":     "utf8mb4",
    "autocommit":  False,
    "cursorclass": pymysql.cursors.DictCursor,
} if os.getenv("POLAR_DB_HOST") else None

SQL_BASELINE = os.path.join(os.path.dirname(__file__), "..", "test_data", "baseline.sql")
SQL_CLEANUP = os.path.join(os.path.dirname(__file__), "..", "test_data", "cleanup.sql")


# ──────────────────────────────────────────────
# 数据库 fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def db_pool():
    """会话级：建立一次连接池（单连接模拟），会话结束后关闭。"""
    conn = pymysql.connect(**DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_conn(db_pool):
    """函数级：每个用例独立事务，用例结束后回滚，保持数据隔离。"""
    db_pool.ping(reconnect=True)
    yield db_pool
    db_pool.rollback()


@pytest.fixture(scope="function")
def db_cursor(db_conn):
    """函数级：基于 db_conn 的 DictCursor，用例结束自动关闭。"""
    cursor = db_conn.cursor()
    yield cursor
    cursor.close()


@pytest.fixture(scope="function")
def load_baseline(db_conn):
    """
    函数级：执行 test_data/baseline.sql 插入基准数据。
    用例结束后执行 cleanup.sql 清理，再回滚事务。

    用法：
        def test_something(load_baseline, db_cursor):
            ...
    """
    _exec_sql_file(db_conn, SQL_BASELINE)
    db_conn.commit()
    yield
    _exec_sql_file(db_conn, SQL_CLEANUP)
    db_conn.commit()


@pytest.fixture(scope="session")
def polar_db_pool():
    """
    会话级：PolarDB 连接（兼容 MySQL 协议）。
    未配置 POLAR_DB_HOST 时自动跳过，不影响仅使用 MySQL 的用例。
    """
    if POLAR_DB_CONFIG is None:
        pytest.skip("未配置 POLAR_DB_HOST，跳过需要 PolarDB 的用例")
    conn = pymysql.connect(**POLAR_DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def polar_db_conn(polar_db_pool):
    """函数级：每个用例独立事务，用例结束后回滚，保持数据隔离。"""
    polar_db_pool.ping(reconnect=True)
    yield polar_db_pool
    polar_db_pool.rollback()


@pytest.fixture(scope="function")
def polar_db_cursor(polar_db_conn):
    """函数级：基于 polar_db_conn 的 DictCursor，用例结束自动关闭。"""
    cursor = polar_db_conn.cursor()
    yield cursor
    cursor.close()


def _exec_sql_file(conn, filepath):
    """执行 SQL 文件（以 ; 分隔的多条语句）。"""
    if not os.path.exists(filepath):
        return
    with open(filepath, encoding="utf-8") as f:
        sql_text = f.read()
    with conn.cursor() as cur:
        for stmt in sql_text.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)


# ──────────────────────────────────────────────
# 登录辅助函数
# ──────────────────────────────────────────────

def do_login(username: str, password: str) -> requests.Session:
    """
    调用 POST /api/login/sub2 完成账密登录。
    登录成功后 requests.Session 会自动保存服务端返回的 Set-Cookie，
    后续请求无需手动传 Cookie。

    接口参数：
      username  string  必填
      password  string  必填
      captcha   object  必填  测试环境传 {"ticket": "1234", "randstr": "1234"} 绕过验证码
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })

    payload = {
        "username": username,
        "password": password,
        "captcha": {
            "ticket":  "1234",
            "randstr": "1234",
        },
    }

    try:
        resp = session.post(LOGIN_URL, json=payload, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"登录请求异常：{e}") from e

    if resp.status_code != 200:
        raise RuntimeError(
            f"登录失败，HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )

    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(
            f"登录业务错误，code={body.get('code')}，message={body.get('message')}"
        )

    logger.info("登录成功，用户：%s", body.get("data", {}).get("username"))
    return session


def _make_session_with_cookie(cookie: str) -> requests.Session:
    """使用手动 Cookie 构造 Session（备用方案）。"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": cookie,
    })
    return session


# ──────────────────────────────────────────────
# HTTP Session fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def login_session() -> requests.Session:
    """
    会话级：已完成认证的 requests.Session。

    优先级：
      1. LOGIN_USERNAME + LOGIN_PASSWORD → /api/login/sub2 自动登录
      2. AUTH_COOKIE → 注入 Cookie 头（备用）
      3. 均未配置 → pytest.skip

    用法：
        def test_something(login_session):
            resp = login_session.get(f"{BASE_URL}/api/keyword/getApp", ...)
    """
    if LOGIN_USERNAME and LOGIN_PASSWORD:
        logger.info("使用账密自动登录：%s", LOGIN_USERNAME)
        session = do_login(LOGIN_USERNAME, LOGIN_PASSWORD)
    elif AUTH_COOKIE:
        logger.info("使用手动 Cookie 认证")
        session = _make_session_with_cookie(AUTH_COOKIE)
    else:
        pytest.skip("未配置 LOGIN_USERNAME/PASSWORD 或 AUTH_COOKIE，跳过需要认证的用例")
        return  # 不会执行，让类型检查器满意

    yield session
    session.close()


@pytest.fixture(scope="session")
def http_session():
    """
    会话级：无认证的基础 requests.Session（用于测试公开接口或越权场景）。
    若需要认证请使用 login_session fixture。
    """
    session = requests.Session()
    if AUTH_TOKEN:
        session.headers.update({"Authorization": f"Bearer {AUTH_TOKEN}"})
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    yield session
    session.close()


# ──────────────────────────────────────────────
# pytest-html 报告增强
# 每条用例执行后将 HTTP 请求/响应详情写入 HTML 报告的 Extras 区域
# ──────────────────────────────────────────────

# 用于在用例执行期间收集 HTTP 调用记录
_http_calls: list = []


def record_http_call(method: str, url: str,
                     request_body,
                     status_code: int,
                     response_body: str) -> None:
    """在测试辅助函数中调用，将一次 HTTP 交互追加到当前用例的记录列表。"""
    _http_calls.append({
        "method":    method,
        "url":       url,
        "req_body":  request_body,
        "status":    status_code,
        "resp_body": response_body,
    })


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    用例执行完毕后：
      1. 将收集到的 HTTP 记录以格式化 HTML 写入报告 Extras
      2. 清空记录列表，准备下一条用例
    """
    outcome = yield
    report  = outcome.get_result()

    # 只在 call 阶段（实际执行，非 setup/teardown）处理
    if report.when != "call":
        return

    # 检查 pytest-html 插件是否可用
    try:
        from pytest_html import extras as html_extras  # type: ignore
    except ImportError:
        return

    extra = getattr(report, "extra", [])

    # ── 结果徽章 ──────────────────────────────────────
    badge_color = {"passed": "#28a745", "failed": "#dc3545", "skipped": "#6c757d"}.get(
        report.outcome, "#999"
    )
    badge_html = (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:4px;'
        f'background:{badge_color};color:#fff;font-weight:bold;font-size:13px;">'
        f'{report.outcome.upper()}</span>'
    )
    extra.append(html_extras.html(badge_html))

    # ── docstring（测试函数说明） ──────────────────────
    doc = item.function.__doc__
    if doc:
        doc_html = (
            f'<div style="margin:6px 0;padding:6px 10px;background:#f8f9fa;'
            f'border-left:3px solid #6c757d;color:#333;font-size:12px;">'
            f'<b>用例说明：</b>{doc.strip()}</div>'
        )
        extra.append(html_extras.html(doc_html))

    # ── HTTP 请求/响应详情 ────────────────────────────
    if _http_calls:
        rows = ""
        for i, call_info in enumerate(_http_calls, 1):
            # 尝试格式化 JSON 响应体
            try:
                resp_pretty = json.dumps(
                    json.loads(call_info["resp_body"]),
                    ensure_ascii=False, indent=2
                )[:2000]
            except Exception:
                resp_pretty = (call_info["resp_body"] or "")[:2000]

            # 请求体
            req_display = ""
            if call_info["req_body"]:
                try:
                    req_display = json.dumps(call_info["req_body"],
                                             ensure_ascii=False, indent=2)
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

    # ── 断言步骤明细 ──────────────────────────────────
    # 从测试模块动态读取 _assert_steps 列表
    test_module = getattr(item, "module", None)
    steps = list(getattr(test_module, "_assert_steps", []))
    if steps:
        rows = ""
        for i, s in enumerate(steps, 1):
            icon   = "✅" if s["passed"] else "❌"
            bg     = "#f0fff4" if s["passed"] else "#fff0f0"
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
        # 清空，准备下一条用例
        test_module._assert_steps.clear()

    # ── 失败时附加断言错误信息 ────────────────────────
    if report.outcome == "failed" and report.longrepr:
        err_text = str(report.longrepr)[-1500:]
        err_html = (
            f'<div style="margin-top:8px;">'
            f'<b style="color:#dc3545;">断言失败详情：</b>'
            f'<pre style="background:#fff0f0;padding:8px;font-size:11px;'
            f'border-left:3px solid #dc3545;overflow-x:auto;">{err_text}</pre></div>'
        )
        extra.append(html_extras.html(err_html))

    report.extra = extra
    _http_calls.clear()  # 清空，下一条用例重新收集
