# 核心命令

所有命令都追加 `--json --download-dir ./output`。执行前可用 `meitu <command> --help` 再确认当前版本参数。

## 自定义工作流

自定义工作流在 [MeituHub Chat](https://meituhub.cn/zh-cn/chat) 创建并发布，CLI 负责发现和执行当前登录账号可见的工作流。创建工作流与执行工作流必须使用同一 MeituHub 中国区账号。

```bash
meitu workflow update --json
meitu workflow list --json
meitu workflow info <listing_code> --json
meitu workflow <listing_code> --help
meitu workflow <listing_code> <arguments> --json --download-dir ./output
```

新建或修改工作流后必须重新执行 `meitu workflow update --json`。只有已发布、在线且对当前账号可见的工作流才能执行。

## text-to-image

从文字生成全新图片；有底图需要修改时改用 `image-edit`，含明确海报排版时改用 `image-poster-generate`。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--prompt <text>` | 是 | 图片内容描述 |
| `--image_list <values...>` | 否 | 风格或氛围参考图；与 `ratio` 互斥 |
| `--size <value>` | 否 | `1K`、`2K`、`4K`，默认 `2K` |
| `--ratio <value>` | 否 | 输出宽高比 |
| `--model <value>` | 否 | `auto`、`gummy`、`praline_pro`、`nougat` |

```bash
meitu text-to-image --prompt "电影感雪山旅行宣传图" --size 2K --ratio 16:9 --json --download-dir ./output
```

## image-edit

编辑已有图片或以参考图为主要内容来源进行创作。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--image_list <values...>` | 是 | 第一张为底图，可追加参考图 |
| `--prompt <text>` | 是 | 编辑要求 |
| `--ratio <value>` | 否 | 输出宽高比 |
| `--size <value>` | 否 | 输出尺寸 |
| `--output_format <value>` | 否 | `jpeg`、`png`、`webp`，以 `--help` 为准 |
| `--model <value>` | 否 | `auto`、`gummy_pro`、`praline_pro`、`praline_lite`、`mint_edit`、`nougat` |

```bash
meitu image-edit --image_list "/absolute/path/product.jpg" --prompt "替换成极简摄影棚背景，保持商品不变" --json --download-dir ./output
```

## image-poster-generate

生成包含文字和版式的海报。用户提供的标题、价格和品牌文字必须原样保留。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--prompt <text>` | 是 | 海报文案和设计要求 |
| `--image_list <values...>` | 否 | 产品、人像或其他素材图 |
| `--model <value>` | 否 | `Gummy`、`Nougat`、`PralineV2`、`GummyV4.5`、`Praline_2` |
| `--size <value>` | 否 | 输出尺寸 |
| `--ratio <value>` | 否 | 输出宽高比，默认 `auto` |
| `--output_format <value>` | 否 | 默认 `png` |
| `--enhance_prompt <value>` | 否 | 是否增强提示词，以 `--help` 为准 |

```bash
meitu image-poster-generate --image_list "/absolute/path/product.png" --prompt "夏日新品促销海报，标题：清凉一夏" --ratio 3:4 --json --download-dir ./output
```

## image-cutout

仅用于人物、宠物、商品、图标或印章的透明背景抠图。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--image_url <value>` | 是 | 单张本地图片或 HTTPS URL |
| `--model_type <value>` | 否 | `0` 人像、`1` 商品、`2` 图形；不确定时省略 |

```bash
meitu image-cutout --image_url "/absolute/path/person.jpg" --model_type 0 --json --download-dir ./output
```

## image-superres-enhance

提升图片清晰度；单纯按倍数改变尺寸时应选择图片变换能力。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--image_url <value>` | 是 | 单张本地图片或 HTTPS URL |
| `--prompt <text>` | 是 | 描述图片内容，帮助选择通用、商品或文档超清算法 |

```bash
meitu image-superres-enhance --image_url "/absolute/path/old-photo.jpg" --prompt "老照片人像，提升清晰度并保留自然细节" --json --download-dir ./output
```

## image-to-video

基于一至九张图片生成视频。无图片时改用 `text-to-video`。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--image_list <values...>` | 是 | 1–9 张图片 |
| `--prompt <text>` | 是 | 动作、镜头和画面描述 |
| `--mode <value>` | 否 | `auto`、`i2v`、`mi2v`、`flf` |
| `--model <value>` | 否 | `auto`、`toffee`、`bonbon` |
| `--video_duration <value>` | 否 | 4–15 秒，默认 5 秒 |
| `--sound <value>` | 否 | `off` 或 `on`，默认 `off` |
| `--aspect_ratio <value>` | 否 | 默认 `adaptive` |
| `--multi_shot <value>` | 否 | 多镜头开关，以 `--help` 为准 |

```bash
meitu image-to-video --image_list "/absolute/path/portrait.jpg" --prompt "镜头缓慢推进，人物自然转身并微笑" --video_duration 5 --sound off --json --download-dir ./output
```
