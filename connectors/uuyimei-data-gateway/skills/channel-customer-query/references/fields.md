# 渠道客户字段参考

本文件是「渠道客户」数据集的完整字段口径，直接来自 `crm-data-gateway` 网关的 `configs/channel_customer.xml` 与 `gateway/dataset.py`。

> 返回字段名不区分大小写与下划线差异（`fnameL2` / `fname_l2` / `FNAME_L2` 等价）。过滤字段（`filters` 里 `field` 填的值）用下面的固定小写名。

## 1. 可过滤字段（filters 白名单，11 个）

> 2026-09-18 字段裁剪：录入员/跟进人/创建人/是否加顾问企微/渠道分类/深度平台/私域分类/美容院/职业/预估开发金额/会员卡类别等过滤项已随返回字段一并移除，再用会返回 `INVALID_PARAMS`。

| field | 含义 | 备注 |
|-------|------|------|
| `province` | 省份 | |
| `city` | 县市 | |
| `region` | 区域 | |
| `consultear` | 顾问姓名 | |
| `useraccount` | 顾问工号 | |
| `name` | 客户姓名 | 敏感：过滤值落审计前会脱敏 |
| `fchanneltwoname` | 三级渠道名 | 命中即视为「单渠道」，豁免默认时间 |
| `ftype` | 用户组 | |
| `cfintent` | 意向度 | |
| `tempcomdate` | 建档时间 | 日期字段，支持范围过滤 |
| `fcreatetime1` | 创建时间 | 日期字段，支持范围过滤；**仅过滤用，不在返回字段里** |

### 操作符语义

| op | 说明 |
|----|------|
| `=` `!=` `>` `<` `>=` `<=` | 常规比较 |
| `like` | 包含匹配；未显式给 `%` 时自动 `%value%` |
| `in` | 传非空列表，如 `{"field":"city","op":"in","value":["石家庄市","北京市"]}` |
| `is_null` | `value` 传 0（IS NULL）或 1（IS NOT NULL） |

日期字段（`tempcomdate`/`fcreatetime1`）的字符串值会自动解析为日期；支持 `YYYY-MM-DD`、`YYYY-MM-DD HH:MM:SS` 等格式。表达「某一天」用 `>= 当天00:00:00` 且 `< 次日00:00:00`。

## 2. 默认时间限制规则

`query_channel_customers` 与 `query_channel_customer_count` 在以下情况会**自动追加**「建档时间近 30 天」：

- filters 已含 `tempcomdate` / `fcreatetime1` → 已给时间，不注入；
- filters 已含 `fchanneltwoname`（单渠道）→ 豁免，不注入；
- 其余情况 → 注入 `tempcomdate >= 今天-30天`。

返回 `meta.default_time_filter_applied` 为 `true` 表示本次命中了默认限制。

## 3. 返回字段目录（24 个，2026-09-18 裁剪后）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 临时客户ID | 原值（内部关联键，供查聊天 `temp_id`） |
| `cusid` | 正式客户ID | 原值（关联键，供微信/企微对话按 `cus_id` 过滤） |
| `fname_l2` | 渠道客户姓名 | 🔒 SHA256 |
| `fage` | 年龄 | |
| `cfsex` | 性别 | |
| `cftelephone` | 电话 | 🔒 SHA256 |
| `bulidtypename` | 一级渠道 | |
| `fchannelonename` | 二级渠道 | |
| `fchanneltwoname` | 三级渠道 | |
| `cfintent` | 意向度 | |
| `consultear` | 顾问 | |
| `cfremark` | 备注 | |
| `tempcomdate` | 建档时间 | |
| `flastduildrecorddastr` | 最后建档时间 | |
| `fisaddv` | 是否加微 | |
| `ffaceanalysis` | 是否看脸 | |
| `province` | 省份 | |
| `city` | 县市 | |
| `region` | 区域 | |
| `rvisitcnt` | 回访次数 | |
| `rvisitnum` | 有效回访次数 | |
| `flastrvisitdate` | 最后回访时间 | |
| `cuscomdate` | 来院时间 | |
| `ftype` | 用户组 | |

> 说明：SQL 底层 `select temp.*` 会取出 150+ 列，但网关只按上表（XML 声明的输出白名单）返回这 24 个字段，未声明的敏感列（如 `cusphone`/`fqq`/`fname_l1`/`fip` 等）一律不返回。`bulidtypename`/`fchannelonename` 为服务端按 `CT_BAS_SOURCETYPE` 枚举表解析出的一/二级渠道中文名，仅随行返回、不可过滤；三级渠道名 `fchanneltwoname` 可过滤。此前的私域分类/障碍点/30天对话标记/会员卡/美容院/深度平台/初渠道/婚姻/经济能力等 37 个冗余字段已裁剪，追问这些内容时如实告知档案接口不再返回。

## 4. 聊天记录查询（query_channel_customer_chats）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | str | 二选一 | 渠道客户手机号（仅服务端解析，不返回、审计里脱敏） |
| `temp_id` | str | 二选一 | 临时客户 ID（`fid`），从档案查询结果拿到 |
| `cus_type` | int | 否 | 2=临时客户（默认），1=正式客户 |
| `begintime` / `endtime` | str | 否 | ISO 时间，缺省默认近 30 天 |
| `limit` | int | 否 | 返回条数上限（默认 100，封顶 `MAX_ROWS`） |

`phone` 与 `temp_id` 必须且只能传一个。`temp_id` 入口专为「档案里手机号已脱敏、拿不到明文」场景设计。

**返回**：`data.customers`（命中客户上下文，姓名/手机号脱敏，`fid` 原值）、`data.staff_list`（聊天记录）、`data.note`（提示）。

**查不到记录的两种常见原因**（工具会在 `data.note` 给提示）：
1. 该客户未添加顾问企微——大多数客户如此，本就无企微聊天；
2. 客户所属组织未接入聊天系统（聊天接口 HTTP 400）。

## 5. 返回信封

成功：

```json
{
  "success": true,
  "data": [ { "fid": "…原值…", "city": "石家庄市", "tempcomdate": "2026-07-27 09:01:11" } ],
  "meta": {
    "row_count": 3,
    "masked_fields": ["fname_l2", "cftelephone"],
    "fields": [ { "name": "city", "title": "县市", "is_sha256": false } ],
    "limit": 3, "offset": 0,
    "default_time_filter_applied": false
  },
  "audit": { "trace_id": "…" }
}
```

`query_channel_customer_count` 的 `data` 为 `{ "count": <总数> }`；`query_channel_customer_chats` 的 `data` 为 `{ "customers": …, "staff_list": …, "note": … }`。

---

# 正式客户数据集

> 到院成交后的**正式客户档案**（源自 CRM「客户指标查询」画面，2026-09-18 按需求从 150+ 字段裁剪到 28 个）。工具：`query_formal_customers`（明细列表，分页）/ `query_formal_customer_count`（总数，按客户ID去重）。数据桶 `company`。主链 `consultant_oustanding_rpt prt INNER JOIN ct_crm_customerinfo cus`（每客户一行，实测全库 231 万正式客户）。
>
> 与渠道客户档案的分工：渠道客户 = 到院前临时档案（渠道/意向度/回访）；正式客户 = 成交后档案（私域分类/用户组/归属医生/会员卡/专家特助/渠道建档人）。

## 1. 可过滤字段（filters 白名单，23 个）

