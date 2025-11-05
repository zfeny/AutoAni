#!/usr/bin/env python3
"""
Telegram Bot 启动脚本
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from telegram_bot.bot import main

if __name__ == '__main__':
    main()
