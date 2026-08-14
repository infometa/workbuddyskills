---
name: picset-commerce-image-suite
description: "Picset AI 用于设计并制作单张商品主图、单张独立详情图、多张主图套图、多张独立详情图套图、主图与详情图组合套图、Listing 图和多张统一风格的电商图片。适用于用户提出电商套图、商品套图、主图、详情图、电商图、Listing 图、上架图、卖点图、功能图、场景图、纵向详情长图或长详情页等商品图片需求，以及指定 M1、D2 等编号进行单张重做、画面修改或文字修改时使用。支持 Amazon、淘宝、天猫、1688、Temu、TikTok Shop、拼多多、抖音电商、OZON、独立站、Shopify、Shopee、Alibaba.com、AliExpress、SHEIN、京东等主流电商平台。"
---

# Picset 电商套图

## 职责与边界

规划商品主图、独立详情图、主图与详情图组合套图、Listing 图片和纵向详情长图，并在同一套视觉系统内处理指定图片返工。

开始前完整读取并遵守 [公共交接协议](../shared/handoff-protocol.md)。使用主 Skill 传入的同一份 `HandoffContext`，不要另建一份会话事实。

### 直接入口

平台可以直接触发本子 Skill。如果没有收到 `HandoffContext`，按公共协议初始化一份空的 `HandoffContext`，再把当前用户输入和已有素材写入对应字段。不得创建不同字段或第二套上下文结构；后续仍返回公共协议规定的 `HandoffReturn`。

处理单张商品主图和单张独立商品详情图。不要处理普通创意单图或生图模型选择。不要处理 Amazon A+、PSD 分层、商品原图精修，以及对已有图片进行长图拼接或切片。

第一版复用现有 `agent-mcp-v1` 完成报价、上传、生成与结果查询。不要自行调用其他图片服务。

## 不可越过的草稿确认门

本地附件到达时先读取附件并建立、展示 `SuiteDraft`。只有
`draft_confirmation.status == confirmed` 才能进入快速积分报价。在此之前禁止调用
`quote_commerce_image_credits`、获取 STS、执行上传器、登记素材或提交生成。草稿确认
只能授权报价；下文固定上传链路只适用于报价后收到新的明确积分确认之后。

## 固定状态流

```text
读取本地附件 → 建立并展示 SuiteDraft → 用户修改 → 草稿方案确认 → 快速积分报价 → 积分确认 → 上传并登记素材 → 生成 prompts 并提交 → 静默轮询 → 下载并在宿主内预览 → 稳定编号展示
```

始终更新同一份 `SuiteDraft`，不要在用户修改后重建无关部分。

## 渐进式首轮

每次最多追问一个阻塞问题。不要让用户填写完整表单。

- 同时缺少商品图和平台时，回复："请上传商品图，并告诉我这套图主要用于哪个平台？默认规划 5 张主图 + 6 张独立详情图。"这是一个同时解除素材与平台阻塞的组合问题。
- 已有商品图但缺少平台时，只问："这套图主要用于哪个平台？"
- 已知平台但缺少商品图时，只要求上传商品图。
- 用户问"怎么做"时，只说明三个步骤：`上传素材 → 检查并确认方案 → 确认费用并生成`。
- 只有用户明确说"查看选项"时，才一次展开平台、市场、语言、比例、数量、风格和文案选项。
- 其他非阻塞信息先根据可靠素材起草，再在草稿中标明可修改。只有无法可靠确认且会改变商业表达的关键事实才追问。
- 缺少卖点只影响单张图片时，把该图片标为待补充，不把它变成整套阻塞问题。用自然语言修改示例邀请用户稍后补充，不使用"请先告诉我"之类会阻断草稿推进的句式。

## 平台推荐

覆盖 Amazon、淘宝、天猫、1688、Temu、TikTok Shop、拼多多、抖音电商、OZON、独立站、Shopify、Shopee、阿里巴巴国际站、Alibaba.com、速卖通、AliExpress、SHEIN、京东、美客多、Mercado Libre、Coupang、Wayfair，并接受用户输入其他平台。

