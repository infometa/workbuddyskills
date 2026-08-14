# 输出模板

> 模型在部署流程特定节点向用户汇报时，**必须严格使用以下模板**。
> 本文件由 `writing-plans.md` 和 `SKILL.md` 在部署阶段引用。

---

## 预览确认模板

`full-deploy` 成功后，在弹出确认按钮**之前**，必须先输出以下内容让用户预览。

### 模板

```markdown
### 🔍 预览就绪

| | |
|---|---|
| 项目ID | {projectId} |
| 预览地址 | [点击预览](http://{ip}:{port}) |
| 状态 | 🟢 预览中 |
```

### 后续动作

输出模板后**紧接着**弹出 `ask_followup_question`：

```json
[{
  "id": "confirm-publish",
  "question": "请点击上方预览地址确认页面效果。确认无误后点击下方按钮完成HRClaw平台注册。如需修改，直接在对话框中输入即可。",
  "options": [
    "确认注册"
  ],
  "multiSelect": false
}]
```

### 硬性约束

- 预览地址**必须以 markdown 超链接形式输出**（`[点击预览](http://...)`），方便用户直接点击
- 确认按钮**紧跟**模板之后，不插入其他内容

---

## 部署输出模板

`publish` 成功后向用户汇报最终结果时使用。

### 模板

```markdown
### 🎉 部署完成，待上线

| | |
|---|---|
| 项目ID | {projectId} |
| 版本 | v{version} |
| 状态 | 🟡 已创建 |
| 管理端地址 |  [应用详情页]({publicUrl}) |

> {功能概述一句话}

**下一步**：前往[应用详情页]({publicUrl})，点击 **『发布上线』** 按钮，生成可访问的线上地址。
```

### 占位符来源

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{projectId}` | `.deploy-state.json` 的 `projectId` 字段 | — |
| `{version}` | `anydev publish` 返回的 `data.packUpload.version` | — |
| `{publicUrl}` | `anydev publish` 返回的 `data.url` | Gateway 注册成功后回传的 OA 认证公开访问 URL。**严禁**自行拼接或猜测。 |

### 硬性约束

- **禁止**出现容器 ID（envInsId）等内部信息
- **禁止**在模板外附加额外表格或信息块
- **禁止**自行拼接 / 猜测 `{publicUrl}`，必须从 `publish` 返回的 `data.url` 读取
- 功能概述仅限一句话，不超过 80 字
- 必须包含 Admin 上线指引（下一步）
