"""
查看订阅处理器
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes
from typing import List, Dict

from src.models.database import Database
from src.utils.season_helper import SeasonHelper
from telegram_bot.keyboards import Keyboards
from telegram_bot.utils import generate_progress_bar, format_status_summary, format_episode_status
from telegram_bot.config import BotConfig


async def series_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """订阅菜单处理"""
    query = update.callback_query
    await query.answer()

    text = "📺 我的订阅\n\n请选择分类："

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.series_menu()
    )


async def series_current_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看新番（当前季度）"""
    query = update.callback_query
    await query.answer()

    db = Database()
    season_helper = SeasonHelper()

    # 获取当前季度标签
    current_season = season_helper.get_current_season_tag()

    # 获取所有订阅
    all_series = db.get_all_series(status='active')

    # 筛选当前季度
    current_series = [s for s in all_series if s.get('season_tag') == current_season]

    if not current_series:
        text = f"🆕 {current_season}\n\n暂无新番订阅"
        await query.edit_message_text(
            text=text,
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 存储到 context 以便分页使用
    context.user_data['current_series_list'] = current_series
    context.user_data['current_season'] = current_season

    # 显示第一页
    await show_series_page(query, context, current_series, 0, f"🆕 {current_season}", "series_current")


async def series_old_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看老番 - 显示季节选择器"""
    query = update.callback_query
    await query.answer()

    db = Database()
    season_helper = SeasonHelper()

    # 获取当前季度
    current_season = season_helper.get_current_season_tag()

    # 获取所有订阅
    all_series = db.get_all_series(status='active')

    # 获取所有非当前季度的 season_tag（去重）
    old_seasons = set()
    for series in all_series:
        season_tag = series.get('season_tag')
        if season_tag and season_tag != current_season:
            old_seasons.add(season_tag)

    if not old_seasons:
        text = "📚 老番\n\n暂无老番订阅"
        await query.edit_message_text(
            text=text,
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 排序（降序，最新的在前）
    sorted_seasons = sorted(list(old_seasons), reverse=True)

    # 存储到 context
    context.user_data['old_seasons'] = sorted_seasons
    context.user_data['all_series'] = all_series

    text = f"📚 老番\n\n共 {len(sorted_seasons)} 个季度，请选择："

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.season_selector(sorted_seasons)
    )


async def season_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """季节筛选处理"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 提取季节标签
    season_tag = query.data.replace("season_", "")

    # 从 context 获取所有订阅
    all_series = context.user_data.get('all_series', [])

    # 筛选指定季节
    season_series = [s for s in all_series if s.get('season_tag') == season_tag]

    if not season_series:
        text = f"📚 {season_tag}\n\n该季度暂无订阅"
        await query.edit_message_text(
            text=text,
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 存储到 context 以便分页使用
    context.user_data['season_series_list'] = season_series
    context.user_data['selected_season'] = season_tag

    # 显示第一页
    await show_series_page(query, context, season_series, 0, f"📚 {season_tag}", f"season_{season_tag}")


async def show_series_page(query, context, series_list: List[Dict], page: int, title: str, prefix: str):
    """
    显示番剧列表页

    Args:
        query: Telegram query
        context: Context
        series_list: 番剧列表
        page: 页码
        title: 标题
        prefix: 回调前缀
    """
    db = Database()

    # 分页
    page_size = BotConfig.PAGE_SIZE
    total_pages = (len(series_list) + page_size - 1) // page_size
    start = page * page_size
    end = start + page_size
    page_items = series_list[start:end]

    # 构建文本
    lines = [f"{title} ({len(series_list)}部)\n"]

    for series in page_items:
        tmdb_id = series['tmdb_id']
        series_name = series['series_name']

        # 获取剧集统计
        episodes = db.get_episodes_by_series(tmdb_id)
        total = series.get('total_episodes', len(episodes))

        # 计算完成度
        stats = format_episode_status(episodes)
        completed = stats.get('openlist_exists', 0) + stats.get('completed', 0)

        # 进度条
        progress_bar = generate_progress_bar(completed, total)

        # 状态摘要
        status_summary = format_status_summary(stats)

        lines.append(f"┌─────────────────────")
        lines.append(f"│ 🎯 {series_name}")
        lines.append(f"│ 进度: {progress_bar} {completed}/{total}")
        lines.append(f"│ 状态: {status_summary}")
        lines.append(f"└─────────────────────\n")

    text = '\n'.join(lines)

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.series_list(page_items, page, total_pages, prefix)
    )


async def series_page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """分页处理"""
    query = update.callback_query
    await query.answer()

    # 解析 callback_data: prefix_page_N
    parts = query.data.split('_')
    page = int(parts[-1])
    prefix = '_'.join(parts[:-2])

    # 根据 prefix 确定使用哪个列表
    if prefix == "series_current":
        series_list = context.user_data.get('current_series_list', [])
        title = f"🆕 {context.user_data.get('current_season', '')}"
    elif prefix.startswith("season_"):
        series_list = context.user_data.get('season_series_list', [])
        title = f"📚 {context.user_data.get('selected_season', '')}"
    else:
        await query.edit_message_text("❌ 数据错误，请重新选择")
        return

    await show_series_page(query, context, series_list, page, title, prefix)
