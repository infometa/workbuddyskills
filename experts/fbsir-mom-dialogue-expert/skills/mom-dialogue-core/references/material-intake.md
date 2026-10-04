# 生活资料与来源事务

先确认用户选定的工作区、项目目录和授权来源。一个工作区可采用 `工作区/原有生活资料/` 与 `工作区/妈妈问答_整理结果/` 结构；项目目录自动排除。专业项目也可把项目与来源根分开。原件始终只读。

## 标准顺序

`REGISTER ROOT → SCAN → VALIDATE RECEIPT → DIFF → REVIEW → COMMIT`。

```text
init_project.py <project>
register_source_root.py <project> <authorized_root> --label "标签"
scan_sources.py <project> --root-id ROOT-... --hash-mode incremental|full
validate_scan_receipt.py <project> SCAN-...
diff_sources.py <project> --scan-id SCAN-...
commit_sources.py <project> SCAN-... --approve-diff-sha256 <digest>
```

SCAN 的 inventory 和 hashes 都进入 staging，并由回执绑定文件 SHA-256 与组合摘要。只有完整回执、当前正式账本摘要未改变且用户复核了差异摘要，COMMIT 才能原子更新来源账。`--confirm-empty`、`--confirm-missing` 和 `--accept-migrations` 都是额外的明确确认。

## 多来源与续接

来源身份是 `root_id::relative_path`。每个根独立维护在线状态、最近成功扫描和排除目录；离线根不会制造缺失。增量扫描可复用 size/mtime 未变的哈希，需强制重验时使用 full。文件同根改名且哈希唯一时产生迁移候选；跨根同哈希保持新 `SRC` 并提示重复，不自动合并。

任何新增、修改、迁移或缺失都在复核后写入检查点。只重分析差异行，已确认来源和锁定章节不静默改写。
