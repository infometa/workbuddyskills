# Swift LSP Plugin

为 Swift 项目提供 LSP 支持。

## 功能

- 通过 [SourceKit-LSP](https://github.com/swiftlang/sourcekit-lsp) 为 Swift 提供 LSP 支持
- 自动为 `Package.swift` 中的 `.executableTarget()` 和 `.testTarget()` 目标设置入口点

## 配置

创建 `.lsp.json` 文件并添加以下内容：

```json
{
  "command": "sourcekit-lsp",
  "settings": {},
  "configurations": [
    {
      "languages": ["swift"],
      "testLanguages": ["swift"],
      "sdk": "macosx"
    }
  ]
}
```

## 安装 SourceKit-LSP

### 使用 Swift 包管理器

```bash
# Swift 5.6 及更高版本
git clone https://github.com/swiftlang/sourcekit-lsp.git
cd sourcekit-lsp
swift build
```

### 使用 macOS

在 macOS 上，SourceKit-LSP 通常随 Xcode 或 Swift 工具链一起安装。

### 使用 Linux

```bash
# 安装 Swift 工具链
wget https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz
tar xzf swift-5.9.2-RELEASE-ubuntu22.04.tar.gz
```

## 开源许可

本项目采用 MIT 许可证开源。
