# auth — 认证管理

Lovrabet CLI 只使用 User Access Key（client-ak）认证。AK 属于当前用户；同一环境下选择不同应用仍使用同一身份，访问范围由平台权限决定。

## auth login — 保存 accessKey

```bash
lovrabet auth login
lovrabet auth login --non-interactive
lovrabet auth login --access-key <ACCESS_KEY>
lovrabet auth login --global
```

**行为**：
- 默认写入全局配置 `~/.lovrabet.json`
- 只保存所选作用域的顶层用户 accessKey；项目配置或显式环境变量可能覆盖全局存储值
- 兼容场景可用 `--project` 写入当前目录本地配置；常规使用不需要
- 交互模式下，不传 `--access-key` 会提示输入 AK，并给出当前 `userDomain` 下的 `/user/ak` 自助创建地址
- `--non-interactive` 表示无打扰模式：不进入 stdin prompt；如果缺少 AccessKey，会立即提示创建链接和 `--access-key` 命令
- `auth login` 不支持 `--yes`；`--yes` 只用于高风险写操作的确认跳过
- 也可以直接显式传入：`lovrabet auth login --access-key <ACCESS_KEY>`
- Agent 可以使用用户提供的 AccessKey 完成认证，但不要在答复、日志或文档示例中回显真实值
- 在 Agent、CI、后台任务或非 TTY 环境中，不要运行裸 `auth login`；使用 `lovrabet auth login --non-interactive` 获取提示，等用户提供 AccessKey 后再执行带 `--access-key` 的命令

**适用场景**：
- 想替换当前 AK，但尽量保留已有 `defaultApp`、`format`、`pageSize`、域名覆盖等配置
- 不希望破坏当前作用域里的其他用户意图配置

**推荐顺序**：

1. Agent 先执行 `lovrabet auth login --non-interactive`，把命令根据当前 `userDomain` 返回的创建地址发给用户
2. 用户创建或复制 AccessKey，并提供给 Agent
3. Agent 执行 `lovrabet auth login --access-key <ACCESS_KEY>`
4. 再执行 `lovrabet auth info`，确认当前 AK 对应的是预期用户

## 配置节点与认证的边界

- 首次使用先执行 `lovrabet config init` 配置官方节点或独立部署 Domain
- `auth login` 只保存 AccessKey，不接受 region 或 Domain 参数，也不会清除其他配置
- 后续切换节点继续使用 `config init --region <region>`；精确调整使用 `config set/delete`

## auth logout — 清除本地 accessKey

```bash
lovrabet auth logout
```

只清除所选作用域的顶层 accessKey；另一作用域或显式环境变量中的凭证不受影响，可能继续用于请求。

## auth status — 查看当前认证状态

```bash
lovrabet auth status
```

会显示：
- 当前是否已配置 accessKey
- 实际请求凭证的来源（环境变量或合并后的顶层 accessKey）
- 非默认环境提示；默认不显示 `Environment` 行，实际服务地址通过 `lovrabet doctor` 核对
- 所选 global / project 作用域存储的顶层 AK，与实际请求凭证分别标注并脱敏

应用选择不改变用户凭证。已有有效 AK 时，`--check` 只检查是否已配置，不校验远端权限；远端身份使用 `auth info` 查询。没有有效 AK 但存在未过期的设备授权码时，`--check` 会查询授权结果，成功后将 AK 保存到该授权指定作用域的顶层配置；仅需查看本地状态时不加 `--check`。

## auth info — 查看当前 AK 对应的登录用户

```bash
lovrabet auth info
```

会调用：

```text
GET /client/user/loginUserInfo
X-User-AK: <redacted>
```

会返回：

- 当前 AccessKey 对应的登录用户信息
- 常见字段如 `id`、`userName`、`loginName`
- `meta.env`：实际环境标识，用于排障；该标识不能替代最终服务地址，地址通过 `lovrabet doctor` 核对

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
项目顶层 accessKey
  ↓
环境变量 LOVRABET_ACCESS_KEY
  ↓
全局顶层 accessKey
```

项目已配置 AK 时，环境变量不会覆盖它。CI 需要注入 AK 时，执行目录应省略项目 AK。`auth status` 和 `doctor` 可查看实际来源。

`auth login --access-key` 是保存参数，不是通用请求参数。默认应用与配置规则见 [配置参考](lovrabet-config.md)。已选中的 AK 认证失败时不自动重试其他 AK。

## 与 app cache 的关系

一旦配置了 AK：
- `lovrabet app list` 可以直接查询当前 AK 在平台上的应用目录
- 结果会缓存在 `~/.lovrabet/cache/<env>/<ak-fingerprint>/my-apps.json`

`auth login` 本身不会主动把应用目录写进 `.lovrabet.json`。

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-config.md](lovrabet-config.md)
