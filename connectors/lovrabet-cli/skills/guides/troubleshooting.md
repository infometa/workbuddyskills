# Troubleshooting Guide

## Authentication required

说明当前没有可用的 `accessKey`，或服务端明确返回业务码 `201`。HTTP `401` 本身不能区分认证失败和权限不足。

优先检查：

1. `lovrabet auth status`
2. `~/.lovrabet.json` 或项目 `.lovrabet.json` 是否有顶层 `accessKey`
3. 是否设置了 `LOVRABET_ACCESS_KEY`

如果确认只是没登录：

- 先执行 `lovrabet auth login --non-interactive`，到命令根据当前 `userDomain` 返回的地址创建 AccessKey
- 想保留当前配置，使用 `lovrabet auth login --access-key <ACCESS_KEY>`
- 想切换节点或重建连接配置，执行 `lovrabet config init --region cn|id|global`，再按需执行 `lovrabet auth login --access-key <ACCESS_KEY>`

## Permission denied（业务码 202）

`permission_denied` 表示权限检查拒绝，本次 HTTP 状态也可能为 `401`。先用 `lovrabet auth info` 确认当前用户，再核对应用、目标数据集及实际动作的角色授权。Backend Function 能进入执行，不代表它访问的每个数据集都已授权，`byTable` 也相同。

保留当前用户和入口，报告拒绝；不要自动重新登录、切换 AK、添加系统执行参数或转用其他入口。只有业务码 `201` 或明确缺少凭证时，才按认证问题处理。

## 已登录，但业务命令仍失败

先只读核对，不通过切换身份或环境试探：

1. 用 `lovrabet doctor` 核对最终 Domain、默认 AppCode 及配置来源；项目默认选择优先于全局。
2. 用 `lovrabet auth info` 核对当前用户。
3. 对照[默认应用与应用发现](app-resolution.md)，核对本次目标及命令中的 `--app` / `--appcode`；上一条命令的临时目标不会自动沿用。
4. 区分认证失败、权限拒绝、连接错误与查询成功但没有匹配；只在最后一种情况且任务范围允许时扩大只读发现。

应用目标不对时，在本次命令中显式指定正确目标，不重设路由或 AccessKey。只有用户明确要求记住默认应用时才执行 `workspace init/use`。连接配置或用户身份确需调整时，按用户确认的目标分别配置；不要把应用选择问题当成登录问题。

`config init` 只替换全局 region/Domain 路由字段，`auth login` 只替换目标作用域的 AccessKey；两者都保留其他配置。企业独立部署使用 `lovrabet config init --domain-config <file>`；调整后用 `lovrabet doctor` 核对最终生效值。

## 默认应用无法解析

顶层 `appcode` 或本地 `apps` 名称中的 `appcode` 可直接提供目标，不依赖远端名称缓存。先检查配置结构和名称是否匹配。

`defaultApp` 使用远端名称、且本地没有对应名称映射时，才检查当前身份的应用目录：

```bash
lovrabet app list --no-cache
```

仍无法解析时，核对名称是否变化、应用是否已发布及当前用户是否有访问权限；保留真实错误，不换 AK 或环境绕过。

## `app list --local` 没数据

说明本地还没有建立 cache，或者 cache 已清空。

先执行：

```bash
lovrabet app list
```

或强制刷新：

```bash
lovrabet app list --no-cache
```

## 什么时候该看 doctor

遇到以下情况时，优先执行：

```bash
lovrabet doctor
```

典型场景：

- 配置来源不清楚
- `defaultApp` / `currentApp` 判断异常
- 国家/地区或 Domain 和实际请求不一致
- 认证信息看起来存在，但命令仍失败
