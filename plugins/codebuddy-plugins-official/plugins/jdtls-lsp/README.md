# jdtls-lsp

Java Language Server (Eclipse JDT.LS)，为 CodeBuddy 提供代码智能和重构功能。

## 支持的文件类型

`.java`

## 安装方式

### 通过 Homebrew (macOS)
```bash
brew install jdtls
```

### 通过包管理器 (Linux)
```bash
# Arch Linux (AUR)
yay -S jdtls

# 其他发行版：需要手动安装
```

### 手动安装
1. 从 [Eclipse JDT.LS 发布页](https://download.eclipse.org/jdtls/snapshots/) 下载
2. 解压到指定目录（如 `~/.local/share/jdtls`）
3. 在 PATH 中创建名为 `jdtls` 的包装脚本

## 系统要求

- Java 17 或更高版本（需要 JDK，不仅仅是 JRE）

## 更多信息

- [Eclipse JDT.LS GitHub](https://github.com/eclipse-jdtls/eclipse.jdt.ls)
- [VSCode Java 扩展](https://github.com/redhat-developer/vscode-java)（使用 JDT.LS）