| field | 含义 | 备注 |
|-------|------|------|
| `cusid` | 客户ID | 关联键，原值返回 |
| `consultorid` | 顾问ID | 关联键，原值返回 |
| `tempcusid` | 临时客户ID | 关联键；无渠道档案时为空 |
| `cusname` | 姓名 | 敏感：返回 SHA256，过滤值落审计同样脱敏 |
| `cfhandset` | 电话 | 敏感：同上 |
| `cussex` | 性别 | 如 女/男 |
| `cusage` | 年龄 | 数值（空按 0） |
| `birthday` | 生日 | |
| `fbodysize` | 体型 | 返回/过滤中文「偏胖/中等/偏瘦」（CRM 字典 1/2/3 服务端 decode，历史 0 值原样透传，未填为空） |
| `ismarry` | 婚姻 | |
| `provincename` | 省份 | 中文名 |
| `city` | 县市 | 中文名 |
| `regionname` | 区域 | 中文名 |
| `workname` | 职业 | 中文名 |
| `cusmanagelevel1name` | 私域一级分类 | |
| `cusmanagelevel2name` | 私域二级分类 | |
| `cusmanagelevel3name` | 私域三级分类 | |
| `consultant` | 顾问姓名 | |
| `beauname` | 专家特助 | |
| `tempconsultor` | 渠道建档人 | 即在渠道时的渠道顾问 |
| `ftypename` | 用户组 | |
| `fgroupname` | 用户组别名 | |
| `cardtype` | 会员卡类型 | 无卡客户返回 `'非会员'` |

操作符语义与渠道客户一致（`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`(默认 `%value%`)、`in`、`is_null`）。

**归属医生 `secdoc1-5` 不在白名单**：它们是外层函数列，随行返回但传入过滤会 `INVALID_PARAMS`；要按归属医生筛人，先用其它字段收敛，再在结果里本地过滤，并向用户如实说明该限制。

## 2. 默认时间限制规则

**无默认时间窗**（档案类数据，同 `customer_info`/`temp_client_info`）；`meta.default_time_filter_applied` 恒为 `false`。不传 filters 时按全库范围分页返回。

## 3. 计数去重

`COUNT(DISTINCT cusid)`（客户ID）。计数 SQL 按过滤字段**动态装配最小 JOIN**（无过滤时只 join `prt`+`cus` 两表）；等值/选择性过滤实测 0.2–12s，**非选择性前导通配 like**（如 `fgroupname like '%组%'`）count 可达 ~100s，计数请尽量用等值或 `in` 精确过滤。

## 4. 返回字段目录（28 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `cusid` | 客户ID | 原值（→ 微信/企微对话 `cus_id`、业绩大盘 `customer_id`） |
| `consultorid` | 顾问ID | 原值（→ 业绩大盘 `rec_consultant_id`） |
| `tempcusid` | 临时客户ID | 原值（→ 聊天记录 `temp_id`） |
| `cfhandset` | 电话 | 🔒 SHA256 |
| `cusname` | 姓名 | 🔒 SHA256 |
| `cussex` | 性别 | |
| `cusage` | 年龄 | |
| `birthday` | 生日 | |
| `provincename` | 省份 | |
| `city` | 县市 | |
| `regionname` | 区域 | |
| `workname` | 职业 | |
| `fbodysize` | 体型 | 返回/过滤中文「偏胖/中等/偏瘦」（CRM 字典 1/2/3 服务端 decode，历史 0 值原样透传，未填为空） |
| `ismarry` | 婚姻 | |
| `cusmanagelevel1name` | 私域一级分类 | |
| `cusmanagelevel2name` | 私域二级分类 | |
| `cusmanagelevel3name` | 私域三级分类 | |
| `consultant` | 顾问 | |
| `ftypename` | 用户组 | |
| `fgroupname` | 用户组别名 | |
| `secdoc1` | 整形归属医生 | |
| `secdoc2` | 皮肤归属医生 | |
| `secdoc3` | 口腔归属医生 | |
| `secdoc4` | 无创归属医生 | |
| `secdoc5` | 中医归属医生 | |
| `cardtype` | 会员卡类型 | |
| `beauname` | 专家特助 | |
| `tempconsultor` | 渠道建档人（渠道时的渠道顾问） | |

> 说明：消费/治疗明细、RFM 标签、企微绑定、科室消费、障碍点等 130+ 冗余字段已裁剪，追问这些内容时如实告知档案接口不再返回。归属医生 `secdoc1-5` 因 `V_CT_CRM_BELONGSECDATA` 视图未授权给网关账号，改由授权函数 `Get_secBelongDocOrHelprOrg` 逐科取医生姓名（无归属时为 NULL）；服务助理/医生ID 暂无法提供。`cfhandset` 已脱敏，对话工具的 `phone` 过滤需明文手机号，跨工具链路请改用 `cusid`(cus_id)/`tempcusid`(temp_id)。

## 5. 返回信封

成功：

```json
{
  "success": true,
  "data": [ { "cusid": "…原值…", "cusname": "…sha256…", "cardtype": "银卡", "secdoc2": "罗玉燕" } ],
  "meta": {
    "row_count": 3,
    "masked_fields": ["cusname", "cfhandset"],
    "fields": [ { "name": "cardtype", "title": "会员卡类型", "is_sha256": false } ],
    "limit": 3, "offset": 0,
    "default_time_filter_applied": false
  },
  "audit": { "trace_id": "…" }
}
```

`query_formal_customer_count` 的 `data` 为 `{ "count": <总数> }`。

---

# 客户RFM指标数据集

> 每客户一行的**RFM 价值快照**（源自 CRM「客户RFM指标查询」画面，2026-09-20 按需求从 90+ 字段裁剪到 19 个）。工具：`query_customer_rfm`（明细列表，分页）/ `query_customer_rfm_count`（总数，按客户ID去重）。数据桶 `company`。主链 `T_Stats_Custsalesrfm t INNER JOIN ct_crm_customerinfo cus`，仅按 `firstchargedate` 过滤时追加 `LEFT JOIN consultant_oustanding_rpt rpt`；实测全库 1,635,985 行 = 去重客户数（零扇出，每客户恰好一行）。
>
> 与正式客户档案的分工：正式客户 = 档案属性（私域分类/用户组/归属医生/会员卡/专家特助）；RFM = 消费行为价值指标（星级/评分/到院间隔/保留周期/消费次数/转介绍/等级积分）。

## 1. 可过滤字段（filters 白名单，21 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fcustid` | 客户ID | 关联键，原值返回 |
| `cfname` | 客户姓名 | 敏感：返回 SHA256，过滤值落审计同样脱敏 |
| `cfhandset` | 电话 | 敏感：同上 |
| `fcustoverallgrade` | 客户价值级别（星级） | 数值 1–5；实测分布 1星84.4万 / 2星59.2万 / 3星14.0万 / 4星4.7万 / 5星1.3万 |
| `fcustoverallvalue` | 客户价值总评分 | 数值 |
| `firstchargedate` | 首次消费日 | 日期；来自 rpt 表，覆盖率 98%（约 3 万客户为空） |
| `fqbillfirstdate` | 首次到院日期 | 日期 |
| `fqbilllastdate` | 最近到院日期 | 日期 |
| `fqbilllastdays` | 距最近到院间隔天数 | 数值 |
| `fqbilllastdaysvalue` | 间隔分值 | 数值 1–5 |
| `fqbilllastdaysstr` | 最近到院标签 | ⚠️ 实际是 `fqbilllastdaysvalue` 的别名（数值 1–5），非文字标签 |
| `flifespan` | 顾客保留周期 | 数值（天） |
| `flifespanvalue` | 保留周期分值 | 数值 1–5 |
| `fqbillcnt` | 总消费次数 | 数值 |
| `freferralnumber` | 顾客转介绍人数 | 数值 |
| `freferralnumbervalue` | 转介绍分值 | 数值 1–5 |
| `freferralnumberstr` | 转介绍积极度标签 | ⚠️ 实际是 `freferralnumbervalue` 的别名（数值 1–5），非文字标签 |
| `fmttlamt` | 等级积分（累计消费金额） | 数值 |
| `fmttlamtvalue` | 总消费能力分值 | 数值 1–5 |
| `fmttlamtstr` | 总消费能力标签 | ⚠️ 实际是 `fmttlamtvalue` 的别名（数值 1–5），非文字标签 |
| `freferralamt` | 转介绍客户消费金额 | 数值 |

