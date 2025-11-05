"""
剧集刮削服务
"""
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.models.database import Database
from src.utils.subtitle_helper import SubtitleHelper


class EpisodeScraper:
    """剧集刮削器"""

    def __init__(self):
        self.db = Database()
        self.subtitle_helper = SubtitleHelper()

    def scrape_all_series(self):
        """刮削所有活跃 series 的 episodes"""
        print("\n开始刮削所有番剧的剧集...")

        series_list = self.db.get_all_series(status='active')
        print(f"找到 {len(series_list)} 个活跃番剧")

        for series in series_list:
            try:
                self.scrape_series_episodes(series)
            except Exception as e:
                print(f"刮削 {series['series_name']} 失败: {e}")

        print("\n刮削完成")

    def scrape_series_episodes(self, series: Dict):
        """
        刮削单个 series 的 episodes

        流程：
        1. 检查 7 天规则
        2. 拉取 RSS
        3. 检测字幕偏好（如果未设置）
        4. 存储所有 episodes
        """
        series_name = series['series_name']
        tmdb_id = series['tmdb_id']

        print(f"\n处理: {series_name}")

        # 检查是否需要刮削
        if not self._should_scrape(series):
            print(f"  跳过（7天内已刮削）")
            return

        # 检查是否有 RSS URL
        if not series.get('raw_rss_url'):
            print(f"  跳过（无 RSS URL）")
            return

        # 拉取 RSS
        print(f"  拉取 RSS: {series['raw_rss_url']}")
        items = self._fetch_rss(series['raw_rss_url'])

        if not items:
            print(f"  未找到剧集")
            return

        print(f"  找到 {len(items)} 个剧集")

        # 检测字幕偏好
        if not series.get('subtitle_lang'):
            print(f"  检测字幕偏好...")
            subtitle_lang, fansub_group = self._detect_subtitle_preference(items)

            if subtitle_lang:
                print(f"  字幕偏好: {subtitle_lang}, 字幕组: {fansub_group}")
                self.db.update_series_subtitle_lang(tmdb_id, subtitle_lang, fansub_group)
                series['subtitle_lang'] = subtitle_lang
                series['fansub_group'] = fansub_group
            else:
                print(f"  ⚠️  无法检测字幕偏好，跳过")
                return

        # 存储 episodes
        self._store_episodes(series, items)

        # 检查是否需要失活
        self.db.check_and_deactivate_series(tmdb_id)

        # 更新刮削时间
        self.db.update_series_last_scraped(tmdb_id)
        print(f"  ✓ 完成")

    def _should_scrape(self, series: Dict) -> bool:
        """检查是否需要刮削（7天规则）"""
        last_scraped = series.get('last_scraped_at')

        if not last_scraped:
            return True

        try:
            last_scraped_time = datetime.fromisoformat(last_scraped)
            now = datetime.now()
            days_diff = (now - last_scraped_time).days

            return days_diff >= 7

        except Exception:
            return True

    def _fetch_rss(self, rss_url: str) -> List[Dict]:
        """拉取 RSS feed"""
        try:
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                print(f"  RSS 解析错误: {feed.bozo_exception}")
                return []

            items = []
            for entry in feed.entries:
                item = {
                    'title': entry.title,
                    'link': entry.link,
                    'pub_date': entry.published if hasattr(entry, 'published') else None,
                    'torrent_link': None,
                    'file_size': None,
                }

                # 提取种子链接和文件大小
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    item['torrent_link'] = entry.enclosures[0].get('href')
                    item['file_size'] = entry.enclosures[0].get('length')

                # 或者从 torrent 标签获取
                if hasattr(entry, 'torrent_contentlength'):
                    item['file_size'] = entry.torrent_contentlength

                items.append(item)

            return items

        except Exception as e:
            print(f"  RSS 拉取失败: {e}")
            return []

    def _detect_subtitle_preference(self, items: List[Dict]) -> tuple:
        """
        检测字幕语言偏好

        Returns:
            (subtitle_lang, fansub_group)
        """
        if not items:
            return None, None

        # 统计所有字幕类型
        subtitle_stats = {}
        fansub_groups = set()

        for item in items:
            lang = self.subtitle_helper.detect_subtitle_lang(item['title'])
            group = self.subtitle_helper.extract_fansub_group(item['title'])

            if lang:
                subtitle_stats[lang] = subtitle_stats.get(lang, 0) + 1

            if group:
                fansub_groups.add(group)

        if not subtitle_stats:
            return None, None

        # 如果只有一种字幕
        if len(subtitle_stats) == 1:
            lang = list(subtitle_stats.keys())[0]
            group = list(fansub_groups)[0] if len(fansub_groups) == 1 else None
            return lang, group

        # 多种字幕，按优先级选择
        priority = ['chs', 'chs_cht', 'cht']
        for lang in priority:
            if lang in subtitle_stats:
                group = list(fansub_groups)[0] if len(fansub_groups) == 1 else None
                return lang, group

        return None, None

    def _store_episodes(self, series: Dict, items: List[Dict]):
        """存储剧集到数据库"""
        tmdb_id = series['tmdb_id']
        preferred_lang = series['subtitle_lang']

        stored_count = 0
        skipped_count = 0

        for item in items:
            # 提取信息
            episode_number = self.subtitle_helper.extract_episode_number(item['title'])
            if not episode_number:
                continue

            subtitle_lang = self.subtitle_helper.detect_subtitle_lang(item['title'])
            torrent_link = item.get('torrent_link')

            if not torrent_link:
                continue

            # 确定状态
            if subtitle_lang == preferred_lang:
                status = 'pending'
            elif subtitle_lang:
                status = 'mismatched'
            else:
                status = 'mismatched'
                skipped_count += 1

            # 存储
            try:
                self.db.insert_episode(
                    tmdb_id=tmdb_id,
                    episode_number=episode_number,
                    title=item['title'],
                    torrent_link=torrent_link,
                    episode_link=item.get('link'),
                    file_size=item.get('file_size'),
                    pub_date=item.get('pub_date'),
                    subtitle_lang=subtitle_lang,
                    status=status
                )
                stored_count += 1
            except Exception as e:
                print(f"    存储失败: {e}")

        print(f"  存储 {stored_count} 个剧集，跳过 {skipped_count} 个")