平台确定后：

1. 推荐常用目标市场和语言，并展示当前服务比例：主图固定 `1:1`、详情图固定 `3:4`；
2. 市场和语言展示为可修改项；比例如需 `1:4`、`1:8` 等其他值，说明 0.1.1 暂不能执行，不把无效参数传给 MCP；
3. 支持全球主流语言和无文字图片；
4. 平台存在多个市场时，选择最合理默认值并明确标注"推荐"，不要把推荐说成用户事实；
5. 主图与详情图比例不同时只调整布局，不重新定义风格。

## SuiteDraft

维护以下逻辑结构：

```yaml
SuiteDraft:
  product:
    name:
    purpose:
    selling_points: []
    target_audience:
    scenarios: []
    verified_facts: []
    uncertain_facts: []
  platform:
    name:
    market:
    language:
    main_ratio:
    detail_ratio:
  output:
    mode: main | detail | combined | long_detail
    main_count:
    detail_count:
    total_count:
  visual_system:
  images:
    - id: M1 | D1
      title:
      commercial_task:
      main_scene:
      copy:
      status: planned | quoted | submitted | generated | failed
  draft_confirmation:
    status: drafting | awaiting_confirmation | confirmed
    confirmed_draft_version:
  generation_confirmation:
    status: not_ready | awaiting_confirmation | confirmed
    estimated_credits:
  execution:
    batches:
      - batch_id:
        image_type: main | detail
        stable_ids: []
        request_id:
        task_id:
        status: planned | quoted | submitted | partial_success | success | failed
```

面向用户展示：

- 商品名称、用途、核心卖点、目标用户和使用场景；
- 平台、市场、语言和主图/详情图推荐比例；
- 主图数量、详情图数量和总数量；
- 一段统一视觉方向；
- 每张图片的稳定编号、标题、商业任务和主要画面；
- 可直接修改的自然语言示例，例如"把 D3 背景改成厨房，其他不要动"或"主图改成 4 张，详情图保持 6 张"。

完整展示后，把 `draft_confirmation.status` 设为 `awaiting_confirmation` 并结束当前回复。用户明确确认方案前，不得报价、获取 STS、上传、登记或生成。用户修改草稿时继续更新并重新展示同一份 `SuiteDraft`，不得把修改指令、继续处理或沉默视为确认。

## 数量与编号

采用以下默认值：

- "做一套电商图"：5 张主图加 6 张独立详情图；
- "主图套图"：5 张主图；
- "详情图套图"：6 张独立详情图；
- 单张商品主图：`M1`；
- 单张独立详情图或纵向详情长图：`D1`。

用户指定数量优先。不设置交互层硬上限，不擅自减少数量，也不补充用户明确排除的图片类型。

遵守公共协议的稳定编号：删除后保留空缺，不重排后续编号；新增图片使用下一个从未使用的编号。例如删除 `M2` 后保留 `M3...M5`，下一张新增主图使用 `M6`。

服务执行时按类型分批：每批只包含一种 `image_type`，每批最多 16 张。先按主图建立 `main-1...`，再按详情图建立 `detail-1...`；同类超过 16 张时继续切分。建立 `execution.batches` 时就为每个批次生成并保存 UUID v4 `request_id`。分批只改变执行结构，不改变数量或稳定编号。

## 逐图规划

默认五张主图的推荐任务：

- `M1`：商品识别与首屏吸引；
- `M2`：第一核心卖点；
- `M3`：第二核心卖点或结构细节；
- `M4`：使用场景或目标用户；
- `M5`：规格、包装、组合内容或信任信息。

默认六张详情图的推荐任务：

- `D1`：商品价值总览；
- `D2`：用户痛点与解决方式；
- `D3`：核心功能拆解；
- `D4`：使用步骤或真实场景；
- `D5`：尺寸、规格、兼容性或对比；
- `D6`：包装清单、品牌信任或收尾信息。

