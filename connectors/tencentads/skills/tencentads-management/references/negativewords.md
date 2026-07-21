# 否定词管理（adgroup_negativewords）

---

## add.mjs — 新增否定词

```bash
node scripts/negativewords/add.mjs '{"account_id":"123456789","adgroup_id":987654321,"phrase_negative_words":["短语否词1","短语否词2"],"exact_negative_words":["精确否词1","精确否词2"]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `adgroup_id` | int64 | 广告 ID |
| `phrase_negative_words` | string[] | 短语否定词列表（每词最大 20 等宽字符 / 150 字节，数组最大 900 条，可为空数组） |
| `exact_negative_words` | string[] | 精确否定词列表（每词最大 20 等宽字符 / 150 字节，数组最大 900 条，可为空数组） |

**返回**：
```json
{
  "success": true,
  "adgroup_id": 987654321,
  "status": "OPER_SUCCESS",
  "duplicate_words": { "phrase_negative_words": [], "exact_negative_words": [] },
  "exceed_length_words": { "phrase_negative_words": [], "exact_negative_words": [] },
  "exceed_limit_words": { "phrase_negative_words": [], "exact_negative_words": [] },
  "has_special_words": { "phrase_negative_words": [], "exact_negative_words": [] },
  "success_words": { "phrase_negative_words": ["短语否词1"], "exact_negative_words": ["精确否词1"] }
}
```

> `status` 枚举：`OPER_SUCCESS`（全部成功）、`OPER_FAIL`（有操作失败）
> 失败详情通过 `duplicate_words`（重复词）、`exceed_length_words`（超长词）、`exceed_limit_words`（超限词）、`has_special_words`（含特殊字符词）返回

---

## update.mjs — 更新否定词

> ⚠️ **全量覆盖**：更新操作是全量替换，需传入完整的否定词列表。

```bash
node scripts/negativewords/update.mjs '{"account_id":"123456789","adgroup_id":987654321,"phrase_negative_words":["新短语否词1"],"exact_negative_words":["新精确否词1"]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `adgroup_id` | int64 | 广告 ID |
| `phrase_negative_words` | string[] | 短语否定词列表（全量替换） |
| `exact_negative_words` | string[] | 精确否定词列表（全量替换） |

**返回**：与 negativewords/add 相同结构。

---

## get.mjs — 查询否定词

```bash
node scripts/negativewords/get.mjs '{"account_id":"123456789","adgroup_ids":[987654321]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `adgroup_ids` | integer[] | 广告 ID 列表（最少 1 条，最多 100 条） |

**返回**：
```json
{
  "adgroup_list": [
    {
      "adgroup_id": 987654321,
      "phrase_negative_words": ["短语否词1", "短语否词2"],
      "exact_negative_words": ["精确否词1", "精确否词2"]
    }
  ],
  "adgroup_error_list": []
}
```

---

## 用户意图映射

| 用户表述 | 处理方式 |
|---------|----------|
| "否定词：免费、破解" / "排除关键词：免费" | 默认作为短语否定词，构造 `phrase_negative_words` 数组 |
| "精确否定：盗版下载" / "精确排除：XX" | 使用 `exact_negative_words` |
| "短语否定：免费" / "短语排除：XX" | 使用 `phrase_negative_words` |
| "查看/查询否定词" / "查看否词" | 调用 `negativewords/get.mjs`，传入 `adgroup_ids` |
| "添加否词：免费、破解" | 调用 `negativewords/add.mjs` |

> ⚠️ **注意**：`phrase_negative_words` 和 `exact_negative_words` 都是必填参数，如果用户只指定了一种类型的否定词，另一种传空数组 `[]` 即可。
