# 能力与工具索引（Kuaizi-Atom 视频商业工具栈 · 32 能力 / 120 工具）

> 工具与说明由网关 tools/list 全量生成（2026-10-29），不截断；`kmcp_fee_confirm` 计费授权见 api-spec.md。


## 客户产品库（product-library）

| 工具 | 说明 |
|---|---|
| `context_spu_ingest` | 产品解析：按材料选 provider 读原文（链接调商品解析，文档读正文，图片先看图读成原文），再跑一轮填进产品档字段表。origin=extracted，不覆盖人工改过的字段。默认 async。 |
| `context_job_get` | 查询建资产等异步 job 状态与结果。 |
| `context_spu_upsert` | 人工写入/整份保存产品档（origin=manual）。ready 门槛 name + profile。改一个或几个属性用 context_spu_patch。不做多源抽取——那是 context_spu_ingest。 |
| `context_spu_get` | 按 spu_id 读产品档，默认拼装 SKU。view=profile／md／full 控制粒度。 |
| `context_spu_list` | 列客户名下产品档摘要（不含 profile 正文）。 |
| `context_spu_delete` | 软删产品档并级联软删其 SKU；列表不再出现，行保留。重复删 / 找不到返回 NOT_FOUND。 |
| `context_sku_upsert` | 无 sku_id 则新建，有则更新。抽取入库一律新建、不做同名匹配，重复由 context_sku_delete 清理。 |
| `context_sku_list` | 按 spu_id / batch_id 列 SKU，供删除页面分组展示。 |
| `context_sku_delete` | 客户删重复 SKU；该 SKU 的字段元数据随行一起删除。 |

## 客户 IP（customer-ip）

| 工具 | 说明 |
|---|---|
| `context_ip_list` | 列客户名下 IP 摘要与就绪状态。 |
| `context_ip_get` | 按 ip_id 读 IP，含 look_ready / voice_ready 两个维度。 |
| `context_ip_upsert` | 写入 IP（人物·声音·性格·作品）并按需建形象/音色资产。默认 async，返回 job_ids[]。 |
| `context_ip_review` | 形象或声音的审核。submit 提审，approve 标成已过审，reject 标成未过审。形象提审后才会去建资产。 |
| `context_job_get` | 查询建资产等异步 job 状态与结果。 |
| `token_generate_video` | prompt/visual_desc → 异步 task_id；可带参考图和参考视频（reference_video_url）。完成态用 token_job_get 取 video_url。 |
| `token_job_get` | payload.task_id + 可选 kind=image／video／rig／enhancement；返回 status 与 image_url/video_url/file_url 和 cost。增强任务须传 kind=enhancement。 |
| `context_ip_delete` | 软删 IP；列表不再出现，行保留。重复删 / 找不到返回 NOT_FOUND。 |

## 客户资料库（customer-assets）

| 工具 | 说明 |
|---|---|
| `context_material_ingest` | 登记原始图片/视频 + 归属。不切片/不打标/不召回（那是 mcp-asset），也不代为触发处理。 |
| `context_material_list` | 按归属（spu_id/ip_id/batch_id）与文件名筛选。无语义检索——语义召回在 mcp-asset。 |
| `context_material_get` | 按 material_id 读原料记录。 |
| `context_material_delete` | 软删客户资料库素材；列表不再出现，行保留。 |

## 智能素材清洗（asset-cleaning）

| 工具 | 说明 |
|---|---|
| `vproc_subtitle_erase` | 擦除视频中的字幕，支持 v4/v5 算法。v5 优化 AIGC 生成视频字幕擦除后的闪烁问题与带阴影字幕擦除效果，优化误擦问题，并提升处理速度。默认 Subtitle 模式只处理画面下半部分（Y≥0.5）；要擦左上角水印/台标等固定元素时用 mode=Text + erase_ratio_location 框选。 |
| `vproc_enhance` | 对已有成片做画质增强/超分（异步）。payload.video_url 必填且须是公网可直连的 http(s) 地址——本枢纽不做转存，file_id/内网地址不支持。分辨率二选一：resolution（720p/1080p/2k/4k 固定档）或 resolution_limit（短边像素 64–2160）；fps 可选（≤120，0/不传=保持原帧率）；tool_version=standard(默认)/professional，scene（aigc/short_series/ugc/old_film）仅 standard 生效，professional 下会被忽略并标 scene_ignored。提交返回 job_id，用 vproc_job_get 轮询，终态产物在 data.data.video_url。按视频秒数计费，只在 succeeded 时收。 |
| `vproc_transcode_video` | 将视频转码为指定编码格式（H.264/H.265）和分辨率的输出。按输出时长 × 换算系数计费，系数依赖编码格式与输出分辨率档位。 |
| `vproc_job_get` | 按 payload.job_id 查询本枢纽异步任务状态（pending/running/succeeded/failed/expired）。自动轮询下游并回写本地 job；终态后再次调用直接回缓存。产物在 data.data（注意是两层 data），超分为 data.data.video_url。未完成时返回 failed(JOB_NOT_DONE)，供 SOP expect 自动重试。同步。 |

## 素材理解（asset-understanding）

| 工具 | 说明 |
|---|---|
| `asset_material_submit` | 投喂素材（对齐 SubmitMaterial）：登记即返回真实 material_id + task_id，后台异步流水线理解（INGEST→SPLIT→ASR→UNDERSTAND→TAG→INDEX→DONE），由 asset_job_get 轮询终态；(tenant, biz_id) 幂等返回 duplicated（tenant 由平台从 ctx.enterprise_id 解析，调用方只需管 biz_id）。file_id 须为 filestore 数字 ID。可选 custom_tags：业务方自定义标签 [{key,value}]（≤100 对，key ≤64 字符、value ≤512 字符；随素材进向量库，可用 query 语义召回 value）。 |
| `asset_material_get` | 查素材（对齐 GetMaterial）：按 material_id 实时返回素材 + 处理状态 + 当前步骤 + 切片（内嵌标签/理解）。 |

