#!/usr/bin/env python3
"""
AutoAni Manual - 番剧订阅管理统一入口
用法: python autoani_manual.py <command> [options]
"""
import sys
import argparse
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import Database
from src.services.subscription_tracker import SubscriptionTracker
from src.services.episode_scraper import EpisodeScraper
from src.services.offline_downloader import OfflineDownloader
from src.services.openlist_scanner import OpenListScanner


def init_database():
    """初始化数据库"""
    print("初始化数据库...")
    db = Database()
    db.init_db()
    print("✓ 数据库初始化完成\n")
    return db


def cmd_rebuild_subscriptions(args):
    """重建订阅 - 从蜜柑"我的"订阅重建"""
    print("=== 重建订阅数据 ===\n")

    db = init_database()

    if args.clear:
        print("清空旧数据...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM series")
            cursor.execute("DELETE FROM episodes")
        print("✓ 已清空 series 和 episodes 表\n")

    tracker = SubscriptionTracker()
    tracker.process_subscriptions()

    # 显示结果
    series_list = db.get_all_series()
    print(f"\n✓ 共 {len(series_list)} 个订阅")


def cmd_add_subscription(args):
    """添加订阅 - 通过RSS URL"""
    if not args.url:
        print("✗ 请提供 RSS URL")
        print("用法: autoani_manual.py add-subscription --url <RSS_URL>")
        return

    print(f"添加订阅: {args.url}\n")

    tracker = SubscriptionTracker()
    success = tracker.add_subscription_by_rss_url(args.url)

    if success:
        print("\n✓ 订阅添加成功")
    else:
        print("\n✗ 订阅添加失败")


def cmd_scrape_episodes(args):
    """刮削剧集"""
    print("=== 刮削剧集 ===\n")

    scraper = EpisodeScraper()
    scraper.scrape_all_series()

    db = Database()
    total = len(db.get_episodes_by_status('pending'))
    print(f"\n✓ 刮削完成，共 {total} 个待下载剧集")


def cmd_scan_openlist(args):
    """扫描 OpenList"""
    print("=== 扫描 OpenList ===\n")

    scanner = OpenListScanner()
    scanner.scan_and_update()

    print("\n✓ OpenList 扫描完成")


def cmd_push_downloads(args):
    """推送缺失剧集到离线下载"""
    print("=== 推送离线下载 ===\n")

    downloader = OfflineDownloader()
    limit = args.limit if args.limit else None

    success_count = downloader.push_missing_episodes(limit=limit)

    print(f"\n✓ 推送完成，成功 {success_count} 个")


def cmd_check_downloads(args):
    """检查下载状态"""
    print("=== 检查下载状态 ===\n")

    db = Database()

    # 显示当前状态
    print("当前状态:")
    statuses = ['pending', 'downloading', 'openlist_exists', 'completed', 'mismatched']
    for status in statuses:
        episodes = db.get_episodes_by_status(status)
        print(f"  {status}: {len(episodes)} 集")

    print()

    # 检查 downloading 状态
    downloader = OfflineDownloader()
    downloader.check_downloading_status()


def cmd_show_mismatched(args):
    """显示字幕不匹配的剧集"""
    print("=== Mismatched 剧集列表 ===\n")

    db = Database()
    mismatched = db.get_episodes_by_status('mismatched')

    print(f"共 {len(mismatched)} 个不匹配的剧集:\n")

    series_map = db.get_series_map()

    for episode in mismatched:
        series = series_map.get(episode['tmdb_id'])
        if series:
            print(f"番剧: {series['series_name']}")
            print(f"  集数: EP{episode['episode_number']:02d}")
            print(f"  标题: {episode['title']}")
            print(f"  字幕: {episode.get('subtitle_lang', 'Unknown')}")
            print(f"  偏好: {series.get('subtitle_lang', 'Unknown')}")
            print()


