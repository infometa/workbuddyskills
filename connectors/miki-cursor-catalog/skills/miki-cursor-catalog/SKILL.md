---
name: miki-cursor-catalog
display_name: Miki Cursor 素材库
display_name_en: Miki Cursor Catalog
description: 查询 Miki Cursor 最新宠物、光标、轨迹和指定宠物可用动作；适用于“最新宠物”“最新光标”“最新轨迹”“某宠物有哪些动作”等请求。
description_zh: 查询 Miki Cursor 最新公开素材及指定宠物拥有的动作。
description_en: Browse the latest public Miki Cursor assets and the actions available for a specified pet.
version: 1.0.0
author: Miki Cursor
user-invocable: false
---

# Miki Cursor 素材库

通过连接器提供的 MCP 工具查询 Miki Cursor 网站已经公开发布的宠物、光标、轨迹和宠物动作。所有操作均为只读查询，不需要用户登录或授权。

## 工具选择

### `get_latest_pets`

当用户询问最新宠物、最近新增的宠物或推荐查看新宠物时调用。

- `locale`：可选。中文请求使用 `zh`，英文请求使用 `en`。
- 返回最新发布的 5 个宠物及其公开信息。

### `get_latest_cursors`

当用户询问最新光标样式或最近新增的光标时调用。

- `locale`：可选。中文请求使用 `zh`，英文请求使用 `en`。
- 返回最新发布的 5 个光标及其公开信息。

### `get_latest_trails`

当用户询问最新鼠标轨迹或最近新增的轨迹时调用。

- `locale`：可选。中文请求使用 `zh`，英文请求使用 `en`。
- 返回最新发布的 5 个轨迹及其公开信息。

### `get_pet_actions`

当用户询问某个宠物有哪些动作，或者某个宠物是否会执行某项动作时调用。

- `petName`：必填。传入用户提到的宠物中文名或英文名，例如“小狐狸”“小青龙”“小猫”或“Puppy”。
- `locale`：可选。中文请求使用 `zh`，英文请求使用 `en`。

## 执行规则

1. 必须根据用户的问题选择对应 MCP 工具，不使用网页搜索代替已有工具。
2. 用户使用中文时默认传入 `locale: "zh"`；使用英文时传入 `locale: "en"`。
3. 只陈述 MCP 返回的宠物、素材和动作，不猜测或虚构结果。
4. 如果宠物名称没有匹配结果，直接说明未找到已发布宠物。
5. 如果名称匹配到多个宠物，列出候选项并请用户进一步指定。
6. 用户询问某个宠物会不会某动作时，先调用 `get_pet_actions`，再根据返回的动作列表回答。

## 示例

- “查询最新5个宠物” → 调用 `get_latest_pets`。
- “最近新增了哪些光标？” → 调用 `get_latest_cursors`。
- “给我看看最新的鼠标轨迹” → 调用 `get_latest_trails`。
- “小青龙有哪些动作？” → 调用 `get_pet_actions`，`petName` 传入“小青龙”。
- “小狗会打招呼吗？” → 调用 `get_pet_actions`，然后检查返回动作中是否包含“打招呼”。

## 错误处理

- 工具超时或服务暂时不可用时，说明查询暂时失败并建议用户稍后重试。
- 参数错误时，根据工具输入结构修正参数后最多重试一次。
- 本连接器无需认证；不要要求用户提供密码、Token、Cookie 或其他凭据。
