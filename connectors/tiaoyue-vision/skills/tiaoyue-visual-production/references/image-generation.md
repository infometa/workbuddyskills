# 图片生成参数

适用于 `generate_image`。依据 2026-10-28 当前连接的工具定义整理；运行时定义变化时以当前工具为准。工具异步提交，不能以调用返回作为图片完成的证据。

## 参数

| 字段 | 用法 |
|---|---|
| `prompt` | 必填，画面主体、动作、环境、风格；保持在约 4000 字以内。素材 URL、模型 ID、分辨率放专用字段 |
| `model` | 可省略，默认 `doubao-seedream-5-0-260128`；另一允许值为 `doubao-seedream-4-5-251128` |
| `model_version` | 两种图片模型都必须省略；不传空字符串 |
| `outputConfig` | camelCase；可含 `size`、`aspectRatio`、`count` |
| `file_infos` | snake_case，对象数组；每项 `url` 为可访问图片地址，`type: image`，`role: reference_image` |

`size` 使用 `宽x高` 字符串，`aspectRatio` 使用 `1:1`、`16:9`、`9:16` 等。默认方图可使用工具文档给出的 `1024x1024`、`1:1` 组合；其他尺寸按运行时模型说明确定，保持尺寸与比例一致，不能把一个方图尺寸硬配成长图比例。若服务端不接受某档尺寸，解释参数错误，不静默改动用户指定比例。

`count` 为整数 1～4，缺省 1；它拆成多条独立任务，每条 1 张。超过 4 张时仅在用户已授权总数量和费用范围内分批，保存每批 `taskIds`，不重复提交整批。不要同时使用兼容字段 `taskQuantity`。

## 无参考图示例

```json
{
  "prompt": "白色陶瓷咖啡杯放在浅色木桌上，窗边柔和自然光，杯口有薄雾，干净的产品摄影画面",
  "model": "doubao-seedream-5-0-260128",
  "outputConfig": {
    "size": "1024x1024",
    "aspectRatio": "1:1",
    "count": 1
  }
}
```

参考图在上述参数中增加 `file_infos`，从用户素材或客户端真实上传结果取 `url`，每项结构为 `{ "url": "实际素材地址", "type": "image", "role": "reference_image" }`。这里的占位文字不能直接提交。没有可访问地址时先获取材料，不调用其他工具擅自上传。

## 返回与限制

提交后记录 `conversationId`、`messageId`、`taskId`、`taskIds`；用于查询的只有任务 ID。批量优先使用 `taskIds` 的全部 ID，单图可回退到 `taskId`，去重后逐个查询。

不要传 `MODEL-000xxx`、展示名称或自创模型版本。参考图生成不能保证逐像素保留 Logo、文字或人脸；用户要求完全原样裁剪/缩放时，说明这是图像处理需求，不能假装本生成工具是无损编辑器。
