# 闪卡 · 编辑链接模式（管理员，人工发布）

> 默认交付物：B端编辑页链接（editUrl）+ 课程管理页链接（manageUrl）。适用于 **B 端管理员**（鉴权后有课程管理功能权限）。AI 不主动发布任务。

## 工作流

```text
Step 1: training.flashcard.create()
        → { courseId, courseName, useTo: 0, editUrl, manageUrl }
        注意：此刻是空壳（0 题），不要宣告「课程创建成功」，只报中间态
        （如「课程骨架已就绪，正在出题…」；editUrl 可先给，供用户随时查看）

Step 2: (可选) training.file.upload_document(fileContent=base64, fileName=xx, knowledge_type=0)
        → fileId → 轮询 training.file.status 至 parseStatus=2

Step 3: training.flashcard.update(courseId, message=用户原话, metadata.fileIds=[fileId])
        → taskId（status=running）

Step 4: 每 5 秒 training.flashcard.update_status(courseId, taskId)
        → status=done 时检查 response 是否为 GATE 方案确认请求

Step 5: 若为 GATE → 向用户转述方案 → 用户同意后发送确认语再次 update
        → 生成轮 1~2 分钟 → done 后 response 为最终结果

Step 6: training.flashcard.get(courseId) 验题
        → questions 数量/题型/内容是否覆盖用户需求

Step 7: 交付 editUrl + manageUrl：
        "课程已生成。请在编辑页检查内容，确认无误后在课程管理页发布。"

（可选）Step 8: 用户明确要求"生成学习入口/创建任务"时：
        → training.task.create_open_project({courseId: <id>})
        → 返回学习任务链接（可与 editUrl 一并交付）
```

## 与自动练习模式的差异

| 环节 | 自动练习（学员） | 编辑链接（管理员，本模式） |
|------|----------------|--------------------------|
| 课程 useTo | 4（学员个人） | 0（普通课程） |
| 默认交付物 | learnUrl（C端系列课详情） | editUrl + manageUrl（B端编辑/管理页） |
| 默认发布动作 | 建课完成即自动创建个人系列课 | **不主动发布**，管理员在B端人工确认 |
| 后续可否生成学习入口 | 可（默认动作） | 可，但**仅限用户明确要求时**调用 create_open_project |

## 关键规则

1. **默认只返回 editUrl/manageUrl**，不要在建课收尾时主动生成学习入口。
2. `training.task.create_open_project` **不禁止**，但仅限用户明确要求时调用。
3. 建课完成 ≠ 发布完成：向用户明确"默认发布需在管理端人工确认"。
4. **编辑隔离**：useTo=0 的课程仅管理员可编辑，学员调用 update 返回 43502。
5. **GATE 确认门**：首轮 update 的 response 通常是方案确认请求，必须走确认轮。详见 SKILL.md GATE 段。