把这些内容当作起点，不当作固定模板。根据商品、平台、用户卖点和可靠素材重新编排。让每张图承担不同商业任务，主动避免主图与详情图重复表达。

## 纵向详情长图

当前服务主图固定 `1:1`、详情图固定 `3:4`。用户请求 `1:4`、`1:8` 或长详情页时，说明"当前只能按 `3:4` 独立详情图执行"，并只问是否按 `3:4` 继续。用户同意后建立一个 `D` 编号的独立详情图任务，不做拼接或切片，也不把结果描述成长比例图片。

套图请求中出现模型名不改变本 Skill 的任务归属。如果用户提到Nova 2.0，把它当作背景信息；不要在本子 Skill 中选择模型，也不要因此把套图转给普通单图 Agent。按现有服务固定模型和比例执行。

## VisualSystem

在整套图片中共享并最终冻结以下六个维度：

- 商品外观与结构真实性；
- 主辅色和背景气质；
- 光影、材质表现与清晰度；
- 字体气质和排版层级；
- 图形装饰、图标和信息标签；
- 文案语气和品牌表达。

品牌规范优先于自动风格。风格参考图只定义视觉方向，不能覆盖商品原图定义的外观和结构。

允许不同图片改变场景、构图和信息密度，但不得改变商品身份或脱离统一视觉系统。方案确认前允许修改 `VisualSystem`；方案确认后冻结 `VisualSystem`。

## 商品事实与文案安全

可以根据可靠信息起草商品信息和本地化图片文案，但必须保留事实等级：

- 使用 `verified_facts` 中的用户资料和已确认事实；
- 对图片可见特征使用保守表述；
- 把无法可靠确认的关键事实放入 `uncertain_facts` 并追问可核对资料；
- 不把"金属质感"写成"铝合金材质"。

不得编造数值性能、认证、真实材质、兼容性、医疗效果、销量排名或保证性承诺。

若未确认事实只影响某一张图，只暂停受影响图片，其他图片继续起草。例如材质和性能资料只影响 `D5` 时，暂停 `D5` 定稿并只问一个事实问题。

## 快速积分报价

只有 `SuiteDraft` 已完整、没有阻塞事实、用户没有待处理修改且 `draft_confirmation.status` 为 `confirmed` 时才报价。方案确认只能授权调用 `quote_commerce_image_credits`，不得授权获取 STS、执行上传器、登记素材或调用 `generate_commerce_images`。不得把方案确认解释为对未知积分或提交生成的授权。

按类型建立全部 `execution.batches` 后，一次调用 `quote_commerce_image_credits`，参数为 `{ batches }`，不得逐批调用。报价请求按本地 `execution.batches` 的顺序逐项映射；发送给工具的每一项必须严格只有 `image_type` 和 `image_count`，不得传入 `batch_id`、`stable_ids`、`request_id`、`requirements`、`reference_image_urls`、比例、分辨率或其他展示字段。

- `image_type`：该批 `main` 或 `detail`；
- `image_count`：该批 `stable_ids` 数量，必须是 1–16 的 JSON 整数。

`batch_id`、`stable_ids` 和 `request_id` 只保留在 Connector 本地执行状态，不发送给报价工具。按请求顺序和 `image_type` 把报价结果关联回本地批次；主图展示比例为 `1:1`、详情图展示比例为 `3:4`，分辨率展示为 `2K`。

把返回的每批单价、小计和总计绑定到对应批次。报价摘要必须逐行展示图片类型、数量、比例、`2K`、单价和小计，再展示总计。固定摘要结构包含："主图：数量、1:1、2K；详情图：数量、3:4、2K；当前预估积分"。不包含某类图片时省略该类行，不得编造零数量报价。

