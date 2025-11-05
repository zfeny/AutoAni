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
from telegram_bot.handlers import settings_handler as settings_module

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

    has_mismatched = status_stats['mismatched'] > 0

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.system_status_menu(has_mismatched=has_mismatched)
    )


async def view_mismatched_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看不匹配项目"""
    query = update.callback_query
    await query.answer()

    from src.models.database import Database
    db = Database()

    # 获取所有 mismatched 剧集
    mismatched_episodes = db.get_episodes_by_status('mismatched')

    if not mismatched_episodes:
        await query.edit_message_text(
            "✅ 没有不匹配的项目",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 获取 series 信息
    series_map = db.get_series_map()

    # 丰富剧集信息
    for episode in mismatched_episodes:
        series = series_map.get(episode['tmdb_id'])
        if series:
            episode['series_name'] = series['series_name']

    # 分页显示
    page = 0
    items_per_page = 5
    total_pages = (len(mismatched_episodes) + items_per_page - 1) // items_per_page

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = mismatched_episodes[start_idx:end_idx]

    text = f"⚠️ 不匹配项目 ({len(mismatched_episodes)} 个)\n\n点击查看详情："

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.mismatched_list(page_items, page, total_pages)
    )


async def mismatched_page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """不匹配项目翻页"""
    query = update.callback_query
    await query.answer()

    from src.models.database import Database
    db = Database()

    # 解析页码
    page = int(query.data.split('_')[-1])

    # 获取所有 mismatched 剧集
    mismatched_episodes = db.get_episodes_by_status('mismatched')
    series_map = db.get_series_map()

    for episode in mismatched_episodes:
        series = series_map.get(episode['tmdb_id'])
        if series:
            episode['series_name'] = series['series_name']

    # 分页
    items_per_page = 5
    total_pages = (len(mismatched_episodes) + items_per_page - 1) // items_per_page

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = mismatched_episodes[start_idx:end_idx]

    text = f"⚠️ 不匹配项目 ({len(mismatched_episodes)} 个)\n\n点击查看详情："

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.mismatched_list(page_items, page, total_pages)
    )


async def mismatched_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """不匹配项目详情"""
    query = update.callback_query
    await query.answer()

    from src.models.database import Database
    db = Database()

    # 解析 episode_id
    episode_id = int(query.data.replace('mismatched_detail_', ''))

    # 获取剧集信息
    episode = db.get_episode_by_id(episode_id)
    if not episode:
        await query.edit_message_text(
            "❌ 找不到该剧集",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 获取番剧信息
    series_map = db.get_series_map()
    series = series_map.get(episode['tmdb_id'])
    series_name = series['series_name'] if series else 'Unknown'

    text = (
        f"⚠️ 不匹配项目详情\n\n"
        f"🎬 番剧: {series_name}\n"
        f"📺 剧集: EP{episode['episode_number']:02d}\n"
        f"🏷️ TMDB ID: {episode['tmdb_id']}\n\n"
        f"📋 RSS标题:\n{episode.get('rss_title', 'N/A')}\n\n"
        f"🔗 种子链接:\n{episode.get('torrent_link', 'N/A')}\n\n"
        f"ℹ️ 原因: 字幕语言不匹配\n"
        f"期望: 简体中文\n"
        f"实际: {episode.get('subtitle_lang', 'Unknown')}"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.mismatched_detail(episode_id)
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

    # 启动 Bot
    print("✓ Telegram Bot 启动成功")
    print(f"  Token: {BotConfig.BOT_TOKEN[:20]}...")
    print(f"  允许用户: {len(BotConfig.ALLOWED_USERS)} 个")
    print("\n🤖 Bot 运行中... 按 Ctrl+C 停止\n")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
