# 国际化 / 海外场景定向检索（国际版=是）

> 站内链路上的**正交叠加开关**（`intl=on`）。命中国际化/海外意图时，对 `search_kb_embedding_search` **注入「国际版=是」的 UDF 过滤**，优先召回国际版知识，再做二次筛选剔除国内版噪声。**不联网**、不改变纯站内属性，可与 `mode=standard` 叠加。

---

## 一、意图判定（Phase 1 前置闸门 · 与竞品门控正交）

当用户问题涉及以下任一场景，置 `intl=on`：

- 国际版、海外版、海外市场、出海相关
- 多语言、语言支持、翻译、本地化、多地区适配
- 明确点名某海外地区/站点（如「新加坡节点」「海外金融行业案例」「国际站」）

触发词：**海外、国际版、国际站、出海、海外市场、多地区、多语言、语言支持、翻译、本地化、overseas、international、global**。

判定规则：

- 命中 → `intl=on`，本轮所有 `search_kb_embedding_search` 调用**都注入** UDF 过滤（见第三节），并**强制二次筛选**（见第五节）。
- 未命中 / 不确定 → `intl=off`，走常规站内检索，**不注入** UDF 过滤。
- `intl` 与 `mode`（standard/competitive）**相互独立**：竞品对比里若同时涉及海外（如「海外版 COS 对比阿里云 OSS 海外」），通道 A 站内基线可叠加 `intl=on`；通道 B 站外仍按竞品规则走。

---

## 二、关键参数（2026-08-25 实测 · company 级全局属性）

> 「国际版」是 company 级全局自定义属性（`is_global=true`），`field_type=select`。

| 项 | 值 |
|---|---|
| 字段名 | 国际版 |
| **field_id** | **`250b20760fb74e8bb32955fe83c919cc`** |
| 「是」值代码 | **`lsihfg3ix6d`**（不能用中文「是」） |
| 「否」值代码 | `6duiyp9qyav` |

⚠️ **select 字段过滤 `value` 必须传选项值代码**（`lsihfg3ix6d`），用显示文本「是」会导致过滤失效。

---

## 三、调用结构（`intl=on` 时的 embedding 检索模板）

在原有 `search_kb_embedding_search` 参数基础上追加 `filters.udf_values`：

```json
{
  "filters": {
    "keyword": "<Phase 1 改写产出的语义检索词>",
    "udf_values": [
      {
        "match_logic_type": "and",
        "k_values": {
          "field_id": "250b20760fb74e8bb32955fe83c919cc",
          "values": [ { "value": "lsihfg3ix6d" } ]
        }
      }
    ]
  },
  "limit": 10,
  "threshold": 0.3
}
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `filters.keyword` | 是 | 语义检索词，1–1024 字符 |
| `filters.udf_values` | 是（intl=on 时）| 固定过滤「国际版=是」 |
| `k_values.field_id` | 是 | 固定 `250b20760fb74e8bb32955fe83c919cc` |
| `k_values.values[].value` | 是 | 固定 `lsihfg3ix6d` |
| `match_logic_type` | 否 | 单条件用 `and` |
| `threshold` | 否 | 默认 0.3，别设太高（漏召） |

---

## 四、执行步骤（叠加进 Phase 2 通道 A）

1. Phase 1 判定 `intl=on`。
2. 按 `query-rewriting.md` 正常改写检索词（海外场景可在同义词扩展里补 international/overseas/global 及具体地区名）。
3. 组装每条 Query 的 `search_kb_embedding_search` 参数时，**统一追加 `filters.udf_values`**（第三节模板）。
4. 批量并行调用，按 `target_id` 去重排序。
5. **强制二次筛选**（见第五节）。
6. 兜底判断同常规：全空 / 全低相关时才启用 `search_kb_search`（keyword 接口用 `filters.udf_filters.find_values` 也支持同一 UDF 过滤）。
7. 汇总呈现，链接与引用规则同 `answer-generation.md`。

---

## 五、软过滤 → 强制二次筛选（必须）

⚠️ 乐享 UDF 过滤是**软过滤（加权召回，非硬性排除）**，返回结果仍会混入国内版内容。`intl=on` 时**必须**再做一次内容级筛选：

- 保留标题/正文含「国际版 / 海外 / 出海 / 国际站 / international / overseas / global」等特征，或明确国际版属性命中的条目；
- 剔除明显是国内版的条目后再进入 Phase 3 作答；
- 若二次筛选后有效条目为 0，按 `mode=standard` 拒答策略处理（明确告知「未在乐享知识库检索到国际版/海外相关内容」，不联网兜底）。

---

## 六、多条件叠加与字段速查

叠加其他属性（如「文档语种=英语」）时，在 `udf_values` 数组追加一项，`match_logic_type` 控制 and/or。company 全局级自定义属性速查：

| 属性名 | field_id | 类型 | 选项值代码 |
|---|---|---|---|
| 国际版 | `250b20760fb74e8bb32955fe83c919cc` | select | 是=`lsihfg3ix6d` / 否=`6duiyp9qyav` |
| 文档语种 | `7d4c2885b8f64cd1b3baba4a50d6e043` | select | 简中=`97yhsq3hd3g`、英语=`wipuq6c1urr`、韩语=`76t8moqfrzw`、日语=`ksypfrptyjh`、泰语=`lzwmlcumvec`、印尼语=`6tg7yeqe3yc`、繁中=`8lfl136tz3`、葡语=`2s1oknndo0u` |
| 是否归档 | `e99dbed33f2e4ba2ae74990206f1e8dc` | select | 上架=`zfwhqe8o5al` / 归档=`x2t0jox4zfp` |
| 文档类型 | `edcce54ac342408b90fccc11086d0f2f` | category | 多级树 |

### field 配置可能变动 · 重新枚举方式

field_id / 值代码随后台配置调整，若过滤明显失效，用乐享 MCP 的 3 个隐藏工具（`search_tools` 搜 `udf` 才可见，均 `unlisted:true`）重新确认：

1. `knowledge_user_defined_field_list_entry_fields` — 枚举某 entry 可设的自定义属性（含 field_id/类型/选项）
2. `knowledge_user_defined_field_list_field_values` — 读某 entry 的属性值（含选项值代码）
3. `knowledge_user_defined_field_update_field_value` — 更新属性值

用 `call_tool` 包装，`arguments` 传 `{"entry_id": "<某条目 entry_id>"}`。