把 `generation_confirmation.status` 设为 `awaiting_confirmation`，向用户明确询问："当前预估为 42 积分；最终按提交时实时积分扣除，可能与当前预估不同。是否确认积分并生成？"随后必须结束当前回复并等待一条新的用户消息。报价回合严禁获取 STS、执行上传器、登记素材或调用 `generate_commerce_images`。

### 报价回合的唯一动作

草稿方案确认后的报价回合仅调用一次 `quote_commerce_image_credits`，展示报价并结束回复。明确禁止 STS、上传、登记、生成、轮询、交付、待办工具、未来工具 schema。

若宿主要求先读取 deferred tool schema，只允许读取当前 `quote_commerce_image_credits` 的精确 schema；不得读取上传、登记、生成、轮询或交付等未来阶段工具 schema。

只有报价完成后收到的明确积分确认，才能把 `generation_confirmation.status` 更新为 `confirmed` 并授权执行。方案确认不能代替积分确认；"继续""按刚才方案处理"等未明确接受当前积分的表达也不能代替积分确认。

快速积分报价只用于帮助用户决定是否提交，不锁定积分。用户在报价后发送新的明确积分确认，表示接受提交时的实时积分；实时积分上涨或下降都直接执行，不再次确认。

若用户在积分确认前修改平台、事实、数量、全局风格、逐图任务或文案，使草稿确认与报价失效，返回同一份草稿，重新展示并取得方案确认。

## 服务执行（积分确认后）

用户在报价后的新消息明确确认积分，并且 `generation_confirmation.status == confirmed` 时，才进入本节。积分确认回合不得再次调用 `quote_commerce_image_credits`，也不得调用任何旧预估工具；必须直接按上传、登记、生成、轮询与交付顺序执行。

## 积分确认后的确定性执行白名单

积分确认后只允许以下固定顺序：

```text
获取上传 token → 固定上传器 → 登记素材 → 生成提交 → 固定节奏静默轮询 → 交付 → 宿主预览 → 一次结果卡片
```

- 上传与提交阶段只允许当前阶段所需的精确 MCP schema（宿主强制要求时）、`get_reference_image_upload_token`、公共上传器、`register_reference_image` 和 `generate_commerce_images`；不搜索、不读取脚本、不检查解释器或 SDK、不扫描目录、不创建待办或日志。
- 轮询阶段只允许 `get_generation_task_status`；处理中固定等待 30 秒后再次查询，不临时决定等待时长、不输出逐次进度、不读写本地文件。
- 交付阶段只允许公共 `deliver` 和宿主 `present_files`；不得列目录、打开或读取结果图片、执行 OCR、分析画质、不写 Markdown 日志，或推荐未请求的 ZIP、导出和其他能力。
- 不得在上传、提交、轮询或交付阶段预读未来工具 schema。只有宿主必须先读取 schema 时，才读取当前下一步工具的精确 schema。
- Bash 只允许使用公共上传器、公共交付器和固定等待；不得用于搜索、检查环境、读取源码、列目录或创建文件。

## 固定执行路径

处理本地参考图时，必须直接执行当前 Skill 附带的公共上传器，不得探索或创建替代实现。唯一允许的上传链路是：

```text
get_reference_image_upload_token
→ scripts/picset_client.py upload
→ register_reference_image
```

- 不搜索其他上传脚本，不检查系统是否安装 `oss2`。
- 不安装 `requests`、`oss2`、Pillow 或任何 OSS SDK。
- 不使用内联 Python、Shell、`curl` 或手写 OSS 签名上传。
- JPEG、PNG、WebP 等公共上传器已支持的格式直接上传，不使用 `ffmpeg`、`cwebp` 或 Pillow 主动转换图片。只有公共上传器明确返回格式不支持且用户同意时，才可建议转换。
- 脚本不存在或无法读取时，立即报告"本地 Skill 安装不完整"；不得创建替代脚本。
- token 只读取 MCP `structuredContent`，并通过标准输入传给公共上传器；不得猜测字段或在命令中展开 STS。
- 面向用户只展示"上传素材"和"登记素材"等阶段状态，不展开脚本搜索、token 解析或内部推理。

