# WorkBuddy 同程旅行连接配置

WorkBuddy 渠道不使用手工 API Key。用户通过 WorkBuddy「连应用」完成同程登录授权，令牌由 `tc-chengxin` CLI 在本机维护。

## 授权流程

1. 在 WorkBuddy「连应用」中找到「同程旅行」。
2. 点击「连接」，按浏览器页面完成同程登录授权。
3. 授权成功后，Skill 执行脚本前通过 `tc-chengxin token` 获取有效令牌。

## 查询前环境

每次调用查询脚本前，WorkBuddy Agent 必须设置：

macOS/Linux shell：

```bash
export CHENGXIN_WORKBUDDY_OUTPUT_DIR="$PWD/outputs"
export CHENGXIN_API_KEY="$(tc-chengxin token)"
export CHENGXIN_OUTPUT_GUARD=display_contract
```

Windows PowerShell：

```powershell
$env:CHENGXIN_WORKBUDDY_OUTPUT_DIR = Join-Path (Get-Location).Path "outputs"
$env:CHENGXIN_API_KEY = (tc-chengxin token)
$env:CHENGXIN_OUTPUT_GUARD = "display_contract"
```

`CHENGXIN_OUTPUT_GUARD=display_contract` 会让脚本输出 WorkBuddy v2 展示协议，并生成本地 HTML 文件供 `present_files` 打开。

`CHENGXIN_WORKBUDDY_OUTPUT_DIR` 会让 HTML 直接输出到当前工作区，便于 WorkBuddy 展示和用户查找。Windows 下必须使用 `D:\...\outputs` 这类原生盘符路径，不要使用 `/d/...`、`\d\...` 或字面量 `$PWD/outputs`。

## 网关地址

CLI 默认使用生产网关：

```text
https://wx.17u.cn/skills/gateway
```

本地调试可通过安装脚本写入临时网关地址：

```bash
bash scripts-workbuddy/install-local.sh --gateway http://127.0.0.1:8971/skills/gateway
```

该地址会写入 `~/.tc-chengxin/cli-config.json`，由 CLI 转发请求时读取。

发布前应删除本地调试配置，避免继续指向 `127.0.0.1` 或测试环境。

## 常见问题

- `tc-chengxin token` 无输出：提示用户重新连接「同程旅行」。
- HTML 没有打开：检查脚本 JSON 中是否有 `htmlFilePath`，并确认 Agent 是否调用了 `present_files`。
- 二维码缺失：保留 PC 预订和手机打开链接，不编造二维码。
