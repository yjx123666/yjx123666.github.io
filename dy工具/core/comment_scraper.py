"""
评论抓取核心逻辑
- 优先通过 API 拦截获取评论数据（在导航前设置监听）
- DOM 解析作为兜底方案
- RENDER_DATA 作为最终兜底
"""
import json
import os
import random
import re
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

import config


def extract_url(text: str) -> str:
    """从分享文本中提取 URL"""
    if text.strip().startswith("http"):
        return text.strip()
    url_pattern = r'https?://[^\s<>"\']+(?:douyin|iesdouyin)[^\s<>"\']*'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    url_pattern = r'https?://v\.douyin\.com/[^\s<>"\']+'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    return text.strip()


def scrape_comments(
    page: Page,
    video_url: str,
    target_count: int,
    log_callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Dict]:
    """抓取视频评论的主入口"""
    def log(msg):
        if log_callback:
            log_callback(msg)

    def progress(current, total):
        if progress_callback:
            progress_callback(current, total)

    # 1. 提取并解析 URL
    url = extract_url(video_url)
    log(f"解析链接: {url}")

    # 2. 设置 API 拦截（关键：必须在导航之前设置！）
    api_comments: List[Dict] = []
    seen_ids = set()
    api_urls_captured = []

    def handle_comment_response(response):
        """拦截评论 API 响应"""
        try:
            resp_url = response.url
            is_comment_api = any(kw in resp_url for kw in [
                "/comment/list", "/comment/", "comment_list",
                "/aweme/v1/comment", "/web/comment",
            ])
            if not is_comment_api:
                return
            if response.status != 200:
                return
            api_urls_captured.append(resp_url[:150])
            data = response.json()
            comments = data.get("comments") or data.get("comment_list") or []
            if not comments:
                return
            for c in comments:
                cid = str(c.get("cid") or c.get("comment_id") or c.get("id", ""))
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    create_time = c.get("create_time") or c.get("create_time_ms", 0)
                    if isinstance(create_time, (int, float)) and create_time > 1000000000:
                        time_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_str = str(create_time) if create_time else ""
                    user_info = c.get("user", {})
                    api_comments.append({
                        "comment_id": cid,
                        "user_name": user_info.get("nickname") or user_info.get("nick_name", ""),
                        "user_id": str(user_info.get("uid") or user_info.get("sec_uid", "")),
                        "comment_text": c.get("text") or c.get("content", ""),
                        "like_count": c.get("digg_count") or c.get("like_count", 0),
                        "reply_count": c.get("reply_comment_total") or c.get("reply_count", 0),
                        "publish_time": time_str,
                    })
        except Exception:
            pass

    # 关键修复：在导航之前就设置监听，不会错过首次加载的评论 API
    page.on("response", handle_comment_response)

    # 3. 导航到视频页
    log("正在打开视频页面...")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=config.PAGE_LOAD_TIMEOUT)
    except Exception:
        pass
    page.wait_for_timeout(5000)
    real_url = page.url
    log(f"真实地址: {real_url}")

    # 4. 尝试展开评论区
    log("正在展开评论区...")
    _try_open_comment_section(page, log)

    # 5. 滚动加载评论
    log("开始滚动加载评论...")
    no_new_count = 0
    scroll_count = 0
    prev_count = 0
    dom_comments: List[Dict] = []

    while len(api_comments) < target_count and scroll_count < config.MAX_SCROLL_TIMES:
        # 滚动评论列表
        _scroll_comment_list(page)
        scroll_count += 1

        # 等待加载（更长的等待时间）
        wait_time = config.SCROLL_WAIT_SEC + random.uniform(0.5, 1.5)
        page.wait_for_timeout(int(wait_time * 1000))

        # 等待加载状态消失
        _wait_for_loading(page)

        log(f"滚动第 {scroll_count} 次...")

        # DOM 解析兜底
        try:
            dom_items = _extract_visible_comments(page)
            log(f"  DOM 扫描到 {len(dom_items)} 条评论")
            for item in dom_items:
                cid = item.get("comment_id", "")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    dom_comments.append(item)
        except Exception:
            pass

        # 合并 API 和 DOM 评论
        all_comments = api_comments + dom_comments
        current_count = len(all_comments)

        if current_count == prev_count:
            no_new_count += 1
        else:
            no_new_count = 0
            progress(min(current_count, target_count), target_count)
            log(f"已收集 {current_count} 条评论 (API: {len(api_comments)}, DOM: {len(dom_comments)})")

        prev_count = current_count

        # 检查是否到底
        if _check_reached_bottom(page):
            log("检测到「到底」提示")
            break

        # 连续无新内容
        if no_new_count >= config.NO_NEW_SCROLL_LIMIT:
            log(f"连续 {config.NO_NEW_SCROLL_LIMIT} 次无新评论，停止滚动")
            break

        # 检测验证码
        if _check_captcha(page):
            log("检测到验证码，请在浏览器中手动完成验证...")
            _wait_for_captcha_done(page)
            log("验证完成，继续抓取...")

    # 调试信息
    log(f"API 拦截到 {len(api_urls_captured)} 个评论请求")
    if api_urls_captured:
        log(f"示例 URL: {api_urls_captured[0]}")

    # RENDER_DATA 兜底
    if not api_comments and not dom_comments:
        log("API 和 DOM 均未获取到评论，尝试 RENDER_DATA 提取...")
        render_comments = _extract_from_render_data(page)
        if render_comments:
            log(f"从 RENDER_DATA 提取到 {len(render_comments)} 条评论")
            dom_comments.extend(render_comments)

    # 6. 合并结果
    final_comments = _merge_comments(api_comments, dom_comments, target_count)
    progress(len(final_comments), target_count)

    # 移除监听
    try:
        page.remove_listener("response", handle_comment_response)
    except Exception:
        pass

    if not final_comments:
        log("未获取到任何评论，正在保存调试信息...")
        save_debug_info(page, "no_comments")

    log(f"抓取完成，共 {len(final_comments)} 条评论")
    return final_comments


