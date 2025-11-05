"""
删除订阅处理器
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes

from src.models.database import Database
from src.services.subscription_manager import SubscriptionManager
from telegram_bot.keyboards import Keyboards


async def delete_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除确认"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 提取 tmdb_id
    tmdb_id = int(query.data.replace("delete_confirm_", ""))

    db = Database()

    # 获取番剧信息
    series_list = db.get_all_series()
    series = next((s for s in series_list if s['tmdb_id'] == tmdb_id), None)

    if not series:
        await query.edit_message_text("❌ 未找到该番剧")
        return

    series_name = series['series_name']

    # 获取统计信息
    manager = SubscriptionManager()
    stats = manager.get_series_stats(tmdb_id)

    text = (
        f"⚠️ 确认删除订阅？\n\n"
        f"番剧: {series_name}\n"
        f"剧集记录: {stats['total_episodes']} 条\n"
        f"已下载文件: {stats['downloaded_files']} 个\n\n"
        f"是否同时删除已下载的文件？"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.delete_confirmation(tmdb_id)
    )


async def delete_with_files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除订阅+文件"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 提取 tmdb_id
    tmdb_id = int(query.data.replace("delete_with_files_", ""))

    await query.edit_message_text("🗑️ 正在删除订阅和文件...")

    manager = SubscriptionManager()
    success, deleted_files, error = manager.delete_subscription(tmdb_id, delete_files=True)

    if success:
        text = (
            f"✅ 删除成功\n\n"
            f"已删除文件: {deleted_files} 个"
        )
    else:
        text = f"❌ 删除失败\n\n{error}"

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )


async def delete_only_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """仅删除订阅"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 提取 tmdb_id
    tmdb_id = int(query.data.replace("delete_only_", ""))

    await query.edit_message_text("📝 正在删除订阅（保留文件）...")

    manager = SubscriptionManager()
    success, _, error = manager.delete_subscription(tmdb_id, delete_files=False)

    if success:
        text = "✅ 订阅已删除\n\n已下载的文件已保留"
    else:
        text = f"❌ 删除失败\n\n{error}"

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.back_to_main()
    )
