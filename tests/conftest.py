"""
pytest 全局配置 — 按职责拆分到 tests/conftest_plugins/ 子模块：
  - tests/conftest_plugins/db.py     : MySQL、PolarDB、load_baseline、adam_id
  - tests/conftest_plugins/auth.py   : login_session、http_session、Playwright E2E
  - tests/conftest_plugins/report.py : pytest-html 报告增强

原 conftest.py 内容已拆分，此文件仅作入口。
"""
import pytest
from tests.conftest_plugins.auth import do_login
from tests.conftest_plugins.report import record_http_call
from tests.helpers.write_cleanup import WriteTracker

pytest_plugins = [
    "tests.conftest_plugins.db",
    "tests.conftest_plugins.auth",
    "tests.conftest_plugins.report",
]


@pytest.fixture(scope="function")
def write_tracker():
    """
    写操作清理追踪器。

    用法：
        def test_创建账户(auth_client, write_tracker):
            resp = auth_client.post("/api/org/add", json={...})
            new_id = resp.json()["data"]["id"]
            write_tracker.api_call(auth_client, "/api/org/delete", {'id': new_id})
            # 或 write_tracker.sql('DELETE FROM ... WHERE id=%s', (new_id,))
    """
    tracker = WriteTracker()
    yield tracker
    tracker.run()


__all__ = ["do_login", "record_http_call", "write_tracker"]
