---
name: mglc-project
description: 灵创项目管理技能 - 项目、剧集、剧本、分镜、(角色/场景/道具)设定的完整创作工作流管理
version: "1.0.0"
author: "灵创 AI"
---

# 灵创项目管理 Skill

本 Skill 提供完整的创作工作流管理能力，涵盖项目、剧集、剧本、分镜和(角色/场景/道具)设定的全生命周期操作。

## 项目管理

### project list - 列出项目

分页列出当前用户有权限访问的项目。

**命令**：
```bash
mglc project list
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --page | int | - | 页码，默认 1 |
| --page-size | int | - | 每页数量，默认 20 |

### project show - 查看项目详情

查看项目详细信息。

**命令**：
```bash
mglc project show <project_id>
```

### project create - 创建项目

创建新项目。

**命令**：
```bash
# 基本创建
mglc project create --name "项目名称"

# 带描述和封面
mglc project create --name "项目名称" --description "项目描述" --cover /path/to/cover.jpg
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --name | string | ✓ | 项目名称 |
| --description | string | - | 项目描述 |
| --cover | string | - | 封面图片路径 |

### project update - 更新项目

修改项目基础信息。

**命令**：
```bash
mglc project update <project_id> --name "新名称"
mglc project update <project_id> --description "新描述"
```

### project delete - 删除项目

删除项目。

**命令**：
```bash
mglc project delete <project_id> --yes
```

## 剧集管理

### episode list - 列出剧集

列出项目下的剧集。

**命令**：
```bash
mglc episode list --project-id <project_id>
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |

### episode create - 创建剧集

创建新剧集。

**命令**：
```bash
# 创建第1集
mglc episode create --project-id <project_id> --episode 1 --name "第一集"

# 带描述
mglc episode create --project-id <project_id> --episode 1 --name "第一集" --description "剧集描述"
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --episode | int | - | 集号 |
| --name | string | - | 剧集名称 |
| --description | string | - | 剧集描述 |

### episode update - 更新剧集

修改剧集信息。

**命令**：
```bash
mglc episode update <episode_id> --project-id <project_id> --name "新名称"
```

### episode delete - 删除剧集

删除剧集。

**命令**：
```bash
mglc episode delete <episode_id> --project-id <project_id> --yes
```

## 剧本管理

### script show - 查看剧本

查看项目下的剧集的剧本详情。

**命令**：
```bash
mglc script show --project-id <project_id> --episode-id <episode_id>
```

### script create - 创建剧本

创建项目剧集的剧本。

**命令**：
```bash
# 直接传入内容
mglc script create --project-id <project_id> --episode-id <episode_id> --content "剧本内容..."

# 从文件读取
mglc script create --project-id <project_id> --episode-id <episode_id> --content ./script.txt
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --episode-id | int64 | ✓ | 剧集 ID，必填 |
| --content | string | ✓ | 剧本内容（文本或文件路径） |

## 分镜管理

### storyboard list - 列出分镜

分页列出剧集分镜。

**命令**：
```bash
mglc storyboard list --project-id <project_id> --episode <episode_number>
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --episode | int | ✓ | 集号 |
| --page | int | - | 页码，默认 1 |
| --page-size | int | - | 每页数量，默认 20 |

### storyboard show - 查看分镜详情

查看分镜详细信息。

**命令**：
```bash
mglc storyboard show <shot_id> --project-id <project_id>
```

### storyboard add - 添加分镜

创建新分镜。

**命令**：
```bash
# 基本创建
mglc storyboard add --project-id <project_id> --episode <episode_number> --scene-order <scene_order> --shot-name <shot_name>

# 带画面描述
mglc storyboard add --project-id <project_id> --episode <episode_number> --scene-order <scene_order> --shot-name <shot_name> --prompt <prompt>

# 指定插入位置
mglc storyboard add --project-id <project_id> --episode <episode_number> --prev-shot-id <id> --scene-order <scene_order> --shot-name <shot_name>

# 批量创建
mglc storyboard add --project-id <project_id> --episode <episode_number> --scene-order <scene_order> --shot-name <shot_name> --number <number>
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --episode | int | ✓ | 集号 |
| --scene-order | int | ✓ | 场次序号 |
| --shot-name | string | ✓ | 分镜名称 |
| --prev-shot-id | int64 | - | 插入到指定分镜之后 |
| --next-shot-id | int64 | - | 插入到指定分镜之前 |
| --number | int | - | 一次创建数量，默认1 |
| --prompt | string | - | 分镜画面描述 |
| --duration | int | - | 分镜时长（秒） |
| --voice | string | - | 对白/旁白/音效 JSON |
| --remark | string | - | 备注 |

### storyboard update - 更新分镜

修改分镜信息。

**命令**：
```bash
# 修改名称
mglc storyboard update <shot_id> --project-id <project_id> --shot-name <shot_name>

# 修改画面描述
mglc storyboard update <shot_id> --project-id <project_id> --prompt <prompt>

# 修改时长
mglc storyboard update <shot_id> --project-id <project_id> --duration <duration>
```

### storyboard delete - 删除分镜

删除分镜。

**命令**：
```bash
mglc storyboard delete <shot_id> --project-id <project_id> --yes
```

### storyboard views - 查看剧集视图

查看剧集视图列表。

**命令**：
```bash
mglc storyboard views --project-id <project_id> --episode-id <episode_id>
```

## 设定管理

项目(角色/场景/道具)设定的创建、查询、更新和删除。

### subject list - 列出(角色/场景/道具)设定

列出当前可见范围内的项目或剧本设定。

**命令**：
```bash
# 列出项目下的所有设定
mglc subject list --project-id <project_id>

