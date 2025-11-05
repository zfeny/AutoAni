"""
Telegram 通知服务
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from typing import List

from telegram_bot.config import BotConfig


class TelegramNotifier:
    """Telegram 通知器"""

    def __init__(self):
        self.bot = Bot(token=BotConfig.BOT_TOKEN)

    async def send_download_complete_notification(self, series_name: str, episode_number: int, user_ids: List[int] = None):
        """
        发送下载完成通知

        Args:
            series_name: 番剧名称
            episode_number: 集数
            user_ids: 接收通知的用户 ID 列表（默认为所有允许的用户）
        """
        if user_ids is None:
            user_ids = BotConfig.ALLOWED_USERS

        text = (
            f"✅ 下载完成\n\n"
            f"🎬 {series_name}\n"
            f"📺 EP{episode_number:02d}\n\n"
            f"已添加到 OpenList"
        )

        for user_id in user_ids:
            try:
                await self.bot.send_message(chat_id=user_id, text=text)
            except TelegramError as e:
                print(f"发送通知失败 (用户 {user_id}): {e}")

    async def send_batch_complete_notification(self, completed_items: List[dict], user_ids: List[int] = None):
        """
        发送批量下载完成通知

        Args:
            completed_items: 完成的剧集列表 [{series_name, episode_number}, ...]
            user_ids: 接收通知的用户 ID 列表
        """
        if not completed_items:
            return

        if user_ids is None:
            user_ids = BotConfig.ALLOWED_USERS

        # 按番剧分组
        series_groups = {}
        for item in completed_items:
            series_name = item['series_name']
            ep_num = item['episode_number']

            if series_name not in series_groups:
                series_groups[series_name] = []
            series_groups[series_name].append(ep_num)

        # 构建通知文本
        lines = [f"✅ 下载完成 ({len(completed_items)} 集)\n"]

        for series_name, episodes in series_groups.items():
            episodes.sort()
            ep_list = ', '.join([f"EP{ep:02d}" for ep in episodes])
            lines.append(f"🎬 {series_name}")
            lines.append(f"   {ep_list}\n")

        text = '\n'.join(lines)

        for user_id in user_ids:
            try:
                await self.bot.send_message(chat_id=user_id, text=text)
            except TelegramError as e:
                print(f"发送批量通知失败 (用户 {user_id}): {e}")

    def send_notification_sync(self, series_name: str, episode_number: int):
        """
        同步版本的发送通知（用于非异步环境）

        Args:
            series_name: 番剧名称
            episode_number: 集数
        """
        try:
            asyncio.run(self.send_download_complete_notification(series_name, episode_number))
        except Exception as e:
            print(f"发送通知失败: {e}")

    def send_notification_sync_batch(self, completed_items: List[dict]):
        """
        同步版本的批量发送通知（用于非异步环境）

        Args:
            completed_items: 完成的剧集列表
        """
        try:
            asyncio.run(self.send_batch_complete_notification(completed_items))
        except Exception as e:
            print(f"发送批量通知失败: {e}")
