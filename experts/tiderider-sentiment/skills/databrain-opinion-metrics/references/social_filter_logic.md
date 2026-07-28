# Social 模式下公共 Filter 特殊过滤方式

> **主表**：`tencent-databrain-prod.opinion.feeds`  
> **配置表**：`tencent-databrain-prod.opinion.dim_media_account`（监控账号）、`tencent-databrain-prod.opinion.dim_keyword`（监控关键词）  
> **分区字段**：`comment_time`（`opinion.feeds`）⚠️ 查询必须带时间范围

---

## 一、数据表分类

### 主数据表

| 表名 | 说明 |
|------|------|
| `tencent-databrain-prod.opinion.feeds` | 舆情主表 |
| `t_opinion_streaming`（BQ 路径待确认） | 直播数据表 |

### 监控配置表（过滤用）

| 表名 | 说明 |
|------|------|
| `tencent-databrain-prod.opinion.dim_media_account` | 监控官号配置表，`category` 字段对应账号分类 |
| `tencent-databrain-prod.opinion.dim_keyword` | 监控关键词配置表 |

---

## 二、dim_media_account 分类映射

| category 值 | 中文名称 | 说明 |
|-------------|---------|------|
| `official-accounts` | 官方运营账号 | 官方运营的社媒账号 |
| `discussion-groups` | 讨论群组/论坛 | 论坛、群组类账号 |
| `kol-monitoring` | 监控KOL | 重点监控的KOL账号 |
| `single-post-comments` | 单帖评论/弹幕 | 单帖采集的评论/弹幕数据 |
| `PRIVATE` | 私密渠道 | 私密/内部渠道账号 |
| `live-broadcast` | 直播采集 | 直播相关数据采集 |
| `material` | UA素材 | UA投放素材相关 |
| `EXTERNAL` | 外部数据源 | 外部第三方数据源 |

**过滤逻辑**（查询指定分类的账号列表）：

```sql
SELECT DISTINCT LOWER(CONCAT(account_url, '#_#', account_name)) AS match_key
FROM `tencent-databrain-prod.opinion.dim_media_account`
WHERE unified_edition_id = '<game_id>'
  AND category = 'official-accounts'   -- 替换为目标 category 值
  AND LOWER(visibility) != 'hidden'
  AND crawler_state = 1
```

---

## 三、特殊过滤方式

### 1. SocialMediaByAccounts（监控官号过滤）

**说明**：过滤出来自指定官方账号的内容，需与 feeds 表的 `sources` 字段关联

```sql
-- Step 1：从配置表获取有效官号 match_key
WITH valid_accounts AS (
  SELECT DISTINCT LOWER(CONCAT(account_url, '#_#', account_name)) AS match_key
  FROM `tencent-databrain-prod.opinion.dim_media_account`
  WHERE unified_edition_id = '<game_id>'
    AND LOWER(visibility) != 'hidden'
    AND crawler_state = 1
    AND account_name != ''
)
-- Step 2：在 feeds 表中过滤包含官号来源的内容
SELECT *
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND EXISTS (
    SELECT 1 FROM UNNEST(sources) s
    WHERE LOWER(s.source) = 'account'
      AND LOWER(CONCAT(s.url, '#_#', s.name)) IN (SELECT match_key FROM valid_accounts)
  )
```

**匹配方式**：`source#_#account_name`（渠道 + 账号名组合）

---

### 2. SocialMediaByKeywords（监控关键词过滤）

```sql
WITH valid_keywords AS (
  SELECT DISTINCT LOWER(keyword) AS match_key
  FROM `tencent-databrain-prod.opinion.dim_keyword`
  WHERE unified_edition_id = '<game_id>'
    AND LOWER(visibility) != 'hidden'
    AND crawler_state = 1
    AND keyword != ''
)
SELECT *
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND EXISTS (
    SELECT 1 FROM UNNEST(sources) s
    WHERE LOWER(s.source) = 'keyword'
      AND LOWER(s.name) IN (SELECT match_key FROM valid_keywords)
  )
```

---

### 3. ExternalDataSources（外部数据源过滤）

```sql
SELECT *
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND EXISTS (
    SELECT 1 FROM UNNEST(sources) s
    WHERE LOWER(s.source) IN ('levelup')   -- 替换为实际外部数据源标识
  )
```

---

### 4. AccountCategory（账号分类过滤）

```sql
WITH category_accounts AS (
  SELECT DISTINCT LOWER(CONCAT(account_url, '#_#', account_name)) AS match_key
  FROM `tencent-databrain-prod.opinion.dim_media_account`
  WHERE unified_edition_id = '<game_id>'
    AND category = '<category>'           -- 替换为目标 category 值
    AND LOWER(visibility) != 'hidden'
    AND crawler_state = 1
)
SELECT *
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND EXISTS (
    SELECT 1 FROM UNNEST(sources) s
    WHERE LOWER(CONCAT(s.url, '#_#', s.name)) IN (SELECT match_key FROM category_accounts)
  )
```

---

### 5. ChannelType（渠道类型过滤）

**字段**：`feeds.channel_type`

| 值 | 说明 |
|----|------|
| `social` | 社区/社媒渠道 |
| `comments` | 商店评论渠道 |
| `news` | 新闻渠道 |

```sql
-- 示例：仅查 social 渠道
WHERE channel_type = 'social'
```

---

### 6. Reviewer（发帖作者过滤）

```sql
-- 过滤指定作者（多个时用 IN）
WHERE LOWER(reviewer) = '<author_name>'
```

---

### 7. MediaType（媒体类型过滤）

**字段**：`feeds.media_type`

| 值 | 说明 |
|----|------|
| `video` | 视频 |
| `live` | 直播 |
| `image` | 图片 |
| `text` | 文本 |
| 空 | 默认类型 |

```sql
-- 示例：仅查视频和图片
WHERE media_type IN ('video', 'image')
```

---

### 8. IsValid（有效评论过滤）

**字段**：`feeds.isvalid`

| 值 | 说明 |
|----|------|
| `0` | 无效 |
| `1` | 有效 |
| `2` | 待确认 |
| `3` | 系统标记有效 |

```sql
-- 示例：仅统计有效评论
WHERE isvalid IN (1, 3)
```

---

## 四、sources 字段结构说明

`feeds.sources` 是 `ARRAY<STRUCT<source STRING, name STRING, url STRING>>` 类型，使用 `UNNEST` 展开：

```sql
-- 判断内容来源类型
FROM UNNEST(sources) AS s
WHERE s.source = 'account'    -- 来自监控官号
   OR s.source = 'keyword'    -- 来自监控关键词
   OR s.source = 'game_store' -- 来自游戏商店
   OR s.source = 'levelup'    -- 来自外部数据源
```
