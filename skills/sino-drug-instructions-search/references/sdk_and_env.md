# sinohealth_skills_sdk 与运行说明

本 Skill 依赖 **sinohealth_skills_sdk**（`SkillsClient`）提供检索能力。

## 鉴权环境变量（脚本不写死默认值）

- **`SKILLS_BIZ_TYPE`**、**`SKILLS_BIZ_TOKEN`**：须由环境提供；脚本**不会**默认填 `workbuddy`。
- **推荐流程**：先 **`connect_cloud_service`**（按运行环境提供的 MCP/工具）→ **若成功**将返回值作为 **`SKILLS_BIZ_TOKEN`**，将 **`SKILLS_BIZ_TYPE`** 设为 **`workbuddy`** 并 `export` → 再运行脚本；**若失败**则仅使用已配置的环境变量。

若两者任一未设置，脚本会以非零退出并提示。

## 依赖安装

```bash
pip3 install -U sinohealth_skills_sdk
```

## 其它 SDK 环境变量

如 `SKILLS_TRACE_IDENTIFIER`、`SKILLS_TIMEOUT` 等以 SDK 官方文档为准。
