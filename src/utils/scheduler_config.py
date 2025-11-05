"""
调度器配置管理
支持动态修改定时任务间隔
"""
import json
from pathlib import Path
from typing import Dict


class SchedulerConfig:
    """调度器配置"""

    CONFIG_FILE = Path(__file__).parent.parent.parent / 'data' / 'scheduler_config.json'

    # 默认配置（分钟）
    DEFAULT_CONFIG = {
        'rss_scrape_interval': 30,          # RSS 刮削间隔
        'push_download_interval': 10,       # 推送下载间隔
        'check_complete_interval': 5,       # 检测下载完成间隔
        'check_failed_interval': 60,        # 检测下载失败间隔（1小时）
    }

    @classmethod
    def _ensure_file_exists(cls):
        """确保配置文件存在"""
        if not cls.CONFIG_FILE.exists():
            cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            cls.save_config(cls.DEFAULT_CONFIG)

    @classmethod
    def load_config(cls) -> Dict[str, int]:
        """加载配置"""
        cls._ensure_file_exists()

        try:
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置，确保所有键都存在
                return {**cls.DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config: Dict[str, int]) -> bool:
        """保存配置"""
        try:
            cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    @classmethod
    def update_interval(cls, task_name: str, interval: int) -> bool:
        """
        更新任务间隔

        Args:
            task_name: 任务名称（rss_scrape_interval/push_download_interval等）
            interval: 间隔时间（分钟）

        Returns:
            是否成功
        """
        if task_name not in cls.DEFAULT_CONFIG:
            return False

        if interval < 1:
            return False

        config = cls.load_config()
        config[task_name] = interval
        return cls.save_config(config)

    @classmethod
    def get_interval(cls, task_name: str) -> int:
        """获取任务间隔"""
        config = cls.load_config()
        return config.get(task_name, cls.DEFAULT_CONFIG.get(task_name, 30))

    @classmethod
    def reset_to_default(cls) -> bool:
        """重置为默认配置"""
        return cls.save_config(cls.DEFAULT_CONFIG.copy())
