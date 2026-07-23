# -*- coding: utf-8 -*-
"""
自动化报表 · 任务列表 GET /api/autoCustom/getList

ADM 响应约定（实测）：
  - 成功: HTTP 200 + code=0
  - 参数校验失败: HTTP 200 + code=-1（NOT 400/422）
  - 无认证: HTTP 401 + code=-1 msg=Unauthenticated
"""

import os
import pytest
import requests
from dotenv import load_dotenv
from tests.utils.api_client import ApiClient
from tests.helpers.basic_info_http import client_with_session_cookies, assert_http_401_or_403
from tests.conftest import do_login

load_dotenv()

PATH = "/api/autoCustom/getList"
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

REQUIRED_FIELDS = [
    "id", "job_name", "mail_subject", "status", "week_days",
    "rise_time", "open_type", "lang", "last_rise_date", "last_status",
    "created_at", "updated_at", "user_id", "is_send_excel", "user_name",
]
STRING_FIELDS = ["job_name", "mail_subject", "rise_time", "open_type", "lang", "user_name"]
INT_FIELDS = ["id", "status", "user_id", "is_send_excel", "last_status"]


@pytest.fixture(scope="session")
def auth_client(login_session) -> ApiClient:
    return client_with_session_cookies(login_session)


# ────────────────────────────────────────────────
# 正常场景
# ────────────────────────────────────────────────

class TestGetListNormal:
    """正常场景 — 分页、字段结构、数据一致性。"""

    @pytest.mark.smoke
    def test_默认分页(self, auth_client):
        """无参数时默认返回第1页、每页10条。"""
        resp = auth_client.get(PATH)
        auth_client.assert_status(resp, 200)
        auth_client.assert_business_code(resp, "code", 0)
        auth_client.assert_field_exists(resp, "data", "data.list", "data.total")
        auth_client.assert_json_field(resp, "data.current", lambda v: v == 1)
        auth_client.assert_json_field(resp, "data.size", lambda v: v == 10)

    @pytest.mark.smoke
    def test_自定义分页(self, auth_client):
        """指定 page=2, limit=5。"""
        resp = auth_client.get(PATH, params={"page": 2, "limit": 5})
        auth_client.assert_business_code(resp, "code", 0)
        auth_client.assert_json_field(resp, "data.current", lambda v: v == 2)
        auth_client.assert_json_field(resp, "data.size", lambda v: v == 5)
        auth_client.assert_json_field(resp, "data.list", lambda v: len(v) <= 5)

    @pytest.mark.smoke
    def test_列表项字段完整(self, auth_client):
        """每条记录包含所有必需字段，且类型正确。"""
        resp = auth_client.get(PATH, params={"limit": 3})
        auth_client.assert_business_code(resp, "code", 0)
        items = resp.json()["data"]["list"]
        assert len(items) > 0, "列表不应为空"
        item = items[0]
        for f in REQUIRED_FIELDS:
            assert f in item, f"字段 [{f}] 缺失"
        for f in INT_FIELDS:
            assert isinstance(item[f], int), f"字段 [{f}] 应为 int，实际 {type(item[f])}"
        for f in STRING_FIELDS:
            assert isinstance(item[f], str), f"字段 [{f}] 应为 str，实际 {type(item[f])}"

    @pytest.mark.smoke
    def test_total一致性(self, auth_client):
        """不同 limit 下 total 应一致。"""
        t1 = auth_client.get(PATH, params={"page": 1, "limit": 5}).json()["data"]["total"]
        t2 = auth_client.get(PATH, params={"page": 1, "limit": 10}).json()["data"]["total"]
        assert t1 == t2, f"total 不一致: {t1} vs {t2}"

    @pytest.mark.smoke
    def test_status有效值(self, auth_client):
        """status 应为 1 或 2。"""
        resp = auth_client.get(PATH, params={"limit": 20})
        items = resp.json()["data"]["list"]
        if items:
            for item in items:
                assert item["status"] in (1, 2), f"status={item['status']}，id={item['id']}"

    @pytest.mark.smoke
    def test_week_days有效数组(self, auth_client):
        """week_days 应是 1-7 组成的数组。"""
        resp = auth_client.get(PATH, params={"limit": 20})
        items = resp.json()["data"]["list"]
        if items:
            for item in items:
                wd = item.get("week_days", [])
                assert isinstance(wd, list), f"week_days 应为数组"
                for d in wd:
                    assert d in [str(v) for v in range(1, 8)], f"week_days 非法值: {d}"


