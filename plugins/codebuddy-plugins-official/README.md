# CodeBuddy 官方插件市场

CodeBuddy 官方插件市场，提供高质量的 CodeBuddy 插件。

## 安全提示

> **重要警告**: CodeBuddy 无法控制插件中包含的 MCP 服务器、文件或其他软件，也无法验证它们是否按预期工作或不会发生变化。请在安装前确认您信任该插件。

## 安装

添加此插件市场：

```bash
/plugin marketplace add <repo-url>
```

安装市场中的插件：

```bash
/plugin install <plugin-name>
```

## 插件开发

如需开发插件，请参考 [CodeBuddy 插件开发文档](https://copilot.tencent.com/docs/cli/plugins)。

## 贡献

欢迎提交 PR 贡献新的插件。请确保您的插件：

1. 包含完整的 `.codebuddy-plugin/plugin.json` 配置
2. 提供清晰的 README 文档
3. 通过基本的安全审查
