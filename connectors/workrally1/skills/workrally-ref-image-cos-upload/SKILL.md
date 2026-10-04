---
name: workrally-ref-image-cos-upload
description: 当需要把本机图片/视频作为「参考图（input_images）」传给 WorkRally（workrally1 / workrally MCP）的画布生成工具，但 mcp__workrally*__upload_file 返回「文件不存在」时使用。核心原因：WorkRally MCP 的 upload_file 运行在与本机隔离的环境里，读不到本地任何路径（中文路径、纯 ASCII 路径、/tmp 都失败）。本技能给出绕行方案——用 get_upload_token 取 COS 临时凭证，本地用 curl 直传对象存储拿到公开 CDN URL，再作为 input_images 传入。适用于角色基准图锁定、风格参考、首尾帧、图生视频等一切需要本地文件变成公网 URL 的场景。
description_zh: WorkRally 参考图本地上传绕行
description_en: WorkRally ref-image upload via COS
disable: false
agent_created: true
---

# workrally-ref-image-cos-upload

把**本机文件**变成 WorkRally 生成工具可用的**公网参考图 URL**。

## When to use

触发条件（满足其一即用）：

- 调用 `mcp__workrally*__upload_file` 返回 `❌ 文件不存在: /...`（哪怕文件确实存在、`ls` 能看到、md5 能算）
- 需要用**本机已有图片**做 `canvas_generate_image` 的 `input_images`（角色基准图、风格参考、构图参考）
- 需要用**本机已有图片**做 `canvas_generate_video` / 图生视频的首帧
- 已知 WorkRally 的 MCP server 与本地文件系统隔离，无法读取本地路径

**不适用**：文件已经在公网 URL 上（直接用该 URL 即可，无需本技能）。

## 根因（先确认，别瞎试）

`upload_file` 失败不是路径写错，而是 **MCP server 与本机沙箱隔离**：

- 中文路径 → 文件不存在
- 纯 ASCII 路径（`/Users/.../ref_tmp/a.jpg`）→ 文件不存在
- `/tmp`、`/private/tmp` → 文件不存在

所以**不要反复换本地路径重试**，直接走下面的 COS 直传。

## Steps

### 1. 取 COS 临时凭证

调 MCP 工具 `get_upload_token`，参数：

```
file_ext: "jpg"          # 或 png / mp4 / mp3
upload_type: 200         # 200=普通(公网可读，图片用)；210=私有读(音视频用)
```

返回：`tmp_secret_id` / `tmp_secret_key` / `tmp_token` / `bucket` / `region` / `key` / `cdn_path`。

**每个文件单独取一次**（每次调用返回一个专属 `key`）。

### 2. 本地 COS 签名直传

用 `scripts/cos_put.py`（本技能自带，已封装签名 + curl PUT）：

```bash
python3 scripts/cos_put.py \
  --secret-id  "<tmp_secret_id>" \
  --secret-key "<tmp_secret_key>" \
  --token      "<tmp_token>" \
  --bucket     "<bucket>" \
  --region     "<region>" \
  --key        "<key>" \
  --file       "/绝对路径/本地图.jpg" \
  --content-type "image/jpeg"
```

成功输出 `HTTP 200`。

### 3. 拼出公网 URL

```
https://<cdn 域名>/<key>
```

`cdn_path` 返回形如 `//zenvideo-pro.gtimg.com`，取域名部分拼 `https://` + 域名 + `/` + `key`。

