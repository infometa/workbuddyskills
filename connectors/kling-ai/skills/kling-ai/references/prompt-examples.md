# Prompt and usage examples

## 建议提示词

- 画一只身穿复古宇航服的小熊猫，漂浮在空间站舷窗前，地球蓝光映亮面部，细节丰富，电影级质感
- 制作一段 5 秒电影感视频：机甲战士从高空重砸地面，冲击波瞬间震开碎石与尘雾，镜头快速推近，充满力量感
- 制作一条 15 秒运动鞋营销短片：街头开场抓住注意力，三秒切出产品特写与穿着动态，结尾落在鞋身细节特写

## Natural-language requests

Text-to-video:

> 用可灵生成一个 5 秒、16:9 的电影感视频：雨夜便利店门口，一辆复古摩托缓慢停下，镜头从远景平稳推近。

Image-to-video:

> 用我附上的图片做 5 秒图生视频。人物身份、五官和服装保持一致，只让镜头缓慢从左侧环绕到正面，720p。

Multi-shot video:

> 生成一条多镜头产品片：先用全景建立场景，再推近产品并从侧面展示，最后定格品牌细节，镜头衔接自然。时长和分镜参数使用当前可灵支持的值。

Text-to-image:

> 用可灵生成一张 16:9 海报主视觉：极简白色摄影棚，一只透明玻璃茶壶，柔和侧光，保留右侧标题留白。

Complete generation request:

> 用可灵生成 5 秒、16:9、720p 的单镜头视频：雨夜便利店门口，一辆复古摩托缓慢停下。生成后返回任务编号。

Status check:

> 查询这个可灵任务编号的当前状态，只查一次，不要循环轮询。

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

## User-facing submission result

Do not add a credit warning or a separate confirmation step. After submission,
use one compact block:

```text
完成后返回主结果。结果链接可能是临时签名地址；地址失效不代表作品丢失，
可重新查询原任务编号获取新的访问地址，或在已授权账号的可灵官网生成记录中查看。
```
