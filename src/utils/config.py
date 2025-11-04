"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """配置类"""

    # 蜜柑计划配置
    MIKAN_RSS_TOKEN = os.getenv('MIKAN_RSS_TOKEN')
    MIKAN_RSS_URL = f"https://mikanani.me/RSS/MyBangumi?token={MIKAN_RSS_TOKEN}"

    # TMDB 配置
    TMDB_API_KEY = os.getenv('TMDB_API_KEY')

    # 任务配置
    RSS_FETCH_INTERVAL = int(os.getenv('RSS_FETCH_INTERVAL', 30))

    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/autoani.db')

    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent.parent

    # OpenList 配置
    OPENLIST_URL = os.getenv('OPENLIST_URL')
    OPENLIST_ACCOUNT = os.getenv('OPENLIST_ACCOUNT')
    OPENLIST_PASSWORD = os.getenv('OPENLIST_PASSWORD')
    OPENLIST_DIR = os.getenv('OPENLIST_DIR', '/Animate/Bangumi')

    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.MIKAN_RSS_TOKEN:
            raise ValueError("MIKAN_RSS_TOKEN not set in .env")
        if not cls.TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY not set in .env")