## 智能标签（smart-tags）

| 工具 | 说明 |
|---|---|
| `asset_material_get` | 查素材（对齐 GetMaterial）：按 material_id 实时返回素材 + 处理状态 + 当前步骤 + 切片（内嵌标签/理解）。 |
| `asset_custom_label_create` | 新增自定义标签字典词条（对齐 CreateCustomLabel）：namespace+label 均必填；tenant 由平台从 ctx.enterprise_id 解析，调用方无需也不能传。同一 tenant+namespace 下重复创建会失败。 |
| `asset_custom_label_retag` | 触发该标签的存量切片补打标（对齐 TriggerRetagLabel）：异步执行，只负责投递任务，不等待扫描完成，也没有进度查询接口。 |
| `asset_custom_label_list_segments` | 按标签查询命中的切片列表（对齐 ListSegmentsByLabel）：纯 MySQL 精确匹配查询，不是语义召回，不支持模糊搜索。 |
| `asset_custom_label_list` | 列出 namespace 下的自定义标签字典（对齐 ListCustomLabels，tenant 由平台解析），不分页。 |
| `asset_custom_label_delete` | 物理删除自定义标签字典词条，并级联清空该标签下的全部命中记录（对齐 DeleteCustomLabel，不可逆）。 |

## 向量语义检索召回（semantic-search）

| 工具 | 说明 |
|---|---|
| `asset_search` | 向量语义召回（对齐 SearchMaterial）：语义 query + 标签硬过滤（FilteredANN）→ 重排 topN 命中（segment + material + score + matched_tags）。 |
| `asset_search_batch` | 按 beats[] 批量语义召回（替换 kclaw beats_recall）：每格用 visual_intent/visual_desc/vo 派 query，写入 beat.video_url 与 shots；continue_on_fail 默认 true。 |

## 品类爆款视频（hot-videos）

| 工具 | 说明 |
|---|---|
| `nx_list_benchmark_categories` | 返回品类对标用的带货分类树（蝉妈妈分类，全量 14751 节点、最大深度 5）。每节点 {id, label, sub}，sub 为空表示叶子。静态数据，无入参条件；品类 id 用于后续账号/视频列表接口的 category 入参。 |
| `nx_list_benchmark_videos` | 按品类/产品语义向量召回对标视频（search-api VikingDB，对齐 ref_matrix_topn）。入参 platform/category 必填；searchKeywords 可选（传了跳过品类转换）；product_name 可选（启用 B+C 过滤：产品名命中 + 分数联合）。直接返回，不落库。 |
| `nx_list_search_channels` | 返回 nx_search_content 当前支持的检索渠道目录（静态数据）。每项含 channel（入参 id）/ name_cn（中文名）/ platform / icon / kind（video／article，决定检索结果结构）/ enabled / description。 |
| `nx_search_content` | 按关键词 + 渠道从向量库/知识库检索相关内容。channel=douyin 返回相关视频列表（search-api topn 语义召回）；channel=winshang/canyin88 返回行业文章（VikingDB 文本召回 + 时间过滤，默认 180 天）；channel=douhot 按抖音话题 id（challenge_id）取热点话题热榜视频（透传 crawl-api，固定约 30 条、无分页）。用 nx_list_search_channels 查询全量渠道目录。 |

## 对标账号（account-benchmark）

| 工具 | 说明 |
|---|---|
| `nx_list_benchmark_categories` | 返回品类对标用的带货分类树（蝉妈妈分类，全量 14751 节点、最大深度 5）。每节点 {id, label, sub}，sub 为空表示叶子。静态数据，无入参条件；品类 id 用于后续账号/视频列表接口的 category 入参。 |
| `nx_list_benchmark_accounts` | 按品类/产品语义向量召回对标账号。数据流：topn 召回作品 → 每条 vid 调作品详情接口拿作者信息 → 用 unique_id 匹配 author_full 拿 author_id（匹配不到为空）。返回账号含 sec_uid/uid/unique_id/nickname 等；只有 author_id 非空才能调 nx_get_benchmark_account_profile。 |
| `nx_list_benchmark_account_videos` | 按 sec_uid 从向量库（VikingDB）召回账号视频列表。直连 VikingDB 数据面（search_by_scalar + f_author_sec_uid 标量过滤，精确匹配），不走 search-api网关（其 filter 不支持 sec_uid）。 |
| `nx_get_benchmark_account_profile` | 按 author_id 查达人画像（蝉妈妈 infoExtend，crawl-api author-detail）。返回 aweme/common/live 三块原始数据（作品/通用/直播画像摘要），由调用方自行取用。 |

## 行业热点（industry-trends）