**务必校验**（图片是公网可读，视频/音频必须用带签名的 `url`）：

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}\n" "<URL>"
# 期望：200 image/jpeg <本地字节数>
```

### 4. 作为参考图传入

`canvas_generate_image`（或 video 工具）：

```
input_images: ["<URL1>", "<URL2>"]
prompt: "...角色外形严格参照第一张图片..."
```

**prompt 用「第一张图片」「第二张图片」引用**，与 `input_images` 数组下标一一对应。
参考图数量上限看 `canvas_image_model_list` 返回的 `kontext_config.max_input_images`。

## 参考图选择纪律（实测：哪个锚会泄漏什么）

传上去只是第一步；**选错锚会稳定污染输出**。以下 5 条为 2026-09-19 在真实项目（《呼噜噜的夏日》补齐 11 项角色 + 5 项场景）上逐张目检得出的结论：

| 现象 | 结论 |
|---|---|
| 把**含人物的场景图**当结构参考 | 原图人物会被抄进画面（实测：中景凭空出现 8–10 个红色小人剪影）→ **场景结构参考只能传干净无人的图** |
| 同时传两张参考图 | **第一张主导**。第一张的色调会压过第二张的风格锚（实测：想用 B 定调色，结果整幅被 A 的冷绿带跑） |
| 把**持道具的角色**当三视图结构锚 | 道具会抄给其他角色（实测：用持竹杖的猫师傅当锚，熊爸与猫妈都长出了竹杖） |
| 把**同科属角色**当锚 | 物种会被抄（实测：换成狐狸当锚后，三花猫被画成狐狸脸） |
| 换锚之后 | **泄漏类型会变**（道具泄漏 → 物种泄漏），**每次换锚都必须重新目检**，不能假设「换了就好了」 |

**选锚优先级**：① 干净、无道具、物种差异大的**同体系三视图** > ② 只有设计没有版式的**半身/立绘**（必须配一张①当版式锚） > ③ 纯文字。

**沿用旧参考的正面经验**：用户给出的原角色三视图（如「呼噜噜」）本身无道具、版式标准，是**最安全的结构锚**，优先复用。

**风格锚要单独挑干净的**：风格统一时不要拿「有建筑/有人/有动物的场景图」当风格锚——结构会一起抄。优先用**空镜场景**或**裁切出的纯风格区块**。

## Pitfalls

- **签名串漏段**：COS 的 `StringToSign` 必须是三段
  `"sha1\n" + KeyTime + "\n" + sha1(HttpString) + "\n"`
  只传 `HttpString` 会稳定报 `SignatureDoesNotMatch`（服务端回包里会带 `StringToSign` / `FormatString`，可对照排查）。
- **Python urllib 直传会 write timeout**：沙箱下用 urllib 发 PUT 常超时；**改用 curl `--data-binary @文件`** 即可通。
- **别用 `requests`/`urllib`**：走 `subprocess` 调 curl 最稳。
- **凭证时效**：STS 临时凭证有效期短（约 1 小时级），取到后尽快传完；`get_upload_token` 返回的 `key` 已带日期目录与 uuid，不要自己拼。
- **音视频是私有读**：`upload_file` 返回的 `url`（带签名）才能访问，`original_url` 不行。图片是公网读，无此限制。
- **不要拿风格/氛围图当 input_images**：会污染画面（把参考图里的人、道具一起抄进去）。参考图只传**结构/身份**参考；风格走文字描述。
- **组合图（多视图并置的资产图）不能直接当 input_images**：道具/角色资产常做成「一张图里并排多个视图」（如同时有封面＋内页、全杖＋杖头特写）。直接整张传入，模型会把**多个视图一起画进同一画面**（同框出现两份物料）。传入前先**按视图裁成单件**。
- **含大量汉字的资产图慎传**：视频模型复现汉字会写成乱码或伪字形。关键文字（书名/表格/题词）走**后期叠印**（Pillow 渲染＋overlay），生成时不要求模型写字。
- **否定式约束不可靠**：写「画面里不要出现 X」常被忽略；改**肯定式**描述（「这是已清场的空镜，台面上除了雨水什么都没有」）更有效。
- **一张图只有一个主导者**：传两张参考图时**第一张主导**，其色调与内容会压过第二张——把「要什么」放第一张，「风格/结构」放第二张。

## Verification

1. `curl -o /dev/null -w "%{http_code}"` 返回 **200**，且 `%{size_download}` 与本地文件字节数一致。
2. `%{content_type}` 是 `image/jpeg` / `image/png` 等预期类型。
3. 把 URL 填进 `input_images` 后，生成结果确实复现了参考图中的**目标特征**（造型/配色/结构），且背景没有被参考图污染。
