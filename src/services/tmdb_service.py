"""
TMDB API 服务
"""
from tmdbv3api import TMDb, TV, Search
from typing import Optional, Dict
from src.utils.config import Config


class TMDBService:
    """TMDB 服务"""

    def __init__(self):
        self.tmdb = TMDb()
        self.tmdb.api_key = Config.TMDB_API_KEY
        self.tmdb.language = 'zh-CN'
        self.search = Search()
        self.tv = TV()

    def search_anime(self, series_name: str) -> Optional[Dict]:
        """
        搜索番剧

        Args:
            series_name: 番剧名称

        Returns:
            番剧信息字典，包含 tmdb_id, name, overview 等
        """
        try:
            # 搜索电视节目
            results = self.search.tv_shows(series_name)

            if not results:
                print(f"No TMDB results found for: {series_name}")
                return None

            # 取第一个结果
            first_result = results[0]

            return {
                'tmdb_id': first_result.id,
                'name': first_result.name,
                'original_name': first_result.original_name if hasattr(first_result, 'original_name') else None,
                'overview': first_result.overview if hasattr(first_result, 'overview') else None,
                'first_air_date': first_result.first_air_date if hasattr(first_result, 'first_air_date') else None,
                'vote_average': first_result.vote_average if hasattr(first_result, 'vote_average') else None,
            }

        except Exception as e:
            print(f"Failed to search TMDB for '{series_name}': {e}")
            return None

    def get_series_details(self, tmdb_id: int) -> Optional[Dict]:
        """
        获取番剧详细信息

        Args:
            tmdb_id: TMDB ID

        Returns:
            番剧详细信息
        """
        try:
            details = self.tv.details(tmdb_id)

            return {
                'tmdb_id': details.id,
                'name': details.name,
                'original_name': details.original_name,
                'overview': details.overview,
                'number_of_episodes': details.number_of_episodes if hasattr(details, 'number_of_episodes') else None,
                'number_of_seasons': details.number_of_seasons if hasattr(details, 'number_of_seasons') else None,
                'status': details.status if hasattr(details, 'status') else None,
                'first_air_date': details.first_air_date if hasattr(details, 'first_air_date') else None,
            }

        except Exception as e:
            print(f"Failed to get TMDB details for ID {tmdb_id}: {e}")
            return None
