"""E2E 测试辅助函数。"""
import os
import time
from datetime import datetime

from playwright.sync_api import Page, BrowserContext


def take_screenshot(page: Page, test_name: str, output_dir: str = "reports/screenshots") -> str:
    """截图保存。

    Args:
        page: Playwright Page 对象
        test_name: 测试名称（用于文件名）
        output_dir: 截图保存目录

    Returns:
        截图文件路径
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)

    # 截图保存
    page.screenshot(path=filepath, full_page=True)

    return filepath


def start_video_recording(context: BrowserContext, output_dir: str = "reports/videos") -> None:
    """开始视频录制。

    Args:
        context: Playwright BrowserContext 对象
        output_dir: 视频保存目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 配置 video 录制（需要在创建 context 时配置）
    # context = browser.new_context(record_video_dir=output_dir)
    pass  # 实际配置在 fixture 中


def stop_video_recording(page: Page) -> None:
    """停止视频录制。

    Args:
        page: Playwright Page 对象
    """
    # Playwright 会在 context 关闭时自动保存视频
    pass


def attach_screenshot_to_allure(screenshot_path: str, name: str = "screenshot") -> None:
    """将截图附加到 Allure 报告。

    Args:
        screenshot_path: 截图文件路径
        name: 附件名称
    """
    try:
        import allure
        with open(screenshot_path, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.PNG)
    except ImportError:
        pass  # allure 未安装


def attach_video_to_allure(video_path: str, name: str = "video") -> None:
    """将视频附加到 Allure 报告。

    Args:
        video_path: 视频文件路径
        name: 附件名称
    """
    try:
        import allure
        with open(video_path, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.MP4)
    except ImportError:
        pass  # allure 未安装


def wait_for_api_response(page: Page, api_url: str, timeout: int = 30000) -> dict:
    """等待 API 响应并返回 JSON 数据。

    Args:
        page: Playwright Page 对象
        api_url: API URL（部分匹配）
        timeout: 超时时间（毫秒），默认 30 秒

    Returns:
        API 响应的 JSON 数据
    """
    response = page.wait_for_response(
        lambda response: api_url in response.url and response.status == 200,
        timeout=timeout
    )
    return response.json()


def wait_for_element_with_retry(
    page: Page,
    selector: str,
    max_retries: int = 3,
    retry_interval: int = 1000,
    timeout: int = 10000
) -> bool:
    """等待元素可见，失败重试。

    Args:
        page: Playwright Page 对象
        selector: 元素选择器
        max_retries: 最大重试次数
        retry_interval: 重试间隔（毫秒）
        timeout: 每次等待的超时时间（毫秒）

    Returns:
        元素是否可见
    """
    for i in range(max_retries):
        try:
            page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception:
            if i < max_retries - 1:
                time.sleep(retry_interval / 1000)  # 转换为秒
            else:
                return False
    return False


def check_cookie_validity(page: Page, cookie_name: str) -> bool:
    """检查 Cookie 是否有效。

    Args:
        page: Playwright Page 对象
        cookie_name: Cookie 名称

    Returns:
            Cookie 是否有效
    """
    cookies = page.context.cookies()
    for cookie in cookies:
        if cookie["name"] == cookie_name:
            # 检查是否过期
            if "expires" in cookie:
                expires = cookie["expires"]
                if expires > 0 and expires < time.time():
                    return False
            return True
    return False


def inject_cookie_from_env(page: Page, env_file: str = ".env") -> None:
    """从 .env 文件读取 Cookie 并注入到 Playwright context。

    Args:
        page: Playwright Page 对象
        env_file: .env 文件路径
    """
    # 读取 .env 文件
    cookie_value = ""
    try:
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("AUTH_COOKIE="):
                    cookie_value = line.split("=", 1)[1].strip()
                    break
    except FileNotFoundError:
        return

    # 注入 Cookie
    if cookie_value:
        page.context.add_cookies([{
            "name": "sessionid",  # 根据实际 Cookie 名调整
            "value": cookie_value,
            "domain": "adm.gm825.net",
            "path": "/",
        }])