| 工具 | 说明 |
|---|---|
| `ref_hot_topics` | 按社媒热点话题给构思提供「可关联」的参考（只作关联可能性，不要硬插进脚本）。 怎么选参（二选一）： 1) 已知品类/产品/话题 → 传 query 或 category（例如 "保健品"）。按意思找相关热点。 2) 只想看最近在热什么 → 不要传 query/category，可只传 top_k。刷最近一批（自动避开衰退期与高风险）。 可选：top_k（默认10）、start_time/end_time（unix秒）、platform_list、min_score（仅关键词检索）、max_risk_level（仅刷列表，默认1）。 返回 data.list[]：title/desc/platform/hot_value/category_list/tags/trend/score 等；data.lookup 标明本次是 by_keyword 还是 recent_list。 |
| `ref_matrix_topn` | 品类名→LLM 品类转换→VikingDB 向量召回；落 hit_batch（含口播/OCR/粗标签/互动/作者/CDN 透传）。不做自建下载。若 payload 已带 searchKeywords 则跳过品类转换。 |

## 流量 IP（traffic-ip）

| 工具 | 说明 |
|---|---|
| `ref_hot_topics` | 按社媒热点话题给构思提供「可关联」的参考（只作关联可能性，不要硬插进脚本）。 怎么选参（二选一）： 1) 已知品类/产品/话题 → 传 query 或 category（例如 "保健品"）。按意思找相关热点。 2) 只想看最近在热什么 → 不要传 query/category，可只传 top_k。刷最近一批（自动避开衰退期与高风险）。 可选：top_k（默认10）、start_time/end_time（unix秒）、platform_list、min_score（仅关键词检索）、max_risk_level（仅刷列表，默认1）。 返回 data.list[]：title/desc/platform/hot_value/category_list/tags/trend/score 等；data.lookup 标明本次是 by_keyword 还是 recent_list。 |
| `nx_list_hot_ip_tags` | 热点 IP 的标签目录（人物/品牌/影视/歌曲等），每条含标签名、词形别名、该标签下 IP 数、起止日期；标签是 nx_hot_ip 的 payload.tag 合法取值，用它做话题选题/脚本构思时先拉目录再按标签取 IP。 |
| `nx_hot_ip` | 按标签取最近的热点 IP（人物/品牌/影视/歌曲等 IP 及其关联话题、热度、人群画像），给选题/脚本构思做参考。tag 可选（如「明星」「品牌」「影视」，不传则返回全部 IP 按热度前 top_k，完整标签目录用工具 nx_list_hot_ip_tags 或 crawl-api GET /api/douhot-ip/tags）；也可直接传 ip（如「刘亦菲」）精确查单个 IP 的信息（忽略 tag）；top_k 可选（默认10上限50）。 |
| `ref_hot_topics_judge` | 从一批热点里判定能不能和当前产品软关联（提示词模板默认 #190）。 入参：payload.candidates 为热点列表原样（ref_hot_topics 的 list）；payload.spu_id 用来自取品牌、产品名和禁说。 品类、品牌、产品、禁说、表达偏好也可以直接放在 payload 里，有值就以 payload 为准。 出参 data.selected：judged、can_associate、picked_title、soft_hook、hotspot_line。 不能关联时 hotspot_line 为空。没有候选时不调模型，直接返回不可关联。 |
| `ref_matrix_keywords` | 品类名→prompt_manager「品类转换检索条件」→ searchKeywords。供调试台先看词；topn 也可内嵌同路径。 |
| `ref_matrix_topn` | 品类名→LLM 品类转换→VikingDB 向量召回；落 hit_batch（含口播/OCR/粗标签/互动/作者/CDN 透传）。不做自建下载。若 payload 已带 searchKeywords 则跳过品类转换。 |

## 品类语境 & 证据链（context-evidence）

| 工具 | 说明 |
|---|---|
| `ref_matrix_parse` | 同步：从 hit_batch 投影片记录；硬过滤 item_asr 非空。不爬取、不转存、不自建 ASR。 |
| `ref_matrix_induce` | 异步：对已 parse 片记录分批 LLM 归纳内容三件套池（语境人×场×痛 / 证据链 / CTR），新 pool_id；权重为互动代理。 |
| `ref_matrix_job_get` | 查询异步 job（induce / narrative）。 |
| `ref_matrix_pool_get` | 同步：按 pool_id 精确取，或 platform+category+selector=latest。 |
| `ref_matrix_pool_filter` | 同步：按客户上文把行业母池筛成客户投影池，新建 pool_id 返回，母池原样保留可追溯。 前置条件：先跑 ref_matrix_induce 拿到母池 pool_id。 怎么用：传 pool_id（母池）+ customer（品牌/产品/受众/场景/痛点/卖点，取自 context_spu_get 的 profile.spu.*）。 入参 payload 把三池候选打下标编号交给 prompt_manager 模板 #188，模型回 keep 下标，按下标裁剪后落一个新池。 幂等性：非幂等，每次调用产生新 pool_id；母池不修改。 降级（不中断出片链，一律返回 succeeded）：客户上文为空 / 模型调用失败 / 模型把三池全筛空 / 新池落库失败， projected_pool_id 均回落为母池 id，data.skipped 标明原因。下游一律读 projected_pool_id，不要读 pool_id。 |
| `ref_matrix_pool_save` | 同步：把已算好的 keep 下标（context/evidence/ctr 三个下标数组）按母池裁成投影池并落库，返回 projected_pool_id。不跑 #188——keep 由调用方（前端本地跑过 #188，可带自定义 system）传入。供 ref_matrix_compose 等下游读 projected_pool_id，避免读到母池导致被筛掉的候选回流。 |
| `ref_matrix_compose` | 同步：抽 N 张配方（语境×1 + 证据×k + CTR×1）。证据匹配在三池归纳时预计算（抽卡不再打模型）。match_mode=llm 取预匹配最优；context 在预匹配里加权抽；none 三池独立。 |
| `ref_matrix_narrative` | 异步：配方×客户上下文/IP→叙述结构 beats（visual_intent + visual_desc + 旁白）；走 prompt_manager 平台模板（缺省 #184）或 chat 兜底生成，job_get 查结果并按 token 计费。 |
| `ref_matrix_split_beats` | 同步：规范化 beats[]（份数由列表/max_beats 控制）；兼容写出前 3 路 beat{i}_*。不调 LLM。 |

