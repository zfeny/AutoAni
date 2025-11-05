"""
异步定时任务调度器
整合所有定时任务，支持动态配置和手动触发
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.services.subscription_tracker import SubscriptionTracker
from src.services.episode_scraper import EpisodeScraper
from src.services.offline_downloader import OfflineDownloader
from src.services.openlist_scanner import OpenListScanner
from src.models.database import Database
from src.utils.scheduler_config import SchedulerConfig


class AsyncScheduler:
    """异步调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.subscription_tracker = SubscriptionTracker()
        self.episode_scraper = EpisodeScraper()
        self.downloader = OfflineDownloader()
        self.openlist_scanner = OpenListScanner()
        self.db = Database()
        self.config = SchedulerConfig()

        # 任务 ID
        self.TASK_IDS = {
            'rss_scrape': 'rss_scrape_task',
            'push_download': 'push_download_task',
            'check_complete': 'check_complete_task',
            'check_failed': 'check_failed_task',
        }

    async def task_rss_scrape(self):
        """任务1: RSS刮削 + 更新series"""
        try:
            print(f"\n{'='*60}")
            print(f"[RSS刮削] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            # 在异步环境中同步调用
            await asyncio.to_thread(self.subscription_tracker.process_subscriptions)

            print(f"[RSS刮削] 完成\n")

        except Exception as e:
            print(f"[RSS刮削] 失败: {e}\n")

    async def task_scrape_episodes(self):
        """任务2: 刮削剧集信息 + 更新episodes"""
        try:
            print(f"\n{'='*60}")
            print(f"[剧集刮削] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            await asyncio.to_thread(self.episode_scraper.scrape_all_subscriptions)

            print(f"[剧集刮削] 完成\n")

        except Exception as e:
            print(f"[剧集刮削] 失败: {e}\n")

    async def task_push_download(self):
        """任务3: 推送离线下载"""
        try:
            print(f"\n{'='*60}")
            print(f"[推送下载] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            # 限制每次推送5个
            await asyncio.to_thread(self.downloader.push_missing_episodes, limit=5)

            print(f"[推送下载] 完成\n")

        except Exception as e:
            print(f"[推送下载] 失败: {e}\n")

    async def task_check_complete(self):
        """任务4: 检测下载完成"""
        try:
            print(f"\n{'='*60}")
            print(f"[检测完成] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            # 启用通知
            await asyncio.to_thread(self.downloader.check_downloading_status, enable_notification=True)

            print(f"[检测完成] 完成\n")

        except Exception as e:
            print(f"[检测完成] 失败: {e}\n")

    async def task_check_failed(self):
        """任务5: 检测下载失败（超过1天的downloading）"""
        try:
            print(f"\n{'='*60}")
            print(f"[检测失败] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            # 获取所有 downloading 状态的剧集
            downloading_episodes = self.db.get_episodes_by_status('downloading')

            if not downloading_episodes:
                print("没有 downloading 状态的剧集")
                print(f"[检测失败] 完成\n")
                return

            # 重新扫描 OpenList
            print("重新扫描 OpenList...")
            await asyncio.to_thread(self.openlist_scanner.scan_and_update)

            # 获取 OpenList 索引
            openlist_index = self.db.get_openlist_index()
            series_map = self.db.get_series_map()

            # 检查超过1天的 downloading 剧集
            now = datetime.now()
            failed_count = 0

            for episode in downloading_episodes:
                updated_at = episode.get('updated_at')
                if not updated_at:
                    continue

                # 解析更新时间
                try:
                    updated_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                except:
                    continue

                # 判断是否超过1天
                if now - updated_time < timedelta(days=1):
                    continue

                # 检查是否在 OpenList 中
                key = (episode['tmdb_id'], episode['episode_number'])
                if key in openlist_index:
                    # 已下载完成，更新状态
                    self.db.update_episode_status(episode['id'], 'openlist_exists')
                    series = series_map.get(episode['tmdb_id'])
                    series_name = series['series_name'] if series else 'Unknown'
                    print(f"✓ {series_name} EP{episode['episode_number']:02d} - 下载完成")
                else:
                    # 下载失败，回退为 pending
                    self.db.update_episode_status(episode['id'], 'pending')
                    failed_count += 1
                    series = series_map.get(episode['tmdb_id'])
                    series_name = series['series_name'] if series else 'Unknown'
                    print(f"✗ {series_name} EP{episode['episode_number']:02d} - 超时回退为 pending")

            print(f"\n回退 {failed_count} 个超时剧集")
            print(f"[检测失败] 完成\n")

        except Exception as e:
            print(f"[检测失败] 失败: {e}\n")

    def start(self):
        """启动调度器"""
        print("\n" + "="*60)
        print("AutoAni 异步调度器启动")
        print("="*60)

        # 加载配置
        config = SchedulerConfig.load_config()

        print("\n当前配置:")
        print(f"  RSS刮削间隔: {config['rss_scrape_interval']} 分钟")
        print(f"  推送下载间隔: {config['push_download_interval']} 分钟")
        print(f"  检测完成间隔: {config['check_complete_interval']} 分钟")
        print(f"  检测失败间隔: {config['check_failed_interval']} 分钟")

        # 添加定时任务
        self.scheduler.add_job(
            self.task_rss_scrape,
            trigger=IntervalTrigger(minutes=config['rss_scrape_interval']),
            id=self.TASK_IDS['rss_scrape'],
            name='RSS刮削',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.task_push_download,
            trigger=IntervalTrigger(minutes=config['push_download_interval']),
            id=self.TASK_IDS['push_download'],
            name='推送下载',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.task_check_complete,
            trigger=IntervalTrigger(minutes=config['check_complete_interval']),
            id=self.TASK_IDS['check_complete'],
            name='检测完成',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.task_check_failed,
            trigger=IntervalTrigger(minutes=config['check_failed_interval']),
            id=self.TASK_IDS['check_failed'],
            name='检测失败',
            replace_existing=True
        )

        # 启动调度器
        self.scheduler.start()
        print("\n✓ 调度器已启动\n")

    async def trigger_task(self, task_name: str) -> bool:
        """
        手动触发任务

        Args:
            task_name: 任务名称 (rss_scrape/push_download/check_complete/check_failed/scrape_episodes)

        Returns:
            是否成功触发
        """
        task_map = {
            'rss_scrape': self.task_rss_scrape,
            'push_download': self.task_push_download,
            'check_complete': self.task_check_complete,
            'check_failed': self.task_check_failed,
            'scrape_episodes': self.task_scrape_episodes,
        }

        task = task_map.get(task_name)
        if not task:
            return False

        # 立即执行任务
        await task()
        return True

    def update_task_interval(self, task_name: str, interval: int) -> bool:
        """
        更新任务间隔

        Args:
            task_name: 任务名称 (rss_scrape/push_download/check_complete/check_failed)
            interval: 新的间隔（分钟）

        Returns:
            是否成功
        """
        # 配置键名映射
        config_key_map = {
            'rss_scrape': 'rss_scrape_interval',
            'push_download': 'push_download_interval',
            'check_complete': 'check_complete_interval',
            'check_failed': 'check_failed_interval',
        }

        config_key = config_key_map.get(task_name)
        if not config_key:
            return False

        # 更新配置
        if not SchedulerConfig.update_interval(config_key, interval):
            return False

        # 重新调度任务
        task_id = self.TASK_IDS.get(task_name)
        if not task_id:
            return False

        try:
            job = self.scheduler.get_job(task_id)
            if job:
                job.reschedule(trigger=IntervalTrigger(minutes=interval))
                print(f"✓ 任务 {task_name} 间隔已更新为 {interval} 分钟")
                return True
        except Exception as e:
            print(f"✗ 更新任务失败: {e}")

        return False

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        print("\n调度器已停止")
