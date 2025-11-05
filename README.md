# AutoAni - 自动番剧订阅管理系统

AutoAni 是一个自动化番剧订阅、下载和管理工具，支持蜜柑计划订阅源和 Telegram Bot 交互。

## ✨ 功能特性

- 🤖 **Telegram Bot 集成** - 便捷的订阅管理和状态查看
- 📡 **自动订阅刮削** - 定时拉取蜜柑计划订阅更新
- 🎯 **智能字幕检测** - 自动检测和匹配字幕语言
- 📥 **离线下载推送** - 自动推送到 Alist/OpenList 离线下载
- 📊 **状态同步跟踪** - 实时监控下载状态
- 🔔 **下载完成通知** - Telegram 推送通知
- ⚙️ **动态任务配置** - 通过 Bot 调整定时任务间隔
- 🎬 **TMDB 元数据** - 完整的番剧信息集成

## 📁 项目结构

```
AutoAni/
├── src/                      # 源代码
│   ├── models/              # 数据模型 (Database)
│   ├── services/            # 业务服务 (RSS, 刮削, 下载)
│   ├── parsers/             # 解析器 (标题, 页面)
│   ├── utils/               # 工具函数
│   └── scheduler_async.py   # 异步调度器
├── telegram_bot/            # Telegram Bot
│   ├── handlers/           # 消息处理器
│   ├── bot.py              # Bot 主程序
│   └── keyboards.py        # 键盘布局
├── scripts/                # 工具脚本
│   └── autoani_manual.py   # 手动管理 CLI
├── docs/                   # 文档
│   ├── TELEGRAM_BOT.md     # Bot 使用文档
│   └── BOTFATHER_SETUP.md  # BotFather 配置指南
├── tests/                  # 测试文件
├── data/                   # 数据库和配置
├── run.py                  # 统一启动入口 ⭐
├── README.md              # 项目说明
└── README_RUN.md          # 运行指南
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆仓库
git clone <repository>
cd AutoAni

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要配置
```

必需配置项：
```bash
# 蜜柑计划 RSS Token
MIKAN_RSS_TOKEN=your_token_here

# TMDB API Key
TMDB_API_KEY=your_tmdb_api_key

# OpenList 配置
OPENLIST_URL=http://your_openlist_server:5244
OPENLIST_ACCOUNT=admin
OPENLIST_PASSWORD=your_password
OPENLIST_DIR=/Animate/Bangumi
OPENLIST_DOWNLOAD_TOOL=qBittorrent

# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### 3. 配置 Telegram Bot

参考 [docs/BOTFATHER_SETUP.md](docs/BOTFATHER_SETUP.md) 配置 Bot 命令。

### 4. 启动系统

```bash
python run.py
```

这会同时启动：
- ✅ Telegram Bot 监听
- ✅ 定时 RSS 刮削
- ✅ 定时推送下载
- ✅ 定时检测下载完成
- ✅ 定时检测下载失败

详细说明见 [README_RUN.md](README_RUN.md)

## 📱 Telegram Bot 使用

### 基本命令

- `/start` - 启动 Bot，显示主菜单
- `/series` - 查看订阅列表
- `/add` - 添加订阅
- `/status` - 系统状态
- `/help` - 帮助信息

### 主要功能

#### 📺 查看订阅
- 🆕 新番：当前季度番剧
- 📚 老番：历史季度番剧（按季节筛选）
- 查看剧集详情和下载进度

#### ➕ 添加订阅
1. 发送 `/add` 或点击主菜单「➕ 添加订阅」
2. 发送蜜柑 RSS URL
3. 确认番剧信息

#### 🗑️ 删除订阅
- 在剧集详情页点击「🗑️ 删除订阅」
- 可选择：删除订阅+文件 或 仅删除订阅

#### ⚙️ 设置
- **定时任务设置**：修改刮削、下载、检测间隔
- **手动执行任务**：立即触发指定任务
- **查看不匹配项目**：查看字幕不匹配的剧集

#### 📊 系统状态
- 订阅统计
- 剧集状态分布
- OpenList 文件数
- 查看不匹配项目（如果有）

详细使用说明见 [docs/TELEGRAM_BOT.md](docs/TELEGRAM_BOT.md)

## 🛠️ 手动管理（CLI）

如需手动执行任务，使用 `scripts/autoani_manual.py`：

```bash
# 查看帮助
python scripts/autoani_manual.py --help

