---
name: linkfox-amazon-opportunity-search-by-metrics
description: 亚马逊反向选品：基于历史商业洞察报告沉淀的指标数据池，按 30+ 项商业维度（市场规模与增长、价格区间与档位份额、竞争密度与头部集中度、人群画像如年龄/性别/收入、评论卖点与痛点等）反向筛选亚马逊赛道与关键词。当用户提到反向选品、指标筛选、细分市场反查、蓝海赛道挖掘、低竞争赛道、新人友好赛道、品牌分散市场、痛点切入、卖点反查、定价档位机会、人群画像选品、Amazon niche reverse search, niche metrics filter, low-competition niche, blue ocean niche, demographic-based selection, pain-point niche, price tier opportunity, sweet spot pricing, brand fragmentation时触发此技能。即使用户未明确说"反向选品"，只要其需求是按商业维度筛选符合条件的亚马逊赛道，也应触发此技能。
---

# 亚马逊-商业洞察(反向)

## 基本信息

- **业务工具名**：`/amazon/opportunity/searchByMetrics`
- **所属分组**：Amazon · 搜索、评论与商业洞察
- **功能说明**：基于历史商业洞察报告沉淀的指标数据池，支持以选品视角反向筛选亚马逊赛道与关键词。能够将用户口语化的需求映射为具体的查询条件，支持通过 30+ 项商业维度（包含市场规模与增长势能、价格区间与档位份额、竞争密度与头部集中度、人群画像如年龄/性别/收入、评论卖点与痛点标签等）精准圈选细分市场。工具会反向匹配出符合条件的关键词候选池，并输出结构化的赛道指标对比表，辅助选品与商业决策。
- **关键词**：亚马逊选品，反向选品，细分市场反查，蓝海赛道挖掘，指标筛选


## 何时使用