## 包装板式（packaging-template）

| 工具 | 说明 |
|---|---|
| `composition_compose` | 提交合成任务（inf-video-editor-api，内部转交 skymedia-composer）：payload.videos 必填（[{video_url, cover_url, duration?, audio_url?, audio_duration?, position?}]，≥1 段；每段可带口播，按画面时间轴对齐；position 五键 trans_x/trans_y/scale_x/scale_y/rotate 用于画中画/分屏，任一键非 0 则该段进叠加轨、与 layout_id 互斥；或 shots/beats 传分镜素材 URL 列表追加）、可选 layout_id（取 edit_layout_list，版式字幕/标题轨保真叠加）或 layout_skyjson、可选 bgm_id/bgm_url+bgm_duration（取 edit_bgm_pick）、可选 bgm_volume（BGM 音量 0.0–1.0，默认 0.4 即 -8dB，建议口播场景 0.1–0.3）、可选整条 audio_uri+audio_duration（无分段口播时兜底）、可选 title/sub_title（仅版式有标题轨时生效）、可选 captions（[{text, begin_time, end_time}]，字幕/花字句列表，与 caption_effect_id 配套）、可选 caption_effect_id（TEXT 字幕/花字素材 id，取 mcp-video-design effect_list kind=text_material 或 effect_pick；有 captions 无 caption_effect_id 时跳过字幕）、可选 width/height/frame_rate（无版式时默认 1080x1920x30）、biz_id（缺省取 customer_id）、可选 video_effect_id/video_effect_url/video_effect_path（主画面特效包，未传用服务端默认配置）。返回 job_id+ive_job_id，用 composition_job_get 轮询（终态响应为 {job_id,status,tool,data:{...,data:{url,...}}}，产物地址在 data.data.url，注意是两层 data，不是 data.url）。同 request_id 若上次失败会自动重置重跑（job_id 不变）；传 payload.retry=true 可无视旧状态强制重新提交。异步。 |
| `composition_job_get` | 按 payload.job_id 查询 edit_tts/composition_compose 异步任务状态（pending/running/succeeded/failed）。自动轮询下游（model_manager 合成状态 / inf-video-editor-api job 状态）并回写本地 job。终态后再次调用直接返回缓存。返回 job_id、tool、status、created_at、updated_at、data（终态含产物 URL）。同步。 |

## BGM 库（bgm-library）

| 工具 | 说明 |
|---|---|
| `edit_bgm_pick` | 按条件搜索背景音乐：payload.name 关键词、category_id、page/page_size、asc。返回 bgm_id、name、download_url、cover_url、duration_sec（秒）、md5、suffix、file_size。结果供 composition_compose 的 bgm_id/bgm_url+bgm_duration 使用。同步。 |

## 声音克隆（voice-clone）

| 工具 | 说明 |
|---|---|
| `edit_tts` | 提交口播文案合成配音（model_manager AudioSynthesize），返回 job_id，用 composition_job_get 轮询（终态 data.data 含 audio_url/format/duration 及 asr_result，注意是两层 data）。asr_result：句级时间戳数组，每句含 start_ms/end_ms/sub_index(固定 0)/sentence/words[]（逐字 word/start_ms/end_ms），供字幕/花字逐字对齐。入参：payload.text（必填）、voice_id（预注册音色，缺省取配置 default_voice_id；可用 effect_list kind=voice 拉取）或 references（zero-shot 声音克隆：[{audio_url:声音样本URL}]，与 voice_id 二选一）、model_key（缺省取配置）、speed(0.5–2.0)、volume(0.5–2.0)、pitch(-12–12)、format、sample_rate；version 仅透传。同 request_id 若上次失败会自动重置重跑（job_id 不变）；传 payload.retry=true 可无视旧状态强制重新提交。异步。 |
| `composition_job_get` | 按 payload.job_id 查询 edit_tts/composition_compose 异步任务状态（pending/running/succeeded/failed）。自动轮询下游（model_manager 合成状态 / inf-video-editor-api job 状态）并回写本地 job。终态后再次调用直接返回缓存。返回 job_id、tool、status、created_at、updated_at、data（终态含产物 URL）。同步。 |

## 口播 TTS（tts）

| 工具 | 说明 |
|---|---|
| `edit_tts` | 提交口播文案合成配音（model_manager AudioSynthesize），返回 job_id，用 composition_job_get 轮询（终态 data.data 含 audio_url/format/duration 及 asr_result，注意是两层 data）。asr_result：句级时间戳数组，每句含 start_ms/end_ms/sub_index(固定 0)/sentence/words[]（逐字 word/start_ms/end_ms），供字幕/花字逐字对齐。入参：payload.text（必填）、voice_id（预注册音色，缺省取配置 default_voice_id；可用 effect_list kind=voice 拉取）或 references（zero-shot 声音克隆：[{audio_url:声音样本URL}]，与 voice_id 二选一）、model_key（缺省取配置）、speed(0.5–2.0)、volume(0.5–2.0)、pitch(-12–12)、format、sample_rate；version 仅透传。同 request_id 若上次失败会自动重置重跑（job_id 不变）；传 payload.retry=true 可无视旧状态强制重新提交。异步。 |
| `composition_job_get` | 按 payload.job_id 查询 edit_tts/composition_compose 异步任务状态（pending/running/succeeded/failed）。自动轮询下游（model_manager 合成状态 / inf-video-editor-api job 状态）并回写本地 job。终态后再次调用直接返回缓存。返回 job_id、tool、status、created_at、updated_at、data（终态含产物 URL）。同步。 |

