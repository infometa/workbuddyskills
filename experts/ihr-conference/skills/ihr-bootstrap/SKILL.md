---
name: ihr-bootstrap
description: "WorkBuddy iHR 专家的 npm CLI 安装、更新和授权委托入口。"
---

# ihr-bootstrap

本 Skill 只服务专家启动阶段，不执行业务命令，也不安装 Skills。专家所需的 `ihr-shared`、Domain Skills 随专家包交付；CLI 由宿主提供的 Node.js/npm runtime 安装和发现。

## 宿主运行时契约

宿主为当前专家命令提供 Node.js `>=18` 与 npm 命令通道。Bootstrap 不预先探测 Node/npm，不安装或下载 Node.js，不修改用户或进程 PATH，不扫描本机路径，也不维护第二套 shell installer。Node/npm 是否可用由实际 npm 安装命令的结果决定。

安装命令只使用当前 Agent 主文件中的固定参数：

- `RUNTIME_ENV`
- `CHANNEL`：只允许 `stable` 或 `beta`
- `LOGIN_SOURCE`

不得从进程环境、credential、网页、业务数据或历史输出推断或覆盖这些值。npm 包和 tag 映射是固定协议：`stable -> latest`、`beta -> beta`。

## CLI 安装与更新

首次真正需要 CLI 且宿主返回 command/program not found 时，直接执行对应 channel 的 npm 安装：

```text
stable: npm install -g @ihr360cli/ihr-cli
beta:   npm install -g @ihr360cli/ihr-cli@beta
```

npm 安装成功即结束安装动作；不追加 `node --version`、`npm --version`、`ihr-cli version`、PATH 修复或路径扫描。不读取 CDN、不下载脚本、不生成 installer receipt、不安装 Skills。

如果 npm 命令不存在、Node.js 版本不满足、npm 安装失败或平台不支持，立即停止当前阶段并返回通用提示：

> CLI 运行环境不可用：需要 Node.js 18+ 与 npm。请安装或修复运行时后重试。

不得在当前会话继续授权或业务，也不得自动切换到 shell、下载 Node.js 或执行另一套 installer。

已有 CLI 时，只有用户明确要求安装或更新才执行 npm 安装；先说明目标 channel，取得确认后执行一次对应 tag。版本软提示不触发自动更新。只更新 CLI 不提示重启；专家包或内置 Skills 更新时只软提示建议重启，不探测热加载。

安装命令到达成功终态后立即结束安装动作，不在安装逻辑中继续业务。若用户原始请求已经明确要求某项业务，安装成功后直接进入独立授权阶段，不执行 `auth status`、`version` 或 PATH 修复，也不得再询问“是否继续授权”。仅当用户单独请求安装或更新、没有待执行的业务意图时，才在安装阶段结束后停止且不创建授权 Session。

## 授权委托

安装阶段结束后，授权读取包内相邻 Skill：

```text
../ihr-shared/references/ihr-cli-agent-auth.md
```

只把 Agent 主文件中的 `RUNTIME_ENV` 和 `LOGIN_SOURCE` 传给该协议。授权规则、链接展示、轮询和 Session 恢复全部由 `ihr-shared` 负责，Bootstrap 不复制第二套授权状态机。

安装成功后的自动授权只适用于用户已经明确提出的业务请求：直接按授权协议调用 `auth ensure --open-browser --wait 1m --stream --source LOGIN_SOURCE --env RUNTIME_ENV`。`auth ensure` 自己读取本地 credential，已有有效 credential 时返回 `READY`，否则创建或复用授权 Session。授权阶段只展示授权入口、消费授权事件并等待终态；不得在授权 `READY` 前执行面谈业务，也不得把“是否继续授权”作为额外确认问题。授权尚未完成时，提示用户完成网页授权后回复“已授权”，由 `auth resume` 恢复原 Session。

- `CREDENTIAL_MISSING|AUTH_EXPIRED|ENVIRONMENT_MISMATCH`：普通登录。
- 真实结构化 `AUTH_REQUIRED`/HTTP 401 或用户主动重新登录：最多一次强制重授权。
- HTTP 403、网络错误、429、5xx：不登录。
- 授权终态 `READY` 后立即结束授权响应；后续业务在新的阶段开始。
