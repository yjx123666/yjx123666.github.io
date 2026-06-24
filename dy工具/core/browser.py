"""
Playwright 浏览器生命周期管理 + Cookie 持久化
"""
import json
import os
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright

import config


class BrowserManager:
    """管理 Playwright 浏览器实例"""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def launch(self, headless: bool = False) -> BrowserContext:
        """启动浏览器并返回上下文"""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            channel="msedge",
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--start-maximized",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-popup-blocking",
                "--disable-notifications",
            ],
        )
        self._context = self._browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            user_agent=config.USER_AGENT,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        # 注入反检测脚本（更全面）
        self._context.add_init_script("""
            // 隐藏 webdriver 标志
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            delete navigator.__proto__.webdriver;

            // 伪造 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                    ];
                    plugins.length = 3;
                    return plugins;
                },
            });

            // 伪造 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            });

            // 伪造 chrome 对象
            window.chrome = {
                runtime: {
                    onConnect: { addListener: function() {} },
                    onMessage: { addListener: function() {} },
                },
                loadTimes: function() { return {}; },
                csi: function() { return {}; },
            };

            // 隐藏自动化相关属性
            Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 1 });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

            // 修改 permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );
        """)
        return self._context

    def new_page(self) -> Page:
        """创建新页面"""
        if not self._context:
            raise RuntimeError("浏览器未启动，请先调用 launch()")
        self._page = self._context.new_page()
        return self._page

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context

    def close(self):
        """关闭所有资源"""
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    @staticmethod
    def save_cookies(context: BrowserContext):
        """保存 Cookie 到文件"""
        cookies = context.cookies()
        with open(config.COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_cookies(context: BrowserContext) -> bool:
        """从文件加载 Cookie，返回是否成功"""
        if not os.path.exists(config.COOKIE_FILE):
            return False
        try:
            with open(config.COOKIE_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            if not cookies:
                return False
            # 过滤 Playwright 不接受的字段，保留更多字段
            valid_keys = {"name", "value", "domain", "path", "secure", "httpOnly", "sameSite", "expires"}
            clean_cookies = []
            for c in cookies:
                clean = {k: v for k, v in c.items() if k in valid_keys}
                # sameSite 必须是 "Strict"/"Lax"/"None" 之一
                ss = clean.get("sameSite")
                if ss not in ("Strict", "Lax", "None"):
                    clean["sameSite"] = "Lax"
                # 确保 domain 存在
                if "domain" not in clean:
                    continue
                clean_cookies.append(clean)
            if clean_cookies:
                context.add_cookies(clean_cookies)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def clear_cookies():
        """清除本地 Cookie 文件"""
        if os.path.exists(config.COOKIE_FILE):
            os.remove(config.COOKIE_FILE)
