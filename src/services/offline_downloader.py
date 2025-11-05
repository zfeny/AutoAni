"""
离线下载服务 - 推送缺失剧集到 OpenList 离线下载
"""
from typing import List, Dict
from src.models.database import Database
from src.services.openlist_client import OpenListClient


class OfflineDownloader:
    """离线下载器"""

    def __init__(self):
        self.db = Database()
        self.client = OpenListClient()

    def sync_openlist_status(self):
        """
        同步 OpenList 状态
        检测 episodes 表中的剧集是否已在 OpenList 中存在
        如果存在则更新状态为 'openlist_exists'
        """
        print("=== 同步 OpenList 状态 ===\n")

        # 获取所有 pending 状态的剧集
        pending_episodes = self.db.get_episodes_by_status('pending')
        print(f"找到 {len(pending_episodes)} 个 pending 剧集")

        # 获取 OpenList 索引
        openlist_index = self.db.get_openlist_index()
        print(f"OpenList 中有 {len(openlist_index)} 个文件\n")

        # 获取番剧映射
        series_map = self.db.get_series_map()

        # 检测并更新状态
        updated_count = 0
        for episode in pending_episodes:
            key = (episode['tmdb_id'], episode['episode_number'])

            if key in openlist_index:
                # 文件已存在，更新状态
                self.db.update_episode_status(episode['id'], 'openlist_exists')
                updated_count += 1

                series = series_map.get(episode['tmdb_id'])
                series_name = series['series_name'] if series else 'Unknown'
                print(f"✓ {series_name} EP{episode['episode_number']:02d} - 已存在于 OpenList")

        print(f"\n更新了 {updated_count} 个剧集状态")
        return updated_count

    def check_downloading_status(self, enable_notification: bool = False):
        """
        检查 downloading 状态的剧集
        如果已在 OpenList 中，则更新为 openlist_exists
        如果不在 OpenList 中，则回退为 pending（下载失败）

        Args:
            enable_notification: 是否发送 Telegram 通知
        """
        print("=== 检查 Downloading 状态 ===\n")

        # 获取 downloading 状态的剧集
        downloading_episodes = self.db.get_episodes_by_status('downloading')
        print(f"找到 {len(downloading_episodes)} 个 downloading 剧集")

        if not downloading_episodes:
            print("没有 downloading 状态的剧集")
            return

        # 重新扫描 OpenList
        print("重新扫描 OpenList...")
        from src.services.openlist_scanner import OpenListScanner
        scanner = OpenListScanner()
        scanner.scan_and_update()

        # 获取更新后的 OpenList 索引
        openlist_index = self.db.get_openlist_index()
        print(f"OpenList 中有 {len(openlist_index)} 个文件\n")

        # 获取番剧映射
        series_map = self.db.get_series_map()

        # 检查每个 downloading 剧集
        completed_count = 0
        failed_count = 0
        completed_items = []

        for episode in downloading_episodes:
            key = (episode['tmdb_id'], episode['episode_number'])
            series = series_map.get(episode['tmdb_id'])
            series_name = series['series_name'] if series else 'Unknown'

            if key in openlist_index:
                # 下载完成，更新状态
                self.db.update_episode_status(episode['id'], 'openlist_exists')
                completed_count += 1
                print(f"✓ {series_name} EP{episode['episode_number']:02d} - 下载完成")

                # 记录完成项
                completed_items.append({
                    'series_name': series_name,
                    'episode_number': episode['episode_number']
                })
            else:
                # 仍未出现在 OpenList，回退为 pending
                self.db.update_episode_status(episode['id'], 'pending')
                failed_count += 1
                print(f"✗ {series_name} EP{episode['episode_number']:02d} - 下载失败，回退为 pending")

        print(f"\n=== 检查完成 ===")
        print(f"下载完成: {completed_count} 个")
        print(f"下载失败: {failed_count} 个")

        # 发送 Telegram 通知
        if enable_notification and completed_items:
            try:
                from telegram_bot.notifier import TelegramNotifier
                notifier = TelegramNotifier()
                notifier.send_notification_sync_batch(completed_items)
                print(f"\n✓ 已发送 Telegram 通知")
            except Exception as e:
                print(f"\n⚠️  发送 Telegram 通知失败: {e}")

        return completed_count, failed_count

    def get_missing_episodes(self) -> List[Dict]:
        """
        获取需要下载的剧集
        返回 status='pending' 且不在 OpenList 中的剧集
        """
        # 先同步状态
        self.sync_openlist_status()

        # 获取 pending 状态的剧集
        pending_episodes = self.db.get_episodes_by_status('pending')

        # 获取番剧映射并丰富信息
        series_map = self.db.get_series_map()

        missing = []
        for episode in pending_episodes:
            series = series_map.get(episode['tmdb_id'])
            if series:
                missing.append({
                    **episode,
                    'series_name': series['series_name']
                })

        return missing

    def add_offline_download(self, torrent_url: str, download_path: str = None, tool: str = None) -> bool:
        """
        添加离线下载任务

        Args:
            torrent_url: 种子 URL 或磁力链接
            download_path: 下载路径（可选）
            tool: 下载工具（aria2/qbittorrent/transmission，可选）

        Returns:
            bool: 是否成功
        """
        if not self.client.token:
            if not self.client.login():
                print("✗ 登录失败")
                return False

        # 如果是蜜柑的种子链接，先下载种子内容转换为 magnet
        from src.utils.config import Config
        from src.utils.torrent_helper import TorrentHelper

        final_url = torrent_url

        if 'mikanani.me' in torrent_url and torrent_url.endswith('.torrent'):
            print(f"  下载种子文件...")
            torrent_content = TorrentHelper.download_torrent_content(torrent_url)

            if torrent_content:
                # 尝试转换为 magnet 链接
                magnet = TorrentHelper.get_magnet_link(torrent_content)
                if magnet:
                    print(f"  ✓ 转换为 magnet 链接")
                    final_url = magnet
                else:
                    print(f"  ⚠️  无法转换为 magnet，使用原始链接")
            else:
                print(f"  ⚠️  下载种子失败，使用原始链接")

        url = f"{self.client.base_url}/api/fs/add_offline_download"

        # 根据 API 文档构建请求
        payload = {
            "urls": [final_url],
            "path": download_path or Config.OPENLIST_DIR,
        }

        # 添加 tool 参数
        tool_to_use = tool or Config.OPENLIST_DOWNLOAD_TOOL
        if tool_to_use:
            payload["tool"] = tool_to_use

        try:
            import requests
            response = requests.post(url, json=payload, headers=self.client._get_headers(), timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('code') == 200:
                print(f"  ✓ 添加离线下载成功")
                return True
            else:
                print(f"  ✗ 添加失败: {data.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
            return False

    def push_missing_episodes(self, limit: int = None) -> int:
        """
        推送缺失剧集到离线下载

        Args:
            limit: 限制推送数量

        Returns:
            int: 成功推送的数量
        """
        print("\n=== 推送缺失剧集到离线下载 ===\n")

        # 获取缺失剧集
        missing = self.get_missing_episodes()

        if not missing:
            print("没有需要下载的剧集")
            return 0

        print(f"\n找到 {len(missing)} 个缺失剧集")

        if limit:
            missing = missing[:limit]
            print(f"限制推送 {limit} 个\n")

        # 推送
        success_count = 0
        for episode in missing:
            series_name = episode['series_name']
            ep_num = episode['episode_number']
            torrent_link = episode['torrent_link']

            print(f"推送: {series_name} EP{ep_num:02d}")

            if self.add_offline_download(torrent_link):
                # 更新状态为 downloading
                self.db.update_episode_status(episode['id'], 'downloading')
                success_count += 1
            else:
                print(f"  推送失败")

        print(f"\n=== 推送完成 ===")
        print(f"成功: {success_count}/{len(missing)}")

        return success_count
