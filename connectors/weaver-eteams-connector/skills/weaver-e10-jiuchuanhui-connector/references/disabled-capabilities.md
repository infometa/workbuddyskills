# 禁用能力边界（disabled-capabilities）

## 何时使用

用户表达九氚汇相关意图，但目标能力不在 `weaver-work-cli --profile eteams jiuchuanhui schema` 中，或源资料给出了接口但尚未安全封装为 CLI operation 时。

## 未暴露为 CLI operation 的能力

| 能力 | 原因 | 处理方式 |
|---|---|---|
| `jiuchuanhui.sale.stage-advance`（商机阶段推进） | 依赖缓存 `sale_stage` 配置做阶段 ID 映射与前置校验，属于 Skill 编排层职责 | 用 `sale.update` + `sale.stage.search` 组合实现；先查阶段选项，再按目标阶段映射 ID 走 `sale.update.prepare/apply` |
| `jiuchuanhui.ds.fields`（表单字段发现） | 缓存初始化（`cache.init`）已在 `config/{pk}.json` 的 `detail` 中合并字段 `component_type`，字段信息直接读缓存即可，无需单独调用 `/api/ebuilder/common/ds/fields` | 字段 `component_type` 来自缓存配置，未封装为独立 CLI operation |

## 处理规则

- 禁止绕过 CLI 直接 curl、fetch、浏览器自动化或拼 E10 原始接口。
- 禁止加载原始 `weaver-e10-jiuchuanhui-connector` 源 Skill 代替 CLI；禁止直接运行源目录 `scripts/*.mjs`。
- 禁止读取或复制 CLI runtime 内部 Token、Cookie、ETEAMSID。
- 源资料中有、但 CLI 未暴露的接口，**不要自行调用原始接口，也不要编造 operation**：先明确告知用户该能力暂不可用，并由连接器维护方评估是否补 operation。

## 注意

- 缓存文件 `~/.weaver-e10-jiuchuanhui-connector/{tenantKey}/{userId}/` 是 Agent 本地状态，不随 Skill 打包、不入库。
- 不要编造不存在的 operation 或字段。
