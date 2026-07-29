# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "limit": {
      "type": "integer",
      "default": 25,
      "examples": [
        {
          "value": "25",
          "summary": "默认 25 条"
        },
        {
          "value": "100",
          "summary": "扩大到 100 条"
        }
      ],
      "description": "返回条数上限（1-200 整数）。本接口没有 page 参数，不支持翻页，只按 source_collected_at 倒序返回最近 N 条。不传默认 25 条；首次探索建议保持默认值，用户明确要求「看更多」「扩大候选」「尽量多给一些」时再提高。"
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "whoop band",
          "summary": "Whoop 表带类"
        }
      ],
      "maxLength": 1000,
      "description": "搜索关键词文本片段（模糊匹配）。用户提到具体关键词或品类时使用，例如用户说「找 whoop 相关的赛道」则传 'whoop band'；传词或短语片段即可，不要传整句口语。"
    },
    "nicheName": {
      "type": "string",
      "examples": [
        {
          "value": "wired_ribbon",
          "summary": "金属丝带类赛道"
        }
      ],
      "maxLength": 1000,
      "description": "赛道归一化名称片段（模糊匹配，snake_case 小写）。当用户想跟踪某个具体赛道历次报告时使用；通常为小写英文 + 下划线，传词根即可（如 'wired_ribbon'、'bicep_band'）。与 keyword 区别：niche_name 是 LLM 从报告标题提炼的归一名，跨次采集稳定，适合做赛道时序对比。"
    },
    "amazonDomain": {
      "type": "string",
      "pattern": "US",
      "examples": [
        {
          "value": "US",
          "summary": "美国站"
        }
      ],
      "description": "亚马逊站点代码（闭枚举）。当前仅支持美国站，固定填 'US'，其它站点暂未开放。用户未指定站点时不传，等同于「仅查美国站」。"
    },
    "priceMaxUsdGte": {
      "type": "number",
      "examples": [
        {
          "value": "50",
          "summary": "顶价 ≥ $50 有溢价空间"
        }
      ],
      "description": "赛道最高商品价格下限（USD）。当用户希望「赛道有高客单价空间」「能做品牌溢价」时使用，确保头部产品价格够高。"
    },
    "priceMaxUsdLte": {
      "type": "number",
      "examples": [
        {
          "value": "50",
          "summary": "顶价 ≤ $50 聚焦平价"
        }
      ],
      "description": "赛道最高商品价格上限（USD）。当用户表达「避开高价赛道」「聚焦平价市场」时使用。"
    },
    "priceMinUsdGte": {
      "type": "number",
      "examples": [
        {
          "value": "5",
          "summary": "底价 ≥ $5"
        }
      ],
      "description": "赛道最低商品价格下限（USD）。当用户想避开极端低价赛道（如「不做 1-2 美元的赛道」）时填。"
    },
    "priceMinUsdLte": {
      "type": "number",
      "examples": [
        {
          "value": "10",
          "summary": "底价 ≤ $10 低门槛"
        }
      ],
      "description": "赛道最低商品价格上限（USD）。少用，仅当用户想找「低价产品起步门槛低」的赛道时填。"
    },
    "nichePeakMonthGte": {
      "type": "integer",
      "examples": [
        {
          "value": "11",
          "summary": "Q4 旺季 11 月起"
        }
      ],
      "description": "搜索峰值月份下限（1-12 整数）。当用户提到旺季备货、季节性选品时使用；与 Lte 配合圈定季节窗口。如 Q4 旺季填 11，仲夏 Prime Day 周边填 7。"
    },
    "nichePeakMonthLte": {
      "type": "integer",
      "examples": [
        {
          "value": "12",
          "summary": "Q4 旺季截至 12 月"
        }
      ],
      "description": "搜索峰值月份上限（1-12 整数）。与 Gte 配合圈定季节窗口，例如同时填 11 和 12 表示旺季在年末两个月内的赛道。"
    },
    "demoGenderDominant": {
      "type": "string",
      "examples": [
        {
          "value": "female",
          "summary": "女性主导"
        },
        {
          "value": "male",
          "summary": "男性主导"
        },
        {
          "value": "mixed",
          "summary": "混合人群"
        },
        {
          "value": "unspecified",
          "summary": "未指定"
        }
      ],
      "maxLength": 1000,
      "description": "性别主导（闭枚举，精确匹配）。决定营销语言基调。当用户提到「做女性市场/男性市场」「不限性别」「未明确人群」时使用。可选值（必须四选一，不允许其它取值）：female（女性主导，营销语言偏女性化）、male（男性主导）、mixed（混合人群，男女均衡）、unspecified（报告未明确性别倾向，可视为通用）。"
    },
    "nicheBrandCountGte": {
      "type": "integer",
      "examples": [
        {
          "value": "5",
          "summary": "至少 5 个品牌"
        }
      ],
      "description": "活跃品牌数下限（整数）。当用户希望赛道「已有一定品牌参与」，避免过度小众/垃圾赛道时填。"
    },
    "nicheBrandCountLte": {
      "type": "integer",
      "examples": [
        {
          "value": "20",
          "summary": "新人友好低密度"
        }
      ],
      "description": "活跃品牌数上限（整数）。当用户提到「新人友好」「低竞争」「品牌少」「避开寡头」时使用；这是判断竞争密度最直接的字段，越低代表越易切入。"
    },
    "demoPrimaryAgeMaxGte": {
      "type": "integer",
      "examples": [
        {
          "value": "55",
          "summary": "年龄段覆盖到 ≥ 55"
        }
      ],
      "description": "主人群年龄上界的最小值（岁，0-120）。少用，仅当用户希望「覆盖到中老年」「年龄段够宽」时填。"
    },
    "demoPrimaryAgeMaxLte": {
      "type": "integer",
      "examples": [
        {
          "value": "45",
          "summary": "目标 ≤45 岁"
        }
      ],
      "description": "主人群年龄上界的最大值（岁，0-120）。当用户提到「目标人群偏年轻」「避开老龄人群」时使用，例如填 45 表示核心人群最高年龄不超过 45 岁。"
    },
    "demoPrimaryAgeMinGte": {
      "type": "integer",
      "examples": [
        {
          "value": "25",
          "summary": "目标 25+ 岁"
        }
      ],
      "description": "主人群年龄下界（岁，0-120）的最小值。当用户提到「目标年龄不低于 X 岁」「避开太年轻人群」时使用。注意是「年龄下界 ≥ X」，意思是这个赛道的核心人群最低年龄至少要到 X 岁。"
    },
    "demoPrimaryAgeMinLte": {
      "type": "integer",
      "examples": [
        {
          "value": "20",
          "summary": "起始年龄 ≤ 20 岁，含年轻端"
        }
      ],
      "description": "主人群年龄下界的最大值（岁，0-120）。少用，仅当用户希望「赛道核心人群从年轻端开始」时填，例如填 18 表示核心年龄段从青少年起步。"
    },
    "demoPrimaryIncomeTier": {
      "type": "string",
      "examples": [
        {
          "value": "high",
          "summary": "高收入"
        },
        {
          "value": "middle_upper",
          "summary": "中上收入"
        },
        {
          "value": "upper_middle",
          "summary": "上中产"
        },
        {
          "value": "middle",
          "summary": "中产"
        },
        {
          "value": "middle_low",
          "summary": "中低收入"
        },
        {
          "value": "low",
          "summary": "低收入"
        }
      ],
      "maxLength": 1000,
      "description": "主人群收入档（闭枚举，精确匹配）。当用户提到「高端/中产/平价」等定价相关人群定位时使用。决定赛道支持的定价天花板。可选值（必须六选一，不允许其它取值）：low（低收入/budget）、middle_low（中低收入）、middle（中产）、middle_upper（中上收入，偏好型表达）、upper_middle（上中产，偏强表达）、high（高收入/premium，含 $100k+ 家庭）。如果用户说「中上」两种写法都可，建议优先 middle_upper。"
    },
    "priceSweetSpotMaxUsdGte": {
      "type": "number",
      "examples": [
        {
          "value": "30",
          "summary": "建议定价上限 ≥ $30"
        }
      ],
      "description": "Sweet Spot 上限的下界（USD）。当用户希望最佳定价空间够大、有溢价想象力时填。"
    },
    "priceSweetSpotMaxUsdLte": {
      "type": "number",
      "examples": [
        {
          "value": "100",
          "summary": "建议定价 ≤ $100"
        }
      ],
      "description": "Sweet Spot 上限的上界（USD）。少用，仅当用户想「避开建议定价过高的赛道」时填。"
    },
    "priceSweetSpotMinUsdGte": {
      "type": "number",
      "examples": [
        {
          "value": "10",
          "summary": "建议入场价 ≥ $10"
        }
      ],
      "description": "Sweet Spot 下限的下界（USD）。Sweet Spot 是亚马逊建议的最佳定价区间。当用户问「目标定价应该 ≥ 多少」或想确保赛道支持较高入场定价时填。"
    },
    "priceSweetSpotMinUsdLte": {
      "type": "number",
      "examples": [
        {
          "value": "30",
          "summary": "建议入场价 ≤ $30"
        }
      ],
      "description": "Sweet Spot 下限的上界（USD）。当用户希望入场价不要太高、定价友好时填。"
    },
    "reviewNegativeTop1Topic": {
      "type": "string",
      "examples": [
        {
          "value": "size",
          "summary": "尺码相关痛点"
        }
      ],
      "maxLength": 1000,
      "description": "差评 #1 主题片段（半开放词典，模糊匹配，snake_case 小写）。当用户表达「想做尺码痛点切入」「找质量问题严重的赛道」时使用，传词根（如 size、quality、durability、leather、material、comfort）即可命中含该词根的归一化主题。常见值（仅举例，不限于此）：size_smaller_than_expected、quality_overall_generic、not_leather、breaks_easily、material_cheap_feel、comfort_overall_generic、durability_low。Agent 应根据用户具体诉求传最有信号的词根，模糊匹配会自动覆盖语义相近的归一标签。"
    },
    "reviewNegativeTop2Topic": {
      "type": "string",
      "examples": [
        {
          "value": "leather",
          "summary": "材质相关痛点"
        }
      ],
      "maxLength": 1000,
      "description": "差评 #2 主题片段（半开放词典，模糊匹配，snake_case 小写）。Top1 常为通用大类（如 quality_overall_generic），Top2 通常是具体可操作的痛点；当用户想找「具体痛点」而非「通用质量问题」时优先用本字段。常见值（仅举例，不限于此）：not_leather、breaks_easily、size_smaller_than_expected、odor_strong、color_inaccurate、battery_short。"
    },
    "reviewPositiveTop1Topic": {
      "type": "string",
      "examples": [
        {
          "value": "comfort",
          "summary": "舒适度相关卖点"
        }
      ],
      "maxLength": 1000,
      "description": "好评 #1 主题片段（半开放词典，模糊匹配，snake_case 小写）。当用户想「找以舒适度/性价比/质量驱动的好评赛道」作为卖点参考时使用。常见值（仅举例，不限于此）：quality_overall_generic、comfort_overall_generic、works_good、value_good、easy_to_use、looks_good、durability_high。"
    },
    "searchTopCategory1Label": {
      "type": "string",
      "examples": [
        {
          "value": "set_kit",
          "summary": "套装/工具包主导赛道"
        }
      ],
      "maxLength": 1000,
      "description": "搜索流量第一类目标签片段（半开放词典，模糊匹配，snake_case 小写）。表达赛道的「消费形态」——用户主要按什么维度搜索。当用户提到「想做套装/兼容产品/版本特定/颜色尺寸主导」等消费形态相关诉求时使用。常见值（仅举例，不限于此）：core_product_terms（核心产品词主导）、branded_searches（品牌词主导）、set_kit_configurations（套装/工具包）、version_specific_compatibility（版本/型号兼容）、alternative_placements（替代部位/用法）、size_specific（尺寸特定）、color_specific（颜色特定）、seasonal_specific（季节特定）。Agent 也可以根据用户诉求生成新的 snake_case 标签（如 gender_specific、material_specific）。"
    },
    "featureTopBrandsContains": {
      "type": "string",
      "examples": [
        {
          "value": "Beetles",
          "summary": "包含 Beetles 品牌"
        }
      ],
      "maxLength": 1000,
      "description": "Top 3 品牌名片段（模糊匹配，大小写不敏感）。当用户想找「含某品牌的赛道」「跟踪竞品所在赛道」时使用，传品牌名或可识别的片段即可（如 Beetles、whoop、anker）。不需要确切官方拼写，传 anker 也能命中 AnkerPro。"
    },
    "demoLifeStageTagsContains": {
      "type": "string",
      "examples": [
        {
          "value": "parent",
          "summary": "父母人群"
        }
      ],
      "maxLength": 1000,
      "description": "主人群生命阶段标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。表达「年龄+性别之外」的人群信息（同样 30 岁，新手父母 vs 单身职业人士的产品偏好完全不同）。当用户表达「做妈妈赛道」「学生群体」「退休人群」「健身爱好者」等时使用。常见值（仅举例，不限于此）：parent（父母）、new_parent（新手父母）、professional（职场人士）、student（学生）、retiree（退休）、empty_nester（空巢）、gift_buyer（送礼场景）、athlete（运动员）、fitness_enthusiast（健身爱好者）、homemaker（居家主妇/夫）。Agent 可根据用户诉求生成新的 snake_case 标签（如 pet_owner、frequent_traveler）。"
    },
    "nichePeakSearchVolumeAtLeastGte": {
      "type": "integer",
      "examples": [
        {
          "value": "100000",
          "summary": "峰值 ≥ 10 万次"
        }
      ],
      "description": "峰值月搜索量下限（非负整数）。当用户希望赛道「流量天花板足够高」「旺季单月够能打」时使用，是流量上限的硬门槛。"
    },
    "nichePeakSearchVolumeAtLeastLte": {
      "type": "integer",
      "examples": [
        {
          "value": "1000000",
          "summary": "峰值 ≤ 100 万次"
        }
      ],
      "description": "峰值月搜索量上限（非负整数）。少用，仅当用户想避开过热赛道时填。"
    },
    "priceMidClickSharePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "30",
          "summary": "中档 ≥ 30% 已经成立"
        }
      ],
      "description": "中档点击份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「中档已经成立」的赛道时填。"
    },
    "priceMidClickSharePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "5",
          "summary": "≤5% 中档蓝海"
        }
      ],
      "description": "中档点击份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「中档蓝海」「中价位机会」「现有产品两极化（要么便宜要么贵）」时使用，配合 priceEntryClickSharePctAtLeastGte 一起表达「低价主导但中档稀缺」。"
    },
    "reviewNegativeTop1PctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "70",
          "summary": "≥70% 主导痛点"
        }
      ],
      "description": "差评 #1 主题在负面评论中的占比下限（输入 N 表示 N%，取值范围 0-100，不是总评论占比）。当用户提到「主导痛点」「痛点集中」「痛点强烈」时使用，配合 reviewNegativeTop1Topic 一起表达「找尺码痛点强烈到 ≥70% 的赛道」。"
    },
    "reviewNegativeTop1PctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "50",
          "summary": "痛点 ≤ 50% 不主导"
        }
      ],
      "description": "差评 #1 主题占比上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「痛点不那么集中、相对均匀」的赛道时填。"
    },
    "reviewPositiveTop1PctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "70",
          "summary": "≥70% 主导卖点"
        }
      ],
      "description": "好评 #1 主题在正面评论中的占比下限（输入 N 表示 N%，取值范围 0-100，不是总评论占比）。当用户提到「主导卖点」「卖点集中」「明确卖点」时使用；高占比意味着 listing 文案应当把这个主题放主图。"
    },
    "reviewPositiveTop1PctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "50",
          "summary": "卖点 ≤ 50% 不主导"
        }
      ],
      "description": "好评 #1 主题占比上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「卖点分散，需要多角度表达」的赛道时填。"
    },
    "featureEmergingTrendTagsContains": {
      "type": "string",
      "examples": [
        {
          "value": "cordless",
          "summary": "无线趋势"
        }
      ],
      "maxLength": 1000,
      "description": "新兴趋势特征标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想「提前布局新形态」「跟风口产品」时使用。常见值（仅举例，不限于此）：cordless（无线）、portable（便携）、eco_friendly（环保）、smart（智能）、app_connected（APP 联动）、wireless（无线）、rechargeable（可充电）、sustainable（可持续）、modular（模块化）。Agent 可根据用户诉求生成新的 snake_case 标签。"
    },
    "nicheRevenue360dMaxUsdAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "1000000",
          "summary": "营收上界 ≥ 100 万美元"
        }
      ],
      "description": "市场营收上界（USD）的最小值，含。当用户希望赛道有较高营收天花板时填，配合 Min 字段判断市场规模区间。比如用户说「赛道上限要够大」。"
    },
    "nicheRevenue360dMaxUsdAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "5000000",
          "summary": "上界 ≤ 500 万美元"
        }
      ],
      "description": "市场营收上界（USD）的最大值，含。少用，仅当用户明确要排除大赛道时填。"
    },
    "nicheRevenue360dMinUsdAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "500000",
          "summary": "市场营收 ≥ 50 万美元"
        }
      ],
      "description": "市场营收下界（USD）的最小值，含。当用户表达「市场规模至少要 X 美元」时使用，只关心市场规模底线时填这一侧；通常和 nicheRevenue360dMaxUsdAtLeastGte 二选一即可。源文本带 + 表示真实值 ≥ 该数（如 $110k+ → 110000）。"
    },
    "nicheRevenue360dMinUsdAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "200000",
          "summary": "下界 ≤ 20 万美元，避开太大的赛道"
        }
      ],
      "description": "市场营收下界（USD）的最大值，含。少用，仅当用户想「排除市场规模下界过高的赛道」（小赛道偏好者）时填。"
    },
    "priceHighClickSharePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "25",
          "summary": "≥25% 高端可做"
        }
      ],
      "description": "高端档点击份额下限（输入 N 表示 N%，取值范围 0-100）。当用户想做「品牌溢价产品」「高端定位」「有付费意愿的人群」时使用，数值越高代表赛道支撑高价能力越强。"
    },
    "priceHighClickSharePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "10",
          "summary": "高端 ≤ 10%"
        }
      ],
      "description": "高端档点击份额上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想避开「过度高端化」的赛道时填。"
    },
    "priceEntryClickSharePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "70",
          "summary": "≥70% 低价主导"
        }
      ],
      "description": "入门档点击份额下限（输入 N 表示 N%，取值范围 0-100）。当用户想找「低价主导」「价格敏感人群驱动」的赛道时填高值。这是档位主导信号，回答「消费者的注意力是否集中在低价档」。"
    },
    "priceEntryClickSharePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "50",
          "summary": "入门档 ≤ 50% 不主导"
        }
      ],
      "description": "入门档点击份额上限（输入 N 表示 N%，取值范围 0-100）。少用，配合 mid/high 档反推时偶尔填。"
    },
    "featureNewAvgReviewCountAtLeastGte": {
      "type": "integer",
      "examples": [
        {
          "value": "200",
          "summary": "新品 ≥ 200 条评论"
        }
      ],
      "description": "新品平均评论量下限（非负整数）。少用，仅当用户想找「新品已经积累起来」的成熟赛道时填。"
    },
    "featureNewAvgReviewCountAtLeastLte": {
      "type": "integer",
      "examples": [
        {
          "value": "500",
          "summary": "新人友好 ≤500 条评论"
        }
      ],
      "description": "新品平均评论量上限（非负整数）。当用户提到「新人友好」「新品进入门槛低」「不用刷太多评论」时使用，是切入难度的核心指标。"
    },
    "featureTop5BrandSharePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "70",
          "summary": "≥70% 品牌寡头"
        }
      ],
      "description": "Top5 品牌合计份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「品牌寡头」「头部品牌瓜分市场」赛道时填高值。注意与 nicheTop5ProductClickSharePctAtLeast（产品级）区分：本字段是品牌级集中度，二者可同时存在分歧（如品牌分散但产品集中=私域品牌堆 SKU）。"
    },
    "featureTop5BrandSharePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "60",
          "summary": "≤60% 品牌分散"
        }
      ],
      "description": "Top5 品牌合计份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「品牌分散」「无寡头」「新品牌易切入」时使用。常和 nicheTop5ProductClickSharePctAtLeast（产品级集中度）配合：品牌分散 + 产品集中 = 品牌延伸切入机会。"
    },
    "featureUncommonFeatureTagsContains": {
      "type": "string",
      "examples": [
        {
          "value": "hema_free",
          "summary": "无 HEMA 特性"
        }
      ],
      "maxLength": 1000,
      "description": "稀有差异化特征标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想找「行业里少见但有亮点的差异化特征」「有供应链优势可发挥差异化」赛道时使用。常见值（仅举例，不限于此）：hema_free（无 HEMA）、medical_grade_silicone（医疗级硅胶）、bpa_free（无 BPA）、waterproof（防水）、foldable（可折叠）、magnetic_clasp（磁吸扣）、led_indicator（LED 指示）、fda_approved（FDA 认证）。Agent 可根据用户诉求生成新的 snake_case 标签（如 vegan、odor_free、anti_microbial）；传词根即可命中含该词根的归一化标签。"
    },
    "reviewStrategicInsightTagsContains": {
      "type": "string",
      "examples": [
        {
          "value": "material_transparency",
          "summary": "材质透明化建议"
        }
      ],
      "maxLength": 1000,
      "description": "评论策略建议标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想「通过 Listing 优化或产品改良切入」赛道时使用，本字段表达「赛道适合靠什么角度做差异化 listing」。常见值（仅举例，不限于此）：sizing_clarity（尺码沟通清晰化）、material_transparency（材质透明化）、durability_enhancement（耐用性强化）、safety_proactive（主动安全沟通）、comfort_positioning（舒适度定位）、value_bundle（套装/超值组合）、brand_trust（品牌信任建设）。Agent 可根据具体场景生成新的 snake_case 标签。"
    },
    "nicheBrandCountYoyChangePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "20",
          "summary": "品牌数同比 ≥ 20% 涌入"
        }
      ],
      "description": "品牌数同比变化率下限（%，带符号）。少用，仅当用户想找「品牌正在涌入的热门赛道」时填正数。"
    },
    "nicheBrandCountYoyChangePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "0",
          "summary": "品牌数未增长或缩减"
        }
      ],
      "description": "品牌数同比变化率上限（%，带符号）。当用户提到「品牌退出」「老玩家撤退」「新人切入机会」时使用；填 0 表示品牌数未增长，填负数表示品牌净缩减赛道（典型的反向选品信号）。"
    },
    "nicheSearchVolumeYoyChangePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "100",
          "summary": "同比 ≥ 100% 高增长"
        }
      ],
      "description": "搜索量同比变化率下限（输入 N 表示 N%，取值范围 -100 及以上，带符号）。当用户提到「增长型赛道」「高增长」「上升趋势」时使用；填正数表示增长门槛（100=同比翻倍）。本字段是「增长动能」信号的核心入口。"
    },
    "nicheSearchVolumeYoyChangePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "0",
          "summary": "搜索量未增长或衰退"
        }
      ],
      "description": "搜索量同比变化率上限（输入 N 表示 N%，取值范围 -100 及以上，带符号）。少用，仅当用户想「避开增长过热」或「找衰退赛道」时填；后者填 0 即可（搜索量未增长）。"
    },
    "nicheTop5ProductClickSharePctAtLeastGte": {
      "type": "number",
      "examples": [
        {
          "value": "70",
          "summary": "≥70% 头部产品寡头"
        }
      ],
      "description": "Top5 产品点击份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「产品端高度集中」的赛道（典型如想做白牌跟卖时找寡头赛道）时填高值。"
    },
    "nicheTop5ProductClickSharePctAtLeastLte": {
      "type": "number",
      "examples": [
        {
          "value": "40",
          "summary": "≤40% 产品分散，新人友好"
        }
      ],
      "description": "Top5 产品点击份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「避开寡头」「产品分散」「单品不集中」时使用；这是产品级集中度的核心反向指标，与 featureTop5BrandSharePctAtLeast（品牌级）互补。"
    },
    "featureEstablishedAvgReviewCountAtLeastGte": {
      "type": "integer",
      "examples": [
        {
          "value": "5000",
          "summary": "老品 ≥ 5000 条评论"
        }
      ],
      "description": "成熟老品平均评论量下限（非负整数）。少用，仅当用户特别想找「头部壁垒高的成熟赛道」（避开早期赛道）时填。"
    },
    "featureEstablishedAvgReviewCountAtLeastLte": {
      "type": "integer",
      "examples": [
        {
          "value": "5000",
          "summary": "头部壁垒 ≤5000 条"
        }
      ],
      "description": "成熟老品平均评论量上限（非负整数）。当用户提到「头部壁垒不高」「有机会撼动头部」「老品评论也不多」时使用。配合 New 字段一起用可以判断「赛道整体年轻 vs 成熟」。"
    }
  }
}
```

</details>

## 原始 Output Schema

<details>
<summary>展开查看完整 Output Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "msg": {
      "type": "string",
      "description": "提示信息。成功为 ok。"
    },
    "code": {
      "type": "string",
      "description": "响应码。成功为 200。"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "keyword": {
            "type": "string",
            "description": "关键词.原始搜索关键词，用于反向追溯报告来源。"
          },
          "nicheName": {
            "type": "string",
            "description": "赛道名称.归一化赛道名称，适合按赛道做时序对比。"
          },
          "priceMaxUsd": {
            "type": "number",
            "description": "最高价.赛道整体最高商品价格，单位 USD。"
          },
          "priceMinUsd": {
            "type": "number",
            "description": "最低价.赛道整体最低商品价格，单位 USD。"
          },
          "amazonDomain": {
            "type": "string",
            "description": "站点.亚马逊站点代码，当前固定 US。"
          },
          "nichePeakMonth": {
            "type": "integer",
            "description": "峰值月份.年内搜索峰值月份，取值范围 1-12。"
          },
          "nicheBrandCount": {
            "type": "integer",
            "description": "品牌数.活跃品牌数量，数值越小通常竞争密度越低。"
          },
          "featureTopBrands": {
            "type": "array",
            "items": {},
            "description": "Top3品牌.核心品牌名列表，按出现顺序返回。"
          },
          "demoLifeStageTags": {
            "type": "array",
            "items": {},
            "description": "生命阶段标签.核心人群的生命阶段或生活状态标签。"
          },
          "demoPrimaryAgeMax": {
            "type": "integer",
            "description": "最高年龄.核心人群最高年龄，单位岁。"
          },
          "demoPrimaryAgeMin": {
            "type": "integer",
            "description": "最低年龄.核心人群最低年龄，单位岁。"
          },
          "demoGenderDominant": {
            "type": "string",
            "description": "性别主导.核心人群性别倾向，可选值为 female、male、mixed、unspecified。"
          },
          "priceSweetSpotMaxUsd": {
            "type": "number",
            "description": "建议最高价.Value Sweet Spot 价格区间最高值，单位 USD。"
          },
          "priceSweetSpotMinUsd": {
            "type": "number",
            "description": "建议最低价.Value Sweet Spot 价格区间最低值，单位 USD。"
          },
          "demoPrimaryIncomeTier": {
            "type": "string",
            "description": "收入档.核心人群收入档，可选值为 low、middle_low、middle、middle_upper、upper_middle、high。"
          },
          "reviewNegativeTop1Topic": {
            "type": "string",
            "description": "差评主因.负面评论中最主要的归一化主题。"
          },
          "reviewNegativeTop2Topic": {
            "type": "string",
            "description": "差评次因.负面评论中第二主要的归一化主题。"
          },
          "reviewPositiveTop1Topic": {
            "type": "string",
            "description": "好评主因.正面评论中最主要的归一化主题。"
          },
          "searchTopCategory1Label": {
            "type": "string",
            "description": "搜索形态.流量第一类目归一化标签，表达用户主要按什么维度搜索。"
          },
          "featureEmergingTrendTags": {
            "type": "array",
            "items": {},
            "description": "趋势特征.行业内新出现的产品形态或功能趋势标签。"
          },
          "featureUncommonFeatureTags": {
            "type": "array",
            "items": {},
            "description": "稀有特征.行业中较少产品具备的差异化功能、材质或规格标签。"
          },
          "reviewStrategicInsightTags": {
            "type": "array",
            "items": {},
            "description": "评论策略标签.基于评论洞察生成的 Listing 优化或产品改良方向标签。"
          },
          "nichePeakSearchVolumeAtLeast": {
            "type": "integer",
            "description": "峰值月搜索量.峰值月份搜索量下界，越高代表旺季流量天花板越高。"
          },
          "priceMidClickSharePctAtLeast": {
            "type": "number",
            "description": "中档份额.中档价格点击份额百分比，取值范围 0-100。"
          },
          "reviewNegativeTop1PctAtLeast": {
            "type": "number",
            "description": "差评主因占比.差评主因在负面评论中的占比，取值范围 0-100。"
          },
          "reviewPositiveTop1PctAtLeast": {
            "type": "number",
            "description": "好评主因占比.好评主因在正面评论中的占比，取值范围 0-100。"
          },
          "nicheRevenue360dMaxUsdAtLeast": {
            "type": "number",
            "description": "最高营收.近 360 天市场营收最高估值，单位 USD；越高代表赛道流水天花板越高。"
          },
          "nicheRevenue360dMinUsdAtLeast": {
            "type": "number",
            "description": "最低营收.近 360 天市场营收最低估值，单位 USD；源文本带 + 时表示真实值不低于该数。"
          },
          "priceHighClickSharePctAtLeast": {
            "type": "number",
            "description": "高端档份额.高端价格档点击份额百分比，取值范围 0-100。"
          },
          "priceEntryClickSharePctAtLeast": {
            "type": "number",
            "description": "入门档份额.入门价格档点击份额百分比，取值范围 0-100。"
          },
          "featureNewAvgReviewCountAtLeast": {
            "type": "integer",
            "description": "新品评论数.新品平均评论量下界，非负整数。"
          },
          "featureTop5BrandSharePctAtLeast": {
            "type": "number",
            "description": "Top5品牌份额.头部品牌合计份额百分比，取值范围 0-100。"
          },
          "nicheBrandCountYoyChangePctAtLeast": {
            "type": "number",
            "description": "品牌数同比.百分比，正值表示品牌涌入，负值表示品牌净减少。"
          },
          "nicheSearchVolumeYoyChangePctAtLeast": {
            "type": "number",
            "description": "搜索量同比.百分比，100 表示同比增长 100%，-20 表示同比下降 20%。"
          },
          "nicheTop5ProductClickSharePctAtLeast": {
            "type": "number",
            "description": "Top5产品份额.点击份额百分比，取值范围 0-100，用于判断产品级集中度。"
          },
          "featureEstablishedAvgReviewCountAtLeast": {
            "type": "integer",
            "description": "成熟品评论数.成熟老品平均评论量下界，非负整数。"
          }
        }
      },
      "description": "命中关键词指标列表。每条等于 1 个 (站点, 关键词) 的完整 37 字段记录；按报告采集时间倒序。"
    },
    "type": {
      "type": "string",
      "description": "响应类型。前端按 tableListWorkbenches 渲染表格。"
    },
    "columns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "表格列定义。用于按 BusinessInsightMertrics 字段渲染指标结果。"
    },
    "costTime": {
      "type": "integer",
      "description": "处理耗时，单位毫秒。"
    },
    "costToken": {
      "type": "integer",
      "description": "token 消耗量。"
    }
  }
}
```

</details>
