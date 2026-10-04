---
name: efunds
display_name: 易方达基金MCP服务
display_name_en: E Fund MCP
description: 接入易方达基金MCP服务，一句话查透基金画像——业绩、风险收益、持仓结构等核心指标一目了然，还能随时调阅易方达发布的投研观点、产品解读与市场洞察，助力您高效进行投资决策。
description_zh: 接入易方达基金MCP服务，一句话查透基金画像——业绩、风险收益、持仓结构等核心指标一目了然，还能随时调阅易方达发布的投研观点、产品解读与市场洞察，助力您高效进行投资决策。
description_en: Connect to the E Fund MCP service to get a complete fund profile in a single query—performance, risk-return metrics, holdings structure, and other key indicators at a glance. You can also access E Fund's investment research insights, product interpretations, and market perspectives anytime to support efficient investment decision-making.
category: 投资理财
version: 1.1.0
author: 易方达基金
---

# 易方达基金MCP服务（efunds）

本连接器提供易方达基金的官方信息查询能力，共 3 个工具：

| 工具 | 用途 |
| --- | --- |
| `fund_profile_query` | 按基金代码查询基金画像（净值、业绩、基金经理、持仓、费率等） |
| `search_wx_articles` | 检索易方达官方微信公众号文章列表 |
| `get_wx_article_detail` | 按文章 ID 读取单篇公众号文章全文 |

## fund_profile_query —— 基金画像查询

用户询问某只基金的具体情况（净值/收益、基金经理、业绩、持仓、规模、费率、分红、公告等）时调用。

### 参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `fund_code` | string | 是 | 基金代码，六位数字字符串，如 `"005827"` |
| `modules` | string[] | 否 | 模块编码数组（大小写敏感，共 11 个编码）。省略=全量模块（页面全量渲染，含头部）；空数组=页面不渲染任何内容（含头部）；传入时页面仅当含 `banner` 编码才展示头部。**默认规则：显式传入 modules 时一律附带 `banner`，除非用户明确要求不展示头部** |

### modules 模块编码与意图映射

| 模块编码 | 内容 | 适用用户意图 |
| --- | --- | --- |
| `banner` | 顶部头部区（基金名称/代码/类型、晨星评级、风险等级与适合投资者、限购类标签、锁定期、A/C份额切换、Y份额个人养老金提示） | 问风险等级/评级/适合谁买（页面侧仅携带该编码才渲染头部，不参与模块排序） |
| `baseInfo` | 基本信息（日涨跌、单位/累计净值、今年以来/近1年/成立以来收益、总规模、成立日期、业绩比较基准文案及 cy/1y/all 基准收益、标的指数（指数基金）、联接基金入口；货币基金为万份收益与七日年化） | 了解基金概况 |
| `performance` | 业绩表现（近1年本基金与基准对比头部值、9区间涨跌幅与同类排名表、累计收益率曲线（本基金+基准）、基准文案、经理任期脚注） | 问业绩/收益/涨跌（通常与 baseInfo 同传） |
| `keyIndicators` | 关键指标（近1/2/3/5年 4 个时间维度并列在 periods[]，每维度含净值增长率/波动率/最大回撤/夏普比率/收益回撤比及同类平均、同类排名、优于同类比例；指数基金另含跟踪误差/信息比率；附经理任期脚注与银河分类） | 问回撤/夏普/波动/同类排名 |
| `fundManager` | 基金经理（经理姓名/任职起止/简介） | 问基金经理 |
| `assetAllocation` | 资产配置（大类资产配置与总资产、重仓持股（最新价/行业/占比/较上期/被重仓基金数）、前十占比、行业分布、重仓持债、重仓基金、股票及存托凭证） | 问持仓/重仓股/行业分布 |
| `scaleHolder` | 规模及持有人结构（历史规模与机构持有占比） | 问规模/谁在持有 |
| `feeStructure` | 费率结构（申购/赎回费率表与说明、运作费率（管理/托管/销售服务/指数许可费）、其他费用项目） | 问费率/申购赎回费 |
| `dividend` | 基金分红（权益登记日/每份分红/场外场内支付日） | 问分红 |
| `announcement` | 产品公告（公告列表/风险提示函/净值入口可用性） | 问公告/风险提示函 |
| `popularQuestions` | 大家都在问（问题/回答/跳转模块） | 常见问题 |

