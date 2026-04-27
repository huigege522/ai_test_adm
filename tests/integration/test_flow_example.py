"""
端到端业务流程测试示例 — 以"用户注册→登录→查询个人信息"为参考模板。

使用说明：
  1. 复制本文件，将文件名替换为实际业务流程，如 test_order_flow.py
  2. 使用阶段一 Prompt（prompts/01_req_to_testpoints.md）提取业务流程步骤
  3. 让 AI 按业务流程补充断言
  4. 运行：pytest tests/integration/test_flow_example.py -v
"""
import pytest
from tests.utils.api_client import ApiClient

client = ApiClient()


class TestUserRegisterAndLoginFlow:
    """
    业务流程：用户注册 → 登录获取 Token → 查询个人信息
    覆盖场景：完整正向流程 + 各步骤异常中断
    """

    @pytest.mark.smoke
    def test_完整注册登录查询流程(self):
        # Step 1: 注册
        username = "flow_test_user_001"
        password = "Flow@Test123"
        register_resp = client.post("/api/user/register", json={
            "username": username,
            "password": password,
            "email": "flowtest001@example.com",
        })
        client.assert_status(register_resp, 200)
        client.assert_business_code(register_resp, "code", 0)

        # Step 2: 登录
        login_resp = client.post("/api/auth/login", json={
            "username": username,
            "password": password,
        })
        client.assert_status(login_resp, 200)
        client.assert_business_code(login_resp, "code", 0)
        token = login_resp.json()["data"]["token"]
        assert token, "登录后 token 不应为空"

        # Step 3: 用 token 查询个人信息
        authed_client = ApiClient(token=token)
        profile_resp = authed_client.get("/api/user/profile")
        client.assert_status(profile_resp, 200)
        client.assert_business_code(profile_resp, "code", 0)
        client.assert_json_field(profile_resp, "data.username", lambda v: v == username)

    @pytest.mark.negative
    def test_错误密码登录失败(self):
        login_resp = client.post("/api/auth/login", json={
            "username": "flow_test_user_001",
            "password": "WrongPassword",
        })
        client.assert_status(login_resp, 200)
        # 业务层返回 200 但业务码非 0
        body = login_resp.json()
        assert body.get("code") != 0, "错误密码应返回业务错误码"

    @pytest.mark.negative
    def test_过期Token访问被拒(self):
        expired_client = ApiClient(token="expired.token.here")
        resp = expired_client.get("/api/user/profile")
        assert resp.status_code in (401, 403), (
            f"过期 token 访问期望 401/403，实际 {resp.status_code}"
        )

    @pytest.mark.regression
    def test_注销后Token失效(self):
        # Step 1: 登录拿 token
        login_resp = client.post("/api/auth/login", json={
            "username": "flow_test_user_001",
            "password": "Flow@Test123",
        })
        client.assert_status(login_resp, 200)
        token = login_resp.json()["data"]["token"]

        # Step 2: 注销
        authed_client = ApiClient(token=token)
        logout_resp = authed_client.post("/api/auth/logout")
        client.assert_status(logout_resp, 200)

        # Step 3: 注销后再访问应被拒
        profile_resp = authed_client.get("/api/user/profile")
        assert profile_resp.status_code in (401, 403), (
            f"注销后 token 应失效，实际状态码 {profile_resp.status_code}"
        )
