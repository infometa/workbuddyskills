> 迁移自源技能 §异步任务生命周期、§建课完成的判断标准、§两种完成的区分，业务规则以本文为准

# 结果核实与进度语义

## 异步任务的生命周期

`ai_customer.update` 秒返 taskId，后台异步处理。任务状态通过 `ai_customer.update_status` 轮询：

| 状态 | 含义 | 下一步 |
|------|------|--------|
| `running` | 后台正在处理 | 5s 后重查 |
| `done` | 本轮对话结束 | 调 `ai_customer.get` 验证课程是否建成 |
| `failed` | 任务失败 | 读 errorMessage，决定重试或报告 |

## 两种"完成"的区别（⚠️ 极易混淆）

**任务完成 ≠ 课程创建完成**

| 概念 | 含义 | 判断方式 | 常见误导 |
|------|------|----------|----------|
| **任务完成** | `update_status` 返回 `status="done"` | 本轮对话结束 | AI 可能只是提问、生成计划 |
| **课程创建完成** | 课程真正创建成功 | `ai_customer.get` 返回 `status="create_status_created"` 且 `stages.length > 0` | 无 |

### update_status done 的陷阱

```json
{
  "status": "done",
  "response": "课程已创建完成"
}
```

- `status: "done"` 只表示本轮对话结束
- `response` 只是 AI 说的话，可能具有误导性
- **这不代表课程已经创建！**

### 正确的判断逻辑（唯一判断标准）

```javascript
const config = await call_tool('training.ai_customer.get', {courseId});
const isCreated = config.status === 'create_status_created' && config.stages.length > 0;
```

必须验证的字段：

- ✅ `status === "create_status_created"`
- ✅ `stages.length > 0`
- ✅ `evaluates.length > 0`（通常）

**不要依赖**：

- ❌ `update_status` 的 status 字段
- ❌ AI 助手的回复文字（"建课完成"、"课程已生成"等）
- ❌ 任务的运行状态

### AI 助手的回复具有误导性（实测发现）

| AI 回复 | 实际状态 | 说明 |
|---------|----------|------|
| "建课完成" | `status="create_status_prepare"` | AI 只是完成了对话，还没创建课程 |
| "课程已生成" | `stages=[]` | AI 在描述计划，不是实际创建 |
| "配置已满足要求" | 字段值未变 | AI 幻觉，实际未修改 |

**原则：只信 `ai_customer.get` 的字段值，不信 AI 回复文字。**

## 响应数据位置与错误封装

- 业务数据在 `result.structuredContent` **顶层**（如 `{"count":..,"courseList":[..]}`、`{"courseId":..}`），**无 `.data` 信封**
- 错误时 structuredContent 为 null，错误 msg 在 `result.content[0].text`
- 后端业务错误一律封装为 `isError: true` + 原始 msg
- 字段转换：后端 snake_case 字段经服务自动转 camelCase
- 认证透传：工具调用自动使用当前认证用户的凭据

## 轮询纪律

1. **每 5 秒一次**：`update_status` 轮询间隔 5s
2. **全程静默**：轮询期间禁止询问用户"还在吗"
3. **最长 10 分钟**：`update_status` 总时长未超 10 分钟，不要重新调用 `update`
4. **完成后验证**：`done` 后立即 `get` 验证课程状态
5. **内容未就绪**：`get` 返回 stages 为空，等 30s 再查一次（agent 可能仍在写入）

## 实测经验标注（M07）

本文量化经验（3-6 分钟建课、5s 轮询间隔、10 分钟轮询上限、60s 冷却期）适用日期 **2026-09-21**，**测试环境（服务版本未记录）**，为阶段性实测结论，不得直接断言为服务端确定行为；生产环境或服务升级后需复测更新。
