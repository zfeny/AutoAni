"""
显示 mismatched 状态的剧集
"""
from src.models.database import Database


def main():
    print("=== Mismatched 剧集列表 ===\n")

    db = Database()
    mismatched = db.get_episodes_by_status('mismatched')

    print(f"共 {len(mismatched)} 个不匹配的剧集:\n")

    # 获取 series 信息
    series_list = db.get_all_series()
    series_map = {s['tmdb_id']: s for s in series_list}

    for episode in mismatched:
        series = series_map.get(episode['tmdb_id'])
        if series:
            print(f"番剧: {series['series_name']}")
            print(f"  集数: EP{episode['episode_number']:02d}")
            print(f"  标题: {episode['title']}")
            print(f"  字幕: {episode.get('subtitle_lang', 'Unknown')}")
            print(f"  偏好: {series.get('subtitle_lang', 'Unknown')}")
            print()


if __name__ == "__main__":
    main()
