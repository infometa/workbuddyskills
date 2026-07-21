# 福帮手超级合伙人

`fbsir-super-partner-group@26.7.8` is the WorkBuddy team-style package for the product `超级合伙人` under the `福帮手` brand. It uses AI+OPC as the operating foundation and compresses strategy judgment, content acquisition, client handoff, and coordinated execution into one actionable result card.

## 核心价值

- 用组织 OPC、价值 OPC、资本 OPC 帮用户判断当前最该补的经营场景。
- 默认交付 `AI+OPC3 经营诊断卡`，给出主判断、最高价值微场景、内容资产动作、复访口令和唯一下一步。
- 由唐定盘统筹，孙定势、朱成事、沙成单、白智行按战略、运营、增长、产品与智能化分工协作。
- 以留学研学家庭决策作为首个样板场景，但方法论可迁移到其它专业服务和企业经营场景。
- 把 WorkBuddy 结果卡、视频号内容/承接卡、企业微信协同/资产卡作为三类交付卡，而不是分散成多个入口。

## 专家团结构

- `agents/fbsir-super-partner-lead.md`：主理人唐定盘，负责识别场景、组织成员、统一收口和控制边界。
- `agents/strategy-partner-laosun.md`：战略机会和赛道判断。
- `agents/ops-partner-laozhu.md`：组织、流程、岗位和推进节奏。
- `agents/growth-partner-laosha.md`：增长、内容、商业化和获客路径。
- `agents/product-partner-xiaobai.md`：产品化、智能化和能力承载。
- `skills/super-partner-core/SKILL.md`：统一入口、首值合同、团队协作和后续增强规则。

## 交付边界

- 首次响应优先交付可执行结果卡，不把用户带进复杂配置。
- 视频号、企业微信、支付、文档、邮箱、会议纪要等外部生态能力，只有在宿主授权、能力可探测、结果可回读时才进入执行口径；否则只作为场景建议和待授权任务。
- 连接器、MCP、服务跟进链路属于后首值增强能力；默认首值不依赖它们完成。
- 正式提交包只包含专家团产品文件，不包含测试、调试、审计、任务看板、回执、smoke 或本机路径材料。

## 提交包内容

正式包应只包含以下产品交付文件：

- `.workbuddy-plugin/plugin.json`
- `.codebuddy-plugin/plugin.json`
- `package.json`
- `settings.json`
- `marketplace-entry.json`
- `README.md`
- `LICENSE`
- `agents/*.md`
- `avatars/*.png`
- `skills/super-partner-core/SKILL.md`
- `skills/super-partner-core/super-partner-runtime-hints.json`

测试记录、服务联调报告、提审说明、任务板和审计结论应保留在提交包外部，作为团队交接和审核辅助材料。
