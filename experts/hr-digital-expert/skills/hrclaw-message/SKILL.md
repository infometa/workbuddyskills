---
name: hrclaw-message
description: 当用户在自己搭建的 AI 生成网页（前端页面）中需要集成"发送邮件"或"发送企业微信 Tips"能力时使用。只要用户提到在页面里想要发邮件、发企微消息、通知同事、给某某同学发通知、一键给团队群发邮件、页面上加一个"发送"按钮、集成消息推送、调用 HR 消息通道等需求，就应当触发本 skill。即便用户没有明确说"HRClaw"，只要场景是"AI 生成/自建网页 → 发消息给员工"，都使用本 skill 指导接口集成。
---

# HRClaw 消息发送接口集成指南

本 skill 指导如何在 AI 自动生成的网页中集成 HRClaw 接口，实现 **发送邮件** 和 **发送企业微信 Tips** 两种能力。

## 适用场景

- 用户搭建的内部工具 / AI 生成页面，想加一个"发送邮件给某几位同事"的按钮
- 页面上想做一个"任务完成后通知相关人"的 Tips 推送
- 任何需要"以当前登录员工身份"向其他员工发消息的场景

## 一、一条铁律：收件人必须通过"员工选择器"组件获取

收件人字段（`receivers` / `cc` / `bcc`）只接受**员工英文名**，不接受邮箱。接口会用正则 `^[A-Za-z][A-Za-z0-9_\-]{1,30}$` 校验，一旦出现 `@` 字符直接拒绝。

因此在页面上：

- **必须**提供员工选择器组件（内部通用组件 / 通讯录选择器），让用户在下拉或弹窗中"选人"，拿到英文名列表
- **绝不**做一个 `<input placeholder="请输入英文名">` 让用户手动填写。一方面容易拼错，另一方面用户很容易习惯性填邮箱导致 40001 报错
- 如果当前代码库里没有现成的员工选择器，集成时应明确向用户指出"需要先接入员工选择器组件"，而不是绕开

## 二、接口基本信息

**请求方法**：`POST`
**Content-Type**：`application/json`

**频率限制**：同一个员工 60 秒内最多 30 次请求（邮件和 Tips 共用配额）。超限返回 `40901`。

## 三、发送邮件

### 接口

`POST https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/mail/send`

### 请求体字段

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `receivers` | `string[]` | 条件必填 | 收件人英文名列表 |
| `cc` | `string[]` | 否 | 抄送英文名列表 |
| `bcc` | `string[]` | 否 | 密送英文名列表 |
| `subject` | `string` | 是 | 主题，≤ 200 字符 |
| `content` | `string` | 是 | 正文，支持 HTML，≤ 500 KB |
| `attachments` | `Record<string,string>` | 否 | key=文件名，value=base64 |

限制要点：

- `receivers` / `cc` / `bcc` 三者至少一个非空，合计数量 ≤ 200
- 每一项必须是员工英文名（严禁邮箱）
- 附件：数量 ≤ 10，单个 ≤ 10 MB（解码后），合计 ≤ 25 MB
- 附件扩展名白名单：`pdf, doc, docx, xls, xlsx, ppt, pptx, png, jpg, jpeg, gif, txt, csv, zip`
- 附件文件名不允许含 `..` / `/` / `\`

### 前端调用示例（fetch）

```javascript
async function sendMail({ receivers, cc, bcc, subject, content, attachments }) {
  const res = await fetch(
    `https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/mail/send`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ receivers, cc, bcc, subject, content, attachments }),
    }
  );
  const data = await res.json();
  return data; // { code, message, data: msgId }
}
```

## 四、发送企业微信 Tips

### 接口

`POST https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/workchat-tips/send`

### 请求体字段

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `receivers` | `string[]` | 是 | 接收人英文名列表，数量 ≤ 100 |
| `title` | `string` | 是 | 标题，≤ 100 字符 |
| `content` | `string` | 是 | 正文，≤ 2000 字符 |

### 前端调用示例

```javascript
async function sendWorkchatTips({ receivers, title, content }) {
  const res = await fetch(
    `https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/workchat-tips/send`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ receivers, title, content }),
    }
  );
  return await res.json();
}
```

## 五、必须完善的结果反馈

接口返回结构统一为：

```json
{ "code": 0, "message": "success", "data": "812964582400000001" }
```

集成时**必须**根据 `code` 区分成功 / 失败，并给到用户清晰的 UI 反馈——不允许静默吞掉。

### 成功处理（`code === 0`）

**必须**把 `data`（`msgId`）展示给用户，例如：

- 成功 Toast：`邮件已发送，消息 ID：812964582400000001`
- 或者在操作记录面板里追加一行，包含 msgId，方便后续查询 / 溯源
- 可把 msgId 设为可复制（点击复制到剪贴板）

不要只显示"发送成功"就完事，msgId 是排查问题唯一的凭证。

### 失败处理（`code !== 0`）

**必须**把后端返回的 `message` 字段原样（或稍加包装）展示给用户，不要替换成自造的"发送失败，请稍后重试"：

```javascript
if (data.code === 0) {
  showSuccess(`发送成功，消息 ID：${data.data}`);
} else {
  showError(`发送失败（错误码 ${data.code}）：${data.message}`);
}
```

### 错误码与用户侧建议

| code | 含义 | 用户应当知道的处理建议 |
| ---- | ---- | ---------------------- |
| 40001 | 参数校验失败 | `message` 会指出具体字段，按提示修改后重试（最常见：收件人填了邮箱、英文名格式不对、附件超限） |
| 40301 | 员工维度黑名单 | 当前登录员工被拉黑，联系管理员。重试无意义 |
| 40302 | 来源站点黑名单 | 当前页面域名被拉黑，联系管理员。重试无意义 |
| 40901 | 触发频率限制 | 60 秒后重试；UI 上可禁用按钮倒计时 |
| 50000 | 服务端异常 | 可指数退避后重试 |

建议在前端封装一个统一的错误处理函数，把上面的建议文案做成 map，让每次错误都给出可执行的反馈，而不是简单的"发送失败"。

## 六、常见踩坑清单

1. **收件人填邮箱**：最高频错误。请直接拒绝在输入框里接受 `@`，强制走员工选择器
2. **静默失败**：只打 `console.error` 不提示用户 → 用户以为发出去了，实际没到。永远展示 `message`
3. **成功不回显 msgId**：出问题后无法追溯。永远展示 `data`
4. **附件未做前端校验**：最好在上传时就按白名单、单文件 10 MB、合计 25 MB 提前拦截，不要等后端报错
5. **批量发送超限**：邮件 200 人 / Tips 100 人是硬上限；超过时在前端分批并展示每批结果

## 七、集成完成自检表

接入完成后，对照下表自检：

- [ ] 收件人通过员工选择器获取，页面上没有"手写英文名"的 input
- [ ] 成功路径展示了 `msgId`，且用户可看到 / 可复制
- [ ] 失败路径展示了后端返回的 `message` 原文，并针对 40901 等给出对应建议
- [ ] 附件场景：前端做了扩展名、大小、数量的预校验
