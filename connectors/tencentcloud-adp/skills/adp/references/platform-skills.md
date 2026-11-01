# 平台 Skill：发布、引用与共享

`adp skill` 管的是平台技能目录里的 Skill，不是本配套 skill。

```bash
adp skill release --skill-id <id> --space-id <id> --format json      # 新建/更新后要发布，应用才能用；可重复执行
adp skill refs --skill-id <id> --space-id <id> --format json         # 谁在用：应用、智能体、用户
adp skill categories --format json                                   # 分类 key
adp skill share submit --skill-id <id> --space-id <id> --remark <说明> --yes   # 共享到企业技能中心
adp skill share withdraw --skill-id <id> --space-id <id> --yes                # 撤回共享
adp skill share approval --approval-id <id> --format json
```

- Skill zip 根目录必须有 `SKILL.md`，且带 YAML front matter，至少包含 `name` 和 `description`，否则 `skill create` 报 450020：

  ```markdown
  ---
  name: my-skill
  description: 一句话说明这个 Skill 做什么、什么时候用
  ---
  ```

- 创建或更新后平台会做约 2 分钟的安全扫描。扫描期间 `skill release` 报 450028、`skill delete` 报 450063，CLI 都报 `SkillScanning`（`retryable: true`），next_action 就是原命令：等 30 秒左右再执行，最多等几分钟，不要改包重传。扫描中的 Skill 不出现在 `skill list` 里，列表里找不到不代表没建成。
- `skill list` / `plugin list` 必须有空间：没传 `--space-id` 又不在 `adp.jsonc` 项目里时报 `UsageError`（exit 2），next_action 是 `adp space list`。
- 不传 `--version-id` 时用当前版本。
- Skill 标识（`--name`）重名报 450021（CLI 报 `SkillNameTaken`，消息里写的是你创建时用的空间；平台原文不说明范围，内部记录为全企业唯一，跨空间是否可重名未实测）。换一个名字，不要去删别人的同名 Skill。`skill list --query <词>` 按名称/展示名称模糊查找，先查再起名。
- `skill release` 撞上安全扫描（450028）时 CLI 报 `SkillScanning`（`retryable: true`）：等一两分钟再执行同一条命令。
- `skill get` 查不到时报 `SkillNotFound`（平台码 450002，文案「技能不存在」）。450002 在别的接口表示无权限，CLI 只按「技能不存在」文案映射。刚创建的 Skill 在安全分析（`AnalysisStatus` 1）结束前不出现在 `skill list` 里，可能要好几分钟，所以重试 create 撞 450021 时多半是自己刚建的：用第一次 create 返回的 `skillId`，不要换名再建。
- 共享和撤回对其他空间可见，先问用户；返回 `pending_approval` 表示等审批，不要替用户催审。
- 撤回时其他空间还在用会报 `SkillShareInUse`，把引用方列给用户，用户明确同意才加 `--force`。
- 删除或大改前先跑 `skill refs`，告诉用户会影响哪些应用。
