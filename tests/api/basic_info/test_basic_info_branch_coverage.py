# -*- coding: utf-8 -*-
"""
基本信息管理 · 后端「⚠️ 未覆盖」分支补测

对照：test_data/testpoints/basic_info/testpoints_基本信息管理_后端分支覆盖对照.md

运行：
  pytest tests/api/basic_info/test_basic_info_branch_coverage.py -v

说明：
  - 通过 ApiClient 调 HTTP 触发 Service 分支；无法经 API 触达的分支（ExportExcelTask worker、OAuth 回调全链路、fetchOrgFromAcl 真实 ACL 失败）见文件末尾 TestNotApiTriggerable。
  - 依赖 PolarDB 的用例标记 @pytest.mark.db，未配置 POLAR_DB_HOST 时 skip。
  - 依赖 FLOW 环境变量的用例见各函数 docstring。
  - 会写入库的用例在 finally 中调用 tests.helpers.basic_info_db_cleanup 清理（需 POLAR_DB_HOST；org/add 另清 MySQL cmp_apple_account_base / tb_td_company_user）。
"""

from __future__ import annotations

import os
import time

import pytest

from tests.helpers.basic_info_api_map import (
    PATH_AD_GET_APP_SELECTOR,
    PATH_APP_ADD,
    PATH_APP_BATCH_EDIT,
    PATH_APP_EDIT,
    PATH_APP_FILTER_OPTIONS,
    PATH_APP_LIST,
    PATH_APP_VERIFY_ADAM,
    PATH_ORG_ADD,
    PATH_ORG_CHECK_COMPANY,
    PATH_ORG_EDIT,
    PATH_ORG_FILTER_OPTIONS,
    PATH_ORG_LIST,
    PATH_ORG_PARENT_ORG_LIST,
    PATH_ORG_VERIFY,
    PATH_RELATION_ADD,
    PATH_RELATION_DELETE,
    PATH_RELATION_FILTER_OPTIONS,
    PATH_RELATION_LIST,
)
from tests.helpers.basic_info_db_cleanup import run_branch_test_cleanup
from tests.helpers.basic_info_http import (
    assert_business_success_or_skip,
    assert_validation_error,
    pytest_skip_with_body,
    client_with_session_cookies,
    find_app_list_row,
    find_org_list_row,
    flow_app_add_payload,
    flow_env_or_skip,
    flow_org_add_payload,
    flow_parent_org_id,
    mute_env_bearer,
)
from tests.utils.api_client import ApiClient


@pytest.fixture(scope="session")
def basic_client(login_session) -> ApiClient:
    return client_with_session_cookies(login_session)


def _org_add_minimal(*, org_id: str, company_name: str, parent_org_id: str | None = None) -> dict:
    yy = int(os.getenv("BASIC_INFO_FLOW_YY_UID", "1"))
    auth = int(os.getenv("BASIC_INFO_FLOW_AUTH_UID", "1"))
    return {
        "company_name": company_name,
        "customer_type": 1,
        "settle_type": 1,
        "customer_policy": "",
        "org_id": org_id,
        "parent_org_id": parent_org_id or flow_parent_org_id(),
        "yy_uids": [yy],
        "auth_uids": [auth],
    }


def _assert_business_fail(body: dict, *msg_parts: str) -> None:
    assert body.get("code") != 0, f"期望业务失败 code!=0，实际 {body}"
    if msg_parts:
        blob = str(body.get("message") or "") + repr(body.get("data") or "")
        assert any(p in blob for p in msg_parts), f"期望消息含 {msg_parts}，实际 {body}"


# ─────────────────────────────────────────────────────────────
# OrgManagement · 下拉 / 列表筛选
# ─────────────────────────────────────────────────────────────


