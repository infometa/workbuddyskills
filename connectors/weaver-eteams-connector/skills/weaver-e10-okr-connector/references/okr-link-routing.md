# 链路判定与详情页链接（okr-link-routing）

OKR 目标在不同租户使用**两套互不兼容的接口链路**。同一租户内只使用其中一条，判定结果由 CLI 按租户缓存，业务侧不应自行猜测链路。

## 判定依据

| 项 | 值 |
| --- | --- |
| 版本接口 | `POST /api/ebuilder/form/formdata/v2/getFormDataList/okr_searchAppver` |
| 版本字段 | `datajson.datas[].mainTable.ver_name` |
| 路由规则 | `ver_name >= V2` → ebuilder 链路；其它或接口不可用 → 标准版链路 |
| 缓存 | 按租户隔离，key 前缀 `okr:version:`，有效期 1 天（86400 秒） |

兼容 `V2` / `v2` / `V14` / `2` 等写法，只比较主版本号。

### `okr.version.check`

- 入参：`refresh`（boolean，默认 `false`）。`refresh=true` 时忽略缓存重新判定。
- 返回：`link`（`standard` | `eb`）、`verName`、`tenantKey`、`cached`、`degraded`、`reason`、`checkedAt`、`versionInterface`。
- **缓存只在真正拿到版本答案时写入**。标准版租户通常没有该 ebuilder 接口，此时接口报错会**降级为标准版链路**（`degraded=true`、`verName=null`、`reason` 说明原因），且**不写缓存**、不硬编码链路。

便捷入口：`weaver-work-cli --profile eteams okr route`（`okr.version.check` 的薄包装，加 `--refresh` 忽略缓存）。

## 两套链路的接口面

| 能力 | 标准版链路 | ebuilder 链路 |
| --- | --- | --- |
| 目标分页查询 | `POST /api/workrelate/goal/getSearchList` | `POST /api/ebuilder/form/formdata/v2/getFormDataList/okr_pageQueryGoal` |
| 目标详情 | `GET /api/workrelate/goal/getObjectDetail/{id}` | `POST /api/ebuilder/form/formdata/v2/getFormDataByPk/okr_queryGoal` |
| 关键成果列表 | 随目标列表/详情返回（`keyresultList`） | `POST .../getFormDataList/okr_pageQueryGoalKeyResults` |
| 关键成果保存 | `POST /api/workrelate/goal/fs/krForm/saveForm` | `POST .../saveFormData/okr_createKeyResult` / `.../updateFormData/okr_updateKeyResult` |
| 目标评论 | `POST /api/goal/common/comment/commentPage` | **无接口** |
| 目标对齐 | **无接口** | `POST .../saveFormData/okr_createGoalAlign` |
| 新建 / 编辑目标 | `POST /api/workrelate/goal/create` / `/update` | `POST .../saveFormData/okr_createGoal` / `.../updateFormData/okr_updateGoal` |

链路专属能力被调用时会返回 `policy/link_unsupported`，**不要换接口硬试**。

## ebuilder 目标详情页表单 id

ebuilder 链路的详情页地址形如 `/sp/ebdfpage/card/0/{okr目标详情eb表单id}/{目标id}`，其中的**表单 id 需要解析**：

| 项 | 值 |
| --- | --- |
| 应用标签 appTag | `weaver-wr-goal-eb` |
| 表单标签 formTag | `uf_wrgm_baseinfo` |
| 解析步骤 | `GET /api/bs/ebuilder/app/tags/getAppIds?tag=<appTag>` → `GET /api/ebuilder/form/obj/getObjsByTag?tag=<formTag>&appId=<appId>` |
| 已知固定租户 | 租户 `tqasclatif` 的 okr 目标详情表单 id 为 `1027322801024458753`，命中时跳过两步解析 |
| 缓存 | 解析结果按租户长期缓存（key 前缀 `okr:ebform:`） |

`okr.eb.form.resolve` 用于显式解析并返回该表单 id（仅 ebuilder 链路可用）。

**表单 id 解析失败只影响链接，不影响主操作**：链接降级为 `null` 并写入 `warnings`（「目标详情页链接暂不可用」），绝不因此让主查询/主写入失败或被重试。

## 详情页链接

| operation | 用途 |
| --- | --- |
| `okr.viewlink` | 传入目标 ID（数组或英文逗号拼接字符串），返回 `path`（站内相对路径）与 `url`（绝对地址） |
| `okr.detail.link` | 返回当前链路的地址模板，不含具体目标 id |

标准版地址模板 `/sp/goal/openDetail?id={goalId}`；ebuilder 地址模板 `/sp/ebdfpage/card/0/{formId}/{goalId}`。

## 注意

- 本 reference 只说明判定与链接语义，**接口路径不是可直接调用的地址**；实际调用一律通过 `weaver-work-cli --profile eteams okr run <operation>`。
- 链路判定结果来自租户实际版本，不要根据「客户是否上过 ebuilder」之类的经验臆断链路。
- 同一次任务内如果需要多次操作，复用同一租户的判定结果即可，不必每次 `refresh`。
