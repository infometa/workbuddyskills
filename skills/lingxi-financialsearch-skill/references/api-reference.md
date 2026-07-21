# API 参考 & 错误码对照表

## MCP 网关端点

| 领域 | 网关 | 地址 | 环境 |
| --- | --- | --- | --- |
| 金融数据查询 | financial | `https://zx.app.gtja.com:8443/mcp/financialsearch/lingxi` | 生产环境 |

## 可用工具

| 工具名称 | 参数 | 描述 |
| --- | --- | --- |
| `financial-search` | `query` (string, 必填) | 自然语言查询A股实时行情、公司基本信息、F10财务数据、个股技术指标等金融数据 |

## 调用示例

```bash
node skill-entry.js mcpClient call financial financial-search query='查询科大讯飞营业收入和贵州茅台净利润'
```

## 错误码对照表

| 错误码 | 含义 | 可能原因 | 解决方案 |
| --- | --- | --- | --- |
| 400 | 请求参数错误 | 传入的参数格式不正确或缺少必填参数 | 检查工具所需的参数，确保格式正确 |
| 401 | 未授权 | API Key 过期或无效 | 删除 `./gtht-skill-shared/gtht-entry.json`，重新执行 `node skill-entry.js authChecker auth` |
| 403 | 禁止访问 | 没有权限访问该工具 | 联系管理员确认权限配置 |
| 404 | 工具不存在 | 工具名称错误或网关地址变更 | 检查工具名称是否正确 |
| 500 | 服务器内部错误 | MCP 网关服务异常 | 稍后重试，或联系管理员 |
| 502/503 | 网关不可用 | 网关服务暂时不可用 | 检查网络连接，稍后重试 |
| ECONNREFUSED | 连接被拒绝 | 无法连接到网关服务器 | 检查网络连接，确认网关地址是否正确 |
| 授权超时 | 用户未在规定时间内扫码 | 用户未及时完成授权 | 重新运行 `node skill-entry.js authChecker auth`，按提示重新扫码 |

## 网关配置文件格式

**文件**: `gateway-config.json`

```json
{
  "active_env": "PROD",
  "base_urls": {
    "test": "https://test.gtjadev.com:38443/",
    "prod": "https://zx.app.gtja.com:8443/"
  },
  "gateway_paths": {
    "financial": "mcp/financialsearch/lingxi"
  },
  "gateways": {
    "financial": "https://zx.app.gtja.com:8443/mcp/financialsearch/lingxi"
  }
}
```