def cmd_list_subscriptions(args):
    """列出所有订阅"""
    print("=== 订阅列表 ===\n")

    db = Database()
    series_list = db.get_all_series()

    print(f"共 {len(series_list)} 个订阅:\n")

    for series in series_list:
        print(f"- {series['series_name']} (TMDB: {series['tmdb_id']})")
        if args.verbose:
            print(f"  状态: {series.get('status', 'active')}")
            print(f"  字幕: {series.get('subtitle_lang', 'N/A')}")
            print(f"  RSS: {series.get('raw_rss_url', 'N/A')}")
        print()


def cmd_status(args):
    """显示系统状态"""
    print("=== AutoAni 状态 ===\n")

    db = Database()

    # 订阅统计
    series_list = db.get_all_series()
    print(f"订阅数: {len(series_list)}")

    # 剧集统计
    total_episodes = 0
    for series in series_list:
        episodes = db.get_episodes_by_series(series['tmdb_id'])
        total_episodes += len(episodes)
    print(f"总剧集数: {total_episodes}")

    # 状态分布
    print("\n剧集状态分布:")
    statuses = ['pending', 'downloading', 'openlist_exists', 'completed', 'mismatched']
    for status in statuses:
        episodes = db.get_episodes_by_status(status)
        print(f"  {status}: {len(episodes)} 集")

    # OpenList 统计
    openlist_files = db.get_openlist_files()
    print(f"\nOpenList 文件数: {len(openlist_files)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AutoAni Manual - 番剧订阅管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令列表:
  rebuild-subscriptions  重建订阅（从蜜柑"我的"订阅）
  add-subscription      添加单个订阅
  scrape-episodes       刮削所有订阅的剧集
  scan-openlist         扫描 OpenList 目录
  push-downloads        推送缺失剧集到离线下载
  check-downloads       检查下载状态
  show-mismatched       显示字幕不匹配的剧集
  list-subscriptions    列出所有订阅
  status                显示系统状态

示例:
  python autoani_manual.py rebuild-subscriptions --clear
  python autoani_manual.py add-subscription --url "https://mikanani.me/RSS/Bangumi?bangumiId=3736&subgroupid=370"
  python autoani_manual.py scrape-episodes
  python autoani_manual.py push-downloads --limit 5
  python autoani_manual.py status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # rebuild-subscriptions
    parser_rebuild = subparsers.add_parser('rebuild-subscriptions', help='重建订阅')
    parser_rebuild.add_argument('--clear', action='store_true', help='清空旧数据')
    parser_rebuild.set_defaults(func=cmd_rebuild_subscriptions)

    # add-subscription
    parser_add = subparsers.add_parser('add-subscription', help='添加订阅')
    parser_add.add_argument('--url', required=True, help='RSS URL')
    parser_add.set_defaults(func=cmd_add_subscription)

    # scrape-episodes
    parser_scrape = subparsers.add_parser('scrape-episodes', help='刮削剧集')
    parser_scrape.set_defaults(func=cmd_scrape_episodes)

    # scan-openlist
    parser_scan = subparsers.add_parser('scan-openlist', help='扫描 OpenList')
    parser_scan.set_defaults(func=cmd_scan_openlist)

    # push-downloads
    parser_push = subparsers.add_parser('push-downloads', help='推送离线下载')
    parser_push.add_argument('--limit', type=int, help='限制推送数量')
    parser_push.set_defaults(func=cmd_push_downloads)

    # check-downloads
    parser_check = subparsers.add_parser('check-downloads', help='检查下载状态')
    parser_check.set_defaults(func=cmd_check_downloads)

    # show-mismatched
    parser_mismatched = subparsers.add_parser('show-mismatched', help='显示不匹配剧集')
    parser_mismatched.set_defaults(func=cmd_show_mismatched)

    # list-subscriptions
    parser_list = subparsers.add_parser('list-subscriptions', help='列出订阅')
    parser_list.add_argument('-v', '--verbose', action='store_true', help='详细信息')
    parser_list.set_defaults(func=cmd_list_subscriptions)

    # status
    parser_status = subparsers.add_parser('status', help='显示系统状态')
    parser_status.set_defaults(func=cmd_status)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    try:
        args.func(args)
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
