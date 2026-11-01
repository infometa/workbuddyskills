# logout

退出当前 ReelMate 账号，并删除保存在本机的登录凭据。

## 用法

```text
reelmate logout [--account PROFILE] [--credential-store STORE_TYPE]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate logout` | 注销指定账号并删除本地凭据 |

## `reelmate logout`

### 作用

删除本地账号凭据并退出当前账号。

### 参数

- `--account PROFILE`：要注销的已登录账号，通常是登录结果中的 uid；省略时注销当前账号。
- `--credential-store STORE_TYPE`：`file`、`auto` 或 `keychain`，应与登录时一致。

### 输出

返回注销摘要，不输出令牌。

### 示例

```bash
reelmate logout
reelmate logout --account PROFILE --credential-store keychain
```

## 注意事项

- 注销只删除登录凭据，不删除设备 ID。
- 如果凭据由 `REELMATE_ACCESS_TOKEN` 托管，CLI 无法删除它，请直接清除环境变量。
- 网络注销失败时 CLI 仍会删除本地凭据；服务端会话可能仍有效。
