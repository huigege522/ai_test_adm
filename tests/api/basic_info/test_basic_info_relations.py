# -*- coding: utf-8 -*-
"""
基本信息管理 · 账户-产品关系 API

运行：
  pytest tests/api/basic_info/test_basic_info_relations.py -v

负向参数校验实测多为 HTTP 200 + code=-1（非 400/422），见 assert_validation_error。
"""

from __future__ import annotations

import os

import pytest

from tests.helpers.basic_info_api_map import (
    PATH_APP_LIST,
    PATH_APP_VERIFY_ADAM,
    PATH_ORG_LIST,
    PATH_RELATION_ADD,
    PATH_RELATION_DELETE,
    PATH_RELATION_LIST,
)
from tests.helpers.basic_info_http import (
    assert_business_success_or_skip,
    assert_http_401_or_403,
    assert_validation_error,
    pytest_skip_with_body,
    client_with_session_cookies,
    find_app_list_row,
    find_org_list_row,
    find_relation_rows,
    flow_env_or_skip,
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


def _relation_list_body():
    return {"page": 1, "per_page": 20}


class TestRelationList:
    @pytest.mark.smoke
    def test_TC031_P0_关系列表(self, basic_client: ApiClient):
        resp = basic_client.post(PATH_RELATION_LIST, json=_relation_list_body())
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        basic_client.assert_field_exists(resp, "data.list", "data.total")

    @pytest.mark.negative
    def test_TC227_style_低权限无法访问关系列表(self, low_perm_client: ApiClient):
        resp = low_perm_client.post(PATH_RELATION_LIST, json=_relation_list_body())
        assert_http_401_or_403(resp, expect_403=True)

    @pytest.mark.negative
    def test_无会话401(self, anon_client: ApiClient):
        resp = anon_client.post(PATH_RELATION_LIST, json=_relation_list_body())
        assert resp.status_code == 401, resp.text[:400]


class TestRelationAddPrefillViaApi:
    @pytest.mark.smoke
    def test_TC033_账户与产品ID可通过接口解析名称(self, basic_client: ApiClient):
        """
        TC033：添加关系弹窗「自动带出名称」在 API 层等价于：
        org/list 按 org_id 可得 org_name；app/list / verifyAdamId 按 adam_id 可得 app_name。
        """
        env = flow_env_or_skip()
        org_id, adam_id = env["org_id"], env["adam_id"]

        r_org = basic_client.post(
            PATH_ORG_LIST,
            json={"org_id": org_id, "page": 1, "limit": 5, "export": 0},
        )
        basic_client.assert_status(r_org, 200)
        basic_client.assert_business_code(r_org, "code", 0)
        org_row = find_org_list_row(r_org.json(), org_id)
        assert org_row is not None, f"org/list 未返回 org_id={org_id} 的记录"
        assert org_row.get("org_name"), "账户名称应随 org_id 可解析"

        r_app = basic_client.post(
            PATH_APP_LIST,
            json={"app_search": adam_id, "page": 1, "limit": 10, "export": 0},
        )
        basic_client.assert_status(r_app, 200)
        basic_client.assert_business_code(r_app, "code", 0)
        app_row = find_app_list_row(r_app.json(), adam_id)
        app_name = None
        if app_row is not None:
            app_name = app_row.get("app_name") or app_row.get("appName")

        if not app_name:
            r_verify = basic_client.post(
                PATH_APP_VERIFY_ADAM,
                json={"adam_id": adam_id, "org_id": org_id},
            )
            basic_client.assert_status(r_verify, 200)
            body = r_verify.json()
            if body.get("code") == 0:
                wrap = body.get("data") or {}
                if wrap.get("valid") is True:
                    inner = wrap.get("data") if isinstance(wrap.get("data"), dict) else wrap
                    app_name = inner.get("app_name") or inner.get("appName")
            if not app_name:
                pytest.skip(
                    "app/list 与 verifyAdamId 均未解析到 app_name（Adam 可能未建档或 iTunes 不可达）"
                )

        r_rel = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "org_id": org_id,
                "adam_id": adam_id,
                "page": 1,
                "per_page": 20,
            },
        )
        basic_client.assert_status(r_rel, 200)
        basic_client.assert_business_code(r_rel, "code", 0)
        rel_rows = find_relation_rows(r_rel.json(), org_id=org_id, adam_id=adam_id)
        if rel_rows:
            assert rel_rows[0].get("org_name"), "关系列表应含 org_name"
            assert rel_rows[0].get("app_name"), "关系列表应含 app_name"


