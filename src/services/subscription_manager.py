"""
订阅管理服务 - 负责订阅的增删改查和文件清理
"""
from typing import List, Dict
from src.models.database import Database
from src.services.openlist_client import OpenListClient


class SubscriptionManager:
    """订阅管理器"""

    def __init__(self):
        self.db = Database()
        self.openlist_client = OpenListClient()

    def delete_subscription(self, tmdb_id: int, delete_files: bool = True) -> tuple:
        """
        删除订阅

        Args:
            tmdb_id: 番剧 TMDB ID
            delete_files: 是否同时删除 OpenList 中的文件

        Returns:
            tuple: (是否成功, 删除文件数, 错误信息)
        """
        try:
            # 1. 获取番剧信息
            series_list = self.db.get_all_series()
            series = next((s for s in series_list if s['tmdb_id'] == tmdb_id), None)

            if not series:
                return False, 0, f"未找到 TMDB ID: {tmdb_id} 的订阅"

            series_name = series['series_name']
            deleted_files = 0

            # 2. 删除 OpenList 文件（如果需要）
            if delete_files:
                print(f"  正在删除 {series_name} 的文件...")
                openlist_files = self.db.get_openlist_files(tmdb_id)

                if openlist_files:
                    file_paths = [f['file_path'] for f in openlist_files]
                    success, failed = self.openlist_client.delete_files_batch(file_paths)
                    deleted_files = success
                    print(f"  ✓ 删除文件: {success} 个成功, {failed} 个失败")
                else:
                    print(f"  - 没有需要删除的文件")

            # 3. 删除数据库中的 openlist 记录
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM openlist WHERE tmdb_id = ?", (tmdb_id,))

            # 4. 删除数据库中的 episodes
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM episodes WHERE tmdb_id = ?", (tmdb_id,))
                deleted_episodes = cursor.rowcount

            # 5. 删除数据库中的 series
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM series WHERE tmdb_id = ?", (tmdb_id,))

            print(f"  ✓ 删除订阅: {series_name}")
            print(f"  ✓ 删除剧集记录: {deleted_episodes} 条")

            return True, deleted_files, None

        except Exception as e:
            error_msg = f"删除订阅失败: {e}"
            print(f"  ✗ {error_msg}")
            return False, 0, error_msg

    def get_series_stats(self, tmdb_id: int) -> Dict:
        """
        获取番剧统计信息

        Args:
            tmdb_id: 番剧 TMDB ID

        Returns:
            Dict: 统计信息
        """
        episodes = self.db.get_episodes_by_series(tmdb_id)
        openlist_files = self.db.get_openlist_files(tmdb_id)

        # 统计各状态数量
        status_count = {}
        for episode in episodes:
            status = episode.get('status', 'unknown')
            status_count[status] = status_count.get(status, 0) + 1

        return {
            'total_episodes': len(episodes),
            'downloaded_files': len(openlist_files),
            'status_count': status_count
        }
