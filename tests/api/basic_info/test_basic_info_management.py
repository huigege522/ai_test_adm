# -*- coding: utf-8 -*-
"""
基本信息管理 · 账户列表接口 — API 契约测试（Apple CMP）

================================================================================
接口路径：**POST** /api/org/list
摘要：账户列表 / 导出（PDF 6.1.1 + 6.1.4，`export=1` 异步导出：JSON code=0 + 离线下载中心提示）

Apifox 接口 ID：
  当前仓库内 `V3.24.0.0.0 基本信息管理-Apifox.openapi.yaml` 导出未包含 `x-apifox-id`；
  请以 Apifox 项目中「POST /api/org/list · 账户列表 / 导出」条目为准手动补齐 ID。

参考：
  - `apple_cmp_api/docs/requirements/基本信息管理/V3.24.0.0.0 基本信息管理-接口规约.md` · B3.1 org/list
  - `apple_cmp_api/docs/V3.24.0.0.0 基本信息管理-Apifox.openapi.yaml` · components/schemas/OrgListRequest

鉴权说明：
  - 路由中间件 `per:AppManagement`（与规约一致）
  - 本项目集成测试优先使用 **Cookie 会话**（`login_session`），并移除环境变量中的 Bearer，
    与被测 ADM 站点登录方式保持一致（参见 `tests/api/test_auto_custom_getlist.py`）。

运行：
  pytest tests/api/basic_info/test_basic_info_management.py -v
================================================================================
"""

from __future__ import annotations

import copy
import os
import pytest

from tests.helpers.basic_info_http import (
    assert_http_401_or_403,
    client_with_session_cookies,
    mute_env_bearer,
)
from tests.utils.api_client import ApiClient
from tests.conftest import do_login


PATH_ORG_LIST = "/api/org/list"

# OpenAPI OrgListRequest 未声明 required；Laravel `OrgManagementController::getList` 校验均为 nullable。
# 因此不存在「缺少契约必填项 → 400/422」场景；以下字段列表用于「逐项省略仍成功」回归。
ORG_LIST_BODY_KEYS = (
    "bloc_search",
    "company_search",
    "org_id",
    "org_name",
    "customer_type",
    "agent_2nd_label",
    "page",
    "limit",
    "export",
)

LONG_STR_201 = "x" * 201  # maxLength 200 + 1（bloc_search / company_search / org_name）
LONG_STR_33 = "x" * 33    # org_id max 32 + 1
LONG_STR_51 = "x" * 51    # agent_2nd_label max 50 + 1


def _baseline_json_payload() -> dict:
    """与 OpenAPI example 对齐（export=0 走 JSON 列表）。"""
    return {
        "bloc_search": "",
        "company_search": "",
        "org_id": "",
        "org_name": "",
        "customer_type": 1,
        "agent_2nd_label": "",
        "page": 1,
        "limit": 20,
        "export": 0,
    }


@pytest.fixture(scope="session")
def basic_client(login_session) -> ApiClient:
    return client_with_session_cookies(login_session)


@pytest.fixture(scope="session")
def anon_client() -> ApiClient:
    return mute_env_bearer(ApiClient())


@pytest.fixture(scope="session")
def low_perm_client():
    lu, lp = os.getenv("LOW_PERM_USERNAME", ""), os.getenv("LOW_PERM_PASSWORD", "")
    if not (lu and lp):
        pytest.skip("未配置 LOW_PERM_USERNAME / LOW_PERM_PASSWORD")
    sess = do_login(lu, lp, login_endpoint="sub")
    return client_with_session_cookies(sess)


