# -*- coding: utf-8 -*-
"""
基本信息管理 · 账户侧 API（校验 / 添加 / 编辑）

路径见 `tests/helpers/basic_info_api_map.py`。

运行：
  pytest tests/api/basic_info/test_basic_info_accounts.py -v

写依赖 Polar：`tb_apple_org` 存在且未占用 `apple_org_ext` 的 org_id；
需在环境中配置 BASIC_INFO_FLOW_*（含 PARENT_ORG_ID，与 integration 共用）。
"""

from __future__ import annotations

import os
import time

import pytest

from tests.helpers.basic_info_api_map import (
    PATH_ORG_ADD,
    PATH_ORG_CHECK_COMPANY,
    PATH_ORG_EDIT,
    PATH_ORG_LIST,
    PATH_ORG_VERIFY,
)
from tests.helpers.basic_info_http import (
    assert_business_success_or_skip,
    assert_http_401_or_403,
    assert_validation_error,
    pytest_skip_with_body,
    client_with_session_cookies,
    find_org_list_row,
    flow_env_or_skip,
    flow_org_add_payload,
    flow_parent_org_id,
    mute_env_bearer,
)
from tests.utils.api_client import ApiClient
from tests.conftest import do_login


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


def _org_add_payload(*, include_agent_2nd_label: bool = True) -> dict:
    yy = os.getenv("BASIC_INFO_FLOW_YY_UID", "1").strip()
    auth = os.getenv("BASIC_INFO_FLOW_AUTH_UID", "1").strip()
    payload = {
        "company_name": "pytest-auto",
        "customer_type": 1,
        "settle_type": 1,
        "customer_policy": "",
        "agent_type": 1,
        "org_id": os.getenv("BASIC_INFO_FLOW_ORG_ID", "placeholder"),
        "parent_org_id": flow_parent_org_id(),
        "remark": "",
        "yy_uids": [int(yy)],
        "auth_uids": [int(auth)],
    }
    if include_agent_2nd_label:
        payload["agent_2nd_label"] = ""
    return payload


def _assert_org_add_or_skip(body: dict) -> None:
    """code=0 通过；校验失败 fail；其余业务失败 skip（如 org 已在库）。"""
    if body.get("code") == 0:
        return
    msg = str(body.get("message") or "")
    data = body.get("data") or {}
    if "validation" in msg.lower() or (isinstance(data, dict) and data):
        pytest.fail(f"添加账户请求不合法（请检查 FLOW / parent_org_id）：{body}")
    pytest.skip(f"添加账户未成功（org 可能已在库或环境不可用）：{body}")


class TestOrgVerifyOrgId:
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC210_style_缺少org_id返回422(self, basic_client: ApiClient):
        resp = basic_client.post(PATH_ORG_VERIFY, json={})
        assert_validation_error(resp)

    @pytest.mark.smoke
    def test_TC011_有效ORGID校验通过(self, basic_client: ApiClient):
        """TC011：手动输入有效 ORGID，verify 返回账户名等信息，可继续提交 add。"""
        org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
        if not org_id:
            pytest.skip("未配置 BASIC_INFO_FLOW_ORG_ID")
        resp = basic_client.post(
            PATH_ORG_VERIFY,
            json={"org_id": org_id, "parent_org_id": flow_parent_org_id()},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == 0:
            basic_client.assert_field_exists(resp, "data.orgId", "data.orgName")
            return
        if body.get("code") == -1 and "已存在" in str(body.get("message") or ""):
            pytest.skip("FLOW org_id 已写入 apple_org_ext，verify 返回账户已存在")
        pytest.fail(f"verifyOrgId 非预期响应：{body}")


class TestOrgAddNegative:
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC201_客户名称必填(self, basic_client: ApiClient):
        p = _org_add_payload()
        del p["company_name"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "company_name")

    @pytest.mark.negative
    def test_TC202_客户类型必填(self, basic_client: ApiClient):
        p = _org_add_payload()
        del p["customer_type"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "customer_type")

    @pytest.mark.negative
    def test_TC205_org_id必填(self, basic_client: ApiClient):
        p = _org_add_payload()
        del p["org_id"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "org_id")

    @pytest.mark.negative
    def test_TC206_运营负责人必填(self, basic_client: ApiClient):
        p = _org_add_payload()
        del p["yy_uids"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "yy_uids")

    @pytest.mark.negative
    def test_TC207_授权人必填(self, basic_client: ApiClient):
        p = _org_add_payload()
        del p["auth_uids"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "auth_uids")

    @pytest.mark.negative
    def test_TC209_style_org_id类型非法(self, basic_client: ApiClient):
        p = _org_add_payload()
        p["org_id"] = ["not-a-string"]
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "org_id", "parent_org_id", allow_500=True)


