# Picset AI 电商图片 0.1.1

这是 WorkBuddy 的 Picset MCP + Skill 包。主 Skill 负责路由，`picset-commerce-image-suite` 负责规划和生成商品主图、独立详情图与 Listing 套图。

连接器使用 `PICSET_AGENT_SK` Bearer 鉴权并调用 `https://picsetai.cn/functions/v1/agent-mcp-v1/mcp`。本地素材通过公共 Python `urllib.request` 上传器上传；不需要第三方 `requests` 或 OSS SDK。

## 使用方式

1. 在连接器配置中填写 Picset AI Secret Key；
2. 附加本地商品图并说明平台；系统只读取附件、建立并展示 `SuiteDraft`，此时不报价、不获取 STS、不上传、不登记；
3. 检查并修改 `SuiteDraft`，发送新的明确消息确认草稿方案（停点一）；
4. 草稿确认后一次调用快速积分报价，查看主图/详情图的数量、比例、2K、单价、小计和总计；该回合不获取 STS、不上传、不登记、不生成；
5. 发送新的明确消息接受提交时实时积分（停点二）；随后才执行 MCP 获取 STS → 本地 Python 上传 OSS → MCP 登记素材 → 生成 prompts 并提交；
6. 静默轮询后下载结果，并使用 WorkBuddy 当前会话右侧预览栏打开返回的本地文件；只预览，不分析图片，按 `M...`、`D...` 查看或局部重做。

完整顺序固定为：读取本地附件 → 建立并展示 `SuiteDraft` → 用户修改 → 草稿方案确认 → 快速积分报价 → 积分确认 → 上传并登记素材 → 生成 prompts 并提交 → 静默轮询 → 下载并在宿主内预览 → 稳定编号展示。不得调用系统 `open` 或外部 Preview.app。

当前服务比例固定为主图 `1:1`、详情图 `3:4`。`1:4` / `1:8` 参数化长图留到后续版本。

Amazon A+、PSD 分层、普通创意单图模型选择、商品原图精修，以及已有图片的长图拼接/切片尚未进入第一版。