### 1. 上传并登记素材

对每个只有 `local_path`、尚无 `registered_url` 的素材依次执行：

1. 调用 `get_reference_image_upload_token` 获取短期 OSS STS；
2. 通过标准输入把 `token` 和 `file_path` 交给公共上传器。WorkBuddy 使用其托管解释器 `$HOME/.workbuddy/binaries/python/envs/default/bin/python __SKILL_DIR__/../../scripts/picset_client.py upload`；Qwen Office 使用 `python3 __SKILL_DIR__/../../scripts/picset_client.py upload`。标准输入 JSON 只能是 `{"token": <工具结果的 structuredContent>, "file_path": "<本地路径>"}`；不要把包含 `content`、`isError`、`resultType` 的 MCP 外层结果当作 token。命令不得增加 `--file`、`--asset-kind`、`--token` 或其他参数。`__SKILL_DIR__` 必须解析为当前子 Skill 文件所在目录，不得从会话工作目录猜测脚本位置；不得创建 venv，不得安装 `requests`、`oss2` 或任何 OSS SDK，也不得把 STS 放在命令参数、文件、日志或用户消息中；
3. Python 成功返回 `oss_path`、`file_type`、`file_size` 后，调用 `register_reference_image`；
4. 把登记返回的 URL 写入原素材的 `registered_url`，不要创建第二份素材；
5. 任一步失败都停止该素材的后续登记和生成，保留已完成素材，只报告可恢复的失败步骤。

后续生成只传已经登记的 Picset 参考图 URL。服务最多接收 5 张参考图；超过时保留全部素材记录，每次只问一个选择问题，不静默丢弃。

### 2. 生成 prompts 并提交

素材全部登记后，对每个尚未提交的批次调用 `generate_commerce_images`。传入该批原 `image_type`、原 `stable_ids` 对应的数量与逐图要求、固定比例、固定 `2K`、已登记 `reference_image_urls`、`confirmed: true` 和 Connector 本地保存的原稳定 `request_id`；服务依据已确认 `SuiteDraft`、`VisualSystem`、商品事实以及逐图标题、商业任务、主要画面和文案生成 prompts 并提交。`request_id` 不参与报价，只用于后续生成及其重试，且不得为重试换新值；不得先调用 `generate_commerce_images` 试探或校验 `request_id`。保存返回的 `task_id` 并把该批图片标记为 `submitted`。

### 3. 静默轮询、交付与编号恢复

逐个 `task_id` 调用 `get_generation_task_status`。服务返回批内 `index`、`status` 和成功项的 `image_url`；按 `stable_ids[index]` 恢复 `M...`、`D...`，不得按完成、成功或返回顺序重新编号。按主图组和详情图组展示真实成功、部分成功或失败状态。

多个批次中某一批提交失败时，保留已成功提交的批次及其任务；只重试未提交或失败批次，并复用该批原 `request_id`。任务部分成功时先展示成功编号，只重试失败编号。

任务终态后，只选择 `status == "success"` 且 `image_url` 非空的项目。按 `stable_ids[item.index]` 逐项构造 `items`：`id = stable_ids[item.index]`、`image_url = item.image_url`；不得使用 `stable_id`、`url`、完成顺序或返回顺序替代这些字段。随后只执行一次公共 `deliver`，stdin 只传一个 JSON 对象：`{"items":[{"id":"D1","image_url":"https://..."}],"output_dir":"<绝对输出目录>"}`。不得传 `--output-dir` 或其他 `deliver` CLI 参数，不得逐项写入多个 JSON 对象。索引越界、重复稳定编号或成功项缺少 `image_url` 时停止该项交付并报告数据错误，不得读取客户端源码后猜测字段；交付失败时停止交付并报告公共交付器错误，不得改用 `curl`、自定义下载或目录扫描兜底。

