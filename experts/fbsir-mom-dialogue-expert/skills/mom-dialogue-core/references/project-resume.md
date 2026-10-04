# 项目续接

续接先读取 `00_项目看板/当前状态.md`、`下一步.md`、`续接胶囊.md`、`source-roots.json` 和最新 `12_版本与检查点/` 检查点。对每个在线来源运行完整 SCAN → VALIDATE → DIFF；只重跑新增、修改或明确标记 `needs_reanalysis=yes` 的资料。已确认来源与锁定章节不静默重写。

来源离线、空扫描、部分扫描或中断时保持现有正式账，不产生批量缺失。若存在 prepared 但没有 terminal 的提交，先运行 `recover_source_commit.py`；不能用重跑提交掩盖未收束事务。续接完成后写入新的 CPK，列出新增/变化来源、待确认事项、阻断项和一个推荐下一步。
