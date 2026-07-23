"""基本信息管理页 — Playwright Page Object（productManagementNew）。"""
from __future__ import annotations

import os
import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from pages.base_page import BasePage


def frontend_base_url() -> str:
    """
    前端 SPA 根地址（与 API 的 BASE_URL 区分）。
    优先 PLAYWRIGHT_BASE_URL，其次 E2E_BASIC_INFO_URL，最后 BASE_URL。
    """
    for key in ("PLAYWRIGHT_BASE_URL", "E2E_BASIC_INFO_URL", "BASE_URL"):
        raw = os.getenv(key, "").strip()
        if raw:
            return raw.rstrip("/")
    return "http://localhost:8080"


class BasicInfoManagementPage(BasePage):
    """路由：`/managementCenter/productManagement` → productManagementNew/index.vue。"""

    PATH = "/managementCenter/productManagement"
    TAB_ACCOUNT = "账户管理"
    TAB_PRODUCT = "产品管理"
    TAB_RELATION = "账户-产品关系"

    def __init__(self, page: Page):
        super().__init__(page)

    def open_product_management(self, *, timeout_ms: int = 30000) -> None:
        base = frontend_base_url()
        self.navigate_to(base + self.PATH)
        self.wait_for_load_state("domcontentloaded")
        # 等待 Tab 容器出现（字典接口较慢时 networkidle 易超时）
        self.page.get_by_role("tab", name=self.TAB_ACCOUNT).wait_for(
            state="visible", timeout=timeout_ms
        )

    def switch_tab_account(self) -> None:
        self.page.get_by_role("tab", name=self.TAB_ACCOUNT).click()

    def switch_tab_product(self) -> None:
        self.page.get_by_role("tab", name=self.TAB_PRODUCT).click()

    def switch_tab_relation(self) -> None:
        self.page.get_by_role("tab", name=self.TAB_RELATION).click()

    def wait_account_hero_visible(self, *, timeout_ms: int = 30000) -> None:
        """
        账户 Tab 已渲染：优先 `.account-page`，其次 h2.hero-title。
        index.vue 默认 activeName=account，一般无需先点 Tab。
        """
        self.switch_tab_account()
        root = self.account_root()
        try:
            root.wait_for(state="visible", timeout=timeout_ms)
        except PlaywrightTimeoutError as exc:
            hint = (
                f"未加载账户管理页（.account-page）。请配置 PLAYWRIGHT_BASE_URL 为前端 SPA 根地址（非仅 API 的 BASE_URL），"
                f"当前打开：{self.page.url}；登录 Cookie 域名需与前端一致。"
            )
            raise AssertionError(hint) from exc
        hero = self.page.locator("h2.hero-title").filter(
            has_text=re.compile(r"账户管理|Account", re.I)
        )
        if hero.count() > 0:
            hero.first.wait_for(state="visible", timeout=5000)

    def click_add_account(self) -> None:
        self.page.get_by_role("button", name="添加账户").click()

    def click_add_product(self) -> None:
        self.page.get_by_role("button", name="添加产品").click()

    def account_hero_visible(self) -> bool:
        return self.page.locator("h2.hero-title").filter(has_text=self.TAB_ACCOUNT).is_visible()

    def account_root(self):
        """账户 Tab 根容器（account/index.vue `.account-page`）。"""
        return self.page.locator(".account-page")

    def fill_account_org_id_filter(self, org_id: str) -> None:
        """筛选区：广告系列组 ID（key=org_id）。"""
        item = self.account_root().locator(".el-form-item").filter(has_text="广告系列组ID")
        item.locator("input").first.fill(org_id)

    def click_account_search(self) -> None:
        """FormParcel 主搜索按钮（icon + common.search，优先 CSS 避免 role 名不可见）。"""
        root = self.account_root()
        btn = root.locator(".form-search .search-btn button.el-button--primary").first
        if btn.count() == 0:
            btn = root.get_by_role("button", name=re.compile(r"搜索|查询|Search", re.I)).first
        btn.click()

    def search_account_by_org_id(self, org_id: str, *, timeout_ms: int = 30000) -> None:
        """填写 org_id 并触发搜索，等待 /api/org/list 返回。"""
        with self.page.expect_response(
            lambda r: "/api/org/list" in r.url and r.request.method == "POST",
            timeout=timeout_ms,
        ):
            self.fill_account_org_id_filter(org_id)
            # FormParcel input 有 debounce 自动 submit；再点一次搜索确保触发
            self.click_account_search()

    def expect_account_table_empty_state(self, *, timeout_ms: int = 15000) -> None:
        """
        TC110/TC111：表格无数据时的 el-empty 与 total=0 表现。
        文案：product.noAccountData → 简体中文「暂无账户数据」。
        """
        root = self.account_root()
        empty = root.locator(".el-empty")
        expect(empty).to_be_visible(timeout=timeout_ms)
        expect(empty).to_contain_text(re.compile(r"暂无账户数据|No account data", re.I))
        expect(root.locator(".el-table__body tbody tr")).to_have_count(0, timeout=timeout_ms)
        expect(root.locator(".pagination-bar")).to_have_count(0, timeout=timeout_ms)
        stat = root.locator(".stat-num")
        if stat.count() > 0:
            expect(stat).to_have_text(re.compile(r"^0$"), timeout=timeout_ms)
