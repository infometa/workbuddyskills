# HSK DevOps Expert

> WorkBuddy 专家 — 贝锐花生壳，基于 HSK CLI 提供 NAT 穿透、文件托管、项目部署能力。

## 简介

本专家包为 WorkBuddy 生态提供 HSK CLI 的 AI 专家角色，用户安装后可通过自然语言完成：
- 内网穿透：将本地服务（HTTP/WebSocket/API/SSR）一键暴露到公网
- 文件托管：上传单文件或目录，获取公网下载/访问链接
- 构建部署：一键 build → upload，部署前端项目到公网
- 资源管理：检测状态、复用资源、更新已发布内容

支持 Windows / macOS / Linux 多平台，零配置开箱即用。

## 目录结构

```
hsk-devops-expert/
├── .codebuddy-plugin/
│   └── plugin.json              # 专家配置
├── avatars/
│   └── expert.png               # 专家头像（512×512）
├── agents/
│   └── hsk-devops-architect.md  # 专家能力与行为定义
├── skills/
│   └── hsk-cli/
│       └── SKILL.md             # 内置技能
└── README.md
```

## 依赖

- HSK CLI（`@aweray/hsk-cli`）：优先自动安装，未安装时可手动执行 `npm install -g @aweray/hsk-cli`
- Node.js >= 14

## 使用

安装后在 WorkBuddy 中直接对话：

- "把本地 9000 端口的服务暴露到公网"
- "上传 dist 目录并生成公网访问链接"
- "构建并部署我的前端项目"

## 平台支持

| Platform | Architectures |
|----------|---------------|
| macOS    | Intel (amd64), Apple Silicon (arm64) |
| Linux    | amd64 |
| Windows  | amd64 |

## License

MIT
