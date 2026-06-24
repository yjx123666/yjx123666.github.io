"""
QThread 工作线程
流程：启动浏览器 → 加载Cookie → 检查登录 → (需要则等待登录) → 抓取评论
"""
import threading
import traceback

from PyQt5.QtCore import QThread, pyqtSignal


class ScrapeWorker(QThread):
    """评论抓取工作线程"""

    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    login_ready = pyqtSignal()
    login_done = pyqtSignal()

    def __init__(self, video_url: str, target_count: int, cookies_exist: bool, parent=None):
        super().__init__(parent)
        self.video_url = video_url
        self.target_count = target_count
        self.cookies_exist = cookies_exist
        self._is_running = True
        self._login_confirmed = threading.Event()

    def confirm_login(self):
        """主线程调用：用户点击了「确认登录」按钮"""
        self._login_confirmed.set()

    def run(self):
        try:
            from core.browser import BrowserManager
            from core.auth import load_and_check_login, do_login
            from core.comment_scraper import scrape_comments, save_debug_info

            self.log_message.emit("正在启动浏览器...")
            bm = BrowserManager()
            context = bm.launch(headless=False)
            page = bm.new_page()

            try:
                logged_in = False

                # ===== 阶段一：加载 Cookie 并检查登录 =====
                if self.cookies_exist:
                    self.log_message.emit("检测到已保存的 Cookie，正在加载...")
                    if load_and_check_login(page):
                        self.log_message.emit("Cookie 有效，已登录")
                        logged_in = True
                        self.login_done.emit()
                    else:
                        self.log_message.emit("Cookie 已失效，需要重新登录")

                # ===== 阶段二：需要登录 =====
                if not logged_in:
                    self.log_message.emit("请在弹出的浏览器窗口中扫码登录抖音")
                    self.log_message.emit("登录完成后，请点击「确认登录」按钮")
                    self.login_ready.emit()

                    # 打开抖音首页
                    try:
                        page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=30000)
                    except Exception:
                        pass

                    # 等待用户点击「确认登录」（最长5分钟）
                    if not self._login_confirmed.wait(timeout=300):
                        self.error.emit("登录等待超时（5分钟），请重试")
                        return

                    if not self._is_running:
                        return

                    # 保存 Cookie
                    self.log_message.emit("正在保存 Cookie...")
                    bm.save_cookies(context)
                    self.log_message.emit("登录成功，Cookie 已保存")
                    self.login_done.emit()

                if not self._is_running:
                    return

                # ===== 阶段三：抓取评论 =====
                self.log_message.emit("=" * 40)
                self.log_message.emit("开始抓取评论...")
                self.log_message.emit(f"目标数量: {self.target_count}")

                comments = scrape_comments(
                    page=page,
                    video_url=self.video_url,
                    target_count=self.target_count,
                    log_callback=lambda msg: self.log_message.emit(msg),
                    progress_callback=lambda cur, tot: self.progress_update.emit(cur, tot),
                )

                if not comments:
                    self.log_message.emit("未获取到评论，正在保存调试信息...")
                    save_debug_info(page, "no_comments")

                self.finished.emit(comments)

            except Exception as e:
                self.log_message.emit(f"抓取出错: {e}")
                try:
                    save_debug_info(page, "error")
                    self.log_message.emit("调试信息已保存到 data/debug/ 目录")
                except Exception:
                    pass
                self.error.emit(f"抓取失败: {str(e)}\n{traceback.format_exc()}")
            finally:
                bm.close()

        except Exception as e:
            self.error.emit(f"初始化失败: {str(e)}\n{traceback.format_exc()}")

    def stop(self):
        self._is_running = False
        self._login_confirmed.set()
