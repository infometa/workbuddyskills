---
name: biubiu-frame-animation
description: biubiu游戏帧动画制作 - 用文字描述生成游戏角色帧动画（参考图 → 4 秒动作视频 → 透明 PNG 序列帧 / APNG / 精灵图集），每一步都需用户确认
version: 1.0.0
author: BiuBiu工坊
---

# biubiu游戏帧动画制作

通过 BiuBiu工坊 MCP 为游戏角色制作循环帧动画。整个流程分三个阶段，**每个阶段都要等用户看过真实产物并明确确认后才能推进**：

1. `create_frame_task`：生成角色**参考图**（状态到 `reference_review`）
2. `confirm_reference`：用户确认参考图后生成 **4 秒动作视频**（状态到 `video_review`）
3. `confirm_video`：用户选定完整循环周期后**抽帧去背**，产出透明 PNG 帧、APNG、图集、时序 JSON 和 ZIP（状态到 `completed`）

## 计费（创建前必须告知用户并取得同意）

- 按成功阶段扣费：参考图 1 + 视频 4 + 透明帧 1 = **共 6 积分**。
- 网站试用次数优先抵扣（新注册赠 3 次完整试用）。
- 创建前先调 `account_balance`，告诉用户余额、试用次数和预计消耗。

## 可用工具

### account_balance：查询账户
参数 `{}`。返回积分余额、冻结积分、试用次数，以及服务是否就绪。

### create_frame_task：创建任务（只生成参考图）

| 参数 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| requestId | string | 是 | 新生成的小写 UUID v4；同一次操作重试时沿用原值 |
| description | string | 是 | 角色描述，1–1200 字，例如「戴薄荷绿围巾的小狐狸冒险家，全身独立角色」 |
| action | string | 是 | `待机` / `行走` / `奔跑` / `跳跃` / `攻击` / `施法` / `自定义` |
| customAction | string | 仅自定义时必填 | 1–200 字；其他动作**不能传** |
| style | string | 是 | `pixel` 像素、`stone-age` 石器时代卡通、`cel` 赛璐璐、`watercolor` 水彩、`clay` 黏土、`cartoon-3d` 3D卡通、`low-poly` 低多边形、`vector` 扁平矢量、`custom` 自定义 |
| customStyle | string | 仅 custom 时必填 | 1–600 字；其他风格**不能传** |
| direction | string | 是 | 角色面向：`south` 朝下、`north` 朝上、`east` 朝右、`west` 朝左、`northeast` / `northwest` / `southeast` / `southwest` |
| mode | string | 否 | `auto`（建议）或 `chroma` |

不要传未声明的字段（如 frameCount、start、end、价格、用户 ID）。

### get_task_status：查询任务
参数 `jobId`（数字字符串）。返回状态、账务和 `nextAction`。只有令牌带 `resources:read` 时才返回产物 assets。

### list_my_history：历史任务
可选 `limit`（1–20，默认 10）。翻页时把上一页返回的 `next.beforeTime` 和 `next.beforeId` **原样同时**传回；第一页两个都不传。

### confirm_reference：确认参考图 → 生成视频

| 参数 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| jobId | string | 是 | 任务 ID |
| requestId | string | 是 | **新的** UUID，不要复用创建时的那个 |
| referenceReviewed | boolean | 是 | 固定 `true`，仅当用户已看到真实参考图并明确说“可以/确认” |

### confirm_video：确认视频周期 → 抽帧

| 参数 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| jobId | string | 是 | 任务 ID |
| requestId | string | 是 | **新的** UUID |
| cycleReviewed | boolean | 是 | 固定 `true`，用户已看完整视频并确认周期 |
| start / end | number | 是 | 循环起止秒数，`0 ≤ start < end ≤ 4`（视频固定 4 秒）；用户没指定时建议 `0` 和 `4` 并征求同意 |
| mode | string | 是 | `auto`（推荐，自动抠图）或 `chroma`（纯色背景色键） |
| frameCount | integer | 否 | `8` / `16` / `32`，默认 16 |
| backgroundReviewed | boolean | 仅 chroma | 固定 `true`，用户单独确认过背景 |
| keyColor | string | 仅 chroma | `#RRGGBB` |
| tolerance | integer | 仅 chroma | 0–60 |