## 封面抽取与生成（cover-gen）

| 工具 | 说明 |
|---|---|
| `cover_frames_extract` | 抽帧策略 strategy：auto（默认，有 frames 则透传否则 average）/ provided（必须传 frames）/ average（video_url 先转存 kuaizi_cloud 再 GEN_SPRITE，终态删临时素材；或直接传 file_id）/ scene（分镜→每镜一帧，对齐 remix media_audit：需 video_url + duration（秒）或 duration_ms，可选 width/height/fps）。count 默认 4，count=1 即封面场景（推荐 mode=Interval）。异步时用 cover_job_get 轮询（终态 data.data 含 urls/frames 帧图列表，注意是两层 data）。 |
| `cover_generate` | 封面生成（异步）。mode=template：本地 ffmpeg 套版（frame_url + template_id 必填，可选 title/subtitle/logo_url/platform）；mode=ai：调 token_generate_image 文生图（prompt 必填）。提交返回 job_id，用 cover_job_get 轮询（终态 data.data.cover_uri）。 |
| `cover_job_get` | 按 payload.job_id 查询 cover_frames_extract / cover_generate / cover_batch 异步任务状态（pending/running/succeeded/failed）。自动轮询下游（filestore 雪碧图任务）并回写本地 job。终态后再次调用直接返回缓存。返回 job_id、tool、status、created_at、updated_at、data（终态含产物 URL）。同步。 |
| `token_generate_image` | prompt/visual_desc → 异步 task_id；完成态用 token_job_get 取 image_url。 |
| `token_job_get` | payload.task_id + 可选 kind=image／video／rig／enhancement；返回 status 与 image_url/video_url/file_url 和 cost。增强任务须传 kind=enhancement。 |

## 音视频合成（av-compose）

| 工具 | 说明 |
|---|---|
| `composition_compose` | 提交合成任务（inf-video-editor-api，内部转交 skymedia-composer）：payload.videos 必填（[{video_url, cover_url, duration?, audio_url?, audio_duration?, position?}]，≥1 段；每段可带口播，按画面时间轴对齐；position 五键 trans_x/trans_y/scale_x/scale_y/rotate 用于画中画/分屏，任一键非 0 则该段进叠加轨、与 layout_id 互斥；或 shots/beats 传分镜素材 URL 列表追加）、可选 layout_id（取 edit_layout_list，版式字幕/标题轨保真叠加）或 layout_skyjson、可选 bgm_id/bgm_url+bgm_duration（取 edit_bgm_pick）、可选 bgm_volume（BGM 音量 0.0–1.0，默认 0.4 即 -8dB，建议口播场景 0.1–0.3）、可选整条 audio_uri+audio_duration（无分段口播时兜底）、可选 title/sub_title（仅版式有标题轨时生效）、可选 captions（[{text, begin_time, end_time}]，字幕/花字句列表，与 caption_effect_id 配套）、可选 caption_effect_id（TEXT 字幕/花字素材 id，取 mcp-video-design effect_list kind=text_material 或 effect_pick；有 captions 无 caption_effect_id 时跳过字幕）、可选 width/height/frame_rate（无版式时默认 1080x1920x30）、biz_id（缺省取 customer_id）、可选 video_effect_id/video_effect_url/video_effect_path（主画面特效包，未传用服务端默认配置）。返回 job_id+ive_job_id，用 composition_job_get 轮询（终态响应为 {job_id,status,tool,data:{...,data:{url,...}}}，产物地址在 data.data.url，注意是两层 data，不是 data.url）。同 request_id 若上次失败会自动重置重跑（job_id 不变）；传 payload.retry=true 可无视旧状态强制重新提交。异步。 |
| `composition_job_get` | 按 payload.job_id 查询 edit_tts/composition_compose 异步任务状态（pending/running/succeeded/failed）。自动轮询下游（model_manager 合成状态 / inf-video-editor-api job 状态）并回写本地 job。终态后再次调用直接返回缓存。返回 job_id、tool、status、created_at、updated_at、data（终态含产物 URL）。同步。 |

## 效果和质量（quality）

| 工具 | 说明 |
|---|---|
| `qc_prepare` | 一次准备口播与抽帧，产出 bundle_id。strategy：auto（默认，上游 frames 优先否则 average）/ provided / average / scene（分镜每镜一帧，未接通）。有 frames 时不抽。 |
| `qc_review` | 按 checks 跑多维检查（默认 company+quality）。支持 persona / quality_system_prompt / quality_user_prompt；画面人设可传 bundle_id/frames + vision。输出 review_id、verdict、issues。 |
| `qc_review_get` | 按 review_id 读取完整审片记录。 |
| `qc_review_list` | 按 customer_id（必填）+ verdict/render_id/product_id/from_ms/to_ms 过滤，分页返回历史审片记录列表。分页用 limit/offset（默认 20，上限 200），回包 data.page 带 total/has_more。 |
| `qc_job_get` | 查询 qc_review async 任务状态与结果。 |

## 重复率（duplication）

