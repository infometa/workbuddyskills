# 秘宝 26.9.2 Agent 专家候选

秘宝在不改动原件的前提下，实际完成影像盘点、严格 SHA-256、精确重复识别、SQLite FTS5 本地索引、项目检索和可打开报告。当前只开放 `inventory_build` 与 `inventory_search`，不安装或连接本地 MCP、连接器或常驻服务。

## 第一次使用

1. 召唤“秘宝”，选择“扫描我授权的影像文件夹…”推荐问题。
2. 提供并确认一个绝对源目录、一个互不包含的绝对项目目录和项目显示名。
3. 秘宝只读源目录，在项目目录生成 `project.json`、SQLite 数据库、索引和 HTML/CSV/JSONL/manifest 报告。
4. 秘宝回读报告后给出发现文件、资产、严格重哈希、精确重复组、索引与异常数量。
5. 后续可使用“检索已有秘宝项目”或“更新已有秘宝项目”推荐问题。

严格有效的 one-shot 请求绑定宿主给出的绝对请求根与固定作用域，并在访问源目录或项目目录前被消费；无效、错根或清理失败请求不作自动清理承诺。项目检索只接受 `local-private`，旧隐私模式会失败关闭且不会自动迁移。

单个不符合闭合路径策略的文件名或 reparse 条目会被明确排除，不会读取、跟随、哈希或索引；其受限相对路径和原因随 `partial` 结果返回。真正不可读、源离线、身份变化或预算超限仍阻断。项目目录可以不存在，也可以是预先创建的完全空目录。

检索文件名时，点作为白名单 token 分隔符，`normal.jpg` 会同时匹配 `normal` 与 `jpg`；FTS 操作符、通配符、引号和路径符仍拒绝。

重复组统计中，`content.exactDuplicateGroupCount` 表示本次严格哈希确认值；报告的严格 token 时点值是 `strict_as_of_exact_duplicate_group_count`。`current_exact_duplicate_group_count=0` 是防止把 token 后文件系统竞态误报为实时重复结论的保守语义。

## 当前不包含

格式转换、OCR、ASR、人物/事件识别、视觉/语义检索、片段导出、素材包和成片都未进入本版执行面。缺少报告回读、证据引用或边界回执时，不得把任务报告为完成。

## 版本变更

- 26.9.2（QA 修复）：修复 Windows 上含可执行文件（`.exe`/`.bat`/`.cmd`/`.com`）的源目录必然盘点失败的问题。CPython 在 Windows 上 `os.stat()` 会按扩展名合成执行位而 `os.fstat()` 不会，媒体探测的 stat↔fstat 身份比对使用了原始 `st_mode`，导致可执行文件被确定性误判为"身份已变"（MB-FS-0006 → scan_candidate_stale → fail-closed）。现改为只比较文件类型位（`stat.S_IFMT`），与哈希管线 `_same_open_identity` 的既有正确写法一致；防篡改语义（device/inode/size/mtime）不变。
- 26.8.30：首次提交范围（`execution_core_v1`）。

## 随包说明

- [当前提交范围](TASKBOOK.md)
- [隐私说明](PRIVACY.md)
- [第一方许可](LICENSE)
- [第三方通知](THIRD_PARTY_NOTICES.md)

本包已通过本地、独立解压和 isolated Expert Manager 门；当前后继尚未通过活动 WorkBuddy 会话、自包含 Windows、企业上传、正式提审或上架门。
