# ticket 普通附件

> **前置条件：** 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md)。

附件命令的 Agent 策略为 `CONFIRM_REQUIRED`。不公开 signed URL、外部存储凭证、
诊断上传或越权清理入口。

## ihr-cli ticket +upload

```bash
ihr-cli ticket +upload --file ./evidence.png
ihr-cli ticket +upload --file ./report.pdf --content-type application/pdf
```

| Flag | Type | 必填 | 默认值 | JSON 字段 | 格式与约束 |
| --- | --- | --- | --- | --- | --- |
| `--file` | string | REQUIRED | 无 | `file` | 本地文件路径；单文件最大 50MB |
| `--content-type` | string | OPTIONAL | 自动探测 | `contentType` | MIME 类型 |

multipart 字段固定为 `file`。响应只保留 fileId、文件名、大小和内容类型。

## ihr-cli ticket +download

```bash
ihr-cli ticket +download --file-id 9007199254740993 --target ./download/evidence.png
ihr-cli ticket +download --file-id 9007199254740993 --target ./download/evidence.png --overwrite
```

| Flag | Type | 必填 | 默认值 | JSON 字段 | 格式与约束 |
| --- | --- | --- | --- | --- | --- |
| `--file-id` | string | REQUIRED | 无 | `fileId` | 正整数 ID |
| `--target` | string | REQUIRED | 无 | `target`（本地控制） | 本地目标路径 |
| `--overwrite` | bool | OPTIONAL | `false` | `overwrite`（本地控制） | presence-style flag；完整下载后原子覆盖 |

默认拒绝覆盖。INTERNAL 附件对普通用户返回权限错误，不得猜测 fileId 或改用 raw
HTTP 绕过；下载始终通过 Gateway proxy。
