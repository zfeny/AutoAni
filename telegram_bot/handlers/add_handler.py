"""
添加订阅处理器
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.services.subscription_tracker import SubscriptionTracker
from telegram_bot.keyboards import Keyboards


# 会话状态
WAITING_RSS_URL = 1


async def add_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """添加订阅 - 请求输入 RSS URL"""
    query = update.callback_query
    await query.answer()

    text = (
        "➕ 添加订阅\n\n"
        "请发送蜜柑 RSS URL\n"
        "格式: https://mikanani.me/RSS/Bangumi?bangumiId=xxx&subgroupid=xxx\n\n"
        "或点击取消"
    )

    # 设置会话状态
    context.user_data['waiting_for_rss_url'] = True

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.add_subscription_cancel()
    )


async def rss_url_received_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收到 RSS URL"""
    # 检查是否在等待输入状态
    if not context.user_data.get('waiting_for_rss_url'):
        return

    rss_url = update.message.text.strip()

    # 验证 URL 格式
    if not rss_url.startswith('https://mikanani.me/RSS/Bangumi'):
        await update.message.reply_text(
            "❌ URL 格式错误\n\n请发送正确的蜜柑 RSS URL",
            reply_markup=Keyboards.add_subscription_cancel()
        )
        return

    # 显示解析中
    processing_msg = await update.message.reply_text("🔍 正在解析...")

    # 解析 RSS（但不添加）
    tracker = SubscriptionTracker()

    try:
        # 使用 page_scraper 解析信息
        from src.parsers.page_scraper import MikanPageScraper
        scraper = MikanPageScraper()
        scrape_result = scraper.scrape_bangumi_page_from_rss_url(rss_url)

        if not scrape_result:
            await processing_msg.edit_text(
                "❌ 解析失败\n\n请检查 URL 是否正确",
                reply_markup=Keyboards.add_subscription_cancel()
            )
            return

        series_name = scrape_result.get('series_name')
        img_url = scrape_result.get('img_url')

        # 搜索 TMDB
        tmdb_result = tracker.tmdb_service.search_anime(series_name)

        if not tmdb_result:
            await processing_msg.edit_text(
                f"❌ 未找到 TMDB 信息\n\n番剧: {series_name}",
                reply_markup=Keyboards.add_subscription_cancel()
            )
            return

        tmdb_id = tmdb_result['tmdb_id']
        tmdb_name = tmdb_result['name']

        # 获取详细信息
        details = tracker.tmdb_service.get_series_details(tmdb_id)
        total_episodes = details.get('number_of_episodes') if details else None
        first_air_date = tmdb_result.get('first_air_date') or (details.get('first_air_date') if details else None)

        # 生成季节标签
        season_tag = None
        if first_air_date:
            from src.utils.season_helper import SeasonHelper
            season_tag = SeasonHelper().generate_season_tag(first_air_date)

        # 构建确认文本
        text = (
            "✅ 找到番剧：\n"
            "──────────────\n"
            f"🎬 {tmdb_name}\n"
            f"📅 首播: {first_air_date or 'N/A'}\n"
            f"📺 总集数: {total_episodes or 'N/A'} 集\n"
            f"🏷️ 季节: {season_tag or 'N/A'}\n"
            "──────────────\n\n"
            "确认添加订阅？"
        )

        # 保存信息到 context
        context.user_data['add_rss_url'] = rss_url
        context.user_data['add_series_name'] = series_name
        context.user_data['waiting_for_rss_url'] = False

        # 如果有封面图，发送图片
        if img_url:
            try:
                await processing_msg.delete()
                await update.message.reply_photo(
                    photo=img_url,
                    caption=text,
                    reply_markup=Keyboards.add_subscription_confirm(rss_url)
                )
            except:
                # 图片发送失败，只发文本
                await processing_msg.edit_text(
                    text=text,
                    reply_markup=Keyboards.add_subscription_confirm(rss_url)
                )
        else:
            await processing_msg.edit_text(
                text=text,
                reply_markup=Keyboards.add_subscription_confirm(rss_url)
            )

    except Exception as e:
        await processing_msg.edit_text(
            f"❌ 解析失败\n\n错误: {e}",
            reply_markup=Keyboards.add_subscription_cancel()
        )


async def add_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """确认添加订阅"""
    query = update.callback_query
    await query.answer()

    # 从 callback_data 或 context 获取 RSS URL
    if query.data.startswith("add_confirm_"):
        rss_url = query.data.replace("add_confirm_", "")
    else:
        rss_url = context.user_data.get('add_rss_url')

    if not rss_url:
        await query.edit_message_text(
            "❌ 数据错误，请重新操作",
            reply_markup=Keyboards.back_to_main()
        )
        return

    await query.edit_message_caption(caption="⏳ 正在添加订阅...")

    # 添加订阅
    tracker = SubscriptionTracker()
    success = tracker.add_subscription_by_rss_url(rss_url)

    # 清理 context
    context.user_data.pop('add_rss_url', None)
    context.user_data.pop('add_series_name', None)
    context.user_data.pop('waiting_for_rss_url', None)

    if success:
        text = "✅ 订阅添加成功\n\n可以在「查看订阅」中查看"
    else:
        text = "❌ 订阅添加失败\n\n请查看日志获取详细信息"

    await query.edit_message_caption(
        caption=text,
        reply_markup=Keyboards.back_to_main()
    )
