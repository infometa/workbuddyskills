# 生成约束与媒体角色

指定 Model 和动态参数时，只增加一个 Generation Constraints Part；`model` 使用 Model 机器标识，`arguments` 的字段和值取自 `model get`，并如实保留用户指定值：

```json
{
  "message": {
    "parts": [
      { "text": "<用户要求>" },
      {
        "data": {
          "model": "<model>",
          "arguments": {
            "<parameter>": "<value from model detail and user request>"
          }
        }
      }
    ]
  }
}
```

`arguments` 可以在不指定 `model` 时单独提交，由服务端 Agent 选择 Model。指定 `model` 时，CLI 会按实时 Model detail 校验已提供参数；不要为了 Agent 调用补齐 Tool 的全部 required 字段。Prompt 使用 Text Part，素材使用独立 URL Part，不放入 `arguments`。素材保持消息 Part 的输入顺序；`metadata.role` 可标记 `reference`、`first_frame` 或 `last_frame`，不注入“首帧”或“尾帧”文本。例如：

```json
{
  "message": {
    "parts": [
      { "text": "生成一段转场视频" },
      { "url": "file:///absolute/first.png", "metadata": { "role": "first_frame" } },
      { "url": "file:///absolute/last.png", "metadata": { "role": "last_frame" } },
      { "data": { "model": "<model>", "arguments": { "mode": "<value>" } } }
    ]
  }
}
```
