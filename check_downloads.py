"""
检查下载状态 - 更新 downloading 状态的剧集
"""
from src.services.offline_downloader import OfflineDownloader
from src.models.database import Database


def show_status():
    """显示当前状态统计"""
    print("\n=== 当前状态统计 ===")
    db = Database()

    statuses = ['pending', 'downloading', 'openlist_exists', 'completed', 'mismatched']
    for status in statuses:
        episodes = db.get_episodes_by_status(status)
        print(f"{status}: {len(episodes)} 集")


def main():
    """主函数"""
    print("检查下载状态\n")

    # 显示检查前状态
    show_status()

    # 检查 downloading 状态
    downloader = OfflineDownloader()
    downloader.check_downloading_status()

    # 显示检查后状态
    show_status()


if __name__ == "__main__":
    main()
