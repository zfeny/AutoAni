"""
RSS 订阅拉取服务
"""
import feedparser
from typing import List, Dict
from src.utils.config import Config


class RSSFetcher:
    """RSS 拉取器"""

    def __init__(self):
        self.rss_url = Config.MIKAN_RSS_URL

    def fetch(self) -> List[Dict]:
        """
        拉取 RSS 订阅

        Returns:
            List[Dict]: 番剧条目列表
        """
        try:
            feed = feedparser.parse(self.rss_url)

            if feed.bozo:
                raise Exception(f"RSS parse error: {feed.bozo_exception}")

            items = []
            for entry in feed.entries:
                item = {
                    'title': entry.title,
                    'link': entry.link,
                    'pub_date': entry.published if hasattr(entry, 'published') else None,
                    'guid': entry.id if hasattr(entry, 'id') else None,
                }

                # 提取种子信息
                if hasattr(entry, 'torrent_contentlength'):
                    item['content_length'] = entry.torrent_contentlength

                items.append(item)

            return items

        except Exception as e:
            print(f"Failed to fetch RSS: {e}")
            return []

    def fetch_unique_titles(self) -> List[str]:
        """
        获取所有唯一的标题

        Returns:
            List[str]: 标题列表
        """
        items = self.fetch()
        return [item['title'] for item in items]
