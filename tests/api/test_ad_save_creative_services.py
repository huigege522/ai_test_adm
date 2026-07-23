# -*- coding: utf-8 -*-
"""
广告素材服务 - 保存创意素材 POST /api/ad/saveCreativeServices

业务背景：
  广告投放前，运营人员录入创意素材信息。包含产品名称、素材类型、
  素材尺寸（宽x高）、文件格式、文件大小、需求数量。

字段说明（基于行业常识推导）：
  product_name   : 推广产品名称，如"王者荣耀"、"拼多多"
  material_type  : 素材类型枚举（1=图片 2=视频 3=HTML5 4=原生 等）
  width/height   : 素材像素尺寸，如横幅 320x50、全屏 1080x1920
  material_format: 文件格式枚举（1=JPG 2=PNG 3=GIF 4=MP4 等）
  material_size  : 文件大小（KB），通常 < 2GB
  quantity_needed: 需要的素材数量
"""

import os
import pytest
import requests
from dotenv import load_dotenv
from tests.utils.api_client import ApiClient
from tests.helpers.basic_info_http import client_with_session_cookies

load_dotenv()

PATH = "/api/ad/saveCreativeServices"
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

# ── 有意义的业务数据 ────────────────────────────

# 常见广告素材规格
VALID_CREATIVES = [
    # (描述, product_name, material_type, width, height, material_format, material_size, quantity)
    ("横幅广告", "拼多多-电商推广", 1, 320, 50, 1, 80, 3),
    ("中等矩形", "王者荣耀-游戏推广", 1, 300, 250, 2, 150, 2),
    ("全屏竖版视频", "抖音-短视频推广", 2, 1080, 1920, 4, 5120, 1),
    ("插屏广告", "美团-外卖推广", 1, 750, 1334, 2, 200, 5),
    ("开屏广告", "支付宝-金融推广", 1, 1080, 1920, 2, 300, 2),
]


def make_body(product_name, material_type, width, height, material_format, material_size, quantity_needed):
    return {
        "product_name": product_name,
        "material_type": material_type,
        "width": width,
        "height": height,
        "material_format": material_format,
        "material_size": material_size,
        "quantity_needed": quantity_needed,
    }


@pytest.fixture(scope="session")
def auth_client(login_session) -> ApiClient:
    return client_with_session_cookies(login_session)


# ────────────────────────────────────────────────
# 一、正常业务场景 — 真实的广告素材录入
# ────────────────────────────────────────────────

class Test正常创建广告素材:

    @pytest.mark.smoke
    @pytest.mark.parametrize("desc,product,mt,w,h,mf,ms,qty", VALID_CREATIVES)
    def test_常见素材规格创建成功(self, auth_client, desc, product, mt, w, h, mf, ms, qty):
        """运营录入不同规格的广告素材，均应成功。"""
        resp = auth_client.post(PATH, json=make_body(product, mt, w, h, mf, ms, qty))
        auth_client.assert_status(resp, 200)
        auth_client.assert_business_code(resp, "code", 0)

    @pytest.mark.smoke
    def test_同一产品可多次录入不同素材(self, auth_client):
        """一个产品可能需要多种素材规格，每次录入都是独立的。"""
        resp1 = auth_client.post(PATH, json=make_body("京东-618大促", 1, 320, 50, 1, 50, 2))
        resp2 = auth_client.post(PATH, json=make_body("京东-618大促", 2, 1080, 1920, 4, 8192, 1))
        auth_client.assert_business_code(resp1, "code", 0)
        auth_client.assert_business_code(resp2, "code", 0)


# ────────────────────────────────────────────────
# 二、业务规则验证 — 从业务角度应该拒绝的场景
# ────────────────────────────────────────────────

