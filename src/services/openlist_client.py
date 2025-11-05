"""
OpenList API 客户端
"""
import requests
from typing import Optional, Dict, List
from src.utils.config import Config


class OpenListClient:
    """OpenList API 客户端"""

    # 支持的视频文件扩展名
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v'}

    def __init__(self):
        self.base_url = Config.OPENLIST_URL
        self.account = Config.OPENLIST_ACCOUNT
        self.password = Config.OPENLIST_PASSWORD
        self.token: Optional[str] = None

    def login(self) -> bool:
        """
        登录获取 JWT token

        Returns:
            bool: 是否登录成功
        """
        url = f"{self.base_url}/api/auth/login"

        payload = {
            "username": self.account,
            "password": self.password
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('code') == 200 and 'data' in data:
                self.token = data['data'].get('token')
                print(f"✓ OpenList 登录成功")
                return True
            else:
                print(f"✗ OpenList 登录失败: {data.get('message', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ OpenList 登录请求失败: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头

        Returns:
            Dict[str, str]: 请求头
        """
        if not self.token:
            raise ValueError("Token not set. Please login first.")

        return {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    def list_directory(self, path: str, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        """
        列出目录内容

        Args:
            path: 目录路径
            page: 页码
            per_page: 每页数量

        Returns:
            Dict: 目录内容，包含 content 列表和 total 总数
        """
        if not self.token:
            if not self.login():
                return None

        url = f"{self.base_url}/api/fs/list"

        payload = {
            "path": path,
            "page": page,
            "per_page": per_page,
            "refresh": False
        }

        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('code') == 200 and 'data' in data:
                return data['data']
            else:
                print(f"✗ 列出目录失败: {data.get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"✗ 列出目录请求失败: {e}")
            return None

    def scan_directory_recursive(self, path: str) -> List[Dict]:
        """
        递归扫描目录，获取所有视频文件

        Args:
            path: 目录路径

        Returns:
            List[Dict]: 视频文件列表
        """
        video_files = []

        def _scan(current_path: str):
            """递归扫描子函数"""
            result = self.list_directory(current_path)

            if not result:
                return

            content = result.get('content', [])

            for item in content:
                name = item.get('name', '')
                is_dir = item.get('is_dir', False)

                if is_dir:
                    # 递归扫描子目录
                    sub_path = f"{current_path}/{name}"
                    _scan(sub_path)
                else:
                    # 检查是否为视频文件
                    if self._is_video_file(name):
                        item['path'] = f"{current_path}/{name}"
                        video_files.append(item)

        _scan(path)
        return video_files

    def _is_video_file(self, filename: str) -> bool:
        """
        判断是否为视频文件

        Args:
            filename: 文件名

        Returns:
            bool: 是否为视频文件
        """
        import os
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.VIDEO_EXTENSIONS

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否删除成功
        """
        if not self.token:
            if not self.login():
                return False

        url = f"{self.base_url}/api/fs/remove"

        payload = {
            "names": [file_path],
            "dir": ""  # 使用绝对路径时为空
        }

        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('code') == 200:
                return True
            else:
                print(f"✗ 删除文件失败: {data.get('message', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ 删除文件请求失败: {e}")
            return False

    def delete_files_batch(self, file_paths: List[str]) -> tuple:
        """
        批量删除文件

        Args:
            file_paths: 文件路径列表

        Returns:
            tuple: (成功数量, 失败数量)
        """
        success = 0
        failed = 0

        for file_path in file_paths:
            if self.delete_file(file_path):
                success += 1
            else:
                failed += 1

        return success, failed
