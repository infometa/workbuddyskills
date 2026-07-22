# Singapore HR & Admin Expert

新加坡人力行政专家 — Agent 型专家模型。精通新加坡招聘、工签（EP/SP/WP）、薪酬福利、CPF社保、Employment Act、办公场地租赁及人力资源全流程合规，基于政府公开数据和商业薪酬报告辅助企业决策。

## 类型

Agent 型（单个 AI 专家）

## 核心能力

- 招聘与工签：EP/SP/WP 申请 + COMPASS 评分 + FCF 合规 + SOL 紧缺职业
- 薪酬与 CPF：薪酬结构设计 + CPF OW/AW 分类 + 代通知金/假期折现 CPF 规则 + 雇主成本模型
- 劳动合同与雇佣法律：Employment Act + Part IV + KETs + 裁员 MRN + TADM/ECT
- 办公场地：URA 租金指数 + CBD/郊区成本 + 服务式办公室对比
- 中国企业专项：外派模型 + 数据跨境 PDPA + 人力成本对比 + HR 启动清单
- 170+ 条推理与自检规则 + 24 个官方数据模块

## 使用示例

- "我们公司计划在新加坡招聘一名高级软件工程师，请帮我梳理 EP 申请条件和合规薪资基准"
- "新加坡办公室租赁需要关注哪些行政流程？CBD 和郊区在租金水平与合规要求上有什么差异？"
- "新加坡员工离职与裁员的法律规定和行政流程是什么？遣散费如何计算？"

## 数据模块

专家内置 18 个结构化数据模块，涵盖 EP/SP 门槛、CPF 费率与 OW/AW 规则、法定假期、个税税率、Levy 按行业、KETs 字段、MRN 规则、办公成本基准、违规处罚参考等。数据按模块分文件存储在 `skills/sg-hr-data-sync/references/data/`，每季度自动同步更新。

## 依赖

- SingStat MCP：连接后可查询 2,500+ 新加坡官方统计数据集。该 MCP 无需认证，专家在首次对话时引导用户连接。

## 安装

将压缩包解压到 WorkBuddy 专家目录，重启 WorkBuddy 后可见。

## 打包分享

```bash
zip -r sg-hr-admin-expert.zip sg-hr-admin-expert/ -x "*.gitkeep" "*.created-by-session" "__pycache__/*" "*.pyc"
```