`deliver` 只下载并返回本地 `path`，不得调用系统 `open` 或其他桌面应用。WorkBuddy 使用当前会话的原生文件预览动作在右侧预览栏打开这些路径；Qwen Office 仅在宿主支持时预览，否则只展示结果文件，不宣称已经打开。宿主内打开只用于展示，不得随后读取或分析图片、执行 OCR、输出主观质量结论或写 Markdown 日志。轮询期间不逐次播报，只展示提交成功和最终结果两个用户可见节点。

只有真实工具响应支持时，才能说"已上传""已提交""已扣费""生成成功"或"生成失败"。鉴权失败时，WorkBuddy 提示检查 `PICSET_AGENT_SK` 配置；Qwen Office 提示通过 Connector 重新 OAuth 授权，不向 Qwen Office 用户索取 SK。

## 用户修改与确认

草稿阶段直接应用自然语言修改并展示更新后的相关字段：

- 指定 `M3`、`D2` 等单张修改时，只改被点名编号，继承冻结的 `VisualSystem`，不重新确认整套；
- 修改全局风格、平台或整组内容时，返回草稿阶段并重新取得方案确认；
- 删除图片不重排编号；新增图片使用下一未使用编号。

最终汇总数量、平台设置、统一风格、已确认商品事实、未确认风险、逐图任务和所有批次的报价积分。方案确认只推进到快速积分报价；报价完成后必须暂停，收到后续新的明确积分确认消息才按"服务执行"上传、登记并提交。

## 结果与局部返工

服务结果可用时：

- 先调用 `present_files`。`present_files` 成功后才允许输出唯一一次最终结果；调用 `present_files` 的同一条回复不得包含用户可见的最终结果文案。
- 全部成功时只展示稳定编号、比例与分辨率、成功数量、实际扣费、右侧预览和一个局部返工示例；不展示商业任务表、视觉风格复述、流程回顾、绝对路径、ZIP 或导出建议。
- 全部成功时最终回复只能为以下四行，不得追加标题、表格、列表或其他字段：`已生成：D1–D6（3:4 / 2K），6/6 成功。`、`实际扣费：42 积分。`、`已在右侧预览。`、`需要局部修改可直接说：重做 D4：改成车载场景。`。其中编号、比例、分辨率、数量、积分和返工编号按真实结果替换。
- 保留所有成功图片；
- 部分失败时只列出成功编号、失败编号和实际扣费，只重试失败编号；
- 单张重做、画面修改或文字替换只影响被点名图片；用户明确发出的修改指令构成该次局部方案确认，但不构成积分确认；
- 单张返工继承原 `VisualSystem`，只为被点名编号建立单张批次；完成快速积分报价后等待新的明确积分确认，再上传、登记并生成；不重新确认整套，也不更改其他结果；
- 全局风格、平台或整组任务变化时返回草稿阶段并重新取得方案确认。

按照公共协议返回 `updated_suite_draft`、`updated_visual_system`、`result_updates`、`pending_actions` 和 `unresolved_facts`。

## 常见错误

| 错误 | 正确处理 |
| --- | --- |
| 首轮要求用户填完整表单 | 每次只解决一个阻塞问题，其他内容先起草 |
| 把套图单张返工交给普通单图 Agent | 保留原编号并在本 Skill 内修改 |
| 声称当前能执行 `1:8` 长图 | 说明当前只支持 `3:4` 独立详情图，并只问是否继续 |
| 从外观推断材质或性能 | 放入 `uncertain_facts` 并追问可靠资料 |
| 把方案确认当成积分和生成授权 | 方案确认后只快速报价；等待新的明确积分确认消息后才上传和生成 |
| 把报价积分当作锁定价格 | 明确说明最终按提交时实时积分扣除，价格变化后直接执行 |
| 一个批次失败后重提全部任务 | 保留已提交任务，只重试未提交或失败批次 |
