# tmeet auth — 认证

管理腾讯会议 CLI 的登录状态。

---

## login — 登录

```bash
# 必须后台运行，以便立即捕获输出中的授权 URL
tmeet auth login 2>&1 &

# 禁用自动打开浏览器，仅输出授权 URL
tmeet auth login --no-browser 2>&1 &
```

执行后输出授权 URL，在浏览器中打开并完成腾讯会议 OAuth 授权，CLI 自动轮询获取授权结果并将凭证保存到本地。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| `--no-browser` | bool | — | `false` | 禁用自动打开浏览器。`false`（默认）会尝试自动打开系统默认浏览器跳转到授权 URL；`true` 则仅输出授权 URL，需用户手动在浏览器中打开 |

**注意：**
- `auth login` 是**阻塞命令**，**必须以后台方式运行**（命令末尾加 `2>&1 &`），否则命令会一直阻塞等待，模型无法捕获输出中的授权 URL
- 执行后必须从输出中提取授权 URL，**完整展示给用户**，并明确提示用户在浏览器中打开完成授权，不得省略
- 如果已经登录，命令返回错误 `user has been initialized`，无需重复登录
- 如需重新登录，先执行 `tmeet auth logout` 清除凭证后再登录

**典型输出：**
```
Please open the following URL in your browser to authorize
authorize url: https://...
Login successful. Start managing your meetings using tmeet.
```

---

## logout — 登出

```bash
tmeet auth logout
```

清除本地保存的所有认证凭证。登出后所有需要认证的命令都将失败，需重新执行 `auth login`。

**无任何可选参数。**

---

## status — 查看登录状态

```bash
tmeet auth status
```

显示当前登录状态及凭证信息，**无需登录即可执行**。

**无任何可选参数。**

**典型输出（已登录，Token 有效）：**
```
Logged in
  OpenId:  xxx
  UserName:  xxx
  AccessToken:  valid (expires at 2026-05-01 10:00:00, remaining 25d 0h 6m)
  RefreshToken: valid (expires at 2026-07-01 10:00:00, remaining 86d 0h 6m)
```

**典型输出（已登录，Token 已过期）：**
```
Logged in
  OpenId:  xxx
  AccessToken:  expired (at 2026-03-01 10:00:00)
  RefreshToken: valid (expires at 2026-07-01 10:00:00, remaining 86d 0h 6m)
```

**典型输出（未登录）：**
```
Not logged in. Please use 'tmeet auth login' to authenticate.
```

---

## 常见错误

| 错误现象 | 原因 | 解决方案 |
|---------|------|---------|
| `user has been initialized` | 已登录，重复执行 login | 直接使用，或先 logout 再 login |
| `user config is empty` | 未登录就执行其他命令 | 先执行 `tmeet auth login` |

## 参考

- [tmeet](../SKILL.md) — 全部命令概览