| 工具 | 说明 |
|---|---|
| `composition_render_upsert` | 给一条成片（视频成品）登记或更新档案：记录视频链接、口播文案、时长、状态等信息，供后续质检审片与文案查重（按 transcript 自动算指纹，避免同文案重复成片）。render_id 已存在则更新、否则新建；video_uri 与 transcript 至少传一个。 示例——合成完成后登记一条成片： { "ctx": {"run_id": "r_1", "customer_id": "cus_1"}, "payload": { "render_id": "render_abc", "video_uri": "https://cdn.example.com/out.mp4", "duration_ms": 23400, "status": "ready", "transcript": "今天给大家介绍一款……" } } |
| `composition_render_list` | 列出某个客户（租户）名下的历史成片清单，返回每条成片的元数据。主要用于查重：新合成前调出来和历史成片对比口播文案判断是否重复；可用 exclude_render_id 排除当前这条自身。 示例： { "ctx": {"run_id": "r_1", "customer_id": "cus_1"}, "payload": {"exclude_render_id": "render_abc"} } |
| `qc_review` | 按 checks 跑多维检查（默认 company+quality）。支持 persona / quality_system_prompt / quality_user_prompt；画面人设可传 bundle_id/frames + vision。输出 review_id、verdict、issues。 |

## 平台 / 法规 / 公司合规（compliance）

| 工具 | 说明 |
|---|---|
| `qc_review` | 按 checks 跑多维检查（默认 company+quality）。支持 persona / quality_system_prompt / quality_user_prompt；画面人设可传 bundle_id/frames + vision。输出 review_id、verdict、issues。 |
| `qc_consistency_check` | 逐帧比对生成镜头首帧与锁定参考图（face_ref_url/product_ref_url，至少传一个）的身份一致性，判断脸/商品是否漂移。独立工具，不接入 qc_review 裁决。frames[] 或 bundle_id（复用 qc_prepare 产物）传入要检测的帧。 |
| `context_rule_list` | 列合规库规则；可按适用平台 / 品类 / 产品与生效期筛，返回合并的禁说词与规则文本供审核使用。 |
| `context_rule_upsert` | 新建 / 更新合规库规则：名称、类型（公司 / 平台 / 法规）、适用平台 / 品类 / SKU、依据来源、原始文件、生效 / 失效时间、规则正文、禁说词。 |
| `context_rule_get` | 按 rule_id 读一条合规规则。 |
| `context_rule_delete` | 软删一条合规规则；列表不再出现，行保留。 |

## 绑定自有账号（owned-accounts）

| 工具 | 说明 |
|---|---|
| `publish_owned_subaccounts_list` | 查询某企业下的企业子账号列表，供选择子账号做绑定。需 ctx.enterprise_id（KP 主体 ID 或 koc enterprise_id，后端反查 advertiser）。同步返回 data.total（子账号数）+ data.subaccounts[]，每条含 subaccount_id（绑定用）/subaccount_name。 |
| `publish_owned_accounts_list` | 查询某企业下的企业账号列表，供后续发布选号（把返回的 account_id 传给 publish_owned_run 的 account_strategy.account_ids）。需 ctx.enterprise_id（KP 主体 ID 或 koc enterprise_id，后端反查 advertiser）；payload.platform 可选。同步返回 data.total（账号数）+ data.accounts[]，每条含 account_id/advertiser_id/subaccount_id/nickname/platform/fans_num/access_token_status/websocket_status（0未知/1在线/2离线）。 |
| `publish_owned_publish_list` | 按子账号（业务）+ 平台 + 企业账号分页查发布明细，不需 activity_id。需 ctx.enterprise_id + payload.subaccount_id + payload.platform + payload.account_id；advertiser_id 可选。返回 data.total + data.items[]（字段同 publish_owned_run_status）。 |

## 批量发布（batch-publish）

| 工具 | 说明 |
|---|---|
| `publish_run` | 一条成片+account_strategy 批量受理发布，返回 job_id(=request_id)。异步，结果查 publish_run_status。全越界/全当日满→needs_input；部分失败→succeeded+partial；系统错误→failed。 |
| `publish_run_status` | 按 job_id 查发布批次状态与每条明细。成功 succeeded。 |

## 多平台账号匹配（account-match）

| 工具 | 说明 |
|---|---|
| `publish_platforms` | 返回 FDE 支持的发布平台列表（id + 名称 + key）。同步，不需 enterprise_id。 |
| `publish_accounts_list` | 按平台+数量选号（复用 seatLockChooseAccountsCore，独享池/共享池/席位池三池同口径，与 publish_choose_accounts 同源），回 nickname/头像/省/市/粉丝/tag/commission/sec_uid_url + publishable 给 Agent 选号。在线优先+随机轮换，非分页浏览；选定 account_id 后传给 publish_run(manual)。锁号释号写操作走 KOC 后台。成功 succeeded（空列表 total=0 也 succeeded）；缺 ctx.enterprise_id 或 payload.platform/count → failed/needs_input。 |
| `publish_choose_accounts` | 按平台+数量自动选号（在线优先+随机轮换），返回账号列表。需 ctx.enterprise_id + payload.platform + payload.count。成功 succeeded（含空列表）。 |

## 发布包装和挂载（publish-package）