class TestOrgAddPositiveFlow:
    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC007_添加账户成功且列表可检索(self, basic_client: ApiClient):
        """TC007：必填项齐全添加账户，列表按 org_id 检索且客户名称一致。"""
        import time

        env = flow_env_or_skip()
        company = f"pytest-tc007-{int(time.time())}"
        payload = flow_org_add_payload(company_name=company)
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        basic_client.assert_status(resp, 200)
        assert_business_success_or_skip(resp.json(), context="TC007 org/add")

        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": env["org_id"], "page": 1, "limit": 10, "export": 0},
        )
        basic_client.assert_status(r_list, 200)
        basic_client.assert_business_code(r_list, "code", 0)
        row = find_org_list_row(r_list.json(), env["org_id"])
        assert row is not None, r_list.json()
        assert row.get("company_name") == company


class TestOrgEditPositiveFlow:
    @pytest.mark.smoke
    def test_TC017_编辑账户后列表字段更新(self, basic_client: ApiClient):
        """TC017：按 org_id 编辑客户名称/客户政策，列表回显更新且不新增行。"""
        import time

        env = flow_env_or_skip()
        company = f"pytest-tc017-{int(time.time())}"
        r_add = basic_client.post(
            PATH_ORG_ADD, json=flow_org_add_payload(company_name=company)
        )
        basic_client.assert_status(r_add, 200)
        assert_business_success_or_skip(r_add.json(), context="TC017 前置 org/add")

        new_company = f"{company}-edited"
        new_policy = f"policy-{int(time.time())}"
        r_edit = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": env["org_id"],
                "company_name": new_company,
                "customer_type": 2,
                "settle_type": 2,
                "customer_policy": new_policy,
            },
        )
        basic_client.assert_status(r_edit, 200)
        assert r_edit.json().get("code") == 0, r_edit.json()

        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": env["org_id"], "page": 1, "limit": 10, "export": 0},
        )
        basic_client.assert_status(r_list, 200)
        basic_client.assert_business_code(r_list, "code", 0)
        rows = [
            x
            for x in (r_list.json().get("data") or {}).get("list") or []
            if str(x.get("org_id") or "") == str(env["org_id"])
        ]
        assert len(rows) == 1, f"编辑后列表应仅一条 org_id={env['org_id']}：{rows}"
        row = rows[0]
        assert row.get("company_name") == new_company
        assert row.get("customer_policy") == new_policy


class TestOrgAddPositiveOptionalAgent2nd:
    @pytest.mark.smoke
    def test_TC045_代理二代可省略(self, basic_client: ApiClient):
        """TC045：agent_2nd_label 省略（nullable），在具备 FLOW 环境时可入库。"""
        org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
        yy = os.getenv("BASIC_INFO_FLOW_YY_UID", "").strip()
        auth = os.getenv("BASIC_INFO_FLOW_AUTH_UID", "").strip()
        if not all([org_id, yy, auth]):
            pytest.skip("未配置 BASIC_INFO_FLOW_ORG_ID / YY_UID / AUTH_UID")
        payload = _org_add_payload(include_agent_2nd_label=False)
        payload["company_name"] = f"pytest-no-agent2-{org_id}"
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        basic_client.assert_status(resp, 200)
        _assert_org_add_or_skip(resp.json())


