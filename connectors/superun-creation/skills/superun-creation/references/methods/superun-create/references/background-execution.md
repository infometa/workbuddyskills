# 云端命令执行包装

先读取 [宿主后台工具](host-tools.md#后台进程)。以下仅用于 superun-ai。

按 [运行脚本](../scripts/run-cli.mjs) 的链接解析其绝对路径，将下面的命令作为宿主进程工具的 command，工具参数从宿主工具小节取得：

```sh
"<已核实的 node 绝对路径>" "<run-cli.mjs 的绝对路径>" --out-dir "<宿主临时目录>/superun-chat-wait-<时间戳>" -- "<CLI 绝对路径>" chat wait "<原 sessionId>" --timeout 600
```

create/send/reply/select/test/review 同样通过包装器提交一次，只替换已授权的业务命令。输出目录由 run-cli 创建，不预先 mkdir，也不复用上一次的目录名。输入处理与具体参数见 [命令表](commands.md)。

CLI 的 --timeout 是业务等待窗口，宿主命令寿命与一次读取超时是不同参数。保留原进程标识与 run-cli 输出目录，终态后读取 stdout.json、stderr.log、exit.json；收到 NEEDS_INPUT / NEEDS_SELECTION 后进入问答，不继续 wait/state。结果已消费或通知丢失时优先读取该次保存的输出，业务恢复遵循 [固定循环](state-and-recovery.md)，不重新 create/send。
