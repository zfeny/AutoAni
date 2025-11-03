"""
AutoAni - 自动番剧订阅管理
主程序入口
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import Database
from src.scheduler import Scheduler
from src.utils.config import Config


def init():
    """初始化"""
    print("初始化 AutoAni...")

    # 验证配置
    try:
        Config.validate()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        sys.exit(1)

    # 初始化数据库
    db = Database()
    db.init_db()
    print("✓ 数据库初始化完成")


def main():
    """主函数"""
    init()

    # 启动调度器
    scheduler = Scheduler()
    scheduler.start()


if __name__ == '__main__':
    main()
