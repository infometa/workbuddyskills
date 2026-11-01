# login

登录 ReelMate 并把凭据保存到凭据链。默认打开浏览器完成 handoff；无图形环境可从文件或 stdin 导入授权结果。

## 用法

```text
reelmate login [--credential-store STORE_TYPE]
reelmate login --token-file TOKEN_FILE
reelmate login --token-file -
reelmate login --code -
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate login` | 登录并保存凭据；选项决定凭据存储和无浏览器登录方式 |

## `reelmate login`

### 作用

完成登录并保存凭据。

### 参数

- `--credential-store STORE_TYPE`：`file`、`auto` 或 `keychain`；默认 `file`。
- `--token-file TOKEN_FILE`：从文件读取已有凭据；传 `-` 从 stdin 读取。
- `--code -`：从 stdin 读取授权码，当前不替代普通浏览器登录。

| 值 | 含义 |
|---|---|
| `file` | 使用 ReelMate 配置目录中的加密凭据文件；当前默认值 |
| `auto` | 优先使用系统凭据库；系统凭据库不可用时降级到加密文件，并在 stderr 提示 |
| `keychain` | 强制使用系统凭据库；系统凭据库不可用时直接报错，不会降级 |

### 输出

输出账号摘要，不输出令牌。

### 示例

```bash
# 使用默认的加密文件存储
reelmate login

# 明确使用系统凭据库
reelmate login --credential-store keychain

# 自动选择系统凭据库或加密文件
reelmate login --credential-store auto

reelmate login --token-file TOKEN_FILE
```
## 无浏览器环境登录

- `TOKEN_FILE` 是本地文件路径。文件内容必须是已有登录流程提供的 `user_data` 凭据载荷；它通常由管理员或 CI 凭据系统提供，或由另一台可打开浏览器的机器完成登录后取得。CLI 只负责读取并保存这份凭据，不负责生成或申请它。
- `reelmate login --token-file TOKEN_FILE` 从指定文件读取凭据。
- `reelmate login --token-file -` 从 stdin 读取凭据，适合不落盘传递；不要把密文写入 shell 历史。
- `reelmate login --code -` 从 stdin 读取授权码；当前版本尚未支持授权码兑换，不能替代普通的 `reelmate login`。
- `--token-file` 和 `--code` 不接受命令行内联密文。
- 普通用户不需要准备 `TOKEN_FILE`，直接运行 `reelmate login` 完成浏览器登录即可。

## 注意事项

- 可识别 Agent 宿主时，浏览器授权链接会附带 `ai_platform`；无法识别则不附带。
- 登录后执行其他命令时，使用同一个 `--credential-store` 取值。例如用 `keychain` 登录后，查询账号也要使用 `--credential-store keychain`；用默认方式登录则可以继续省略该参数。文件存储需要口令时，可设置 `REELMATE_CREDENTIAL_PASSPHRASE`。
- `file` 使用加密文件，`auto` 优先系统凭据库，`keychain` 不可用时直接报错。
- `TOKEN_FILE` 内容应像密码一样处理；`--token-file` 和 `--code` 不接受命令行内联密文。
- CI 不要把令牌写入构建参数或日志。
