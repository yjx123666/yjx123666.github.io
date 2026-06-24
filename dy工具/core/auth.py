"""
登录流程管理：Cookie 复用 + 扫码登录
"""
import time
from typing import Callable, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

import config
from core.browser import BrowserManager


def load_and_check_login(page: Page) -> bool:
    """
    加载 Cookie 并检查登录状态。
    返回 True 表示 Cookie 有效且已登录。
    """
    loaded = BrowserManager.load_cookies(page.context)
    if not loaded:
        return False

    try:
        page.goto(config.DOUYIN_DOMAIN, wait_until="domcontentloaded", timeout=config.PAGE_LOAD_TIMEOUT)
        page.wait_for_timeout(3000)
    except Exception:
        pass

    return _check_logged_in(page)


def _check_logged_in(page: Page) -> bool:
    """
    检测页面是否有登录态。
    只通过页面 UI 元素判断，不用 Cookie 名字判断（容易误判）。
    """
    try:
        # 检查是否有「登录」按钮（有则说明未登录）
        login_btn_selectors = [
            'text=登录',
            'button:has-text("登录")',
            '[data-e2e="login-button"]',
        ]
        for selector in login_btn_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=1500):
                    return False  # 看到登录按钮 = 未登录
            except Exception:
                continue

        # 检查是否有用户头像（有则说明已登录）
        avatar_selectors = [
            '[data-e2e="user-info"]',
            'img[src*="avatar"]',
            '[class*="avatar"][class*="user"]',
        ]
        for selector in avatar_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=1500):
                    return True  # 看到用户头像 = 已登录
            except Exception:
                continue

        # 不确定 → 默认未登录
        return False
    except Exception:
        return False


def do_login(page: Page, log_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    执行登录流程。
    打开抖音首页，等待用户扫码登录，成功后保存 Cookie。
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    try:
        log("正在打开抖音登录页面...")
        try:
            page.goto(config.DOUYIN_DOMAIN, wait_until="domcontentloaded", timeout=config.PAGE_LOAD_TIMEOUT)
            page.wait_for_timeout(2000)
        except PlaywrightTimeout:
            log("页面加载超时，继续尝试...")

        log("请在弹出的浏览器窗口中扫码登录")
        log("等待登录成功...")

        # 轮询检测登录成功
        max_wait = 180
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # 检查登录按钮是否消失
                login_btn_visible = False
                for sel in ['text=登录', 'button:has-text("登录")']:
                    try:
                        if page.locator(sel).first.is_visible(timeout=500):
                            login_btn_visible = True
                            break
                    except Exception:
                        continue

                # 检查是否出现用户头像
                avatar_visible = False
                for sel in ['[data-e2e="user-info"]', 'img[src*="avatar"]']:
                    try:
                        if page.locator(sel).first.is_visible(timeout=500):
                            avatar_visible = True
                            break
                    except Exception:
                        continue

                if avatar_visible or not login_btn_visible:
                    # 再确认一次
                    page.wait_for_timeout(1000)
                    if avatar_visible:
                        log("检测到用户头像，登录成功！")
                        BrowserManager.save_cookies(page.context)
                        log("Cookie 已保存")
                        return True

            except Exception:
                pass

            time.sleep(2)

        log("登录等待超时（3分钟）")
        return False

    except PlaywrightTimeout:
        log("页面加载超时，请检查网络连接")
        return False
    except Exception as e:
        log(f"登录过程出错: {e}")
        return False