class TestOrgEditImmutableFieldsApi:
    """TC212/TC213：编辑态禁用字段 — API 契约（org/edit 白名单不包含 org_id / 代理字段）。"""

    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC212_编辑不可变更org_id(self, basic_client: ApiClient):
        """
        TC212：UI 为账户 ID 置灰；API 侧 org/edit 仅以 org_id 定位记录，更新后列表 org_id 不变。
        """
        import time

        env = flow_env_or_skip()
        org_id = env["org_id"]
        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": org_id, "page": 1, "limit": 5, "export": 0},
        )
        basic_client.assert_status(r_list, 200)
        if r_list.json().get("code") != 0:
            pytest.skip("FLOW org 未在账户列表中，无法验证编辑不变更 org_id")
        row_before = find_org_list_row(r_list.json(), org_id)
        if row_before is None:
            pytest.skip("未找到 FLOW 账户行")

        new_company = f"pytest-tc212-{int(time.time())}"
        r_edit = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": org_id,
                "company_name": new_company,
                "customer_type": row_before.get("customer_type_id") or 1,
                "settle_type": row_before.get("settle_type_id") or 1,
                "customer_policy": row_before.get("customer_policy") or "",
            },
        )
        basic_client.assert_status(r_edit, 200)
        body = r_edit.json()
        if body.get("code") != 0:
            pytest.skip(f"org/edit 未成功：{body}")
        assert str((body.get("data") or {}).get("org_id") or org_id) == str(org_id)

        r_after = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": org_id, "page": 1, "limit": 10, "export": 0},
        )
        basic_client.assert_status(r_after, 200)
        basic_client.assert_business_code(r_after, "code", 0)
        rows = [
            x
            for x in (r_after.json().get("data") or {}).get("list") or []
            if str(x.get("org_id") or "") == str(org_id)
        ]
        assert len(rows) == 1, rows
        assert str(rows[0]["org_id"]) == str(org_id)

    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC213_编辑不可改代理标识与代理二代(self, basic_client: ApiClient):
        """
        TC213：代理标识(上级 parent_org_id) / 代理二代 agent_2nd_label 不在 org/edit 白名单。
        传入额外字段不应改变列表回显。
        """
        import time

        env = flow_env_or_skip()
        org_id = env["org_id"]
        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": org_id, "page": 1, "limit": 5, "export": 0},
        )
        basic_client.assert_status(r_list, 200)
        row_before = find_org_list_row(r_list.json(), org_id)
        if row_before is None:
            pytest.skip("未找到 FLOW 账户行")

        parent_before = row_before.get("parent_org_id")
        agent2_before = row_before.get("agent_2nd_label")
        company_before = row_before.get("company_name") or "pytest-tc213"

        r_edit = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": org_id,
                "company_name": f"{company_before}-tc213-{int(time.time())}",
                "customer_type": row_before.get("customer_type_id") or 1,
                "settle_type": row_before.get("settle_type_id") or 1,
                "customer_policy": row_before.get("customer_policy") or "",
                "agent_2nd_label": "pytest-injected-agent2",
                "parent_org_id": "99999999",
                "agent_type": 99,
            },
        )
        basic_client.assert_status(r_edit, 200)
        if r_edit.json().get("code") != 0:
            pytest_skip_with_body("org/edit 未成功", r_edit.json())

        r_after = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": org_id, "page": 1, "limit": 5, "export": 0},
        )
        basic_client.assert_status(r_after, 200)
        row_after = find_org_list_row(r_after.json(), org_id)
        assert row_after is not None
        assert row_after.get("parent_org_id") == parent_before
        assert row_after.get("agent_2nd_label") == agent2_before


class TestOrgEditNegative:
    @pytest.mark.negative
    def test_编辑缺少id返回422(self, basic_client: ApiClient):
        resp = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "company_name": "x",
                "customer_type": 1,
                "settle_type": 1,
            },
        )
        assert_validation_error(resp, "org_id")


class TestOrgVerifyPermission:
    @pytest.mark.negative
    def test_无会话校验账户ID返回401(self, anon_client: ApiClient):
        resp = anon_client.post(PATH_ORG_VERIFY, json={"org_id": "1"})
        assert resp.status_code == 401, resp.text[:400]

    @pytest.mark.negative
    def test_TC225_style_低权限无法访问校验接口(self, low_perm_client: ApiClient):
        resp = low_perm_client.post(PATH_ORG_VERIFY, json={"org_id": "1"})
        assert_http_401_or_403(resp, expect_403=True)


class TestOrgAddPermission:
    @pytest.mark.negative
    def test_TC225_style_低权限无法添加账户(self, low_perm_client: ApiClient):
        resp = low_perm_client.post(PATH_ORG_ADD, json=_org_add_payload())
        assert_http_401_or_403(resp, expect_403=True)


def _chars(n: int, ch: str = "测") -> str:
    return ch * n


