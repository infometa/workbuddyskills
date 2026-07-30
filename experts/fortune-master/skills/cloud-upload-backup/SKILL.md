---
name: cloud-upload-backup
description: "Cloud file upload and backup tool. Upload local files to Tencent SMH cloud storage, viewable in QClaw Mini Program."
metadata:
  openclaw:
    emoji: "☁️"
    requires:
      bins:
        - curl
---

# 云文件上传备份工具 (Tencent SMH)

将本地文件上传至腾讯 SMH 云存储，上传后可在 QClaw 小程序中查看。

## Setup

无需额外安装依赖。文件上传通过本地 HTTP 接口 `/proxy/qclaw-cos` 完成，SMH 凭证由主进程自动管理。

---

## 典型使用场景

- 用户要求上传/备份文件到云端（如"上传文件"、"备份到云"、"传到云空间"）
- 用户要求将任务产出物发送到手机（如"把文件发给我"、"发到手机"、"做完了发我一份"）
- 用户要求上传至 COS（如"上传到cos"、"打包并上传到cos"）
- 用户查询云端文件状态（如"这个云文件还在吗"、"之前上传的文件还能下吗"）

---

## 脚本入口

| 平台 | 入口脚本 |
|------|---------|
| macOS / Linux | `bash scripts/unix/cloud_backup.sh <command> [options]` |
| Windows CMD | `scripts\windows\cloud_backup.cmd <command> [options]` |

脚本自动处理端口获取、JSON 构造、HTTP 请求和响应输出。

---

## 核心流程

```
1. 确定本地文件路径
2. 调用 upload (单文件) 或 batch-upload (多文件) 命令
3. 校验返回 JSON 中 message 字段的 URL 域名 → 输出 message 给用户
```

**关键设计 (Anti-hallucination)**：所有上传命令返回的 `message` 字段是服务端预渲染的完整回复文本（含文件名、大小、链接）。QClaw 校验 URL 域名后直接输出 `message`，**不要**从 `fileUrl`/`fileInfo` 等字段自行拼接。

### URL 域名安全校验

输出 `message` 前，校验其中所有 URL 的域名：

| 可信域名 | 用途 |
|---------|------|
| `jsonproxy.3g.qq.com` | 短链服务 (文件链接) |
| `smh.tencentcs.com` | SMH 预览/文件链接 |

- URL 域名不在白名单 → 不输出该 URL，提示："文件上传成功，但链接地址异常，请联系管理员检查。"
- 不含 URL 的 `message`（错误信息、冲突对话）可直接输出

---

## Commands

### upload — 上传单个文件

```bash
# macOS / Linux
bash scripts/unix/cloud_backup.sh upload --local-path "<path>" [--remote-path "<cloud-path>"] [--conflict-strategy ask|overwrite|rename]

# Windows CMD
scripts\windows\cloud_backup.cmd upload --local-path "<path>" [--remote-path "<cloud-path>"] [--conflict-strategy ask|overwrite|rename]
```

**Parameters：**
- `--local-path`（必填）：本地文件绝对路径，支持 `~` 展开
- `--remote-path`（可选）：云端目标路径，省略则上传到根目录并保留原文件名
- `--conflict-strategy`（可选，**默认必须用 `ask`**）：
  - `ask` — 同名文件存在时返回 HTTP 409，QClaw 询问用户
  - `overwrite` — 仅当用户明确说"覆盖/替换"时使用
  - `rename` — 仅当用户明确说"重命名"时使用

**成功输出：**
```json
{
  "success": true,
  "message": "链接已生成，可在 QClaw 小程序中随时查看。（保留 30 天后自动清理）\n\n已上传文件: photo.jpg (2.0 MB)\n文件链接: https://jsonproxy.3g.qq.com/urlmapper/aB3xYz",
  "fileUrl": "https://jsonproxy.3g.qq.com/urlmapper/aB3xYz"
}
```

→ 校验 `message` 中 URL 域名，通过后直接输出 `message` 内容给用户。

**HTTP 409 — 同名文件冲突：**
```json
{
  "success": false,
  "message": "已存在同名文件 `report.pdf`，你想怎么处理？\n\n1. 🔄 覆盖 — 替换已有文件\n2. 📝 重命名 — 自动改名上传（如 report(1).pdf）\n3. ❌ 取消 — 不上传",
  "conflict": { "fileName": "report.pdf", "remotePath": "report.pdf" }
}
```

→ 输出 `message`，等用户选择后用对应策略重新上传。

**失败输出：**
```json
{
  "success": false,
  "message": "❌ 文件上传失败：文件不存在: /path/to/missing.pdf\n\n你可以：\n1. 🔄 重试\n2. ❌ 取消",
  "error": "文件不存在: /path/to/missing.pdf"
}
```

→ 直接输出 `message`（错误信息通常不含 URL，无需域名校验）。

