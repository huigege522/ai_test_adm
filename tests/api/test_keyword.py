"""
接口：GET /api/keyword/getApp
描述：搜索 APP（关键词模块）
Apifox 路径引用：/paths/_api_keyword_getApp.json
认证方式：Cookie（通过 /api/login/sub2 自动登录获取）

请求体（application/json）：
  - country  string  必填  国家代码，如 "CN"
  - app      string  必填  搜索关键词，允许空字符串

响应体：
  {
    "code":    0,
    "message": "success",
    "data": [
      {
        "app_id":      3,            # integer
        "app_name":    "CF",         # string
        "icon":        "http://xxx", # string
        "is_expanded": "true"        # string，"true"/"false" 表示是否已拓词
      }
    ]
  }

注意：is_expanded 在接口文档定义为 string，示例中出现 boolean，
      测试中两种类型均可接受，以实际业务为准。
"""
import os
import pytest
import requests
from tests.utils.api_client import ApiClient

ENDPOINT = "/api/keyword/getApp"
BASE_URL  = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")


def _make_client_from_session(session: requests.Session) -> ApiClient:
    """将 conftest 登录后的 Session 注入 ApiClient，复用断言辅助方法。"""
    client = ApiClient()
    client.session = session
    return client


def get_app(session: requests.Session, country=None, app=None, **kwargs):
    """
    发送 GET /api/keyword/getApp 请求。
    Apifox 定义为 GET + requestBody，同时发送 query params + JSON Body，
    兼容服务端两种实现方式。
    """
    params = {}
    body   = {}
    if country is not None:
        params["country"] = country
        body["country"]   = country
    if app is not None:
        params["app"] = app
        body["app"]   = app
    url = f"{BASE_URL}{ENDPOINT}"
    return session.get(url, params=params, json=body if body else None,
                       timeout=int(os.getenv("REQUEST_TIMEOUT", 10)), **kwargs)


def assert_status(resp: requests.Response, expected: int):
    assert resp.status_code == expected, (
        f"期望状态码 {expected}，实际为 {resp.status_code}。\n响应体：{resp.text[:500]}"
    )


def assert_biz_ok(resp: requests.Response):
    body = resp.json()
    assert body.get("code") == 0, (
        f"业务码期望 0，实际 {body.get('code')}，message：{body.get('message')}"
    )


# ══════════════════════════════════════════════════════════════════════
# 正常场景
# ══════════════════════════════════════════════════════════════════════

class TestGetAppNormal:

    @pytest.mark.smoke
    def test_正常搜索APP_关键词精确匹配(self, login_session):
        """选择有效国家 + 关键词，返回匹配的 APP 列表。"""
        resp = get_app(login_session, country="CN", app="CF")
        assert_status(resp, 200)
        assert_biz_ok(resp)
        body = resp.json()
        assert "message" in body and "data" in body
        assert isinstance(body["data"], list), "data 字段应为数组"

    @pytest.mark.smoke
    def test_正常搜索APP_app为空字符串返回全量(self, login_session):
        """app 字段为空字符串时，期望返回该国家下全量 APP 列表（文档示例如此）。"""
        resp = get_app(login_session, country="CN", app="")
        assert_status(resp, 200)
        assert_biz_ok(resp)
        assert "data" in resp.json()

    @pytest.mark.smoke
    def test_正常搜索APP_响应data每条记录字段完整(self, login_session):
        """data 列表非空时，每条记录必须包含 app_id、app_name、icon、is_expanded。"""
        resp = get_app(login_session, country="CN", app="")
        assert_status(resp, 200)
        data = resp.json().get("data", [])
        if not data:
            pytest.skip("当前环境 data 为空，跳过字段完整性断言")
        for item in data:
            assert "app_id"      in item, f"记录缺少 app_id：{item}"
            assert "app_name"    in item, f"记录缺少 app_name：{item}"
            assert "icon"        in item, f"记录缺少 icon：{item}"
            assert "is_expanded" in item, f"记录缺少 is_expanded：{item}"
            assert isinstance(item["app_id"], int), \
                f"app_id 应为 integer，实际：{type(item['app_id'])}"

    @pytest.mark.regression
    def test_不同国家返回不同APP列表(self, login_session):
        """切换国家代码，两次请求均应成功。"""
        resp_cn = get_app(login_session, country="CN", app="")
        resp_us = get_app(login_session, country="US", app="")
        assert_status(resp_cn, 200)
        assert_status(resp_us, 200)
        assert resp_cn.json()["code"] == 0
        assert resp_us.json()["code"] == 0


# ══════════════════════════════════════════════════════════════════════
# 参数缺失场景
# ══════════════════════════════════════════════════════════════════════

class TestGetAppMissingParams:

    @pytest.mark.negative
    def test_缺少必填参数_country(self, login_session):
        """请求体缺少 country 字段，期望 400/422 或业务错误码非 0。"""
        resp = get_app(login_session, app="CF")
        is_http_error = resp.status_code in (400, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"缺少 country 期望校验失败，实际 {resp.status_code}，响应：{resp.text[:200]}"
        )

    @pytest.mark.negative
    def test_缺少必填参数_app(self, login_session):
        """请求体缺少 app 字段，期望 400/422 或业务错误码非 0。"""
        resp = get_app(login_session, country="CN")
        is_http_error = resp.status_code in (400, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"缺少 app 期望校验失败，实际 {resp.status_code}，响应：{resp.text[:200]}"
        )

    @pytest.mark.negative
    def test_请求体完全为空(self, login_session):
        """不传任何参数，期望 400/422 或业务错误码非 0。"""
        resp = get_app(login_session)
        is_http_error = resp.status_code in (400, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"空参数期望校验失败，实际 {resp.status_code}，响应：{resp.text[:200]}"
        )


