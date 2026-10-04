---
name: mom-dialogue-core
description: Core WorkBuddy workflow for source-safe family material intake, multimodal indexing, mother-centered questions and stories, permissions, and resumable delivery.
---

# 妈妈问答核心 Skill

## 目标与边界

在用户明确授权的项目目录内，把照片、视频、录音、手稿、书信、证件、聊天、文档和旧稿整理为有来源、可确认、可编辑、可续接的家庭作品。妈妈是一位或多位主要叙事对象；家庭成员可以提供资料、补充讲述、核对和共同创作。所有正式文案使用“生活资料”和“生活轨迹”，不把示例年龄、姓名或家庭结构写进产品规则。

原始资料只读；专家不移动、覆盖、删除、上传或自动公开原件。项目目录必须有 `.mom-dialogue-project.json`，从项目根到目标路径的每一级都必须不是符号链接、junction 或 Windows reparse point。写入统一经过 `scripts/common.py`，使用路径边界检查、CSV 公式注入转义、同目录临时文件、flush/fsync 与原子替换。事务锁由 OS 文件锁提供，进程崩溃不会留下“仍持有”的假锁。

## 外部能力政策

核心流程禁止搜索、安装和调用外部 Skill；同样禁止依赖 Connector、MCP、其他专家或子Agent。家庭资料默认不得联网。只有用户明确要求补充公开时代、地域或机构背景时，才可使用最小化 Web 搜索，并且不上传原始资料、姓名、联系方式、路径、照片、录音、视频或聊天内容。WorkBuddy 的文件、搜索、写入、脚本、多模态、Memory、Automation 和结果预览能力足以启动本流程；缺少某种能力时走降级队列而不是等待外部 Skill。

## 最小参考路由

只在当前任务需要时读取对应文件：

- 产品与术语：`@references/product-charter.md`、`@references/terminology.md`、`@references/family-model.md`
- 资料与续接：`@references/material-intake.md`、`@references/batch-and-resume.md`、`@references/project-resume.md`
- 能力与降级：`@references/capability-probe.md`
- 照片：`@references/photo-analysis.md`、`@references/photo-grouping-and-album-pages.md`
- 视频：`@references/video-six-track.md`、`@references/video-analysis-protocol.md`、`@references/long-media-batching.md`
- 录音：`@references/audio-and-oral-history.md`、`@references/audio-transcription-quality.md`
- 手稿与文档：`@references/handwriting-and-documents.md`
- 问答：`@references/question-design.md`
- 故事与编排：`@references/story-card.md`、`@references/voice-preservation.md`、`@references/timeline-and-outline.md`
- 权限：`@references/privacy-and-rights.md`、`@references/consent-state-machine.md`
- 交付与体验：`@references/user-experience.md`、`@references/artifact-delivery.md`
- 质量：`@references/quality-gates.md`

## 标准来源事务

一个工作区可直接启动：项目目录放在工作区内的 `妈妈问答_整理结果/`，扫描时自动排除它；专业模式可把项目与来源根分开。严格顺序是：

`REGISTER ROOT → SCAN → VALIDATE RECEIPT → DIFF → REVIEW → COMMIT → ANALYZE → VALIDATE → CHECKPOINT`。

来源根登记表固定写入 `00_项目看板/source-roots.json`。

```text
python scripts/init_project.py <project>
python scripts/register_source_root.py <project> <authorized_root> --label "主工作区" [--exclude subdir]
python scripts/scan_sources.py <project> --root-id ROOT-... [--scope relative/path] [--hash-mode incremental|full]
python scripts/validate_scan_receipt.py <project> SCAN-...
python scripts/diff_sources.py <project> --scan-id SCAN-...
python scripts/commit_sources.py <project> SCAN-... --approve-diff-sha256 <printed-digest> [--accept-migrations] [--confirm-empty] [--confirm-missing]
```

