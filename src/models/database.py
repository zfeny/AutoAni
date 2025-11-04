"""
数据库模型和初始化
"""
import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "data/autoani.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def init_db(self):
        """初始化数据库表结构"""
        conn = self.connect()
        cursor = conn.cursor()

        # 创建 series 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            tmdb_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            series_name TEXT NOT NULL,
            blocked_keyword TEXT,
            alias_names TEXT,
            total_episodes INTEGER,
            raw_rss_url TEXT,
            img_url TEXT,
            first_air_date TEXT,
            season_tag TEXT,
            fansub_group TEXT,
            subtitle_lang TEXT,
            last_scraped_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'mikan',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_series_name ON series(series_name)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_blocked_keyword ON series(blocked_keyword)
        """)

        # 创建 episodes 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            torrent_link TEXT NOT NULL,
            episode_link TEXT,
            file_size INTEGER,
            pub_date TEXT,
            subtitle_lang TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tmdb_id, episode_number, subtitle_lang),
            FOREIGN KEY(tmdb_id) REFERENCES series(tmdb_id)
        )
        """)

        # 创建 episodes 表索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_episodes_tmdb_id ON episodes(tmdb_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status)
        """)

        # 创建 openlist 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS openlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER,
            episode_number INTEGER,
            file_path TEXT NOT NULL UNIQUE,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            modified_at TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tmdb_id) REFERENCES series(tmdb_id)
        )
        """)

        # 创建 openlist 表索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_openlist_tmdb_id ON openlist(tmdb_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_openlist_episode ON openlist(tmdb_id, episode_number)
        """)

        conn.commit()
        self.close()

    def insert_series(self, tmdb_id: int, title: str, series_name: str,
                     blocked_keyword: str, **kwargs):
        """插入或更新番剧信息"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO series
        (tmdb_id, title, series_name, blocked_keyword, alias_names,
         total_episodes, raw_rss_url, img_url, first_air_date, season_tag,
         fansub_group, subtitle_lang, last_scraped_at, source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tmdb_id, title, series_name, blocked_keyword,
            kwargs.get('alias_names'),
            kwargs.get('total_episodes'),
            kwargs.get('raw_rss_url'),
            kwargs.get('img_url'),
            kwargs.get('first_air_date'),
            kwargs.get('season_tag'),
            kwargs.get('fansub_group'),
            kwargs.get('subtitle_lang'),
            kwargs.get('last_scraped_at'),
            kwargs.get('source', 'mikan'),
            datetime.now().isoformat()
        ))

        conn.commit()
        self.close()

    def is_blocked(self, series_name: str) -> bool:
        """检查番剧是否已被屏蔽"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) as count FROM series
        WHERE blocked_keyword = ?
        """, (series_name,))

        result = cursor.fetchone()
        self.close()

        return result['count'] > 0

    def get_all_series(self, status: str = 'active'):
        """获取所有番剧"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM series WHERE status = ?
        ORDER BY updated_at DESC
        """, (status,))

        results = cursor.fetchall()
        self.close()

        return [dict(row) for row in results]

    def insert_episode(self, tmdb_id: int, episode_number: int, title: str,
                      torrent_link: str, **kwargs):
        """插入或更新剧集信息"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO episodes
        (tmdb_id, episode_number, title, torrent_link, episode_link,
         file_size, pub_date, subtitle_lang, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tmdb_id, episode_number, title, torrent_link,
            kwargs.get('episode_link'),
            kwargs.get('file_size'),
            kwargs.get('pub_date'),
            kwargs.get('subtitle_lang'),
            kwargs.get('status', 'pending'),
            datetime.now().isoformat()
        ))

        conn.commit()
        self.close()

    def get_episodes_by_series(self, tmdb_id: int):
        """获取某个番剧的所有剧集"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM episodes WHERE tmdb_id = ?
        ORDER BY episode_number ASC
        """, (tmdb_id,))

        results = cursor.fetchall()
        self.close()

        return [dict(row) for row in results]

    def get_episodes_by_status(self, status: str):
        """按状态获取剧集"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM episodes WHERE status = ?
        ORDER BY created_at DESC
        """, (status,))

        results = cursor.fetchall()
        self.close()

        return [dict(row) for row in results]

    def update_episode_status(self, episode_id: int, status: str):
        """更新剧集状态"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE episodes SET status = ?, updated_at = ?
        WHERE id = ?
        """, (status, datetime.now().isoformat(), episode_id))

        conn.commit()
        self.close()

    def update_series_last_scraped(self, tmdb_id: int):
        """更新番剧最后刮削时间"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE series SET last_scraped_at = ?, updated_at = ?
        WHERE tmdb_id = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), tmdb_id))

        conn.commit()
        self.close()

    def update_series_subtitle_lang(self, tmdb_id: int, subtitle_lang: str,
                                   fansub_group: str = None):
        """更新番剧字幕语言偏好"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE series SET subtitle_lang = ?, fansub_group = ?, updated_at = ?
        WHERE tmdb_id = ?
        """, (subtitle_lang, fansub_group, datetime.now().isoformat(), tmdb_id))

        conn.commit()
        self.close()

    def insert_openlist_file(self, file_path: str, file_name: str, **kwargs):
        """插入或更新 OpenList 文件信息"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO openlist
        (file_path, file_name, tmdb_id, episode_number, file_size, modified_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            file_path, file_name,
            kwargs.get('tmdb_id'),
            kwargs.get('episode_number'),
            kwargs.get('file_size'),
            kwargs.get('modified_at'),
            datetime.now().isoformat()
        ))

        conn.commit()
        self.close()

    def clear_openlist(self):
        """清空 OpenList 表"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM openlist")

        conn.commit()
        self.close()

    def get_openlist_files(self, tmdb_id: int = None):
        """获取 OpenList 文件"""
        conn = self.connect()
        cursor = conn.cursor()

        if tmdb_id:
            cursor.execute("""
            SELECT * FROM openlist WHERE tmdb_id = ?
            ORDER BY episode_number ASC
            """, (tmdb_id,))
        else:
            cursor.execute("""
            SELECT * FROM openlist
            ORDER BY tmdb_id, episode_number ASC
            """)

        results = cursor.fetchall()
        self.close()

        return [dict(row) for row in results]