> 上传成功后短链格式为 `https://jsonproxy.3g.qq.com/urlmapper/xxx`。手机端点击拉起 QClaw 小程序（文件保留 30 天），PC 端打开 H5 扫码页。`rawDownloadUrl` 仅在短链生成失败时作为 fallback 出现。

### batch-upload — 批量上传多个文件

**2 个及以上文件时必须用此命令**，不要多次调用 `upload`。

```bash
# macOS / Linux
bash scripts/unix/cloud_backup.sh batch-upload --files '<JSON array>'

# Windows CMD
scripts\windows\cloud_backup.cmd batch-upload --files "<JSON array>"
```

**`--files` JSON 格式**（最多 20 个）：
```json
[{"localPath":"/path/to/file1.pdf","conflictStrategy":"ask"},{"localPath":"/path/to/file2.docx","conflictStrategy":"ask"}]
```

每项：`localPath`（必填）、`remotePath`（可选）、`conflictStrategy`（可选，默认 `ask`）

> Windows CMD 中 JSON 需转义双引号：`"[{\"localPath\":\"C:\\path\\to\\file.pdf\",\"conflictStrategy\":\"ask\"}]"`

**成功输出：**
```json
{
  "success": true,
  "message": "3 个文件全部上传成功！链接可在 QClaw 小程序中随时查看。（保留 30 天后自动清理）\n\n📎 report.pdf (2.3 MB) — https://jsonproxy.3g.qq.com/urlmapper/aB3xYz\n📎 photo.jpg (1.1 MB) — https://jsonproxy.3g.qq.com/urlmapper/xK9mWq\n📎 data.csv (156 KB) — https://jsonproxy.3g.qq.com/urlmapper/pL2nRt",
  "total": 3, "successCount": 3, "failedCount": 0
}
```

→ 校验 URL 域名后输出 `message`。不要自行汇总/改写批量结果。

### info — 查询云端文件信息

```bash
# macOS / Linux
bash scripts/unix/cloud_backup.sh info --remote-path "report.pdf"

# Windows CMD
scripts\windows\cloud_backup.cmd info --remote-path "report.pdf"
```

### list — 列出云端文件

```bash
# macOS / Linux
bash scripts/unix/cloud_backup.sh list [--dir-path "/"] [--limit 50]

# Windows CMD
scripts\windows\cloud_backup.cmd list [--dir-path "/"] [--limit 50]
```

---

## 文件大小

**无文件大小限制。** 小文件 (≤50MB) 直接上传，大文件 (>50MB) 自动分片上传 (5MB chunks)。不要告诉用户有大小限制。

---

## 冲突处理策略

| Strategy | 行为 | 使用场景 |
|----------|------|---------|
| `ask` (**默认**) | 同名返回 HTTP 409，QClaw 询问用户 | 用户未表明偏好时 |
| `overwrite` | 直接覆盖 | 用户明确说"覆盖/替换" |
| `rename` | 自动重命名 `file(1).pdf` | 用户明确说"重命名" |

---

## Error Handling

所有命令输出 JSON。失败时 `message` 已包含用户友好的错误提示，直接输出即可。

| 错误 | 处理 |
|------|------|
| HTTP 409 冲突 | 输出 `message`，用户选择后用对应策略重新上传 |
| 上传失败 (非 409) | 直接输出 `message` |
| 401 / token 过期 | 提示用户联系管理员刷新 |
| 网络错误 | 重试 2 次 (间隔 3s)，仍失败则输出 `message` 并结束任务 |
| 配额满 | 提示清理过期文件 |

---

## 全局退出条件

- 连续失败 3 次 → 立即停止，提示：⚠️ 文件上传服务暂时不可用，请稍后重试
- 单次 Skill 调用最多执行 10 次命令
- 禁止流程级无限循环重试

---

## 规则

**输出规则：**
- `upload` / `batch-upload` 返回的 `message` 是服务端预渲染文本，校验 URL 域名后直接输出
- 不要从 `fileUrl`、`fileInfo` 等字段自行拼接回复
- 不要修改、截断、重组 `message` 中的 URL 或排版
- `success: false` 时不展示文件链接

**URL 安全：**
- 不要自行拼接/构造任何 URL（短链由服务端生成）
- 不要把 `rawDownloadUrl` 片段与 `jsonproxy.3g.qq.com` 拼接
- 不输出域名不在白名单 (`jsonproxy.3g.qq.com`、`smh.tencentcs.com`、`jprx.sparta.html5.qq.com`) 中的 URL

**用户交互：**
- 用户说"上传文件"但没指定路径 → 追问文件路径
- 默认用 `--conflict-strategy ask`，未经用户明确表态不要用 `overwrite` 或 `rename`
- 不要未经用户主动要求就上传其本地个人文件

**其他：**
- 不要硬编码或暴露 SMH 凭证
- 用户反馈链接过期时，用 `info` 获取新链接
- 依赖 `node` 和 `curl`（Windows 10+ 自带 curl），macOS/Linux 优先用 `jq`
