"""页面对象基类，封装公共方法。"""
from playwright.sync_api import Page, expect


class BasePage:
    """所有 Page Object 的基类。"""

    def __init__(self, page: Page):
        """初始化页面对象。

        Args:
            page: Playwright Page 对象
        """
        self.page = page
        self.expect = expect

    def navigate_to(self, url: str) -> None:
        """导航到指定 URL。

        Args:
            url: 目标 URL
        """
        self.page.goto(url)

    def wait_for_load_state(self, state: str = "networkidle", timeout: int = 30000) -> None:
        """等待页面加载状态。

        Args:
            state: 加载状态（"load"|"domcontentloaded"|"networkidle"|"commit"）
            timeout: 超时时间（毫秒），默认 30 秒
        """
        self.page.wait_for_load_state(state, timeout=timeout)

    def wait_for_element(self, selector: str, timeout: int = 10000) -> None:
        """等待元素可见。

        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒），默认 10 秒
        """
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    def click(self, selector: str) -> None:
        """点击元素。

        Args:
            selector: 元素选择器
        """
        self.page.click(selector)

    def fill(self, selector: str, text: str) -> None:
        """填充输入框。

        Args:
            selector: 元素选择器
            text: 要填充的文本
        """
        self.page.fill(selector, text)

    def get_text(self, selector: str) -> str:
        """获取元素文本。

        Args:
            selector: 元素选择器

        Returns:
            元素文本内容
        """
        return self.page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        """判断元素是否可见。

        Args:
            selector: 元素选择器

        Returns:
            元素是否可见
        """
        return self.page.is_visible(selector)

    def is_enabled(self, selector: str) -> bool:
        """判断元素是否可用。

        Args:
            selector: 元素选择器

        Returns:
            元素是否可用
        """
        return self.page.is_enabled(selector)

    def screenshot(self, path: str) -> None:
        """截图保存。

        Args:
            path: 截图保存路径
        """
        self.page.screenshot(path=path)

    def reload(self) -> None:
        """重新加载页面。"""
        self.page.reload()

    def wait_for_timeout(self, timeout: int) -> None:
        """强制等待指定时间（毫秒）。

        Args:
            timeout: 等待时间（毫秒）
        """
        self.page.wait_for_timeout(timeout)
