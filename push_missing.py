"""
推送缺失剧集到离线下载
"""
from src.services.offline_downloader import OfflineDownloader


def main():
    downloader = OfflineDownloader()

    print("开始推送缺失剧集...\n")

    # 推送所有缺失剧集（或指定数量限制）
    # downloader.push_missing_episodes(limit=5)  # 限制推送 5 个测试
    downloader.push_missing_episodes()  # 推送全部


if __name__ == "__main__":
    main()
