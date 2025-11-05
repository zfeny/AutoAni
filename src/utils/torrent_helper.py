"""
种子辅助工具 - 处理蜜柑种子链接
"""
import requests
import base64
from typing import Optional


class TorrentHelper:
    """种子辅助工具"""

    @staticmethod
    def download_torrent_content(torrent_url: str) -> Optional[bytes]:
        """
        下载种子文件内容

        Args:
            torrent_url: 种子下载链接

        Returns:
            bytes: 种子文件内容，失败返回 None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(torrent_url, headers=headers, timeout=30)
            response.raise_for_status()

            # 确保是种子文件
            content_type = response.headers.get('content-type', '')
            if 'torrent' not in content_type.lower() and not torrent_url.endswith('.torrent'):
                print(f"  ⚠️  可能不是种子文件: {content_type}")

            return response.content

        except Exception as e:
            print(f"  ✗ 下载种子失败: {e}")
            return None

    @staticmethod
    def torrent_to_base64(torrent_content: bytes) -> str:
        """
        将种子内容转换为 base64 编码

        Args:
            torrent_content: 种子文件字节内容

        Returns:
            str: base64 编码的字符串
        """
        return base64.b64encode(torrent_content).decode('utf-8')

    @staticmethod
    def get_magnet_link(torrent_content: bytes) -> Optional[str]:
        """
        从种子内容提取 magnet 链接（如果可能）

        Args:
            torrent_content: 种子文件字节内容

        Returns:
            str: magnet 链接，失败返回 None
        """
        try:
            import hashlib
            import bencodepy

            # 解析种子文件
            torrent_dict = bencodepy.decode(torrent_content)

            # 获取 info hash
            info = torrent_dict[b'info']
            info_encoded = bencodepy.encode(info)
            info_hash = hashlib.sha1(info_encoded).hexdigest()

            # 构建 magnet 链接
            magnet = f"magnet:?xt=urn:btih:{info_hash}"

            # 添加 tracker（如果有）
            if b'announce' in torrent_dict:
                announce = torrent_dict[b'announce'].decode('utf-8')
                magnet += f"&tr={announce}"

            return magnet

        except ImportError:
            # bencodepy 未安装，返回 None
            return None
        except Exception as e:
            print(f"  ✗ 生成 magnet 链接失败: {e}")
            return None
