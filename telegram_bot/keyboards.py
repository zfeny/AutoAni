"""
Telegram Bot 键盘定义
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


class Keyboards:
    """键盘工厂类"""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """主菜单键盘"""
        keyboard = [
            [
                InlineKeyboardButton("📺 查看订阅", callback_data="series_menu"),
                InlineKeyboardButton("➕ 添加订阅", callback_data="add_subscription")
            ],
            [
                InlineKeyboardButton("📊 系统状态", callback_data="system_status"),
                InlineKeyboardButton("⚙️ 设置", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def series_menu() -> InlineKeyboardMarkup:
        """订阅分类菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🆕 新番", callback_data="series_current"),
                InlineKeyboardButton("📚 老番", callback_data="series_old")
            ],
            [InlineKeyboardButton("⬅️ 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def season_selector(seasons: List[str]) -> InlineKeyboardMarkup:
        """季节选择器"""
        keyboard = []

        # 每行2个按钮
        for i in range(0, len(seasons), 2):
            row = []
            for season in seasons[i:i+2]:
                row.append(InlineKeyboardButton(
                    season,
                    callback_data=f"season_{season}"
                ))
            keyboard.append(row)

        # 返回按钮
        keyboard.append([InlineKeyboardButton("⬅️ 返回", callback_data="series_menu")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def series_list(series_items: List[Dict], page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """
        番剧列表键盘

        Args:
            series_items: 番剧列表
            page: 当前页
            total_pages: 总页数
            prefix: 回调前缀（用于区分不同列表）
        """
        keyboard = []

        # 番剧按钮
        for item in series_items:
            tmdb_id = item['tmdb_id']
            series_name = item['series_name']

            # 截断过长的名称
            display_name = series_name if len(series_name) <= 25 else series_name[:25] + '...'

            keyboard.append([
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"detail_{tmdb_id}"
                )
            ])

        # 分页按钮
        if total_pages > 1:
            pagination = []
            if page > 0:
                pagination.append(InlineKeyboardButton("⬅️ 上一页", callback_data=f"{prefix}_page_{page-1}"))
            pagination.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                pagination.append(InlineKeyboardButton("下一页 ▶️", callback_data=f"{prefix}_page_{page+1}"))
            keyboard.append(pagination)

        # 返回按钮
        keyboard.append([InlineKeyboardButton("⬅️ 返回", callback_data="series_menu")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def series_detail(tmdb_id: int) -> InlineKeyboardMarkup:
        """番剧详情键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新状态", callback_data=f"refresh_{tmdb_id}"),
                InlineKeyboardButton("🗑️ 删除订阅", callback_data=f"delete_confirm_{tmdb_id}")
            ],
            [InlineKeyboardButton("⬅️ 返回列表", callback_data="series_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def delete_confirmation(tmdb_id: int) -> InlineKeyboardMarkup:
        """删除确认键盘"""
        keyboard = [
            [InlineKeyboardButton("🗑️ 删除订阅+文件", callback_data=f"delete_with_files_{tmdb_id}")],
            [InlineKeyboardButton("📝 仅删除订阅", callback_data=f"delete_only_{tmdb_id}")],
            [InlineKeyboardButton("❌ 取消", callback_data=f"detail_{tmdb_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def add_subscription_cancel() -> InlineKeyboardMarkup:
        """添加订阅取消键盘"""
        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data="main_menu")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def add_subscription_confirm(url: str) -> InlineKeyboardMarkup:
        """添加订阅确认键盘"""
        keyboard = [
            [InlineKeyboardButton("✅ 确认添加", callback_data=f"add_confirm_{url}")],
            [InlineKeyboardButton("❌ 取消", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """返回主菜单键盘"""
        keyboard = [[InlineKeyboardButton("⬅️ 返回主菜单", callback_data="main_menu")]]
        return InlineKeyboardMarkup(keyboard)
