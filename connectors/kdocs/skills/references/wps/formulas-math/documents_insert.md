# wps.formulas.math

#### 功能说明

插入公式

**幂等性**：是 — safe

> 段落插入用 paragraph_index（1-based），公式插入在目标段落末尾、保留段落原有内容；区间插入用 begin/end（0-based），替换该区间文本，可由 wps.texts.search 返回的 ranges 回填。paragraph_index 与 begin/end 二选一，同时给定时优先 begin/end。
> display_type 为 WdOMathType 枚举：0=wdOMathDisplay（专业格式，独立成行）、1=wdOMathInline（内嵌）；缺省 0。
> 插入成功后用 wps.formulas.math verb=query 读回公式列表核验落点（paragraphIndex/begin/end）与内容 text。
> wps.texts.search 不索引 OMath 公式内部文本：按公式内容搜索会返回空 ranges（not found），这是预期行为而非缺陷（TC_118）；核验公式内容/位置一律用 wps.formulas.math verb=query，不要用 texts.search。
> 若报 500002 且文档被改动，检查 text 是否含未转义引号；段落索引越界会返回明确的 paragraph not found 错误。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：insert（插入公式） / query（查询公式列表）。可选值：`insert` / `query`
- `begin` (number, 可选): 区间起始位置
- `display_type` (number, 可选): 公式显示类型（WdOMathType）：0=专业格式（wdOMathDisplay，独立成行，缺省） / 1=内嵌（wdOMathInline，随文字排版）。可选值：`0` / `1`；默认值：`0`
- `end` (number, 可选): 区间结束位置
- `paragraph_index` (number, 可选): 段落索引，从 1 开始
- `text` (string, 必填): 文本内容

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