class TestOrgList:
    """POST /api/org/list — 账户列表 / 导出"""

    @pytest.mark.smoke
    def test_正常获取账户列表_JSON分页(self, basic_client: ApiClient):
        resp = basic_client.post(PATH_ORG_LIST, json=_baseline_json_payload())
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        basic_client.assert_field_exists(resp, "data", "data.list", "data.total", "data.page", "data.limit")

        body = resp.json()
        items = body.get("data", {}).get("list") or []
        if items:
            # B3.1 `data.list[]` 关键字段（id / agent_type* 已废弃，接口不再返回）
            basic_client.assert_field_exists(
                resp,
                "data.list.0.org_id",
                "data.list.0.org_name",
                "data.list.0.company_name",
                "data.list.0.customer_type_id",
                "data.list.0.customer_type",
                "data.list.0.settle_type_id",
                "data.list.0.settle_type",
                "data.list.0.agent_2nd_label",
                "data.list.0.yy_users",
                "data.list.0.auth_users",
                "data.list.0.status_id",
                "data.list.0.status",
                "data.list.0.created_at",
            )

    @pytest.mark.smoke
    def test_最小请求体空JSON仍可分页查询(self, basic_client: ApiClient):
        """契约层请求体 optional：服务端应对 `{}` 使用默认分页。"""
        resp = basic_client.post(PATH_ORG_LIST, json={})
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        basic_client.assert_field_exists(resp, "data.list", "data.total", "data.page", "data.limit")

    @pytest.mark.regression
    @pytest.mark.parametrize(
        "omit_key",
        [pytest.param(k, id=k) for k in ORG_LIST_BODY_KEYS],
    )
    def test_逐项省略单个字段仍可成功(self, basic_client: ApiClient, omit_key: str):
        """
        说明：本接口 OpenAPI / Laravel 均无必填字段；此处验证「少传任一字段」不破坏默认行为。
        若后续契约增加 required，应将本组改为期望 400/422，并收窄 parametrized 列表为必填集合。
        """
        body = copy.deepcopy(_baseline_json_payload())
        body.pop(omit_key, None)
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)

    @pytest.mark.negative
    @pytest.mark.parametrize(
        ("field", "bad_value", "_reason", "expected_code"),
        [
            ("bloc_search", 12345, "字符串筛选字段传数字", -1),
            ("company_search", ["nested"], "字符串筛选字段传数组", -1),
            ("org_id", True, "字符串字段传布尔", 0),
            ("customer_type", "not_int", "整数字段传非数字字符串", -1),
            ("customer_type", {}, "整数字段传对象", -1),
            ("page", "NaN", "分页整数传非数字字符串", -1),
            ("limit", {}, "limit 传对象", -1),
            ("export", [], "export 传数组", -1),
            ("agent_2nd_label", 999, "字符串字段传数字", -1),
        ],
    )
    def test_参数类型错误HTTP200业务码校验(
        self,
        basic_client: ApiClient,
        field: str,
        bad_value,
        _reason: str,
        expected_code: int,
    ):
        """
        实测：类型/格式校验失败时 HTTP 仍为 200，业务码 code=-1 且 data 含 validation.*；
        非 HTTP 400/422。org_id 传布尔可被接受（code=0）。
        """
        body = copy.deepcopy(_baseline_json_payload())
        body[field] = bad_value
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", expected_code)
        if expected_code == -1:
            err = (resp.json().get("data") or {}).get(field)
            assert err, f"期望 data[{field!r}] 含校验错误，实际响应：{resp.text[:500]}"

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        ("field", "value", "_reason", "expected_code"),
        [
            ("bloc_search", LONG_STR_201, "模糊字段超长 +1", -1),
            ("company_search", LONG_STR_201, "客户名称模糊超长 +1", -1),
            ("org_name", LONG_STR_201, "系列组名称超长 +1", -1),
            ("org_id", LONG_STR_33, "org_id 超长 +1（实测未校验，空列表成功）", 0),
            ("agent_2nd_label", LONG_STR_51, "代理二代超长 +1", -1),
            ("page", 0, "page 最小值 -1（相对 min 1）", -1),
            ("page", -1, "page 负数边界", -1),
            ("limit", 0, "limit 最小值 -1", -1),
            ("limit", 501, "limit 最大值 +1（max 500）", -1),
            ("customer_type", 0, "customer_type 枚举下溢", -1),
            ("customer_type", 4, "customer_type 枚举上溢", -1),
            ("export", 2, "export 非法枚举值", -1),
            ("export", -1, "export 负数", -1),
        ],
    )
    def test_边界值非法HTTP200业务码校验(
        self,
        basic_client: ApiClient,
        field: str,
        value,
        _reason: str,
        expected_code: int,
    ):
        """
        实测：边界/枚举非法时 HTTP 200 + code=-1（与类型错误用例一致，非 400/422）。
        """
        body = copy.deepcopy(_baseline_json_payload())
        body[field] = value
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", expected_code)
        if expected_code == -1:
            err = (resp.json().get("data") or {}).get(field)
            assert err, f"期望 data[{field!r}] 含校验错误，实际响应：{resp.text[:500]}"

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("bloc_search", ""),
            ("company_search", ""),
            ("org_name", ""),
            ("org_id", ""),
            ("agent_2nd_label", ""),
        ],
    )
    def test_字符串字段允许空字符串(self, basic_client: ApiClient, field: str, value: str):
        body = copy.deepcopy(_baseline_json_payload())
        body[field] = value
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)

    @pytest.mark.smoke
    def test_导出开关为1时添加离线下载任务(self, basic_client: ApiClient):
        """
        实测 export=1 成功：HTTP 200 + application/json，code=0，message 提示离线下载中心，data=[]。
        10 分钟内重复导出：code=-1 防重文案。
        """
        body = copy.deepcopy(_baseline_json_payload())
        body["export"] = 1
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        payload = resp.json()
        code = payload.get("code")
        message = str(payload.get("message") or "")
        if code == 0:
            assert "导出" in message or "下载" in message, (
                f"成功导出应提示离线下载，实际 message={message!r}"
            )
            assert isinstance(payload.get("data"), list), (
                f"成功导出 data 应为列表，实际 {payload.get('data')!r}"
            )
            return
        if code == -1 and ("10" in message or "重复" in message):
            return
        pytest.fail(f"export=1 期望 code=0 任务已添加或 code=-1 防重，实际 body={payload!r}"[:800])

    @pytest.mark.negative
    def test_无认证访问返回401(self, anon_client: ApiClient):
        resp = anon_client.post(PATH_ORG_LIST, json=_baseline_json_payload())
        assert_http_401_or_403(resp, expect_403=False)

    @pytest.mark.negative
    def test_低权限访问返回403(self, low_perm_client: ApiClient):
        resp = low_perm_client.post(PATH_ORG_LIST, json=_baseline_json_payload())
        assert_http_401_or_403(resp, expect_403=True)

    @pytest.mark.smoke
    def test_TC005_P1_org_id筛选请求合法(self, basic_client: ApiClient):
        """TC005：携带广告系列组 ID（精确）筛选时接口成功返回分页结构。"""
        body = copy.deepcopy(_baseline_json_payload())
        body["org_id"] = "0"
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        basic_client.assert_field_exists(resp, "data.list", "data.total")

    @pytest.mark.regression
    def test_TC003_TC004_TC060_多筛选字段同时存在(self, basic_client: ApiClient):
        """TC003/TC004/TC060：所属集团 / 客户名称 / 广告系列组名称模糊筛选可同时传递。"""
        body = copy.deepcopy(_baseline_json_payload())
        body["bloc_search"] = "集团"
        body["company_search"] = "客户"
        body["org_name"] = "系列"
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)

    @pytest.mark.regression
    def test_TC006_列表项含客户类型与代理二代字段路径(self, basic_client: ApiClient):
        """TC006：在存在数据时校验 list[0] 含 customer_type / agent_2nd_label（名称因接口而异）。"""
        resp = basic_client.post(PATH_ORG_LIST, json=_baseline_json_payload())
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        items = (resp.json().get("data") or {}).get("list") or []
        if not items:
            pytest.skip("当前环境列表为空，跳过字段存在性断言")
        basic_client.assert_field_exists(
            resp,
            "data.list.0.customer_type_id",
            "data.list.0.customer_type",
            "data.list.0.agent_2nd_label",
        )