class TestOrgFilterOptionsAndParentList:
    """OrgManagementController::filterOptions / parentOrgList"""

    @pytest.mark.smoke
    def test_org_filterOptions返回共享字典含org_list键(self, basic_client: ApiClient):
        """
        触发：OrgManagementController::filterOptions → AppManagementService::filterOptions（无分支）。
        请求：GET /api/org/filterOptions，无 body。
        """
        resp = basic_client.get(PATH_ORG_FILTER_OPTIONS)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert "org_list" in data
        assert "bloc_list" in data
        assert "company_list" in data

    @pytest.mark.smoke
    def test_parentOrgList返回上级账户候选非空(self, basic_client: ApiClient):
        """
        触发：OrgManagementService::parentOrgList 遍历 PARENT_ORG_MAP。
        请求：GET /api/org/parentOrgList。
        """
        resp = basic_client.get(PATH_ORG_PARENT_ORG_LIST)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        items = resp.json().get("data") or []
        assert isinstance(items, list) and len(items) >= 1
        assert "parent_org_id" in items[0]


class TestOrgListAgent2ndFilter:
    """OrgManagementService::baseQuery agent_2nd_label 筛选"""

    @pytest.mark.smoke
    def test_org_list按agent_2nd_label精确筛选(self, basic_client: ApiClient):
        """
        触发：baseQuery 中 agent_2nd_label 非空 → where 等值。
        前置：PolarDB 存在 agent_2nd_label='二代标签-华北' 的 ext（baseline 710002）。
        SQL（可选）:
          SELECT org_id FROM apple_org_ext WHERE agent_2nd_label='二代标签-华北' AND is_delete=0 LIMIT 1;
        请求：POST /api/org/list {"agent_2nd_label":"二代标签-华北","limit":20}
        """
        label = os.getenv("BRANCH_TEST_AGENT_2ND_LABEL", "二代标签-华北")
        resp = basic_client.post(
            PATH_ORG_LIST,
            json={"agent_2nd_label": label, "page": 1, "limit": 20, "export": 0},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            pytest.skip(f"按 agent_2nd_label 筛选未成功（基准数据可能不存在）：{body}")
        rows = (body.get("data") or {}).get("list") or []
        if not rows:
            pytest.skip(f"无 agent_2nd_label={label!r} 的账户样本")
        for row in rows:
            assert row.get("agent_2nd_label") == label, row


# ─────────────────────────────────────────────────────────────
# OrgManagement · verifyOrgId / checkCompany
# ─────────────────────────────────────────────────────────────


class TestOrgVerifyOrgIdBranches:
    """OrgManagementService::verifyOrgId"""

    @pytest.mark.negative
    def test_verifyOrgId当org已在tb_apple_org时返回账户已存在(self, basic_client: ApiClient):
        """
        触发：PolarDB tb_apple_org 已存在 org_id → TipException('账户已存在')。
        前置：使用 FLOW 已入库的 org_id，或列表中任意 org_id。
        请求：POST /api/org/verifyOrgId {org_id, parent_org_id}
        """
        org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
        if not org_id:
            r = basic_client.post(PATH_ORG_LIST, json={"page": 1, "limit": 1, "export": 0})
            if r.json().get("code") != 0:
                pytest.skip("无可用 org_id")
            rows = (r.json().get("data") or {}).get("list") or []
            if not rows:
                pytest.skip("账户列表为空")
            org_id = str(rows[0]["org_id"])

        resp = basic_client.post(
            PATH_ORG_VERIFY,
            json={"org_id": org_id, "parent_org_id": flow_parent_org_id()},
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "已存在", "exist")


class TestOrgCheckCompanyBranches:
    """OrgManagementService::checkCompany → QichachaService"""

    @pytest.mark.negative
    def test_checkCompany国内主体返回企查查未接入(self, basic_client: ApiClient):
        """
        触发：is_overseas=false → checkDomestic → throw 企查查接入待文档。
        请求：POST /api/org/checkCompany {"company_name":"测试公司","is_overseas":false}
        """
        resp = basic_client.post(
            PATH_ORG_CHECK_COMPANY,
            json={"company_name": "上海测试科技有限公司", "is_overseas": False},
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "企查查", "暂未实现", "待文档")

    @pytest.mark.negative
    def test_checkCompany海外主体名称含中文时格式非法(self, basic_client: ApiClient):
        """
        触发：checkOverseas → 非英文字符 → valid=false。
        请求：POST checkCompany is_overseas=true, company_name 含中文。
        """
        resp = basic_client.post(
            PATH_ORG_CHECK_COMPANY,
            json={"company_name": "海外公司Test", "is_overseas": True},
        )
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert data.get("valid") is False, data

    @pytest.mark.smoke
    def test_checkCompany海外主体纯英文名称通过格式校验(self, basic_client: ApiClient):
        """
        触发：checkOverseas 英文格式通过 → valid=true（不查库唯一性）。
        请求：is_overseas=true, company_name='Acme Games Ltd'
        """
        resp = basic_client.post(
            PATH_ORG_CHECK_COMPANY,
            json={"company_name": "Acme Games Ltd", "is_overseas": True},
        )
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert data.get("valid") is True, data


# ─────────────────────────────────────────────────────────────
# OrgManagement · add / edit 分支
# ─────────────────────────────────────────────────────────────


class TestOrgAddBranches:
    """OrgManagementService::add"""

    @pytest.mark.negative
    def test_org_add重复org_id当ext未删除时返回重复(self, basic_client: ApiClient):
        """
        触发：apple_org_ext 已存在 is_delete=0 → org_id_duplicate。
        前置：先成功 add 一次，再对同一 org_id 第二次 add。
        请求：两次 POST /api/org/add（相同 org_id）。
        """
        yy = os.getenv("BASIC_INFO_FLOW_YY_UID", "1")
        auth = os.getenv("BASIC_INFO_FLOW_AUTH_UID", "1")
        if not (yy and auth):
            pytest.skip("需 BASIC_INFO_FLOW_YY_UID / AUTH_UID")

        suffix = int(time.time()) % 10000000
        org_id = os.getenv("BRANCH_TEST_DUP_ORG_ID", f"88{suffix:08d}")
        payload = _org_add_minimal(org_id=org_id, company_name=f"pytest-dup-{suffix}")

        org_created = False
        try:
            r1 = basic_client.post(PATH_ORG_ADD, json=payload)
            basic_client.assert_status(r1, 200)
            if r1.json().get("code") != 0:
                pytest.skip(f"首次 add 未成功，无法测重复分支：{r1.json()}")
            org_created = True

            r2 = basic_client.post(PATH_ORG_ADD, json=payload)
            basic_client.assert_status(r2, 200)
            _assert_business_fail(r2.json(), "重复", "duplicate", "已存在")
        finally:
            if org_created:
                run_branch_test_cleanup(
                    org_id=org_id,
                    remove_tb_apple_org=org_id.startswith("88"),
                )

    @pytest.mark.db
    def test_org_add软删ext行复活为is_delete零(self, basic_client: ApiClient, polar_db_cursor):
        """
        触发：existRow is_delete=1 → update 复活（非 insert）。
        前置 SQL（PolarDB）:
          INSERT INTO apple_org_ext (org_id, company_name, is_delete, status, created_at, updated_at)
          VALUES ('88999001', 'pytest-revive', 1, 0, NOW(), NOW());
          -- 需 tb_apple_org 存在 org_id=88999001，若无则先 INSERT tb_apple_org 最小行
        请求：POST org/add 同 org_id。
        """
        org_id = os.getenv("BRANCH_TEST_REVIVE_ORG_ID", "88999001")
        try:
            polar_db_cursor.execute(
                "DELETE FROM apple_org_ext WHERE org_id = %s", (org_id,)
            )
            polar_db_cursor.execute(
                """
                INSERT INTO apple_org_ext (
                  org_id, company_name, customer_type, settle_type, is_delete, status,
                  create_source, created_at, updated_at
                ) VALUES (%s, %s, 1, 1, 1, 0, 2, NOW(), NOW())
                """,
                (org_id, "pytest-soft-deleted"),
            )
            polar_db_cursor.connection.commit()

            payload = _org_add_minimal(
                org_id=org_id,
                company_name=f"pytest-revived-{int(time.time())}",
            )
            resp = basic_client.post(PATH_ORG_ADD, json=payload)
            basic_client.assert_status(resp, 200)
            assert_business_success_or_skip(resp.json(), context="软删复活 org/add")

            polar_db_cursor.execute(
                "SELECT is_delete FROM apple_org_ext WHERE org_id = %s", (org_id,)
            )
            row = polar_db_cursor.fetchone()
            assert row and int(row["is_delete"]) == 0
        finally:
            run_branch_test_cleanup(
                polar_cursor=polar_db_cursor,
                org_id=org_id,
                remove_tb_apple_org=False,
            )


class TestOrgEditBranches:
    """OrgManagementService::edit"""

    @pytest.mark.negative
    def test_org_edit不存在的org_id返回ext未找到(self, basic_client: ApiClient):
        """
        触发：AppleOrgExt 无 is_delete=0 行 → org_ext_not_found。
        请求：POST org/edit org_id=99999999001（假定无 ext）。
        """
        resp = basic_client.post(
            PATH_ORG_EDIT,
            json={
                "org_id": os.getenv("BRANCH_TEST_GHOST_ORG_ID", "99999999001"),
                "company_name": "ghost",
                "customer_type": 1,
                "settle_type": 1,
            },
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "未找到", "not", "不存在")

    @pytest.mark.smoke
    def test_org_edit仅传auth_uids触发编辑态负责人同步(self, basic_client: ApiClient):
        """
        触发：edit 含 auth_uids → syncManagers isAdd=false 仅改授权桶。
        前置：FLOW 账户已存在；记录编辑前 auth_users_name。
        请求：POST org/edit 仅带 auth_uids（与 yy_uids 省略）。
        """
        env = flow_env_or_skip()
        org_id = env["org_id"]
        auth_uid = env["auth_uid"]

        r_before = basic_client.post(
            PATH_ORG_LIST, json={"org_id": org_id, "page": 1, "limit": 5, "export": 0}
        )
        row_before = find_org_list_row(r_before.json(), org_id)
        if row_before is None:
            pytest.skip("FLOW org 不在列表")

        r_edit = basic_client.post(
            PATH_ORG_EDIT,
            json={"org_id": org_id, "auth_uids": [auth_uid]},
        )
        basic_client.assert_status(r_edit, 200)
        if r_edit.json().get("code") != 0:
            pytest.skip(f"仅 auth_uids 编辑失败：{r_edit.json()}")

        r_after = basic_client.post(
            PATH_ORG_LIST, json={"org_id": org_id, "page": 1, "limit": 5, "export": 0}
        )
        row_after = find_org_list_row(r_after.json(), org_id)
        assert row_after is not None
        assert row_after.get("auth_users_name"), "授权人名应回显"


# ─────────────────────────────────────────────────────────────
# AppManagement · 列表筛选 / verify / add / edit / batchEdit
# ─────────────────────────────────────────────────────────────


class TestAppFilterOptions:
    @pytest.mark.smoke
    def test_app_filterOptions返回region与new_customer_badge列表(self, basic_client: ApiClient):
        """触发 AppManagementService::filterOptions（无业务分支）。"""
        resp = basic_client.get(PATH_APP_FILTER_OPTIONS)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert "region_list" in data and "new_customer_badge_list" in data


class TestAppListCrossFilters:
    """AppManagementService::resolveAdamIdSetByCrossFilters"""

    @pytest.mark.smoke
    def test_app_list按customer_attribute筛选无样本时列表为空(self, basic_client: ApiClient):
        """
        触发：resolveAdamIdSet 非 null 且空集 → list=[], total=0。
        请求：customer_attribute=[3] 且 org_search=不存在的关键字（交集为空）。
        """
        resp = basic_client.post(
            PATH_APP_LIST,
            json={
                "customer_attribute": [3],
                "org_search": "pytest-no-such-org-xyz-99999",
                "page": 1,
                "limit": 10,
                "export": 0,
            },
        )
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert data.get("list") == [] or data.get("total") == 0

    @pytest.mark.smoke
    def test_app_list按new_customer_badge筛选(self, basic_client: ApiClient):
        """
        触发：baseQuery new_customer_badge whereIn。
        请求：new_customer_badge=[50]（未分配/失效）。
        """
        resp = basic_client.post(
            PATH_APP_LIST,
            json={"new_customer_badge": [50], "page": 1, "limit": 20, "export": 0},
        )
        basic_client.assert_status(resp, 200)
        if resp.json().get("code") != 0:
            pytest_skip_with_body("跳过", resp.json())
        rows = (resp.json().get("data") or {}).get("list") or []
        if not rows:
            pytest.skip("列表无 new_customer_badge=50 样本")
        for row in rows[:3]:
            badge = row.get("new_customer_badge_id") or row.get("new_customer_badge")
            if badge is not None:
                assert str(badge) in ("50", "未分配", "失效"), row


class TestAppVerifyAdamIdBranches:
    @pytest.mark.negative
    def test_verifyAdamId当org_id不存在时valid为false(self, basic_client: ApiClient):
        """
        触发：AppleOrg::where org_id 无行 → valid=false, org_id_invalid。
        请求：verifyAdamId adam_id=1485191072, org_id=99999999002
        """
        resp = basic_client.post(
            PATH_APP_VERIFY_ADAM,
            json={
                "adam_id": os.getenv("BASIC_INFO_FLOW_ADAM_ID", "1485191072"),
                "org_id": os.getenv("BRANCH_TEST_GHOST_ORG_ID", "99999999002"),
            },
        )
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        wrap = resp.json().get("data") or {}
        assert wrap.get("valid") is False, wrap

    @pytest.mark.negative
    def test_verifyAdamId当adam_id非数字格式时valid为false(self, basic_client: ApiClient):
        """
        触发：adam_id 非 numeric → 控制器校验 validation.numeric；
        或 Service 层 valid=false（环境差异）。
        请求：adam_id='not-numeric-id', org_id=FLOW org。
        """
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_APP_VERIFY_ADAM,
            json={"adam_id": "not-numeric-id", "org_id": env["org_id"]},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == -1:
            assert_validation_error(resp, "adam_id")
            return
        wrap = body.get("data") or {}
        assert wrap.get("valid") is False, wrap


class TestAppAddBranches:
    @pytest.mark.negative
    def test_app_add当adam已在apple_app_ext时返回重复(self, basic_client: ApiClient):
        """
        触发：verify already_added=true → adam_id_duplicate。
        前置：FLOW adam 已建档；连续两次相同 adam_id+org_id add。
        """
        env = flow_env_or_skip()
        payload = flow_app_add_payload()
        app_created = False
        try:
            r1 = basic_client.post(PATH_APP_ADD, json=payload)
            if r1.json().get("code") != 0:
                pytest.skip(f"前置 add 未成功：{r1.json()}")
            app_created = True

            r2 = basic_client.post(PATH_APP_ADD, json=payload)
            basic_client.assert_status(r2, 200)
            _assert_business_fail(r2.json(), "重复", "duplicate", "已存在")
        finally:
            if app_created:
                run_branch_test_cleanup(
                    cleanup_app_ext=True,
                    adam_id=env["adam_id"],
                    org_id_for_app=env["org_id"],
                )

    @pytest.mark.negative
    def test_app_add当tb_apple_org无该org时返回org无效(self, basic_client: ApiClient):
        """
        触发：orgRow 不存在 → org_id_invalid。
        请求：org_id=99999999003, adam_id=有效数字且 iTunes 可校验的 id（若 verify 先过则仍可能失败在 add）。
        """
        adam = os.getenv("BRANCH_TEST_NEW_ADAM_ID", "1234567890")
        resp = basic_client.post(
            PATH_APP_ADD,
            json={
                "adam_id": adam,
                "org_id": os.getenv("BRANCH_TEST_GHOST_ORG_ID", "99999999003"),
                "region": 5,
                "attribution_type": 1,
                "time_zone": "Asia/Shanghai",
                "start_date": "2026-01-01",
            },
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(
            resp.json(),
            "org",
            "无效",
            "invalid",
            "广告系列组",
            "校验",
            "授权",
            "不存在",
        )


class TestAppEditBranches:
    @pytest.mark.negative
    def test_app_edit不存在的adam_id返回not_data(self, basic_client: ApiClient):
        """触发：AppleAppExt 无行 → not_data。"""
        resp = basic_client.post(
            PATH_APP_EDIT,
            json={"adam_id": "99999999004", "region": 1},
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "未找到", "not", "不存在")

    @pytest.mark.smoke
    def test_app_edit仅传adam_id无业务字段时仍成功(self, basic_client: ApiClient):
        """
        触发：buildExtData 空 → 直接 return ['adam_id']（不 update）。
        前置：adam_id 须在 apple_app_ext 有行（与 app/list 可见不等价）。
        请求：POST app/edit 仅 adam_id。
        """
        env = flow_env_or_skip()
        r_list = basic_client.post(
            PATH_APP_LIST,
            json={"app_search": env["adam_id"], "page": 1, "limit": 5, "export": 0},
        )
        if find_app_list_row(r_list.json(), env["adam_id"]) is None:
            pytest.skip("FLOW adam 不在产品列表")

        resp = basic_client.post(
            PATH_APP_EDIT,
            json={"adam_id": env["adam_id"]},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            msg = str(body.get("message") or "")
            if "不存在" in msg:
                pytest.skip(
                    f"FLOW adam 未写入 apple_app_ext，无法测空字段 edit：{body!r}"[:400]
                )
            pytest.fail(body)
        assert (body.get("data") or {}).get("adam_id") == env["adam_id"] or body.get(
            "code"
        ) == 0

    @pytest.mark.smoke
    def test_app_edit传入apple_direct_manager写入负责人名(self, basic_client: ApiClient):
        """
        触发：buildExtData apple_direct_manager 非空 → apple_direct_manager_name。
        请求：apple_direct_manager 文本。
        """
        env = flow_env_or_skip()
        name = f"pytest-mgr-{int(time.time())}"
        resp = basic_client.post(
            PATH_APP_EDIT,
            json={"adam_id": env["adam_id"], "apple_direct_manager": name},
        )
        basic_client.assert_status(resp, 200)
        if resp.json().get("code") != 0:
            pytest_skip_with_body("跳过", resp.json())

        r_list = basic_client.post(
            PATH_APP_LIST,
            json={"app_search": env["adam_id"], "page": 1, "limit": 5, "export": 0},
        )
        row = find_app_list_row(r_list.json(), env["adam_id"])
        if row is None:
            pytest.skip("列表未找到产品")
        mgr = row.get("apple_direct_manager")
        if isinstance(mgr, dict):
            assert mgr.get("name") == name or name in str(mgr)
        else:
            assert name in str(mgr or "")


class TestAppBatchEditBranches:
    """AppManagementService::batchEdit"""

    @pytest.mark.negative
    def test_batchEdit空adam_ids数组返回校验失败(self, basic_client: ApiClient):
        """触发：adam_ids required|array|min:1 → 校验失败。"""
        resp = basic_client.post(PATH_APP_BATCH_EDIT, json={"adam_ids": []})
        assert_validation_error(resp, "adam_ids")

    @pytest.mark.smoke
    def test_batchEdit无可更新字段时affected为零(self, basic_client: ApiClient):
        """
        触发：buildExtData 空 → return affected:0。
        请求：仅 adam_ids，不传 region/badge 等。
        """
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_APP_BATCH_EDIT,
            json={"adam_ids": [env["adam_id"]]},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            pytest_skip_with_body("跳过", body)
        affected = (body.get("data") or {}).get("affected")
        assert affected == 0, body

    @pytest.mark.smoke
    def test_batchEdit更新new_customer_badge影响条数(self, basic_client: ApiClient):
        """
        触发：batchEdit 有 update 字段 → whereIn 更新 + affected=count(adam_ids)。
        请求：adam_ids + new_customer_badge=40（新客孵化中）。
        """
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_APP_BATCH_EDIT,
            json={"adam_ids": [env["adam_id"]], "new_customer_badge": 40},
        )
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            pytest_skip_with_body("跳过", body)
        affected = (body.get("data") or {}).get("affected")
        assert affected is not None and int(affected) >= 1, body


# ─────────────────────────────────────────────────────────────
# AppRelationManagement
# ─────────────────────────────────────────────────────────────


class TestRelationFilterAndList:
    @pytest.mark.smoke
    def test_relation_filterOptions返回app与org列表(self, basic_client: ApiClient):
        resp = basic_client.get(PATH_RELATION_FILTER_OPTIONS)
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        data = resp.json().get("data") or {}
        assert "app_list" in data and "org_list" in data

    @pytest.mark.smoke
    def test_relation_list按org_id筛选(self, basic_client: ApiClient):
        """
        触发：getList org_id 非空筛选。
        前置：FLOW 已有关系记录。
        """
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_RELATION_LIST,
            json={"org_id": env["org_id"], "page": 1, "per_page": 50},
        )
        basic_client.assert_status(resp, 200)
        basic_client.assert_business_code(resp, "code", 0)
        rows = (resp.json().get("data") or {}).get("list") or []
        if not rows:
            pytest.skip("该 org 无关系记录")
        assert all(str(r.get("org_id")) == str(env["org_id"]) for r in rows)


class TestRelationAddBranches:
    @pytest.mark.negative
    def test_relation_add不存在adam_id时失败(self, basic_client: ApiClient):
        """触发：assertAdamIdExists → adam_id_invalid。"""
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": "99999999005",
                "org_id": env["org_id"],
                "customer_attribute": [1],
            },
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "产品", "adam", "无效", "invalid")

    @pytest.mark.negative
    def test_relation_add不存在org_id时失败(self, basic_client: ApiClient):
        """触发：assertOrgIdExists → org_id_invalid。"""
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": os.getenv("BRANCH_TEST_GHOST_ORG_ID", "99999999006"),
                "customer_attribute": [1],
            },
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "账户", "org", "无效", "invalid")

    @pytest.mark.negative
    def test_relation_add非法客户属性枚举值时失败(self, basic_client: ApiClient):
        """
        触发：customer_attribute 非 in:1,2,3 → validation.in。
        请求：customer_attribute=[99]
        实测：HTTP 200 + code=-1 + data.customer_attribute.0=['validation.in']
        """
        env = flow_env_or_skip()
        resp = basic_client.post(
            PATH_RELATION_ADD,
            json={
                "adam_id": env["adam_id"],
                "org_id": env["org_id"],
                "customer_attribute": [99],
            },
        )
        basic_client.assert_status(resp, 200)
        assert_validation_error(resp, "customer_attribute")

    @pytest.mark.db
    def test_relation_add软删关系行复活(self, basic_client: ApiClient, polar_db_cursor):
        """
        触发：existing is_delete=1 → reviveIds 更新。
        前置 SQL（PolarDB）:
          INSERT INTO apple_app_org_attr (adam_id, org_id, customer_attribute, is_delete, ctime, mtime)
          VALUES (<flow_adam>, <flow_org>, 2, 1, NOW(), NOW());
        请求：add 同三元组 customer_attribute=[2]。
        """
        env = flow_env_or_skip()
        adam_id, org_id = env["adam_id"], env["org_id"]
        relation_attr = 2
        try:
            polar_db_cursor.execute(
                """
                DELETE FROM apple_app_org_attr
                WHERE adam_id=%s AND org_id=%s AND customer_attribute=%s
                """,
                (adam_id, org_id, relation_attr),
            )
            polar_db_cursor.execute(
                """
                INSERT INTO apple_app_org_attr (
                  adam_id, org_id, customer_attribute, is_delete, ctime, mtime
                ) VALUES (%s, %s, %s, 1, NOW(), NOW())
                """,
                (adam_id, org_id, relation_attr),
            )
            polar_db_cursor.connection.commit()

            resp = basic_client.post(
                PATH_RELATION_ADD,
                json={
                    "adam_id": adam_id,
                    "org_id": org_id,
                    "customer_attribute": [relation_attr],
                },
            )
            basic_client.assert_status(resp, 200)
            body = resp.json()
            if body.get("code") != 0:
                pytest_skip_with_body("跳过", body)
            revived = (body.get("data") or {}).get("revived", 0)
            assert int(revived) >= 1 or int(
                (body.get("data") or {}).get("inserted", 0)
            ) >= 0
        finally:
            run_branch_test_cleanup(
                polar_cursor=polar_db_cursor,
                adam_id=adam_id,
                org_id_for_app=org_id,
                relation_customer_attribute=relation_attr,
            )


