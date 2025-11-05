"""
Telegram Bot 配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Bot 配置类"""

    # Bot Token
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # 允许的用户 ID 列表
    ALLOWED_USERS = [
        int(uid.strip())
        for uid in os.getenv('TELEGRAM_ALLOWED_USERS', '').split(',')
        if uid.strip()
    ]

    # 每页显示的番剧数量
    PAGE_SIZE = 5

    # 状态图标映射
    STATUS_EMOJI = {
        'pending': '⏳',
        'downloading': '⬇️',
        'openlist_exists': '✅',
        'completed': '✅',
        'mismatched': '⚠️'
    }

    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN 未配置")

        if not cls.ALLOWED_USERS:
            raise ValueError("TELEGRAM_ALLOWED_USERS 未配置")

        print(f"✓ Bot 配置验证通过")
        print(f"  允许的用户: {len(cls.ALLOWED_USERS)} 个")
