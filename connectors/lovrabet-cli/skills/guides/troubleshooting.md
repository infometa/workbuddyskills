# Troubleshooting Guide

## Authentication required

说明当前没有可用的 `accessKey`。

优先检查：

1. `lovrabet auth status`
2. `~/.lovrabet.json` 或项目 `.lovrabet.json` 是否有顶层 `accessKey`
3. 是否设置了 `LOVRABET_ACCESS_KEY`

如果确认只是没登录：

- 先执行 `lovrabet auth login --non-interactive`，到命令根据当前 `userDomain` 返回的地址创建 AccessKey
- 想保留当前配置，使用 `lovrabet auth login --access-key <ACCESS_KEY>`
- 想切换节点或重建连接配置，执行 `lovrabet config init --region cn|id|global`，再按需执行 `lovrabet auth login --access-key <ACCESS_KEY>`

## 已登录，但业务命令仍失败

优先检查：

1. `lovrabet doctor` 显示的国家/地区和最终 Domain 是否正确
2. 当前 AK 对应的是否是预期用户：`lovrabet auth info`
3. `defaultApp` 是否能在 cache 中解析到 appcode
4. 是否需要先刷新 app cache

```bash
lovrabet app list --no-cache
```

如果你怀疑连接配置或认证信息不符合预期，比如：

- `defaultApp` 明显不对
- `auth info` 返回的用户不是你预期的账号
- `lovrabet doctor` 显示的 region 或 Domain 不符合预期

分别重设全局连接配置和 AccessKey：

```bash
lovrabet config init --region cn
lovrabet auth login --access-key <ACCESS_KEY>
```

如果业务节点在印尼，把第一条改成 `lovrabet config init --region id`。企业独立部署使用 `lovrabet config init --domain-config <file>`。

`config init` 只替换全局 region/Domain 路由字段，`auth login` 只替换目标作用域的 AccessKey；两者都保留其他配置。最后执行 `lovrabet doctor` 核对最终生效的国家/地区和 Domain。

## `defaultApp` 已有，但仍然找不到 appcode

说明当前 `defaultApp` 对应的远端 app 目录还没建立或已经失效。

先执行：

```bash
lovrabet app list --no-cache
```

如果仍不行，说明：

- 当前 `accessKey` 看不到这个 app
- 或 `defaultApp` 名称本身已过时

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