# ────────────────────────────────────────────────
# 参数边界值 + 类型错误
# ────────────────────────────────────────────────

class TestGetListValidation:
    """负向 — 边界值、类型错误。"""

    @pytest.mark.boundary
    @pytest.mark.parametrize("page,limit", [
        (1, 1),
        (1, 100),
    ])
    def test_分页边界值正常(self, auth_client, page, limit):
        resp = auth_client.get(PATH, params={"page": page, "limit": limit})
        auth_client.assert_business_code(resp, "code", 0)

    @pytest.mark.negative
    @pytest.mark.parametrize("page,limit,desc", [
        (0, 10, "page=0"),
        (1, 0, "limit=0"),
        (-1, 10, "page=-1"),
        (1, 9999, "limit=9999"),
    ])
    def test_分页边界值非法(self, auth_client, page, limit, desc):
        resp = auth_client.get(PATH, params={"page": page, "limit": limit})
        body = resp.json()
        assert body["code"] == -1, f"[{desc}] 期望 code=-1，实际 {body.get('code')}"
        assert "validation" in body.get("message", "").lower(), \
            f"[{desc}] 期望 validation 错误，实际 message={body.get('message')}"

    @pytest.mark.negative
    @pytest.mark.parametrize("page,limit,desc", [
        ("abc", 10, "page=abc"),
        (1, "abc", "limit=abc"),
    ])
    def test_参数类型错误(self, auth_client, page, limit, desc):
        """page/limit 为非数字时应返回 validation 错误。"""
        resp = auth_client.get(PATH, params={"page": page, "limit": limit})
        body = resp.json()
        assert body["code"] == -1, f"[{desc}] 期望 code=-1，实际 {body.get('code')}"
        assert "validation" in body.get("message", "").lower(), \
            f"[{desc}] 期望 validation 错误"

    def test_page空字符串被忽略使用默认值(self, auth_client):
        """page='' 时后端容错，视作未传，返回 code=0 且 current=1。"""
        resp = auth_client.get(PATH, params={"page": "", "limit": 10})
        auth_client.assert_business_code(resp, "code", 0)
        auth_client.assert_json_field(resp, "data.current", lambda v: v == 1)

    @pytest.mark.xfail(reason="已知后台 Bug: limit='' 导致 PHP 类型转换异常，返回 HTTP 500 而非参数校验错误")
    def test_limit空字符串应返回参数错误(self, auth_client):
        """limit='' 期望返回 HTTP 200 + code=-1 的 validation 错误，但实际后台 PHP 报 500。"""
        resp = auth_client.get(PATH, params={"page": 1, "limit": ""})
        body = resp.json()
        assert body["code"] == -1, f"期望 code=-1，实际 {body.get('code')}"
        assert "validation" in body.get("message", "").lower()

    @pytest.mark.boundary
    def test_超大页码返回空列表(self, auth_client):
        """page=99999 返回空列表。"""
        resp = auth_client.get(PATH, params={"page": 99999, "limit": 10})
        if resp.json()["code"] == 0:
            assert resp.json()["data"]["list"] == []


# ────────────────────────────────────────────────
# 越权场景
# ────────────────────────────────────────────────

class TestGetListAuth:
    """越权 — 无认证、低权限。"""

    @pytest.mark.negative
    def test_无认证访问(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        resp = s.get(BASE_URL + PATH, timeout=10)
        assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}"
        body = resp.json()
        assert body["code"] == -1
        assert "Unauthenticated" in body.get("message", "")

    @pytest.mark.negative
    def test_低权限用户只能看到自己的记录(self):
        low_user = os.getenv("LOW_PERM_USERNAME", "")
        low_pass = os.getenv("LOW_PERM_PASSWORD", "")
        if not low_user or not low_pass:
            pytest.skip("未配置 LOW_PERM_USERNAME/LOW_PERM_PASSWORD")
        try:
            sess = do_login(low_user, low_pass)
        except RuntimeError:
            pytest.skip("低权限账号登录失败，跳过")
        resp = sess.get(BASE_URL + PATH, timeout=10)
        body = resp.json()
        if body.get("code") == 0:
            for item in body["data"]["list"]:
                assert item.get("user_name", "") == low_user, \
                    f"低权限用户看到了他人记录: {item.get('user_name')}"
