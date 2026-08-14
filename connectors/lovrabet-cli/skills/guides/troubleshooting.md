# Troubleshooting Guide

## Authentication required

说明当前没有可用的 `accessKey`。

优先检查：

1. `lovrabet auth status`
2. `~/.lovrabet.json` 或项目 `.lovrabet.json` 是否有顶层 `accessKey`
3. 是否设置了 `LOVRABET_ACCESS_KEY`

如果确认只是没登录：

- 先到 `https://user.lovrabet.com/user/ak` 创建 AccessKey
- 想保留当前配置，执行 `lovrabet auth login`
- 想清空当前作用域配置后重建认证，执行 `lovrabet auth init --access-key <ACCESS_KEY> [--env daily]`

## 已登录，但业务命令仍失败

优先检查：

1. 当前 `env` 是否正确
2. 当前 AK 对应的是否是预期用户：`lovrabet auth info`
3. `defaultApp` 是否能在 cache 中解析到 appcode
4. 是否需要先刷新 app cache

```bash
lovrabet app list --no-cache
```

如果你怀疑当前作用域配置已经混乱，比如：

- `defaultApp` 明显不对
- `env` 和预期不一致
- `auth info` 返回的用户不是你预期的账号
- 同一作用域里残留了不该继承的旧配置

可直接重建认证配置：

```bash
lovrabet auth init --access-key <ACCESS_KEY> --env daily
```

注意：这会清掉当前作用域里已有的其他配置字段，不只是 `accessKey`。

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
- 环境和实际请求不一致
- 认证信息看起来存在，但命令仍失败
