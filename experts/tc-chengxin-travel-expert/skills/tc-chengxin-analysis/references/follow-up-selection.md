# 复用本次结果继续筛选

只在同一对话已经交付 `direct_render`，且用户只补充筛选偏好、比较目标或询问本次结果时使用。正文会按资源类型给出“优先便宜、少换乘、只看直飞、距离近、适合亲子”等自然示例，也允许直接说“帮我综合解读推荐”；不要要求内部固定口令。

使用上轮回执的 `snapshotFilePath`，把用户本轮原话完整传入：

    node "<本 Skill Base directory>/scripts/analyze-existing-snapshot.js" --snapshot "<上轮 snapshotFilePath>" --request "<用户本轮原话>"

脚本只读取、校验原结果并生成决策页，不调用查询接口或授权。收到回执后按 `allowedReads`、`allowedCalls` 和 `quickPlanTemplate` 一次写 plan、渲染和交付；不要先自行解释一版。

以下情况重新查询而不是复用：用户改变地点、方向、日期或查询对象；明确要求“现在、最新、重新查、还有没有、能否预订”；原 `snapshotFilePath` 已不可访问。只有补充价格、时间、换乘、席别、距离、评分、人群等偏好时才复用。