def _try_open_comment_section(page: Page, log=None):
    """尝试展开评论区 - 多策略"""
    page.wait_for_timeout(2000)

    # 策略1: 查找并点击评论按钮
    selectors = [
        '[data-e2e="comment-icon"]',
        '[class*="comment-bar"]',
        '[class*="CommentIcon"]',
        '[class*="comment-icon"]',
        '[class*="commentEntry"]',
        '[class*="comment-entry"]',
        '[class*="comment-trigger"]',
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=3000):
                el.click()
                page.wait_for_timeout(3000)
                if log:
                    log(f"已点击评论按钮: {selector}")
                return
        except Exception:
            continue

    # 策略2: 用 JS 查找评论区并滚动到可视区域
    try:
        page.evaluate("""
        () => {
            // 查找评论相关的元素
            const els = document.querySelectorAll('[class*="comment"], [data-e2e*="comment"]');
            for (const el of els) {
                if (el.offsetHeight > 100) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    break;
                }
            }
        }
        """)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    # 策略3: 向下滚动页面
    for _ in range(3):
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(1000)


def _scroll_comment_list(page: Page):
    """滚动评论列表容器 - 多策略"""
    # 策略1: 查找评论列表容器，用鼠标滚轮滚动
    list_selectors = [
        '[data-e2e="comment-list"]',
        '[class*="comment-list"]',
        '[class*="CommentList"]',
        '[class*="comment-list-container"]',
        '[class*="commentList"]',
        '[class*="scroll-view"]',  # 抖音新版可能用的滚动容器
    ]
    for selector in list_selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1000):
                box = el.bounding_box()
                if box:
                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
                    page.mouse.move(x, y)
                    # 更多的滚动次数和更大的步长
                    for _ in range(8):
                        page.mouse.wheel(0, 600)
                        page.wait_for_timeout(300)
                    return
        except Exception:
            continue

    # 策略2: 直接设置 scrollTop
    for selector in list_selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1000):
                for _ in range(3):
                    el.evaluate("el => el.scrollTop += el.clientHeight * 2")
                    page.wait_for_timeout(500)
                return
        except Exception:
            continue

    # 策略3: 滚动整个页面 + 鼠标滚轮
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    page.mouse.move(960, 540)
    for _ in range(8):
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(300)


def _wait_for_loading(page: Page):
    """等待加载状态消失"""
    try:
        loading_selectors = [
            '[class*="loading"]',
            '[class*="Loading"]',
            'text=加载中',
            'text=正在加载',
        ]
        for selector in loading_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=500):
                    # 等待加载完成（最多5秒）
                    el.wait_for(state="hidden", timeout=5000)
                    return
            except Exception:
                continue
    except Exception:
        pass


def _extract_visible_comments(page: Page) -> List[Dict]:
    """从 DOM 中提取当前可见的评论"""
    result = page.evaluate("""
    () => {
        const itemSelectors = [
            '[data-e2e="comment-list-item"]',
            '[class*="CommentItem"]',
            '[class*="comment-item"]',
            '[class*="commentItem"]',
        ];
        let items = [];
        for (const sel of itemSelectors) {
            items = document.querySelectorAll(sel);
            if (items.length > 0) break;
        }
        if (!items || items.length === 0) return [];

        const nameSelectors = [
            '[data-e2e="comment-user-name"]',
            '[class*="CommentName"]',
            '[class*="comment-name"]',
            '[class*="commentName"]',
        ];
        const textSelectors = [
            '[data-e2e="comment-text"]',
            '[class*="CommentText"]',
            '[class*="comment-text"]',
            '[class*="commentText"]',
        ];
        const likeSelectors = [
            '[data-e2e="comment-like-count"]',
            '[class*="CommentLike"]',
            '[class*="comment-like"]',
            '[class*="commentDigg"]',
        ];
        const timeSelectors = [
            '[data-e2e="comment-time"]',
            '[class*="CommentTime"]',
            '[class*="comment-time"]',
            '[class*="commentTime"]',
        ];

        return Array.from(items).map((el, idx) => {
            const nameEl = nameSelectors.map(s => el.querySelector(s)).find(e => e);
            const textEl = textSelectors.map(s => el.querySelector(s)).find(e => e);
            const likeEl = likeSelectors.map(s => el.querySelector(s)).find(e => e);
            const timeEl = timeSelectors.map(s => el.querySelector(s)).find(e => e);

            return {
                comment_id: el.getAttribute('data-comment-id') || el.id || ('dom_' + idx),
                user_name: nameEl ? nameEl.textContent.trim() : '',
                comment_text: textEl ? textEl.textContent.trim() : '',
                like_count: likeEl ? likeEl.textContent.trim() : '0',
                reply_count: '0',
                publish_time: timeEl ? timeEl.textContent.trim() : '',
            };
        }).filter(c => c.comment_text);
    }
    """)
    return result or []


