# -*- coding: utf-8 -*-
"""
基本信息管理 · 浏览器 E2E（少量主路径）

前置：
  - LOGIN_USERNAME / LOGIN_PASSWORD（与 API 登录相同，Cookie 注入 Playwright）
  - PLAYWRIGHT_BASE_URL：前端 SPA 根地址（须能打开 Vue 页面；仅 API 的 BASE_URL 不够）
    例：与登录同域的 https://adm.xxx.com 或本地 npm run dev 的 http://localhost:5173
  - Cookie 域名须与 PLAYWRIGHT_BASE_URL 一致

运行：
  pytest tests/integration/basic_info/test_basic_info_management_e2e.py -v -m e2e
"""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import expect

from pages.basic_info_management_page import BasicInfoManagementPage


@pytest.mark.smoke
@pytest.mark.e2e
def test_TC001_P0_进入账户管理页展示标题(playwright_page):
    """TC001：有权限用户可进入账户管理并看到页面标题区域。"""
    pm = BasicInfoManagementPage(playwright_page)
    pm.open_product_management()
    pm.wait_account_hero_visible(timeout_ms=30000)
    expect(
        playwright_page.locator("h2.hero-title").filter(has_text="账户管理")
    ).to_be_visible()


@pytest.mark.smoke
@pytest.mark.e2e
def test_TC019_P0_产品管理Tab可切换(playwright_page):
    pm = BasicInfoManagementPage(playwright_page)
    pm.open_product_management()
    pm.switch_tab_product()
    playwright_page.get_by_role("button", name="添加产品").wait_for(
        state="visible", timeout=30000
    )
    expect(playwright_page.get_by_role("button", name="添加产品")).to_be_visible()


@pytest.mark.smoke
@pytest.mark.e2e
def test_TC031_P0_关系管理Tab可切换(playwright_page):
    pm = BasicInfoManagementPage(playwright_page)
    pm.open_product_management()
    pm.switch_tab_relation()
    tab = playwright_page.get_by_role("tab", name="账户-产品关系")
    tab.wait_for(state="visible", timeout=30000)
    expect(tab).to_have_attribute("aria-selected", "true")


@pytest.mark.e2e
def test_TC014_TC022_placeholder_跳转预填需完整浏览器流水(playwright_page):
    pytest.skip(
        "TC014/TC022：依赖添加账户成功后的二次确认弹窗与路由跳转，需在稳定测试账号与录制环境下扩展"
    )


@pytest.mark.e2e
def test_TC053_添加产品弹窗不含负责人(playwright_page):
    pytest.skip(
        "TC053：当前前端 ProductDialog.vue 仍包含运营负责人等字段；与测试点对齐后改为断言对话框内不存在对应 label"
    )


@pytest.mark.e2e
def test_TC212_TC213_编辑账户禁用字段需新路由E2E_blocked(playwright_page):
    pytest.skip(
        "TC212/TC213：编辑态账户ID/代理标识置灰需打开 AccountDialog 编辑模式；"
        "当前 E2E 路由为 productManagement，新实现在 productManagementNew/account。"
        "API 契约见 tests/api/basic_info/test_basic_info_accounts.py::TestOrgEditImmutableFieldsApi"
    )


def _e2e_skip_unless_playwright_base_url() -> None:
    """E2E 须单独配置前端 SPA 地址，避免误用仅提供 API 的 BASE_URL。"""
    if not os.getenv("PLAYWRIGHT_BASE_URL", "").strip():
        pytest.skip(
            "未配置 PLAYWRIGHT_BASE_URL（前端 SPA 根地址，如 https://前端域名 或 http://localhost:5173），"
            "跳过 UI E2E；API 层见 test_TC110_筛选无匹配时列表为空态"
        )


@pytest.mark.regression
@pytest.mark.e2e
def test_TC110_P1_账户列表筛选无结果展示空状态(playwright_page):
    """
    TC110（UI）：筛选不存在的广告系列组 ID 后，表格展示空状态且无分页。

    与 API 用例 test_TC110_筛选无匹配时列表为空态 对齐（ghost org_id）。
    共享环境无法清空整库，故用「筛选无匹配」等价验证 el-empty，而非整库为空。
    """
    _e2e_skip_unless_playwright_base_url()
    ghost_org_id = os.getenv("TC110_GHOST_ORG_ID", "99999999991")
    pm = BasicInfoManagementPage(playwright_page)
    pm.open_product_management()
    pm.wait_account_hero_visible(timeout_ms=30000)

    pm.search_account_by_org_id(ghost_org_id, timeout_ms=30000)
    pm.expect_account_table_empty_state(timeout_ms=15000)

    # 页面无报错 Toast（Element Plus 错误类）
    err = playwright_page.locator(".el-message--error")
    expect(err).to_have_count(0)
