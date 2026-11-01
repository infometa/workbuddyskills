# 鉴权与站点

先 `adp auth status --format json` 查看 `profile/site/endpoint/source`。
`adp auth list --format json` 查看已存 profile。不要读取凭据文件内容到上下文。

- 公有云 `cloud` 的 CAM SecretId 以 AKID 开头，入口 https://console.cloud.tencent.com/cam/capi。
- 独立站 `independent` 的 API 密钥在 https://adp.tencent.com/adp#/key-manage （企业管理 → 密钥管理 → 新建API密钥）获取，使用 OneID，不要求 AKID 前缀；登录时显式 `--site independent`。不要把独立站用户指到 CAM 控制台。
- 自定义站点使用 `--site custom --endpoint <host>`，先确认用户提供的目标地址。
- `--profile` 优先于 `ADP_PROFILE` 和 active profile，但环境凭据仍优先于 profile 中的凭据。
  根据 `source` 验证实际身份，不凭参数猜测。profile 存于 `~/.adp/profiles/`，权限 0600。

已有 profile 时无需重新登录。

## 在对话里完成首次登录（默认：Agent 交互填充）

`adp auth status --format json` 返回退出码 `4`（无本机凭据）时，除非用户主动要求网页登录，默认直接与用户交互收集站点与 AK/SK 并写入 profile：

1. 向用户确认站点（默认公有云 `cloud`；独立站为 `independent`；私有化/自定义传 `--site custom --endpoint <host>`）以及 `SecretId`、`SecretKey`（临时密钥可附加 `--token`）。**提问时必须在回复中同时给出两个站点的密钥获取 URL 与入口说明**：
   - **公有云（`cloud`）**：在腾讯云 CAM 控制台 [API 密钥管理](https://console.cloud.tencent.com/cam/capi)（`https://console.cloud.tencent.com/cam/capi`）新建或获取 `SecretId`（`AKID` 开头）与 `SecretKey`（使用说明见 `https://cloud.tencent.com/document/product/598/40488`）。
   - **独立站（`independent`）**：在 ADP 独立站 [密钥管理](https://adp.tencent.com/adp#/key-manage)（`https://adp.tencent.com/adp#/key-manage`，路径：企业管理 → 密钥管理 → 新建 API 密钥）创建并获取 `SecretId` 与 `SecretKey`。
2. 收到用户提供的信息后，执行非交互登录写入本地 `~/.adp/profiles/`：

```bash
adp auth login --site <cloud|independent> --secret-id "<SecretId>" --secret-key "<SecretKey>" --format json
adp auth status --format json
```

- 不要在回复、总结或报告中回显用户的明文 `SecretKey`，也不要将密钥写入仓库文件。

## 从网页发起登录（仅当用户明确要求网页登录时）

当用户明确要求通过网页/本地浏览器填写密钥，或拒绝在对话中粘贴密钥时，使用本地网页登录：

```bash
adp auth login --web --detach --format json   # 返回 result.url / expiresAt / pid
adp auth status --format json                 # 轮询，直到 ok:true
```

- 页面只监听 `127.0.0.1`，链接带一次性 token，默认 5 分钟过期（`--timeout <秒>` 调整，最长 1800）。
- 页面先用一次只读调用校验密钥，校验失败会在页面上提示并允许重填，不会保存无效密钥。
- `--site independent` / `--profile <name>` 可与 `--web` 同用；`--open` 会尝试直接打开浏览器。

## 在终端或 CI 通过环境变量登录

用户已在本地终端环境设置了 `TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY` 时，可直接持久化当前环境凭据：

```bash
adp auth login --site cloud --format json
adp auth status --format json
```

不要把密钥写进报告或仓库。非 TTY 且未传参数/环境变量时命令会直接退出，不会挂起等待终端输入。

## 只有一套凭据

所有命令（含 `adp workflow`、`adp kb doc`）都共用同一套 CAM SecretId/SecretKey（或独立站 API 密钥）。
`adp workflow` 和 `adp kb doc import` 会调用 LKE 2023-11-30 接口，只支持公有云站点；
鉴权失败时先看 `auth status` 的 `source`，再让用户确认 CAM 策略含 ADP 与 LKE 权限。
不要反复登录，不要换应用绕过权限。
`adp env list --format json` 只列环境变量名称和敏感标记，不返回值。
