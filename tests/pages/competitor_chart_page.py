"""竞品分析-图表页面对象。"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class CompetitorChartPage(BasePage):
    """竞品分析-图表页面 Page Object。"""

    # 页面 URL
    URL = "/competitor/chart"

    # 页面元素定位器（需要根据实际页面调整）
    SEARCH_CHART = "#search-chart"  # 搜索分布图
    ASA_CHART = "#asa-chart"  # 预估安装量分布图
    COVERAGE_CHART = "#coverage-chart"  # 覆盖分布图（type=2）
    BIDDING_CHART = "#bidding-chart"  # 竞价分布图（type=2）
    LOADING_SPINNER = ".loading"  # 加载动画
    ERROR_MESSAGE = ".error-message"  # 错误信息

    def navigate_to_chart(self, base_url: str = "") -> None:
        """导航到图表页面。

        Args:
            base_url: 基础 URL（如 "https://adm.gm825.net"）
        """
        url = base_url.rstrip("/") + self.URL
        self.navigate_to(url)
        self.wait_for_load_state()

    def is_chart_loaded(self) -> bool:
        """判断图表是否加载成功。

        Returns:
            图表是否加载成功
        """
        # 方法 1：判断图表容器是否可见
        if self.is_visible(self.SEARCH_CHART) or self.is_visible(self.ASA_CHART):
            return True
        
        # 方法 2：判断加载动画是否消失
        return not self.is_visible(self.LOADING_SPINNER)

    def get_chart_data(self, chart_name: str) -> dict:
        """获取图表数据（需要实际页面调整）。

        Args:
            chart_name: 图表名称（"search"|"asa"|"coverage"|"bidding"）

        Returns:
            图表数据字典
        """
        # 示例：通过 JavaScript 获取图表数据
        script = f"return window.chartData['{chart_name}'];"
        return self.page.evaluate(script)

    def is_error_displayed(self) -> bool:
        """判断是否显示错误信息。

        Returns:
            是否显示错误信息
        """
        return self.is_visible(self.ERROR_MESSAGE)
