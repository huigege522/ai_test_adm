"""
端到端测试：竞品分析完整流程（UI 级）。

业务流程：
  1. 词找应用（type=1）→ 输入关键词 → 选择国家 → 点击探索
  2. 等待探索完成（轮询 sync_status 直到 completed）
  3. 查看图表（chart）→ 验证搜索分布图、预估安装量分布图
  4. 查看列表（list）→ 验证关键词列表、分页、筛选
  5. 导出数据（export）→ 验证导出成功

认证方式：复用 login_session 的 Cookie，注入 Playwright context。
注意：页面元素定位器是占位符，需要根据实际页面调整。
"""
import pytest
from playwright.sync_api import Page, expect

from pages.competitor_explore_page import CompetitorExplorePage
from pages.competitor_chart_page import CompetitorChartPage
from pages.competitor_list_page import CompetitorListPage


class TestCompetitorE2EFlow:
    """
    竞品分析 E2E 完整流程测试。
    覆盖：词找应用 → 等待完成 → 查看图表 → 查看列表 → 导出数据
    """

    @pytest.mark.smoke
    @pytest.mark.e2e
    def test_词找应用完整流程(self, competitor_explore_page: CompetitorExplorePage):
        """测试词找应用完整流程（type=1）。"""
        # Step1：选择类型（词找应用）
        competitor_explore_page.select_type(1)
        
        # Step2：输入关键词
        competitor_explore_page.enter_value("game")
        
        # Step3：选择国家
        competitor_explore_page.select_country("US")
        
        # Step4：点击探索按钮
        competitor_explore_page.click_explore()
        
        # Step5：等待探索完成（最多 5 分钟）
        competitor_explore_page.wait_for_explore_complete(timeout=300000)
        
        # Step6：验证同步状态为 completed
        status = competitor_explore_page.get_sync_status()
        assert status == "completed", f"期望 sync_status=completed，实际：{status}"

    @pytest.mark.smoke
    @pytest.mark.e2e
    def test_应用找词完整流程(self, competitor_explore_page: CompetitorExplorePage):
        """测试应用找词完整流程（type=2）。"""
        # Step1：选择类型（应用找词）
        competitor_explore_page.select_type(2)
        
        # Step2：输入 APP ID
        competitor_explore_page.enter_value("389801252")  # 示例 APP ID
        
        # Step3：选择国家
        competitor_explore_page.select_country("US")
        
        # Step4：点击探索按钮
        competitor_explore_page.click_explore()
        
        # Step5：等待探索完成（最多 5 分钟）
        competitor_explore_page.wait_for_explore_complete(timeout=300000)
        
        # Step6：验证同步状态为 completed
        status = competitor_explore_page.get_sync_status()
        assert status == "completed", f"期望 sync_status=completed，实际：{status}"

    @pytest.mark.regression
    @pytest.mark.e2e
    def test_查看图表(self, playwright_page: Page, competitor_explore_page: CompetitorExplorePage):
        """测试查看图表（chart）。"""
        # 先完成探索
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        competitor_explore_page.wait_for_explore_complete()
        
        # 导航到图表页面
        chart_page = CompetitorChartPage(playwright_page)
        chart_page.navigate_to_chart()
        
        # 验证图表加载成功
        assert chart_page.is_chart_loaded(), "图表加载失败"

    @pytest.mark.regression
    @pytest.mark.e2e
    def test_查看列表(self, playwright_page: Page, competitor_explore_page: CompetitorExplorePage):
        """测试查看列表（list）。"""
        # 先完成探索
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        competitor_explore_page.wait_for_explore_complete()
        
        # 导航到列表页面
        list_page = CompetitorListPage(playwright_page)
        list_page.navigate_to_list()
        
        # 验证列表加载成功
        assert list_page.is_list_loaded(), "列表加载失败"
        
        # 验证列表项数 > 0
        count = list_page.get_list_count()
        assert count > 0, f"列表项数应为 > 0，实际：{count}"

    @pytest.mark.regression
    @pytest.mark.e2e
    def test_列表分页(self, playwright_page: Page, competitor_explore_page: CompetitorExplorePage):
        """测试列表分页功能。"""
        # 先完成探索
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        competitor_explore_page.wait_for_explore_complete()
        
        # 导航到列表页面
        list_page = CompetitorListPage(playwright_page)
        list_page.navigate_to_list()
        
        # 测试下一页
        list_page.go_to_next_page()
        current_page = list_page.get_current_page()
        assert current_page == 2, f"期望当前页=2，实际：{current_page}"

    @pytest.mark.regression
    @pytest.mark.e2e
    def test_导出数据(self, playwright_page: Page, competitor_explore_page: CompetitorExplorePage):
        """测试导出数据功能。"""
        # 先完成探索
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        competitor_explore_page.wait_for_explore_complete()
        
        # 导航到列表页面
        list_page = CompetitorListPage(playwright_page)
        list_page.navigate_to_list()
        
        # 点击导出按钮
        list_page.click_export()
        
        # 验证导出成功
        assert list_page.is_export_success(), "导出失败"


class TestCompetitorE2ENegative:
    """竞品分析 E2E 异常场景测试。"""

    @pytest.mark.negative
    @pytest.mark.e2e
    def test_错误关键词_探索失败(self, competitor_explore_page: CompetitorExplorePage):
        """测试输入错误关键词，探索失败。"""
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("invalid_keyword_12345")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        
        # 验证显示错误提示
        assert competitor_explore_page.is_error_displayed(), "应显示错误提示"

    @pytest.mark.negative
    @pytest.mark.e2e
    def test_未选择国家_点击探索_显示错误(self, competitor_explore_page: CompetitorExplorePage):
        """测试未选择国家，点击探索显示错误。"""
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        # 不选择国家
        competitor_explore_page.click_explore()
        
        # 验证显示错误提示
        assert competitor_explore_page.is_error_displayed(), "应显示错误提示"

    @pytest.mark.negative
    @pytest.mark.e2e
    def test_未选择类型_点击探索_显示错误(self, competitor_explore_page: CompetitorExplorePage):
        """测试未选择类型，点击探索显示错误。"""
        # 不选择类型
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        
        # 验证显示错误提示
        assert competitor_explore_page.is_error_displayed(), "应显示错误提示"

    @pytest.mark.negative
    @pytest.mark.e2e
    def test_探索配额耗尽(self, competitor_explore_page: CompetitorExplorePage):
        """测试探索配额耗尽时的处理。"""
        # 24h 内重复探索相同参数会命中缓存
        # 但配额耗尽时应该显示错误提示
        competitor_explore_page.select_type(1)
        competitor_explore_page.enter_value("game")
        competitor_explore_page.select_country("US")
        competitor_explore_page.click_explore()
        
        # 等待一段时间后检查是否显示配额耗尽提示
        competitor_explore_page.page.wait_for_timeout(5000)
        
        # 验证显示错误提示或配额耗尽提示
        assert (competitor_explore_page.is_error_displayed() or 
                "配额" in competitor_explore_page.page.content()), "应显示配额耗尽提示"
