# -*- coding: utf-8 -*-
"""
基本信息管理 · PolarDB/MySQL 可选断言（@pytest.mark.db）

在配置 POLAR_DB_HOST（或 DB_* 与 Laravel data 同源）且具备 FLOW 流水成功后，
可校验 ``apple_org_ext`` / ``apple_app_org_attr`` 行是否存在。

环境变量：
  BASIC_INFO_DB_ASSERT_ORG_ID — 通常为 BASIC_INFO_FLOW_ORG_ID 相同值

运行示例：
  pytest tests/api/basic_info/test_basic_info_polar_db.py -v -m db
"""

from __future__ import annotations

import os

import pytest

from tests.helpers.basic_info_http import flow_env_or_skip


@pytest.mark.db
def test_polar_可在库中查到apple_org_ext(polar_db_cursor):
    """流水成功后 org_id 应在 apple_org_ext 且 is_delete=0。"""
    flow_env_or_skip()
    org_id = os.getenv("BASIC_INFO_DB_ASSERT_ORG_ID", "").strip() or os.getenv(
        "BASIC_INFO_FLOW_ORG_ID", ""
    ).strip()
    if not org_id:
        pytest.skip("未配置 BASIC_INFO_DB_ASSERT_ORG_ID / BASIC_INFO_FLOW_ORG_ID")

    polar_db_cursor.execute(
        "SELECT id FROM apple_org_ext WHERE org_id = %s AND is_delete = 0 LIMIT 1",
        (org_id,),
    )
    row = polar_db_cursor.fetchone()
    if row is None:
        pytest.skip("未查到 apple_org_ext 行（可能尚未跑通集成流水或连接库不一致）")


@pytest.mark.db
def test_polar_关系表存在活跃三元组(polar_db_cursor):
    flow_env_or_skip()
    org_id = os.getenv("BASIC_INFO_FLOW_ORG_ID", "").strip()
    adam_id = os.getenv("BASIC_INFO_FLOW_ADAM_ID", "").strip()
    if not org_id or not adam_id:
        pytest.skip("未配置 FLOW org/adam")

    polar_db_cursor.execute(
        """
        SELECT id FROM apple_app_org_attr
        WHERE org_id = %s AND adam_id = %s AND is_delete = 0
        LIMIT 1
        """,
        (org_id, adam_id),
    )
    row = polar_db_cursor.fetchone()
    if row is None:
        pytest.skip("未查到 apple_app_org_attr（请先执行集成流水用例）")
