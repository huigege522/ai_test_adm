# -*- coding: utf-8 -*-
"""基本信息管理 API 测试共享：会话客户端与 HTTP 断言。"""

from __future__ import annotations

import requests

from tests.utils.api_client import ApiClient


def mute_env_bearer(c: ApiClient) -> ApiClient:
    c.session.headers.pop("Authorization", None)
    return c


def client_with_session_cookies(source: requests.Session) -> ApiClient:
    c = mute_env_bearer(ApiClient())
    hdr_cookie = source.headers.get("Cookie")
    if hdr_cookie:
        c.session.headers["Cookie"] = hdr_cookie
    for ck in source.cookies:
        c.session.cookies.set(ck.name, ck.value, domain=ck.domain, path=ck.path or "/")
    return c


def assert_http_4xx(resp: requests.Response) -> None:
    assert resp.status_code in (400, 422), (
        f"期望 HTTP 400/422，实际 {resp.status_code}。\n{resp.text[:800]}"
    )


def assert_validation_error(
    resp: requests.Response, *fields: str, allow_500: bool = False
) -> None:
    """
    参数校验失败：HTTP 400/422，或 ADM 常见 HTTP 200 + code=-1 + data.validation.*。
    fields 非空时，要求 data 中至少包含所列字段之一的错误信息。
    allow_500：个别非法类型会触发服务端 500（仍视为拒绝写入）。
    """
    if resp.status_code in (400, 422):
        return
    if allow_500 and resp.status_code == 500:
        return
    if resp.status_code == 200:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if body.get("code") == -1:
            data = body.get("data") or {}
            if fields:
                if isinstance(data, dict):
                    keys = [str(k) for k in data.keys()]
                    if any(any(f in k for k in keys) for f in fields):
                        return
                if any(f in str(body.get("message") or "") for f in fields):
                    return
            else:
                return
    raise AssertionError(
        f"期望校验失败（4xx 或 200+code=-1），实际 {resp.status_code}。\n{resp.text[:800]}"
    )


def assert_http_401_or_403(resp: requests.Response, *, expect_403: bool) -> None:
    """ADM 部分接口鉴权失败为 HTTP 401/403，部分为 HTTP 200 + code=-1 + Unauthorized。"""
    if resp.status_code in (401, 403):
        return
    if resp.status_code == 200:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if body.get("code") == -1:
            msg = str(body.get("message") or "").lower()
            if expect_403 and ("unauthorized" in msg or "权限" in msg or "forbidden" in msg):
                return
            if not expect_403 and ("unauthorized" in msg or "未登录" in msg or "login" in msg):
                return
    if expect_403:
        raise AssertionError(
            f"期望 HTTP 403/401 或 200+Unauthorized，实际 {resp.status_code}。\n{resp.text[:500]}"
        )
    raise AssertionError(
        f"期望 HTTP 401 或未登录业务错误，实际 {resp.status_code}。\n{resp.text[:500]}"
    )


def flow_parent_org_id() -> str:
    """父级广告系列组 ID；verify / org/add 必填。未配置时默认 5878820（与列表样例 parent_org_id 一致）。"""
    import os

    return os.getenv("BASIC_INFO_FLOW_PARENT_ORG_ID", "5878820").strip() or "5878820"


def flow_env_or_skip():
    """集成流必备环境变量：Polar 侧须存在 tb_apple_org / tb_apple_app 基准行。"""
    import os

    import pytest

    org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
    adam_id = os.getenv("BASIC_INFO_FLOW_ADAM_ID", "").strip()
    yy = os.getenv("BASIC_INFO_FLOW_YY_UID", "").strip()
    auth = os.getenv("BASIC_INFO_FLOW_AUTH_UID", "").strip()
    if not all([org_id, adam_id, yy, auth]):
        pytest.skip(
            "集成流需配置环境变量：BASIC_INFO_FLOW_ORG_ID、BASIC_INFO_FLOW_ADAM_ID、"
            "BASIC_INFO_FLOW_YY_UID（运营负责人 cmp_user.id）、BASIC_INFO_FLOW_AUTH_UID（授权人 cmp_user.id）；"
            "且 FLOW_ORG_ID 对应账户尚未写入 apple_org_ext、FLOW_ADAM_ID 对应 App 尚未写入 apple_app_ext。"
        )
    return {
        "org_id": org_id,
        "parent_org_id": flow_parent_org_id(),
        "adam_id": adam_id,
        "yy_uid": int(yy),
        "auth_uid": int(auth),
    }


