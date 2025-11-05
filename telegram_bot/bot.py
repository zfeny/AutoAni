"""
Telegram Bot 主程序
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from telegram_bot.config import BotConfig
from telegram_bot.keyboards import Keyboards

# 导入 handlers
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

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def auth_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE, handler):
    """用户认证中间件"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        if update.callback_query:
            await update.callback_query.answer("⛔ 无权限", show_alert=True)
        elif update.message:
            await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    # 继续执行
    return await handler(update, context)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令处理"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    text = (
        "🎬 AutoAni 番剧管理\n\n"
        "欢迎使用番剧订阅管理 Bot\n"
        "请选择功能："
    )

    await update.message.reply_text(
        text=text,
        reply_markup=Keyboards.main_menu()
    )


async def series_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令：/series - 查看订阅"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    text = "📺 我的订阅\n\n请选择分类："

    await update.message.reply_text(
        text=text,
        reply_markup=Keyboards.series_menu()
    )


async def add_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令：/add - 添加订阅"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    text = (
        "➕ 添加订阅\n\n"
        "请发送蜜柑 RSS URL\n"
        "格式: https://mikanani.me/RSS/Bangumi?bangumiId=xxx&subgroupid=xxx\n\n"
        "或点击取消"
    )

    # 设置会话状态
    context.user_data['waiting_for_rss_url'] = True

    await update.message.reply_text(
        text=text,
        reply_markup=Keyboards.add_subscription_cancel()
    )


async def status_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令：/status - 系统状态"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    from src.models.database import Database
    db = Database()

    # 获取统计信息
    series_list = db.get_all_series()
    total_series = len(series_list)

    total_episodes = 0
    for series in series_list:
        episodes = db.get_episodes_by_series(series['tmdb_id'])
        total_episodes += len(episodes)

    # 状态分布
    statuses = ['pending', 'downloading', 'openlist_exists', 'completed', 'mismatched']
    status_stats = {}
    for status in statuses:
        episodes = db.get_episodes_by_status(status)
        status_stats[status] = len(episodes)

    openlist_files = db.get_openlist_files()

    text = (
        "📊 系统状态\n\n"
        f"订阅数: {total_series}\n"
        f"总剧集数: {total_episodes}\n\n"
        "剧集状态分布:\n"
        f"  ⏳ 待下载: {status_stats['pending']} 集\n"
        f"  ⬇️ 下载中: {status_stats['downloading']} 集\n"
        f"  ✅ 已下载: {status_stats['openlist_exists']} 集\n"
        f"  ⚠️ 不匹配: {status_stats['mismatched']} 集\n\n"
        f"OpenList 文件数: {len(openlist_files)}"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )


async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令：/help - 帮助信息"""
    user_id = update.effective_user.id

    if user_id not in BotConfig.ALLOWED_USERS:
        await update.message.reply_text("⛔ 无权限使用此 Bot")
        return

    text = (
        "🤖 AutoAni Bot 帮助\n\n"
        "📺 查看订阅\n"
        "  /series - 查看所有订阅\n"
        "  🆕 新番 - 当前季度番剧\n"
        "  📚 老番 - 历史季度番剧\n\n"
        "➕ 添加订阅\n"
        "  /add - 通过 RSS URL 添加\n\n"
        "📊 系统状态\n"
        "  /status - 查看统计信息\n\n"
        "💡 使用技巧\n"
        "  • 在剧集详情页可以删除订阅\n"
        "  • 删除时可选择是否保留文件\n"
        "  • 下载完成会自动通知\n\n"
        "需要帮助？发送 /help\n"
        "查看详细文档：TELEGRAM_BOT.md"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """主菜单处理"""
    query = update.callback_query
    await query.answer()

    text = (
        "🎬 AutoAni 番剧管理\n\n"
        "选择功能："
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.main_menu()
    )


async def system_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """系统状态处理"""
    query = update.callback_query
    await query.answer()

    from src.models.database import Database
    db = Database()

    # 获取统计信息
    series_list = db.get_all_series()
    total_series = len(series_list)

    total_episodes = 0
    for series in series_list:
        episodes = db.get_episodes_by_series(series['tmdb_id'])
        total_episodes += len(episodes)

    # 状态分布
    statuses = ['pending', 'downloading', 'openlist_exists', 'completed', 'mismatched']
    status_stats = {}
    for status in statuses:
        episodes = db.get_episodes_by_status(status)
        status_stats[status] = len(episodes)

    openlist_files = db.get_openlist_files()

    text = (
        "📊 系统状态\n\n"
        f"订阅数: {total_series}\n"
        f"总剧集数: {total_episodes}\n\n"
        "剧集状态分布:\n"
        f"  ⏳ 待下载: {status_stats['pending']} 集\n"
        f"  ⬇️ 下载中: {status_stats['downloading']} 集\n"
        f"  ✅ 已下载: {status_stats['openlist_exists']} 集\n"
        f"  ⚠️ 不匹配: {status_stats['mismatched']} 集\n\n"
        f"OpenList 文件数: {len(openlist_files)}"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置处理"""
    query = update.callback_query
    await query.answer()

    text = "⚙️ 设置\n\n功能开发中..."

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )


async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """空操作处理（用于分页页码显示）"""
    query = update.callback_query
    await query.answer()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """错误处理"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.callback_query:
        await update.callback_query.answer("❌ 发生错误，请重试", show_alert=True)
    elif update and update.message:
        await update.message.reply_text("❌ 发生错误，请重试")


def main():
    """主函数"""
    # 验证配置
    try:
        BotConfig.validate()
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        sys.exit(1)

    # 创建 Application
    application = Application.builder().token(BotConfig.BOT_TOKEN).build()

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
    application.add_handler(CallbackQueryHandler(settings_handler, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(noop_handler, pattern="^noop$"))

    # 注册消息处理器（用于接收 RSS URL）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rss_url_received_handler))

    # 注册错误处理器
    application.add_error_handler(error_handler)

    # 启动 Bot
    print("✓ Telegram Bot 启动成功")
    print(f"  Token: {BotConfig.BOT_TOKEN[:20]}...")
    print(f"  允许用户: {len(BotConfig.ALLOWED_USERS)} 个")
    print("\n🤖 Bot 运行中... 按 Ctrl+C 停止\n")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
