# Region Insight WorkBuddy Connector 上架自查结论

依据 `WorkBuddy Connector 第三方开发者对接规范.docx`，`region-insight` 采用 MCP + Skill + 用户自填 Token 模式提交。

## 结论

当前目录已补齐静态提交包和压测报告材料，可作为 WorkBuddy Connector 上架审核包提交。需要使用有效 `REGION_INSIGHT_API_KEY` 完成最终线上联调复核；该项不应在文档中伪造结果。

## 提交文件

| 文件                               | 状态  | 说明                                                                                                |
| -------------------------------- | --- | ------------------------------------------------------------------------------------------------- |
| `connector-meta.json`            | 已具备 | `source` 为 `region-insight`，`type` 为 `mcp`，`auth_mode` 为 `token`，`minWorkbuddyVersion` 为 `4.23.0` |
| `mcp.json`                       | 已具备 | 单一 SSE server，HTTPS 地址，通过 `Authorization: Bearer ${REGION_INSIGHT_API_KEY}` 注入凭证                  |
| `token-schema.json`              | 已具备 | 包含 `title`、`description`、`fields`，字段 key 与 `mcp.json` 占位符一致                                       |
| `icon.png`                       | 已具备 | 根目录图标文件，满足 `icon.svg` 或 `icon.png` 的文件名要求                                                         |
| `skills/region-insight/SKILL.md` | 已具备 | 包含 Frontmatter、工具清单、调用流程、坐标规则、鉴权和错误处理                                                             |
| `load-test/README.md`            | 已具备 | 包含压测环境、QPS、延迟、错误率、资源占用和 SSE 长连接结果                                                                 |
| `load-test/*.png`                | 已具备 | 压测曲线和资源截图，使用相对路径引用                                                                                |

# 
