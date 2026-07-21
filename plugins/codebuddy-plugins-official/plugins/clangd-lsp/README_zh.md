# clangd-lsp

C/C++ Language Server (clangd)，为 CodeBuddy 提供代码智能、诊断和格式化功能。

## 支持的文件类型

`.c`, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hxx`, `.C`, `.H`

## 安装方式

### 通过 Homebrew (macOS)
```bash
brew install llvm
# 添加到 PATH: export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
```

### 通过包管理器
```bash
# Ubuntu/Debian
sudo apt install clangd

# Fedora
sudo dnf install clang-tools-extra

# Arch Linux
sudo pacman -S clang
```

### Windows
从 [LLVM 发布页](https://github.com/llvm/llvm-project/releases) 下载，或使用：
```bash
winget install LLVM.LLVM
```

## 更多信息

- [clangd 官网](https://clangd.llvm.org/)
- [入门指南](https://clangd.llvm.org/installation)
