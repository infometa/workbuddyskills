---
name: mglc-image
description: 灵创图片生成技能 - 根据提示词生成图片、图生图、图片超分、结果查询
version: "1.0.0"
author: "灵创 AI"
---

# 灵创图片生成 Skill

本 Skill 提供 AI 图片生成能力，支持文生图、图生图和图片超分。

## 可用命令

### image generate - 生成图片

根据提示词和参考图生成图片。

**命令**：
```bash
# 基础生成（比例和分辨率必须同时指定）
mglc image generate --model-id <model_id> --prompt "图片描述" --ratio 1:1 --resolution 1K

# 生成多张
mglc image generate --model-id <model_id> --prompt "图片描述" --num 4

# 带参考图（图生图）
mglc image generate --model-id <model_id> --prompt "图片描述" --image /path/to/ref.jpg

# 多张参考图
mglc image generate --model-id <model_id> --prompt "图片描述" --image /path/ref1.jpg --image /path/ref2.jpg
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --model-id | int64 | ✓ | 图片模型 ID |
| --prompt | string | ✓ | 图片描述词（越详细效果越好） |
| --ratio | string | ✓ | 图片比例（如 1:1, 16:9, 4:3, 3:4），需与 `--resolution` 同时提供 |
| --resolution | string | ✓ | 图片分辨率，需与 `--ratio` 同时提供 |
| --num | int | - | 生成数量，默认1，最大4 |
| --image | string[] | - | 参考图路径，可重复指定多张 |
| --session-id | int64 | - | 项目会话 ID，用于关联项目 |

**使用示例**：
- 生成赛博朋克风格的城市夜景
- 基于角色参考图生成新姿势
- 批量生成产品设计稿
- 创建概念艺术图
**注意事项**：
- 不同模型有不同的生成参数和参数范围，在生成前先查看模型能力，避免参数错误
- ratio和resolution必须全部指定

### image upscale - 图片超分

提交图片高清任务，提升图片分辨率。

**命令**：
```bash
# 提升到 4096px
mglc image upscale <image_id> --resolution 4096

# 提升到 6144px
mglc image upscale <image_id> --resolution 6144
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| image_id | int64 | ✓ | 图片 ID |
| --resolution | int | ✓ | 目标最大边，支持 2048-6144 |
| --session-id | int64 | - | 项目会话 ID |

## 使用建议

1. **先查模型**：使用 `mglc model list --type image` 查看可用模型
2. **Prompt 优化**：描述越详细越好，建议包含风格、(角色/场景/道具)设定、环境、光线等元素
3. **参考图**：图生图时，参考图质量直接影响效果
4. **批量生成**：不确定效果时，用 `--num 4` 生成多张挑选最佳
5. **本地文件**：直接传入本地文件路径即可，CLI 会自动上传
6. **进度查询**：图片生成是异步的，用 `task status` 查询结果
