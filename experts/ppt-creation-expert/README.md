# PPT 制作专家（PPT Creation Expert）

把你的主题、资料或行业场景，一键变成专业演示文稿。

## 类型

Agent 型（单专家）

## 功能

PPT 制作专家整合了四套互补的技能，会根据你的需求自动路由到合适的一套：

- **通用 PPT 生成**：面向任意主题，通过需求澄清表单（主题/受众/风格/页数）快速收集需求后直接生成，支持基于文档或深度研究生成。
- **面客解决方案 PPT 生成**：面向"行业 + 场景"，围绕一个具体场景方案，通过多轮深度研究（知识库语义检索 + WebSearch + WebFetch），按"行业背景 → 需求挑战 → 解决方案 → 客户案例"四大板块组织，产出 30-45 页售前级方案（受众 CEO / CTO 均可，按岗位自动调节技术深度）。
- **高拜（Call High）材料生成**：面向客户高层（一把手/二把手）的战略拜访场景，不聚焦单一方案，按"腾讯云介绍 → 行业趋势与理解 → 重点合作项目与探讨"三段框架组织，产出 20-30 页宏观、战略视角、收口到高层拍板项目的拜访材料。
- **PPT 讲稿生成**：为已生成的 PPT 生成逐页演讲讲稿（口播稿）。读取 PPT 规划 + 深度研究报告，产出对齐每页的讲稿 + 页间过渡 + 开场/结尾 + 控场提示。三个出 PPT 技能生成完 PPT 后都会主动引导用户生成讲稿。

## 技能

| 技能名 | 说明 |
|--------|------|
| guided-ppt-creation-workflow | 通用 PPT 生成工作流：需求澄清 → 内容获取 → 生成 |
| solution-ppt-generator-v3 | 面客解决方案 PPT 生成器：深度研究 → 四大板块框架 → 30-45 页面客方案 |
| call-high-deck-generator | 高拜材料生成器：深度研究 → 三段框架 → 20-30 页高层拜访材料 |
| ppt-script-generator | PPT 讲稿生成器：读取 PPT 规划 + 研究报告 → 逐页口播稿 + 过渡 + 控场提示 |

## 使用示例

- 帮我做一个关于 AI Agent 的 PPT
- 帮我生成一份智慧医疗行业的面客解决方案 PPT
- 帮我做一份拜访某省联通董事长的高拜材料
- 把这份文档做成 PPT

## 依赖与配置

本专家的深度研究能力依赖**乐享知识库 MCP（lexiang）**。首次使用需完成一次连接配置：

- **依赖声明**：见 `.workbuddy-plugin/plugin.json` 的 `dependencies.mcpServers.lexiang`（http 类型，token 鉴权）。
- **鉴权方式**：token 鉴权，需提供环境变量 `LEXIANG_TOKEN`（通过请求头 `Authorization: Bearer ${LEXIANG_TOKEN}` 注入）。
- **获取 Token**：访问 `https://lexiangla.com/mcp?company_from=CSIG` 获取 `LEXIANG_TOKEN`，在专家的 MCP 连接引导卡片中填入。
- **验证连接**：技能在检索前会调用 `mcp__lexiang__whoami` 校验绑定状态；返回正常即表示已连接，可正常检索乐享知识库。
- **未连接/过期时**：技能会引导重新完成绑定；此时深度研究会降级为 WebSearch + WebFetch 补充（乐享内部素材将缺失）。

> ⚠️ 网关地址为司内内网域名（`*.agent-gateway.auth-proxy.local`），仅腾讯司内网络可访问。

## 头像

头像已自动生成在 `avatars/expert.png`。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：不超过 500KB

## 说明

两个既有技能模块（guided-ppt-creation-workflow、solution-ppt-generator-v3）均按用户要求**原样保留、未做任何改动**；新增的 call-high-deck-generator 技能撰写结构对齐 solution-ppt-generator-v3。专家层（agents/ppt-creator.md）只负责场景路由，技能内部的所有规则以各自 SKILL.md 为唯一权威来源。

## 打包

```bash
zip -r ppt-creation-expert.zip ppt-creation-expert/
```
