"""
蜜柑页面刮削器
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse, parse_qs
from functools import wraps
import feedparser


def safe_scrape(func):
    """安全刮削装饰器，统一处理异常"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Scrape error in {func.__name__}: {e}")
            return None
    return wrapper


class MikanPageScraper:
    """蜜柑页面刮削器"""

    BASE_URL = "https://mikanani.me"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    @safe_scrape
    def scrape_episode_page(self, episode_url: str) -> Optional[Dict]:
        """
        刮削单集页面，提取 raw_rss_url 和 img_url

        Args:
            episode_url: 单集链接，如 https://mikanani.me/Home/Episode/xxx

        Returns:
            包含 raw_rss_url 和 img_url 的字典
        """
        # 如果是相对链接，转换为绝对链接
        if not episode_url.startswith('http'):
            episode_url = urljoin(self.BASE_URL, episode_url)

        response = self.session.get(episode_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取 raw_rss_url 和 img_url
        raw_rss_url = self._extract_raw_rss_url(soup)
        img_url = self._extract_img_url(soup)

        if raw_rss_url or img_url:
            return {
                'raw_rss_url': raw_rss_url,
                'img_url': img_url
            }

        return None

    @safe_scrape
    def _extract_raw_rss_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        提取 raw_rss_url

        从 <p class="bangumi-title"> 中的 RSS 链接提取
        例如: /RSS/Bangumi?bangumiId=3676&subgroupid=370
        """
        bangumi_title = soup.find('p', class_='bangumi-title')
        if not bangumi_title:
            return None

        rss_link = bangumi_title.find('a', class_='mikan-rss')
        if not rss_link:
            return None

        href = rss_link.get('href')
        if not href:
            return None

        return urljoin(self.BASE_URL, href)

    @safe_scrape
    def _extract_img_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        提取图片 URL

        从 <div class="bangumi-poster"> 的 background-image 提取
        """
        poster_div = soup.find('div', class_='bangumi-poster')
        if not poster_div:
            return None

        style = poster_div.get('style')
        if not style:
            return None

        # 使用正则提取 background-image URL
        match = re.search(r"url\('([^']+)'\)", style)
        if not match:
            return None

        img_path = match.group(1).split('?')[0]  # 去除查询参数
        return urljoin(self.BASE_URL, img_path)

    @safe_scrape
    def scrape_bangumi_page_from_rss_url(self, raw_rss_url: str) -> Optional[Dict]:
        """
        从 raw_rss_url 刮削 Bangumi 页面

        Args:
            raw_rss_url: RSS URL，如 https://mikanani.me/RSS/Bangumi?bangumiId=3736&subgroupid=370

        Returns:
            包含 img_url 和 series_name 的字典
        """
        # 解析 URL，提取 bangumiId 和 subgroupid
        parsed = urlparse(raw_rss_url)
        params = parse_qs(parsed.query)

        bangumi_id = params.get('bangumiId', [None])[0]
        subgroup_id = params.get('subgroupid', [None])[0]

        if not bangumi_id or not subgroup_id:
            print(f"Failed to parse bangumiId or subgroupid from {raw_rss_url}")
            return None

        # 构建 Bangumi 页面 URL
        bangumi_url = f"{self.BASE_URL}/Home/Bangumi/{bangumi_id}#{subgroup_id}"
        print(f"刮削 Bangumi 页面: {bangumi_url}")

        # 请求页面
        response = self.session.get(bangumi_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取图片 URL 和番剧名称
        img_url = self._extract_img_url(soup)
        series_name = self._fetch_series_name_from_rss(raw_rss_url)

        return {
            'img_url': img_url,
            'series_name': series_name,
            'bangumi_id': bangumi_id,
            'subgroup_id': subgroup_id
        }

    @safe_scrape
    def _fetch_series_name_from_rss(self, rss_url: str) -> Optional[str]:
        """
        从 RSS feed 获取番剧名称

        Args:
            rss_url: RSS URL

        Returns:
            番剧名称
        """
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            print(f"RSS parse error: {feed.bozo_exception}")
            return None

        # 从 channel title 提取，格式: "Mikan Project - 永远的黄昏"
        channel_title = feed.feed.get('title', '')
        if channel_title:
            return channel_title.replace('Mikan Project - ', '').strip()

        return None
