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
         source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tmdb_id, title, series_name, blocked_keyword,
            kwargs.get('alias_names'),
            kwargs.get('total_episodes'),
            kwargs.get('raw_rss_url'),
            kwargs.get('img_url'),
            kwargs.get('first_air_date'),
            kwargs.get('season_tag'),
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
