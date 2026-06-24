"""
全局配置常量
"""
import os

# === 路径配置 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
COOKIE_FILE = os.path.join(DATA_DIR, "cookies.json")
DEBUG_DIR = os.path.join(DATA_DIR, "debug")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# === 抖音配置 ===
DOUYIN_DOMAIN = "https://www.douyin.com"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# === 抓取参数 ===
MAX_SCROLL_TIMES = 100          # 最大滚动次数
SCROLL_WAIT_SEC = 3.5           # 每次滚动后等待秒数（增加到3.5s）
NO_NEW_SCROLL_LIMIT = 10        # 连续无新内容则停止
PAGE_LOAD_TIMEOUT = 60000       # 页面加载超时(ms)（增加到60s）
DEFAULT_TARGET_COUNT = 200      # 默认抓取评论数

# === 浏览器配置 ===
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
