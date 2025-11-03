# AutoAni

自动番剧订阅管理工具

## 功能

- 跟踪蜜柑计划（Mikan Project）订阅
- 自动解析番剧标题，提取关键信息
- 通过 TMDB API 获取番剧详细信息
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
| status | TEXT | 状态（active/inactive） |
| source | TEXT | 来源（mikan） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 工作流程

1. 每30分钟拉取蜜柑计划 RSS 订阅
2. 解析标题，提取番剧名称
3. 检查是否已屏蔽（避免重复处理）
4. 搜索 TMDB，获取番剧 ID 和详细信息
5. 存储到数据库，并添加屏蔽关键词
6. 下次执行时自动跳过已处理的番剧

## 依赖

- feedparser: RSS 解析
- tmdbv3api: TMDB API 封装
- python-dotenv: 环境变量管理
- schedule: 定时任务