操作符语义与其它数据集一致（`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`(默认 `%value%`)、`in`、`is_null`）。日期字段（`firstchargedate`/`fqbillfirstdate`/`fqbilllastdate`）传字符串（如 `"2026-01-01"`）服务端自动转日期绑定。

**「标签/str」列的真实语义**：CRM 前端把这些分值列渲染成文字标签（如「积极/一般/沉睡」），但网关返回的是原始分值数字，且映射字典不在库里——转述时直接说分值，不要编造文字标签映射。

## 2. 默认时间限制规则

**无默认时间窗**（快照类数据）；`meta.default_time_filter_applied` 恒为 `false`。不传 filters 时按全库范围分页返回。

## 3. 计数去重

`COUNT(DISTINCT fcustid)`（客户ID）。计数 SQL 按过滤字段**动态装配最小 JOIN**：始终带 `t+cus`（保证与明细口径一致），仅当过滤 `firstchargedate` 时追加 `rpt` 左连。实测（dev 全库最坏情况）：无过滤 count 163 万行 ~6s；`fcustoverallgrade=5` → 12,528，~1–2s；`firstchargedate>='2026-01-01'` → 77,900，~5s；明细列表 0.1–0.2s。

## 4. 返回字段目录（19 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fcustid` | 客户ID | 原值（= 正式客户 `cusid` = 对话 `cus_id` = 业绩大盘 `customer_id`） |
| `cfname` | 客户姓名 | 🔒 SHA256 |
| `cfhandset` | 电话 | 🔒 SHA256 |
| `fcustoverallgrade` | 客户价值级别（星级 1-5） | |
| `fcustoverallvalue` | 客户价值总评分 | |
| `firstchargedate` | 首次消费日 | |
| `fqbillfirstdate` | 首次到院日期 | |
| `fqbilllastdate` | 最近到院日期 | |
| `fqbilllastdays` | 最近到院距近间隔天数 | |
| `fqbilllastdaysvalue` | 间隔分值（1-5） | |
| `fqbilllastdaysstr` | 最近到院标签（=间隔分值） | |
| `flifespan` | 顾客保留周期（天） | |
| `flifespanvalue` | 保留周期分值（1-5） | |
| `fqbillcnt` | 总消费次数 | |
| `freferralnumber` | 顾客转介绍人数 | |
| `freferralnumberstr` | 转介绍积极度标签（=转介绍分值） | |
| `fmttlamt` | 等级积分（累计消费金额） | |
| `fmttlamtstr` | 总消费能力（=消费能力分值） | |
| `freferralamt` | 转介绍客户消费金额 | |

> 说明：原画面 90+ 字段中的消费明细分布、卡项/项目分类、渠道/网电标记、生日年龄段、顾问维度等已裁剪，追问这些内容时如实告知 RFM 接口不再返回（部分维度可转 `query_formal_customers` 或业绩大盘数据集）。

## 5. 返回信封

成功：

```json
{
  "success": true,
  "data": [ { "fcustid": "…原值…", "cfname": "…sha256…", "fcustoverallgrade": 5, "fqbilllastdays": 120 } ],
  "meta": {
    "row_count": 2,
    "masked_fields": ["cfname", "cfhandset"],
    "fields": [ { "name": "fcustoverallgrade", "title": "客户价值级别", "is_sha256": false } ],
    "limit": 2, "offset": 0,
    "default_time_filter_applied": false
  },
  "audit": { "trace_id": "…" }
}
```

`query_customer_rfm_count` 的 `data` 为 `{ "count": <总数> }`。

---

# 渠道客户到院/接诊数据集

本部分覆盖 `channel_customer_visit` 数据集（工具 `query_channel_customer_visit` / `query_channel_customer_visit_count`），主表 `ct_rec_crmreceive`（接诊记录，约 695 万行），inner join `ct_crm_customerinfo`（正式客户）。参考视图 `Come_examine_msg_view`（2024-12-18）裁剪版。

> **2026-09-20 字段裁剪**：返回字段 95→**15**（关联键 fid/cusid/tempid + 姓名、接诊顾问、新老客、接诊年龄、是否二次、接待时间、医助描述、客户意向、未成交处理、科室、二级分诊、主诊医生），过滤白名单 32→**15**。原「主诉/是否成交/渠道/企微/会员卡/画像/协诊开单分诊导诊人员/首咨重咨/状态/时间(分诊/创建)」等 80 个字段不再返回也不可过滤（传入 INVALID_PARAMS）。JOIN 37→7：`crm + cus(inner) + tempcus(电话→tempid) + ar(t_app_registration→fintention) + comtype(fsecondtype→二级分诊名) + t(接诊顾问) + c(主诊医生)`；30 天窗口实测 45,513 行 = distinct crm.fid **零扇出**（tempcus/ar 均 1:0/1:1）。`f_getcusttag`/`get_ContextList`/`isbind_*` 标量函数与计费/RFM/企微/回访等重 JOIN 全部移除：近 30 天 count **43.8s→1.5s**、列表 ~0.25s（裁剪前 0.2–0.9s）。
>
> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，15 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fid` | 接诊ID | 关联/计数键，原值 |
| `cusid` | 正式客户ID | 原值 → 微信/企微对话 `cus_id`、业绩大盘 `customer_id` |
| `tempid` | 临时客户ID | 原值 → 聊天记录 `temp_id` |
| `cusname` | 姓名 | 敏感：返回 SHA256，过滤值落审计同样脱敏 |
| `cfreceptiontime` | 接待时间 | 日期（默认时间窗注入列）；字符串自动转绑定 |
| `consultator` | 接诊顾问 | |
| `doctor` | 主诊医生 | |
| `fisnewcustomer` | 新老客 | `"1"`新客/`"0"`老客 |
| `fisrecsecond` | 是否二次 | `"1"`/`"0"` |
| `cfsamplingtype` | 接诊年龄 | 数值 |
| `fsection` | 科室 | ⚠️ 编码列：1整形/2皮肤/3口腔/4无创/5中医（与大盘 rec_section_code 一致），按编码过滤、原样转述 |
| `twoname` | 二级分诊 | t_pro_comtype 中文名，like |
| `fcuredesc` | 医助描述 | 长文本，like |
| `fintention` | 客户意向 | 来自挂号表(ar)，覆盖率低、多为空 |
| `isdeal` | 未成交处理 | 1=有登记处理项/原因（t_rec_notdealitem/notdealreason exists），0=无 |

操作符语义与其它数据集一致（`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`(默认 `%value%`)、`in`、`is_null`）。

## 2. 默认时间限制规则

filters 未含 `cfreceptiontime` 时自动注入「接待时间近 30 天」（渠道类豁免字段已随裁剪下线）。`meta.default_time_filter_applied` 标注是否命中。表达「某一天」用 `>= 当天00:00:00` 且 `< 次日00:00:00`。

## 3. 计数去重

`query_channel_customer_visit_count` 用 `COUNT(DISTINCT fid)`（接诊 ID）计数；主 SQL 零扇出，与列表行数口径一致。实测（dev 全库 30 天窗）：count 1.5s、列表首页 0.25s。

## 4. 返回字段目录（15 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 接诊ID | 原值 |
| `cusid` | 正式客户ID | 原值（→ 对话 `cus_id`） |
| `tempid` | 临时客户ID | 原值（→ 聊天记录 `temp_id`） |
| `cusname` | 姓名 | 🔒 SHA256 |
| `consultator` | 接诊顾问 | |
| `fisnewcustomer` | 新老客 | |
| `cfsamplingtype` | 接诊年龄 | |
| `fisrecsecond` | 是否二次 | |
| `cfreceptiontime` | 接待时间 | |
| `fcuredesc` | 医助描述 | |
| `fintention` | 客户意向 | |
| `isdeal` | 未成交处理 | 0/1 标记 |
| `fsection` | 科室 | 编码 1-5 |
| `twoname` | 二级分诊 | |
| `doctor` | 主诊医生 | |

> 原 95 字段中的电话/尊称/地址（🔒）、开单状态、渠道四类、RFM/活跃度/等级积分、企微添加、主诉、面诊/宣贯/咨询总结、AI 分析画像、套餐、会员、协诊/导诊/分诊/开单人员等已全部下线；追问时如实告知本接口只返回精简 15 字段（电话链路改走正式客户 `cusid`→对话工具，成交判断无直接字段、可用 `isdeal` 反向参考）。

## 5. 返回信封

与其它数据集一致：`query_channel_customer_visit` 返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`default_time_filter_applied`) + `audit.trace_id`；`query_channel_customer_visit_count` 返回 `data.count`。`masked_fields` 仅 `cusname`。

---

# 渠道客户新客线索数据集

本部分覆盖 `channel_lead` 数据集（工具 `query_channel_leads` / `query_channel_lead_count`），主表 `t_crm_cus_third_part_submit`（第三方/转诊平台派单线索），inner join `ct_crm_temp_client_info`（临时客户，限定"已建渠道档案"人口，与裁剪前一致）。SQL 内固定过滤 `tps.ftype in ('2','3')` 并按 `tps.fsubmittime desc` 排序。

> **2026-09-20 字段裁剪**：按需求从 49 个返回字段精简到 **10 个**（必要关联键 + 来源/一二级三级渠道/姓名/电话/派单时间/备注），过滤白名单 28→8。原「是否来院/处理状态/线索等级/分值/分诊/人员/地域/企微/产品/建档时间」等跟踪字段不再返回也不再可过滤；需要它们请改用 `query_lead_submit`（见下一章节）。JOIN 21→4，同时消除原 `cus`/`pre`/`s`/`g` 左连的 fid 扇出（实测 676,377 条线索原查出 676,403 行，现每线索恰好一行）。
>
> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，8 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fsubmittimestr` | 派单时间 | 日期字段，底层按 `tps.fsubmittime` 过滤，字符串值自动转日期绑定 |
| `fchannelname` | 线索三级渠道名 | 命中即视为「按渠道限定」，豁免默认时间窗 |
| `fchannel1name` | 线索一级渠道名 | 服务端按 `CT_BAS_SOURCETYPE` 解析；命中同样豁免默认时间窗 |
| `fchannel2name` | 线索二级渠道名 | 同上（二级带 fparentid 消歧） |
| `fcusname` | 姓名 | 敏感：过滤值落审计前脱敏 |
| `fmobile` | 电话 | 敏感：过滤值落审计前脱敏 |
| `submittype` | 线索来源 | 1/2 归并为 1（`'1'`=API/二维码合并值、`'3'`=CRM 等） |
| `ftempcusid` | 渠道客户ID | 关联键，原值 |