当用户意图与“亚马逊-商业洞察(反向)”匹配，或需要以下能力时使用本工具：基于历史商业洞察报告沉淀的指标数据池，支持以选品视角反向筛选亚马逊赛道与关键词。能够将用户口语化的需求映射为具体的查询条件，支持通过 30+ 项商业维度（包含市场规模与增长势能、价格区间与档位份额、竞争密度与头部集中度、人群画像如年龄/性别/收入、评论卖点与痛点标签等）精准圈选细分市场。工具会反向匹配出符合条件的关键词候选池，并输出结构化的赛道指标对比表，辅助选品与商业决策。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `limit` | `integer` | 否 | 默认 `25`；示例：`25`, `100` | 返回条数上限（1-200 整数）。本接口没有 page 参数，不支持翻页，只按 source_collected_at 倒序返回最近 N 条。不传默认 25 条；首次探索建议保持默认值，用户明确要求「看更多」「扩大候选」「尽量多给一些」时再提高。 |
| `keyword` | `string` | 否 | 最长 1000；示例：`whoop band` | 搜索关键词文本片段（模糊匹配）。用户提到具体关键词或品类时使用，例如用户说「找 whoop 相关的赛道」则传 'whoop band'；传词或短语片段即可，不要传整句口语。 |
| `nicheName` | `string` | 否 | 最长 1000；示例：`wired_ribbon` | 赛道归一化名称片段（模糊匹配，snake_case 小写）。当用户想跟踪某个具体赛道历次报告时使用；通常为小写英文 + 下划线，传词根即可（如 'wired_ribbon'、'bicep_band'）。与 keyword 区别：niche_name 是 LLM 从报告标题提炼的归一名，跨次采集稳定，适合做赛道时序对比。 |
| `amazonDomain` | `string` | 否 | 格式 `US`；示例：`US` | 亚马逊站点代码（闭枚举）。当前仅支持美国站，固定填 'US'，其它站点暂未开放。用户未指定站点时不传，等同于「仅查美国站」。 |
| `priceMaxUsdGte` | `number` | 否 | 示例：`50` | 赛道最高商品价格下限（USD）。当用户希望「赛道有高客单价空间」「能做品牌溢价」时使用，确保头部产品价格够高。 |
| `priceMaxUsdLte` | `number` | 否 | 示例：`50` | 赛道最高商品价格上限（USD）。当用户表达「避开高价赛道」「聚焦平价市场」时使用。 |
| `priceMinUsdGte` | `number` | 否 | 示例：`5` | 赛道最低商品价格下限（USD）。当用户想避开极端低价赛道（如「不做 1-2 美元的赛道」）时填。 |
| `priceMinUsdLte` | `number` | 否 | 示例：`10` | 赛道最低商品价格上限（USD）。少用，仅当用户想找「低价产品起步门槛低」的赛道时填。 |
| `nichePeakMonthGte` | `integer` | 否 | 示例：`11` | 搜索峰值月份下限（1-12 整数）。当用户提到旺季备货、季节性选品时使用；与 Lte 配合圈定季节窗口。如 Q4 旺季填 11，仲夏 Prime Day 周边填 7。 |
| `nichePeakMonthLte` | `integer` | 否 | 示例：`12` | 搜索峰值月份上限（1-12 整数）。与 Gte 配合圈定季节窗口，例如同时填 11 和 12 表示旺季在年末两个月内的赛道。 |
| `demoGenderDominant` | `string` | 否 | 最长 1000；示例：`female`, `male`, `mixed`, `unspecified` | 性别主导（闭枚举，精确匹配）。决定营销语言基调。当用户提到「做女性市场/男性市场」「不限性别」「未明确人群」时使用。可选值（必须四选一，不允许其它取值）：female（女性主导，营销语言偏女性化）、male（男性主导）、mixed（混合人群，男女均衡）、unspecified（报告未明确性别倾向，可视为通用）。 |
| `nicheBrandCountGte` | `integer` | 否 | 示例：`5` | 活跃品牌数下限（整数）。当用户希望赛道「已有一定品牌参与」，避免过度小众/垃圾赛道时填。 |
| `nicheBrandCountLte` | `integer` | 否 | 示例：`20` | 活跃品牌数上限（整数）。当用户提到「新人友好」「低竞争」「品牌少」「避开寡头」时使用；这是判断竞争密度最直接的字段，越低代表越易切入。 |
| `demoPrimaryAgeMaxGte` | `integer` | 否 | 示例：`55` | 主人群年龄上界的最小值（岁，0-120）。少用，仅当用户希望「覆盖到中老年」「年龄段够宽」时填。 |
| `demoPrimaryAgeMaxLte` | `integer` | 否 | 示例：`45` | 主人群年龄上界的最大值（岁，0-120）。当用户提到「目标人群偏年轻」「避开老龄人群」时使用，例如填 45 表示核心人群最高年龄不超过 45 岁。 |
| `demoPrimaryAgeMinGte` | `integer` | 否 | 示例：`25` | 主人群年龄下界（岁，0-120）的最小值。当用户提到「目标年龄不低于 X 岁」「避开太年轻人群」时使用。注意是「年龄下界 ≥ X」，意思是这个赛道的核心人群最低年龄至少要到 X 岁。 |
| `demoPrimaryAgeMinLte` | `integer` | 否 | 示例：`20` | 主人群年龄下界的最大值（岁，0-120）。少用，仅当用户希望「赛道核心人群从年轻端开始」时填，例如填 18 表示核心年龄段从青少年起步。 |
| `demoPrimaryIncomeTier` | `string` | 否 | 最长 1000；示例：`high`, `middle_upper`, `upper_middle`, `middle`, `middle_low`, `low` | 主人群收入档（闭枚举，精确匹配）。当用户提到「高端/中产/平价」等定价相关人群定位时使用。决定赛道支持的定价天花板。可选值（必须六选一，不允许其它取值）：low（低收入/budget）、middle_low（中低收入）、middle（中产）、middle_upper（中上收入，偏好型表达）、upper_middle（上中产，偏强表达）、high（高收入/premium，含 $100k+ 家庭）。如果用户说「中上」两种写法都可，建议优先 middle_upper。 |
| `priceSweetSpotMaxUsdGte` | `number` | 否 | 示例：`30` | Sweet Spot 上限的下界（USD）。当用户希望最佳定价空间够大、有溢价想象力时填。 |
| `priceSweetSpotMaxUsdLte` | `number` | 否 | 示例：`100` | Sweet Spot 上限的上界（USD）。少用，仅当用户想「避开建议定价过高的赛道」时填。 |
| `priceSweetSpotMinUsdGte` | `number` | 否 | 示例：`10` | Sweet Spot 下限的下界（USD）。Sweet Spot 是亚马逊建议的最佳定价区间。当用户问「目标定价应该 ≥ 多少」或想确保赛道支持较高入场定价时填。 |
| `priceSweetSpotMinUsdLte` | `number` | 否 | 示例：`30` | Sweet Spot 下限的上界（USD）。当用户希望入场价不要太高、定价友好时填。 |
| `reviewNegativeTop1Topic` | `string` | 否 | 最长 1000；示例：`size` | 差评 #1 主题片段（半开放词典，模糊匹配，snake_case 小写）。当用户表达「想做尺码痛点切入」「找质量问题严重的赛道」时使用，传词根（如 size、quality、durability、leather、material、comfort）即可命中含该词根的归一化主题。常见值（仅举例，不限于此）：size_smaller_than_expected、quality_overall_generic、not_leather、breaks_easily、material_cheap_feel、comfort_overall_generic、durability_low。Agent 应根据用户具体诉求传最有信号的词根，模糊匹配会自动覆盖语义相近的归一标签。 |
| `reviewNegativeTop2Topic` | `string` | 否 | 最长 1000；示例：`leather` | 差评 #2 主题片段（半开放词典，模糊匹配，snake_case 小写）。Top1 常为通用大类（如 quality_overall_generic），Top2 通常是具体可操作的痛点；当用户想找「具体痛点」而非「通用质量问题」时优先用本字段。常见值（仅举例，不限于此）：not_leather、breaks_easily、size_smaller_than_expected、odor_strong、color_inaccurate、battery_short。 |
| `reviewPositiveTop1Topic` | `string` | 否 | 最长 1000；示例：`comfort` | 好评 #1 主题片段（半开放词典，模糊匹配，snake_case 小写）。当用户想「找以舒适度/性价比/质量驱动的好评赛道」作为卖点参考时使用。常见值（仅举例，不限于此）：quality_overall_generic、comfort_overall_generic、works_good、value_good、easy_to_use、looks_good、durability_high。 |
| `searchTopCategory1Label` | `string` | 否 | 最长 1000；示例：`set_kit` | 搜索流量第一类目标签片段（半开放词典，模糊匹配，snake_case 小写）。表达赛道的「消费形态」——用户主要按什么维度搜索。当用户提到「想做套装/兼容产品/版本特定/颜色尺寸主导」等消费形态相关诉求时使用。常见值（仅举例，不限于此）：core_product_terms（核心产品词主导）、branded_searches（品牌词主导）、set_kit_configurations（套装/工具包）、version_specific_compatibility（版本/型号兼容）、alternative_placements（替代部位/用法）、size_specific（尺寸特定）、color_specific（颜色特定）、seasonal_specific（季节特定）。Agent 也可以根据用户诉求生成新的 snake_case 标签（如 gender_specific、material_specific）。 |
| `featureTopBrandsContains` | `string` | 否 | 最长 1000；示例：`Beetles` | Top 3 品牌名片段（模糊匹配，大小写不敏感）。当用户想找「含某品牌的赛道」「跟踪竞品所在赛道」时使用，传品牌名或可识别的片段即可（如 Beetles、whoop、anker）。不需要确切官方拼写，传 anker 也能命中 AnkerPro。 |
| `demoLifeStageTagsContains` | `string` | 否 | 最长 1000；示例：`parent` | 主人群生命阶段标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。表达「年龄+性别之外」的人群信息（同样 30 岁，新手父母 vs 单身职业人士的产品偏好完全不同）。当用户表达「做妈妈赛道」「学生群体」「退休人群」「健身爱好者」等时使用。常见值（仅举例，不限于此）：parent（父母）、new_parent（新手父母）、professional（职场人士）、student（学生）、retiree（退休）、empty_nester（空巢）、gift_buyer（送礼场景）、athlete（运动员）、fitness_enthusiast（健身爱好者）、homemaker（居家主妇/夫）。Agent 可根据用户诉求生成新的 snake_case 标签（如 pet_owner、frequent_traveler）。 |
| `nichePeakSearchVolumeAtLeastGte` | `integer` | 否 | 示例：`100000` | 峰值月搜索量下限（非负整数）。当用户希望赛道「流量天花板足够高」「旺季单月够能打」时使用，是流量上限的硬门槛。 |
| `nichePeakSearchVolumeAtLeastLte` | `integer` | 否 | 示例：`1000000` | 峰值月搜索量上限（非负整数）。少用，仅当用户想避开过热赛道时填。 |
| `priceMidClickSharePctAtLeastGte` | `number` | 否 | 示例：`30` | 中档点击份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「中档已经成立」的赛道时填。 |
| `priceMidClickSharePctAtLeastLte` | `number` | 否 | 示例：`5` | 中档点击份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「中档蓝海」「中价位机会」「现有产品两极化（要么便宜要么贵）」时使用，配合 priceEntryClickSharePctAtLeastGte 一起表达「低价主导但中档稀缺」。 |
| `reviewNegativeTop1PctAtLeastGte` | `number` | 否 | 示例：`70` | 差评 #1 主题在负面评论中的占比下限（输入 N 表示 N%，取值范围 0-100，不是总评论占比）。当用户提到「主导痛点」「痛点集中」「痛点强烈」时使用，配合 reviewNegativeTop1Topic 一起表达「找尺码痛点强烈到 ≥70% 的赛道」。 |
| `reviewNegativeTop1PctAtLeastLte` | `number` | 否 | 示例：`50` | 差评 #1 主题占比上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「痛点不那么集中、相对均匀」的赛道时填。 |
| `reviewPositiveTop1PctAtLeastGte` | `number` | 否 | 示例：`70` | 好评 #1 主题在正面评论中的占比下限（输入 N 表示 N%，取值范围 0-100，不是总评论占比）。当用户提到「主导卖点」「卖点集中」「明确卖点」时使用；高占比意味着 listing 文案应当把这个主题放主图。 |
| `reviewPositiveTop1PctAtLeastLte` | `number` | 否 | 示例：`50` | 好评 #1 主题占比上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「卖点分散，需要多角度表达」的赛道时填。 |
| `featureEmergingTrendTagsContains` | `string` | 否 | 最长 1000；示例：`cordless` | 新兴趋势特征标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想「提前布局新形态」「跟风口产品」时使用。常见值（仅举例，不限于此）：cordless（无线）、portable（便携）、eco_friendly（环保）、smart（智能）、app_connected（APP 联动）、wireless（无线）、rechargeable（可充电）、sustainable（可持续）、modular（模块化）。Agent 可根据用户诉求生成新的 snake_case 标签。 |
| `nicheRevenue360dMaxUsdAtLeastGte` | `number` | 否 | 示例：`1000000` | 市场营收上界（USD）的最小值，含。当用户希望赛道有较高营收天花板时填，配合 Min 字段判断市场规模区间。比如用户说「赛道上限要够大」。 |
| `nicheRevenue360dMaxUsdAtLeastLte` | `number` | 否 | 示例：`5000000` | 市场营收上界（USD）的最大值，含。少用，仅当用户明确要排除大赛道时填。 |
| `nicheRevenue360dMinUsdAtLeastGte` | `number` | 否 | 示例：`500000` | 市场营收下界（USD）的最小值，含。当用户表达「市场规模至少要 X 美元」时使用，只关心市场规模底线时填这一侧；通常和 nicheRevenue360dMaxUsdAtLeastGte 二选一即可。源文本带 + 表示真实值 ≥ 该数（如 $110k+ → 110000）。 |
| `nicheRevenue360dMinUsdAtLeastLte` | `number` | 否 | 示例：`200000` | 市场营收下界（USD）的最大值，含。少用，仅当用户想「排除市场规模下界过高的赛道」（小赛道偏好者）时填。 |
| `priceHighClickSharePctAtLeastGte` | `number` | 否 | 示例：`25` | 高端档点击份额下限（输入 N 表示 N%，取值范围 0-100）。当用户想做「品牌溢价产品」「高端定位」「有付费意愿的人群」时使用，数值越高代表赛道支撑高价能力越强。 |
| `priceHighClickSharePctAtLeastLte` | `number` | 否 | 示例：`10` | 高端档点击份额上限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想避开「过度高端化」的赛道时填。 |
| `priceEntryClickSharePctAtLeastGte` | `number` | 否 | 示例：`70` | 入门档点击份额下限（输入 N 表示 N%，取值范围 0-100）。当用户想找「低价主导」「价格敏感人群驱动」的赛道时填高值。这是档位主导信号，回答「消费者的注意力是否集中在低价档」。 |
| `priceEntryClickSharePctAtLeastLte` | `number` | 否 | 示例：`50` | 入门档点击份额上限（输入 N 表示 N%，取值范围 0-100）。少用，配合 mid/high 档反推时偶尔填。 |
| `featureNewAvgReviewCountAtLeastGte` | `integer` | 否 | 示例：`200` | 新品平均评论量下限（非负整数）。少用，仅当用户想找「新品已经积累起来」的成熟赛道时填。 |
| `featureNewAvgReviewCountAtLeastLte` | `integer` | 否 | 示例：`500` | 新品平均评论量上限（非负整数）。当用户提到「新人友好」「新品进入门槛低」「不用刷太多评论」时使用，是切入难度的核心指标。 |
| `featureTop5BrandSharePctAtLeastGte` | `number` | 否 | 示例：`70` | Top5 品牌合计份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「品牌寡头」「头部品牌瓜分市场」赛道时填高值。注意与 nicheTop5ProductClickSharePctAtLeast（产品级）区分：本字段是品牌级集中度，二者可同时存在分歧（如品牌分散但产品集中=私域品牌堆 SKU）。 |
| `featureTop5BrandSharePctAtLeastLte` | `number` | 否 | 示例：`60` | Top5 品牌合计份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「品牌分散」「无寡头」「新品牌易切入」时使用。常和 nicheTop5ProductClickSharePctAtLeast（产品级集中度）配合：品牌分散 + 产品集中 = 品牌延伸切入机会。 |
| `featureUncommonFeatureTagsContains` | `string` | 否 | 最长 1000；示例：`hema_free` | 稀有差异化特征标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想找「行业里少见但有亮点的差异化特征」「有供应链优势可发挥差异化」赛道时使用。常见值（仅举例，不限于此）：hema_free（无 HEMA）、medical_grade_silicone（医疗级硅胶）、bpa_free（无 BPA）、waterproof（防水）、foldable（可折叠）、magnetic_clasp（磁吸扣）、led_indicator（LED 指示）、fda_approved（FDA 认证）。Agent 可根据用户诉求生成新的 snake_case 标签（如 vegan、odor_free、anti_microbial）；传词根即可命中含该词根的归一化标签。 |
| `reviewStrategicInsightTagsContains` | `string` | 否 | 最长 1000；示例：`material_transparency` | 评论策略建议标签片段（半开放词典，模糊匹配，大小写不敏感，snake_case 小写）。当用户想「通过 Listing 优化或产品改良切入」赛道时使用，本字段表达「赛道适合靠什么角度做差异化 listing」。常见值（仅举例，不限于此）：sizing_clarity（尺码沟通清晰化）、material_transparency（材质透明化）、durability_enhancement（耐用性强化）、safety_proactive（主动安全沟通）、comfort_positioning（舒适度定位）、value_bundle（套装/超值组合）、brand_trust（品牌信任建设）。Agent 可根据具体场景生成新的 snake_case 标签。 |
| `nicheBrandCountYoyChangePctAtLeastGte` | `number` | 否 | 示例：`20` | 品牌数同比变化率下限（%，带符号）。少用，仅当用户想找「品牌正在涌入的热门赛道」时填正数。 |
| `nicheBrandCountYoyChangePctAtLeastLte` | `number` | 否 | 示例：`0` | 品牌数同比变化率上限（%，带符号）。当用户提到「品牌退出」「老玩家撤退」「新人切入机会」时使用；填 0 表示品牌数未增长，填负数表示品牌净缩减赛道（典型的反向选品信号）。 |
| `nicheSearchVolumeYoyChangePctAtLeastGte` | `number` | 否 | 示例：`100` | 搜索量同比变化率下限（输入 N 表示 N%，取值范围 -100 及以上，带符号）。当用户提到「增长型赛道」「高增长」「上升趋势」时使用；填正数表示增长门槛（100=同比翻倍）。本字段是「增长动能」信号的核心入口。 |
| `nicheSearchVolumeYoyChangePctAtLeastLte` | `number` | 否 | 示例：`0` | 搜索量同比变化率上限（输入 N 表示 N%，取值范围 -100 及以上，带符号）。少用，仅当用户想「避开增长过热」或「找衰退赛道」时填；后者填 0 即可（搜索量未增长）。 |
| `nicheTop5ProductClickSharePctAtLeastGte` | `number` | 否 | 示例：`70` | Top5 产品点击份额下限（输入 N 表示 N%，取值范围 0-100）。少用，仅当用户想找「产品端高度集中」的赛道（典型如想做白牌跟卖时找寡头赛道）时填高值。 |
| `nicheTop5ProductClickSharePctAtLeastLte` | `number` | 否 | 示例：`40` | Top5 产品点击份额上限（输入 N 表示 N%，取值范围 0-100）。当用户提到「避开寡头」「产品分散」「单品不集中」时使用；这是产品级集中度的核心反向指标，与 featureTop5BrandSharePctAtLeast（品牌级）互补。 |
| `featureEstablishedAvgReviewCountAtLeastGte` | `integer` | 否 | 示例：`5000` | 成熟老品平均评论量下限（非负整数）。少用，仅当用户特别想找「头部壁垒高的成熟赛道」（避开早期赛道）时填。 |
| `featureEstablishedAvgReviewCountAtLeastLte` | `integer` | 否 | 示例：`5000` | 成熟老品平均评论量上限（非负整数）。当用户提到「头部壁垒不高」「有机会撼动头部」「老品评论也不多」时使用。配合 New 字段一起用可以判断「赛道整体年轻 vs 成熟」。 |


