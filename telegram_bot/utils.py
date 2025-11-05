"""
Telegram Bot 工具函数
"""
from typing import List, Dict
from telegram_bot.config import BotConfig


def generate_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    生成进度条

    Args:
        current: 当前进度
        total: 总数
        length: 进度条长度

    Returns:
        str: 进度条字符串 ▓▓▓░░░
    """
    if total == 0:
        return '░' * length

    filled = int(current / total * length)
    return '▓' * filled + '░' * (length - filled)


def format_episode_status(episodes: List[Dict]) -> Dict[str, int]:
    """
    格式化剧集状态统计

    Args:
        episodes: 剧集列表

    Returns:
        Dict: 状态统计 {status: count}
    """
    stats = {}
    for episode in episodes:
        status = episode.get('status', 'unknown')
        stats[status] = stats.get(status, 0) + 1
    return stats


def format_status_summary(stats: Dict[str, int]) -> str:
    """
    格式化状态摘要文本

    Args:
        stats: 状态统计

    Returns:
        str: 格式化的状态文本
    """
    parts = []
    for status, count in stats.items():
        emoji = BotConfig.STATUS_EMOJI.get(status, '❓')
        parts.append(f"{count}{emoji}")

    return ' '.join(parts) if parts else "无剧集"


def escape_markdown(text: str) -> str:
    """
    转义 Markdown 特殊字符（用于 MarkdownV2）

    Args:
        text: 原始文本

    Returns:
        str: 转义后的文本
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 30) -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'
