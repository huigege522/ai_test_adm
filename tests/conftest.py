"""
pytest 全局配置 — 按职责拆分到 tests/conftest_plugins/ 子模块：
  - tests/conftest_plugins/db.py     : MySQL、PolarDB、load_baseline、adam_id
  - tests/conftest_plugins/auth.py   : login_session、http_session、Playwright E2E
  - tests/conftest_plugins/report.py : pytest-html 报告增强

原 conftest.py 内容已拆分，此文件仅作入口。
"""
from tests.conftest_plugins.auth import do_login
from tests.conftest_plugins.report import record_http_call

pytest_plugins = [
    "tests.conftest_plugins.db",
    "tests.conftest_plugins.auth",
    "tests.conftest_plugins.report",
]

__all__ = ["do_login", "record_http_call"]
