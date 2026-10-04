# 工具目录

## 账号与能力

| 工具 | 用途 |
| --- | --- |
| `studio_get_current_account` | 核对 OAuth 绑定账号、权限和生成能力 |
| `studio_get_balance` | 查询当前可消费、冻结和到期 Studio 积分 |
| `studio_get_generation_catalog` | 查询后台当前开放的模型、画质、时长和默认参数 |

## 素材与画布读取

| 工具 | 用途 |
| --- | --- |
| `material_list` | 分页查询当前账号图片、视频和音频素材 |
| `material_import_url` | 把公开 HTTPS 素材归档到素材库和 TOS |
| `material_get_upload_instructions` | 获取本地文件 multipart 上传要求 |
| `canvas_list_projects` | 查询当前账号画布及最新 revision |
| `canvas_get_project` | 读取完整画布、节点、连线和视口 |
| `canvas_get_node_catalog` | 获取支持的节点、端口和默认尺寸 |
| `canvas_validate` | 校验节点、端口、连线和循环依赖 |
| `canvas_list_versions` | 查询画布历史版本 |

## 画布写入

| 工具 | 用途 |
| --- | --- |
| `canvas_create_project` | 幂等创建空白画布 |
| `canvas_create_workflow` | 在一个事务中创建完整工作流，优先用于新画布 |
| `canvas_apply_operations` | 原子执行节点、素材、连线、分组和布局操作 |
| `canvas_rename_project` | 使用最新 revision 重命名画布 |
| `canvas_copy_project` | 复制当前账号的画布 |
| `canvas_restore_version` | 经确认后恢复历史版本并自动备份当前版本 |
| `canvas_delete_project` | 经确认后永久删除指定画布 |

## 生成与任务

| 工具 | 用途 |
| --- | --- |
| `generation_estimate` | 预估生成积分并取得一次性确认令牌 |
| `canvas_estimate_node` | 根据画布节点及前置连线预估积分 |
| `canvas_run_node` | 使用确认令牌运行画布节点并自动回填 |
| `image_generate` / `image_get_task` | 创建和查询图片任务 |
| `video_generate` / `video_get_task` | 创建和查询视频任务 |
| `video_one_click_replace` | 创建一键替换任务 |
| `audio_generate` / `audio_list_speakers` | 生成音频并查询公共音色 |
| `video_extract_frames` / `video_extract_frames_get_task` | 视频抽帧及状态查询 |
| `video_process` / `video_process_get_task` | 视频增强、擦除、去水印或人脸打码 |
| `generation_list_tasks` | 分页查询统一任务历史 |
| `generation_get_task` | 查询任务、归档、扣费、退款与回填状态 |
| `generation_cancel_task` | 经确认后取消仍可取消的任务 |
| `generation_retry_task` | 使用新的确认令牌重试失败或取消任务 |
| `generation_delete_task` | 经确认后删除已结束任务记录，不删除素材 |

工具是否可见取决于当前 OAuth 权限、账号权限及图片、视频、音频能力开关。工具不可见时不得换用其他工具绕过权限。
