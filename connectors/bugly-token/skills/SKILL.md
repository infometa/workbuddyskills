---
name: bugly-quality-overview
description: 查看 Bugly 产品质量概览（崩溃率、ANR 率、FOOM/OOM 率、启动耗时等）。当用户询问应用的大盘质量、版本质量、今日质量等指标时使用。
---

# Bugly 质量概览

本 Skill 配合 Bugly MCP Server（HTTP / streamableHttp，token 模式）使用，提供产品质量概览能力。

## 能力

- 查看应用的大盘质量概览（崩溃率 / ANR 率 / FOOM(OOM) 率 / 启动耗时）
- 查看指定版本的质量概览
- 查看今天的质量概览

## 鉴权说明（用户自填 Token 模式）

本连接器使用 `auth_mode: "token"`，凭证由用户自行从 Bugly 平台获取并在 WorkBuddy 表单中填入：

- `BUGLY_ACCESS_TOKEN`：访问 Bugly OpenAPI 的个人访问令牌，注入到请求头 `Authorization: Bearer ${BUGLY_ACCESS_TOKEN}`。
- `BUGLY_API_BASE_URL`：MCP Server 入口地址，默认 `https://bugly.mcp.it.woa.com`，私有部署可改为内网地址。

凭证仅存储在本机 `~/.workbuddy/connectors/bugly-token/` 下，不会上传云端。

## 如何重新生成 / 更换 Token

如果调用返回未授权（401/403），通常是 Token 失效或被撤销。请到 Bugly 控制台重新生成 Access Token，然后在 WorkBuddy 的连接器设置中重新填入并保存即可，无需重启 WorkBuddy（下次连接即生效）。
