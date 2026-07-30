# Smoke test — study-revision-planner

## 目标

验证该 skill 具备最小可用交付结构，且本地辅助脚本可被解释器加载。

## 检查项

1. `SKILL.md` 存在，且 frontmatter 含 `name`、`description`、`version`
2. `README.md`、`SELF_CHECK.md`、`examples/example-prompt.md` 存在
3. `scripts/` 下至少有一个可执行脚本
4. `resources/` 下至少有一个真实资源文件
5. 运行 `python3 scripts/revision_schedule.py --help` 返回退出码 0

## 人工验证

- 用 `examples/example-prompt.md` 中的触发词在会话中调用 skill
- 检查输出是否覆盖以下内容：
  - revision calendar
  - topic effort table
  - mock test schedule
  - today-next checklist
- 检查是否优先给出预览、草案或确认步骤，而非直接做破坏性操作

## 通过标准

全部检查项通过，即视为 smoke test 通过。
