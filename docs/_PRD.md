---
title: ▷ AutoAni
aliases: 
banner: https://api.neix.in/random/pc
tags: 
createDate: 2025-11-03 14:25
modifyDate: 2025-11-03 14:55
cssclasses:
---

# ▷ AutoAni

计划重新做一个小程序，目标就是刮削 Bangumi，获取对应剧集。

---

## 计划

1. 跟踪 MikanAni“我的”订阅
	1. 通过 `.env` 配置；蜜柑是第一个适配器，以后需要添加新的适配器。
2. 从中拆解出关键元素，加入新番订阅列表，然后“屏蔽”
	1. 订阅列表用 sqlite 存储，表为 `series`
	2. 为了保持唯一性，使用 `TMDB_id` 为唯一值
3. 刮削订阅列表，获取剧集列表
	1. 采用 sqlite 存储，表为 `episodes`
	2. 为了保持唯一性，使用 `TMDB_id` 为唯一值
4. 存在性检查，避免重复下载
	1. 定期检测 openlist，逆向解析剧集信息，存储进 `openlist`
	2. 为了保持唯一性，使用 `TMDB_id` 为唯一值
5. 新番订阅列表定期失活；在达到定额后直接失活
6. Telegram Bot 集成
	1. 查看全部剧集信息（分为新番、老番，一个命令多个按钮实现）
	2. 查看对应系列的全部已下载剧集
	3. 添加订阅（单条）
	4. 删除订阅（同步删除 openlist 内容）
