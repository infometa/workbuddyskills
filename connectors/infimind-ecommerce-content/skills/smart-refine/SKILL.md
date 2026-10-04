---
name: smart-refine
description: 在用户要求保留商品主体并精修、换景、优化光影或画质时，创建智能精修任务并查询结果。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 智能精修

## 使用时机

用于商品图精修、光影/画质改善、背景或陈列调整等单图编辑诉求。如用户要的是多张商品主图策划、详情页、参考图结构复制或视频，使用对应 Skill。

## 调用流程

1. 收集待精修图和明确的精修要求；本 OAuth 远程 Connector 只向工具传递可安全访问的 HTTPS 素材 URL。
2. 在提交前说明会使用当前 OAuth 授权的工作空间并按服务端规则计费。
3. 调用 `create_smart_refine_task`，保留返回的任务 ID。
4. 用 `get_user_tasks` 传入该 `taskId` 和 `taskType=smart_refine` 查询，不使用模糊列表猜测任务。
5. 处理中告知用户稍后查询；完成后返回固化结果。失败或查询超时时不得自动重建任务。

## 工具与参数

### `create_smart_refine_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `images` | 是 | 待精修图 HTTPS URL 数组 |
| `prompt` | 是 | 应改变什么、保留什么的明确要求 |
| `modelId` | 否 | 已授权 AI 模特 ID；不得代填未授权 ID |
| `aspectRatios` | 否 | 输出比例数组；`auto` 仅 GPT Image 2 支持 |
| `resolution` | 否 | `1k` / `2k` / `3k` / `4k`，服务端按模型校验 |
| `model` | 否 | 当前公开图像模型，不传供应商内部路由 |

### `get_user_tasks`

| 参数 | 用法 |
| --- | --- |
| `taskId` | 必须使用创建返回的正整数 ID |
| `taskType` | 固定为 `smart_refine` |
| `status` | 可选终态/处理态筛选；精确查询时不必填 |
| `limit` | 精确查询时使用最小值 |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 决定当前用户、个人/企业空间和 operator；不要索要或显示 Token。
- 创建、查看和结果访问都由服务端重验空间所有权；不得尝试他人任务 ID。
- 仅传 HTTPS URL；不传本地路径、`file:`、`data:`、base64、localhost 或私网地址。
- 积分以服务端业务表和实际任务为准；不从文案或客户端状态推断扣费成功。

## 错误处理

向用户说明公开错误码的可操作建议；不透传供应商错误、存储地址或内部提示词。只有错误明确标记可重试且用户同意时才重试；内容安全、权限、余额和素材错误要先修正原因。