### 操作符语义

与档案/到院一致：`=` `!=` `>` `<` `>=` `<=`、`like`(默认 `%value%`)、`in`(传非空列表)、`is_null`(传 0/1)。日期字段传字符串自动解析；表达「某一天」用 `>= 当天00:00:00` 且 `< 次日00:00:00`。

## 2. 默认时间限制规则

`query_channel_leads` / `_count` 在以下情况会**自动追加**「派单时间近 30 天」：

- filters 已含 `fsubmittimestr` → 已给时间，不注入；
- filters 已含 `fchannelname` / `fchannel1name` / `fchannel2name` 任一 → 视为按渠道限定，豁免，不注入；
- 其余情况 → 注入 `fsubmittimestr >= 今天-30天`。

返回 `meta.default_time_filter_applied` 为 `true` 表示本次命中了默认限制。

## 3. 计数去重

`query_channel_lead_count` 用 `COUNT(DISTINCT fid)`（`fid` = 线索 ID = `tps.fid`，SQL 首列）计数。裁剪后主 SQL 零扇出，count 与列表行数口径一致；计数一律走 `_count` 工具，不要数列表行。实测（dev 全库）：全库 count ~14s（裁剪前 ~20s）、近 30 天窗 ~2s、列表 ~1.7s。

## 4. 返回字段目录（10 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 线索ID | 原值（本数据集计数/去重键） |
| `ftempcusid` | 渠道客户ID | 原值（→ 渠道客户 `fid` / 聊天记录 `temp_id`） |
| `submittype` | 线索来源 | |
| `fchannel1name` | 线索一级渠道 | 服务端解析中文名 |
| `fchannel2name` | 线索二级渠道 | 服务端解析中文名 |
| `fchannelname` | 线索三级渠道 | |
| `fcusname` | 姓名 | 🔒 SHA256 |
| `fmobile` | 电话 | 🔒 SHA256 |
| `fsubmittimestr` | 派单时间 | |
| `fremark` | 线索备注 | |

> 一/二级渠道代码列（`fchannel1`/`fchannel2`）只参与服务端中文名解析，不再返回（与渠道客户档案一致）。原 49 字段中的跟踪/分诊/人员/地域/企微/产品等列已全部下线；`fcontrolunitid` 为租户辅助列，不返回。

## 5. 返回信封

与其它数据集一致：`query_channel_leads` 返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`default_time_filter_applied`) + `audit.trace_id`；`query_channel_lead_count` 返回 `data.count`。

---


# 线索提交记录数据集（线索查询）

本部分覆盖 `lead_submit` 数据集（工具 `query_lead_submit` / `query_lead_submit_count`），主表 `t_crm_cus_third_part_submit`（转诊平台提交客户资料记录）**单表直查**，覆盖全部客户类型（`ftype` 1老客 2新客 3未建档），按 `t.fcreatetime desc` 排序。join 表仅做渠道/人员/省市/产品/派单方式的可读名称解析。

**与「新客线索」（`channel_lead`）的区别**：`channel_lead` 限新客/未建档（`ftype in ('2','3')`）且须已建渠道客户档案（inner join 临时客户），2026-09-20 裁剪后只返回**精简档案视角**（来源/一二级三级渠道/姓名电话/派单时间/备注）；`lead_submit` 是**全类型原始提交记录**（含老客），带咨询内容/多重需求/分诊备注/处理状态/派单方式等更全字段——问「未处理/老客线索/是否处理」一律用 `lead_submit`。

> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，32 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fcreatetimestr` | 创建(提交)时间 | 日期字段，底层按 `t.fcreatetime` 过滤 |
| `fsubmittimestr` | 派单时间 | 日期字段，底层按 `t.fsubmittime` |
| `fallocatetimestr` | 分诊时间 | 日期字段，底层按 `t.fallocatetime` |
| `fdepthtimestr` | 深度标记时间 | 日期字段，底层按 `t.fdepthtime` |
| `fchannelname` | 转诊三级渠道名 | 命中即视为「单渠道」，豁免默认时间 |
| `fchannel1name` | 转诊一级渠道名 | |
| `fchannel2name` | 转诊二级渠道名 | |
| `fchannel` | 转诊三级渠道ID | |
| `fcusname` | 客户姓名 | 敏感：过滤值落审计前脱敏 |
| `fmobile` | 手机号码 | 敏感：过滤值落审计前脱敏 |
| `fmoble2` | 辅助号码 | 敏感（列名拼写即 `FMOBLE2`）；过滤值落审计前脱敏 |
| `fgender` | 性别 | |
| `fage` | 年龄 | |
| `ftype` | 客户类型 | 1老客 2新客 3未建档 |
| `fstatue` | 状态 | 1未处理 2已处理 |
| `submittype` | 派单方式 | 1API 2二维码 3CRM 4巨量本地推线索 5巨量飞鱼线索 6小红书私信 7云晰 8小红书小程序 9商城小程序 10优居营客 11快商通 12美团 |
| `fdepth` | 是否深度 | 1是 0否 |
| `funitname` | 单位名称 | |
| `fcusid` | 正式客户ID | |
| `ftempcusid` | 临时客户ID | |
| `fthirdpartycusid` | 第三方客户ID | |
| `fsourceid` | 源ID | 巨量渠道有值 |
| `org_id` | 医院组织ID | 映射 `t.fcontrolunitid` |
| `fassignpername` | 派单人 | |
| `fallocatepername` | 分诊人 | |
| `ffollowername` | 跟进人 | |
| `fdepthusername` | 深度标记人 | |
| `fcreateperson` | 第三方派单人 | |
| `provincename` | 省 | |
| `cityname` | 城市/地址 | |
| `pty1name` | 分诊产品一级 | |
| `pty2name` | 分诊产品二级 | |

### 操作符语义

与其它数据集一致：`=` `!=` `>` `<` `>=` `<=`、`like`(默认 `%value%`)、`in`(传非空列表)、`is_null`(传 0/1)。标志位/枚举字段（`ftype`/`fstatue`/`submittype`/`fdepth`）用字符串比较（如 `"1"`）。日期字段的字符串值自动解析；表达「某一天」用 `>= 当天00:00:00` 且 `< 次日00:00:00`。

## 2. 默认时间限制规则

`query_lead_submit` / `_count` 在以下情况会**自动追加**「创建时间近 30 天」：

- filters 已含 `fcreatetimestr` / `fsubmittimestr` / `fallocatetimestr` / `fdepthtimestr` → 已给时间，不注入；
- filters 已含 `fchannelname`（单渠道）→ 豁免，不注入；
- 其余情况 → 注入 `fcreatetimestr >= 今天-30天`。

返回 `meta.default_time_filter_applied` 为 `true` 表示本次命中了默认限制。

## 3. 计数去重

`query_lead_submit_count` 用 `COUNT(DISTINCT fid)`（`fid` = 线索记录 ID，SQL 首列）计数，规避名称解析 left join 可能的扇出；列表工具不强行 DISTINCT，计数一律走 `_count` 工具。

## 4. 返回字段目录（37 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 线索记录ID | |
| `ftype` | 客户类型(1老客2新客3未建档) | |
| `fchannelname` | 转诊三级渠道 | |
| `fchannel1name` | 转诊一级渠道 | |
| `fchannel2name` | 转诊二级渠道 | |
| `funitname` | 单位名称 | |
| `fcusname` | 客户姓名 | 🔒 SHA256 |
| `fmobile` | 手机号码 | 🔒 SHA256 |
| `fmoble2` | 辅助号码 | 🔒 SHA256 |
| `fgender` | 性别 | |
| `fage` | 年龄 | |
| `provincename` | 省 | |
| `cityname` | 城市/地址 | |
| `fremark` | 咨询内容 | |
| `fmultidemand` | 多重需求 | |
| `fcreateperson` | 第三方派单人 | |
| `fcreatetimestr` | 创建(提交)时间 | |
| `fsubmittimestr` | 派单时间 | |
| `submittype` | 派单方式代码 | |
| `submittypename` | 派单方式（中文，服务端 decode） | |
| `fcusid` | 正式客户ID | |
| `ftempcusid` | 临时客户ID | |
| `fthirdpartycusid` | 第三方客户ID | |
| `fsourceid` | 源ID(巨量有值) | |
| `ffilepath` | 附件地址 | |
| `fstatue` | 状态(1未处理2已处理) | |
| `pty1name` | 分诊产品一级 | |
| `pty2name` | 分诊产品二级 | |
| `fassignpername` | 派单人 | |
| `fallocatepername` | 分诊人 | |
| `fallocatetimestr` | 分诊时间 | |
| `fallocatemark` | 分诊备注 | |
| `ffollowername` | 跟进人 | |
| `fdepth` | 是否深度(1是0否) | |
| `fdepthusername` | 深度标记人 | |
| `fdepthtimestr` | 深度标记时间 | |
| `frevisitrequire` | 回访要求 | |

> SQL 底层另 select 出 `fcontrolunitid`/`fchannel`/`fchannel1`/`fchannel2` 代码、`fprovince`、`ftwoprotypeid`、`fassignperid`/`fallocateperid`/`ffollowerid` 等原始 ID 列，网关只按上表 XML 白名单返回 37 个字段，未声明列一律不返回。`fchannel1name`/`fchannel2name` 为服务端按 `CT_BAS_SOURCETYPE` 解析出的一、二级渠道中文名（一级缺失时回退三级渠道的归属一级），仅随行返回、按名称过滤。

## 5. 返回信封

与其它数据集一致：`query_lead_submit` 返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`default_time_filter_applied`) + `audit.trace_id`；`query_lead_submit_count` 返回 `data.count`。

---

# 渠道客户回访数据集

本部分覆盖 `channel_customer_revisit` 数据集（工具 `query_channel_customer_revisit` / `query_channel_customer_revisit_count`），主表 `ct_ret_returnvisit_temp_plan`（回访计划表，约 2695 万行、fid 唯一）。历史表 `ct_ret_returnvisit_hist` 已停更（最新止于 2023-01），**只查计划活表**。

> **2026-09-20 字段裁剪**：按需求从 128 个返回字段精简到 **12 个**——关联键 `fid`/`cusid`/`tempcusid` + 回访名称、上报时间、实际执行时间、任务等级、姓名、回访目的、拨打结果、回访方式、回访反馈。过滤白名单 42→12。原「执行人/部门/用户组/申请人/审核人/回访状态/是否到场/是否有效/按期执行/科室/渠道/企微/会员卡/RFM/AI 外呼/障碍点/顾问」等跟踪字段不再返回也不可过滤（传入 INVALID_PARAMS）。JOIN 40→4：`rvp` + `cus`(inner，姓名/关联键，兼「已建渠道档案」人口口径) + `be`(t_ret_basesetentry→回访名称) + `fb`(T_RET_VisitPlanFeedbackTemp→回访反馈文本)；原 `c`(电话匹配正式客户) 左连实测扇出 ~5k 行，随裁剪消除，`cusinfoid` 不再返回（正式客户链路改走 `tempcusid` → `query_formal_customers` 的 tempcusid 过滤）。
>
> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，12 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fid` | 回访记录ID | 关联/计数键，原值 |
| `cusid` | 临时客户ID | 与 `tempcusid` 同值（历史兼容名） |
| `tempcusid` | 渠道客户ID | 原值 → 渠道客户档案 `fid` / 聊天记录 `temp_id` |
| `cusname` | 姓名 | 敏感：返回 SHA256，过滤值落审计同样脱敏 |
| `fretvname` | 回访名称 | like；命中时计数动态补 `be` 表 |
| `createtime` | 上报时间 | 日期（主表无独立上报列，取计划上报/创建时间 `rvp.fcreatetime`） |
| `revisittime` | 实际执行时间 | 日期；默认时间窗注入列（约 74% 计划已执行、其余为空） |
| `jobgrade` | 任务等级 | 数值 1-5（实测分布：3 级 1328 万、1 级 748 万、4 级 236 万、2 级 117 万、5 级 222 万） |
| `purpose` | 回访目的 | 文本，like |
| `doresult` | 拨打结果 | ⚠️ 编码 1-6（文字字典不在库，原样返回，别编造标签） |
| `frevisitway` | 回访方式 | ⚠️ 编码 1-8（同上） |
| `ffeedbackname` | 回访反馈 | 文本，like；命中时计数动态补 `fb` 表 |

### 操作符语义

与其它数据集一致：`=` `!=` `>` `<` `>=` `<=`、`like`(默认 `%value%`)、`in`(传非空列表)、`is_null`(传 0/1)。日期字段（`createtime`/`revisittime`）的字符串值自动解析；表达「某一天」用 `>= 当天00:00:00` 且 `< 次日00:00:00`。

## 2. 默认时间限制规则

`query_channel_customer_revisit` / `_count` 在 filters **未含 `revisittime`/`createtime` 任一**时，自动注入 `revisittime >= 今天-30天`（渠道类豁免字段已随跟踪维度下线）。返回 `meta.default_time_filter_applied` 为 `true` 表示本次命中了默认限制。源表近 2700 万行，务必依赖此限制避免全表扫描。

## 3. 计数去重