| 工具 | 说明 |
|---|---|
| `publish_pack_game_search` | 按关键词搜索抖音游戏挂载，返回游戏列表（unified_game_id + name + mount_game JSON）。需 payload.game_name，平台后端固定抖音。成功 succeeded。 |
| `publish_run` | 一条成片+account_strategy 批量受理发布，返回 job_id(=request_id)。异步，结果查 publish_run_status。全越界/全当日满→needs_input；部分失败→succeeded+partial；系统错误→failed。 |
| `publish_run_status` | 按 job_id 查发布批次状态与每条明细。成功 succeeded。 |
| `publish_owned_run` | 用企业账号发布一条成片，异步受理（立即返回，实际结果轮询 publish_owned_run_status）。需 ctx.enterprise_id + payload.subaccount_id（必填，扣点/计费维度；advertiser_id 可选，只给子账号时内部反查）+ video.uri + video.platform + account_strategy{mode:manual, account_ids}。可选 payload.mount 挂载（小游戏/购物车/小程序/团购），按平台嵌套区分（抖音支持小游戏/小程序/购物车/团购，快手支持本地生活+商品挂车，小红书/视频号仅 POI 本地生活），字段与 tuini 发布字段一致。account_ids 须全部同属本请求的 advertiser_id + subaccount_id，跨组请拆多次调用。返回 data.activity_id（供状态查询）+ push_detail_id + job_id + accepted_count + status(queued)。 |
| `publish_owned_run_status` | 查询一次企业账号发布的状态与每条视频的指标。需 ctx.enterprise_id + payload.activity_id（来自 publish_owned_run 返回）+ advertiser_id 或 subaccount_id（至少一个）。同步返回 data.total + data.items[]，每条含 publish_status/publish_msg/title/item_id/platform/account_id/play/like/comment/share。publish_status 枚举：0待发布/1发布中/2审核中/3发布成功/4发布失败/5已删除/6定时成功。 |

## 数据回捞（data-pullback）

| 工具 | 说明 |
|---|---|
| `publish_analytics_list` | 按 job_id 或日期范围分页查发布明细 + 全量指标（同 video_analytics_get 字段）。job_id 查整批；日期范围仅查发布成功作品。需 ctx.enterprise_id + payload.job_id 或 start_date+end_date（二选一）。 |
| `publish_data_sync_trigger` | 触发 koc_queue 拉数（按 publish_ids 或 job_id 整批），仅保证受理、非实时。完成靠 synced_at 变化或重试 trigger。读指标改用 publish_video_analytics_get。需 ctx.enterprise_id + payload.publish_ids 或 job_id（二选一）。 |
| `publish_video_analytics_get` | 按 publish_ids 直读单条视频深度指标（play/like/comment/collect/share + 完播率/留存/点击率等）。指标反映最近一次同步，非实时；refresh=true 先触发拉数再读。需 ctx.enterprise_id + payload.publish_ids（上限 100）。 |
| `publish_owned_subaccounts_list` | 查询某企业下的企业子账号列表，供选择子账号做绑定。需 ctx.enterprise_id（KP 主体 ID 或 koc enterprise_id，后端反查 advertiser）。同步返回 data.total（子账号数）+ data.subaccounts[]，每条含 subaccount_id（绑定用）/subaccount_name。 |
| `publish_owned_publish_list` | 按子账号（业务）+ 平台 + 企业账号分页查发布明细，不需 activity_id。需 ctx.enterprise_id + payload.subaccount_id + payload.platform + payload.account_id；advertiser_id 可选。返回 data.total + data.items[]（字段同 publish_owned_run_status）。 |
| `publish_owned_data_sync_trigger` | 触发企业账号（SaaS）作品数据回捞，按 subaccount_id 拉该子账号下全部账号/作品指标（覆盖式更新，非单条）。需 ctx.enterprise_id + payload.subaccount_id（必填，回捞维度；advertiser_id 可选，只给子账号时内部反查）。异步受理，稍后用 publish_owned_run_status 读最新指标。同一 (advertiser_id, subaccount_id) 5 分钟内只能触发一次，超限返回 failed(QUOTA_EXCEEDED)。 |
| `publish_owned_run_status` | 查询一次企业账号发布的状态与每条视频的指标。需 ctx.enterprise_id + payload.activity_id（来自 publish_owned_run 返回）+ advertiser_id 或 subaccount_id（至少一个）。同步返回 data.total + data.items[]，每条含 publish_status/publish_msg/title/item_id/platform/account_id/play/like/comment/share。publish_status 枚举：0待发布/1发布中/2审核中/3发布成功/4发布失败/5已删除/6定时成功。 |

## 增效补量（boost）

| 工具 | 说明 |
|---|---|
| `publish_boost` | 对已发布视频做一次性播放/点赞/评论/关注增量增效。需 payload.channel + publish_ids 或 item_ids（二选一）。异步，返回逐条结果。 |

## 模型网关（compute-gateway）

| 工具 | 说明 |
|---|---|
| `token_models_list` | 列出可用 model_id、模态、评分与成本骨架；payload.modality 可筛 text／image／video／audio／music。 |
| `token_models_get` | payload.model_id → 单个模型对象。 |
| `token_generate_text` | OpenAI 兼容 chat/completions 原语。payload 可传 messages，或 system+user，或 prompt。 |
| `token_generate_image` | prompt/visual_desc → 异步 task_id；完成态用 token_job_get 取 image_url。 |
| `token_generate_video` | prompt/visual_desc → 异步 task_id；可带参考图和参考视频（reference_video_url）。完成态用 token_job_get 取 video_url。 |
| `token_job_get` | payload.task_id + 可选 kind=image／video／rig／enhancement；返回 status 与 image_url/video_url/file_url 和 cost。增强任务须传 kind=enhancement。 |

## 提示词模板（prompt-templates）

