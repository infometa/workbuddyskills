# tencent-news-cli 手动更新指南

## 直接更新

打开终端，执行以下命令：

```sh
tencent-news-cli update
```

如果你手里拿到的是 CLI 完整路径，也可以直接在该路径后追加 `update`。

## 更新命令不可用时

说明当前 CLI 版本过旧或未正确安装。此时改用安装脚本重新安装最新版本：

macOS / Linux：

```sh
curl -fsSL https://mat1.gtimg.com/qqcdn/qqnews/cli/hub/tencent-news/setup.sh | sh
```

Windows：

```powershell
irm https://mat1.gtimg.com/qqcdn/qqnews/cli/hub/tencent-news/setup.ps1 | iex
```

## 验证更新

更新完成后重新打开终端，运行以下命令查看版本信息：

```sh
tencent-news-cli version
```

## 故障排查

- **更新后仍显示旧版本** → 确认终端已重新打开，或运行 `source ~/.zshrc`（macOS/Linux）刷新环境
- **下载失败** → 检查网络连接，确认 CDN 地址 `mat1.gtimg.com` 可达
- **Windows 更新失败** → 检查是否被 SmartScreen、杀软或文件占用拦截