`query_channel_customer_revisit_count` 用 `COUNT(DISTINCT fid)` 计数；计数 SQL 由 `COUNT_SQL_BUILDERS` 动态装配最小 JOIN（恒带 `rvp+cus`，仅过滤 `fretvname`/`ffeedbackname` 时补 `be`/`fb`）。主表 fid 唯一 + 裁剪后零扇出，count 与列表行数口径一致。实测（dev 全库）：近 30 天 count ~13s（30+ JOIN 时代 1–2 分钟）、列表首页 ~0.2s。

## 4. 返回字段目录（12 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 回访记录ID | 原值 |
| `cusid` | 临时客户ID | 原值（=tempcusid） |
| `tempcusid` | 渠道客户ID | 原值（→ 渠道客户档案 `fid`、聊天记录 `temp_id`） |
| `fretvname` | 回访名称 | |
| `createtime` | 上报时间 | |
| `revisittime` | 实际执行时间 | |
| `jobgrade` | 任务等级 | 1-5 |
| `cusname` | 姓名 | 🔒 SHA256 |
| `purpose` | 回访目的 | |
| `doresult` | 拨打结果 | 编码 1-6 |
| `frevisitway` | 回访方式 | 编码 1-8 |
| `ffeedbackname` | 回访反馈 | |

> 原 128 字段中的执行人/部门/用户组、状态/到场/有效性、审核/停止链路、渠道/地域/会员/RFM、AI 外呼、言迹总结、障碍点、顾问 con1-4、企微绑定、回访统计等全部下线；追问时如实告知本接口只返回计划+执行核心 12 字段。

## 5. 返回信封

与其它数据集一致：`query_channel_customer_revisit` 返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`default_time_filter_applied`) + `audit.trace_id`；`query_channel_customer_revisit_count` 返回 `data.count`。`fields` 里 `is_sha256=true` 的字段仅 `cusname`（电话 `custel` 已随裁剪下线）。

---

# 客户投诉数据集

本部分覆盖 `complaint` 数据集（工具 `query_complaints` / `query_complaint_count`），主表 `ct_cha_complaint`。2026-09-20 新增。

> **状态**：四张底表已于 2026-09-20 GRANT SELECT 并全量冒烟通过（handle 外键 FCOMPLAINTID、等级/类型字典 GUID join、租户列 fcontrolunitid 均与推断一致）。全表 17,221 条，挂正式/临时档案的 **15,914 条**为接口人口（fcustype 1=15,258 / 2=656）；约 1,300 条无档案关联的投诉不在接口内。默认按投诉日期倒序。
>
> **双客户类型支持**：参考画面为「注册客户 UNION 渠道临时客户」双分支；网关做**单扫等价改写**——custom 按 `fcusid` LEFT JOIN、tcus 按 `ftempcusid` LEFT JOIN，命中其一才输出，姓名/电话 coalesce，`fcustype` 标记 1=已注册 / 2=渠道临时。一条投诉同时挂两类档案时只出一行（归入已注册），避免 UNION 双分支重复行。处理结果/处理日期取 `ct_cha_complainthandle` **最新一条**（max fcreatetime）。

## 1. 可过滤字段（filters 白名单，15 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fid` | 投诉ID | 关联/计数键 |
| `fcusid` | 正式客户ID | → 正式客户档案 cusid |
| `ftempcusid` | 渠道客户ID | → 渠道客户档案 fid |
| `fcustype` | 客户类型 | 1=已注册 2=渠道临时 |
| `fcusname` | 投诉人姓名 | 敏感：返回 SHA256，过滤值落审计脱敏 |
| `fcftelephone` | 投诉人电话 | 敏感：同上 |
| `ftypename` | 投诉类型 | 来自 complainttype 字典表 |
| `flevelname` | 投诉等级 | 来自 complaintlevel 字典表 |
| `fcomplainttime` | 投诉日期 | 日期范围，字符串自动转绑定 |
| `fcometype` | 投诉来源 | ⚠️ 编码列，文字字典在应用层（Dozer），原样返回 |
| `fdescription` | 描述 | 自由文本，like |
| `fresults` | 处理结果 | 最新 handle 记录，like |
| `fstatus` | 状态 | 1=处理中 2=已关闭 |
| `fcategory` | 投诉类别 | |

## 2. 默认时间限制 / 计数 / 脱敏

**无默认时间窗**。计数 `COUNT(DISTINCT fid)`。脱敏：`fcusname`/`fcftelephone`（SHA256）；`fdescription`/`fresults` 自由文本可能内嵌身份信息——**转述只概括、禁止复述姓名电话**。fcometype/fstatus 编码列别编造文字含义。多类型投诉聚合（fcometype='3' 画面的 WM_CONCAT）所用关系表本库不存在，类型名按单值 ftype 关联字典（部分平台投诉类型为空属正常）。

## 3. 返回字段目录（15 个）

`fid`(投诉ID) / `fcusid`(正式客户ID) / `ftempcusid`(渠道客户ID) / `fcustype`(客户类型 1/2) / `fcusname`(姓名🔒) / `fcftelephone`(电话🔒) / `ftypename`(投诉类型) / `flevelname`(投诉等级) / `fcomplainttime`(投诉日期) / `fcometype`(投诉来源·编码) / `fdescription`(描述) / `fresults`(处理结果) / `fhandlertime`(处理日期) / `fstatus`(状态编码) / `fcategory`(投诉类别)。

---

# 电话黑名单数据集

本部分覆盖 `blacklist` 数据集（工具 `query_blacklist` / `query_blacklist_count`），单表直查 `t_msg_blacktellist`（2026-09-20 实测 150,857 行 / 150,063 去重电话 / 17 组织）。与接诊数据集 `is_black` 同源。

## 1. 可过滤字段（filters 白名单，5 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fid` | 黑名单记录ID | 关联/计数键 |
| `ftelphone` | 电话 | 🔒 返回 SHA256；**过滤传明文精确值**（=或 like），审计值同样脱敏 |
| `fblacktype` | 拉黑类别 | ⚠️ 编码 1/2/3/4/空，文字字典在应用层，原样返回 |
| `fremark` | 拉黑原因/备注 | 自由文本 like（真实原因主要看这里，如「要求不要电话骚扰」「更换机主」） |
| `fcreatetime` | 拉黑时间 | 日期范围，字符串自动转绑定 |

## 2. 返回字段目录（5 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fid` | 黑名单记录ID | 原值 |
| `ftelphone` | 电话 | 🔒 SHA256（底表明文，网关返回前脱敏） |
| `fblacktype` | 拉黑类别 | 编码 |
| `fremark` | 拉黑原因/备注 | 自由文本⚠️可能内嵌姓名电话 |
| `fcreatetime` | 拉黑时间 | |

> fnumber/fname_l1~l3/fdescription 列实测全空，不返回。判定「号码是否在黑名单」：按明文电话 `=` 过滤，`row_count>0` 即在名单内。无默认时间窗；计数 `COUNT(DISTINCT fid)`（全量 0.2s）。

---

# 客户需求数据集

本部分覆盖 `cus_request` 数据集（工具 `query_customer_requests` / `query_customer_request_count`），主表 `ct_bas_cusrequest`（一客户多需求；2026-09-21 授权当日实测上线）。全表 290 万行，服务端固定剔除软删 `isdelete='0'`，有效人口 **1,906,213** 条；按创建时间倒序。

> **默认时间窗**：大表保护——未显式给时间时自动注入「创建时间 `faddtime` 近 30 天」（`meta.default_time_filter_applied` 标注）；查历史全量请显式传宽松的 `faddtime >=` 范围豁免。无敏感返回列（不含姓名/电话，客户身份经关联键串其他数据集）。

## 1. 可过滤字段（filters 白名单，14 个）

