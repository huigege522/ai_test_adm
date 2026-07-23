"""竞品分析-列表页面对象。"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class CompetitorListPage(BasePage):
    """竞品分析-列表页面 Page Object。"""

    # 页面 URL
    URL = "/competitor/list"

    # 页面元素定位器（需要根据实际页面调整）
    KEYWORD_LIST = "#keyword-list"  # 关键词列表容器
    LIST_ITEM = ".list-item"  # 列表项
    PAGINATION = ".pagination"  # 分页控件
    PAGE_BUTTON = ".page-button"  # 页码按钮
    PREV_BUTTON = ".prev-button"  # 上一页按钮
    NEXT_BUTTON = ".next-button"  # 下一页按钮
    EXPORT_BUTTON = "#export-button"  # 导出按钮
    FILTER_INPUT = "#filter-input"  # 筛选输入框
    SORT_BUTTON = ".sort-button"  # 排序按钮
    LOADING_SPINNER = ".loading"  # 加载动画
    ERROR_MESSAGE = ".error-message"  # 错误信息
    SUCCESS_MESSAGE = ".success-message"  # 成功信息

    def navigate_to_list(self, base_url: str = "") -> None:
        """导航到列表页面。

        Args:
            base_url: 基础 URL（如 "https://adm.gm825.net"）
        """
        url = base_url.rstrip("/") + self.URL
        self.navigate_to(url)
        self.wait_for_load_state()

    def is_list_loaded(self) -> bool:
        """判断列表是否加载成功。

        Returns:
            列表是否加载成功
        """
        # 方法 1：判断列表容器是否可见
        if self.is_visible(self.KEYWORD_LIST):
            return True
        
        # 方法 2：判断加载动画是否消失
        return not self.is_visible(self.LOADING_SPINNER)

    def get_current_page(self) -> int:
        """获取当前页码。

        Returns:
            当前页码
        """
        # 示例：获取当前激活的页码按钮文本
        return int(self.get_text(f"{self.PAGE_BUTTON}.active"))

    def go_to_next_page(self) -> None:
        """点击下一页按钮。"""
        self.click(self.NEXT_BUTTON)
        self.wait_for_load_state()

    def go_to_prev_page(self) -> None:
        """点击上一页按钮。"""
        self.click(self.PREV_BUTTON)
        self.wait_for_load_state()

    def go_to_page(self, page_num: int) -> None:
        """跳转到指定页码。

        Args:
            page_num: 目标页码
        """
        self.click(f"{self.PAGE_BUTTON}:has-text('{page_num}')")
        self.wait_for_load_state()

    def filter_by_keyword(self, keyword: str) -> None:
        """按关键词筛选。

        Args:
            keyword: 筛选关键词
        """
        self.fill(self.FILTER_INPUT, keyword)
        self.page.press(self.FILTER_INPUT, "Enter")
        self.wait_for_load_state()

    def sort_by(self, sort_field: str) -> None:
        """按字段排序。

        Args:
            sort_field: 排序字段（如 "relevance"、"volume"）
        """
        self.click(f"{self.SORT_BUTTON}[data-sort='{sort_field}']")
        self.wait_for_load_state()

    def click_export(self) -> None:
        """点击导出按钮。"""
        self.click(self.EXPORT_BUTTON)
        self.wait_for_load_state()

    def is_export_success(self) -> bool:
        """判断是否导出成功。

        Returns:
            是否导出成功
        """
        # 方法 1：判断成功信息是否可见
        if self.is_visible(self.SUCCESS_MESSAGE):
            return True
        
        # 方法 2：判断是否有下载对话框
        return self.page.is_download_triggered()

    def get_list_count(self) -> int:
        """获取列表总数。

        Returns:
            列表总数
        """
        # 示例：获取列表项数量
        return len(self.page.query_selector_all(self.LIST_ITEM))

    def is_error_displayed(self) -> bool:
        """判断是否显示错误信息。

        Returns:
            是否显示错误信息
        """
        return self.is_visible(self.ERROR_MESSAGE)