# ══════════════════════════════════════════════════════════════════════
# 参数类型错误
# ══════════════════════════════════════════════════════════════════════

class TestGetAppTypeError:

    @pytest.mark.negative
    @pytest.mark.parametrize("country,app,desc", [
        (123,  "CF",  "country 传 integer"),
        (True, "CF",  "country 传 boolean"),
        (None, "CF",  "country 传 null"),
        ("CN", 123,   "app 传 integer"),
        ("CN", True,  "app 传 boolean"),
        ("CN", None,  "app 传 null"),
    ])
    def test_参数类型错误(self, login_session, country, app, desc):
        """字段类型与定义不符时，期望 400/422 或业务错误码非 0。"""
        resp = get_app(login_session, country=country, app=app)
        is_http_error = resp.status_code in (400, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"场景【{desc}】期望 400/422 或业务错误，"
            f"实际 HTTP {resp.status_code}，响应：{resp.text[:200]}"
        )


# ══════════════════════════════════════════════════════════════════════
# 边界值场景
# ══════════════════════════════════════════════════════════════════════

class TestGetAppBoundary:

    @pytest.mark.boundary
    @pytest.mark.parametrize("country,app,desc", [
        ("C",       "CF",        "country 最短 1 字符"),
        ("CN",      "CF",        "country 标准 2 字符"),
        ("CHN",     "CF",        "country 3 字符"),
        ("A" * 255, "CF",        "country 255 字符（假设上限）"),
        ("A" * 256, "CF",        "country 256 字符（超出上限）"),
        ("CN",      "",          "app 空字符串（合法，文档示例）"),
        ("CN",      "A" * 100,   "app 100 字符"),
        ("CN",      "A" * 255,   "app 255 字符"),
        ("CN",      "A" * 256,   "app 256 字符（可能超限）"),
        ("CN",      "测试APP",   "app 中文搜索"),
        ("CN",      "App !@#$%", "app 含特殊字符"),
        ("CN",      " CF ",      "app 前后有空格"),
        ("CN",      "   ",       "app 纯空格"),
    ])
    def test_边界值_字段长度与特殊值(self, login_session, country, app, desc):
        """
        边界值测试：
        - 正常范围内期望 200 且不报 5xx
        - 超长字符串（256 字符）期望 400/422 或业务错误码非 0
        - 特殊字符至少不应返回 5xx
        """
        resp = get_app(login_session, country=country, app=app)
        assert resp.status_code != 500, (
            f"场景【{desc}】服务器不应返回 500，"
            f"实际：{resp.status_code}，响应：{resp.text[:200]}"
        )
        if len(str(country)) > 255 or len(str(app)) > 255:
            is_http_error = resp.status_code in (400, 422)
            is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
            assert is_http_error or is_biz_error, (
                f"场景【{desc}】超长参数期望校验失败，实际 {resp.status_code}"
            )


# ══════════════════════════════════════════════════════════════════════
# 越权场景
# ══════════════════════════════════════════════════════════════════════

class TestGetAppAuth:

    @pytest.mark.negative
    def test_无认证访问(self):
        """不携带任何 Cookie，期望返回 401/403 或重定向到登录页（HTML 响应）。"""
        anon = requests.Session()
        anon.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        resp = get_app(anon, country="CN", app="CF")
        is_auth_fail = resp.status_code in (401, 403)
        is_redirect  = "html" in resp.headers.get("Content-Type", "").lower()
        assert is_auth_fail or is_redirect, (
            f"无认证访问期望 401/403 或 HTML 重定向，"
            f"实际 {resp.status_code}，Content-Type: {resp.headers.get('Content-Type', '')}"
        )

    @pytest.mark.negative
    def test_无效Cookie访问(self):
        """携带伪造 Cookie，期望返回 401/403 或重定向登录页。"""
        fake = requests.Session()
        fake.headers.update({
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "Cookie":       "invalid_session=fake_value_12345",
        })
        resp = get_app(fake, country="CN", app="CF")
        is_auth_fail = resp.status_code in (401, 403)
        is_redirect  = "html" in resp.headers.get("Content-Type", "").lower()
        assert is_auth_fail or is_redirect, (
            f"无效 Cookie 期望 401/403 或重定向，实际 {resp.status_code}"
        )

    @pytest.mark.negative
    def test_低权限用户访问(self):
        """
        低权限用户（无竞品分析权限）访问，期望 403 或业务错误码非 0。
        需在 .env 中配置 LOW_PERM_USERNAME + LOW_PERM_PASSWORD，否则跳过。
        """
        from tests.conftest import do_login
        low_user = os.getenv("LOW_PERM_USERNAME", "")
        low_pass = os.getenv("LOW_PERM_PASSWORD", "")
        if not low_user or not low_pass:
            pytest.skip("未配置 LOW_PERM_USERNAME/PASSWORD，跳过低权限测试")
        low_session = do_login(low_user, low_pass)
        resp = get_app(low_session, country="CN", app="CF")
        is_forbidden     = resp.status_code == 403
        is_biz_forbidden = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_forbidden or is_biz_forbidden, (
            f"低权限用户期望 403 或业务错误，实际 {resp.status_code}"
        )
