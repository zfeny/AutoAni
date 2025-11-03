# AutoAni

自动番剧订阅管理工具

## 功能

- 跟踪蜜柑计划（Mikan Project）订阅
- 自动解析番剧标题，提取关键信息
- 通过 TMDB API 获取番剧详细信息
- 刮削番剧页面，获取原始 RSS 链接和封面图片
- **自动生成季节标签**（如"2025年秋季番组"）
- 自动屏蔽已处理的番剧，避免重复
- 定时任务（30分钟执行一次）

## 项目结构

```
AutoAni/
├── src/
│   ├── models/          # 数据库模型
│   ├── parsers/         # 标题解析器
│   ├── services/        # 核心服务（RSS、TMDB、订阅跟踪）
│   └── utils/           # 工具类（配置管理）
├── data/                # 数据库文件
├── logs/                # 日志文件
├── main.py              # 主程序入口（定时任务）
├── test_run.py          # 测试脚本（单次执行）
└── requirements.txt     # 依赖包
```

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
MIKAN_RSS_TOKEN=your_token_here
TMDB_API_KEY=your_tmdb_api_key_here
RSS_FETCH_INTERVAL=30
DATABASE_PATH=data/autoani.db
```

### 3. 运行

**测试运行（执行一次）：**

```bash
source venv/bin/activate
python test_run.py
```

**正式运行（定时任务）：**

```bash
source venv/bin/activate
python main.py
```

## 数据库结构

### series 表

| 字段 | 类型 | 说明 |
|------|------|------|
| tmdb_id | INTEGER | TMDB ID（主键） |
| title | TEXT | 原始标题 |
| series_name | TEXT | 番剧名称 |
| blocked_keyword | TEXT | 屏蔽关键词 |
| alias_names | TEXT | 别名 |
| total_episodes | INTEGER | 总集数 |
| raw_rss_url | TEXT | 原始 RSS 订阅链接 |
| img_url | TEXT | 封面图片链接 |
| first_air_date | TEXT | 首播日期（YYYY-MM-DD） |
| season_tag | TEXT | 季节标签（如"2025年秋季番组"） |
| status | TEXT | 状态（active/inactive） |
| source | TEXT | 来源（mikan） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 工作流程

1. 每30分钟拉取蜜柑计划 RSS 订阅
2. 解析标题，提取番剧名称
3. 检查是否已屏蔽（避免重复处理）
4. 搜索 TMDB，获取番剧 ID 和详细信息
5. 刮削单集页面，提取：
   - 原始 RSS 订阅链接（bangumiId + subgroupid）
   - 封面图片链接
6. 存储到数据库，并添加屏蔽关键词
7. 下次执行时自动跳过已处理的番剧

## API 使用

### 通过 RSS URL 添加订阅

可以直接通过 raw RSS URL 添加订阅（为 Telegram Bot 集成准备）：

```python
from src.services.subscription_tracker import SubscriptionTracker

tracker = SubscriptionTracker()
success = tracker.add_subscription_by_rss_url(
    "https://mikanani.me/RSS/Bangumi?bangumiId=3736&subgroupid=370"
)
```

**工作流程：**
1. 从 RSS URL 解析 `bangumiId` 和 `subgroupid`
2. 构建 Bangumi 页面 URL：`https://mikanani.me/Home/Bangumi/{bangumiId}#{subgroupid}`
3. 刮削页面获取封面图片
4. 从 RSS feed 获取番剧名称
5. 搜索 TMDB 获取详细信息
6. 存储到数据库

**测试：**
```bash
source venv/bin/activate
python demo_add_by_url.py
```

## 季节标签

系统会根据番剧的首播日期（`first_air_date`）自动生成季节标签。

**季节映射规则（日本动画标准）：**
- 1-3月 → 冬季番组
- 4-6月 → 春季番组
- 7-9月 → 夏季番组
- 10-12月 → 秋季番组

**示例：**
- 首播日期：`2025-10-03` → 季节标签：`2025年秋季番组`
- 首播日期：`2025-07-11` → 季节标签：`2025年夏季番组`

## 依赖

- feedparser: RSS 解析
- tmdbv3api: TMDB API 封装
- python-dotenv: 环境变量管理
- schedule: 定时任务
- beautifulsoup4: HTML 解析
- requests: HTTP 请求