class TestRelationAddNegative:
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC222_org_id必填(self, basic_client: ApiClient):
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={"adam_id": "123", "customer_attribute": [1]},
        )
        assert_validation_error(resp, "org_id")

    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC240_adam_id必填(self, basic_client: ApiClient):
        """TC240：产品 ID（接口字段 adam_id）为空 → 校验失败。"""
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={"org_id": "123", "customer_attribute": [1]},
        )
        assert_validation_error(resp, "adam_id")

    @pytest.mark.negative
    def test_客户属性必填数组不可为空(self, basic_client: ApiClient):
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": os.getenv("BASIC_INFO_FLOW_ADAM_ID", "1"),
                "org_id": os.getenv("BASIC_INFO_FLOW_ORG_ID", "1"),
                "customer_attribute": [],
            },
        )
        assert_validation_error(resp, "customer_attribute")


class TestRelationAddPositiveFlow:
    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC034_客户属性多选入库(self, basic_client: ApiClient):
        """TC034：customer_attribute [1,2,3] 多选后列表出现对应记录。"""
        env = flow_env_or_skip()
        attrs = [1, 2, 3]
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": attrs,
            },
        )
        basic_client.assert_status(resp, 200)
        assert_business_success_or_skip(resp.json(), context="TC034 relation/add")

        r_list = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "page": 1,
                "per_page": 50,
            },
        )
        basic_client.assert_status(r_list, 200)
        basic_client.assert_business_code(r_list, "code", 0)
        rows = find_relation_rows(r_list.json(), org_id=env["org_id"], adam_id=env["adam_id"])
        found_attrs = {int(r.get("customer_attribute")) for r in rows}
        for a in attrs:
            assert a in found_attrs, f"列表应含 customer_attribute={a}，实际 {found_attrs}"


class TestRelationDeletePositiveFlow:
    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC036_删除关系后列表不可见(self, basic_client: ApiClient):
        """TC036：添加单条关系后 delete，列表不再出现该 id。"""
        env = flow_env_or_skip()
        attr = 3
        r_add = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [attr],
            },
        )
        basic_client.assert_status(r_add, 200)
        assert_business_success_or_skip(r_add.json(), context="TC036 前置 relation/add")

        r_list = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [attr],
                "page": 1,
                "per_page": 20,
            },
        )
        basic_client.assert_status(r_list, 200)
        basic_client.assert_business_code(r_list, "code", 0)
        rows = find_relation_rows(r_list.json(), org_id=env["org_id"], adam_id=env["adam_id"])
        target = next(
            (r for r in rows if int(r.get("customer_attribute") or 0) == attr), None
        )
        if target is None:
            pytest.skip("未在列表找到待删除的关系行（可能已被其它用例删除）")
        rel_id = target["id"]

        r_del = basic_client.post(PATH_RELATION_DELETE, json={"id": rel_id})
        basic_client.assert_status(r_del, 200)
        assert r_del.json().get("code") == 0, r_del.json()

        r_after = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [attr],
                "page": 1,
                "per_page": 20,
            },
        )
        basic_client.assert_status(r_after, 200)
        basic_client.assert_business_code(r_after, "code", 0)
        still = find_relation_rows(
            r_after.json(), org_id=env["org_id"], adam_id=env["adam_id"]
        )
        assert not any(int(r.get("id") or 0) == int(rel_id) for r in still)


