"""
全局 pytest fixture：
  - db_conn      : MySQL 连接，function 级别，自动提交 + 自动回滚清理
  - db_cursor    : 基于 db_conn 的游标
  - http_session : requests.Session，携带 BASE_URL 与认证头
  - login_session: requests.Session，通过 /api/login/sub2 自动登录后的已认证 Session
  - load_baseline: 执行 test_data/baseline.sql 插入基准数据

登录优先级：
  1. 若 LOGIN_USERNAME + LOGIN_PASSWORD 已配置 → 调用 /api/login/sub2 自动登录
  2. 若仅配置了 AUTH_COOKIE → 直接注入 Cookie 请求头
  3. 两者均未配置 → 抛出 pytest.skip，跳过需要认证的用例
"""
import os
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
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "db": os.getenv("DB_NAME", "test_db"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": "utf8mb4",
    "autocommit": False,
    "cursorclass": pymysql.cursors.DictCursor,
}

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
