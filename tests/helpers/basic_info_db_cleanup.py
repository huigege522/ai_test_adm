# -*- coding: utf-8 -*-
"""基本信息管理 API 测试 · PolarDB / MySQL 测试数据清理。"""

from __future__ import annotations

import logging
import os
from typing import Any

import pymysql

logger = logging.getLogger(__name__)

# OrgManagementService::syncManagers — OrgConstant::COMPANY_USER_PLAT_ID_APPLE
APPLE_COMPANY_USER_PLAT_ID = 9


def _polar_config() -> dict[str, Any] | None:
    host = os.getenv("POLAR_DB_HOST", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("POLAR_DB_PORT", "3306")),
        "db": os.getenv("POLAR_DB_NAME", "test_db"),
        "user": os.getenv("POLAR_DB_USER", "root"),
        "password": os.getenv("POLAR_DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
    }


def _mysql_config() -> dict[str, Any] | None:
    host = os.getenv("DB_HOST", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("DB_PORT", "3306")),
        "db": os.getenv("DB_NAME", "test_db"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
    }


def _commit(cursor: Any) -> None:
    cursor.connection.commit()


def cleanup_org_branch_test_data(
    polar_cursor: Any,
    org_id: str,
    *,
    remove_tb_apple_org: bool = False,
    mysql_cursor: Any | None = None,
) -> None:
    """
    清理 org/add 及分支用例在 Polar / MySQL 产生的测试行。

    remove_tb_apple_org：仅对 pytest 动态 org_id（88 前缀等）建议 True。
    """
    org_id = str(org_id)
    polar_cursor.execute(
        "DELETE FROM apple_app_org_attr WHERE org_id = %s", (org_id,)
    )
    polar_cursor.execute(
        "DELETE FROM tb_apple_app_relation WHERE org_id = %s", (org_id,)
    )
    polar_cursor.execute(
        "DELETE FROM apple_org_ext WHERE org_id = %s", (org_id,)
    )
    if remove_tb_apple_org:
        polar_cursor.execute(
            "DELETE FROM tb_apple_org WHERE org_id = %s", (org_id,)
        )
    _commit(polar_cursor)

    if mysql_cursor is not None:
        mysql_cursor.execute(
            "DELETE FROM cmp_apple_account_base WHERE org_id = %s", (org_id,)
        )
        mysql_cursor.execute(
            """
            DELETE FROM tb_td_company_user
            WHERE plat_id = %s AND company_id = %s
            """,
            (APPLE_COMPANY_USER_PLAT_ID, org_id),
        )
        _commit(mysql_cursor)


def cleanup_app_add_branch_test_data(
    polar_cursor: Any,
    adam_id: str,
    org_id: str,
) -> None:
    """清理 app/add 成功写入的 apple_app_ext / 关系 / 属性行（按 adam_id + org_id）。"""
    adam_id, org_id = str(adam_id), str(org_id)
    polar_cursor.execute(
        """
        DELETE FROM apple_app_org_attr
        WHERE adam_id = %s AND org_id = %s
        """,
        (adam_id, org_id),
    )
    polar_cursor.execute(
        """
        DELETE FROM tb_apple_app_relation
        WHERE adam_id = %s AND org_id = %s
        """,
        (adam_id, org_id),
    )
    polar_cursor.execute(
        "DELETE FROM apple_app_ext WHERE adam_id = %s", (adam_id,)
    )
    _commit(polar_cursor)


def cleanup_relation_attr_branch_test_data(
    polar_cursor: Any,
    adam_id: str,
    org_id: str,
    customer_attribute: int,
) -> None:
    """清理 relation/add 分支用例对 apple_app_org_attr 的写入。"""
    polar_cursor.execute(
        """
        DELETE FROM apple_app_org_attr
        WHERE adam_id = %s AND org_id = %s AND customer_attribute = %s
        """,
        (str(adam_id), str(org_id), int(customer_attribute)),
    )
    _commit(polar_cursor)


def run_branch_test_cleanup(
    *,
    polar_cursor: Any | None = None,
    mysql_cursor: Any | None = None,
    org_id: str | None = None,
    remove_tb_apple_org: bool = False,
    cleanup_app_ext: bool = False,
    adam_id: str | None = None,
    org_id_for_app: str | None = None,
    relation_customer_attribute: int | None = None,
) -> None:
    """
    统一入口：优先使用传入 cursor；未传则按环境变量自建连接（供无 @pytest.mark.db 的用例）。

    cleanup_app_ext：为 True 时才删除 apple_app_ext（避免 relation 用例误删 FLOW 产品 ext）。
    """
    polar_cfg = _polar_config()
    if polar_cursor is None and polar_cfg is None:
        logger.warning("branch cleanup: 未配置 POLAR_DB_HOST，跳过 Polar 清理")
        return

    mysql_cfg = _mysql_config()
    own_polar = polar_cursor is None
    own_mysql = mysql_cursor is None and org_id and mysql_cfg is not None

    polar_conn = None
    mysql_conn = None
    try:
        if polar_cursor is None:
            polar_conn = pymysql.connect(**polar_cfg)
            polar_cursor = polar_conn.cursor()

        if own_mysql:
            mysql_conn = pymysql.connect(**mysql_cfg)
            mysql_cursor = mysql_conn.cursor()

        if org_id:
            cleanup_org_branch_test_data(
                polar_cursor,
                org_id,
                remove_tb_apple_org=remove_tb_apple_org,
                mysql_cursor=mysql_cursor,
            )

        if cleanup_app_ext and adam_id and org_id_for_app:
            cleanup_app_add_branch_test_data(
                polar_cursor, adam_id, org_id_for_app
            )

        if (
            adam_id
            and org_id_for_app is not None
            and relation_customer_attribute is not None
        ):
            cleanup_relation_attr_branch_test_data(
                polar_cursor,
                adam_id,
                org_id_for_app,
                relation_customer_attribute,
            )
    except Exception:
        logger.exception("branch cleanup 失败")
        raise
    finally:
        if own_polar and polar_conn:
            try:
                polar_conn.close()
            except Exception:
                pass
        if own_mysql and mysql_conn:
            try:
                mysql_conn.close()
            except Exception:
                pass
