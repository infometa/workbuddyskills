# auth — 认证管理

当前推荐的认证路径是 **User Access Key（client-ak）**。

## auth login — 保存 accessKey

```bash
lovrabet auth login
lovrabet auth login --non-interactive
lovrabet auth login --access-key <ACCESS_KEY>
lovrabet auth login --global
```

**行为**：
- 默认写入全局配置 `~/.lovrabet.json`
- 兼容场景可用 `--project` 写入当前目录本地配置；常规使用不需要
- 交互模式下，不传 `--access-key` 会提示输入 AK，并提示先到 `https://user.lovrabet.com/user/ak` 自助创建
- `--non-interactive` 表示无打扰模式：不进入 stdin prompt；如果缺少 AccessKey，会立即提示创建链接和 `--access-key` 命令
- `auth login` 不支持 `--yes`；`--yes` 只用于高风险写操作的确认跳过
- 也可以直接显式传入：`lovrabet auth login --access-key <ACCESS_KEY>`
- Agent 可以使用用户提供的 AccessKey 完成认证，但不要在答复、日志或文档示例中回显真实值
- 在 Agent、CI、后台任务或非 TTY 环境中，不要运行裸 `auth login`；使用 `lovrabet auth login --non-interactive` 获取提示，等用户提供 AccessKey 后再执行带 `--access-key` 的命令

**适用场景**：
- 想替换当前 AK，但尽量保留已有 `defaultApp`、`format`、`pageSize`、域名覆盖等配置
- 不希望破坏当前作用域里的其他用户意图配置

**推荐顺序**：

1. Agent 先执行 `lovrabet auth login --non-interactive`，把提示里的 `https://user.lovrabet.com/user/ak` 发给用户
2. 用户创建或复制 AccessKey，并提供给 Agent
3. Agent 执行 `lovrabet auth login --access-key <ACCESS_KEY>`
4. 再执行 `lovrabet auth info`，确认当前 AK 对应的是预期用户

## auth init — 清空并重建当前作用域认证配置

```bash
lovrabet auth init --access-key <ACCESS_KEY>
lovrabet auth init --access-key <ACCESS_KEY> --env daily
```

**行为**：
- 会清空当前作用域下已有的整份 `.lovrabet.json` 配置内容，再仅写回新的认证初始化结果
- 默认写入全局配置 `~/.lovrabet.json`
- 兼容场景可用 `--project` 写入当前目录本地配置；常规使用不需要
- 支持 `--env`，会和新的 `accessKey` 一起写入

**风险提醒**：
- 这是破坏性操作
- 当前作用域下已有的 `defaultApp`、`format`、`pageSize`、域名覆盖等字段都会被清掉
- 如果只是想换 AK，不要用 `auth init`，优先用 `auth login`

## 什么时候用 login，什么时候用 init

- **保留现有配置，只更新认证**：`lovrabet auth login`
- **当前作用域配置已经混乱，想彻底重来**：`lovrabet auth init`
- **需要同时清空旧配置并重建 env**：`lovrabet auth init --access-key <ACCESS_KEY> --env daily`

## auth logout — 清除本地 accessKey

```bash
lovrabet auth logout
```

## auth status — 查看当前认证状态

```bash
lovrabet auth status
```

会显示：
- 当前是否已配置 accessKey
- accessKey 来源（global / project / env）
- 当前 env

## auth info — 查看当前 AK 对应的登录用户

```bash
lovrabet auth info
lovrabet auth info --env daily
```

会调用：

```text
GET /client/user/loginUserInfo
X-User-AK: <redacted>
```

会返回：

- 当前 AccessKey 对应的登录用户信息
- 常见字段如 `id`、`userName`、`loginName`
- `meta.env`，方便确认当前请求落在哪个环境

**适用场景**：

- 你刚切换了 AK，想确认当前命令实际在用谁的身份
- 同一台机器上多人轮流调试，怀疑当前 AK 不是自己的
- 业务命令能执行，但结果明显不像预期，需要先确认身份再继续排查
- 后续任何命令需要“当前登录用户身份信息”作为判断条件时，先执行这一条

**Agent 规则**：

- 不要凭 `defaultApp`、缓存内容或最近一次登录记录去猜当前登录用户
- 遇到“当前用户是谁 / 当前 AK 属于谁 / 当前人是否有权限看到这些应用或数据”这类问题，统一先调 `lovrabet auth info`
- 先拿到身份，再继续做 app 决议、权限判断、结果解释或排障

## 认证优先级

```
CLI flag (--access-key)
  ↓
环境变量 LOVRABET_ACCESS_KEY
  ↓
当前目录 .lovrabet.json（兼容本地配置）
  ↓
全局级 ~/.lovrabet.json
```

## 与 app cache 的关系

一旦配置了 AK：
- `lovrabet app list` 可以直接查询当前 AK 在平台上的应用目录
- 结果会缓存在 `~/.lovrabet/cache/<env>/<ak-fingerprint>/my-apps.json`

`auth login` / `auth init` 本身都不会主动把应用目录写进 `.lovrabet.json`。

## Cookie

Cookie 仍保留历史兼容读取，但不再是推荐主路径。新的 Agent 指导和用户文档应默认使用 AK 流程。

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-config.md](lovrabet-config.md)
