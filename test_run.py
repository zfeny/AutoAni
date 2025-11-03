"""
测试脚本 - 只执行一次订阅处理
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import Database
from src.services.subscription_tracker import SubscriptionTracker
from src.utils.config import Config


def test_run():
    """测试运行"""
    print("=" * 60)
    print("AutoAni 测试运行")
    print("=" * 60)

    # 验证配置
    try:
        Config.validate()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        return

    # 初始化数据库
    db = Database()
    db.init_db()
    print("✓ 数据库初始化完成")

    # 执行一次订阅处理
    tracker = SubscriptionTracker()
    tracker.process_subscriptions()

    # 显示结果
    print("\n" + "=" * 60)
    print("当前订阅列表:")
    print("=" * 60)

    series_list = db.get_all_series()
    if series_list:
        for series in series_list:
            print(f"\n番剧名: {series['series_name']}")
            print(f"TMDB ID: {series['tmdb_id']}")
            print(f"原始标题: {series['title']}")
            print(f"屏蔽关键词: {series['blocked_keyword']}")
            print(f"总集数: {series.get('total_episodes', 'N/A')}")
            print("-" * 60)
    else:
        print("暂无订阅")


if __name__ == '__main__':
    test_run()
