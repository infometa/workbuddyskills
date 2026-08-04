# 竞品对标 / 店铺分析 / 广告调研 SOP

目标：摸清竞争对手的商品、店铺、投放打法，产出竞争格局分析。

## 三种切入维度

### A. 从商品切入（用户给了一个竞品）

1. search(entity="products") 按名称定位拿到 id（用户只给了名字时）
2. get_detail(products, id, country) — 销量趋势、价格、SKU 策略
3. get_related(products, id, "similar", country) — 同类竞品矩阵，看价格带分布
4. get_related(products, id, "creators", country) — 竞品的达人矩阵（可直接挖角）
5. get_related(products, id, "videos", country) — 竞品的爆款内容打法

### B. 从店铺切入（分析一个卖家）

1. search(entity="sellers", country, keyword=店铺名) 定位
2. get_detail(sellers, id, country, include="core,channel") — 总 GMV、商品数、评分、渠道结构
3. get_related(sellers, id, "products", country) — 店铺商品结构：主推款 vs 长尾款，哪些在起量
4. get_related(sellers, id, "creators", country) — 店铺合作的达人网络
5. get_related(sellers, id, "videos", country) — 店铺内容营销打法

### C. 从广告切入（调研投放素材）

1. search(entity="ads", country, keyword=类目词, filters={"ad_type": 1}) — 锁定 TikTok Shop 广告（其他 ad_type 取值见工具说明）
2. get_detail(ads, id, country) — 单条广告的投放时长、消耗量级、互动数据
3. search(entity="creatives", ...) + get_detail(creatives, id, country, include="analysis") — 素材层面的表现分析（GPM、完播、互动）
4. 值得拆解的素材：ai_generate(type="script_breakdown", params={"video_id": 视频id}) 拆口播结构 → 给用户做二创参考。video_id 优先用素材结果里的视频 id 字段；拆解报 video_id 无效时，先 search(entity="videos") 定位对应视频拿 id 再拆

## 产出

按用户的问题组织，常见两种：

- **竞品矩阵表**：竞品名 | 价格 | 近30天销量/GMV | 评分 | 达人数 | 内容打法一句话
- **单店铺深度报告**：店铺概况 → 商品结构 → 达人网络 → 内容/投放打法 → 对我们的启示（可切入的缺口）

结论落在"对用户的可执行启示"上，不要只罗列数据。

## 注意

- 广告消耗、GMV 均为平台估算值，报告里注明"估算"
- 竞品分析常需要跨 entity 组合（商品→店铺→广告），一步步来，每步先看上一步结果再决定下一步
