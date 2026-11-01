---
name: flashcard_design
description: 通过 OmniMay MCP 工具对话式创建/编辑闪卡（考官V2）课程，支持上传文档作为出题素材。自动根据用户权限路由双发布模式（管理员=编辑链接 / 学员=自动练习）。触发：用户要建闪卡课/考官课/出题/改题数/基于文档出题。
---

# 闪卡（考官V2）MCP 对话式建课/编辑

用 6 个 MCP 工具完成「建课 → 上传文档 → 对话出题 → 轮询取果 → 验题 → 增量编辑」。

## 工具总览

| 工具 | 用途 |
|---|---|
| `training.flashcard.create` | 创建闪卡课（**双发布模式**：自动路由管理员/学员路径） |
| `training.flashcard.update` | 对话式建课/编辑（**异步**：提交即返 `taskId`） |
| `training.flashcard.update_status` | 轮询任务状态，取最终回复或失败原因 |
| `training.flashcard.get` | 读取课程详情（题目/配置/答案），用于验题 |
| `training.file.upload_document` | 上传文档（base64），返回 `fileId`；自动触发解析 |
| `training.file.status` | 轮询文件解析状态（`parseStatus`） |

## 双发布模式（create 自动路由）

| 角色 | useTo | 默认交付物 | learnUrl |
|---|---|---|---|
| 管理员（有课程管理权限） | 0 | `editUrl` + `manageUrl` | ❌ 不生成 |
| 学员（无权限） | 4 | `seriesCourseId` + `learnUrl`（done 后经 update_status 返回） | ✅ 内容生成后 |

- 管理员：将 `editUrl` 交给用户在B端编辑页检查；`manageUrl` 为管理列表。
- 学员：内容生成完成后再交付 `learnUrl`（create 时课程为空）。
- **编辑隔离**：`useTo=0` 仅管理员可编辑；`useTo=4` 仅创建者可编辑。

## 核心工作流

```text
1. create → courseId
2. (可选) upload_document → fileId → status 至 parseStatus=2
3. update(courseId, message 原话, metadata.fileIds)
   → taskId（status=running）
4. 每 5 秒 update_status 轮询至 done/failed
5. ⚠ GATE 确认门检测 → 方案请求需走确认轮（→ references/gate-detection.md）
6. get 验题 → 交付 editUrl 或 learnUrl
```

## ⚠ GATE 确认门

done 后的 response 可能是「方案确认请求」或「中间生成状态」而非成品。
必须向终端用户转述方案并征得同意后再发确认轮。关键词列表与检测逻辑见 → `references/gate-detection.md`。

## 硬性规则

1. `message` 必须是终端用户**原话**（verbatim），禁止改写/翻译/合并。
2. `fileIds` 正整数、去重、≤20；重复携带合法且必要。
3. 不要对同一 courseId 并行发起多个 update（43503）。
4. 管理员建课后不要自动创建练习任务。
5. `learnUrl` 延迟交付：内容生成并验题后再交付。
6. **禁止提前宣告「课程创建成功」**：create 只建了 0 题空壳；全部题目生成且 get 验题通过后才可宣告「创建成功/已完成」。create 后只能报中间态（如「课程骨架已就绪，正在出题…」）。

## 错误码速查

详见 → `references/error-codes.md`

| 常见 | 含义 |
|---|---|
| 42901 | 积分不足 |
| 43502 | 无编辑权限（use_to=0 仅管理员） |
| 43503 | 生成中，稍后再试 |
| 43505 | fileIds 非法 |

## 文档索引

| 文件 | 内容 |
|---|---|
| `references/gate-detection.md` | GATE 关键词全表 + 检测逻辑 |
| `references/error-codes.md` | 全量错误码 + 应对 |
| `references/file-reference.md` | 文件上传/解析/引用详细规则 |
| `references/multi-turn-editing.md` | 多轮编辑 + verbatim 详规 |
| `references/known-behaviors.md` | 服务端已知怪癖 |