class Test业务规则校验:

    # ── 素材尺寸应为正数 ──

    @pytest.mark.negative
    @pytest.mark.parametrize("field,value,desc", [
        ("width", 0, "横幅宽度为0像素"),
        ("height", 0, "高度为0像素"),
        ("width", -1, "宽度为负数"),
        ("height", -1, "高度为负数"),
    ])
    def test_素材尺寸为零或负数应拒绝(self, auth_client, field, value, desc):
        """素材尺寸为零或负数在业务上没有意义，应被拒绝。"""
        body = make_body("测试产品", 1, 1920, 1080, 1, 100, 3)
        body[field] = value
        resp = auth_client.post(PATH, json=body)
        # 从业务角度期望 code=-1；若后端实际接受（code=0），标记为后端校验缺失
        code = resp.json().get("code")
        if code == 0:
            pytest.fail(
                f"⚠️ 后端校验缺失：{desc} 被接受（code=0），"
                f"但业务上素材尺寸必须为正数。请确认产品规范后决定是否修复。"
            )

    # ── 需求数量应为正数 ──

    @pytest.mark.negative
    @pytest.mark.parametrize("qty,desc", [
        (0, "需要0份素材"),
        (-1, "需要-1份素材"),
        (-100, "需要-100份素材"),
    ])
    def test_需求数量为零或负数应拒绝(self, auth_client, qty, desc):
        """需求数量为零或负数在业务上没有意义。"""
        body = make_body("测试产品", 1, 320, 50, 1, 100, qty)
        resp = auth_client.post(PATH, json=body)
        code = resp.json().get("code")
        if code == 0:
            pytest.fail(
                f"⚠️ 后端校验缺失：'{desc}' 被接受（code=0），"
                f"但业务上需求数量必须为正数。"
            )

    # ── 文件大小应为正数 ──

    @pytest.mark.negative
    @pytest.mark.parametrize("size_kb,desc", [
        (0, "文件大小为0KB"),
        (-1, "文件大小为负数"),
    ])
    def test_文件大小为零或负数应拒绝(self, auth_client, size_kb, desc):
        """文件大小为零或负数在业务上没有意义。"""
        body = make_body("测试产品", 1, 320, 50, 1, size_kb, 3)
        resp = auth_client.post(PATH, json=body)
        code = resp.json().get("code")
        if code == 0:
            pytest.fail(
                f"⚠️ 后端校验缺失：'{desc}' 被接受（code=0），"
                f"但业务上文件大小必须为正数。"
            )

    # ── 文件大小合理性 ──

    @pytest.mark.boundary
    def test_文件大小1KB可创建(self, auth_client):
        """1KB 是最小的合理文件大小。"""
        body = make_body("测试产品", 1, 320, 50, 1, 1, 1)
        resp = auth_client.post(PATH, json=body)
        auth_client.assert_business_code(resp, "code", 0)

    @pytest.mark.boundary
    def test_文件大小2GB可创建(self, auth_client):
        """2GB（2097152KB）是视频素材常见上限。"""
        body = make_body("测试产品", 2, 1920, 1080, 4, 2097152, 1)
        resp = auth_client.post(PATH, json=body)
        auth_client.assert_business_code(resp, "code", 0)

    # ── product_name 应有意义 ──

    @pytest.mark.negative
    def test_产品名称为空应拒绝(self, auth_client):
        body = make_body("", 1, 320, 50, 1, 100, 3)
        resp = auth_client.post(PATH, json=body)
        assert resp.json()["code"] == -1, "产品名称为空应被拒绝"

    # ── 素材类型枚举有效性 ──

    @pytest.mark.negative
    def test_无效素材类型应拒绝(self, auth_client):
        """material_type=99 不在有效枚举中，应被拒绝。"""
        body = make_body("测试产品", 99, 320, 50, 1, 100, 3)
        resp = auth_client.post(PATH, json=body)
        code = resp.json().get("code")
        if code == 0:
            pytest.fail(
                "⚠️ 后端校验缺失：material_type=99 被接受（code=0），"
                "但该值不在有效枚举范围内。"
            )

    @pytest.mark.negative
    def test_无效素材格式应拒绝(self, auth_client):
        """material_format=99 不在有效枚举中，应被拒绝。"""
        body = make_body("测试产品", 1, 320, 50, 99, 100, 3)
        resp = auth_client.post(PATH, json=body)
        code = resp.json().get("code")
        if code == 0:
            pytest.fail(
                "⚠️ 后端校验缺失：material_format=99 被接受（code=0），"
                "但该值不在有效枚举范围内。"
            )

    # ── 图片格式不应传视频尺寸（业务逻辑一致性） ──

    @pytest.mark.boundary
    def test_图片素材300KB以内创建成功(self, auth_client):
        """JPEG/PNG 图片素材通常 < 300KB。"""
        body = make_body("测试产品-图片", 1, 320, 50, 1, 150, 3)
        resp = auth_client.post(PATH, json=body)
        auth_client.assert_business_code(resp, "code", 0)


# ────────────────────────────────────────────────
# 三、参数缺失 — 必填校验
# ────────────────────────────────────────────────

class Test必填字段校验:

    FIELDS = ["product_name", "material_type", "width", "height",
              "material_format", "material_size", "quantity_needed"]

    @pytest.mark.negative
    @pytest.mark.parametrize("missing", FIELDS)
    def test_缺失必填字段应拒绝(self, auth_client, missing):
        """缺少任一必填字段应提示错误。"""
        body = make_body("测试产品", 1, 320, 50, 1, 100, 3)
        del body[missing]
        resp = auth_client.post(PATH, json=body)
        assert resp.json()["code"] == -1, f"缺 {missing} 应返回 code=-1"


# ────────────────────────────────────────────────
# 四、类型错误 — 传了错误数据格式
# ────────────────────────────────────────────────

class Test参数类型错误:

    @pytest.mark.negative
    def test_产品名传空字符串(self, auth_client):
        body = make_body("", 1, 320, 50, 1, 100, 3)
        resp = auth_client.post(PATH, json=body)
        assert resp.json()["code"] == -1

    @pytest.mark.negative
    def test_尺寸传非数字(self, auth_client):
        """width/height 应传数字，传字符串应被拒绝。"""
        resp = auth_client.post(PATH, json=make_body("测试", 1, "三百", 50, 1, 100, 3))
        assert resp.json()["code"] == -1


# ────────────────────────────────────────────────
# 五、越权
# ────────────────────────────────────────────────

class Test越权:

    @pytest.mark.negative
    def test_无认证访问返回401(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        resp = s.post(BASE_URL + PATH, json=make_body("测试", 1, 320, 50, 1, 100, 3), timeout=10)
        assert resp.status_code == 401

    @pytest.mark.negative
    def test_低权限用户访问(self):
        low_user = os.getenv("LOW_PERM_USERNAME", "")
        low_pass = os.getenv("LOW_PERM_PASSWORD", "")
        if not low_user or not low_pass:
            pytest.skip("未配置低权限账号")
        from tests.conftest import do_login
        try:
            sess = do_login(low_user, low_pass)
        except RuntimeError:
            pytest.skip("低权限账号登录失败")
        resp = sess.post(BASE_URL + PATH, json=make_body("测试", 1, 320, 50, 1, 100, 3), timeout=10)
        assert resp.status_code in (401, 403), f"低权限应被拒绝，实际 HTTP {resp.status_code}"
