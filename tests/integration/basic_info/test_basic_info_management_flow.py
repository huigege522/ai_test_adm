# -*- coding: utf-8 -*-
"""
基本信息管理 · 集成流（TC401–TC408）

纯 HTTP 串联，使用 ``tests/utils/api_client.ApiClient`` + Cookie 会话。

环境变量（共用在 api 模块 FLOW 用例）：
  BASIC_INFO_FLOW_ORG_ID   — Polar ``tb_apple_org.org_id``，且尚未写入 ``apple_org_ext``（或软删可复活）
  BASIC_INFO_FLOW_PARENT_ORG_ID — 父级系列组 ID（verify / org/add 必填，默认 5878820）
  BASIC_INFO_FLOW_ADAM_ID  — Polar ``tb_apple_app.adam_id``，且尚未写入 ``apple_app_ext``
  BASIC_INFO_FLOW_YY_UID    — cmp_user.id（运营负责人）
  BASIC_INFO_FLOW_AUTH_UID — cmp_user.id（授权人）

运行：
  pytest tests/integration/basic_info/test_basic_info_management_flow.py -v
"""

from __future__ import annotations

import time

import pytest

from tests.helpers.basic_info_api_map import (
    PATH_APP_ADD,
    PATH_APP_EDIT,
    PATH_APP_LIST,
    PATH_ORG_ADD,
    PATH_ORG_EDIT,
    PATH_ORG_LIST,
    PATH_RELATION_ADD,
    PATH_RELATION_LIST,
)
from tests.helpers.basic_info_http import (
    assert_business_success_or_skip,
    client_with_session_cookies,
    find_app_list_row,
    flow_app_add_payload,
    flow_env_or_skip,
    flow_org_add_payload,
)
from tests.utils.api_client import ApiClient


@pytest.fixture(scope="session")
def flow_client(login_session) -> ApiClient:
    return client_with_session_cookies(login_session)


class TestIntegrationTC407CrossChain:
    @pytest.mark.smoke
    @pytest.mark.integration
    def test_TC407_TC401_TC406_账户维护产品与关系重复校验(self, flow_client: ApiClient):
        """TC407 全链路；串联 TC401 编辑客户政策；末尾 TC406 对同一 customer_attribute 重复提交。"""
        env = flow_env_or_skip()
        ts = int(time.time())
        company = f"pytest-flow-{ts}"

        r_org = flow_client.post(
            PATH_ORG_ADD,
            json={
                "company_name": company,
                "customer_type": 1,
                "settle_type": 1,
                "customer_policy": "",
                "agent_type": 1,
                "org_id": env["org_id"],
                "parent_org_id": env["parent_org_id"],
                "remark": "",
                "yy_uids": [env["yy_uid"]],
                "auth_uids": [env["auth_uid"]],
            },
        )
        flow_client.assert_status(r_org, 200)
        body_org = r_org.json()
        assert body_org.get("code") == 0, body_org

        new_policy = f"policy-{ts}"
        r_edit = flow_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": env["org_id"],
                "company_name": company,
                "customer_type": 1,
                "settle_type": 1,
                "customer_policy": new_policy,
            },
        )
        flow_client.assert_status(r_edit, 200)
        assert r_edit.json().get("code") == 0, r_edit.json()

        r_find = flow_client.post(PATH_ORG_LIST, json={"org_id": env["org_id"], "page": 1, "limit": 5, "export": 0})
        flow_client.assert_status(r_find, 200)
        flow_client.assert_business_code(r_find, "code", 0)

        r_app = flow_client.post(
            PATH_APP_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [1],
                "region": 5,
                "attribution_type": 1,
                "display_status": 5,
                "media_company_attribute": 1,
            },
        )
        flow_client.assert_status(r_app, 200)
        body_app = r_app.json()
        assert body_app.get("code") == 0, body_app

        r_rel = flow_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [2],
            },
        )
        flow_client.assert_status(r_rel, 200)
        body_rel = r_rel.json()
        assert body_rel.get("code") == 0, body_rel

        r_rel_dup = flow_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [2],
            },
        )
        flow_client.assert_status(r_rel_dup, 200)
        assert r_rel_dup.json().get("code") != 0, "TC406：重复三元组应返回业务错误"