意图不明或用户想整体了解基金时，省略 `modules`（返回全量模块）；显式传 `modules` 时除用户明确要求外一律附带 `banner`，保证页面头部（基金名称/评级/风险等级）正常展示。

### 返回结果怎么读

- `modules.{编码}`：**直接是该模块的数据对象（扁平结构，无 `status` 包装）**；其中数值字段含 `display`（页面展示口径，如 "389.08亿元"/"-20.99%"）与 `raw`（上游原值）。**向用户复述请优先使用 `display`，不要自行估算**
- `modules.banner`：头部固有信息（基金名称/代码/风险等级/适合投资者类型/晨星评级），回答风险等级/适合谁买类问题时使用（对应意图传 `modules=["banner"]`）
- **某模块未返回（`modules` 中无该编码）**：`errors` 有对应记录=上游失败；无记录=命中页面规则不展示（如货币基金不展示关键指标）。两种情况页面同样不渲染该模块，属正常，如实告知用户「该模块暂无数据」即可
- `fund_url`：基金画像 H5 页面地址，**始终返回**；本服务不再内嵌渲染，如需让用户查看完整画像页面，把该链接直接提供给用户
- `generated_at`：数据生成时间（北京时区 ISO8601）；`message`：给 UI 的状态提示文案（服务端调试开启时另有 `debug_info`，可忽略）
- `errors`：上游失败与非法模块编码记录（内部诊断用，不要直接展示给用户）

## search_wx_articles —— 公众号文章检索

用户想找易方达公众号的文章（如"最近易方达发了哪些关于定投的文章"）时调用。检索结果为列表，阅读全文需配合 `get_wx_article_detail`。

### 参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string[] | 否 | 关键词列表，模糊匹配标题/摘要/正文，多关键词为 AND 关系；缺省返回最新文章（按发布时间倒序） |
| `account` | string | 否 | 公众号名称（精确匹配，如"易方达基金"）；缺省查全部白名单公众号，传入不在白名单的账号会被拒绝（白名单由服务端动态配置） |
| `title` | string | 否 | 文章标题，归一化后精确匹配，用于查询标题相同的多篇文章 |
| `start_date` | string | 否 | 开始日期 `yyyymmdd`，缺省 30 天前 |
| `end_date` | string | 否 | 结束日期 `yyyymmdd`，缺省今天 |
| `page` | int | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 20，上限 100 |

### 返回结构

```json
{
  "total": 15,
  "page": 1,
  "page_size": 20,
  "articles": [
    {
      "article_id": "文章 ID（用于查详情）",
      "title": "标题",
      "account_name": "公众号名称",
      "author": "作者",
      "pub_time": "yyyy-MM-dd HH:mm:ss",
      "digest": "摘要",
      "article_url": "原文链接",
      "cover_image": "封面图"
    }
  ]
}
```

`total` 为 0 且调用成功即表示无匹配文章，如实告知用户即可，可建议放宽时间范围或关键词。

## get_wx_article_detail —— 文章详情

用户想阅读某篇文章全文时调用（文章 ID 来自 `search_wx_articles` 的结果，参数名为 `article_id`）。返回在检索结果字段基础上增加：

- `content`：正文原文
- `content_images`：正文图片链接列表

## 组合使用示例

1. 用户："110011 最近表现怎么样？" → `fund_profile_query(fund_code="110011", modules=["banner", "baseInfo", "performance"])`
2. 用户："最近两周易方达公众号发了哪些定投的文章？" → `search_wx_articles(keyword=["定投"], start_date=<两周前 yyyymmdd>)`，向用户展示文章列表
3. 用户："展开第一篇看看" → 用列表中第一条的 `article_id` 调 `get_wx_article_detail(article_id=<article_id>)`，基于 `content` 作答

## 错误处理

- 业务拒绝（公众号不在白名单、文章 ID 不存在、日期非法等）以工具错误形式返回可读的中文原因，请直接把原因转述给用户，不要编造数据
- 基金代码必须为六位数字，用户只给了基金名称时，先确认或补全六位代码再调用
- 画像某模块缺失（`modules` 中无该编码）时，如实告知用户该模块暂无数据（如货币基金不展示关键指标），不要用其他数据替代；是上游失败还是页面规则不展示，可参考 `errors` 有无对应记录
