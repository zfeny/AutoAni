#!/usr/bin/env python3
"""
测试 Telegram Bot 连接
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from telegram import Bot
from telegram.error import TelegramError
from telegram_bot.config import BotConfig


async def test_connection():
    """测试 Bot 连接"""
    print("=== 测试 Telegram Bot 连接 ===\n")

    try:
        # 验证配置
        BotConfig.validate()
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        return

    # 创建 Bot 实例
    bot = Bot(token=BotConfig.BOT_TOKEN)

    try:
        # 获取 Bot 信息
        print("正在连接...")
        me = await bot.get_me()

        print(f"\n✅ 连接成功!\n")
        print(f"Bot 信息:")
        print(f"  用户名: @{me.username}")
        print(f"  名称: {me.first_name}")
        print(f"  ID: {me.id}")
        print(f"\n配置的用户:")
        for user_id in BotConfig.ALLOWED_USERS:
            print(f"  - {user_id}")

        print(f"\n✓ Bot 配置正确，可以运行 python run_bot.py 启动")

    except TelegramError as e:
        print(f"\n✗ 连接失败: {e}")
        print("\n请检查:")
        print("  1. TELEGRAM_BOT_TOKEN 是否正确")
        print("  2. 网络连接是否正常")

    except Exception as e:
        print(f"\n✗ 未知错误: {e}")


if __name__ == '__main__':
    asyncio.run(test_connection())
