---
name: detail-page
description: 在用户要根据商品图和商品信息生成多张电商详情页时，创建详情页任务并精确查询结果。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 商品详情页

## 使用时机

用于生成 5～10 张一组的电商详情页。如只要单张精修、商品主图、KOC 拼图或视频，使用对应 Skill。

## 调用流程

1. 收集 1～5 张商品图、商品类目，可选收集最多 5 张参考详情图。
2. 参考图为空时必须询问生成风格；确认语言、数量、卖点/参数和可选 AI 模特。
3. 仅传 HTTPS 素材 URL，说明将使用当前 OAuth 空间并按服务端计费，调用 `create_detail_page_task`。
4. 保留返回的任务 ID，用 `get_user_tasks` 传入该 `taskId` 和 `taskType=detail_page` 查询到终态。
5. 告知用户实际成功图数；超时、失败或部分成功时不得自动重建任务。

## 工具与参数

### `create_detail_page_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `productImages` | 是 | 1～5 张商品图 HTTPS URL |
| `referenceImages` | 条件 | 最多 5 张参考详情图；与 `generationStyle` 至少提供一项 |
| `productCategory` | 是 | 商品类目 |
| `generationStyle` | 条件 | 参考图为空时提供的风格描述 |
| `language` | 否 | 输出语言，默认简体中文 |
| `extraDescription` | 否 | 卖点、尺寸参数或指定文案等补充要求 |
| `imageCount` | 否 | 5～10，默认 5 |
| `aiModelId` | 否 | 已授权 AI 模特 ID |
| `aspectRatio` | 否 | 默认 `3:4`；`auto` 仅 GPT Image 2 支持 |
| `resolution` | 否 | 公开分辨率，服务端按模型能力校验 |
| `model` | 否 | 当前公开图像模型 |

### `get_user_tasks`

| 参数 | 用法 |
| --- | --- |
| `taskId` | 创建返回的任务 ID |
| `taskType` | 固定为 `detail_page` |
| `status` | 可选状态筛选 |
| `limit` | 精确查询时取最小值 |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；他人任务和素材不可使用。
- 仅传 HTTPS URL，不传本地路径、`data:`/base64、localhost、私网、供应商 URL 或签名存储查询串。
- 服务端重验 MIME/magic、尺寸、数量、模型能力、空间权限和积分；客户端显示不是计费事实。
- 商品功效、参数、价格和认证必须来自用户素材；不负责据参考图臆测。

## 错误处理

使用稳定公开错误码解释要修改的素材、参数、权限或余额；不透传供应商错误、原始提示词、存储地址或内部堆栈。不自动重试会产生新任务或扣费的操作。
