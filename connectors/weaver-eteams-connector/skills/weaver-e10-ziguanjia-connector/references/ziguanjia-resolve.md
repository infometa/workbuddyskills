# 名称解析（存放地点 / 资产状态 / 资产类型）

## 什么时候读取

用户给出资产状态、资产类型或存放地点的中文名称，而写操作需要对应 ID 时读取本文件。

## Operation 与字段

| Operation | 名称字段 | 解析得到的 ID 用途 |
| --- | --- | --- |
| `asset.resolve.location` | `house_name` | 写入 `location_browse` |
| `asset.resolve.status` | `status_name` | 写入 `stateid` |
| `asset.resolve.type` | `type_name` | 写入 `asset_type_browse` |

三个 operation 均为只读，返回 `items`（含 `id` 与 `name`）。解析到 0 条会报 `resolve_not_found`，解析到多条会报 `resolve_ambiguous` 并要求改用 ID。

### 解析规则（源资料 _dict.md）

- **精确优先**：先按名称精确匹配；部分环境名称过滤不生效返回空时，自动回退全量枚举（pageSize 50）后在结果中按名称精确匹配。
- **模糊兜底**：精确与枚举均无命中时，按 contains 模糊匹配（如用户搜「笔记本」命中正式名「便携式计算机」）；仅命中单条即采用，返回 `matched:"contains"` 并在 `note` 中注明映射到正式名；命中多条报 `resolve_ambiguous` 候选。
- **资产类型缓存**：`asset.resolve.type` 首次解析某环境会全量拉取 `zgjasset_type_info` 并落到 skill 包之外 `~/.workbuddy/data/weaver-e10-ziguanjia-connector/asset_type_cache_{env}.json`（按环境隔离，24h 过期），之后本地匹配不再打接口；该缓存严禁写入 skill 包内。
- **已知名称映射**：本环境正式名如「便携式计算机」而非「笔记本电脑」、「液晶显示器」而非「显示器」、「办公椅」而非「椅子」、「办公桌」而非「桌子」，模糊匹配会按正式名解析；0 命中如实告知用户该名称在字典中不存在，不强行创建。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json asset run asset.resolve.type --input-json '{"type_name":"EXAMPLE_TYPE"}'
weaver-work-cli --profile eteams --json asset run asset.resolve.status --input-json '{"status_name":"EXAMPLE_STATUS"}'
weaver-work-cli --profile eteams --json asset run asset.resolve.location --input-json '{"house_name":"EXAMPLE_LOCATION"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json asset run asset.resolve.type --input-json '{"type_name":"EXAMPLE_TYPE"}'
weaver-work-cli --profile eteams --json asset run asset.resolve.status --input-json '{"status_name":"EXAMPLE_STATUS"}'
weaver-work-cli --profile eteams --json asset run asset.resolve.location --input-json '{"house_name":"EXAMPLE_LOCATION"}'
```

## 返回

返回 `items`：`[{ "id": "<解析得到的 ID>", "name": "<名称>" }]`。把 `id` 带入后续写操作的 `asset_type_browse` / `stateid` / `location_browse`。

## 注意

- 解析结果 `id` 是字符串，后续写操作必须原样使用，不要重新按名称猜测。
- 解析到多条时，优先向用户确认用哪一条，或要求用户直接提供 ID，不要随机选取。
