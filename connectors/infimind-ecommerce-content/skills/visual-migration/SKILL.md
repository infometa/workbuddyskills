---
name: visual-migration
description: 在用户要参考爆款商品图的视觉结构为新商品生成图片时，创建爆款图复制任务并查询结果。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 爆款图复制

## 使用时机

用于读取参考图的构图、布光和表达方式，为目标商品生成结构同类的新图。这不是逐像素复制、商标仿冒、人物身份保留，也不是爆款视频复制。

## 调用流程

1. 选择一种输入：一张参考图配 1～20 张商品图，或 1～20 组逐组配对。两种形式不同时传入。
2. 为每张商品图收集可选主体描述，并确认模型、比例、分辨率和质量。
3. 仅传 HTTPS 素材 URL，说明当前 OAuth 空间和计费边界，调用 `create_visual_migration_task`。
4. 使用创建返回的 `taskId` 与 `taskType=visual_migration` 调用 `get_user_tasks`。
5. 只返回当前任务的固化结果；超时、失败或部分成功时不得自动重建任务。

## 工具与参数

### `create_visual_migration_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `referenceImage` | 方式 A | 共用视觉参考图 HTTPS URL |
| `productImages` | 方式 A | 1～20 张商品图 HTTPS URL |
| `subjectDescriptions` | 否 | 与 `productImages` 同顺序，每项最多 40 字符 |
| `pairs` | 方式 B | 1～20 组 `{referenceImage, productImage, subjectDescription?}` |
| `aspectRatio` | 否 | 输出比例；`auto` 仅 GPT Image 2 支持 |
| `resolution` | 否 | 公开分辨率，服务端按模型重验 |
| `quality` | 否 | `low` / `medium` / `high` |
| `model` | 否 | 当前公开图像模型 |

方式 A 和方式 B 二选一。不要把展示名称、本地文件或未授权资源 ID 放入 URL 字段。

### `get_user_tasks`

| 参数 | 用法 |
| --- | --- |
| `taskId` | 创建返回的任务 ID |
| `taskType` | 固定为 `visual_migration` |
| `status` | 可选状态筛选 |
| `limit` | 精确查询时取最小值 |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；创建、查询和结果访问均由服务端鉴权。
- 仅传 HTTPS URL，禁止本地路径、base64、localhost、私网/保留地址或供应商临时 URL。
- 不得使用无授权参考素材，不得复制原品牌标识、人物身份或未经商品图证实的产品事实。
- 数量、素材、权限和积分最终以服务端校验和业务表为准。

## 错误处理

对外仅解释稳定公开错误码和可操作建议，不透传供应商错误、原始分析、提示词、存储 key 或内部 URL。输入配对、权限、余额或内容安全错误需先修正，不自动重试创建。
