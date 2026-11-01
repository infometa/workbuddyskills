# WorkBuddy 运行兼容性（本 Skill 强制）

所有业务查询通过连接器安装的 `sl-sea` 二进制进入 AI Gateway。正文中的
`<sl-sea-absolute>` 是执行前替换的绝对路径占位符，不使用 PATH、`sl`、`sl.cmd`、
`sl.ps1`、Node 或 Python 转发。

## CLI 入口

```text
<sl-sea-absolute> marketing_crm <subcommand> ...
```

| 禁止 | 原因 |
|------|------|
| PATH / `which` / `where` | WorkBuddy 环境通常无 PATH |
| 读取认证文件或产品 Token | 凭据由 Gateway 管理 |
| 直连 MCP、数据库或产品接口 | 必须使用 Gateway 能力 |
| Python/Node 脚本转发 | 统一直接调绝对路径 CLI |

PowerShell 备用时 stdout 必须直出（`Write-Output`），禁止只捕获不打印。

## 执行边界

禁止：`--verbose`/`-v`、`--header`、`--envPath`、`--body-file`、旧的 token 查看命令、动态 DataCube、可变任务 ID、`title/where`、直连 MCP/数据库、产品认证参数。

## 隐私

不向对话输出 Token/密钥/完整认证参数；不展示可绕过权限的内部实现细节。默认不做触达/发券/导出明细/改活动等写操作。
