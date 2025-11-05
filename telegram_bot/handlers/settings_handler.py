"""
设置页处理器
支持定时任务配置和手动触发
"""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram_bot.keyboards import Keyboards
from telegram_bot.utils import is_authorized
from src.utils.scheduler_config import SchedulerConfig


# 任务名称映射
TASK_NAME_MAP = {
    'rss_scrape': '📡 RSS刮削',
    'push_download': '📥 推送下载',
    'check_complete': '✅ 检测完成',
    'check_failed': '❌ 检测失败',
    'scrape_episodes': '📺 刮削剧集',
}


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置菜单"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    text = "⚙️ 设置\n\n请选择操作："

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.settings_menu()
    )


async def settings_scheduler_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """定时任务设置"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    # 加载当前配置
    config = SchedulerConfig.load_config()

    text = (
        "⏰ 定时任务设置\n\n"
        "当前配置:\n"
        f"📡 RSS刮削间隔: {config['rss_scrape_interval']} 分钟\n"
        f"📥 推送下载间隔: {config['push_download_interval']} 分钟\n"
        f"✅ 检测完成间隔: {config['check_complete_interval']} 分钟\n"
        f"❌ 检测失败间隔: {config['check_failed_interval']} 分钟\n\n"
        "点击按钮修改间隔时间："
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.scheduler_settings()
    )


async def set_interval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置间隔 - 请求输入"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    # 解析任务名称
    task_name = query.data.replace("set_interval_", "")

    # 保存到 context
    context.user_data['setting_interval_for'] = task_name

    task_display = TASK_NAME_MAP.get(task_name, task_name)

    text = (
        f"⏰ 设置 {task_display} 间隔\n\n"
        "请输入新的间隔时间（分钟）：\n"
        "例如: 30\n\n"
        "最小值: 1 分钟"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.interval_input_cancel(task_name)
    )


async def interval_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理间隔输入"""
    if not is_authorized(update.message.from_user.id):
        await update.message.reply_text("⛔ 无权限")
        return

    task_name = context.user_data.get('setting_interval_for')
    if not task_name:
        return

    # 清除状态
    del context.user_data['setting_interval_for']

    # 解析输入
    try:
        interval = int(update.message.text.strip())
        if interval < 1:
            raise ValueError("间隔必须 >= 1")
    except:
        await update.message.reply_text(
            "❌ 输入无效，请输入大于等于1的整数",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 更新配置
    config_key = f"{task_name}_interval"
    if not SchedulerConfig.update_interval(config_key, interval):
        await update.message.reply_text(
            "❌ 更新失败",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 通知调度器更新
    scheduler = context.bot_data.get('scheduler')
    if scheduler:
        scheduler.update_task_interval(task_name, interval)

    task_display = TASK_NAME_MAP.get(task_name, task_name)

    await update.message.reply_text(
        f"✅ {task_display} 间隔已更新为 {interval} 分钟",
        reply_markup=Keyboards.back_to_main()
    )


async def reset_scheduler_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """重置为默认配置"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    # 重置配置
    if not SchedulerConfig.reset_to_default():
        await query.edit_message_text(
            "❌ 重置失败",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 重新加载调度器配置
    scheduler = context.bot_data.get('scheduler')
    if scheduler:
        config = SchedulerConfig.load_config()
        for task_name in ['rss_scrape', 'push_download', 'check_complete', 'check_failed']:
            scheduler.update_task_interval(task_name, config[f"{task_name}_interval"])

    await query.edit_message_text(
        "✅ 已重置为默认配置",
        reply_markup=Keyboards.back_to_main()
    )


async def settings_trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """手动触发任务菜单"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    text = (
        "▶️ 手动执行任务\n\n"
        "点击按钮立即执行对应任务：\n"
        "⚠️ 任务会在后台执行，请稍后查看系统状态"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=Keyboards.trigger_task_menu()
    )


async def trigger_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """触发任务"""
    query = update.callback_query
    await query.answer("⏳ 任务已加入执行队列...")

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("⛔ 无权限")
        return

    # 解析任务名称
    task_name = query.data.replace("trigger_", "")

    task_display = TASK_NAME_MAP.get(task_name, task_name)

    # 获取调度器
    scheduler = context.bot_data.get('scheduler')
    if not scheduler:
        await query.edit_message_text(
            "❌ 调度器未运行",
            reply_markup=Keyboards.back_to_main()
        )
        return

    # 触发任务
    await query.edit_message_text(
        f"▶️ 正在执行 {task_display}...\n\n"
        "请稍候，任务完成后会显示结果",
        reply_markup=Keyboards.trigger_task_menu()
    )

    # 异步执行任务
    success = await scheduler.trigger_task(task_name)

    if success:
        await query.edit_message_text(
            f"✅ {task_display} 执行完成\n\n"
            "可以通过「系统状态」查看结果",
            reply_markup=Keyboards.back_to_main()
        )
    else:
        await query.edit_message_text(
            f"❌ {task_display} 执行失败",
            reply_markup=Keyboards.back_to_main()
        )


# 注册处理器的辅助函数
def register_handlers(application):
    """注册所有设置相关处理器"""
    # 设置菜单
    application.add_handler(CallbackQueryHandler(settings_handler, pattern="^settings$"))

    # 定时任务设置
    application.add_handler(CallbackQueryHandler(settings_scheduler_handler, pattern="^settings_scheduler$"))
    application.add_handler(CallbackQueryHandler(set_interval_handler, pattern="^set_interval_"))
    application.add_handler(CallbackQueryHandler(reset_scheduler_config_handler, pattern="^reset_scheduler_config$"))

    # 间隔输入处理（仅当 setting_interval_for 存在时）
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+$'),
        interval_input_handler
    ))

    # 手动触发任务
    application.add_handler(CallbackQueryHandler(settings_trigger_handler, pattern="^settings_trigger$"))
    application.add_handler(CallbackQueryHandler(trigger_task_handler, pattern="^trigger_"))