# 按类型筛选
mglc subject list --project-id <project_id> --type <role|scene|prop>

# 按名称搜索
mglc subject list --keyword "角色名"

# 分页查询
mglc subject list --project-id <project_id> --page 1 --page-size 20
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | - | 项目 ID |
| --script-id | int64 | - | 剧本 ID |
| --type | string | - | 设定类型：role（角色）/ scene（场景）/ prop（道具） |
| --keyword | string | - | 按设定名称搜索 |
| --member-id | int64[] | - | 设定归属成员 ID，可重复传递 |
| --page | int | - | 页码，默认 1 |
| --page-size | int | - | 每页数量，默认 20 |

### subject create - 创建(角色/场景/道具)设定

创建角色、场景或道具设定。

**命令**：
```bash
# 创建角色设定（带图片）
mglc subject create --project-id <project_id> --type role --name "男主角" --image /path/to/avatar.png

# 创建角色设定（带图片和音频）
mglc subject create --project-id <project_id> --type role --name "女主角" --image /path/to/avatar.png --voice /path/to/voice.mp3

# 创建场景设定
mglc subject create --project-id <project_id> --type scene --name "咖啡馆" --description "温馨的咖啡馆内景"

# 创建道具设定
mglc subject create --project-id <project_id> --type prop --name "神秘宝箱" --description "发光的古老宝箱"
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --type | string | ✓ | 设定类型：role / scene / prop |
| --name | string | ✓ | 设定名称 |
| --description | string | - | 设定描述 |
| --image | string | - | 设定图片本地路径 |
| --voice | string | - | 音频本地路径（仅角色类型） |

### subject update - 更新设定

更新设定信息。

**命令**：
```bash
# 修改名称
mglc subject update <subject_id> --project-id <project_id> --name "新名称"

# 修改描述和图片
mglc subject update <subject_id> --project-id <project_id> --description "新描述" --image /path/to/new.png
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| subject_id | int64 | ✓ | 设定 ID |
| --project-id | int64 | ✓ | 项目 ID |
| --name | string | - | 设定名称 |
| --description | string | - | 设定描述 |
| --image | string | - | 设定图片本地路径 |
| --voice | string | - | 音频本地路径（仅角色类型） |

### subject delete - 删除(角色/场景/道具)设定

删除设定。

**命令**：
```bash
mglc subject delete <subject_id> --project-id <project_id> --type role --yes
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| subject_id | int64 | ✓ | 设定 ID |
| --project-id | int64 | ✓ | 项目 ID |
| --type | string | ✓ | 设定类型：role / scene / prop |
| --yes | bool | ✓ | 跳过交互确认 |

## 会话管理

项目生成会话的创建、查询、更新和删除，用于管理 AI 生成的会话上下文。配合video、image技能使用。

### session list - 列出会话

列出项目下的生成会话。

**命令**：
```bash
# 列出项目聚集下的所有会话
mglc session list --project-id <project_id> --episode <episode_number>
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --episode | int | - | 剧集编号 |

### session create - 创建会话

创建新的剧集生成会话。

**命令**：
```bash
# 指定剧集和剧本
mglc session create --project-id <project_id> --episode-id <episode_id> --name "第1集会话"
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --project-id | int64 | ✓ | 项目 ID |
| --name | string | ✓ | 会话名称 |
| --episode-id | int64 | ✓ | 剧集 ID |

### session update - 更新会话

修改会话名称。

**命令**：
```bash
mglc session update <session_id> --project-id <project_id> --name "新名称"
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| session_id | int64 | ✓ | 会话 ID |
| --project-id | int64 | ✓ | 项目 ID |
| --name | string | ✓ | 新会话名称 |

### session delete - 删除会话

删除生成会话，可选择迁移记录到其他会话。

**命令**：
```bash
# 直接删除
mglc session delete <session_id> --project-id <project_id> --yes

# 删除前迁移记录到目标会话
mglc session delete <session_id> --project-id <project_id> --dst-session-id <target_session_id> --yes
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| session_id | int64 | ✓ | 会话 ID |
| --project-id | int64 | ✓ | 项目 ID |
| --dst-session-id | int64 | - | 目标会话 ID，传入时先迁移记录再删除 |
| --yes | bool | ✓ | 跳过交互确认 |

## 使用建议

1. **工作流**：创建项目 → 添加剧集 → 编写剧本 → 创建设定（角色/场景/道具） → 创建分镜 → 创建会话 → AI 生成
2. **项目隔离**：建议为每个创作任务创建独立项目
3. **剧集组织**：按集号顺序创建，便于管理
4. **剧本格式**：建议使用标准剧本格式，包含场景、对白、动作描述
5. **设定分类**：角色（role）、场景（scene）、道具（prop）三类
6. **分镜创建**：按场次序号（scene-order）顺序创建，用 `--number` 批量创建空分镜
7. **本地文件**：图片和音频支持本地路径，CLI 会自动上传处理
8. **会话管理**：会话用于保存 AI 生成上下文，删除时可迁移记录到其他会话
