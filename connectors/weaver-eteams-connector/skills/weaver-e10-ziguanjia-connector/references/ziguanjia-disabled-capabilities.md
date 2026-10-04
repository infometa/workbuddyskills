# 暂未暴露的能力

本文件列出当前 `weaver-e10-ziguanjia-connector` manifest 未暴露、或明确禁用的资管家能力，以及遇到这些意图时的处理边界。

## 已禁用 / 暂未暴露

| 能力 | 状态 | 原因与边界 |
| --- | --- | --- |
| 资产调拨（`asset.transfer`） | 禁用 | 源资料未提供稳定的调拨接口路径、目标资产/接收人 ID 解析来源与写后回查契约。需要补充稳定接口与回查后再开放。 |
| 流程审批（`asset.approve`） | 禁用 | 审批处理未覆盖，源资料未提供审批动作流或回查契约。走通用流程编排 Skill，不要在本 Skill 内猜测。 |
| 图片上传（`asset.file.upload`） | 禁用 | 图片上传依赖外部文件上传模块；CLI 的 `asset.create` 仅接受已上传后得到的裸 `file_id`，不内置文件上传。需要上传时走对应文件上传能力，再把它返回的 `file_id` 传入 create。 |

## 遇到这些意图时

- 不要假装这些能力可用；不要用未出现在 `weaver-work-cli asset schema` 中的 operation。
- 向用户说明当前 CLI 不支持该动作，并给出原因（缺少稳定接口 / 回查契约 / ID 解析来源）。
- 若用户确实需要，先确认源资料里是否有稳定接口与回查方式，再按 CLI 规范实现并补测试、reference 与 docs 后开放。

## 不在本 skill 范围

- 非资产类 E10 业务、通用流程编排、表单/审批/组织等业务不由本 Skill 承载。
- 禁止绕过 `weaver-work-cli` 直接访问 E10 `/api/ebuilder/*`、`/api/esb/*`。