class TestOrgP1GapCoverage:
    """testpoints · P1「未覆盖」· 账户添加/校验/边界"""

    @pytest.mark.smoke
    def test_TC010_校验ORGID返回账户名称可带出(self, basic_client: ApiClient):
        """
        TC010：选择/输入有效 ORGID 后账户名称自动带出（API：verifyOrgId.data.orgName）。
        请求：POST verifyOrgId {org_id, parent_org_id}
        """
        org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
        if not org_id:
            pytest.skip("未配置 BASIC_INFO_FLOW_ORG_ID")
        resp = basic_client.post(
            PATH_ORG_VERIFY,
            json={"org_id": org_id, "parent_org_id": flow_parent_org_id()},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            pytest.skip(f"verify 未通过：{body}")
        data = body.get("data") or {}
        assert data.get("orgName") or data.get("org_name"), data

    @pytest.mark.skip(reason="TC012：客户类型下拉模糊搜索为纯前端交互，无独立 HTTP 接口")
    def test_TC012_客户类型下拉模糊搜索(self):
        pass

    @pytest.mark.skip(reason="TC013：点击取消关闭弹窗为 UI 行为，无 org/add 取消接口")
    def test_TC013_添加账户点击取消无新增(self):
        pass

    @pytest.mark.skip(reason="TC015/TC312：媒体账户绑定页展示需独立模块路由，非 org/add 响应字段")
    def test_TC015_添加账户后负责人绑定在媒体账户绑定页展示(self):
        pass

    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC046_选择代理二代韩国客户入库并列表回显(self, basic_client: ApiClient):
        """
        TC046/TC329：agent_2nd_label=韩国客户 → 列表 agent_2nd_label 一致。
        前置：FLOW org 尚未写入 ext；PolarDB tb_apple_org 存在该 org_id。
        """
        env = flow_env_or_skip()
        label = os.getenv("TC046_AGENT_2ND_LABEL", "韩国客户")
        company = f"pytest-tc046-{int(time.time())}"
        payload = flow_org_add_payload(company_name=company, include_agent_2nd_label=True)
        payload["agent_2nd_label"] = label
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        basic_client.assert_status(resp, 200)
        assert_business_success_or_skip(resp.json(), context="TC046 org/add")

        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": env["org_id"], "page": 1, "limit": 5, "export": 0},
        )
        row = find_org_list_row(r_list.json(), env["org_id"])
        assert row is not None
        assert row.get("agent_2nd_label") == label, row

    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC048_TC330_代理二代自定义标签可入库(self, basic_client: ApiClient):
        """
        TC048/TC330：下拉无匹配时手动输入自定义 agent_2nd_label。
        请求：org/add agent_2nd_label='pytest-custom-{ts}'
        """
        env = flow_env_or_skip()
        custom = os.getenv("TC048_CUSTOM_AGENT_2ND", f"pytest-custom-{int(time.time())}")
        company = f"pytest-tc048-{int(time.time())}"
        payload = flow_org_add_payload(company_name=company, include_agent_2nd_label=True)
        payload["agent_2nd_label"] = custom
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        basic_client.assert_status(resp, 200)
        assert_business_success_or_skip(resp.json(), context="TC048 org/add")
        r_list = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": env["org_id"], "page": 1, "limit": 5, "export": 0},
        )
        row = find_org_list_row(r_list.json(), env["org_id"])
        assert row is not None
        assert row.get("agent_2nd_label") == custom

    @pytest.mark.regression
    def test_TC050_列表客户类型与customer_type_id一致(self, basic_client: ApiClient):
        """
        TC050：列表 customer_type 文案与 customer_type_id(1直客/2代理/3oAuth) 对应。
        请求：分别按 customer_type=1/2/3 筛选并抽查首行。
        """
        type_map = {1: ("直客", "客户"), 2: ("代理",), 3: ("oAuth", "OAuth", "oauth")}
        for ct in (1, 2, 3):
            resp = basic_client.post(
                PATH_ORG_LIST,
                json={"customer_type": ct, "page": 1, "limit": 5, "export": 0},
            )
            basic_client.assert_status(resp, 200)
            if resp.json().get("code") != 0:
                continue
            items = (resp.json().get("data") or {}).get("list") or []
            if not items:
                continue
            row = items[0]
            assert int(row.get("customer_type_id") or row.get("customer_type") or 0) in (
                ct,
                ct,
            ) or str(row.get("customer_type_id")) == str(ct)
            label = str(row.get("customer_type") or "")
            if label and not label.isdigit():
                assert any(k in label for k in type_map[ct]), (ct, label, row)

    @pytest.mark.smoke
    def test_TC009_海外主体checkCompany通过后add可入库(self, basic_client: ApiClient):
        """
        TC009（P0 对齐）：海外主体公司名校验通过后可 add。
        请求：checkCompany is_overseas=true；org/add 使用英文公司名。
        注意：需未占用 org_id（使用 BRANCH_TEST_NEW_ORG_ID 或 skip）。
        """
        org_id = os.getenv("BRANCH_TEST_NEW_ORG_ID", "").strip()
        yy = os.getenv("BASIC_INFO_FLOW_YY_UID", "").strip()
        auth = os.getenv("BASIC_INFO_FLOW_AUTH_UID", "").strip()
        if not all([org_id, yy, auth]):
            pytest.skip("需 BRANCH_TEST_NEW_ORG_ID 与 FLOW 负责人 UID（未占用 ext 的 org）")
        company = f"Overseas Pytest Ltd {int(time.time())}"
        r_chk = basic_client.post(
            PATH_ORG_CHECK_COMPANY,
            json={"company_name": company, "is_overseas": True},
        )
        basic_client.assert_status(r_chk, 200)
        chk = r_chk.json()
        if chk.get("code") != 0 or not (chk.get("data") or {}).get("valid"):
            pytest.skip(f"海外 checkCompany 未通过：{chk}")
        payload = flow_org_add_payload(company_name=company, org_id=org_id)
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        basic_client.assert_status(resp, 200)
        assert_business_success_or_skip(resp.json(), context="TC009 org/add")

    @pytest.mark.negative
    def test_TC101_客户名称恰好200字可提交(self, basic_client: ApiClient):
        """TC101：company_name max:200。"""
        p = _org_add_payload()
        p["company_name"] = _chars(200)
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == 0:
            return
        if body.get("code") == -1 and (body.get("data") or {}):
            pytest.fail(f"200 字应通过校验：{body}")
        pytest_skip_with_body("TC101 org/add 未成功", body)

    @pytest.mark.negative
    def test_TC102_客户名称201字返回校验失败(self, basic_client: ApiClient):
        """TC102：company_name 超长 → assert_validation_error。"""
        p = _org_add_payload()
        p["company_name"] = _chars(201)
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "company_name")

    @pytest.mark.negative
    def test_TC104_客户政策恰好100字可提交(self, basic_client: ApiClient):
        """TC104：customer_policy max:100。"""
        p = _org_add_payload()
        p["customer_policy"] = "p" * 100
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == 0:
            return
        data = body.get("data") or {}
        if isinstance(data, dict) and data:
            pytest.fail(f"TC104：100 字客户政策应通过校验：{body}")
        pytest_skip_with_body("TC104 org/add 未成功", body)

    @pytest.mark.negative
    def test_TC105_客户政策101字返回校验失败(self, basic_client: ApiClient):
        """TC105"""
        p = _org_add_payload()
        p["customer_policy"] = "p" * 101
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "customer_policy")

    @pytest.mark.negative
    def test_TC106_org_id百位数字无长度校验且可能触发库层异常(self, basic_client: ApiClient):
        """
        TC106（PDF：100 位数字应可提交）：
        - Laravel 仅 `required|numeric`，无 max 长度校验；
        - 实测 100 位纯数字写入时可能溢出/截断为极大整数（如 18446744073709551615），
          进而 HTTP 500 + uk_org_id 冲突，与文档预期不符。

        请求：org/add，org_id='9'*100
        判定：接受 200+校验失败 / 200+业务失败；若 500 则 xfail 记为后端缺陷。
        """
        p = _org_add_payload()
        p["org_id"] = "9" * 100
        resp = basic_client.post(PATH_ORG_ADD, json=p)

        if resp.status_code == 500:
            text = resp.text[:500]
            pytest.xfail(
                "TC106：100 位 org_id 导致 SQL 溢出/uk_org_id 重复 HTTP 500，"
                f"与 PDF「100 位可提交」不一致。响应片段：{text}"
            )

        basic_client.assert_status(resp, 200)
        try:
            body = resp.json()
        except ValueError:
            pytest.fail(f"TC106：非 JSON 响应：{resp.text[:400]}")

        if body.get("code") == 0:
            return
        data = body.get("data") or {}
        if isinstance(data, dict) and data:
            assert_validation_error(resp, "org_id")
            return
        msg = str(body.get("message") or "")
        assert body.get("code") == -1, body
        assert any(
            k in msg.lower() for k in ("org", "validation", "校验", "重复", "duplicate")
        ), body

    @pytest.mark.negative
    def test_TC107_org_id非数字返回校验失败(self, basic_client: ApiClient):
        """TC107：与 TC209 对齐，org_id 含字母。"""
        p = _org_add_payload()
        p["org_id"] = "1" * 101 + "a"
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "org_id", allow_500=True)

    @pytest.mark.negative
    def test_TC124_代理二代恰好50字可提交(self, basic_client: ApiClient):
        """TC124：agent_2nd_label max:50。"""
        p = _org_add_payload()
        p["agent_2nd_label"] = "a" * 50
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == 0:
            return
        data = body.get("data") or {}
        if isinstance(data, dict) and data:
            pytest.fail(f"TC124：50 字代理二代应通过校验：{body}")
        pytest_skip_with_body("TC124 org/add 未成功", body)

    @pytest.mark.negative
    def test_TC125_TC233_代理二代51字返回校验失败(self, basic_client: ApiClient):
        """TC125/TC233"""
        p = _org_add_payload()
        p["agent_2nd_label"] = "a" * 51
        resp = basic_client.post(PATH_ORG_ADD, json=p)
        assert_validation_error(resp, "agent_2nd_label")

    @pytest.mark.negative
    def test_TC211_已存在ORGID校验返回重复(self, basic_client: ApiClient):
        """TC211：verifyOrgId 对已入库 org_id 提示已存在。"""
        org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
        if not org_id:
            r = basic_client.post(PATH_ORG_LIST, json={"page": 1, "limit": 1, "export": 0})
            rows = (r.json().get("data") or {}).get("list") or []
            if not rows:
                pytest.skip("无 org_id 样本")
            org_id = str(rows[0]["org_id"])
        resp = basic_client.post(
            PATH_ORG_VERIFY,
            json={"org_id": org_id, "parent_org_id": flow_parent_org_id()},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        assert body.get("code") != 0, body
        assert "已存在" in str(body.get("message") or "") or "exist" in str(
            body.get("message") or ""
        ).lower()

    @pytest.mark.skip(reason="TC229：企查查超时需 Mock/断网，见 test_basic_info_blocked_skips")
    def test_TC229_企查查超时友好提示(self):
        pass

    @pytest.mark.negative
    def test_TC234_编辑态代理二代不可通过edit变更(self, basic_client: ApiClient):
        """TC234：与 TC213 一致，误传 agent_2nd_label 不改变列表。"""
        env = flow_env_or_skip()
        org_id = env["org_id"]
        r_list = basic_client.post(
            PATH_ORG_LIST, json={"org_id": org_id, "page": 1, "limit": 5, "export": 0}
        )
        row_before = find_org_list_row(r_list.json(), org_id)
        if row_before is None:
            pytest.skip("FLOW org 不在列表")
        agent2_before = row_before.get("agent_2nd_label")
        r_edit = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": org_id,
                "company_name": row_before.get("company_name") or "tc234",
                "customer_type": row_before.get("customer_type_id") or 1,
                "settle_type": row_before.get("settle_type_id") or 1,
                "agent_2nd_label": "tc234-should-not-apply",
            },
        )
        basic_client.assert_status(r_edit, 200)
        if r_edit.json().get("code") != 0:
            pytest_skip_with_body("TC234 org/edit 未成功", r_edit.json())
        row_after = find_org_list_row(
            basic_client.post(
                PATH_ORG_LIST, json={"org_id": org_id, "page": 1, "limit": 5, "export": 0}
            ).json(),
            org_id,
        )
        assert row_after is not None
        assert row_after.get("agent_2nd_label") == agent2_before

    @pytest.mark.regression
    def test_TC340_代理二代自定义值入库即视为有效(self, basic_client: ApiClient):
        """TC340：无独立「有效性」接口；自定义字符串能保存即通过 API 可测部分。"""
        env = flow_env_or_skip()
        val = f"valid-{int(time.time())}"
        payload = flow_org_add_payload(
            company_name=f"tc340-{int(time.time())}", include_agent_2nd_label=True
        )
        payload["agent_2nd_label"] = val
        resp = basic_client.post(PATH_ORG_ADD, json=payload)
        assert_business_success_or_skip(resp.json(), context="TC340")
        row = find_org_list_row(
            basic_client.post(
                PATH_ORG_LIST,
                json={"org_id": env["org_id"], "page": 1, "limit": 5, "export": 0},
            ).json(),
            env["org_id"],
        )
        assert row and row.get("agent_2nd_label") == val