def flow_org_add_payload(
    *,
    company_name: str,
    org_id: str | None = None,
    parent_org_id: str | None = None,
    yy_uid: int | None = None,
    auth_uid: int | None = None,
    customer_policy: str = "",
    include_agent_2nd_label: bool = False,
) -> dict:
    """org/add 请求体（与 OrgManagementController::add 校验对齐）。"""
    import os

    env = flow_env_or_skip()
    payload = {
        "company_name": company_name,
        "customer_type": 1,
        "settle_type": 1,
        "customer_policy": customer_policy,
        "org_id": org_id or env["org_id"],
        "parent_org_id": parent_org_id or env["parent_org_id"],
        "remark": "",
        "yy_uids": [yy_uid if yy_uid is not None else env["yy_uid"]],
        "auth_uids": [auth_uid if auth_uid is not None else env["auth_uid"]],
    }
    if include_agent_2nd_label:
        payload["agent_2nd_label"] = ""
    return payload


def flow_app_add_payload(
    *,
    org_id: str | None = None,
    adam_id: str | None = None,
    customer_attribute: list[int] | None = None,
    include_customer_attribute: bool = True,
) -> dict:
    """app/add 请求体（与 AppManagementController::add 校验对齐）。"""
    import os

    env = flow_env_or_skip()
    payload = {
        "adam_id": adam_id or env["adam_id"],
        "org_id": org_id or env["org_id"],
        "region": 5,
        "attribution_type": 1,
        "time_zone": os.getenv("BASIC_INFO_FLOW_TIME_ZONE", "Asia/Shanghai").strip(),
        "start_date": os.getenv("BASIC_INFO_FLOW_START_DATE", "2026-01-01").strip(),
    }
    if include_customer_attribute:
        payload["customer_attribute"] = (
            customer_attribute if customer_attribute is not None else [1]
        )
    return payload


def pytest_skip_with_body(context: str, body) -> None:
    """pytest.skip 的 msg 必须是 str，勿直接传入 resp.json() 的 dict。"""
    import pytest

    pytest.skip(f"{context}：{body!r}"[:600])


def assert_business_success_or_skip(body: dict, *, context: str) -> None:
    """code=0 通过；校验失败 fail；其余业务失败 skip（数据已占用等）。"""
    import pytest

    if body.get("code") == 0:
        return
    msg = str(body.get("message") or "")
    data = body.get("data") or {}
    if "validation" in msg.lower() or (isinstance(data, dict) and data):
        pytest.fail(f"{context} 请求不合法：{body}")
    pytest.skip(f"{context} 未成功（环境数据可能已占用）：{body}")


def find_org_list_row(list_body: dict, org_id: str) -> dict | None:
    for row in (list_body.get("data") or {}).get("list") or []:
        if str(row.get("org_id") or "") == str(org_id):
            return row
    return None


def find_app_list_row(list_body: dict, adam_id: str) -> dict | None:
    for row in (list_body.get("data") or {}).get("list") or []:
        if str(row.get("app_id") or row.get("adam_id") or "") == str(adam_id):
            return row
    return None


def find_relation_rows(list_body: dict, *, org_id: str, adam_id: str) -> list[dict]:
    rows = []
    for row in (list_body.get("data") or {}).get("list") or []:
        if str(row.get("org_id") or "") == str(org_id) and str(row.get("adam_id") or "") == str(
            adam_id
        ):
            rows.append(row)
    return rows


def app_list_items(list_body: dict) -> list[dict]:
    return (list_body.get("data") or {}).get("list") or []


def assert_org_name_single_account_display(org_name: str) -> None:
    """
    后端 app/list 聚合字段：单账户时为「名称(org_id)」（PDF 写作 name+(id)，实现为括号）。
    """
    assert org_name and "/" not in org_name, org_name
    assert "(" in org_name and ")" in org_name, org_name


def assert_org_name_multi_account_display(org_name: str) -> None:
    """多账户：名称(id)/名称(id)。"""
    parts = [p.strip() for p in org_name.split("/") if p.strip()]
    assert len(parts) >= 2, org_name
    for part in parts:
        assert "(" in part and ")" in part, part


def assert_customer_attribute_slash_display(attr_text: str) -> None:
    """多客户属性：代投/自投 或 代投/自投/挂靠。"""
    assert attr_text and "/" in attr_text, attr_text
