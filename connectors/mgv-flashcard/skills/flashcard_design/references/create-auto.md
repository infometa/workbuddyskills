# 闪卡 · 自动练习模式（学员）

> 默认交付物：C端系列课详情链接（learnUrl）。适用于 **B 端学员 / C 端学员**（鉴权后无课程管理功能权限）。

## 工作流

```text
Step 1: training.flashcard.create()
        → { courseId, courseName, useTo: 4 }
        注意：此时课程为空（0 题）——learnUrl 此刻还没有，不要宣告「课程创建成功」，
        只报中间态（如「课程骨架已就绪，正在出题…」）

Step 2: (可选) training.file.upload_document(fileContent=base64, fileName=xx, knowledge_type=0)
        → fileId → 轮询 training.file.status 至 parseStatus=2

Step 3: training.flashcard.update(courseId, message=用户原话, metadata.fileIds=[fileId])
        → taskId（status=running）

Step 4: 每 5 秒 training.flashcard.update_status(courseId, taskId)
        → status=done 时检查 response 是否为 GATE 方案确认请求

Step 5: 若为 GATE → 向用户转述方案 → 用户同意后发送确认语再次 update
        → 生成轮 1~2 分钟 → done 后 response 为最终结果
        （学员路径：内容达标后服务端自动建个人系列课，
         done 的 update_status 响应携带 seriesCourseId + learnUrl）

Step 6: training.flashcard.get(courseId) 验题
        → questions 数量/题型/内容是否覆盖用户需求

Step 7: 将 learnUrl 交付给用户：直接点击开始练习
```

## 关键规则

- **learnUrl 延迟交付**：create 不返回 learnUrl；全部题目生成后服务端自动建个人系列课，done 的 update_status 响应携带 seriesCourseId + learnUrl，此时才交付。
- **GATE 确认门**：首轮 update 的 response 通常是方案确认请求（如"是否开始生成？"），必须向用户转述并征得同意后才发确认轮。详见 SKILL.md GATE 段。
- **fileIds 重复携带**：多轮编辑中重复携带同一 fileIds 是合法且必要的（服务端指纹去重 + 陈旧文件恢复）。
- **编辑隔离**：useTo=4 的课程仅创建者本人可编辑，其他学员调用 update 返回 43502。
- **verbatim**：message 必须是终端用户输入的原话，不要改写/总结/翻译。
