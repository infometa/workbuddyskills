# 文件上传工作流

`file` 命令用于上传本地文件，并为已上传文件查询访问 URL。适用场景包括上传发票、证照、合同、图片、PDF、业务附件，或为后续 OCR、BFF、人工核对提供文件访问地址。默认查询短效 URL；只有富文本、Markdown、HTML、邮件正文或三方系统只接受 URL 且需要长期展示时，才显式查询 3 年长期 URL。

`file upload` 的风险等级为 `read`：上传只生成尚未绑定业务记录的 `filePath`，不创建、更新或删除业务数据。它仍会把本地文件发送到远端并创建文件对象，必须使用明确的目标应用和具备权限的身份。

## 命令概览

| 目标 | 命令 | 风险 |
|------|------|------|
| 上传本地文件 | `lovrabet file upload --file <local-path>` | read |
| 查询临时预览 URL | `lovrabet file query-url --filepath <filePath>` | read |
| 查询临时下载 URL | `lovrabet file query-url --filepath <filePath> --download` | read |
| 查询 3 年长期嵌入 URL | `lovrabet file query-url --filepath <filePath> --long-term` | read |

需要机器可读输出时统一加 `--format compress`；需要截取字段时再叠加 `--jq`。

`file upload` 支持 dry-run 预览。正式上传前先用 `--dry-run` 确认目标应用和本地文件；dry-run 只展示 `/client/uploadFile` multipart 请求，不上传文件。

## 上传文件

```bash
lovrabet file upload --file ./invoice.png --dry-run --format compress
lovrabet file upload --file ./invoice.png --format compress
```

上传成功后，重点读取返回的 `filePath`。这是后续 `file query-url` 的入参。上传组件字段、附件字段和表单文件字段应长期保存 `filePath`，由页面渲染时再按需换取 URL。

`file upload` 不接受 `--download`。需要 URL 时继续执行 `file query-url`；需要下载语义时只在 `file query-url` 上追加 `--download`。

## 查询 URL

```bash
lovrabet file query-url --filepath <filePath> --format compress
lovrabet file query-url --filepath <filePath> --download --format compress
lovrabet file query-url --filepath <filePath> --long-term --format compress
```

短效 URL 可能带签名和有效期，默认用于 OCR、临时预览、一次性下载和短时间消费。默认不要在最终答复中回显完整 URL；如果用户明确要打开或下载，才提供必要链接。

`--long-term` 或 `--long-term=true` 只用于必须把静态 URL 写入长期业务内容的场景，例如需求详情富文本、Markdown、HTML、邮件正文或三方系统只接受图片 URL；当前有效期为 3 年。CLI 不会根据 prompt、字段名或文件名自动启用长期 URL。

## 安全处理

1. 不回显 AccessKey、签名 URL 或本地个人路径。
2. 发票、证照、合同等敏感材料不要写入日志、配置文件或 Skill 文档示例。
3. 只把 `filePath` 用作 CLI 的文件查询入参和业务文件引用。
4. URL 过期或不可访问时，重新执行 `file query-url` 获取新的临时 URL。
5. 普通附件、表单文件字段和上传组件字段保存 `filePath`，不要保存长期 URL。
6. 长期 URL 不是公开 CDN 分发能力；公开站点、大流量外链或客户自担流量场景应走业务方 CDN 或平台受控分享能力。

## 常见错误

| 现象 | 处理 |
|------|------|
| 本地文件不存在 | 检查 `--file` 路径，使用真实本地文件 |
| 文件超过 50 MB | 拆分或压缩文件；当前运行态上传接口上限为 50 MB |
| 服务端返回“权限不足” | 先用 `--dry-run` 核对目标 `appCode`；确认无误后，由目标应用管理员为当前用户角色配置 `/client/uploadFile` API 权限 |
| `filePath is required` | 先执行 `file upload`，从返回中取 `filePath` |
| URL 过期或不可访问 | 重新执行 `file query-url` 获取新的临时 URL |
| 需要下载而不是预览 | 在 `file query-url` 上追加 `--download` |
| 需要长期展示静态图片 URL | 仅在 URL-only 内容嵌入场景追加 `--long-term`，当前有效期 3 年 |