class TestRelationDuplicateTC310:
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_TC310_相同三元组重复添加被拒绝(self, basic_client: ApiClient):
        """TC310：相同 org_id + adam_id + customer_attribute 重复提交应业务失败。"""
        env = flow_env_or_skip()
        payload = {
            "adam_id": env["adam_id"],
            "org_id": env["org_id"],
            "customer_attribute": [1],
        }
        r1 = basic_client.post(PATH_RELATION_ADD, json=payload)
        basic_client.assert_status(r1, 200)
        body1 = r1.json()
        if body1.get("code") != 0:
            msg1 = str(body1.get("message") or "")
            if "存在" not in msg1 and "relation" not in msg1.lower():
                assert_business_success_or_skip(body1, context="TC310 首次 relation/add")

        r_dup = basic_client.post(PATH_RELATION_ADD, json=payload)
        basic_client.assert_status(r_dup, 200)
        body = r_dup.json()
        assert body.get("code") != 0, f"TC310：重复三元组应被拒绝：{body}"
        msg = str(body.get("message") or "")
        assert "存在" in msg or "relation" in msg.lower() or body.get("code") == -1


class TestRelationP1GapCoverage:
    """testpoints · P1「未覆盖」· 关系列表/筛选/排序"""

    @pytest.mark.regression
    def test_TC032_关系列表按org_id与adam_id筛选(self, basic_client: ApiClient):
        """
        TC032：POST relation/list 带 org_id、adam_id、customer_type 筛选。
        前置：FLOW 已有关系。
        """
        env = flow_env_or_skip()
        for key, val in (
            ("org_id", env["org_id"]),
            ("adam_id", env["adam_id"]),
            ("customer_type", 1),
        ):
            resp = basic_client.post(
                PATH_RELATION_LIST,
                json={key: val, "page": 1, "per_page": 30},
            )
            basic_client.assert_status(resp, 200)
            basic_client.assert_business_code(resp, "code", 0)
            rows = (resp.json().get("data") or {}).get("list") or []
            if not rows:
                continue
            if key == "org_id":
                assert all(str(r.get("org_id")) == str(val) for r in rows)
            elif key == "adam_id":
                assert all(str(r.get("adam_id")) == str(val) for r in rows)

    @pytest.mark.smoke
    @pytest.mark.db
    def test_TC115_客户属性三项代投自投挂靠均入库(self, basic_client: ApiClient):
        """
        TC115：customer_attribute [1,2,3] 与 TC034 一致，强调展示「代投/自投/挂靠」。
        """
        env = flow_env_or_skip()
        attrs = [1, 2, 3]
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": attrs,
            },
        )
        assert_business_success_or_skip(resp.json(), context="TC115 relation/add")
        r_list = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "page": 1,
                "per_page": 50,
            },
        )
        found = {
            int(r.get("customer_attribute"))
            for r in find_relation_rows(
                r_list.json(), org_id=env["org_id"], adam_id=env["adam_id"]
            )
        }
        for a in attrs:
            assert a in found, found

    @pytest.mark.regression
    def test_TC112_关系筛选无匹配时列表为空(self, basic_client: ApiClient):
        """TC112"""
        resp = basic_client.post(
            PATH_RELATION_LIST,
            json={"org_id": "99999999993", "page": 1, "per_page": 20},
        )
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert (data.get("list") or []) == [] or int(data.get("total") or 0) == 0

    @pytest.mark.regression
    def test_TC341_新增关系后列表按id倒序首条为最新(self, basic_client: ApiClient):
        """
        TC341：orderByDesc t.id；新增后首条 id 最大（同页内）。
        前置：先 add 一条 customer_attribute=2（若已存在则 skip 写入）。
        """
        import time

        env = flow_env_or_skip()
        attr = 2
        r_add = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [attr],
            },
        )
        if r_add.json().get("code") != 0:
            pytest_skip_with_body("TC341 前置 relation/add", r_add.json())
        time.sleep(0.5)
        r_list = basic_client.post(
            PATH_RELATION_LIST,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "page": 1,
                "per_page": 20,
            },
        )
        rows = (r_list.json().get("data") or {}).get("list") or []
        if len(rows) < 2:
            pytest.skip("关系不足 2 条比较排序")
        ids = [int(r.get("id") or 0) for r in rows]
        assert ids == sorted(ids, reverse=True), ids[:5]

    @pytest.mark.skip(reason="TC322：双用户并发编辑需并行会话，暂不自动化")
    def test_TC322_关系并发编辑最终写入(self):
        pass
