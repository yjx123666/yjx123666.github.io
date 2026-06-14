# -*- coding: utf-8 -*-
"""
新媒体数据采集与分析工具
支持抖音/小红书分享链接批量提取数据，导出Excel，数据分析可视化
"""

import os
import re
import json
import time
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =========================================================================
# 数据提取引擎
# =========================================================================

class DouyinScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Edge(options=options)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
        )

    def _ensure_driver(self):
        if self.driver is None:
            self._init_driver()

    def _extract_url(self, text):
        """从分享文本中提取URL"""
        match = re.search(r'https?://[^\s]+', text)
        if match:
            return match.group().rstrip("/")
        return text.strip()

    def extract(self, url):
        self._ensure_driver()
        real_url = self._extract_url(url)
        try:
            real_url = self._resolve_url(real_url)
            data = self._extract_data(real_url)
            # 如果提取到的数据标题为空，保存调试信息
            if not data.get("title"):
                self._save_debug(real_url)
            return self._fill_defaults(data, url)
        except Exception as e:
            self._save_debug(real_url)
            return self._fill_defaults({"url": url, "error": str(e)}, url)

    def _save_debug(self, url):
        """保存截图和页面源码用于调试"""
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")
        if not os.path.isdir(debug_dir):
            os.makedirs(debug_dir)
        try:
            self.driver.save_screenshot(os.path.join(debug_dir, "screenshot.png"))
        except Exception:
            pass
        try:
            with open(os.path.join(debug_dir, "page_source.html"), "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except Exception:
            pass
        try:
            with open(os.path.join(debug_dir, "current_url.txt"), "w", encoding="utf-8") as f:
                f.write(self.driver.current_url)
        except Exception:
            pass

    def _fill_defaults(self, data, url):
        defaults = {"url": url, "platform": "douyin", "author": "", "title": "",
                    "likes": 0, "comments": 0, "collects": 0, "shares": 0, "views": 0}
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def _resolve_url(self, url):
        self.driver.get(url)
        time.sleep(2)
        return self.driver.current_url

    def _extract_data(self, url):
        time.sleep(4)
        result = {"url": url, "platform": "douyin"}

        # 方案1: 用JS从页面script标签中提取嵌入的JSON数据
        data = self._try_js_extract()
        if data and data.get("title"):
            return data

        # 方案2: 从RENDER_DATA提取
        data = self._try_render_data()
        if data and data.get("title"):
            return data

        # 方案3: DOM提取
        return self._extract_from_dom(url)

    def _try_js_extract(self):
        """用JS遍历所有script标签，查找包含视频数据的JSON"""
        try:
            js_code = """
            var scripts = document.querySelectorAll('script');
            for (var i = 0; i < scripts.length; i++) {
                var text = scripts[i].textContent;
                if (text && text.indexOf('awemeDetail') !== -1) {
                    var match = text.match(/"awemeDetail"\\s*:\\s*(\\{[^}]*"desc"[\\s\\S]*?\\})\\s*[,}]/);
                    if (match) return match[1];
                }
                if (text && text.indexOf('aweme_detail') !== -1) {
                    var match = text.match(/"aweme_detail"\\s*:\\s*(\\{[^}]*"desc"[\\s\\S]*?\\})\\s*[,}]/);
                    if (match) return match[1];
                }
            }
            return null;
            """
            raw = self.driver.execute_script(js_code)
            if raw:
                detail = json.loads(raw)
                return self._build_result_from_detail(detail)
        except Exception:
            pass

        # 尝试从页面全局变量获取
        try:
            js_code2 = """
            try {
                var data = null;
                if (window.__INITIAL_STATE__) data = window.__INITIAL_STATE__;
                if (window.__NEXT_DATA__) data = window.__NEXT_DATA__;
                if (window._SSR_DATA) data = window._SSR_DATA;
                if (!data) return null;
                var detail = null;
                function find(obj, depth) {
                    if (depth > 5 || !obj) return;
                    if (typeof obj !== 'object') return;
                    if (obj.awemeDetail) { detail = obj.awemeDetail; return; }
                    if (obj.aweme_detail) { detail = obj.aweme_detail; return; }
                    if (obj.desc && obj.statistics) { detail = obj; return; }
                    for (var k in obj) { find(obj[k], depth+1); }
                }
                find(data, 0);
                return detail ? JSON.stringify(detail) : null;
            } catch(e) { return null; }
            """
            raw2 = self.driver.execute_script(js_code2)
            if raw2:
                detail = json.loads(raw2)
                return self._build_result_from_detail(detail)
        except Exception:
            pass

        return None

    def _build_result_from_detail(self, detail):
        result = {"platform": "douyin"}
        try:
            result["title"] = detail.get("desc", "") or ""
            # 作者
            author_info = detail.get("author", {})
            if isinstance(author_info, dict):
                result["author"] = author_info.get("nickname", "") or author_info.get("nick_name", "")
            else:
                result["author"] = str(author_info)
            # 统计数据
            stats = detail.get("statistics", {}) or detail.get("stats", {})
            if isinstance(stats, dict):
                result["likes"] = self._safe_int(stats.get("digg_count") or stats.get("diggCount"))
                result["comments"] = self._safe_int(stats.get("comment_count") or stats.get("commentCount"))
                result["collects"] = self._safe_int(stats.get("collect_count") or stats.get("collectCount"))
                result["shares"] = self._safe_int(stats.get("share_count") or stats.get("shareCount"))
                result["views"] = self._safe_int(stats.get("play_count") or stats.get("playCount"))
            return result
        except Exception:
            return result

    def _try_render_data(self):
        try:
            import urllib.parse
            script = self.driver.execute_script(
                "var el = document.getElementById('RENDER_DATA'); "
                "return el ? el.textContent : null;"
            )
            if script:
                decoded = json.loads(urllib.parse.unquote(script))
                detail = self._deep_find(decoded, "awemeDetail") or self._deep_find(decoded, "aweme_detail")
                if detail:
                    return self._build_result_from_detail(detail)
        except Exception:
            pass
        return None

    def _extract_from_dom(self, url):
        """DOM方式提取 - 通过JS获取页面上所有可见文本并解析"""
        result = {"url": url, "platform": "douyin"}
        try:
            js_result = self.driver.execute_script("""
            var result = {};

            // ===== 标题 =====
            var titleEl = document.querySelector('[data-e2e="video-desc"] span')
                || document.querySelector('[data-e2e="video-desc"]')
                || document.querySelector('h1')
                || document.querySelector('.video-info-detail')
                || document.querySelector('[class*="title"][class*="video"]')
                || document.querySelector('[class*="desc"]');
            result.title = titleEl ? titleEl.textContent.trim().substring(0, 200) : document.title;

            // ===== 作者 =====
            var authorEl = document.querySelector('[data-e2e="user-info"]')
                || document.querySelector('[data-e2e="video-author-name"]')
                || document.querySelector('[class*="author"] [class*="name"]')
                || document.querySelector('[class*="nickname"]');
            if (authorEl) {
                var authorText = authorEl.textContent.trim();
                var match = authorText.match(/^(.+?)粉丝/);
                result.author = match ? match[1].trim() : authorText.substring(0, 20);
            } else {
                result.author = '';
            }

            // ===== 互动数据 - 多种策略 =====

            // 策略1: data-e2e 属性
            var e2e_map = {};
            document.querySelectorAll('[data-e2e]').forEach(function(el) {
                var key = el.getAttribute('data-e2e');
                var text = el.textContent.trim().substring(0, 30);
                if (text) e2e_map[key] = text;
            });
            result.e2e = e2e_map;

            // 策略2: aria-label 属性（抖音常用）
            var aria_map = {};
            document.querySelectorAll('[aria-label]').forEach(function(el) {
                var label = el.getAttribute('aria-label');
                var text = el.textContent.trim();
                if (label && text && text.length < 15) {
                    aria_map[label] = text;
                }
            });
            result.aria = aria_map;

            // 策略3: 查找 SVG 图标旁边的数字
            // 抖音右侧互动栏：每个图标 + 数字是一个组合
            var svgParents = document.querySelectorAll('svg');
            var svg_nums = [];
            svgParents.forEach(function(svg) {
                var parent = svg.closest('[class*="item"], [class*="action"], [class*="wrapper"], [class*="container"], li, button');
                if (parent) {
                    var numEl = parent.querySelector('span:not(:first-child)');
                    if (numEl) {
                        var t = numEl.textContent.trim();
                        if (/^[\\d.]+[万亿wW]?$/.test(t)) {
                            // 尝试通过 aria-label 或 class 判断类型
                            var label = parent.getAttribute('aria-label') || '';
                            var cls = (parent.className || '').substring(0, 80);
                            svg_nums.push({text: t, label: label, class: cls});
                        }
                    }
                }
            });
            result.svgNums = svg_nums.slice(0, 10);

            // 策略4: 查找所有数字 span（通用兜底）
            var allSpans = document.querySelectorAll('span');
            var allNums = [];
            allSpans.forEach(function(el) {
                var t = el.textContent.trim();
                if (/^[\\d.]+[万亿wW]?$/.test(t) && t.length < 10) {
                    var parent = el.parentElement;
                    var grandparent = parent ? parent.parentElement : null;
                    var cls = (parent ? parent.className : '').substring(0, 60);
                    var gpcls = (grandparent ? grandparent.className : '').substring(0, 60);
                    var aria = el.getAttribute('aria-label') || parent ? (parent.getAttribute('aria-label') || '') : '';
                    allNums.push({text: t, class: cls, gpClass: gpcls, aria: aria});
                }
            });
            result.allNums = allNums.slice(0, 30);

            return result;
            """)

            result["title"] = js_result.get("title", "")
            result["author"] = js_result.get("author", "")

            # ===== 从各种来源提取数据 =====
            e2e = js_result.get("e2e", {})
            aria = js_result.get("aria", {})
            svg_nums = js_result.get("svgNums", [])
            all_nums = js_result.get("allNums", [])

            # 来源1: data-e2e
            def _get_e2e_val(key):
                val = e2e.get(key)
                if isinstance(val, list):
                    return val[0] if val else None
                return val

            e2e_likes = _get_e2e_val("video-player-digg") or _get_e2e_val("like-icon")
            e2e_comments = _get_e2e_val("feed-comment-icon") or _get_e2e_val("comment-icon")
            e2e_collects = _get_e2e_val("video-player-collect") or _get_e2e_val("collect-icon")
            e2e_shares = _get_e2e_val("video-player-share") or _get_e2e_val("share-icon")

            if e2e_likes:
                result["likes"] = self._parse_number(e2e_likes)
            if e2e_comments:
                result["comments"] = self._parse_number(e2e_comments)
            if e2e_collects:
                result["collects"] = self._parse_number(e2e_collects)
            if e2e_shares:
                result["shares"] = self._parse_number(e2e_shares)

            # 来源2: aria-label（包含"点赞"、"评论"等关键词）
            if not result.get("likes"):
                for label, val in aria.items():
                    if "赞" in label or "like" in label.lower() or "digg" in label.lower():
                        result["likes"] = self._parse_number(val)
                    elif "评论" in label or "comment" in label.lower():
                        result["comments"] = self._parse_number(val)
                    elif "收藏" in label or "collect" in label.lower() or "save" in label.lower():
                        result["collects"] = self._parse_number(val)
                    elif "分享" in label or "share" in label.lower() or "转发" in label:
                        result["shares"] = self._parse_number(val)

            # 来源3: SVG 图标旁边的数字（按位置推断，通常是 点赞/评论/收藏/转发）
            if not result.get("likes") and len(svg_nums) >= 3:
                result["likes"] = self._parse_number(svg_nums[0]["text"])
                result["comments"] = self._parse_number(svg_nums[1]["text"])
                result["collects"] = self._parse_number(svg_nums[2]["text"])
                if len(svg_nums) >= 4:
                    result["shares"] = self._parse_number(svg_nums[3]["text"])

            # 来源4: 通用数字兜底（从 allNums 中按位置推断）
            if not result.get("likes"):
                # 过滤出互动栏的数字（通常在页面右侧，连续出现）
                nums_only = [n["text"] for n in all_nums if self._parse_number(n["text"]) > 0]
                if len(nums_only) >= 3:
                    result["likes"] = self._parse_number(nums_only[0])
                    result["comments"] = self._parse_number(nums_only[1])
                    result["collects"] = self._parse_number(nums_only[2])
                    if len(nums_only) >= 4:
                        result["shares"] = self._parse_number(nums_only[3])

        except Exception as e:
            result["error"] = str(e)
        return self._fill_defaults(result, url)

    def _deep_find(self, obj, key):
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                found = self._deep_find(v, key)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = self._deep_find(item, key)
                if found is not None:
                    return found
        return None

    def _parse_number(self, text):
        if not text:
            return 0
        text = text.strip().replace(",", "")
        multipliers = {"w": 10000, "W": 10000, "万": 10000, "亿": 100000000}
        for suffix, mul in multipliers.items():
            if text.endswith(suffix):
                try:
                    return int(float(text[:-1]) * mul)
                except ValueError:
                    return 0
        try:
            return int(float(text))
        except ValueError:
            return 0

    def _safe_int(self, val):
        if val is None:
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


# =========================================================================
# 小红书数据提取引擎
# =========================================================================

class XiaohongshuScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Edge(options=options)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
        )

    def _ensure_driver(self):
        if self.driver is None:
            self._init_driver()

    def _extract_url(self, text):
        match = re.search(r'https?://[^\s]+', text)
        if match:
            return match.group().rstrip("/")
        return text.strip()

    def extract(self, url):
        self._ensure_driver()
        real_url = self._extract_url(url)
        try:
            real_url = self._resolve_url(real_url)
            data = self._extract_data(real_url)
            return self._fill_defaults(data, url)
        except Exception as e:
            return self._fill_defaults({"url": url, "error": str(e)}, url)

    def _fill_defaults(self, data, url):
        defaults = {"url": url, "platform": "xiaohongshu", "author": "", "title": "",
                    "likes": 0, "comments": 0, "collects": 0, "shares": 0, "views": 0}
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def _resolve_url(self, url):
        self.driver.get(url)
        time.sleep(3)
        return self.driver.current_url

    def _extract_data(self, url):
        time.sleep(3)
        result = {"url": url, "platform": "xiaohongshu"}

        js_result = self.driver.execute_script("""
        var result = {};

        // 标题
        var titleEl = document.querySelector('#detail-desc')
            || document.querySelector('[class*="title"]')
            || document.querySelector('.note-text');
        result.title = titleEl ? titleEl.textContent.trim().substring(0, 200) : document.title;

        // 作者
        var authorEl = document.querySelector('.author-wrapper .username')
            || document.querySelector('[class*="author"] [class*="name"]')
            || document.querySelector('.user-name');
        result.author = authorEl ? authorEl.textContent.trim() : '';

        // 互动数据 - 小红书的点赞、评论、收藏、转发
        var result_nums = {};

        // 方式1: 通过 class 名查找
        var likeEl = document.querySelector('[class*="like"] [class*="count"], [class*="like-wrapper"] span')
            || document.querySelector('.like-wrapper .count');
        var commentEl = document.querySelector('[class*="chat"] [class*="count"], [class*="comment-wrapper"] span')
            || document.querySelector('.chat-wrapper .count');
        var collectEl = document.querySelector('[class*="collect"] [class*="count"], [class*="collect-wrapper"] span')
            || document.querySelector('.collect-wrapper .count');
        var shareEl = document.querySelector('[class*="share"] [class*="count"], [class*="share-wrapper"] span');

        if (likeEl) result_nums.likes = likeEl.textContent.trim();
        if (commentEl) result_nums.comments = commentEl.textContent.trim();
        if (collectEl) result_nums.collects = collectEl.textContent.trim();
        if (shareEl) result_nums.shares = shareEl.textContent.trim();

        // 方式2: 通过 data-e2e 属性
        var allE2e = document.querySelectorAll('[data-e2e]');
        var e2e = {};
        for (var i = 0; i < allE2e.length; i++) {
            var key = allE2e[i].getAttribute('data-e2e');
            var text = allE2e[i].textContent.trim().substring(0, 50);
            if (!e2e[key]) e2e[key] = [];
            e2e[key].push(text);
        }
        result.e2e = e2e;
        result.nums = result_nums;

        // 方式3: 查找互动栏的所有数字
        var interactBar = document.querySelector('[class*="interact"], [class*="engage"], [class*="bottom-bar"]');
        if (interactBar) {
            var spans = interactBar.querySelectorAll('span');
            var nums = [];
            for (var j = 0; j < spans.length; j++) {
                var t = spans[j].textContent.trim();
                if (/^[\\d.]+[万亿wW]?$/.test(t) && t.length < 10) {
                    nums.push(t);
                }
            }
            result.interactNums = nums;
        }

        return result;
        """)

        result["title"] = js_result.get("title", "")
        result["author"] = js_result.get("author", "")

        # 从 nums 提取
        nums = js_result.get("nums", {})
        if nums.get("likes"):
            result["likes"] = self._parse_number(nums["likes"])
        if nums.get("comments"):
            result["comments"] = self._parse_number(nums["comments"])
        if nums.get("collects"):
            result["collects"] = self._parse_number(nums["collects"])
        if nums.get("shares"):
            result["shares"] = self._parse_number(nums["shares"])

        # 从 e2e 提取
        e2e = js_result.get("e2e", {})
        if not result.get("likes"):
            for key in ["like-count", "likeCount", "digg-count"]:
                if e2e.get(key):
                    val = e2e[key][0] if isinstance(e2e[key], list) else e2e[key]
                    result["likes"] = self._parse_number(val)
                    break

        # 从 interactNums 位置推断
        interact_nums = js_result.get("interactNums", [])
        if not result.get("likes") and len(interact_nums) >= 4:
            result["likes"] = self._parse_number(interact_nums[0])
            result["comments"] = self._parse_number(interact_nums[1])
            result["collects"] = self._parse_number(interact_nums[2])
            result["shares"] = self._parse_number(interact_nums[3])

        return result

    def _parse_number(self, text):
        if not text:
            return 0
        text = str(text).strip().replace(",", "")
        multipliers = {"w": 10000, "W": 10000, "万": 10000, "亿": 100000000}
        for suffix, mul in multipliers.items():
            if text.endswith(suffix):
                try:
                    return int(float(text[:-1]) * mul)
                except ValueError:
                    return 0
        try:
            return int(float(text))
        except ValueError:
            return 0

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