| field | 含义 | 备注 |
|-------|------|------|
| `fid` | 需求ID | 关联/计数键 |
| `cfcusid` | 正式客户ID | → 正式客户档案 cusid |
| `ftempcusid` | 渠道客户ID | → 渠道客户档案 fid |
| `firsttypename` | 一级类别 | 取专名列 CFREQFIRSTTYPENAME（fname_l2 实测全空）；源值可能带首尾空格，like 用短词 |
| `secondtypename` | 二级类别 | CFSECONDTYPENAME |
| `fisprimary` | 主销售线索 | '1'=主需求（实测 2.5 万条）/'0'/空 |
| `cfflag` | 解决状态 | 0=未解决 1=解决 |
| `cfrequeststate` | 刚需状态 | 0=非刚需 1=刚需 |
| `cfcityquestion` | 地区问题 | 1=本市 2=本省 3=外省 |
| `cftimequestion` | 时间问题 | 1=都有时间 2=周内没时间 3=其它 |
| `faddtime` | 创建时间 | 日期范围（自动转绑定）；默认时间窗注入列 |
| `fresolvetime` | 解决时间 | 日期范围 |
| `resolvername` | 解决人 | t_bd_person 姓名，like（FDOWNBILLPERSONID 实测 100% 命中） |
| `resolvedays` | 解决周期(天) | 数值比较（如 `{"op":">","value":30}`）；=解决时间-创建时间，未解决为空 |

### 操作符语义

与其它数据集一致。日期字段字符串自动转绑定。

## 2. 返回字段目录（16 个）

上表 14 个过滤字段全量返回，另随行返回 `cfworryquestion1`/`cfworryquestion2`（担心问题一/二，小整数枚举 **0-4**，文字字典在 CRM 前端配置——原样返回值，别编造含义）。`fid`/`cfcusid`/`ftempcusid` 原值。无脱敏列。

## 3. 计数与性能

`COUNT(DISTINCT fid)`。实测（dev 全库 2026-09-21）：列表 0.3s；近 30 天 count 0.7s（走 (FCONTROLUNITID, FADDTIME) 复合索引）；显式豁免窗的全量 count（190 万）可跑、耗时略增属正常。

---

# 微信 / 企微对话数据集

本部分覆盖两个聊天对话统计数据集：`wechat_dialogue`（工具 `query_wechat_dialogue` / `query_wechat_dialogue_count`，个人微信/云客）与 `wecom_dialogue`（工具 `query_wecom_dialogue` / `query_wecom_dialogue_count`，企业微信）。两者都从正式客户档案出发，按手机号/客户ID/姓名过滤，返回「绑定关系 + 对话统计」，**不含聊天内容**。

> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，各 3 个）

两个数据集的 `filters` 白名单相同：

| field | 含义 | wechat 底层列 | wecom 底层列 |
|-------|------|---------------|--------------|
| `phone` | 手机号（精确匹配） | `cus.cfhandset` | `cus.cfhandset` |
| `cus_id` | 正式客户 ID | `cus.fid` | `t.fcusid` |
| `name` | 客户姓名（like 模糊） | `cus.cfname` | `cus.cfname` |

`op` 语义与其它数据集一致（`=` `!=` `>` `<` `>=` `<=`、`like` 默认 `%value%`、`in`、`is_null`）。`phone`/`cus_id` 建议用 `=`，`name` 用 `like`。

## 2. 默认时间限制

**无默认时间过滤**（数据量小，仅按租户 `fcontrolunitid` 范围兜底）。返回 `meta` 不含 `default_time_filter_applied`。

## 3. 计数

`query_wechat_dialogue_count` / `query_wecom_dialogue_count` 用 `COUNT(*)` 计数（每行 = 一条绑定），等价于绑定条数。

## 4. 返回字段目录

### 4.1 微信对话（wechat_dialogue，5 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `fname` | 客户微信昵称 | 🔒 SHA256 |
| `fuserwechatname` | 员工微信昵称 | |
| `fusername` | 员工 | |
| `flastuserchattimestr` | 员工最后对话时间 | |
| `flastcustomerchattimestr` | 客户最后对话时间 | |

### 4.2 企微对话（wecom_dialogue，8 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `cusname` | 姓名 | 🔒 SHA256 |
| `username` | 员工 | |
| `faddtimestr` | 添加时间 | |
| `ftypename` | 平台（企微/聚合） | |
| `fuserchats` | 员工对话数 | |
| `fcustomerchats` | 客户对话数 | |
| `flastuserchattimestr` | 员工最后对话时间 | |
| `flastcustomerchattimestr` | 客户最后对话时间 | |

> 两个数据集的 SQL 底层 `select t.*` / `select wc.*` 会取出手机号等列，但网关只按上表 XML 白名单返回；未声明的敏感列（`cusphone`/`cfhandset` 等）一律不返回。企微的 `fuserchats`/`fcustomerchats` 由子查询 `sum` 得到，无对话数据时为 NULL 属正常。

## 5. 返回信封

与其它数据集一致：list 工具返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`limit`/`offset`) + `audit.trace_id`；count 工具返回 `data.count`。`fields` 里 `is_sha256=true` 的字段即上表标 🔒 者（微信 `fname`、企微 `cusname`）。

---

# 言迹录音文本数据集

本部分覆盖 `yanji_asr` 数据集（工具 `query_yanji_asr` / `query_yanji_asr_count`，言迹语音转写 ASR）。主表 `T_MED_YANJI_ASR`，inner join 正式客户 `CT_CRM_CUSTOMERINFO`（`t.fexternalcusid = cus.fid`），返回整段录音转写文本。

> 返回字段名与过滤字段名同样不区分大小写/下划线。🔒 = 返回前 SHA256 脱敏。

## 1. 可过滤字段（filters 白名单，3 个）

| field | 含义 | 底层列 |
|-------|------|--------|
| `phone` | 手机号（精确匹配） | `cus.cfhandset` |
| `cus_id` | 正式客户 ID | `cus.fid` |
| `name` | 客户姓名（like 模糊） | `cus.cfname` |

`op` 语义与其它数据集一致（`=` `!=` `>` `<` `>=` `<=`、`like` 默认 `%value%`、`in`、`is_null`）。`phone`/`cus_id` 建议用 `=`，`name` 用 `like`。

## 2. 默认时间限制

**无默认时间过滤**（仅按租户 `fcontrolunitid` 范围兜底）。返回 `meta` 不含 `default_time_filter_applied`。

## 3. 计数

`query_yanji_asr_count` 用 `COUNT(*)` 计数（每行 = 一条录音转写）。

## 4. 返回字段目录（7 个）

| 字段 | 中文标题 | 脱敏 |
|------|----------|------|
| `cusname` | 客户姓名 | 🔒 SHA256 |
| `ftext` | 录音文本（整段转写，CLOB） | |
| `fusername` | 员工 | |
| `fduration` | 时长(秒) | |
| `fcreatetimestr` | 创建时间 | |
| `fexternalvisitid` | 接诊ID | |
| `fexternalcusid` | 正式客户ID | |

> SQL 底层 `select t.*` 会取出 `fid`/`faudioid` 等列，但网关只按上表 XML 白名单返回；手机号 `cfhandset` 仅作 join/过滤、不进入输出。`ftext` 为 CLOB，网关已转成字符串返回，可能很长（几十到上千字）。`fusername` 在此数据中多为 NULL 属正常。

## 5. 返回信封

与其它数据集一致：list 工具返回 `data`(数组) + `meta`(含 `masked_fields`/`fields`/`limit`/`offset`) + `audit.trace_id`；count 工具返回 `data.count`。`fields` 里 `is_sha256=true` 的字段即上表标 🔒 者（`cusname`）。

---

## 6. 业绩数字化大盘（8 个数据集）

DBA 为业绩大盘新建的 8 个视图/表，按业务域划分为 4 个数据桶。

### 6.1 全院预收业绩（chargebill）

**数据桶**：`performance`  
**默认时间**：近 30 天（`bill_date`）  
**计数主键**：`bill_id`  
**租户列**：`ORG_ID`

**可过滤字段（11 个）**：

