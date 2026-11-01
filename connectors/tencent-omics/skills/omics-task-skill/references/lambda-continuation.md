# 多步续跑与增量分析

鼓励 AI 在现有多步定义上拆分、选择和组合实际需要的步骤。完整 workflow 仍是一份维护来源；可以抽取一个 Task，也可以组合任意满足输入合同的后续子图，不必把所有应用改成单步模板集合。

## 决定需要执行的部分

1. 保存源 Run 的冻结定义、实际回执及失败原因。用真实 `steps[].name` 和输入输出名定位，不把数组顺序当依赖。
2. 按本次目标标记最早发生变化的步骤及其下游。输入数据、QC、HVG、PCA、注释、数据库或随机种子变化可能使不同范围的结果失效。只改变图例通常不需要重新推断；只改变聚类分辨率可在应用支持的入口复用相同邻居图。子集细胞变化后必须重新评估构图和推断，不能仅裁剪标签冒充重分析。
3. 选择失败步骤及必要下游，或本次追问所需的步骤。复用上游要核对数据身份、细胞/基因顺序、尺度、标签、方法、参数及实际产物。原 Run 为 FAILED 不妨碍复用其中已发布且有效的步骤；`Expected` / `Unconfirmed` 不是可复用回执。
4. 跨子图边界的输入从 `from: {step, output}` 改为实际发布 `url`；子图内仍保留 `from` 和依赖。显式控制依赖即使不传文件，也要确认其成功及语义，不随意删除。
5. 保留镜像、代码、命令、资源与输出合同，仅改变本次所需因素。新输出使用新 Run 隔离的位置，去掉指向旧结果的固定输出 URL；记录所有改动，再 dry-run 核对有效定义并提交。

后台步骤输入覆盖、CLI 本地合并和“只执行子图”是不同能力。覆盖输入不自动跳过上游；除非当前帮助及预览已证明支持步骤选择，否则生成子图定义提交。平台版本尚未支持某种覆盖时，可在本地修改定义这一可审阅操作完成同样组合，不推断平台已部署新能力。

## 随包通用组合工具

先保存原始 JSON 与退出码；以下占位符用本次实际值替换，项目/环境沿已有授权：

```sh
omics run-definition --run <源RunUuid> --project <ProjectId> --format json > source-definition.json
omics debug --run <源RunUuid> --project <ProjectId> -o json > source-debug.json

python3 scripts/compose_lambda_continuation.py \
  --definition source-definition.json --debug source-debug.json \
  --from-step <最早需重跑的步骤名> \
  --output continuation.lambda.json --manifest continuation.provenance.json

omics run --lambda-file continuation.lambda.json \
  --project <ProjectId> --environment <EnvironmentId> --dry-run -o json
```

脚本路径相对于本技能目录。`--from-step` 选择该步骤及全部后代；只需要特定分支时用 `--steps <步骤1> <步骤2>` 明确选择。用 `--steps <步骤> --as-task` 将单个步骤提取为 Task，沿用其原命令，无需另维护模板。输入/参数已改变时，用可重复的 `--invalidated-step <步骤>` 声明失效起点，工具阻止复用其后代缓存。这些标记由本次实际变化决定，不是固定限制。

工具从同一 Run 的 `SnapshotJson.Workflow` 与 `Artifacts` 组合，保留原 Run 状态，要求边界产物为真实 `Ready`，并匹配对应 `Calls[].Runtime.outputResults` 中名称、URL、类型一致的 `PUBLISHED` 回执；核对环境，记录源步骤指纹、发布证据、引用 URL、选中步骤和移除的固定输出 URL。CLI 可因对象存在而显示 Ready，单靠它不足以证明该文件由本次 Run 发布。工具不发起网络请求、不运行科学计算，也不会把组合完成写成云端验收通过。输入内容、科学兼容性和冻结定义是否符合本次目标仍需验证；不能仅凭 URL 存在视为等价。

实际参数修改可用当前 CLI 支持的具名步骤覆盖，或编辑生成的 JSON；修改后记录最终文件 SHA，并通过预览/冻结定义核对实际执行。已有邻居图重聚类、RDS 重绘等新模式需采用应用已提供的命令和输入合同，不能只改步骤名假装获得该能力。

[合成平台验收](lambda-continuation-platform-validation.json) 覆盖三步流程中第二步故意失败后，仅重跑第二、三步；源 Run 保留 EXECUTOR_ERROR，上游未重算，真实发布回执、冻结依赖图与输入输出 SHA 链均核对通过。此记录不代表任意应用的步骤内检查点或科学结果均已验证。

## 结果与缓存身份

- 每次部分执行记录源 Run/步骤/产物、旧输入及实际参数、新定义、变化原因、新 Run 和完成范围。最终报告可组合经过核验的旧上游和新下游，但须明确来源；不要把多个 Run 拼成一个虚构的全流程 SUCCESS。
- 长转换在实际可恢复边界保存检查点及原子完成标记，绑定源文件 SHA、转换版本、参数和中间产物 SHA。没有完成记录或内容不匹配时重新处理受影响部分，不以文件存在推断可恢复。
- 复用压缩包的历史解压结果，要有原档案 SHA → 成员路径/SHA → 转换结果的对应清单。名称、GEO 编号、尺寸或细胞数相同不足以证明同一输入。无法读取新上传档案时，不可自行声称旧目录就是本次输入。
- 只有发布失败时先回收已发布文件或应用支持的检查点；步骤内部尚未保存的内存状态不能通过抽取步骤恢复。普通 retry 是重算，不是只发布。
- 不以恢复策略为由擅自缩样本、改统计精度或改算法；当云端 Lambda 持续受阻无法恢复时，可按“默认 Lambda → 组装自定义 Lambda → 云沙箱 → 本地兜底”顺序降级执行并向用户说明，不增加固定细胞数、文件大小或短时限。
