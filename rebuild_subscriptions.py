"""
重建订阅数据 - 从蜜柑"我的"订阅重建
"""
from src.models.database import Database
from src.services.subscription_tracker import SubscriptionTracker


def rebuild_from_mikan():
    """从蜜柑"我的"订阅重建 series 表"""
    print("=== 从蜜柑\"我的\"订阅重建 ===\n")

    tracker = SubscriptionTracker()

    # 处理订阅
    tracker.process_subscriptions()

    print("\n=== 重建完成 ===")


if __name__ == "__main__":
    # 初始化数据库
    db = Database()
    db.init_db()

    # 清空旧数据
    print("=== 清空旧订阅数据 ===\n")
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM series")
    cursor.execute("DELETE FROM episodes")
    conn.commit()
    db.close()
    print("✓ 已清空 series 和 episodes 表\n")

    # 从蜜柑订阅重建
    rebuild_from_mikan()

    # 显示结果
    print("\n=== 当前订阅列表 ===")
    series_list = db.get_all_series()
    print(f"\n共 {len(series_list)} 个订阅:\n")

    for series in series_list:
        print(f"- {series['series_name']} (TMDB: {series['tmdb_id']})")
        print(f"  RSS: {series.get('raw_rss_url', 'N/A')}")
        print(f"  IMG: {series.get('img_url', 'N/A')[:50] if series.get('img_url') else 'N/A'}...")
        print()
