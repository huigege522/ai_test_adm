"""竞品分析-探索页面对象。"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class CompetitorExplorePage(BasePage):
    """竞品分析-探索页面 Page Object。"""

    # 页面 URL
    URL = "/competitor/explore"

    # 页面元素定位器（需要根据实际页面调整）
    TYPE_SELECTOR = "#type-selector"  # 词找应用/应用找词
    TYPE_OPTION_1 = "#type-option-1"  # 词找应用选项
    TYPE_OPTION_2 = "#type-option-2"  # 应用找词选项
    VALUE_INPUT = "#value-input"  # 关键词或 APP ID 输入框
    COUNTRY_SELECTOR = "#country-selector"  # 国家选择
    COUNTRY_OPTION = "#country-option-{}"  # 国家选项（需要格式化）
    EXPLORE_BUTTON = "#explore-button"  # 探索按钮
    SYNC_STATUS = "#sync-status"  # 同步状态（preview/running/completed/failed）
    PROGRESS_BAR = "#progress-bar"  # 进度条
    ERROR_MESSAGE = ".error-message"  # 错误信息

    def select_type(self, type_value: int) -> None:
        """选择探索类型。

        Args:
            type_value: 1=词找应用，2=应用找词
        """
        self.click(self.TYPE_SELECTOR)
        if type_value == 1:
            self.click(self.TYPE_OPTION_1)
        else:
            self.click(self.TYPE_OPTION_2)

    def enter_value(self, value: str) -> None:
        """输入关键词或 APP ID。

        Args:
            value: 关键词或 APP ID
        """
        self.fill(self.VALUE_INPUT, value)

    def select_country(self, country: str) -> None:
        """选择国家。

        Args:
            country: 国家代码（如 "US", "CN"）
        """
        self.click(self.COUNTRY_SELECTOR)
        self.click(self.COUNTRY_OPTION.format(country))

    def click_explore(self) -> None:
        """点击探索按钮。"""
        self.click(self.EXPLORE_BUTTON)

    def wait_for_explore_complete(self, timeout: int = 300000) -> None:
        """等待探索完成（轮询 sync_status 直到 completed）。

        Args:
            timeout: 超时时间（毫秒），默认 5 分钟
        """
        # 方法 1：等待页面元素显示"completed"状态
        self.page.wait_for_selector(
            f"{self.SYNC_STATUS}:has-text('completed')",
            timeout=timeout
        )

        # 方法 2：通过 API 轮询（更可靠）
        # 可以在测试中调用 API 检查 sync_status

    def get_sync_status(self) -> str:
        """获取当前同步状态。

        Returns:
            同步状态字符串（preview/running/completed/failed）
        """
        return self.get_text(self.SYNC_STATUS)

    def is_error_displayed(self) -> bool:
        """判断是否显示错误信息。

        Returns:
            是否显示错误信息
        """
        return self.is_visible(self.ERROR_MESSAGE)

    def navigate_to_explore(self, base_url: str = "") -> None:
        """导航到探索页面。

        Args:
            base_url: 基础 URL（如 "https://adm.gm825.net"）
        """
        url = base_url.rstrip("/") + self.URL
        self.navigate_to(url)
        self.wait_for_load_state()
