# 调优准则与用户反馈

## 调优准则（`adp guideline`）

准则写的是「在什么场景下应该怎么答」，应用回答时会遵循。所有命令都需要 `--app-id`，不传时读取 `adp.jsonc` 里的应用。

```bash
adp guideline create --content "报价时注明数据日期" --apply-scene "行情报价类问题" --format json
adp guideline list --status candidate --format json        # 待采纳的生成结果
adp guideline enable --guideline-id <id> --guideline-id <id>
adp guideline disable|delete --guideline-id <id> ...
adp guideline changes --format json                        # 下次发布会带上的准则改动
```

- 手动创建的准则直接是 `enabled`。从评测生成的准则先是 `candidate`，执行 `enable` 就等于采纳。准则不能改回 `candidate`。
- 准则改动要 `adp deploy` 之后才对终端用户生效。发布前可以用 `changes` 核对一遍。
- `enable` / `disable` 会返回 `succeeded` 和 `failed`。只要有一部分成功，命令就不算失败，记得检查 `failed` 列表。
- `delete` 是全有或全无：先逐个查 ID，任何一个不存在就报 `GuidelineNotFound`（退出码 3），一条都不删。

### 从评测生成准则

```bash
adp guideline task create --evaluation-id <id> --model Hunyuan/hy3 --name 九月标注提炼
adp guideline task get --task-id <id> --format json     # 查看生成数量和准则 ID
adp guideline list --task-id <id> --status candidate
adp guideline task create --from-task-id <id>           # 复用原任务的配置再生成一次
```

生成任务需要一个已经完成人工标注的评测，评测本身目前在控制台创建。

### 调试反馈自动提炼

```bash
adp guideline auto-distill set --enable --model Hunyuan/hy3
adp guideline auto-distill get --format json
```

开启后，平台会把调试面板里的反馈提炼成候选准则。第一次开启时必须指定 `--model`。

## 终端用户反馈（`adp feedback`）

```bash
adp feedback list --reason 回答错误 --format json
adp feedback get --feedback-id <id>
adp feedback create --record-id <回复记录ID> --session-id <会话ID> --question "…" --answer "…" --reason 回答错误 --accept-terms
adp feedback delete --feedback-id <id> --yes
```

- 平台按应用模式分开存储反馈，CLI 会自动读取应用的模式。
- `--record-id` 要填被反馈的那条回复的记录 ID，不是提问的记录 ID。
- 提交反馈等于同意平台服务条款。只有在用户明确同意后，才加 `--accept-terms`。
- `--question` 和 `--answer` 都必填，缺任何一个平台都会报参数异常。
- 删除前，CLI 会逐个核对反馈是否属于这个应用，不属于的会拒绝删除。

## 同义词（`adp synonym`）

```bash
adp synonym create --word 可口可乐 --synonym 可乐 --synonym coke --format json
adp synonym list --unreleased --format json
adp synonym export --output synonyms.xlsx
adp synonym import --file synonyms.xlsx
```

- 一个词在应用里只能出现一次（标准词或某个同义词）。冲突时命令报 `SynonymConflict`，消息会指出冲突的词现在是标准词还是哪个标准词的同义词，按 `next_actions` 里的 `synonym list --query` 找到已有条目再改。
- 导入只接受 `.xlsx`。`export` 出的文件（包括没有数据、只有表头的导出）可以直接当模板改了再导入；不要改表头，标准词和同义词都不能留空，同义词一行一个。已有的词会被跳过，不会覆盖。
- 导入是异步落库的，命令返回后几秒内 `synonym list` 才能看到。文件有错时报 `SynonymImportFailed`，CLI 会把平台标注过错误行的文件存成 `<原文件名>.errors.xlsx`，打开看每行的原因。
- 同义词改动同样要 `adp deploy` 后才生效。

## 不满意回复（`adp unsatisfied`）

```bash
adp unsatisfied list --status pending --format json
adp unsatisfied get --reply-id <id>          # 看上下文
adp unsatisfied handle --reply-id <id> --status ignored
adp unsatisfied export --output unsatisfied.xlsx
```

- 「加入问答」「加为相似问」目前只能在控制台操作，CLI 只做拒答和忽略。
- 点踩原因标签用 `adp unsatisfied label` 管理。
