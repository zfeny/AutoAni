#!/usr/bin/env python3
"""
AutoAni 统一启动入口
同时启动 Telegram Bot 和后台调度器
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

import logging
from telegram import Update
from telegram.ext import Application

from telegram_bot.config import BotConfig
from src.scheduler_async import AsyncScheduler
from src.models.database import Database
from src.utils.config import Config


# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """初始化后回调 - 启动调度器"""
    print("\n" + "="*60)
    print("初始化调度器...")
    print("="*60)

    # 创建调度器
    scheduler = AsyncScheduler()

    # 保存到 bot_data，供设置页使用
    application.bot_data['scheduler'] = scheduler

    # 启动调度器
    scheduler.start()

    print("\n✓ 调度器启动成功")


async def post_shutdown(application: Application):
    """关闭前回调 - 停止调度器"""
    scheduler = application.bot_data.get('scheduler')
    if scheduler:
        scheduler.stop()
        print("\n✓ 调度器已停止")


def init_system():
    """初始化系统"""
    print("\n" + "="*60)
    print("AutoAni 系统初始化")
    print("="*60)

    # 验证配置
    try:
        Config.validate()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        sys.exit(1)

    try:
        BotConfig.validate()
        print("✓ Bot 配置验证通过")
    except ValueError as e:
        print(f"✗ Bot 配置错误: {e}")
        sys.exit(1)

    # 初始化数据库
    db = Database()
    db.init_db()
    print("✓ 数据库初始化完成")


def main():
    """主函数"""
    # 初始化
    init_system()

    # 构建 Bot Application
    from telegram_bot.bot import main as bot_main_builder
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

    # 导入所有处理器
    from telegram_bot.handlers.series_handler import (
        series_menu_handler,
        series_current_handler,
        series_old_handler,
        season_filter_handler,
        series_page_handler
    )
    from telegram_bot.handlers.detail_handler import (
        detail_handler,
        refresh_handler
    )
    from telegram_bot.handlers.add_handler import (
        add_subscription_handler,
        rss_url_received_handler,
        add_confirm_handler
    )
    from telegram_bot.handlers.delete_handler import (
        delete_confirm_handler,
        delete_with_files_handler,
        delete_only_handler
    )
    from telegram_bot.handlers import settings_handler as settings_module
    from telegram_bot.bot import (
        start_handler,
        series_command_handler,
        add_command_handler,
        status_command_handler,
        help_command_handler,
        main_menu_handler,
        system_status_handler,
        view_mismatched_handler,
        mismatched_page_handler,
        mismatched_detail_handler,
        noop_handler,
        error_handler
    )
    from telegram_bot.keyboards import Keyboards

    print("\n" + "="*60)
    print("启动 Telegram Bot")
    print("="*60)

    # 创建 Application
    application = (
        Application.builder()
        .token(BotConfig.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("series", series_command_handler))
    application.add_handler(CommandHandler("add", add_command_handler))
    application.add_handler(CommandHandler("status", status_command_handler))
    application.add_handler(CommandHandler("help", help_command_handler))

    # 注册回调查询处理器
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(series_menu_handler, pattern="^series_menu$"))
    application.add_handler(CallbackQueryHandler(series_current_handler, pattern="^series_current$"))
    application.add_handler(CallbackQueryHandler(series_old_handler, pattern="^series_old$"))
    application.add_handler(CallbackQueryHandler(season_filter_handler, pattern="^season_"))
    application.add_handler(CallbackQueryHandler(series_page_handler, pattern=".*_page_\\d+$"))
    application.add_handler(CallbackQueryHandler(detail_handler, pattern="^detail_\\d+$"))
    application.add_handler(CallbackQueryHandler(refresh_handler, pattern="^refresh_\\d+$"))
    application.add_handler(CallbackQueryHandler(delete_confirm_handler, pattern="^delete_confirm_\\d+$"))
    application.add_handler(CallbackQueryHandler(delete_with_files_handler, pattern="^delete_with_files_\\d+$"))
    application.add_handler(CallbackQueryHandler(delete_only_handler, pattern="^delete_only_\\d+$"))
    application.add_handler(CallbackQueryHandler(add_subscription_handler, pattern="^add_subscription$"))
    application.add_handler(CallbackQueryHandler(add_confirm_handler, pattern="^add_confirm_"))
    application.add_handler(CallbackQueryHandler(system_status_handler, pattern="^system_status$"))
    application.add_handler(CallbackQueryHandler(view_mismatched_handler, pattern="^view_mismatched$"))
    application.add_handler(CallbackQueryHandler(mismatched_page_handler, pattern="^mismatched_page_\\d+$"))
    application.add_handler(CallbackQueryHandler(mismatched_detail_handler, pattern="^mismatched_detail_\\d+$"))
    application.add_handler(CallbackQueryHandler(noop_handler, pattern="^noop$"))

    # 注册设置页处理器
    settings_module.register_handlers(application)

    # 注册消息处理器（用于接收 RSS URL）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rss_url_received_handler))

    # 注册错误处理器
    application.add_error_handler(error_handler)

    # 启动信息
    print(f"\n✓ Bot Token: {BotConfig.BOT_TOKEN[:20]}...")
    print(f"✓ 允许用户: {len(BotConfig.ALLOWED_USERS)} 个")

    print("\n" + "="*60)
    print("🚀 AutoAni 系统已启动")
    print("="*60)
    print("\n📌 功能列表:")
    print("  • Telegram Bot 监听")
    print("  • 定时 RSS 刮削")
    print("  • 定时推送下载")
    print("  • 定时检测下载完成")
    print("  • 定时检测下载失败")
    print("\n💡 可通过 Bot 设置页修改定时任务间隔")
    print("\n🛑 按 Ctrl+C 停止系统\n")

    # 运行 Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n系统已停止")
        sys.exit(0)