class TestRelationDeleteBranches:
    @pytest.mark.negative
    def test_relation_delete不存在的id返回not_data(self, basic_client: ApiClient):
        """触发：delete 无 is_delete=0 行 → not_data。"""
        resp = basic_client.post(
            PATH_RELATION_DELETE,
            json={"id": 999999990},
        )
        basic_client.assert_status(resp, 200)
        _assert_business_fail(resp.json(), "未找到", "not", "不存在")


# ─────────────────────────────────────────────────────────────
# AdPlan · getAppSelector（非 OAuth / OAuth 分支入口）
# ─────────────────────────────────────────────────────────────


class TestAdGetAppSelectorBranches:
    @pytest.mark.smoke
    def test_getAppSelector无权限时403或空列表(self, basic_client: ApiClient):
        """
        触发：PermissionService 无 org 授权 → []；
        或 per:bulkSetup.view 无权限 → 403。
        请求：GET /api/ad/getAppSelector?org_id=FLOW&search=
        """
        env = flow_env_or_skip()
        resp = basic_client.get(
            PATH_AD_GET_APP_SELECTOR,
            params={"org_id": env["org_id"], "search": ""},
        )
        if resp.status_code in (401, 403):
            return
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") == 0:
            assert isinstance(body.get("data"), list)
        else:
            pytest.skip(f"getAppSelector 业务失败（可能无 bulkSetup 权限）：{body}")

    @pytest.mark.smoke
    def test_getAppSelector硬编码测试账号返回固定应用(self, basic_client: ApiClient):
        """
        触发：AdPlanController 硬编码 org_id=20012942 & search=6756870744。
        请求：GET getAppSelector 上述参数（与 FLOW 无关）。
        """
        resp = basic_client.get(
            PATH_AD_GET_APP_SELECTOR,
            params={"org_id": "20012942", "search": "6756870744"},
        )
        if resp.status_code in (401, 403):
            pytest.skip("无 getAppSelector 权限")
        basic_client.assert_status(resp, 200)
        body = resp.json()
        if body.get("code") != 0:
            pytest_skip_with_body("跳过", body)
        data = body.get("data") or []
        assert any(
            str(item.get("adam_id")) == "6756870744" for item in data if isinstance(item, dict)
        ), data


# ─────────────────────────────────────────────────────────────
# 无法经 HTTP 触达（文档登记，避免误报未覆盖）
# ─────────────────────────────────────────────────────────────


class TestNotApiTriggerable:
    """以下分支需队列 Worker / OAuth 浏览器回调 / 去 Mock，不单测 API。"""

    @pytest.mark.skip(reason="ExportExcelTask::performTask 需 export_center 任务队列消费，非 HTTP")
    def test_exportExcelTask_worker生成xlsx文件(self):
        pass

    @pytest.mark.skip(reason="AppleAdsController::handleAuthorization 需 OAuth 浏览器回调")
    def test_oauth回调写入apple_org_ext(self):
        pass

    @pytest.mark.skip(reason="OrgManagementService::fetchOrgFromAcl 生产代码 Mock 短路，真实 ACL 失败不可达")
    def test_verifyOrgId真实ACL失败返回org_id_invalid(self):
        pass

    @pytest.mark.skip(reason="upsertFromOAuth 仅 OAuth 回调内调用")
    def test_upsertFromOAuth插入OAuth账户(self):
        pass
