"""Auth & HTTP session fixtures + Playwright E2E fixtures。"""
import os
import sys
import logging
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [BASE_DIR, TESTS_DIR]:
    if p not in sys.path:
        sys.path.append(p)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
AUTH_COOKIE = os.getenv("AUTH_COOKIE", "")
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "")
LOGIN_URL = f"{BASE_URL}/api/login/sub2"
LOGIN_URL_SUB = f"{BASE_URL}/api/login/sub"


def do_login(username: str, password: str, *, login_endpoint: str = "sub2") -> requests.Session:
    """账密登录。login_endpoint='sub' 与前端登录页一致。"""
    login_url = LOGIN_URL_SUB if login_endpoint == "sub" else LOGIN_URL
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    payload = {"username": username, "password": password, "captcha": {"ticket": "1234", "randstr": "1234"}}

    try:
        resp = session.post(login_url, json=payload, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"登录请求异常：{e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"登录失败，HTTP {resp.status_code}，响应：{resp.text[:300]}")

    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(f"登录业务错误，code={body.get('code')}，message={body.get('message')}")

    logger.info("登录成功，用户：%s", body.get("data", {}).get("username"))
    return session


def _make_session_with_cookie(cookie: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json", "Cookie": cookie})
    return session


@pytest.fixture(scope="session")
def login_session() -> requests.Session:
    if LOGIN_USERNAME and LOGIN_PASSWORD:
        logger.info("使用账密自动登录：%s", LOGIN_USERNAME)
        session = do_login(LOGIN_USERNAME, LOGIN_PASSWORD)
    elif AUTH_COOKIE:
        logger.info("使用手动 Cookie 认证")
        session = _make_session_with_cookie(AUTH_COOKIE)
    else:
        pytest.skip("未配置 LOGIN_USERNAME/PASSWORD 或 AUTH_COOKIE，跳过需要认证的用例")
        return

    yield session
    session.close()


@pytest.fixture(scope="session")
def http_session():
    session = requests.Session()
    if AUTH_TOKEN:
        session.headers.update({"Authorization": f"Bearer {AUTH_TOKEN}"})
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    yield session
    session.close()


# ── Playwright E2E ──────────────────────────────

@pytest.fixture(scope="session")
def playwright_browser(playwright):
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def playwright_page(playwright_browser, login_session):
    context = playwright_browser.new_context()
    for cookie in login_session.cookies:
        context.add_cookies([{"name": cookie.name, "value": cookie.value, "domain": cookie.domain, "path": cookie.path}])
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def competitor_explore_page(playwright_page):
    from pages.competitor_explore_page import CompetitorExplorePage
    page = CompetitorExplorePage(playwright_page)
    page.navigate_to_explore(BASE_URL)
    return page