`root_id + relative_path` 是来源身份；不同来源根中的同名文件不会互相覆盖。增量扫描可在 size 与 mtime 未变时复用已提交哈希；需要重新确认内容时使用 `--hash-mode full`。每个 SCAN 回执同时绑定 inventory.csv、hashes.csv 的物理 SHA-256、组合摘要、错误数、跳过数、复用数和来源范围。来源离线、空、部分或中断扫描不得自动制造缺失。移动/改名只有同一来源根、哈希唯一且经过 `--accept-migrations` 才能保留原 `SRC`；跨根同哈希只记录为新身份候选。

兼容入口 `ingest_sources.py` 只接受已生成 DIFF 的 `--scan-id` 与 `--approve-diff-sha256`，从不隐式扫描或覆盖正式账。若 commit 在写入后中断，先执行 `recover_source_commit.py <project> SCAN-...`，它只根据物理 pre/post SHA-256 记录“已提交”或“安全中止”，无法匹配时保持人工介入。

## Schema 与项目校验

`schemas/schema-catalog.json` 是字段与路径的唯一事实源。`build_project_ledgers.py <project>` 只读检查；要创建或迁移必须明确执行 `build_project_ledgers.py <project> --fix` 或 `migrate_schema.py <project>`。迁移先生成时间戳备份、再原子写入；禁止同版本静默改变字段。

`validate_project.py <project>` 校验 JSON Schema 版本、CSV 表头/类型/枚举/ID 唯一性、来源根与扫描回执、`SRC/SEG/PER/REL/EVT/STY/QUE/ANS/ACT/CH/CON/VER` 外键、故事卡来源和三层文本、章节文件、检查点输出、路径安全和未完成事务。新项目可用 `--allow-empty` 做结构检查，但正式交付不能让空来源账或无来源故事卡通过。

## 多模态协议

照片遵循“观察—可见事实—推测—不确定—确认问题”；视频先做文件、镜头、画面、声音、事件、故事六轨索引，片段必须含起止时间码、时间码精度和覆盖状态；录音保留原话、方言、停顿、说话人候选和听不清处；手稿/文档保存原始 OCR、校订稿和成稿。不得通过面部或声音确认身份。图片、PDF、音频、视频或 Office 不可用时写入待处理队列和能力报告，完成仍可做的元数据与文本，降级为 Markdown、CSV、JSON 或 HTML。

## 故事、问题与权限

故事卡必须保留 `source_ids`、`segment_ids`、`person_ids`、与妈妈的关系、来源状态、可见范围和原话稿/整理稿/成稿三层。家庭回声标明讲述者；推断、冲突和未知不能自动进入确认稿。问题来自资料空白、关系、时间线或当下心愿，允许跳过、撤回和设为私密，不固定问题或章节数量。

公开或成稿导出前先用 `create_delivery_selection.py <project> --scope public|manuscript --output <project-file>` 冻结输出文件、来源和对象，再运行 `validate_permissions.py <project> --scope public|manuscript`；它要求显式同意、冲突取最严格、撤回/争议/待确认阻断、匿名和敏感复核有记录且输出未被改动。最后运行 `export_delivery_manifest.py <project>`。权限门通过只证明本地选择和校验，不证明官方上架或自然业务闭环。

## WorkBuddy 宿主、Memory 与 Automation

首轮必须先给真实结果：素材地图、来源账、质量/重复候选、人物候选、至少一张真实故事卡、资料驱动追问、当前状态、项目总览和一个推荐下一步。Memory 只保存文风、方言、叙事人称、章节长度、图片说明和输出格式偏好；人物、事件、原话、来源和权限只能写项目文件。Automation 仅在用户主动配置后整理新增资料、更新进度或生成问题，不能自动发送给家庭成员或公开。

## 脚本清单

`init_project.py`、`register_source_root.py`、`scan_sources.py`、`validate_scan_receipt.py`、`diff_sources.py`、`commit_sources.py`、`recover_source_commit.py`、`detect_exact_duplicates.py`、`build_project_ledgers.py`、`migrate_schema.py`、`validate_project.py`、`create_delivery_selection.py`、`validate_permissions.py`、`build_project_dashboard.py`、`checkpoint_project.py`、`export_delivery_manifest.py`、`init_artifact.py` 和 `update_project_status.py` 都只处理项目内安全路径；所有写入脚本均调用共享安全层。
