"""
番剧标题解析器
"""
import re
from typing import Optional


class TitleParser:
    """标题解析器"""

    @staticmethod
    def extract_series_name(title: str) -> Optional[str]:
        """
        从标题中提取番剧名称

        标题格式示例:
        - [LoliHouse] 永远的黄昏 / Towa no Yuugure - 05 [WebRip 1080p HEVC-10bit AAC][简繁内封字幕]
        - [猎户手抄部] 不动声色的柏田与喜形于色的太田 - 01 [1080p HEVC-10bit AAC]

        提取策略:
        1. 去除字幕组标签 [xxx]
        2. 提取 / 前的中文名称或第一个名称
        3. 去除集数信息 (- 数字)

        Args:
            title: 原始标题

        Returns:
            番剧名称，失败返回 None
        """
        if not title:
            return None

        try:
            # 去除字幕组标签 [xxx]
            cleaned = re.sub(r'^\[.*?\]\s*', '', title)

            # 如果包含 / 分隔符，提取 / 前的部分（通常是中文名）
            if '/' in cleaned:
                series_name = cleaned.split('/')[0].strip()
            else:
                # 否则提取 - 前的部分
                series_name = cleaned.split('-')[0].strip()

            # 去除可能的多余空格
            series_name = ' '.join(series_name.split())

            return series_name if series_name else None

        except Exception as e:
            print(f"Failed to parse title '{title}': {e}")
            return None

    @staticmethod
    def extract_episode_number(title: str) -> Optional[int]:
        """
        从标题中提取集数

        Args:
            title: 原始标题

        Returns:
            集数，失败返回 None
        """
        try:
            # 匹配 - 数字 或 第x集 等模式
            patterns = [
                r'-\s*(\d+)\s*(?:\[|$)',     # - 05 [
                r'\[(\d+)\]',                 # [01]
                r'第\s*(\d+)\s*[集话話]',      # 第05集
                r'EP?\s*(\d+)',               # EP05 or E05
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
        提取字幕组名称

        Args:
            title: 原始标题

        Returns:
            字幕组名称
        """
        match = re.match(r'^\[(.*?)\]', title)
        return match.group(1) if match else None
