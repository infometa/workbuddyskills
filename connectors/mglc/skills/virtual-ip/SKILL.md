---
name: mglc-virtual-ip
description: 灵创SD 合规素材库管理技能 - 创建、查询、更新、删除SD 合规素材库资产，用于真实IP创作
version: "1.0.0"
author: "灵创 AI"
---

# 灵创SD 合规素材库管理 Skill

本 Skill 提供SD 合规素材库 资产管理能力，用于创建和管理虚拟角色、形象等素材，配合seedance系列视频模型进行真实IP创作（参考真实人脸、音频等进行AI创作）。

## 可用命令

### virtual-ip list - 列出SD 合规素材库

列出当前企业空间下的SD 合规素材库 资产。

**命令**：
```bash
# 列出所有SD 合规素材库
mglc virtual-ip list

# 按类型筛选
mglc virtual-ip list --type image

# 按状态筛选
mglc virtual-ip list --status active

# 按名称搜索
mglc virtual-ip list --keyword "角色名"

# 分页查询
mglc virtual-ip list --page 1 --page-size 20
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --type | string | - | 资产类型筛选：image / video / audio |
| --status | string | - | 按状态筛选：processing / active / failed |
| --keyword | string | - | 按名称模糊搜索 |
| --page | int | - | 页码，默认 1 |
| --page-size | int | - | 每页数量，默认 20 |

### virtual-ip upload - 创建SD 合规素材库

创建SD 合规素材库 资产，创建后异步审核。

**命令**：
```bash
# 上传本地文件创建
mglc virtual-ip upload --name "角色名" --type image --file /path/to/portrait.png

# 通过URL创建
mglc virtual-ip upload --name "角色名" --type image --file-url https://example.com/portrait.png
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --name | string | ✓ | 资产名称 |
| --type | string | ✓ | 资产类型：image / video / audio |
| --file | string | - | 资产文件（本地路径或COS路径） |
| --file-url | string | - | 图片 URL（仅图片类型） |

**注意**：`--file` 和 `--file-url` 至少需要一个。

### virtual-ip info - 查看SD 合规素材库详情

查看一个SD 合规素材库 资产的审核状态和可用性。

**命令**：
```bash
mglc virtual-ip info <asset_id>
```

### virtual-ip rename - 修改SD 合规素材库名称

修改SD 合规素材库 名称。

**命令**：
```bash
mglc virtual-ip rename <asset_id> --name "新名称"
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| asset_id | int64 | ✓ | 资产 ID |
| --name | string | ✓ | 新名称 |

### virtual-ip delete - 删除SD 合规素材库

软删除SD 合规素材库。

**命令**：
```bash
mglc virtual-ip delete <asset_id> --yes
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| asset_id | int64 | ✓ | 资产 ID |
| --yes | bool | ✓ | 跳过交互确认 |

## 使用建议

1. **上传审核**：创建SD 合规素材库 后需要等待审核通过才能使用
2. **状态跟踪**：使用 `info` 命令查看审核状态
3. **类型选择**：根据素材类型正确选择 image/video/audio
4. **命名规范**：建议使用清晰的命名便于后续管理
5. **配合使用**：创建通过后可在视频生成中作为(角色/场景/道具)设定参考
