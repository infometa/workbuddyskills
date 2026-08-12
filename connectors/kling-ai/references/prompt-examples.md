# Prompt and usage examples

## Natural-language requests

Text-to-video:

> 用可灵生成一个 5 秒、16:9 的电影感视频：雨夜便利店门口，一辆复古摩托缓慢停下，镜头从远景平稳推近。生成完成后自动展示。

Image-to-video:

> 用我附上的图片做 5 秒图生视频。人物身份、五官和服装保持一致，只让镜头缓慢从左侧环绕到正面，720p。

Multi-shot VIDEO 3.0:

> 生成 7 秒四分镜产品片：1.5 秒全景建立场景，2 秒推近产品，2 秒侧面环绕，1.5 秒定格品牌细节。开启多分镜，镜头衔接自然。

Text-to-image:

> 用可灵生成一张 16:9 海报主视觉：极简白色摄影棚，一只透明玻璃茶壶，柔和侧光，保留右侧标题留白。

Immediate submission with explicit approval:

> 直接提交，不需要再次确认：用可灵生成 5 秒、16:9、720p 的单镜头视频。雨夜便利店门口，一辆复古摩托缓慢停下；生成后返回 generationId。

Status check:

> 查询这个 Kling generationId 的当前状态；如果仍在生成，继续轮询直到完成。

## Prompt construction

Prefer concrete direction in this order:

1. subject and setting
2. action or transformation
3. camera and shot structure
4. lighting and visual style
5. identity or consistency constraints
6. exclusions only when they prevent a likely failure

Avoid long lists of repeated negatives. For image-to-video, state what must
remain stable and what is allowed to move.

## User-facing submission summary

Use one compact block:

```text
准备提交：图生视频 · VIDEO 3.0 Turbo · 5 秒 · 720p · 单镜头
动作：人物保持稳定，镜头从左侧缓慢环绕至正面
提交会消耗可灵 credits。
请回复"确认提交"后创建一次生成任务。
```

After acceptance:

```text
任务已提交一次；后续只查询这个 generationId，不会重复创建任务。
完成后会自动展示视频；链接 24 小时有效，过期可重新查询。
```
