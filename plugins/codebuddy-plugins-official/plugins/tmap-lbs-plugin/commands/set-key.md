---
description: "设置腾讯地图 Web Service API Key"
argument-hint: "[your_api_key]"
---

设置腾讯地图 Web Service API Key，用于 POI 搜索、路线规划等服务。

## 使用说明

用户提供了以下 Key：$1

请按照以下步骤执行：

1. 如果用户提供了 Key，将其保存到配置文件
2. 如果用户未提供 Key，引导用户前往 [腾讯位置服务](https://lbs.qq.com/dev/console/key/add) 创建应用并获取 Key
3. 也可以通过设置环境变量 `TMAP_WEBSERVICE_KEY` 来配置

## 获取 Key 的步骤

1. 访问 [腾讯位置服务控制台](https://lbs.qq.com/dev/console/application/mine)
2. 创建应用
3. 添加 Key，选择 "WebServiceAPI" 类型
4. 复制生成的 Key

## 示例

- `/tmap-lbs-plugin:set-key XXXXX-XXXXX-XXXXX-XXXXX` — 设置 API Key
- `/tmap-lbs-plugin:set-key` — 查看如何获取 Key
