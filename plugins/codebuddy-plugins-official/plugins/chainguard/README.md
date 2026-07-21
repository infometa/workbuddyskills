# ChainGuard 供应链安全插件

自动拦截 AI 依赖安装操作，进行供应链安全审计。

## 功能

- 自动监控包安装命令（npm、pip、yarn、cargo、go、maven 等）
- 监控依赖清单文件变更（package.json、requirements.txt、go.mod、Cargo.toml 等）
- 检测已知漏洞组件（CVE/OSV 漏洞库）
- SBOM 白名单核查
- License 合规检测
- 拦截高危操作，保障供应链安全

## 使用

安装插件后自动生效，无需额外配置。Hook 会在 AI 执行以下操作时触发：

- `Bash` — 执行 shell 命令（包安装等）
- `Write` / `Edit` / `MultiEdit` — 修改依赖清单文件