| field | 含义 |
|-------|------|
| `bill_date` | 收费单结账日期 |
| `bill_type_name` | 收费单类型 |
| `rec_newcust_flag` | 客户接诊新老编码：0新客，1老客 |
| `rec_firstcome_flag` | 客户接诊新客编码：0新客首次，1新客二次 |
| `rec_monthly_newcust_flag` | 客户接诊新老（月度）编码：0月度新客，1月度老客 |
| `rec_age` | 客户来院年龄 |
| `rec_consultant_id` | 接诊顾问ID |
| `rec_doctor_id` | 接诊医生ID |
| `org_name` | 医院组织名字 |
| `customer_id` | 客户ID |
| `bill_id` | 收费单ID |

**返回字段（16 个）**：`BILL_ID` / `BILL_CODE` / `BILL_DATE` / `CUSTOMER_ID` / `BILL_TYPE_CODE` / `BILL_TYPE_NAME` / `REC_NEWCUST_FLAG` / `REC_FIRSTCOME_FLAG` / `REC_MONTHLY_NEWCUST_FLAG` / `REC_AGE` / `REC_CONSULTANT_ID` / `REC_DOCTOR_ID` / `BILL_AMT` / `BILL_PAYMENT_REMARK` / `ORG_ID` / `ORG_NAME`

### 6.2 科室预收业绩（chargebill_prod）

**数据桶**：`performance`  
**默认时间**：近 30 天（`bill_date`）  
**计数主键**：`bill_entry_id`（同一收费单多产品明细）  
**租户列**：`ORG_ID`

**可过滤字段（17 个）**：同 chargebill + `product_type1_name` / `product_type2_name` / `product_type3_name` / `product_name` / `rec_section_code` / `bill_entry_id`

**返回字段（27 个）**：同 chargebill + `BILL_ENTRY_ID` / `PRODUCT_TYPE1_ID` / `PRODUCT_TYPE1_NAME` / `PRODUCT_TYPE2_ID` / `PRODUCT_TYPE2_NAME` / `PRODUCT_TYPE3_ID` / `PRODUCT_TYPE3_NAME` / `PRODUCT_ID` / `PRODUCT_NAME` / `PRODUCT_AMT` / `PRODUCT_QTY` / `REC_SECTION_CODE`

### 6.3 产品执行业绩（achieve_prod）

**数据桶**：`performance`  
**默认时间**：近 30 天（`execute_date`）  
**计数主键**：`bill_entry_id`  
**租户列**：`ORG_ID`

**可过滤字段（12 个）**：`execute_date` / `product_type1_name` / `product_type2_name` / `product_type3_name` / `product_name` / `cfdoctorid` / `fexecutorid` / `execute_doctor_id` / `org_name` / `customer_id` / `bill_id` / `bill_entry_id`

**返回字段（20 个）**：`ORG_ID` / `ORG_NAME` / `EXECUTE_DATE` / `EXECUTE_AMT` / `BILL_ID` / `BILL_ENTRY_ID` / `CUSTOMER_ID` / `CFDOCTORID` / `FEXECUTORID` / `EXECUTE_DOCTOR_ID` / `PRODUCT_TYPE1_ID` / `PRODUCT_TYPE1_NAME` / `PRODUCT_TYPE2_ID` / `PRODUCT_TYPE2_NAME` / `PRODUCT_TYPE3_ID` / `PRODUCT_TYPE3_NAME` / `PRODUCT_ID` / `PRODUCT_NAME` / `FCARDACCID` / `CFREMARK`

### 6.4 业绩目标（dailytarget）

**数据桶**：`performance`  
**默认时间**：近 30 天（`ftrgdate`）  
**计数主键**：`fid`  
**租户列**：`FCONTROLUNITID`

**可过滤字段（8 个）**：`ftrgdate` / `ftype` / `fsection` / `fcustnw` / `fbuildtype` / `fpersonid` / `fprodtype2id` / `fcontrolunitid`

**返回字段（23 个）**：`FID` / `FCONTROLUNITID` / `FCREATORID` / `FCREATETIME` / `FLASTUPDATEUSERID` / `FLASTUPDATETIME` / `FTRGDATE` / `FTYPE` / `FPERSONID` / `FSECTION` / `FPRODTYPE2ID` / `FPRODTYPE2NUM` / `FBUILDTYPE` / `FCUSTNW` / `FBUILDCNT` / `FBOOKINGCNT` / `FRECCNT` / `FBILLCNT` / `FAMT` / `FCONV2RECRAITO` / `FQUERYCNT` / `FAVGAMT` / `FEXECUTORMONEY`

### 6.5 客户基础资料（customer_info）

**数据桶**：`channel`  
**默认时间**：无  
**计数主键**：`customer_id`  
**租户列**：`ORG_ID`

**可过滤字段（10 个）**：`customer_name` 🔒 / `customer_current_age` / `build_date` / `province_name` / `city_name` / `region_name` / `org_name` / `owner_consultant_id` / `temp_client_id` / `customer_id`

**返回字段（12 个）**：`ORG_NAME` / `CUSTOMER_ID` / `CUSTOMER_NAME` 🔒 / `PHONE_MASKED` / `CUSTOMER_CURRENT_AGE` / `BUILD_DATE` / `OWNER_CONSULTANT_ID` / `PROVINCE_NAME` / `CITY_NAME` / `REGION_NAME` / `TEMP_CLIENT_ID` / `ORG_ID`

### 6.6 会员卡基础资料（customer_member_info）

**数据桶**：`channel`  
**默认时间**：无  
**计数主键**：`member_card_id`  
**租户列**：`ORG_ID`

**可过滤字段（7 个）**：`member_card_name` / `member_join_date` / `vilidity_flag` / `vip_flag` / `org_name` / `customer_id` / `member_card_id`

**返回字段（10 个）**：`ORG_NAME` / `CUSTOMER_ID` / `MEMBER_CARD_CODE` / `MEMBER_CARD_ID` / `MEMBER_CARD_NAME` / `MEMBER_JOIN_DATE` / `MEMBER_REWARD_POINTS` / `VILIDITY_FLAG` / `VIP_FLAG` / `ORG_ID`

### 6.7 渠道客户基础资料（temp_client_info）

**数据桶**：`channel`  
**默认时间**：无  
**计数主键**：`temp_client_id`  
**租户列**：`ORG_ID`

**可过滤字段（12 个）**：`temp_client_name` 🔒 / `temp_client_current_age` / `build_date` / `province_name` / `city_name` / `region_name` / `channel1_name` / `channel2_name` / `channel3_name` / `org_name` / `owner_consultant_id` / `temp_client_id`

**返回字段（17 个）**：`ORG_ID` / `ORG_NAME` / `TEMP_CLIENT_ID` / `TEMP_CLIENT_NAME` 🔒 / `PHONE_MASKED` / `TEMP_CLIENT_CURRENT_AGE` / `BUILD_DATE` / `OWNER_CONSULTANT_ID` / `PROVINCE_NAME` / `CITY_NAME` / `REGION_NAME` / `CHANNEL1_ID` / `CHANNEL1_NAME` / `CHANNEL2_ID` / `CHANNEL2_NAME` / `CHANNEL3_ID` / `CHANNEL3_NAME`

### 6.8 员工基础资料（staff_info）

**数据桶**：`staff`  
**默认时间**：无  
**计数主键**：`staff_id`  
**租户列**：`ORG_ID`

**可过滤字段（6 个）**：`staff_name` 🔒 / `staff_code` / `group_l1_name` / `group_l2_name` / `org_name` / `staff_id`

**返回字段（10 个）**：`ORG_ID` / `ORG_NAME` / `STAFF_ID` / `STAFF_NAME` 🔒 / `STAFF_CODE` / `PHONE_MASKED` / `GROUP_L2_NAME` / `GROUP_L2_SORT` / `GROUP_L1_NAME` / `GROUP_L1_SORT`

**敏感字段**：`CUSTOMER_NAME` / `TEMP_CLIENT_NAME` / `STAFF_NAME` 返回前 SHA256 脱敏。`PHONE_MASKED` 已由 DBA 脱敏，不再二次处理。

