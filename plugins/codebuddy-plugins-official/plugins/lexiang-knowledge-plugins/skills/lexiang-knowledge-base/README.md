# 乐享 MCP - ClawHub 外部版本

> 适用于外部 ClawHub / mcporter 用户

## 认证方式

需要用户自行配置：
- `COMPANY_FROM`：企业标识（从 https://lexiangla.com/mcp 获取）
- `LEXIANG_TOKEN`：访问令牌（格式 `lxmcp_xxx`）

## 配置方式

### 方式1：环境变量（推荐）

```bash
export COMPANY_FROM="your_company"
export LEXIANG_TOKEN="lxmcp_YOUR_TOKEN_HERE"
```

### 方式2：直接修改 mcp.json

将 `${COMPANY_FROM}` 和 `${LEXIANG_TOKEN}` 替换为实际值。

## 快速配置

运行 setup.sh 进行交互式配置：

```bash
bash setup.sh
```

## 使用说明

详细工具文档请参考 `lexiang-base/SKILL.md`
