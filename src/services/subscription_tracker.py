"""
订阅跟踪服务 - 核心业务逻辑
"""
from typing import List, Dict
from src.services.rss_fetcher import RSSFetcher
from src.parsers.title_parser import TitleParser
from src.parsers.page_scraper import MikanPageScraper
from src.services.tmdb_service import TMDBService
from src.models.database import Database


class SubscriptionTracker:
    """订阅跟踪器"""

    def __init__(self):
        self.rss_fetcher = RSSFetcher()
        self.title_parser = TitleParser()
        self.page_scraper = MikanPageScraper()
        self.tmdb_service = TMDBService()
        self.db = Database()

    def process_subscriptions(self):
        """
        处理订阅 - 主流程

        1. 拉取 RSS 订阅
        2. 解析标题，提取番剧名称
        3. 检查是否已屏蔽
        4. 搜索 TMDB 获取 ID
        5. 存储到数据库
        """
        print("开始处理订阅...")

        # 拉取 RSS
        items = self.rss_fetcher.fetch()
        print(f"拉取到 {len(items)} 个条目")

        # 去重：按番剧名称去重
        unique_series = {}

        for item in items:
            title = item['title']

            # 解析标题
            series_name = self.title_parser.extract_series_name(title)
            if not series_name:
                print(f"无法解析标题: {title}")
                continue

            # 检查是否已处理
            if series_name in unique_series:
                continue

            # 检查是否已屏蔽
            if self.db.is_blocked(series_name):
                print(f"已屏蔽，跳过: {series_name}")
                continue

            unique_series[series_name] = {
                'original_title': title,
                'series_name': series_name,
                'episode_link': item['link'],  # 保存单集链接用于刮削
            }

        print(f"去重后剩余 {len(unique_series)} 个番剧")

        # 处理每个番剧
        for series_name, data in unique_series.items():
            self._process_single_series(series_name, data)

        print("订阅处理完成")

    def _process_single_series(self, series_name: str, data: Dict):
        """
        处理单个番剧

        Args:
            series_name: 番剧名称
            data: 番剧数据
        """
        print(f"\n处理番剧: {series_name}")

        # 搜索 TMDB
        tmdb_result = self.tmdb_service.search_anime(series_name)

        if not tmdb_result:
            print(f"未找到 TMDB 信息: {series_name}")
            return

        tmdb_id = tmdb_result['tmdb_id']
        print(f"找到 TMDB ID: {tmdb_id} - {tmdb_result['name']}")

        # 获取详细信息
        details = self.tmdb_service.get_series_details(tmdb_id)

        # 刮削单集页面，获取 raw_rss_url 和 img_url
        episode_link = data.get('episode_link')
        raw_rss_url = None
        img_url = None

        if episode_link:
            print(f"刮削页面: {episode_link}")
            scrape_result = self.page_scraper.scrape_episode_page(episode_link)
            if scrape_result:
                raw_rss_url = scrape_result.get('raw_rss_url')
                img_url = scrape_result.get('img_url')
                print(f"获取到 raw_rss_url: {raw_rss_url}")
                print(f"获取到 img_url: {img_url}")

        # 存储到数据库
        self.db.insert_series(
            tmdb_id=tmdb_id,
            title=data['original_title'],
            series_name=series_name,
            blocked_keyword=series_name,  # 使用番剧名作为屏蔽关键词
            alias_names=tmdb_result.get('original_name'),
            total_episodes=details.get('number_of_episodes') if details else None,
            raw_rss_url=raw_rss_url,
            img_url=img_url,
            source='mikan'
        )

        print(f"已添加到数据库: {series_name}")

    def add_subscription_by_rss_url(self, raw_rss_url: str) -> bool:
        """
        通过 raw_rss_url 添加订阅（用于 Telegram Bot）

        Args:
            raw_rss_url: RSS URL，如 https://mikanani.me/RSS/Bangumi?bangumiId=3736&subgroupid=370

        Returns:
            是否成功添加
        """
        print(f"\n通过 RSS URL 添加订阅: {raw_rss_url}")

        # 刮削 Bangumi 页面
        scrape_result = self.page_scraper.scrape_bangumi_page_from_rss_url(raw_rss_url)

        if not scrape_result:
            print("刮削失败")
            return False

        series_name = scrape_result.get('series_name')
        img_url = scrape_result.get('img_url')

        if not series_name:
            print("未能获取番剧名称")
            return False

        print(f"番剧名称: {series_name}")
        print(f"封面图片: {img_url}")

        # 检查是否已存在
        if self.db.is_blocked(series_name):
            print(f"番剧已存在: {series_name}")
            return False

        # 搜索 TMDB
        tmdb_result = self.tmdb_service.search_anime(series_name)

        if not tmdb_result:
            print(f"未找到 TMDB 信息: {series_name}")
            return False

        tmdb_id = tmdb_result['tmdb_id']
        print(f"找到 TMDB ID: {tmdb_id} - {tmdb_result['name']}")

        # 获取详细信息
        details = self.tmdb_service.get_series_details(tmdb_id)

        # 存储到数据库
        self.db.insert_series(
            tmdb_id=tmdb_id,
            title=series_name,  # 使用番剧名称作为标题
            series_name=series_name,
            blocked_keyword=series_name,
            alias_names=tmdb_result.get('original_name'),
            total_episodes=details.get('number_of_episodes') if details else None,
            raw_rss_url=raw_rss_url,
            img_url=img_url,
            source='mikan'
        )

        print(f"✓ 成功添加订阅: {series_name}")
        return True

    def get_all_subscriptions(self) -> List[Dict]:
        """
        获取所有订阅

        Returns:
            订阅列表
        """
        return self.db.get_all_series()