# =========================================================================
# 账号分析引擎
# =========================================================================

class AccountScraper:
    """采集账号主页所有作品数据"""

    COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".douyin_cookies.json")

    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.msg_queue = None
        self._wait_for_login = False

    def _init_driver(self):
        """启动 Edge 浏览器"""
        # 关闭已有 Edge 进程
        os.system("taskkill /f /im msedge.exe >nul 2>&1")
        time.sleep(1)

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Edge(options=options)

    def _save_cookies(self):
        """保存当前 cookies 到文件"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存 cookies 失败: {e}")

    def _load_cookies(self):
        """从文件加载 cookies"""
        try:
            if not os.path.isfile(self.COOKIE_FILE):
                return False
            with open(self.COOKIE_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            if not cookies:
                return False
            # 先访问抖音设置域名
            self.driver.get("https://www.douyin.com")
            time.sleep(2)
            # 清除旧 cookies
            self.driver.delete_all_cookies()
            # 添加保存的 cookies
            for cookie in cookies:
                try:
                    # 移除可能导致问题的字段
                    clean = {}
                    for k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly', 'expiry']:
                        if k in cookie:
                            clean[k] = cookie[k]
                    self.driver.add_cookie(clean)
                except Exception:
                    pass
            # 刷新页面使 cookies 生效
            self.driver.refresh()
            time.sleep(3)
            return True
        except Exception:
            return False

    def _is_logged_in(self):
        """检查是否已登录"""
        try:
            # 检查页面是否有登录按钮或用户头像
            result = self.driver.execute_script("""
            // 如果有登录按钮，说明未登录
            var loginBtn = document.querySelector('[class*="login"], [data-e2e="login"]');
            if (loginBtn && loginBtn.offsetParent !== null) return false;
            // 如果有用户头像或"我的"链接，说明已登录
            var userEl = document.querySelector('[class*="avatar"], [data-e2e="user-info"]');
            if (userEl) return true;
            // 检查是否在登录页
            if (window.location.href.includes('login')) return false;
            return true;
            """)
            return result
        except Exception:
            return False

    def _ensure_driver(self):
        if self.driver is None:
            self._init_driver()

    def analyze(self, url, max_scroll=30):
        """采集账号主页作品列表，返回 (账号信息, 作品列表)"""
        self._ensure_driver()

        # 尝试加载 cookies
        has_cookies = self._load_cookies()

        if has_cookies and self._is_logged_in():
            self.msg_queue.put({"type": "account_log", "text": "已加载保存的登录状态，开始采集..."})
        else:
            # 需要登录
            self.driver.get("https://www.douyin.com")
            time.sleep(2)
            self.msg_queue.put({"type": "account_log", "text": "请在浏览器中登录抖音，登录后点击「确认登录」"})
            self._wait_for_login = True
            while self._wait_for_login:
                time.sleep(1)
            # 等待页面加载
            time.sleep(3)
            # 保存 cookies
            self._save_cookies()
            self.msg_queue.put({"type": "account_log", "text": "登录状态已保存，开始采集..."})

        # 导航到目标主页
        self.driver.get(url)
        time.sleep(5)

        # 获取账号信息
        account_info = self._extract_account_info()

        # 滚动加载作品
        videos = []
        seen_keys = set()
        no_new_count = 0

        for i in range(max_scroll):
            self.msg_queue.put({"type": "account_log", "text": f"正在采集作品... 滚动 {i+1}/{max_scroll}，已获取 {len(videos)} 条"})

            new_videos = self._extract_video_list()
            added = 0
            for v in new_videos:
                v_url = v.get("url", "")
                v_title = v.get("title", "")
                v_likes = v.get("likes", 0)
                key = v_url or f"{v_title}_{v_likes}_{len(videos)}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    videos.append(v)
                    added += 1

            if added == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    break
            else:
                no_new_count = 0

            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 检查是否到底
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_new_count += 1

        return account_info, videos

    def _extract_account_info(self):
        """提取账号基本信息"""
        try:
            info = self.driver.execute_script("""
            var result = {};
            // 昵称
            var nameEl = document.querySelector('h1')
                || document.querySelector('[class*="nickname"]');
            result.name = nameEl ? nameEl.textContent.trim() : '';
            // 粉丝数
            var allText = document.body.innerText;
            var followerMatch = allText.match(/(\\d[\\d.]*[万亿]?)\\s*粉丝/);
            result.followers = followerMatch ? followerMatch[1] : '';
            return result;
            """)
            return info or {}
        except Exception:
            return {}

    def _extract_video_list(self):
        """从页面提取作品列表"""
        try:
            videos = self.driver.execute_script("""
            var videos = [];

            // 数字解析（处理"万"、"亿"后缀）
            function parseNum(text) {
                if (!text) return 0;
                text = text.trim().replace(/,/g, '');
                if (text.endsWith('亿')) return Math.round(parseFloat(text) * 100000000);
                if (text.endsWith('万') || text.endsWith('w') || text.endsWith('W'))
                    return Math.round(parseFloat(text) * 10000);
                return Math.round(parseFloat(text)) || 0;
            }

            // 从 RENDER_DATA 提取
            var rd = document.getElementById('RENDER_DATA');
            if (rd) {
                try {
                    var data = JSON.parse(decodeURIComponent(rd.textContent));
                    function findAwemeList(obj, depth) {
                        if (depth > 10 || !obj || typeof obj !== 'object') return null;
                        if (Array.isArray(obj) && obj.length > 0) {
                            var first = obj[0];
                            if (first && (first.aweme_id || first.awemeId) && (first.desc !== undefined || first.statistics)) {
                                return obj;
                            }
                        }
                        for (var k in obj) {
                            var found = findAwemeList(obj[k], depth + 1);
                            if (found) return found;
                        }
                        return null;
                    }
                    var awemeList = findAwemeList(data, 0);
                    if (awemeList) {
                        for (var i = 0; i < awemeList.length; i++) {
                            var item = awemeList[i];
                            var stats = item.statistics || item.stats || {};
                            videos.push({
                                title: (item.desc || '').substring(0, 100),
                                likes: parseInt(stats.digg_count || stats.diggCount || 0),
                                comments: parseInt(stats.comment_count || stats.commentCount || 0),
                                collects: parseInt(stats.collect_count || stats.collectCount || 0),
                                shares: parseInt(stats.share_count || stats.shareCount || 0),
                                views: parseInt(stats.play_count || stats.playCount || 0)
                            });
                        }
                    }
                } catch(e) {}
            }

            // DOM 提取兜底
            if (videos.length === 0) {
                var links = document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]');
                var seen = new Set();
                links.forEach(function(a) {
                    var href = a.href;
                    if (seen.has(href)) return;
                    seen.add(href);
                    var card = a.closest('li') || a;
                    var titleEl = card.querySelector('p span') || card.querySelector('p');
                    var nums = [];
                    card.querySelectorAll('span').forEach(function(el) {
                        var t = el.textContent.trim();
                        if (/^[\\d.]+[万亿wW]?$/.test(t) && t.length < 12) nums.push(t);
                    });
                    videos.push({
                        title: titleEl ? titleEl.textContent.trim().substring(0, 100) : '',
                        url: href,
                        likes: parseNum(nums[0]),
                        comments: parseNum(nums[1]),
                        collects: parseNum(nums[2]),
                        shares: parseNum(nums[3]) || 0,
                        views: 0
                    });
                });
            }

            return videos;
            """)
            return videos or []
        except Exception:
            return []

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


# =========================================================================
# 采集线程
# =========================================================================

class ScraperThread(threading.Thread):
    def __init__(self, scraper, urls, msg_queue, platform="douyin"):
        threading.Thread.__init__(self)
        self.scraper = scraper
        self.urls = urls
        self.queue = msg_queue
        self.platform = platform
        self.daemon = True

    def run(self):
        total = len(self.urls)
        for i, url in enumerate(self.urls):
            url = url.strip()
            if not url:
                continue
            self.queue.put({"type": "log", "text": "[{}/{}] {}".format(i + 1, total, url)})
            try:
                data = self.scraper.extract(url)
                if "error" in data:
                    self.queue.put({"type": "log", "text": "  FAILED: " + data["error"]})
                else:
                    likes = data.get("likes", 0)
                    self.queue.put({"type": "log", "text": "  OK: {} likes={}".format(
                        data.get("title", "")[:30], likes)})
                self.queue.put({"type": "result", "data": data})
            except Exception as e:
                self.queue.put({"type": "log", "text": "  ERROR: " + str(e)})
                self.queue.put({"type": "result", "data": {"url": url, "error": str(e)}})
            self.queue.put({"type": "progress", "current": i + 1, "total": total})
        self.queue.put({"type": "done"})


# =========================================================================
# 数据分析
# =========================================================================

class DataAnalyzer:
    def __init__(self, data_list):
        self.df = pd.DataFrame(data_list)

    def to_excel(self, filepath):
        cols = ["url", "platform", "author", "title", "likes", "comments",
                "collects", "shares", "views"]
        col_names = {
            "url": "链接", "platform": "平台", "author": "作者",
            "title": "标题", "likes": "点赞", "comments": "评论",
            "collects": "收藏", "shares": "转发", "views": "播放量"
        }
        # 确保所有列都存在，缺失的填0
        df_out = self.df.copy()
        for c in cols:
            if c not in df_out.columns:
                df_out[c] = 0
        df_out = df_out[cols]
        df_out.rename(columns=col_names, inplace=True)
        writer = pd.ExcelWriter(filepath, engine="openpyxl")
        df_out.to_excel(writer, index=False, sheet_name="数据")
        ws = writer.sheets["数据"]
        for col_cells in ws.columns:
            max_len = 0
            for cell in col_cells:
                try:
                    cell_len = len(str(cell.value or ""))
                    max_len = max(max_len, cell_len)
                except Exception:
                    pass
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 50)
        ws.freeze_panes = "A2"
        writer.close()

    def get_summary(self):
        numeric_cols = ["likes", "comments", "collects", "shares", "views"]
        existing = [c for c in numeric_cols if c in self.df.columns]
        if not existing:
            return "No numeric data"
        desc = self.df[existing].describe().round(0).astype(int)
        return desc.to_string()

    def get_top(self, column="likes", n=10):
        if column not in self.df.columns:
            return pd.DataFrame()
        top = self.df.nlargest(n, column)
        display_cols = ["title", "author", column]
        existing = [c for c in display_cols if c in top.columns]
        return top[existing]


# =========================================================================
# 主界面
# =========================================================================

class Application(ttk.Window):
    def __init__(self):
        ttk.Window.__init__(self, title="新媒体数据采集与分析工具", themename="cosmo",
                            size=(1060, 720), minsize=(800, 550))
        self.msg_queue = queue.Queue()
        self.results = []
        self.scraper = None
        self.is_running = False
        self.account_results = []
        self._build_ui()

    def _build_ui(self):
        # --- 标题栏 ---
        frm_header = ttk.Frame(self, padding=10)
        frm_header.pack(fill=X)
        ttk.Label(frm_header, text="新媒体数据采集与分析工具",
                  font=("Microsoft YaHei UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(frm_header, text="  支持抖音 / 小红书",
                  font=("Microsoft YaHei UI", 9), bootstyle="secondary").pack(side=LEFT, padx=(5, 0), pady=(5, 0))

        # --- Tab 页 ---
        notebook = ttk.Notebook(self, bootstyle="primary")
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=(0, 8))

        # ========== Tab 1: 作品采集 ==========
        tab_scrape = ttk.Frame(notebook)
        notebook.add(tab_scrape, text="  作品采集  ")
        self._build_scrape_tab(tab_scrape)

        # ========== Tab 2: 账号分析 ==========
        tab_account = ttk.Frame(notebook)
        notebook.add(tab_account, text="  账号分析  ")
        self._build_account_tab(tab_account)

    # --------------------------------------------------
    # Tab 1: 作品采集（原有功能）
    # --------------------------------------------------
    def _build_scrape_tab(self, parent):
        # 输入区
        frm_input = ttk.LabelFrame(parent, text=" 链接输入（每行一个，支持粘贴分享文本）")
        frm_input.pack(fill=X, padx=8, pady=(8, 6))

        self.txt_input = tk.Text(frm_input, height=4, wrap=tk.WORD, font=("Microsoft YaHei UI", 10),
                                 relief=FLAT, padx=8, pady=6)
        self.txt_input.pack(fill=X, side=LEFT, expand=True)
        scrollbar = ttk.Scrollbar(frm_input, command=self.txt_input.yview, bootstyle="info-round")
        scrollbar.pack(side=RIGHT, fill=Y)
        self.txt_input.config(yscrollcommand=scrollbar.set)

        # 按钮区
        frm_btns = ttk.Frame(parent, padding=(8, 0))
        frm_btns.pack(fill=X, pady=(0, 4))

        ttk.Label(frm_btns, text="平台:", font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=(0, 4))
        self.platform_var = tk.StringVar(value="auto")
        ttk.Combobox(frm_btns, textvariable=self.platform_var,
                     values=["auto", "douyin", "xiaohongshu"],
                     state="readonly", width=12, font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=(0, 12))

        self.btn_start = ttk.Button(frm_btns, text="  开始采集", command=self.start_scrape,
                                     bootstyle="success", width=10)
        self.btn_start.pack(side=LEFT, padx=(0, 6))
        ttk.Button(frm_btns, text="清空", command=self.clear_all,
                   bootstyle="light", width=6).pack(side=LEFT, padx=(0, 6))
        ttk.Button(frm_btns, text="从文件导入", command=self.import_file,
                   bootstyle="light", width=10).pack(side=LEFT, padx=(0, 6))

        self.lbl_status = ttk.Label(frm_btns, text="就绪", font=("Microsoft YaHei UI", 9), bootstyle="secondary")
        self.lbl_status.pack(side=RIGHT)

        # 进度条
        self.progress = ttk.Progressbar(parent, mode="determinate", bootstyle="info-striped")
        self.progress.pack(fill=X, padx=8, pady=(0, 4))

        # 日志区
        frm_log = ttk.LabelFrame(parent, text=" 运行日志")
        frm_log.pack(fill=X, padx=8, pady=(0, 4))
        self.txt_log = tk.Text(frm_log, height=2, wrap=tk.WORD, state=tk.DISABLED,
                               font=("Consolas", 9), relief=FLAT, padx=6, pady=4,
                               bg="#f8f9fa", fg="#495057")
        self.txt_log.pack(fill=X)

        # 结果表格
        frm_table = ttk.LabelFrame(parent, text=" 采集结果")
        frm_table.pack(fill=BOTH, expand=True, padx=8, pady=(0, 4))

        columns = ("url", "author", "title", "likes", "comments", "collects", "shares")
        self.tree = ttk.Treeview(frm_table, columns=columns, show="headings", height=6, bootstyle="primary")
        headers = {
            "url": ("链接", 140), "author": ("作者", 90), "title": ("标题", 200),
            "likes": ("点赞", 70), "comments": ("评论", 70),
            "collects": ("收藏", 70), "shares": ("转发", 70)
        }
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, minwidth=50,
                             anchor=CENTER if col in ("likes", "comments", "collects", "shares") else W)

        scroll_y = ttk.Scrollbar(frm_table, orient=VERTICAL, command=self.tree.yview, bootstyle="primary-round")
        scroll_x = ttk.Scrollbar(frm_table, orient=HORIZONTAL, command=self.tree.xview, bootstyle="primary-round")
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frm_table.grid_rowconfigure(0, weight=1)
        frm_table.grid_columnconfigure(0, weight=1)

        # 底部按钮
        frm_bottom = ttk.Frame(parent, padding=(8, 4, 8, 6))
        frm_bottom.pack(fill=X)
        ttk.Button(frm_bottom, text="  导出 Excel", command=self.export_excel,
                   bootstyle="success-outline", width=13).pack(side=LEFT, padx=(0, 8))
        ttk.Button(frm_bottom, text="  数据分析", command=self.show_analysis,
                   bootstyle="info-outline", width=13).pack(side=LEFT, padx=(0, 8))
        ttk.Button(frm_bottom, text="  调试提取", command=self.debug_extract,
                   bootstyle="warning-outline", width=13).pack(side=LEFT, padx=(0, 8))
        self.lbl_count = ttk.Label(frm_bottom, text="共 0 条数据",
                                    font=("Microsoft YaHei UI", 9), bootstyle="secondary")
        self.lbl_count.pack(side=RIGHT)

    # --------------------------------------------------
    # Tab 2: 账号分析
    # --------------------------------------------------
    def _build_account_tab(self, parent):
        # 输入区
        frm_input = ttk.LabelFrame(parent, text=" 输入抖音账号主页链接 ")
        frm_input.pack(fill=X, padx=8, pady=(8, 6))

        frm_row = ttk.Frame(frm_input, padding=6)
        frm_row.pack(fill=X)

        self.txt_account_url = tk.Entry(frm_row, font=("Microsoft YaHei UI", 10))
        self.txt_account_url.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        ttk.Label(frm_row, text="滚动:", font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=(0, 4))
        self.scroll_count_var = tk.StringVar(value="20")
        ttk.Combobox(frm_row, textvariable=self.scroll_count_var,
                     values=["10", "20", "30", "50"], width=5, font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=(0, 8))

        self.btn_account_start = ttk.Button(frm_row, text="  开始分析", command=self.start_account_analysis,
                                             bootstyle="success", width=10)
        self.btn_account_start.pack(side=LEFT)

        # 状态栏 + 确认登录按钮
        frm_status = ttk.Frame(parent)
        frm_status.pack(fill=X, padx=8, pady=(4, 2))

        self.lbl_account_status = ttk.Label(frm_status, text="粘贴账号主页链接，点击开始分析（首次需在弹出浏览器中登录）",
                                             font=("Microsoft YaHei UI", 9), bootstyle="secondary")
        self.lbl_account_status.pack(side=LEFT)

        self.btn_confirm_login = ttk.Button(frm_status, text="  确认登录  ", command=self._confirm_login,
                                             bootstyle="warning", width=10, state=tk.DISABLED)
        self.btn_confirm_login.pack(side=RIGHT)

        # 账号信息 + 数据统计（水平排列）
        frm_top_row = ttk.Frame(parent)
        frm_top_row.pack(fill=X, padx=8, pady=(4, 4))

        # 左侧：账号信息
        frm_info = ttk.LabelFrame(frm_top_row, text=" 账号概览 ")
        frm_info.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 4))

        self.lbl_account_info = tk.Text(frm_info, height=5, wrap=tk.WORD, font=("Microsoft YaHei UI", 10),
                                         relief=FLAT, padx=10, pady=8, state=tk.DISABLED)
        self.lbl_account_info.pack(fill=BOTH, expand=True)

        # 右侧：数据统计
        frm_stats = ttk.LabelFrame(frm_top_row, text=" 数据统计 ")
        frm_stats.pack(side=LEFT, fill=BOTH, expand=True, padx=(4, 0))

        self.txt_account_stats = tk.Text(frm_stats, height=5, wrap=tk.WORD, font=("Consolas", 9),
                                          relief=FLAT, padx=10, pady=8, state=tk.DISABLED)
        self.txt_account_stats.pack(fill=BOTH, expand=True)

        # 作品列表
        frm_table_acc = ttk.LabelFrame(parent, text=" 作品列表（按点赞排序）")
        frm_table_acc.pack(fill=BOTH, expand=True, padx=8, pady=(0, 4))

        acc_columns = ("idx", "title", "likes", "comments", "collects", "shares")
        self.tree_account = ttk.Treeview(frm_table_acc, columns=acc_columns, show="headings",
                                          height=10, bootstyle="info")
        acc_headers = {
            "idx": ("#", 40), "title": ("标题", 320), "likes": ("点赞", 80),
            "comments": ("评论", 70), "collects": ("收藏", 70), "shares": ("转发", 70)
        }
        for col, (text, width) in acc_headers.items():
            self.tree_account.heading(col, text=text)
            self.tree_account.column(col, width=width, minwidth=30, anchor=CENTER if col != "title" else W)

        acc_scroll_y = ttk.Scrollbar(frm_table_acc, orient=VERTICAL, command=self.tree_account.yview,
                                      bootstyle="info-round")
        self.tree_account.configure(yscrollcommand=acc_scroll_y.set)
        self.tree_account.grid(row=0, column=0, sticky="nsew")
        acc_scroll_y.grid(row=0, column=1, sticky="ns")
        frm_table_acc.grid_rowconfigure(0, weight=1)
        frm_table_acc.grid_columnconfigure(0, weight=1)

        # 底部按钮
        frm_acc_bottom = ttk.Frame(parent, padding=(8, 4, 8, 6))
        frm_acc_bottom.pack(fill=X)
        ttk.Button(frm_acc_bottom, text="  导出分析报告", command=self.export_account_report,
                   bootstyle="success-outline", width=14).pack(side=LEFT, padx=(0, 8))
        ttk.Button(frm_acc_bottom, text="  导出作品数据", command=self.export_account_excel,
                   bootstyle="info-outline", width=14).pack(side=LEFT)

    # ------ 操作 ------

    def _detect_platform(self, url):
        if "douyin.com" in url:
            return "douyin"
        elif "xiaohongshu.com" in url or "xhslink.com" in url:
            return "xiaohongshu"
        return "douyin"

    def start_scrape(self):
        text = self.txt_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "请先输入链接！")
            return

        urls = [u.strip() for u in text.split("\n") if u.strip()]
        if not urls:
            messagebox.showwarning("提示", "没有有效的链接！")
            return

        platform = self.platform_var.get()
        if platform == "auto":
            platform = self._detect_platform(urls[0])

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress["maximum"] = len(urls)
        self.lbl_status.config(text="采集中({})...".format(platform))
        self._clear_log()

        if platform == "xiaohongshu":
            self.scraper = XiaohongshuScraper(headless=False)
        else:
            self.scraper = DouyinScraper(headless=False)
        thread = ScraperThread(self.scraper, urls, self.msg_queue, platform)
        thread.start()
        self._poll_queue()

    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg["type"] == "result":
                    self.results.append(msg["data"])
                    self._add_table_row(msg["data"])
                elif msg["type"] == "log":
                    self._append_log(msg["text"])
                elif msg["type"] == "progress":
                    self.progress["value"] = msg["current"]
                    self.lbl_status.config(text="采集中 {}/{}".format(msg["current"], msg["total"]))
                elif msg["type"] == "done":
                    self._on_complete()
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _on_complete(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        ok_count = sum(1 for r in self.results if "error" not in r)
        self.lbl_status.config(text="完成！成功 {} 条".format(ok_count))
        self.lbl_count.config(text="共 {} 条数据".format(len(self.results)))
        if self.scraper:
            self.scraper.close()
            self.scraper = None

    def clear_all(self):
        self.txt_input.delete("1.0", tk.END)
        self.results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._clear_log()
        self.progress["value"] = 0
        self.lbl_status.config(text="就绪")
        self.lbl_count.config(text="共 0 条数据")

    def import_file(self):
        filepath = filedialog.askopenfilename(
            title="选择链接文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.txt_input.delete("1.0", tk.END)
            self.txt_input.insert("1.0", content)

    def export_excel(self):
        if not self.results:
            messagebox.showwarning("提示", "没有数据可导出！")
            return
        filepath = filedialog.asksaveasfilename(
            title="保存Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filepath:
            analyzer = DataAnalyzer(self.results)
            analyzer.to_excel(filepath)
            messagebox.showinfo("完成", "已导出到：\n" + filepath)

    def show_analysis(self):
        if not self.results:
            messagebox.showwarning("提示", "没有数据可分析！")
            return
        analyzer = DataAnalyzer(self.results)
        win = ttk.Toplevel(self)
        win.title("数据分析")
        win.geometry("1000x700")

        notebook = ttk.Notebook(win, bootstyle="info")
        notebook.pack(fill=BOTH, expand=True, padx=8, pady=8)

        # --- Tab 1: 文字统计 ---
        tab_text = ttk.Frame(notebook, padding=5)
        notebook.add(tab_text, text="  统计摘要  ")

        txt = tk.Text(tab_text, wrap=tk.WORD, font=("Consolas", 10), relief=FLAT, padx=10, pady=10)
        txt.pack(fill=BOTH, expand=True)

        txt.insert(tk.END, "=" * 50 + "\n")
        txt.insert(tk.END, "数据统计摘要\n")
        txt.insert(tk.END, "=" * 50 + "\n\n")
        txt.insert(tk.END, analyzer.get_summary() + "\n\n")

        txt.insert(tk.END, "=" * 50 + "\n")
        txt.insert(tk.END, "点赞 Top 10\n")
        txt.insert(tk.END, "=" * 50 + "\n\n")
        top = analyzer.get_top("likes", 10)
        txt.insert(tk.END, top.to_string(index=False) + "\n\n")

        txt.insert(tk.END, "=" * 50 + "\n")
        txt.insert(tk.END, "评论 Top 10\n")
        txt.insert(tk.END, "=" * 50 + "\n\n")
        top_c = analyzer.get_top("comments", 10)
        txt.insert(tk.END, top_c.to_string(index=False) + "\n")
        txt.config(state=tk.DISABLED)

        # --- Tab 2: 点赞排行柱状图 ---
        tab_bar = ttk.Frame(notebook, padding=5)
        notebook.add(tab_bar, text="  点赞排行  ")

        df_likes = analyzer.get_top("likes", 10)
        if not df_likes.empty:
            fig1 = Figure(figsize=(9, 5), dpi=100)
            ax1 = fig1.add_subplot(111)
            labels = [str(t)[:15] for t in df_likes["title"].tolist()]
            values = df_likes["likes"].tolist()
            colors = plt.cm.Reds([0.3 + 0.7 * i / max(len(values), 1) for i in range(len(values))])
            bars = ax1.barh(labels[::-1], values[::-1], color=colors[::-1])
            ax1.set_xlabel("点赞数")
            ax1.set_title("点赞 Top 10")
            for bar, val in zip(bars, values[::-1]):
                ax1.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                         str(val), va="center", fontsize=9)
            fig1.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, tab_bar)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Tab 3: 多维对比图 ---
        tab_compare = ttk.Frame(notebook, padding=5)
        notebook.add(tab_compare, text="  多维对比  ")

        df_top = analyzer.get_top("likes", 10)
        if not df_top.empty:
            fig2 = Figure(figsize=(9, 5), dpi=100)
            ax2 = fig2.add_subplot(111)
            labels2 = [str(t)[:12] for t in df_top["title"].tolist()]
            x = range(len(labels2))
            bar_width = 0.2
            likes_vals = df_top["likes"].tolist()
            comments_vals = df_top["comments"].tolist() if "comments" in df_top.columns else [0] * len(labels2)
            collects_vals = df_top["collects"].tolist() if "collects" in df_top.columns else [0] * len(labels2)

            ax2.bar([i - bar_width for i in x], likes_vals, bar_width, label="点赞", color="#e74c3c")
            ax2.bar(x, comments_vals, bar_width, label="评论", color="#3498db")
            ax2.bar([i + bar_width for i in x], collects_vals, bar_width, label="收藏", color="#2ecc71")
            ax2.set_xticks(list(x))
            ax2.set_xticklabels(labels2, rotation=30, ha="right", fontsize=8)
            ax2.set_ylabel("数量")
            ax2.set_title("点赞 / 评论 / 收藏 对比")
            ax2.legend()
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, tab_compare)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def debug_extract(self):
        """调试模式：提取第1个链接的所有原始数据并显示"""
        text = self.txt_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "请先输入一个链接！")
            return
        url = text.split("\n")[0].strip()
        if not url:
            return

        self._append_log("=== 调试提取 ===")
        self._append_log("URL: " + url)

        scraper = DouyinScraper(headless=False)
        try:
            real_url = scraper._extract_url(url)
            self._append_log("提取的URL: " + real_url)
            scraper._ensure_driver()
            real_url = scraper._resolve_url(real_url)
            self._append_log("跳转后URL: " + real_url)
            time.sleep(4)

            # 执行JS获取页面信息
            js_dump = scraper.driver.execute_script("""
            var result = {};

            // 1. 所有 data-e2e 属性
            var e2e = {};
            document.querySelectorAll('[data-e2e]').forEach(function(el) {
                var key = el.getAttribute('data-e2e');
                var text = el.textContent.trim().substring(0, 50);
                if (!e2e[key]) e2e[key] = [];
                e2e[key].push(text);
            });
            result.e2e = e2e;

            // 2. RENDER_DATA
            var rd = document.getElementById('RENDER_DATA');
            result.hasRenderData = !!rd;
            result.renderDataLength = rd ? rd.textContent.length : 0;

            // 3. h1 标签
            var h1 = document.querySelector('h1');
            result.h1 = h1 ? h1.textContent.trim().substring(0, 100) : null;

            // 4. 所有包含数字的 span (前30个)
            var numSpans = [];
            document.querySelectorAll('span').forEach(function(el) {
                var t = el.textContent.trim();
                if (/^[\\d.]+[万亿wW]?$/.test(t) && t.length < 15) {
                    var cls = el.className || '';
                    var parent = el.parentElement;
                    var parentCls = parent ? (parent.className || '') : '';
                    var dataE2e = el.getAttribute('data-e2e') || '';
                    numSpans.push({text: t, class: cls.substring(0,60), parentClass: parentCls.substring(0,60), e2e: dataE2e});
                }
            });
            result.numSpans = numSpans.slice(0, 30);

            // 5. 页面标题
            result.pageTitle = document.title;

            // 6. 页面URL
            result.pageUrl = window.location.href;

            return result;
            """)

            # 显示结果
            win = ttk.Toplevel(self)
            win.title("调试信息")
            win.geometry("700x500")
            txt = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10), relief=FLAT, padx=10, pady=10)
            txt.pack(fill=BOTH, expand=True, padx=8, pady=8)

            txt.insert(tk.END, "页面URL: " + str(js_dump.get("pageUrl")) + "\n")
            txt.insert(tk.END, "页面标题: " + str(js_dump.get("pageTitle")) + "\n")
            txt.insert(tk.END, "h1标签: " + str(js_dump.get("h1")) + "\n")
            txt.insert(tk.END, "RENDER_DATA存在: " + str(js_dump.get("hasRenderData")) + "\n")
            txt.insert(tk.END, "RENDER_DATA长度: " + str(js_dump.get("renderDataLength")) + "\n\n")

            txt.insert(tk.END, "=" * 50 + "\n")
            txt.insert(tk.END, "data-e2e 属性:\n")
            txt.insert(tk.END, "=" * 50 + "\n")
            e2e = js_dump.get("e2e", {})
            for k, v in e2e.items():
                txt.insert(tk.END, "  " + k + " -> " + str(v) + "\n")

            txt.insert(tk.END, "\n" + "=" * 50 + "\n")
            txt.insert(tk.END, "页面上的数字文本:\n")
            txt.insert(tk.END, "=" * 50 + "\n")
            for item in js_dump.get("numSpans", []):
                txt.insert(tk.END, "  text={text} | class={cls} | parent={pcls} | e2e={e2e}\n".format(
                    text=item.get("text"), cls=item.get("class"),
                    pcls=item.get("parentClass"), e2e=item.get("e2e")))

            txt.config(state=tk.DISABLED)
            self._append_log("调试信息已显示")

        except Exception as e:
            self._append_log("调试失败: " + str(e))
            import traceback
            self._append_log(traceback.format_exc())
        finally:
            scraper.close()

    # ------ 账号分析 ------

    def start_account_analysis(self):
        url = self.txt_account_url.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入账号主页链接！")
            return

        # 自动修正：如果不是完整 URL，当成抖音号搜索
        if not url.startswith("http"):
            url = f"https://www.douyin.com/search/{url}?type=user"

        max_scroll = int(self.scroll_count_var.get())
        self.account_results = []
        self.btn_account_start.config(state=tk.DISABLED)
        self.btn_confirm_login.config(state=tk.NORMAL)
        self.lbl_account_status.config(text="正在启动浏览器，请稍候...")

        # 清空旧数据
        for item in self.tree_account.get_children():
            self.tree_account.delete(item)
        self._set_text(self.lbl_account_info, "")
        self._set_text(self.txt_account_stats, "")

        self.account_scraper = AccountScraper(headless=False)
        thread = threading.Thread(target=self._run_account_analysis, args=(url, max_scroll), daemon=True)
        thread.start()
        self._poll_account_queue()

    def _confirm_login(self):
        if hasattr(self, 'account_scraper') and self.account_scraper:
            self.account_scraper._wait_for_login = False
            self.btn_confirm_login.config(state=tk.DISABLED)

    def _run_account_analysis(self, url, max_scroll):
        try:
            self.account_scraper.msg_queue = self.msg_queue
            self.msg_queue.put({"type": "account_log", "text": "正在启动浏览器..."})
            account_info, videos = self.account_scraper.analyze(url, max_scroll)
            self.msg_queue.put({"type": "account_info", "data": account_info})
            for v in videos:
                self.msg_queue.put({"type": "account_video", "data": v})
            self.msg_queue.put({"type": "account_done"})
        except Exception as e:
            import traceback
            detail = traceback.format_exc()
            self.msg_queue.put({"type": "account_error", "text": f"{e}\n\n{detail}"})

    def _poll_account_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg["type"] == "account_info":
                    self._display_account_info(msg["data"])
                elif msg["type"] == "account_video":
                    self.account_results.append(msg["data"])
                    self._add_account_row(msg["data"], len(self.account_results))
                elif msg["type"] == "account_log":
                    self.lbl_account_status.config(text=msg["text"])
                elif msg["type"] == "account_done":
                    self._on_account_complete()
                    return
                elif msg["type"] == "account_error":
                    self.lbl_account_status.config(text="采集失败: " + msg["text"])
                    self.btn_account_start.config(state=tk.NORMAL)
                    self.btn_confirm_login.config(state=tk.DISABLED)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_account_queue)

    def _display_account_info(self, info):
        name = info.get("name", "未知")
        followers = info.get("followers", "未知")
        desc = info.get("description", "")
        text = f"账号: {name}    粉丝: {followers}\n简介: {desc}" if desc else f"账号: {name}    粉丝: {followers}"
        self._set_text(self.lbl_account_info, text)

    def _on_account_complete(self):
        self.btn_account_start.config(state=tk.NORMAL)
        self.btn_confirm_login.config(state=tk.DISABLED)

        count = len(self.account_results)
        self.lbl_account_status.config(text=f"采集完成，共 {count} 条作品")

        if count > 0:
            self.account_results.sort(key=lambda x: x.get("likes", 0), reverse=True)
            for item in self.tree_account.get_children():
                self.tree_account.delete(item)
            for i, v in enumerate(self.account_results, 1):
                self._add_account_row(v, i)
            self._display_account_stats()

    def _display_account_stats(self):
        videos = self.account_results
        if not videos:
            return

        likes_list = [v.get("likes", 0) for v in videos]
        comments_list = [v.get("comments", 0) for v in videos]
        collects_list = [v.get("collects", 0) for v in videos]
        shares_list = [v.get("shares", 0) for v in videos]

        total_likes = sum(likes_list)
        total_comments = sum(comments_list)
        total_collects = sum(collects_list)
        total_shares = sum(shares_list)
        count = len(videos)

        avg_likes = total_likes / count
        avg_comments = total_comments / count
        avg_collects = total_collects / count
        avg_shares = total_shares / count

        # 爆款率（点赞 > 平均值 3 倍）
        viral_threshold = avg_likes * 3
        viral_count = sum(1 for l in likes_list if l >= viral_threshold)
        viral_rate = viral_count / count * 100

        # Top 5
        sorted_by_likes = sorted(videos, key=lambda x: x.get("likes", 0), reverse=True)

        lines = [
            "=" * 40,
            "账号数据概览",
            "=" * 40,
            f"作品总数:    {count}",
            f"总点赞:      {self._fmt_num(total_likes)}",
            f"总评论:      {self._fmt_num(total_comments)}",
            f"总收藏:      {self._fmt_num(total_collects)}",
            f"总转发:      {self._fmt_num(total_shares)}",
            "",
            f"平均点赞:    {self._fmt_num(int(avg_likes))}",
            f"平均评论:    {self._fmt_num(int(avg_comments))}",
            f"平均收藏:    {self._fmt_num(int(avg_collects))}",
            f"平均转发:    {self._fmt_num(int(avg_shares))}",
            "",
            f"爆款率:      {viral_rate:.1f}%（{viral_count}/{count}，点赞>{self._fmt_num(int(viral_threshold))}）",
            "",
            "=" * 40,
            "点赞 Top 5",
            "=" * 40,
        ]
        for i, v in enumerate(sorted_by_likes[:5], 1):
            title = v.get("title", "")[:30] or "(无标题)"
            likes = self._fmt_num(v.get("likes", 0))
            lines.append(f"  {i}. [{likes}赞] {title}")

        self._set_text(self.txt_account_stats, "\n".join(lines))

        # 标记爆款
        for i, item in enumerate(self.tree_account.get_children()):
            data = self.account_results[i]
            if data.get("likes", 0) >= viral_threshold:
                self.tree_account.item(item, tags=("viral",))
        self.tree_account.tag_configure("viral", background="#fff3cd")

    def _add_account_row(self, data, idx):
        self.tree_account.insert("", tk.END, values=(
            idx,
            (data.get("title", "") or "(无标题)")[:60],
            self._fmt_num(data.get("likes", 0)),
            self._fmt_num(data.get("comments", 0)),
            self._fmt_num(data.get("collects", 0)),
            self._fmt_num(data.get("shares", 0)),
        ))

    def _fmt_num(self, n):
        if n >= 10000:
            return f"{n / 10000:.1f}万"
        return str(n)

    def export_account_report(self):
        if not self.account_results:
            messagebox.showwarning("提示", "没有数据可导出！")
            return
        filepath = filedialog.asksaveasfilename(
            title="保存分析报告", defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if filepath:
            stats = self.txt_account_stats.get("1.0", tk.END)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(stats)
            messagebox.showinfo("完成", "报告已导出到：\n" + filepath)

    def export_account_excel(self):
        if not self.account_results:
            messagebox.showwarning("提示", "没有数据可导出！")
            return
        filepath = filedialog.asksaveasfilename(
            title="保存作品数据", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filepath:
            analyzer = DataAnalyzer(self.account_results)
            analyzer.to_excel(filepath)
            messagebox.showinfo("完成", "已导出到：\n" + filepath)

    def _set_text(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        if text:
            widget.insert("1.0", text)
        widget.config(state=tk.DISABLED)

    # ------ 辅助 ------

    def _add_table_row(self, data):
        if "error" in data:
            values = (data.get("url", ""), "ERROR", data["error"], "", "", "", "")
        else:
            values = (
                data.get("url", ""),
                data.get("author", ""),
                data.get("title", "")[:50],
                data.get("likes", 0),
                data.get("comments", 0),
                data.get("collects", 0),
                data.get("shares", 0),
            )
        self.tree.insert("", tk.END, values=values)

    def _append_log(self, text):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _clear_log(self):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.config(state=tk.DISABLED)


# =========================================================================
# 启动
# =========================================================================

if __name__ == "__main__":
    app = Application()
    app.mainloop()