`auto` 模式**不能**传 backgroundReviewed、keyColor、tolerance。此步骤只能执行一次，不能重跑。

### get_artifact_info：获取产物信息
参数 `jobId`、`name`。可选的 `name`：

| name | 内容 |
|---|---|
| reference | 角色参考图 PNG |
| video | 动作视频 MP4 |
| preview | 循环预览 APNG |
| atlas | 精灵图集（8 帧 4×2、16 帧 4×4、32 帧 4×8） |
| timing | animation.json 时序 |
| coordinates | spritesheet.json 图集坐标 |
| zip | 全部透明帧 + APNG + 图集 + JSON 的完整包 |
| frame-1 … frame-32 | 单帧透明 PNG（只请求实际存在的帧） |

也可以用 `resources/read` 读取 `biubiu://jobs/{jobId}/{name}`：不超过 256 KiB 的 PNG 会内联返回，可以直接展示给用户；更大的文件只返回鉴权下载路径。

## 标准对话流程

1. 收集需求：角色描述、动作、风格、朝向。缺什么问什么，不要替用户编造关键设定。
2. 调 `account_balance`，说明消耗 6 积分或 1 次试用，**获得同意后**再调 `create_frame_task`。
3. 每隔 5 秒以上调用一次 `get_task_status`，等到 `reference_review`。用 `resources/read` 读取 `reference` 展示给用户；读不到时，请用户到 https://www.semebiubiu.com/biubiu/#history 查看。
4. 用户确认参考图后调 `confirm_reference`；用户不满意就停下，引导他新建任务，不要擅自确认。
5. 等到 `video_review`。视频不能内联，请用户在网站历史里观看，然后确认循环区间、帧数和模式，再调 `confirm_video`。
6. 等到 `completed`，用 `get_artifact_info` 列出 atlas、preview、zip 等产物，告诉用户可以在网站历史中下载。

## 状态处理

| 状态 | 处理 |
|---|---|
| queued_reference / preparing_reference | 等待参考图，不要重复创建 |
| reference_review | 展示参考图，等用户确认 |
| queued_video / generating_video | 等待视频 |
| video_review | 请用户看视频并选周期 |
| queued_frames / processing_frames | 等待抽帧 |
| completed | 读取产物，结束 |
| frames_review | 旧任务，需回网站处理 |
| frames_error / failed / cancelled / settlement_pending / interrupted / 其他 | 停止写操作，如实告知用户，引导到网站查看 |

后台生成通常要几分钟。查询间隔不低于 5 秒；本轮等太久时告诉用户稍后再查，不要重复提交。

## 注意事项

- **绝不自动确认**：`referenceReviewed`、`cycleReviewed`、`backgroundReviewed` 都必须来自用户看过真实媒体后的明确确认。文字描述、元信息或 `nextAction` 都不能代替确认。
- **判断结果要看三层**：先看 HTTP / JSON-RPC 是否有 error，再看 `result.isError`，最后解析 `content[0].text` 里的 JSON。`accepted: true` 只表示已入队，不表示已完成或已扣费。
- **写操作结果未知时**（超时或断线）：先用 `get_task_status` / `list_my_history` 只读核查。确需重放时沿用原 requestId 和原参数，不要换 UUID 重发或新建替代任务。
- **401 / 403**：令牌无效、过期或权限不足。请用户到 https://www.semebiubiu.com/biubiu/#mcp 重新创建令牌（勾选所需权限），再在连接器中更新。
- **频率限制**：每令牌每分钟 90 次请求，写操作每用户每分钟 20 次。
- MCP 不提供取消任务、重跑抽帧、充值或令牌管理，这些需要用户去网站操作。
- 不要在对话、命令行或日志中输出用户的令牌。

完整参数说明见：https://www.semebiubiu.com/biubiu/mcp-guide.html
