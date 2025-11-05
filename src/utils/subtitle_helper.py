"""
字幕语言检测和处理工具
"""
import re
from typing import Optional


class SubtitleHelper:
    """字幕语言辅助工具"""

    # 字幕语言检测规则（按优先级排序）
    SUBTITLE_PATTERNS = [
        ('chs_cht', ['简繁', '简繁内封', '简繁内嵌']),
        ('chs', ['简体', '简中', '简日', '简体内嵌', '简体内封', 'chs']),
        ('cht', ['繁体', '繁中', '繁日', '繁体内嵌', '繁体内封', 'cht']),
    ]

    @staticmethod
    def detect_subtitle_lang(title: str) -> Optional[str]:
        """
        从标题检测字幕语言

        Args:
            title: 剧集标题

        Returns:
            'chs' | 'cht' | 'chs_cht' | None
        """
        if not title:
            return None

        title_lower = title.lower()

        # 按优先级检测
        for lang, keywords in SubtitleHelper.SUBTITLE_PATTERNS:
            for keyword in keywords:
                # CHS 特殊处理：避免匹配到 CHT
                if keyword == 'chs' and 'cht' in title_lower:
                    continue
                if keyword.lower() in title_lower:
                    return lang

        return None

    @staticmethod
    def extract_episode_number(title: str) -> Optional[int]:
        """
        从标题提取集数

        Args:
            title: 剧集标题

        Returns:
            集数或 None
        """
        if not title:
            return None

        try:
            # 模式列表（按优先级）
            patterns = [
                r'\[(\d+)\]',              # [05]
                r'\s-\s*(\d+)\s',          # - 05
                r'第\s*(\d+)\s*[集话話]',   # 第05集
                r'EP?\.?\s*(\d+)',         # EP05, E05, EP.05
                r'#(\d+)',                 # #05
            ]

            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    return int(match.group(1))

            return None

        except Exception as e:
            print(f"Failed to extract episode number from '{title}': {e}")
            return None

    @staticmethod
    def extract_fansub_group(title: str) -> Optional[str]:
        """
        从标题提取字幕组名称

        Args:
            title: 剧集标题

        Returns:
            字幕组名称
        """
        match = re.match(r'^\[(.*?)\]', title)
        return match.group(1) if match else None

    @staticmethod
    def select_subtitle_by_priority(episodes: list, priority: list = None) -> Optional[dict]:
        """
        根据优先级从多个版本中选择字幕

        Args:
            episodes: 同一集的多个版本
            priority: 优先级列表，默认 ['chs', 'chs_cht', 'cht']

        Returns:
            选中的剧集或 None
        """
        if not episodes:
            return None

        if not priority:
            priority = ['chs', 'chs_cht', 'cht']

        # 按优先级查找
        for lang in priority:
            for ep in episodes:
                if ep.get('subtitle_lang') == lang:
                    return ep

        # 如果都不匹配，返回 None
        return None
