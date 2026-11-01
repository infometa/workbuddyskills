# 管道与机器输出

ReelMate CLI 把数据和进度分流：stdout 是数据，stderr 是进度、重试和诊断。脚本只读取 stdout，不要把 stderr 合并进数据管道。

## JSON

单条结果使用 `--json` 输出一个 envelope：

```bash
reelmate node get NODE_ID --canvas CANVAS_ID --json > node.json
jq '.data' node.json
```

成功形状为 `{ "ok": true, "data": ..., "links": [] }`；失败时为 `{ "ok": false, "error": ... }`，同时进程返回非零退出码。

## NDJSON

`--ndjson` 每个事件/记录一行，适合 Agent 持续消费：

```bash
reelmate task wait TASK_A TASK_B --ndjson \
  | while IFS= read -r line; do jq -c '.data // .error' <<<"$line"; done
```

不要用 `2>&1` 合并 stderr，否则进度文本会污染 JSON。需要将成功数据写文件时优先使用 `--out PATH`，CLI 会在命令成功后原子落盘，失败不会覆盖旧文件。

## 安全

token、授权码和签名 URL 不应出现在 argv、shell 历史或日志中。令牌只能通过 `--token-file FILE`、`--token-file -` 或环境变量注入；`--verbose` 会脱敏。
