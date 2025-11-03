"""
季节标签辅助函数
"""
from datetime import datetime
from typing import Optional


class SeasonHelper:
    """季节标签生成器"""

    # 季节映射（日本动画标准）
    SEASON_MAP = {
        1: "冬季", 2: "冬季", 3: "冬季",
        4: "春季", 5: "春季", 6: "春季",
        7: "夏季", 8: "夏季", 9: "夏季",
        10: "秋季", 11: "秋季", 12: "秋季"
    }

    @staticmethod
    def generate_season_tag(first_air_date: str) -> Optional[str]:
        """
        根据首播日期生成季节标签

        Args:
            first_air_date: 首播日期，格式 YYYY-MM-DD (如 "2025-10-01")

        Returns:
            季节标签，如 "2025年秋季番组"，失败返回 None
        """
        if not first_air_date:
            return None

        try:
            # 解析日期
            date = datetime.strptime(first_air_date, "%Y-%m-%d")
            year = date.year
            month = date.month

            # 获取季节
            season = SeasonHelper.SEASON_MAP.get(month)

            if not season:
                return None

            # 生成标签
            season_tag = f"{year}年{season}番组"
            return season_tag

        except Exception as e:
            print(f"Failed to generate season tag from {first_air_date}: {e}")
            return None

    @staticmethod
    def get_season_from_date(first_air_date: str) -> Optional[str]:
        """
        从日期获取季节（英文）

        Args:
            first_air_date: 首播日期

        Returns:
            season: spring/summer/fall/winter
        """
        if not first_air_date:
            return None

        try:
            date = datetime.strptime(first_air_date, "%Y-%m-%d")
            month = date.month

            season_map_en = {
                1: "winter", 2: "winter", 3: "winter",
                4: "spring", 5: "spring", 6: "spring",
                7: "summer", 8: "summer", 9: "summer",
                10: "fall", 11: "fall", 12: "fall"
            }

            return season_map_en.get(month)

        except Exception as e:
            print(f"Failed to get season from {first_air_date}: {e}")
            return None
