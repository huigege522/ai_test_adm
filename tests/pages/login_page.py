"""登录页面对象。"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页面 Page Object。"""

    # 页面元素定位器（需要根据实际页面调整）
    USERNAME_INPUT = "#username"  # 用户名输入框
    PASSWORD_INPUT = "#password"  # 密码输入框
    CAPTCHA_TICKET = "#captcha-ticket"  # 验证码 ticket（测试环境可能隐藏）
    CAPTCHA_RANDSTR = "#captcha-randstr"  # 验证码 randstr
    LOGIN_BUTTON = "#login-button"  # 登录按钮
    ERROR_MESSAGE = ".error-message"  # 错误信息显示

    def login(self, username: str, password: str) -> None:
        """执行登录操作。

        Args:
            username: 用户名
            password: 密码
        """
        # 输入用户名和密码
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)

        # 测试环境绕过验证码（使用 ticket: "1234", randstr: "1234"）
        # 方法 1：直接设置 localStorage（如果前端读取 localStorage）
        self.page.evaluate("window.localStorage.setItem('captcha_ticket', '1234')")
        self.page.evaluate("window.localStorage.setItem('captcha_randstr', '1234')")

        # 方法 2：如果页面有隐藏的 captcha 输入框，直接填充
        try:
            self.fill(self.CAPTCHA_TICKET, "1234")
            self.fill(self.CAPTCHA_RANDSTR, "1234")
        except Exception:
            pass  # 忽略，如果元素不存在

        # 点击登录按钮
        self.click(self.LOGIN_BUTTON)

        # 等待导航完成
        self.page.wait_for_load_state("networkidle")

    def get_error_message(self) -> str:
        """获取错误信息。

        Returns:
            错误信息文本
        """
        return self.get_text(self.ERROR_MESSAGE)

    def is_login_successful(self) -> bool:
        """判断登录是否成功。

        Returns:
            登录是否成功（通过 URL 判断）
        """
        # 简单判断：如果 URL 不再包含 "login"，则认为登录成功
        return "login" not in self.page.url()
