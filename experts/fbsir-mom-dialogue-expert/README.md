# 福帮手·妈妈问答

WorkBuddy Agent 型专家，正式职业为“妈妈生活资料整理与家庭故事编纂专家”。它以一位或多位妈妈为主要叙事对象，整理照片、视频、录音、手稿、书信、证件、聊天、文档和旧稿，建立来源锚点、人物关系、生活轨迹、故事卡、追问、家庭行动、章节与可编辑作品。

## 产品边界

妈妈是叙事主轴，但家庭成员可以提供生活资料、补充讲述、核对人物和事件、保留不同记忆版本并参与共同故事。不得假设年龄、代际数量、亲缘形式、发起人身份、妈妈是否健在、是否愿意录音或是否愿意公开。正式产品只使用“生活资料”“生活轨迹”“故事卡”“家庭回声”“来源锚点”“家庭主编”等术语。

## 安全与隐私

原始资料只读；本包不移动、覆盖或删除原件。脚本不联网、不上传资料、不调用外部 Skill、Connector、MCP、其他专家或子Agent。家庭资料默认不做 Web 检索；只有用户明确要求公开背景补充时，才可使用最小化搜索，而且不能上传姓名、路径、原始文件或媒体内容。WorkBuddy 宿主可能按用户选择的模型与设置处理对话或媒体，相关数据边界以宿主当前隐私设置为准。

## 一个工作区即可启动

选择家庭资料工作区后，在其中创建独立结果目录：

```text
家庭资料工作区/
├── 原有照片、视频、录音和文档/
└── 妈妈问答_整理结果/
```

项目目录自动排除；专业用户也可将结果项目放在工作区外，并登记多个授权来源根。所有项目输出都经过符号链接、junction、reparse point、路径越界与原子写保护。

## 来源事务

顺序固定为：

```text
REGISTER ROOT → SCAN → VALIDATE RECEIPT → DIFF → REVIEW → COMMIT
→ ANALYZE → VALIDATE → CHECKPOINT
```

```bash
python scripts/init_project.py <project>
python scripts/register_source_root.py <project> <authorized_root> --label "主工作区"
python scripts/scan_sources.py <project> --root-id ROOT-... --hash-mode incremental
python scripts/validate_scan_receipt.py <project> SCAN-...
python scripts/diff_sources.py <project> --scan-id SCAN-...
python scripts/commit_sources.py <project> SCAN-... --approve-diff-sha256 <printed-digest>
```

`source-roots.json` 独立记录每个来源根、授权路径、在线状态、最近成功扫描和排除目录。`source_key = root_id::relative_path`；同名路径来自不同根时不会互相覆盖。增量扫描可复用 size/mtime 未变的哈希，强制重验使用 `--hash-mode full`。空、离线、部分或中断扫描不会批量产生缺失。移动/改名只有同根哈希唯一且经 `--accept-migrations` 才保留原 `SRC`；跨根同哈希保持新身份。

## Schema 与续接

`skills/mom-dialogue-core/schemas/schema-catalog.json` 是唯一字段源。`build_project_ledgers.py <project>` 只读检查；创建或迁移使用 `--fix` 或 `migrate_schema.py <project>`，先备份再原子写入。`validate_project.py` 校验 Schema、ID、外键、来源、媒体时间码、故事卡三层文本、章节、权限、检查点和未完成事务。`recover_source_commit.py` 只按物理 pre/post 摘要收束中断提交。

续接时先读项目看板、来源根和最新检查点，只处理新增、修改或 `needs_reanalysis=yes` 的资料；已确认资料和锁定章节不静默重写。每轮只给一个推荐下一步。

## 首轮首值与宿主能力

WorkBuddy 宿主负责文件读取/搜索/写入、图片/PDF/音频/视频多模态处理、结果预览、Memory 与 Automation。材料足够时首轮应生成素材地图、来源账、质量/重复候选、人物候选、至少一张带来源的故事卡、资料驱动追问和项目看板；能力不足时写入待处理队列并降级为 Markdown、CSV、JSON 或 HTML。Memory 只保存文风、方言、叙事人称、章节长度、图说和输出格式偏好；Automation 仅在用户主动配置后运行，绝不自动发消息或公开资料。

## 权限与交付

公开或成稿交付前先运行：

```bash
python scripts/create_delivery_selection.py <project> --scope public --output 08_故事卡/STY-...md
python scripts/validate_permissions.py <project> --scope public
python scripts/export_delivery_manifest.py <project>
```

权限冲突采用更严格范围；待确认、争议、撤回、未匿名或敏感未复核内容会被阻断。权限通过只证明本地选择与校验，不证明官方上架、宿主加载或自然业务闭环。

## 开发与发行

开发源码包包含测试、夹具、Schema、脚本和构建说明；官方审核包只包含运行、审核与必要参考文件，不包含缓存、临时文件、会改写自身的测试报告或无关开发资产。最终发行顺序是：在开发副本测试 → 生成报告 → 构建精简审核树 → 生成并验证清单 → 打 ZIP → 解压复验 → 计算 ZIP 外 SHA-256。官方 `validate_expert.py`、`register_expert.py`、`package_expert.py` 仅在隔离的 `my-experts` 演练目录执行；真实宿主注册、重载、市场审核与上架仍需发布方授权。

## 许可与品牌

本包使用福帮手专有最终用户评估许可，详见 `LICENSE`、`TERMS.md`、`PRIVACY.md`、`SECURITY.md`、`RIGHTS-NOTICE.md`、`METHODOLOGY.md` 和 `THIRD-PARTY-NOTICES.md`。头像使用用户提供的福帮手正式 Logo 的无损比例缩放版本，不宣称授予商标、分发或商业合作权。
