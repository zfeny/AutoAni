"""
OpenList 扫描服务
"""
from typing import List, Dict, Optional
from src.services.openlist_client import OpenListClient
from src.services.tmdb_service import TMDBService
from src.parsers.title_parser import TitleParser
from src.models.database import Database
from src.utils.config import Config


class OpenListScanner:
    """OpenList 扫描器"""

    def __init__(self):
        self.client = OpenListClient()
        self.tmdb_service = TMDBService()
        self.title_parser = TitleParser()
        self.db = Database()

    def scan_and_update(self) -> bool:
        """
        扫描 OpenList 目录并更新数据库

        Returns:
            bool: 是否成功
        """
        print("=== 开始扫描 OpenList ===")

        # 登录
        if not self.client.login():
            print("✗ 登录失败")
            return False

        # 扫描目录
        scan_path = Config.OPENLIST_DIR
        print(f"扫描路径: {scan_path}")

        video_files = self.client.scan_directory_recursive(scan_path)
        print(f"找到 {len(video_files)} 个视频文件")

        if not video_files:
            print("未找到视频文件")
            return False

        # 清空旧数据
        print("清空旧数据...")
        self.db.clear_openlist()

        # 处理每个文件
        success_count = 0
        failed_count = 0

        for video in video_files:
            if self._process_video_file(video):
                success_count += 1
            else:
                failed_count += 1

        print(f"\n=== 扫描完成 ===")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")

        return True

    def _process_video_file(self, video: Dict) -> bool:
        """
        处理单个视频文件

        Args:
            video: 视频文件信息

        Returns:
            bool: 是否成功
        """
        file_name = video.get('name', '')
        file_path = video.get('path', '')

        # 提取番剧名
        series_name = self.title_parser.extract_series_name(file_name)
        if not series_name:
            print(f"✗ 无法提取番剧名: {file_name}")
            return False

        # 提取集数
        episode_number = self.title_parser.extract_episode_number(file_name)
        if episode_number is None:
            print(f"✗ 无法提取集数: {file_name}")
            return False

        # 搜索 TMDB
        tmdb_result = self.tmdb_service.search_anime(series_name)
        if not tmdb_result:
            print(f"✗ 未找到 TMDB: {series_name}")
            return False

        tmdb_id = tmdb_result['tmdb_id']

        # 存入数据库
        self.db.insert_openlist_file(
            file_path=file_path,
            file_name=file_name,
            tmdb_id=tmdb_id,
            episode_number=episode_number,
            file_size=video.get('size'),
            modified_at=video.get('modified')
        )

        print(f"✓ {series_name} - {episode_number:02d}")

        return True

    def get_missing_episodes(self, tmdb_id: int = None) -> List[Dict]:
        """
        获取缺失的剧集（在 episodes 表中但不在 openlist 中）

        Args:
            tmdb_id: 番剧 ID，为 None 则检查所有

        Returns:
            缺失的剧集列表
        """
        missing = []

        # 获取所有订阅的番剧
        if tmdb_id:
            series_list = [s for s in self.db.get_all_series() if s['tmdb_id'] == tmdb_id]
        else:
            series_list = self.db.get_all_series()

        for series in series_list:
            tmdb_id = series['tmdb_id']

            # 获取该番剧的所有剧集
            episodes = self.db.get_episodes_by_series(tmdb_id)

            # 获取 OpenList 中的文件
            openlist_files = self.db.get_openlist_files(tmdb_id)

            # 构建已有集数集合
            available_episodes = {f['episode_number'] for f in openlist_files if f.get('episode_number')}

            # 找出缺失的
            for episode in episodes:
                ep_num = episode['episode_number']
                if ep_num not in available_episodes:
                    missing.append({
                        'tmdb_id': tmdb_id,
                        'series_name': series['series_name'],
                        'episode_number': ep_num,
                        'title': episode['title'],
                        'torrent_link': episode['torrent_link']
                    })

        return missing