def _extract_from_render_data(page: Page) -> List[Dict]:
    """从页面 RENDER_DATA 中提取评论（兜底方案）"""
    try:
        result = page.evaluate("""
        () => {
            try {
                const rd = document.getElementById('RENDER_DATA');
                if (!rd) return [];
                const data = JSON.parse(decodeURIComponent(rd.textContent));

                function findComments(obj, depth) {
                    if (depth > 20 || !obj || typeof obj !== 'object') return null;
                    if (Array.isArray(obj) && obj.length > 0) {
                        const first = obj[0];
                        if (first && (first.cid || first.comment_id || first.aweme_id) && (first.text || first.content)) {
                            return obj;
                        }
                    }
                    for (const k in obj) {
                        const found = findComments(obj[k], depth + 1);
                        if (found) return found;
                    }
                    return null;
                }

                const comments = findComments(data, 0);
                if (!comments) return [];

                return comments.map((c, idx) => {
                    const user = c.user || {};
                    const create_time = c.create_time || 0;
                    let time_str = '';
                    if (create_time > 1000000000) {
                        const d = new Date(create_time * 1000);
                        time_str = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0') + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0') + ':' + String(d.getSeconds()).padStart(2,'0');
                    }
                    return {
                        comment_id: String(c.cid || c.comment_id || c.id || ('render_' + idx)),
                        user_name: user.nickname || user.nick_name || '',
                        user_id: String(user.uid || user.sec_uid || ''),
                        comment_text: c.text || c.content || '',
                        like_count: c.digg_count || c.like_count || 0,
                        reply_count: c.reply_comment_total || c.reply_count || 0,
                        publish_time: time_str,
                    };
                }).filter(c => c.comment_text);
            } catch(e) {
                return [];
            }
        }
        """)
        return result or []
    except Exception:
        return []


def _check_reached_bottom(page: Page) -> bool:
    """检查是否到达评论区底部"""
    try:
        bottom_selectors = [
            '[class*="no-more"]',
            '[class*="bottom-tip"]',
            '[class*="NoMore"]',
            '[class*="noMore"]',
            'text=暂时没有更多了',
            'text=已经到底啦',
            'text=没有更多评论了',
        ]
        for selector in bottom_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=500):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def _check_captcha(page: Page) -> bool:
    """检测是否出现验证码"""
    try:
        captcha_selectors = [
            '[class*="captcha"]',
            '[class*="verify"]',
            '[class*="Captcha"]',
            '[class*="Verify"]',
        ]
        for selector in captcha_selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=500):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def _wait_for_captcha_done(page: Page):
    """等待用户手动完成验证码"""
    max_wait = 120
    start = time.time()
    while time.time() - start < max_wait:
        if not _check_captcha(page):
            return
        time.sleep(2)


def _merge_comments(api_comments: List[Dict], dom_comments: List[Dict], target: int) -> List[Dict]:
    """合并评论，API 数据优先，多重去重"""
    seen = set()
    result = []

    for c in api_comments:
        cid = c.get("comment_id", "")
        if cid and cid not in seen:
            seen.add(cid)
            result.append(c)
        if len(result) >= target:
            break

    if len(result) < target:
        for c in dom_comments:
            cid = c.get("comment_id", "")
            if cid and cid not in seen:
                seen.add(cid)
                result.append(c)
            if len(result) >= target:
                break

    return result[:target]


def save_debug_info(page: Page, prefix: str = "debug"):
    """保存调试信息"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=os.path.join(config.DEBUG_DIR, f"{prefix}_{timestamp}.png"))
        html = page.content()
        with open(os.path.join(config.DEBUG_DIR, f"{prefix}_{timestamp}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        with open(os.path.join(config.DEBUG_DIR, f"{prefix}_{timestamp}_url.txt"), "w", encoding="utf-8") as f:
            f.write(page.url)
    except Exception:
        pass
