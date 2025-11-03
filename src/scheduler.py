"""
定时任务调度器
"""
import time
import schedule
from src.services.subscription_tracker import SubscriptionTracker
from src.utils.config import Config


class Scheduler:
    """调度器"""

    def __init__(self):
        self.tracker = SubscriptionTracker()

    def run_subscription_task(self):
        """执行订阅任务"""
        try:
            print(f"\n{'='*50}")
            print(f"执行订阅任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")

            self.tracker.process_subscriptions()

            print(f"\n任务完成 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"任务执行失败: {e}")

    def start(self):
        """启动调度器"""
        print("启动 AutoAni 调度器...")
        print(f"RSS 拉取间隔: {Config.RSS_FETCH_INTERVAL} 分钟")

        # 立即执行一次
        self.run_subscription_task()

        # 设置定时任务
        schedule.every(Config.RSS_FETCH_INTERVAL).minutes.do(self.run_subscription_task)

        # 循环执行
        print("\n调度器运行中，按 Ctrl+C 退出...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n调度器已停止")
