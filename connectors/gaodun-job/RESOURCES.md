# 资源加载说明（RESOURCES.md）

本连接器的 15 个 Skill 分两类，对运行环境的要求如下：

## 一、MCP 工具型（8 个）

gaodun-job-selection / gaodun-notice-search / gaodun-major-search / gaodun-campus-position-search /
gaodun-internship-position-search / gk-answer / interview-brush / mock-interview-report

- 依赖 `mcp.json` 声明的 MCP Server（Streamable HTTP，生产环境），无本地运行时依赖。
- `references/*.md` 为行为契约与提示词规范，随 SKILL.md 一起按需读取（Read 工具），无需执行。
- `interview-brush` 附带 `scripts/capsule_config.py` 与 `data/` 为抽题胶囊静态配置，Python 3 标准库即可运行。

## 二、本地计算型（7 个）

sycp / career-personality / career-anchor / holland / career-ability / resume-diagnosis / resume-ai-help

- 题库与配置在 `references/`（JSON/MD），评分与解析脚本在 `scripts/`，均为 **Python 3 标准库**实现（
  仅 resume-ai-help 的 HTML 渲染额外依赖 `jinja2`，简历 .doc 提取依赖可选的 Spire.Doc，缺失时按 SKILL.md 的降级路径处理）。
- 脚本通过 Bash 工具调用、Read 工具读取 references——即 Agent 环境的标准文件与命令能力，无网络依赖、不外发数据。
- `resume-ai-help` 的 prompt 原文、简历模板与模块配置**不随包分发**，运行时经 MCP 工具 `resume_resource_bundle_get`（兜底 `resume_prompt_get`/`resume_module_config_get`/`resume_template_get`）从服务端获取。

## 三、重复文件说明

`references/resume-module-config.json` 仅 resume-diagnosis 携带本地副本（其解析评分为纯本地流水线）；
resume-ai-help 改为运行时经 `resume_resource_bundle_get` 从服务端获取模块配置，不再随包分发副本。