# 重建订阅
python scripts/autoani_manual.py rebuild-subscriptions

# 添加单个订阅
python scripts/autoani_manual.py add-subscription --url "<RSS_URL>"

# 刮削剧集
python scripts/autoani_manual.py scrape-episodes

# 推送下载（限制5个）
python scripts/autoani_manual.py push-downloads --limit 5

# 检查下载状态
python scripts/autoani_manual.py check-downloads

# 查看系统状态
python scripts/autoani_manual.py status
```

## 📋 工作流程

1. **RSS 刮削**（默认30分钟）
   - 拉取蜜柑订阅
   - 匹配 TMDB 元数据
   - 更新 series 表

2. **剧集刮削**（手动触发）
   - 刮削所有订阅的剧集信息
   - 检测字幕语言
   - 更新 episodes 表

3. **推送下载**（默认10分钟）
   - 查找 pending 状态剧集
   - 推送到 OpenList 离线下载
   - 更新为 downloading 状态

4. **检测完成**（默认5分钟）
   - 扫描 OpenList 文件
   - 检查 downloading 剧集是否完成
   - 发送 Telegram 通知

5. **检测失败**（默认60分钟）
   - 检查超过1天的 downloading 剧集
   - 回退为 pending 状态
   - 等待重新推送

## 📊 剧集状态说明

| 状态 | 说明 | 图标 |
|------|------|------|
| `pending` | 待下载 | ⏳ |
| `downloading` | 下载中 | ⬇️ |
| `openlist_exists` | 已下载 | ✅ |
| `completed` | 已完成 | ✅ |
| `mismatched` | 字幕不匹配 | ⚠️ |

## ⚙️ 定时任务配置

可通过以下方式修改定时任务间隔：

1. **Bot 设置页**（推荐）
   - 发送 `/start` → 点击「⚙️ 设置」
   - 选择「⏰ 定时任务设置」
   - 修改后立即生效

2. **配置文件**
   - 编辑 `data/scheduler_config.json`
   - 需要重启系统生效

默认配置：
```json
{
  "rss_scrape_interval": 30,      // RSS 刮削间隔（分钟）
  "push_download_interval": 10,   // 推送下载间隔（分钟）
  "check_complete_interval": 5,   // 检测完成间隔（分钟）
  "check_failed_interval": 60     // 检测失败间隔（分钟）
}
```

## 🔧 开发说明

### 代码优化

项目已进行全面优化：
- ✅ 数据库连接使用上下文管理器
- ✅ 消除重复查询和索引构建
- ✅ 统一错误处理装饰器
- ✅ 精简字幕检测逻辑
- ✅ 异步调度器集成
- ✅ 代码行数优化: 2221 → 2131 (-90行)

### 技术栈

- **后端**: Python 3.12+
- **异步框架**: asyncio + APScheduler
- **Bot 框架**: python-telegram-bot 20.7+
- **数据库**: SQLite
- **HTTP 客户端**: requests
- **HTML 解析**: BeautifulSoup4
- **元数据**: TMDbv3API

## 📝 常见问题

### Bot 无响应
1. 检查 `TELEGRAM_BOT_TOKEN` 配置
2. 确认用户 ID 在 `TELEGRAM_ALLOWED_USERS` 中
3. 查看终端日志输出

### 通知未收到
1. 确认 Bot Token 正确
2. 检查用户 ID 配置
3. 查看终端是否有错误

### 下载失败
1. 检查 OpenList 连接
2. 验证下载工具配置（qBittorrent/Aria2）
3. 查看不匹配项目（可能是字幕语言）

## 📄 License

MIT License

## 🙏 致谢

- [蜜柑计划](https://mikanani.me/) - 番剧订阅源
- [TMDB](https://www.themoviedb.org/) - 元数据 API
- [Alist](https://alist.nn.ci/) - 文件管理和离线下载