| 工具 | 说明 |
|---|---|
| `ref_personal_prompt_template_list` | 同步：查本人（API Key 归属 customer_id）的提示词模板。归属跟 Key 走，与全局库隔离。 |
| `ref_personal_prompt_template_get` | 同步：按 id 取本人模板详情。只能看自己的（别人的/全局的返回 NOT_FOUND）。 |
| `ref_personal_prompt_template_create` | 同步：在本人名下建模板（business_id 强制=Key 归属，不碰全局库）。payload: name*, type, remark, system/user_prompt, model_id… |
| `ref_personal_prompt_template_update` | 同步：更新本人模板名/备注。只能改自己的。payload: id*, name?, remark? |
| `ref_personal_prompt_template_delete` | 同步：删除本人模板。只能删自己的。payload: id* |

## 存储（storage）

| 工具 | 说明 |
|---|---|
| `store_register` | 将 filestore file_id 登记到客户盘（kind=gen／compose／upload）；business_id 由配置 hub.filestore_business_id 落库；幂等：task_id 优先，其次 file_id。 |
| `store_get` | 按 store_id / file_id / task_id 取台账。 |
| `store_list` | 列某客户未软删文件；可按 kind/run_id/task_id/pinned 过滤。 |
| `store_delete` | 标记 deleted_at；一期不删 filestore 对象。 |
| `store_sign_url` | 按 file_id 现签/续签下载 URL；ttl 以 filestore 桶配置为准（过期签名桶每次返回新鲜有效期，永久桶 ttl=0）。business_id 由配置 hub.filestore_business_id 决定。 |
| `filestore_sign_upload` | 前端签名自传：服务端签发预签名上传地址并落库，调用方拿 upload_url 直传对象存储（无需服务端代传）。传 payload.file_name，可选 file_type（video/image/audio）；物理桶由配置 hub.filestore_business_id 决定。 |
| `filestore_upload` | 服务端拉取源 URL 转存到对象存储（COS/TOS）并落库（异步，回 task_id，用 filestore_upload_status 查询结果）。物理桶由配置 hub.filestore_business_id 决定。 |
| `filestore_upload_status` | 查询 URL 转存任务状态。传 payload.task_id（filestore_upload 返回的任务 ID）。成功回 file_id/download_url，失败回 error_msg，未终态回 status（1 待处理 / 2 处理中）。 |

## 钱包（wallet）

| 工具 | 说明 |
|---|---|
| `platform_balance_get` | 查 KP 主体余额（透传 fde-billing GET /v1/balance → KP wallet/info）。 |
| `platform_billing_events` | 查计费流水分页（透传 fde-billing GET /v1/events → 本地 billing_event 表）。 |

## 账号（account）

| 工具 | 说明 |
|---|---|
| `platform_account_get` | 查当前登录 KP 账号信息（透传 fde-account GetKpAccount gRPC → KP account/get）。 |

## 全量工具速查（补充未挂到以上能力的 10 个工具）


### effect（特效/BGM/音色）

| 工具 | 说明 |
|---|---|
| `effect_get` | 按 effect_id 返回元数据与资源地址。找不到回 NOT_FOUND。 |
| `effect_list` | 按 kind 分页列出库内条目（不做语义排序；语义召回走 effect_search）。 |
| `effect_search` | 输入一句话（如「喜庆大促花字」「轻快咖啡店 BGM」），从 effect 库召回 top-K 候选。可按 kind 过滤。VikingDB 已配时走向量召回；未配时回落关键词匹配（envelope 标 fallback=true）。 |

### nx（解析/爆款/对标/热点IP）

| 工具 | 说明 |
|---|---|
| `nx_parse_job_get` | 查询 nx_parse_product/nx_parse_shop/nx_parse_media/nx_parse_user_posts 异步解析任务状态。按提交返回的 job_id 轮询，status ∈ pending/running/succeeded/failed；终态 succeeded 时返回解析结果。 |
| `nx_parse_product` | 输入淘宝/天猫/京东商品链接（长链或短链）、抖音团购商品链接、美团团购商品短链或大众点评商品链接，返回结构化商品数据（title/price/images/selling_points…）。不建档（→ mcp-context）；必填字段抽不全回 EXTRACT_INCOMPLETE 并带回已抽部分。 |

### asset（素材/检索）

| 工具 | 说明 |
|---|---|
| `asset_job_get` | 查询投喂流水线 job 状态：本地台账 + 实时拉取真实素材状态（真实服务无独立 task 查询 RPC）。 |

### context（客户语境/产品/IP/资料/规则）

| 工具 | 说明 |
|---|---|
| `context_sku_recompare` | 清理重复 SKU 后手动触发：跨批次全量重算 vs_others / live_priority / profile_md。默认全量，传 batch_id 可缩到单批。 |

### kmcp（网关）

| 工具 | 说明 |
|---|---|
| `kmcp_fee_confirm` | 确认知悉并同意《筷子 MCP 工具使用及计费协议》。首次调用任意筷子 MCP 工具前会被要求确认；在用户明确表达同意（如回复「同意并继续」）后，带 payload.agree=true 调用本工具完成确认。确认后该凭证在授权范围内可连续调用工具，无需重复确认。 |

### qc（质检）

| 工具 | 说明 |
|---|---|
| `qc_prepare_batch` | 一次提交多条 render（items[]，每条结构同 qc_prepare 的 payload），并发跑准备，各自独立成败，不因单条失败拖累整批。单次最多 20 条，内部并发度 6。不支持 ASR 异步转写兜底，需要转写兜底的条目请单独调 qc_prepare。 |

### ref（召回/模板/热点）

| 工具 | 说明 |
|---|---|
| `ref_hot_calendar` | 查营销日历节点（节气、电商大促等），给排期/选题参考。 可选 payload：start_time、end_time（unix 秒）、platform_list。 不传则返回下游默认时段。返回 data.list[]：title、date、category。 |