## MCP 调用示例

向以下地址发起 HTTP `POST`：

```text
https://mcp-tool-gateway.linkfox.com/mcp/any-tool
```

请求体：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "/amazon/opportunity/searchByMetrics",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 提示信息。成功为 ok。 |
| `code` | `string` | 否 |  | 响应码。成功为 200。 |
| `data` | `array<object>` | 否 |  | 命中关键词指标列表。每条等于 1 个 (站点, 关键词) 的完整 37 字段记录；按报告采集时间倒序。 |
| `type` | `string` | 否 |  | 响应类型。前端按 tableListWorkbenches 渲染表格。 |
| `columns` | `array<object>` | 否 |  | 表格列定义。用于按 BusinessInsightMertrics 字段渲染指标结果。 |
| `costTime` | `integer` | 否 |  | 处理耗时，单位毫秒。 |
| `costToken` | `integer` | 否 |  | token 消耗量。 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `keyword` | `string` | 否 |  | 关键词.原始搜索关键词，用于反向追溯报告来源。 |
| `nicheName` | `string` | 否 |  | 赛道名称.归一化赛道名称，适合按赛道做时序对比。 |
| `priceMaxUsd` | `number` | 否 |  | 最高价.赛道整体最高商品价格，单位 USD。 |
| `priceMinUsd` | `number` | 否 |  | 最低价.赛道整体最低商品价格，单位 USD。 |
| `amazonDomain` | `string` | 否 |  | 站点.亚马逊站点代码，当前固定 US。 |
| `nichePeakMonth` | `integer` | 否 |  | 峰值月份.年内搜索峰值月份，取值范围 1-12。 |
| `nicheBrandCount` | `integer` | 否 |  | 品牌数.活跃品牌数量，数值越小通常竞争密度越低。 |
| `featureTopBrands` | `array<any>` | 否 |  | Top3品牌.核心品牌名列表，按出现顺序返回。 |
| `demoLifeStageTags` | `array<any>` | 否 |  | 生命阶段标签.核心人群的生命阶段或生活状态标签。 |
| `demoPrimaryAgeMax` | `integer` | 否 |  | 最高年龄.核心人群最高年龄，单位岁。 |
| `demoPrimaryAgeMin` | `integer` | 否 |  | 最低年龄.核心人群最低年龄，单位岁。 |
| `demoGenderDominant` | `string` | 否 |  | 性别主导.核心人群性别倾向，可选值为 female、male、mixed、unspecified。 |
| `priceSweetSpotMaxUsd` | `number` | 否 |  | 建议最高价.Value Sweet Spot 价格区间最高值，单位 USD。 |
| `priceSweetSpotMinUsd` | `number` | 否 |  | 建议最低价.Value Sweet Spot 价格区间最低值，单位 USD。 |
| `demoPrimaryIncomeTier` | `string` | 否 |  | 收入档.核心人群收入档，可选值为 low、middle_low、middle、middle_upper、upper_middle、high。 |
| `reviewNegativeTop1Topic` | `string` | 否 |  | 差评主因.负面评论中最主要的归一化主题。 |
| `reviewNegativeTop2Topic` | `string` | 否 |  | 差评次因.负面评论中第二主要的归一化主题。 |
| `reviewPositiveTop1Topic` | `string` | 否 |  | 好评主因.正面评论中最主要的归一化主题。 |
| `searchTopCategory1Label` | `string` | 否 |  | 搜索形态.流量第一类目归一化标签，表达用户主要按什么维度搜索。 |
| `featureEmergingTrendTags` | `array<any>` | 否 |  | 趋势特征.行业内新出现的产品形态或功能趋势标签。 |
| `featureUncommonFeatureTags` | `array<any>` | 否 |  | 稀有特征.行业中较少产品具备的差异化功能、材质或规格标签。 |
| `reviewStrategicInsightTags` | `array<any>` | 否 |  | 评论策略标签.基于评论洞察生成的 Listing 优化或产品改良方向标签。 |
| `nichePeakSearchVolumeAtLeast` | `integer` | 否 |  | 峰值月搜索量.峰值月份搜索量下界，越高代表旺季流量天花板越高。 |
| `priceMidClickSharePctAtLeast` | `number` | 否 |  | 中档份额.中档价格点击份额百分比，取值范围 0-100。 |
| `reviewNegativeTop1PctAtLeast` | `number` | 否 |  | 差评主因占比.差评主因在负面评论中的占比，取值范围 0-100。 |
| `reviewPositiveTop1PctAtLeast` | `number` | 否 |  | 好评主因占比.好评主因在正面评论中的占比，取值范围 0-100。 |
| `nicheRevenue360dMaxUsdAtLeast` | `number` | 否 |  | 最高营收.近 360 天市场营收最高估值，单位 USD；越高代表赛道流水天花板越高。 |
| `nicheRevenue360dMinUsdAtLeast` | `number` | 否 |  | 最低营收.近 360 天市场营收最低估值，单位 USD；源文本带 + 时表示真实值不低于该数。 |
| `priceHighClickSharePctAtLeast` | `number` | 否 |  | 高端档份额.高端价格档点击份额百分比，取值范围 0-100。 |
| `priceEntryClickSharePctAtLeast` | `number` | 否 |  | 入门档份额.入门价格档点击份额百分比，取值范围 0-100。 |
| `featureNewAvgReviewCountAtLeast` | `integer` | 否 |  | 新品评论数.新品平均评论量下界，非负整数。 |
| `featureTop5BrandSharePctAtLeast` | `number` | 否 |  | Top5品牌份额.头部品牌合计份额百分比，取值范围 0-100。 |
| `nicheBrandCountYoyChangePctAtLeast` | `number` | 否 |  | 品牌数同比.百分比，正值表示品牌涌入，负值表示品牌净减少。 |
| `nicheSearchVolumeYoyChangePctAtLeast` | `number` | 否 |  | 搜索量同比.百分比，100 表示同比增长 100%，-20 表示同比下降 20%。 |
| `nicheTop5ProductClickSharePctAtLeast` | `number` | 否 |  | Top5产品份额.点击份额百分比，取值范围 0-100，用于判断产品级集中度。 |
| `featureEstablishedAvgReviewCountAtLeast` | `integer` | 否 |  | 成熟品评论数.成熟老品平均评论量下界，非负整数。 |

## 响应处理建议

1. 先检查 JSON-RPC 外层是否包含 `error`。
2. 成功时读取 `result`，并继续解析其中的 `content`、`data`、`products`、`items` 或其他业务字段。
3. 如果响应为 `text/event-stream`，按 SSE 事件读取 `data:` 内容，再解析 JSON。
4. 保留分页字段、总数、失败明细及 `costToken`。
5. 向用户输出分析结论，不要直接倾倒大段原始 JSON。

## 原始 Schema

原始的Input Schema 和 Output Schema 参考 references/schema.md

## 解决认证和积分问题

异常情况：未配置 `LINKFOX_AGENT_API_KEY` 和 `LINKFOXAGENT_API_KEY`；响应 401 或 402；消息含"积分余额不足/quota exceeded/insufficient balance/套餐到期/需充值"等。

措施：优先用 skill 内 onboarding.md 引导；找不到则加载 /linkfox-onboarding skill。 根据它的指引操作。

**注意**：你是workbuddy，并且渠道是workbuddy，使用linkfox-onboarding登录注册时**必须**传递channel为 workbuddy。这非常重要！