def _parse_list_time(row: dict) -> str:
    return str(
        row.get("created_at")
        or row.get("create_time")
        or row.get("org_ctime")
        or ""
    )


class TestOrgListP1Gap:
    """testpoints_基本信息管理.md · P1 且「未覆盖」· 账户列表"""

    @pytest.mark.regression
    def test_TC002_列表按创建时间倒序(self, basic_client: ApiClient):
        """
        TC002：默认列表按创建时间倒序（Service: orderByRaw COALESCE(oe.created_at,o.ctime) DESC）。
        请求：POST /api/org/list page=1 limit=20 export=0
        """
        resp = basic_client.post(PATH_ORG_LIST, json=_baseline_json_payload())
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        items = (resp.json().get("data") or {}).get("list") or []
        if len(items) < 2:
            pytest.skip("列表不足 2 条，无法比较排序")
        times = [_parse_list_time(x) for x in items[:10] if _parse_list_time(x)]
        if len(times) < 2:
            pytest.skip("列表项缺少 created_at/create_time 字段")
        assert times == sorted(times, reverse=True), times[:5]

    @pytest.mark.smoke
    def test_TC018_导出与列表同筛选条件可提交导出任务(self, basic_client: ApiClient):
        """
        TC018：导出内容与当前筛选一致（API 层：export=1 接受与列表相同 body，成功则进入离线下载）。
        请求：POST org/list export=1，携带 company_search 与列表一致。
        """
        body = copy.deepcopy(_baseline_json_payload())
        body["export"] = 1
        body["company_search"] = os.getenv("TC018_EXPORT_COMPANY_SEARCH", "")
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        payload = resp.json()
        code = payload.get("code")
        message = str(payload.get("message") or "")
        if code == 0:
            assert "导出" in message or "下载" in message, payload
            return
        if code == -1 and ("10" in message or "重复" in message):
            return
        pytest.fail(f"TC018 export=1 非预期：{payload!r}"[:600])

    @pytest.mark.regression
    def test_TC110_筛选无匹配时列表为空态(self, basic_client: ApiClient):
        """
        TC110：无数据时展示空状态（API：org_id 精确筛选不存在 ID → list 空、total=0）。
        请求：org_id=99999999991
        """
        body = copy.deepcopy(_baseline_json_payload())
        body["org_id"] = os.getenv("TC110_GHOST_ORG_ID", "99999999991")
        resp = basic_client.post(PATH_ORG_LIST, json=body)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert (data.get("list") or []) == [] or int(data.get("total") or 0) == 0