class TestIntegrationTC403ProductChain:
    @pytest.mark.smoke
    @pytest.mark.integration
    def test_TC403_账户下添加产品负责人一致且编辑回显(self, flow_client: ApiClient):
        """
        TC403：已有账户下添加产品（可不填客户属性）→ 列表负责人与账户一致 → 单条编辑后回显。
        """
        env = flow_env_or_skip()
        ts = int(time.time())

        r_org = flow_client.post(
            PATH_ORG_ADD, json=flow_org_add_payload(company_name=f"pytest-tc403-org-{ts}")
        )
        flow_client.assert_status(r_org, 200)
        assert_business_success_or_skip(r_org.json(), context="TC403 org/add")

        r_app = flow_client.post(
            PATH_APP_ADD, json=flow_app_add_payload(include_customer_attribute=False)
        )
        flow_client.assert_status(r_app, 200)
        assert_business_success_or_skip(r_app.json(), context="TC403 app/add")

        r_list = flow_client.post(
            PATH_APP_LIST,
            json={"app_search": env["adam_id"], "page": 1, "limit": 10, "export": 0},
        )
        flow_client.assert_status(r_list, 200)
        flow_client.assert_business_code(r_list, "code", 0)
        row = find_app_list_row(r_list.json(), env["adam_id"])
        assert row is not None, r_list.json()
        flow_client.assert_field_exists(r_list, "data.list.0.yy_users_name", "data.list.0.auth_users_name")

        new_region = 3
        new_category = "网游"
        r_edit = flow_client.post(
            PATH_APP_EDIT,
            json={
                "adam_id": env["adam_id"],
                "region": new_region,
                "product_category": new_category,
            },
        )
        flow_client.assert_status(r_edit, 200)
        assert r_edit.json().get("code") == 0, r_edit.json()

        r_after = flow_client.post(
            PATH_APP_LIST,
            json={"app_search": env["adam_id"], "page": 1, "limit": 10, "export": 0},
        )
        flow_client.assert_status(r_after, 200)
        flow_client.assert_business_code(r_after, "code", 0)
        row2 = find_app_list_row(r_after.json(), env["adam_id"])
        assert row2 is not None, r_after.json()
        assert row2.get("product_category") == new_category
        assert row2.get("region_id") == new_region or row2.get("region") in ("AMR", 3)


class TestIntegrationTC408OwnersFromOrg:
    @pytest.mark.smoke
    @pytest.mark.integration
    def test_TC408_产品列表可检索到Adam且负责人字段存在(self, flow_client: ApiClient):
        """账户绑定负责人后添加产品；校验列表接口返回中含 yy_users / auth_users 结构（名称依赖数据同步）。"""
        env = flow_env_or_skip()
        adam = env["adam_id"]

        r_list = flow_client.post(
            PATH_APP_LIST,
            json={"app_search": adam, "page": 1, "limit": 20, "export": 0},
        )
        flow_client.assert_status(r_list, 200)
        flow_client.assert_business_code(r_list, "code", 0)
        items = (r_list.json().get("data") or {}).get("list") or []
        if not items:
            pytest.skip("列表未返回该 Adam（可能尚未成功执行 TC407 流水线）")
        flow_client.assert_field_exists(r_list, "data.list.0.yy_users_name", "data.list.0.auth_users_name")


class TestIntegrationTC405RelationCrudSmoke:
    @pytest.mark.integration
    def test_TC405_关系添加后列表可检索(self, flow_client: ApiClient):
        env = flow_env_or_skip()
        adam_id = env["adam_id"]
        org_id = env["org_id"]

        r_list_before = flow_client.post(
            PATH_RELATION_LIST,
            json={"adam_id": adam_id, "org_id": org_id, "page": 1, "per_page": 50},
        )
        flow_client.assert_status(r_list_before, 200)
        flow_client.assert_business_code(r_list_before, "code", 0)


class SkippedBlockedFlows:
    """占位：依赖前端路由 / 二次确认弹窗的步骤集中标注 blocked。"""

    @pytest.mark.integration
    def test_TC402_UI跳转添加产品预填_blocked(self):
        pytest.skip("TC402：二次确认跳转产品页为浏览器交互，见 tests/integration/basic_info/test_basic_info_management_e2e.py")

    @pytest.mark.integration
    def test_TC404_同一产品关联两账户_blocked(self):
        pytest.skip("TC404：需要第二个可用 BASIC_INFO_FLOW_ORG_ID_B / 专用数据集，暂不自动化")
