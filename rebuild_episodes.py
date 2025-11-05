"""
重建 episodes 表 - 刮削所有订阅的剧集
"""
from src.models.database import Database
from src.services.episode_scraper import EpisodeScraper


def rebuild_episodes():
    """刮削所有番剧的剧集"""
    print("=== 重建 Episodes 表 ===\n")

    db = Database()
    scraper = EpisodeScraper()

    # 检查是否有订阅
    series_list = db.get_all_series()

    if not series_list:
        print("✗ 没有订阅，请先运行 rebuild_subscriptions.py")
        return

    print(f"找到 {len(series_list)} 个订阅\n")

    # 刮削所有番剧
    scraper.scrape_all_series()

    # 统计
    print("\n=== 统计 ===")
    total_episodes = 0
    for series in series_list:
        episodes = db.get_episodes_by_series(series['tmdb_id'])
        total_episodes += len(episodes)
        print(f"{series['series_name']}: {len(episodes)} 集")

    print(f"\n总计: {total_episodes} 集")


if __name__ == "__main__":
    rebuild_episodes()
