"""
API 接口测试示例 — 以"用户模块"为参考模板。

使用说明：
  1. 复制本文件，将文件名替换为实际模块名，如 test_order.py
  2. 将 ENDPOINT 替换为 Apifox 中对应的接口路径
  3. 使用阶段二 Prompt（prompts/02_apifox_to_cases.md）让 AI 补充完整用例
  4. 运行：pytest tests/api/test_example.py -v
"""
import pytest
from tests.utils.api_client import ApiClient

client = ApiClient()


# ────────────────────────────────────────────────────────────
# 用户列表接口  GET /api/user/list
# ────────────────────────────────────────────────────────────

class TestUserList:

    @pytest.mark.smoke
    def test_正常获取用户列表(self):
        resp = client.get("/api/user/list")
        client.assert_status(resp, 200)
        client.assert_business_code(resp, "code", 0)
        client.assert_field_exists(resp, "data", "data.list")

    @pytest.mark.negative
    def test_未登录访问返回401(self):
        unauthenticated = ApiClient(token="invalid_token")
        resp = unauthenticated.get("/api/user/list")
        client.assert_status(resp, 401)

    @pytest.mark.parametrize("page,page_size,expect_200", [
        (1,   10,  True),
        (1,   100, True),
        (0,   10,  False),   # page 不能为 0
        (1,   0,   False),   # page_size 不能为 0
        (1,   101, False),   # page_size 超出上限
        (9999, 10, True),    # 超大页码，返回空列表但不报错
    ])
    @pytest.mark.boundary
    def test_分页参数边界(self, page, page_size, expect_200):
        resp = client.get("/api/user/list", params={"page": page, "pageSize": page_size})
        if expect_200:
            client.assert_status(resp, 200)
        else:
            assert resp.status_code in (400, 422), (
                f"page={page} pageSize={page_size} 期望 4xx，实际 {resp.status_code}"
            )


# ────────────────────────────────────────────────────────────
# 用户创建接口  POST /api/user/create
# ────────────────────────────────────────────────────────────

class TestUserCreate:

    @pytest.mark.smoke
    def test_正常创建用户(self):
        payload = {
            "username": "test_user_001",
            "password": "Test@123456",
            "email": "test001@example.com",
        }
        resp = client.post("/api/user/create", json=payload)
        client.assert_status(resp, 200)
        client.assert_business_code(resp, "code", 0)
        client.assert_field_exists(resp, "data.userId")

    @pytest.mark.negative
    @pytest.mark.parametrize("payload,desc", [
        ({"password": "Test@123456", "email": "a@b.com"}, "缺少 username"),
        ({"username": "u", "email": "a@b.com"}, "缺少 password"),
        ({"username": "u", "password": "Test@123456", "email": "not_an_email"}, "email 格式错误"),
        ({"username": "", "password": "Test@123456", "email": "a@b.com"}, "username 为空字符串"),
        ({"username": "a" * 256, "password": "Test@123456", "email": "a@b.com"}, "username 超长"),
    ])
    def test_必填/格式校验(self, payload, desc):
        resp = client.post("/api/user/create", json=payload)
        assert resp.status_code in (400, 422), f"场景【{desc}】期望 4xx，实际 {resp.status_code}"

    @pytest.mark.regression
    def test_重复用户名返回业务错误(self):
        payload = {"username": "duplicate_user", "password": "Test@123456", "email": "dup@example.com"}
        client.post("/api/user/create", json=payload)
        resp = client.post("/api/user/create", json=payload)
        client.assert_status(resp, 200)
        client.assert_business_code(resp, "code", 40001)  # 按实际业务码修改


# ────────────────────────────────────────────────────────────
# 数据库断言示例（需要 db fixture）
# ────────────────────────────────────────────────────────────

class TestUserCreateWithDB:

    @pytest.mark.db
    def test_创建用户后数据库有记录(self, load_baseline, db_cursor):
        payload = {
            "username": "db_verify_user",
            "password": "Test@123456",
            "email": "dbverify@example.com",
        }
        resp = client.post("/api/user/create", json=payload)
        client.assert_status(resp, 200)

        user_id = resp.json()["data"]["userId"]
        db_cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = db_cursor.fetchone()

        assert row is not None, f"数据库中未找到 userId={user_id} 的记录"
        assert row["username"] == "db_verify_user"
        assert row["email"] == "dbverify@example.com"
