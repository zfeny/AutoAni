# AutoAni - 自动番剧订阅管理系统

AutoAni 是一个自动化番剧订阅、下载和管理工具，支持蜜柑计划订阅源。

## 功能特性

- ✅ 自动订阅蜜柑计划番剧
- ✅ 智能字幕语言检测和匹配
- ✅ 自动推送到 Alist 离线下载
- ✅ OpenList 目录扫描和状态同步
- ✅ 剧集状态管理和跟踪
- ✅ TMDB 元数据集成

## 项目结构

```
AutoAni/
├── src/                    # 源代码
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   ├── parsers/           # 解析器
│   └── utils/             # 工具函数
├── tests/                 # 测试文件
├── data/                  # 数据库和数据文件
├── main.py               # 自动调度入口
└── autoani_manual.py     # 手动管理CLI
```

## 安装

1. 克隆仓库
```bash
git clone <repository>
cd AutoAni
```

2. 安装依赖
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要配置
```

## 使用方法

### 方式一: 自动调度模式

运行 `main.py` 启动定时任务，自动执行订阅刮削和下载推送:

```bash
python main.py
```

### 方式二: 手动管理模式

使用 `autoani_manual.py` 进行手动操作:

#### 查看帮助
```bash
python autoani_manual.py --help
```

#### 常用命令

**查看系统状态**
```bash
python autoani_manual.py status
```

**重建订阅（从蜜柑"我的"订阅）**
```bash
python autoani_manual.py rebuild-subscriptions --clear
```

**添加单个订阅**
```bash
python autoani_manual.py add-subscription --url "https://mikanani.me/RSS/Bangumi?bangumiId=3736&subgroupid=370"
```

**刮削所有订阅的剧集**
```bash
python autoani_manual.py scrape-episodes
```

**扫描 OpenList 目录**
```bash
python autoani_manual.py scan-openlist
```

**推送缺失剧集到离线下载**
```bash
# 推送所有缺失剧集
python autoani_manual.py push-downloads

# 限制推送数量
python autoani_manual.py push-downloads --limit 5
```

**检查下载状态**
```bash
python autoani_manual.py check-downloads
```

**显示字幕不匹配的剧集**
```bash
python autoani_manual.py show-mismatched
```

**列出所有订阅**
```bash
# 简要列表
python autoani_manual.py list-subscriptions

# 详细信息
python autoani_manual.py list-subscriptions -v
```

## 配置说明

在 `.env` 文件中配置以下项目:

### 蜜柑计划配置
```bash
MIKAN_RSS_URL=https://mikanani.me/RSS/MyBangumi?token=YOUR_TOKEN
```

### Alist/OpenList 配置
```bash
OPENLIST_URL=http://your-alist-server
OPENLIST_ACCOUNT=your_username
OPENLIST_PASSWORD=your_password
OPENLIST_DIR=/downloads/anime
OPENLIST_DOWNLOAD_TOOL=aria2  # 或 qbittorrent, transmission
```

### TMDB 配置
```bash
TMDB_API_KEY=your_tmdb_api_key
TMDB_LANGUAGE=zh-CN
```

## 工作流程

1. **订阅管理**: 从蜜柑计划拉取订阅，匹配 TMDB 元数据
2. **剧集刮削**: 定期刮削订阅的新剧集，检测字幕语言
3. **状态同步**: 扫描 OpenList，标记已下载的剧集
4. **离线下载**: 推送缺失剧集到 Alist 离线下载
5. **状态跟踪**: 监控下载状态，自动更新剧集状态

## 剧集状态说明

- `pending`: 待下载
- `downloading`: 下载中
- `openlist_exists`: 已存在于 OpenList
- `completed`: 已完成
- `mismatched`: 字幕不匹配

## 开发说明

### 代码优化

项目已进行全面优化:
- ✅ 数据库连接使用上下文管理器
- ✅ 消除重复查询和索引构建
- ✅ 统一错误处理装饰器
- ✅ 精简字幕检测逻辑
- ✅ 代码行数优化: 2221 → 2131 (-90行)

### 运行测试

测试文件已归档到 `tests/archived/` 目录。

## License

MIT License
