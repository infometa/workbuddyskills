# 共享 MCP 工具合同

所有业务使用 WorkBuddy 实际加载的本连接器 `shenhuo-designers` MCP 工具，保持宿主实际工具名称及前缀；服务键对应根目录 mcp.json，connector-meta.json 的 source 是发行身份，二者都不是必须手动拼接的工具前缀。OAuth 由客户端管理，不在工具参数中传密码、API Key 或 Token。

| 工具 | 参数与作用 |
|---|---|
| get_account | 无参数；个人账号及积分 |
| list_designers | 无参数；实时公开可调用目录 |
| get_designer | designer_id；输入要求、默认规格、公开模型档位（如 Pro／Flash） |
| create_upload | filename、mime_type、role、idempotency_key，可选 label；短期原始文件上传票据 |
| get_upload | transfer_id；上传状态、资产 ID、哈希 |
| match_designer | brief、idempotency_key；可选 asset_ids、target_image_count、image_spec；匹配可能收费 |
| create_design | brief、designer_id、idempotency_key；可选 asset_ids、routing_evaluation_id、target_image_count、image_spec；创建个人项目并提案 |
| get_task | kind（routing/design/generation）、task_id；查询原任务、追问、方案、结果与项目链接 |
| answer_questions | design_request_id、answer、idempotency_key；可选新增 asset_ids；真实追问回答 |
| quote_images | design_request_id、idempotency_key；报价、此前费用和余额 |
| generate_images | design_request_id、quote_id、idempotency_key、user_confirmed=true；确认有效报价后异步生图 |
| get_result | variant_id、idempotency_key；已结算作品预览及下载凭证 |

`image_spec` 示例为 `{"resolution":"2K","aspect_ratio":"3:4"}`；默认选择省略此字段，不从示例复制。匹配与建项使用 `target_image_count="auto"`，数量要求原样放入 brief，由神火系统设计师解析并决定交付清单。`requires_action` 携真实追问时才等待回答；`ready` 且无待处理追问时直接进入整组报价，不让用户从 final_prompts 中选风格或页码。生图轮询遵循主 Skill 的分阶段等待策略，持续查询原任务直到终态。服务端的完整 Schema 和回执优先于本表。

401／OAUTH_REAUTHORIZATION_REQUIRED：重新授权后恢复原任务。OAUTH_INSUFFICIENT_SCOPE：说明所需权限，重新连接取得该权限。GENERATION_QUOTE_STALE：新报价、新确认。INSUFFICIENT_CREDITS 或 can_run=false：暂停付费操作，展示真实缺口并提供[官网充值入口](https://www.shenhuoai.com/home/recharge)，提示同一账号充值后回复继续；核验余额、恢复原任务并确认有效报价，完整步骤见主 Skill。RATE_LIMIT_EXCEEDED：按返回的 retry_after 等待，同一操作沿用原键和参数。网络超时：查询原 ID，或相同键、相同输入重放。不同写操作使用不同的唯一键；幂等冲突先核对原操作状态。所有费用和错误使用真实回执，不改写成成功。

内容安全检查在上传、匹配或建项前执行，完整规则见主 Skill。服务端返回 CONTENT_SECURITY_REJECTED 或其他安全拒绝时停止对应操作并说明真实原因；不改写请求绕过审查。对外仅展示公开模型档位，不能展开内部模型名称、供应商配置、密钥或内部设计师提示词。
