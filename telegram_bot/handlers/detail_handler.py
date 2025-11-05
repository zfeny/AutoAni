"""
剧集详情处理器
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes

from src.models.database import Database
from telegram_bot.keyboards import Keyboards
from telegram_bot.utils import generate_progress_bar
from telegram_bot.config import BotConfig


async def detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示番剧详情"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 提取 tmdb_id
    tmdb_id = int(query.data.replace("detail_", ""))

    await show_series_detail(query, tmdb_id)


async def refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """刷新番剧详情"""
    query = update.callback_query
    await query.answer("🔄 正在刷新...")

    # 从 callback_data 提取 tmdb_id
    tmdb_id = int(query.data.replace("refresh_", ""))

    await show_series_detail(query, tmdb_id)


async def show_series_detail(query, tmdb_id: int):
    """
    显示番剧详情

    Args:
        query: Telegram query
        tmdb_id: 番剧 TMDB ID
    """
    db = Database()

    # 获取番剧信息
    series_list = db.get_all_series()
    series = next((s for s in series_list if s['tmdb_id'] == tmdb_id), None)

    if not series:
        await query.edit_message_text("❌ 未找到该番剧")
        return

    series_name = series['series_name']
    season_tag = series.get('season_tag', 'N/A')
    total_episodes = series.get('total_episodes', 0)

    # 获取剧集列表
    episodes = db.get_episodes_by_series(tmdb_id)
    episodes.sort(key=lambda x: x['episode_number'])

    # 统计状态
    status_count = {}
    for episode in episodes:
        status = episode.get('status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1

    completed = status_count.get('openlist_exists', 0) + status_count.get('completed', 0)

    # 计算进度百分比
    if total_episodes > 0:
        progress_pct = int(completed / total_episodes * 100)
    else:
        progress_pct = 0 if not episodes else int(completed / len(episodes) * 100)

    # 构建详情文本
    lines = [
        f"🎬 {series_name}",
        f"TMDB: {tmdb_id} | {season_tag}\n",
        f"📊 进度: {completed}/{total_episodes or len(episodes)} 集 ({progress_pct}%)",
        f"{generate_progress_bar(completed, total_episodes or len(episodes), 15)}\n"
    ]

    # 显示前20集的状态
    display_limit = 20
    for i, episode in enumerate(episodes[:display_limit]):
        ep_num = episode['episode_number']
        status = episode.get('status', 'unknown')
        emoji = BotConfig.STATUS_EMOJI.get(status, '❓')

        status_text = {
            'pending': '待下载',
            'downloading': '下载中',
            'openlist_exists': '已下载',
            'completed': '已完成',
            'mismatched': '字幕不匹配'
        }.get(status, '未知')

        lines.append(f"EP{ep_num:02d} {emoji} {status_text}")

    if len(episodes) > display_limit:
        lines.append(f"\n... 还有 {len(episodes) - display_limit} 集")

    text = '\n'.join(lines)

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.series_detail(tmdb_id)
    )
