# macOS 安装步骤（Futu OpenD）

MacOS 版安装包是 **tar.gz 压缩包**，直接从软件下载服务器获取。

压缩包内部结构：
```
Futu_OpenD_x.x.xxxx_Mac/
├── Futu_OpenD-GUI_x.x.xxxx_Mac.dmg   ← GUI 版安装镜像（需挂载安装）
├── Futu_OpenD_x.x.xxxx_Mac.app       ← 命令行版（非 GUI，不要装这个）
├── Futu_OpenD_x.x.xxxx_Mac/
│   ├── FutuOpenD                       ← 命令行版主程序
│   ├── FutuOpenD.xml                   ← 配置文件
│   └── ...
├── fixrun.sh                           ← 路径修复脚本
└── README.txt
```

**重要**：`.app` 是命令行版，`.dmg` 才是 GUI 版。默认应安装 `.dmg`（GUI 版）。

安装包约 **374MB**，下载耗时较长。需要**分步执行**，每步用独立的 Bash 调用，避免超时。

## 第一步：获取最新版本文件名

通过 `fetch-lasted-link` API 的重定向获取最新版本文件名（**不要用 WebFetch 访问官方下载页**）：

```bash
curl -sI "https://www.futunn.com/download/fetch-lasted-link?name=opend-macos" | grep -i "^location:" | awk '{print $2}' | tr -d '\r'
```

从重定向 URL 中提取文件名（如 `Futu_OpenD_10.2.6208_Mac.tar.gz`）。

## 第二步：从 softwaredownload 域名直接下载

用提取到的文件名拼接 softwaredownload 域名 URL，用 Bash 工具执行下载，**必须设置 timeout 为 600000**（10 分钟）：

```bash
curl -L -o "$HOME/Desktop/FutuOpenD.tar.gz" "https://softwaredownload.futunn.com/Futu_OpenD_10.2.6208_Mac.tar.gz"
```

其中文件名替换为第一步获取的实际文件名。

路径替换规则：
- 默认：`$HOME/Desktop`
- 用户通过 `-path` 指定时替换为对应路径

下载完成后确认文件大小：
```bash
du -h "$HOME/Desktop/FutuOpenD.tar.gz"
```

## 第三步：解压

```bash
tar -xzf "$HOME/Desktop/FutuOpenD.tar.gz" -C "$HOME/Desktop/" && rm -f "$HOME/Desktop/FutuOpenD.tar.gz"
```

如果用户通过 `-path` 指定了路径，将 `$HOME/Desktop` 替换为对应路径。

## 第四步：挂载 .dmg 并安装 GUI 版 OpenD

解压后目录中有 `.dmg`（GUI 版）和 `.app`（命令行版），**需要安装 `.dmg`**。

找到 `.dmg` 文件并挂载：

```bash
DMG_PATH=$(find "$HOME/Desktop" -maxdepth 3 -name "*OpenD-GUI*.dmg" -type f | head -1) && echo "Found DMG: $DMG_PATH"
```

挂载 DMG 镜像：

```bash
hdiutil attach "$DMG_PATH" -nobrowse
```

挂载后会输出挂载点路径（如 `/Volumes/Futu OpenD-GUI`），从中找到 `.app` 并复制到 `/Applications`：

```bash
VOLUME_PATH=$(hdiutil attach "$DMG_PATH" -nobrowse | grep "/Volumes" | awk -F'\t' '{print $NF}') && echo "Mounted: $VOLUME_PATH"
APP_IN_DMG=$(find "$VOLUME_PATH" -maxdepth 1 -name "*.app" -type d | head -1) && echo "Found app: $APP_IN_DMG" && cp -R "$APP_IN_DMG" /Applications/ && echo "Installed to /Applications/"
```

处理 macOS Gatekeeper 限制（去除隔离属性），避免启动时被拦截：

```bash
APP_NAME=$(basename "$APP_IN_DMG") && xattr -rd com.apple.quarantine "/Applications/$APP_NAME"
```

卸载 DMG 镜像：

```bash
hdiutil detach "$VOLUME_PATH"
```

## 第五步：启动 GUI 版 OpenD

```bash
APP_NAME=$(ls /Applications/ | grep "OpenD-GUI" | head -1) && open "/Applications/$APP_NAME"
```

## 异常处理

- **Gatekeeper 仍拦截**：提示用户前往「系统偏好设置 → 安全性与隐私 → 通用」点击「仍要打开」
- **路径异常**：如果启动后提示配置文件路径异常，执行解压目录下的 `fixrun.sh`：
```bash
FIXRUN=$(find "$HOME/Desktop" -maxdepth 3 -name "fixrun.sh" | head -1) && chmod +x "$FIXRUN" && bash "$FIXRUN"
```

## 清理解压目录和 DMG（安装完成后可选）

```bash
EXTRACT_DIR=$(find "$HOME/Desktop" -maxdepth 1 -type d -name "*OpenD*" | head -1) && rm -rf "$EXTRACT_DIR" && echo "Cleaned up: $EXTRACT_DIR"
```
