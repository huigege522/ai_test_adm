"""
ApiClient — 封装 requests.Session，提供：
  - 自动拼接 BASE_URL
  - 统一日志打印（请求/响应）
  - 响应断言辅助方法
  - 支持从 .env 读取认证信息

用法示例：
    client = ApiClient()
    resp = client.get("/api/user/list")
    client.assert_status(resp, 200)
    client.assert_json_field(resp, "data.total", lambda v: v >= 0)
"""
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str = None, token: str = None, timeout: int = None):
        self.base_url = (base_url or os.getenv("BASE_URL", "https://adm.gm825.net")).rstrip("/")
        self.timeout = timeout or int(os.getenv("REQUEST_TIMEOUT", 10))
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        _token = token or os.getenv("AUTH_TOKEN", "")
        if _token:
            self.session.headers.update({"Authorization": f"Bearer {_token}"})

    def _url(self, path: str) -> str:
        return self.base_url + path if path.startswith("/") else path

    def _log(self, resp: requests.Response):
        logger.info(
            "[%s] %s %s → %d (%.0fms)",
            resp.request.method,
            resp.request.url,
            resp.request.body or "",
            resp.status_code,
            resp.elapsed.total_seconds() * 1000,
        )
        try:
            logger.debug("Response: %s", json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            logger.debug("Response body: %s", resp.text[:500])

    # ──────────────────────────────────────────────
    # HTTP 方法
    # ──────────────────────────────────────────────

    def get(self, path: str, params=None, **kwargs) -> requests.Response:
        resp = self.session.get(self._url(path), params=params, timeout=self.timeout, **kwargs)
        self._log(resp)
        return resp

    def post(self, path: str, json=None, data=None, **kwargs) -> requests.Response:
        resp = self.session.post(self._url(path), json=json, data=data, timeout=self.timeout, **kwargs)
        self._log(resp)
        return resp

    def put(self, path: str, json=None, **kwargs) -> requests.Response:
        resp = self.session.put(self._url(path), json=json, timeout=self.timeout, **kwargs)
        self._log(resp)
        return resp

    def delete(self, path: str, **kwargs) -> requests.Response:
        resp = self.session.delete(self._url(path), timeout=self.timeout, **kwargs)
        self._log(resp)
        return resp

    def patch(self, path: str, json=None, **kwargs) -> requests.Response:
        resp = self.session.patch(self._url(path), json=json, timeout=self.timeout, **kwargs)
        self._log(resp)
        return resp

    # ──────────────────────────────────────────────
    # 断言辅助
    # ──────────────────────────────────────────────

    def assert_status(self, resp: requests.Response, expected: int):
        """断言 HTTP 状态码。"""
        assert resp.status_code == expected, (
            f"期望状态码 {expected}，实际为 {resp.status_code}。\n"
            f"响应体：{resp.text[:500]}"
        )

    def assert_business_code(self, resp: requests.Response, code_field: str, expected_code):
        """断言业务码字段，如 {"code": 0}。"""
        body = resp.json()
        actual = self._get_nested(body, code_field)
        assert actual == expected_code, (
            f"业务码 [{code_field}] 期望 {expected_code}，实际为 {actual}。\n"
            f"响应：{json.dumps(body, ensure_ascii=False)}"
        )

    def assert_field_exists(self, resp: requests.Response, *field_paths: str):
        """断言响应体中指定字段路径存在，支持点号路径如 'data.list'。"""
        body = resp.json()
        for path in field_paths:
            value = self._get_nested(body, path)
            assert value is not None, f"字段 [{path}] 不存在或为 null。响应：{body}"

    def assert_json_field(self, resp: requests.Response, field_path: str, check_fn):
        """
        断言字段值满足自定义条件。
        check_fn: callable，接收字段值返回 bool。
        示例：client.assert_json_field(resp, "data.total", lambda v: v >= 0)
        """
        body = resp.json()
        value = self._get_nested(body, field_path)
        assert check_fn(value), (
            f"字段 [{field_path}] = {value!r} 未通过自定义断言。响应：{body}"
        )

    def assert_schema(self, resp: requests.Response, schema: dict):
        """使用 jsonschema 验证响应体结构。"""
        import jsonschema
        jsonschema.validate(instance=resp.json(), schema=schema)

    @staticmethod
    def _get_nested(data: dict, path: str):
        """按点号路径取嵌套字段，如 'data.list.0' 。"""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
            if current is None:
                return None
        return current
