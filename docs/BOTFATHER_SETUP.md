# BotFather 配置指南

## 设置 Bot 命令列表

### 1. 打开 BotFather

在 Telegram 搜索 `@BotFather` 并打开对话

### 2. 设置命令

发送 `/setcommands` 命令，然后选择你的 Bot

### 3. 复制并发送以下命令列表

```
start - 🎬 启动 Bot
series - 📺 查看订阅
add - ➕ 添加订阅
status - 📊 系统状态
help - ❓ 帮助信息
```

### 4. 完成

BotFather 会回复 "Success! Command list updated."

---

## 设置 Bot 描述（可选）

### 设置简短描述

发送 `/setdescription` 命令，然后输入：

```
AutoAni - 自动番剧订阅管理 Bot
智能订阅、自动下载、实时通知
```

### 设置关于信息

发送 `/setabouttext` 命令，然后输入：

```
🎬 AutoAni Bot

功能：
• 📺 订阅管理（新番/老番）
• ➕ 快速添加订阅
• 🗑️ 智能删除（可保留文件）
• 🔔 下载完成通知

GitHub: https://github.com/zfeny/AutoAni
```

---

## 设置 Bot 头像（可选）

发送 `/setuserpic` 命令，然后上传一张头像图片（推荐 512x512 像素）

---

## 命令说明

### /start
启动 Bot，显示主菜单，包含：
- 📺 查看订阅
- ➕ 添加订阅
- 📊 系统状态
- ⚙️ 设置

### /series
直接打开订阅列表，选择：
- 🆕 新番（当前季度）
- 📚 老番（按季度筛选）

### /add
启动添加订阅流程：
1. 发送蜜柑 RSS URL
2. Bot 自动解析番剧信息
3. 确认后添加订阅

### /status
查看系统统计：
- 订阅数量
- 剧集总数
- 各状态分布
- OpenList 文件数

### /help
显示帮助信息和使用技巧

---

## 验证设置

设置完成后，在 Telegram 中：

1. 找到你的 Bot
2. 点击输入框左侧的 `/` 按钮
3. 应该能看到所有命令列表

---

## 完整配置清单

- ✅ 命令列表 (`/setcommands`)
- ✅ 简短描述 (`/setdescription`)
- ✅ 关于信息 (`/setabouttext`)
- ⬜ Bot 头像 (`/setuserpic`) - 可选
- ⬜ 内联模式 (`/setinline`) - 未启用

---

## 常见问题

### Q: 命令不显示？
A: 重启 Telegram 客户端或清除对话缓存

### Q: 可以修改命令吗？
A: 可以，重新发送 `/setcommands` 即可覆盖

### Q: 命令支持多语言吗？
A: 目前仅支持中文，可以通过 BotFather 设置多语言命令

---

## 下一步

配置完成后：

1. 配置 `.env` 文件
2. 运行 `python test_bot_connection.py` 测试连接
3. 运行 `python run_bot.py` 启动 Bot
4. 在 Telegram 发送 `/start` 开始使用
