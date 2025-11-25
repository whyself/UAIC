"""
爬虫模块的统一配置文件。
本文件集中管理所有爬虫相关参数，包括目标网站、数据库路径、定时任务、OCR、环境变量等。
所有配置项均可通过环境变量覆盖，方便部署和调试。
"""
from __future__ import annotations  # 兼容未来类型注解语法

import os  # 用于读取环境变量，实现灵活配置
import json
import glob

def _get_bool_env(name: str, default: bool) -> bool:
    """
    读取布尔型环境变量，支持多种写法（1/true/yes/on），无则返回默认值。
    用于控制定时任务、同步开关等布尔配置。
    """
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

CRAWL_INTERVAL = int(os.getenv("CRAWL_INTERVAL", "3600"))  # 定时抓取间隔（秒），默认1小时
REQUEST_TIMEOUT = 30  # 单次请求超时时间（秒）
MAX_RETRIES = 3       # 网络请求最大重试次数
AUTO_CRAWL_ENABLED = _get_bool_env("AUTO_CRAWL_ENABLED", True)  # 是否启用定时自动抓取

VECTOR_SYNC_ENABLED = _get_bool_env("VECTOR_SYNC_ENABLED", True)  # 是否自动同步爬取内容到向量库

TESSERACT_CMD = ""  # OCR工具tesseract命令路径，可用环境变量覆盖
TESSDATA_DIR = ""   # OCR数据目录路径，可用环境变量覆盖

DATABASE_PATH = os.getenv("CRAWLER_DB_PATH", "./data/crawler.db")  # SQLite数据库文件路径

# 动态加载配置
TARGET_SOURCES = []
DETAIL_SELECTORS = []

def load_configurations():
    """
    从 config/sources/ 目录加载所有 JSON 配置文件。
    """
    global TARGET_SOURCES, DETAIL_SELECTORS
    
    # 获取当前文件所在目录的上级目录，即项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, "config", "sources")
    
    if not os.path.exists(config_dir):
        print(f"[WARN] Config directory not found: {config_dir}")
        return

    json_files = glob.glob(os.path.join(config_dir, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "sources" in data:
                    TARGET_SOURCES.extend(data["sources"])
                if "detail_selectors" in data:
                    DETAIL_SELECTORS.extend(data["detail_selectors"])
        except Exception as e:
            print(f"[ERROR] Failed to load config file {file_path}: {e}")

# 初始化加载
load_configurations()

