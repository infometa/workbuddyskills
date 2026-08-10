# 技能匠人 Skill Smith

陪制作者把重复工作流做成可用的 Skill：挖掘场景、确认需求、生成制作、实测验证、按标准审查打分。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 新建 Skill：场景挖掘、需求确认、写入确认、生成、自检、打包和用户级安装
- 优化已有 Skill：只读审查、11 项评分、修复确认、备份、最小侵入修改和复测
- 制作咨询：判断想法是否适合做 Skill、大赛选题建议
- 安全测试：不可信内容隔离、脚本静态预检、受限环境实测和未执行降级
- 依赖设计：MCP、CLI、API、账号和本地环境的配置引导、环境检查、就绪路由与功能降级

## 包内资源

内置 Skill：`skills/skill-crafting/`

- `SKILL.md`：制作、审查、打包和安装的顶层流程
- `references/creation-guide.md`：制作标准
- `references/review-standards.md`：五阶段审查与制作质量 11 项
- `references/common-pitfalls.md`：常见坑和选题建议
- `references/trigger-testing.md`：触发词挖掘、near-miss 和基线对比
- `references/safe-execution.md`：不可信内容和脚本安全执行
- `references/dependency-configuration.md`：依赖配置、环境检查、就绪路由和功能级降级
- `references/output-templates.md`：需求、依赖、环境、降级、测试、评分、修复和交付模板
- `references/platform-compatibility.md`：WorkBuddy 字段、版本、路径和安装规则
- `assets/dependency-kit/check_environment.py`：可复制到依赖型 Skill 的只读环境检查器
- `assets/dependency-kit/skill-dependencies.schema.json`：依赖与普通功能降级清单结构
- `assets/dependency-kit/probe-results.schema.json`：可信宿主的脱敏认证和 MCP 探测结果结构
- `scripts/skill_ops.py`：生成、校验、静态预检、备份、打包和用户级安装

## 包内命令

```text
python skills/skill-crafting/scripts/skill_ops.py validate <skill-dir>
python skills/skill-crafting/scripts/skill_ops.py preflight <skill-dir>
python skills/skill-crafting/scripts/skill_ops.py backup <skill-dir> --output <zip-path> --write-confirmed
python skills/skill-crafting/scripts/skill_ops.py package <skill-dir> --output <zip-path> --write-confirmed
python skills/skill-crafting/scripts/skill_ops.py install <skill-dir>
```

生成命令分别使用需求确认和写入确认参数；备份与打包使用 `--write-confirmed`。安装命令默认只输出计划，执行安装时同时使用 `--apply --install-confirmed`。静态预检阻断的脚本不得直接打包或安装；人工复核接受风险时必须记录 `--risk-ack` 说明。

## 使用示例

- 我每次写周报都要重新教 AI 我们团队的格式，能做成 Skill 吗
- 这是我写的 Skill，帮我看看质量怎么样、哪里要改
- 我想参加 Skill 制作大赛，但只有个模糊想法，帮我理一理

## 头像

头像位于 `avatars/`，支持 PNG 或 JPG，512×512 px，单张不超过 500KB。

## 专家校验与注册

从专家管理器目录运行：

```text
python scripts/validate_expert.py <expert-dir>
python scripts/register_expert.py <expert-dir> --session-id <session-id>
```

## 打包分享

从专家管理器目录运行：

```text
python scripts/package_expert.py <expert-dir> <output-dir>
```
