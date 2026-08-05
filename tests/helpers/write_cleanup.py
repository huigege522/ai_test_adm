# -*- coding: utf-8 -*-
"""
API 写操作通用清理机制。

用法：
    def test_创建账户(auth_client, write_tracker):
        resp = auth_client.post("/api/org/add", json={...})
        new_id = resp.json()["data"]["id"]

        # 注册 API 清理
        write_tracker.api_call(auth_client, "/api/org/delete", {"id": new_id})

        # 或注册 SQL 清理
        write_tracker.sql("DELETE FROM apple_org_ext WHERE org_id=%s", (new_id,))

    用例结束后自动逆序执行清理（后注册的先清）。

API 约定：
    - 被测 ADM 的删除接口均为 POST（如 org/delete、relation/delete）
    - 清理失败只记日志，不抛异常，避免影响后续用例
"""

import logging
import requests

logger = logging.getLogger(__name__)


class WriteTracker:
    """收集用例中产生的写操作副作用，teardown 时逆序清理。"""

    def __init__(self):
        self._stack: list = []

    # ── 注册 API 清理 ──────────────────────────

    def api_call(self, client, path: str, json: dict | None = None):
        """
        用例结束后 POST 到指定 API 做删除清理。

        client: ApiClient 或 requests.Session（需有 base_url 属性或直接可调）.
        path:   接口路径，如 "/api/org/delete"
        json:   请求体
        """
        base = ""
        sess: requests.Session | None = None
        if hasattr(client, "base_url"):
            base = client.base_url.rstrip("/")
        if hasattr(client, "session"):
            sess = client.session
        elif isinstance(client, requests.Session):
            sess = client
        else:
            sess = client  # 尝试直接当 Session 用

        def _cleanup():
            try:
                url = base + path if base else path
                resp = sess.post(url, json=json or {}, timeout=15)
                logger.info("隔离清理 API: POST %s → %d", path, resp.status_code)
            except Exception:
                logger.exception("隔离清理 API 失败: POST %s", path)

        self._stack.append(_cleanup)

    # ── 注册 SQL 清理 ──────────────────────────

    def sql(self, statement: str, params: tuple | None = None):
        """用例结束后直接连 MySQL 执行清理语句。"""
        def _cleanup():
            try:
                import os
                import pymysql
                from dotenv import load_dotenv
                load_dotenv()
                conn = pymysql.connect(
                    host=os.getenv("DB_HOST", "127.0.0.1"),
                    port=int(os.getenv("DB_PORT", "3306")),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "test_db"),
                    charset="utf8mb4",
                    autocommit=True,
                )
                with conn.cursor() as cur:
                    cur.execute(statement, params or ())
                conn.close()
                logger.info("隔离清理 SQL: %s", statement.split("WHERE")[0][:60] + "...")
            except Exception:
                logger.exception("隔离清理 SQL 失败: %s", statement[:80])

        self._stack.append(_cleanup)

    # ── 执行清理 ────────────────────────────────

    def run(self):
        """逆序执行所有清理任务（后注册的先执行）。"""
        for fn in reversed(self._stack):
            try:
                fn()
            except Exception:
                logger.exception("隔离清理步骤异常")
        if self._stack:
            logger.info("隔离清理完成: %d 项", len(self._stack))
        self._stack.clear()
