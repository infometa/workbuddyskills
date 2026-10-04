# Picset 公共交接协议

## 用途

主路由和业务子 Skill 共享同一份会话事实，用于跨轮次恢复（如生成超时后用户下次对话继续查询）。不得复制、改名或并行维护第二份商品信息、草稿或结果编号。

当前包含电商套图、单图文生图/图生图、风格复刻、Agent Canvas 四个业务能力。本协议保留现有电商上下文，并补充风格复刻的最小恢复字段；单图和画布仍按各自手册管理生命周期。跨能力费用授权以 [共享积分确认规则](./credit-confirmation-playbook.md) 的唯一偏好文件为准，不在各能力上下文复制持久化授权。

## HandoffContext

```yaml
HandoffContext:
  active_intent: commerce_image_suite    # 当前业务能力
  product:                               # 商品基本信息，用于恢复草稿
    name:
    selling_points: []
    target_audience:
    scenarios: []
  platform:                              # 平台配置
    name:
    market:
    language:
  output:                                # 输出配置
    main_count: 0
    detail_count: 0
  results:                               # 已生成结果
    - id: M1 | D1                        # 稳定编号
      status: generated | failed
      image_url:
      local_path:
  execution:                             # 进行中的任务，用于恢复轮询
    - task_id:
      image_type: main | detail | aplus
      stable_ids: []
      status: submitted | processing | partial_success | success | failed
  confirmations:                         # 确认状态
    draft_status: drafting | awaiting_confirmation | confirmed
    generation_status: not_ready | awaiting_confirmation | confirmed
    estimated_credits:
```

缺失字段保持为空或空列表，不用推测填满。

## 风格复刻扩展

进入复刻时 `active_intent` / 返回的 `handled_intent` 使用 `style_replicate`；沿用上面的 product、platform、results 和 confirmations，仅在复刻流程补充：

```yaml
replication:
  reference_image:              # 指向原素材记录的已登记风格图路径/URL
  product_images: []            # 指向原素材记录的1–6张商品图路径/URL
  requirements:                # 已确认用途与调整，不复制第二份商品事实
  model: nova-2.0               # 实际公开规格；用户指定时按实际保存
  resolution: 2K
  aspect_ratio: "1:1"
  speed_mode: fast
execution:                     # 复用原执行列表，每次复刻增加一项
  - intent: style_replicate
    request_id:                # 原UUIDv4，同次重放不变
    task_id:                   # 服务返回，与job_id同值，无需冗余保存
    stable_ids: [R1]
    status: submitted
    charged_credits:           # 首次有效提交响应；缺失保持空，不把重放累计
    submission_uncertain: false # 请求发出但未取得可靠响应时为true
```

复刻结果仍放在原 `results` 列表中，`id` 为 `R1` 等。同次提交重放必须恢复原规格、原素材、原要求，不将后续草稿变化混入旧请求；存在多个任务时将各自已提交参数快照保存在相应 execution 项下，引用素材记录而不复制素材文件。

- 查询前校验任务 ID 与原请求对应，成功项 `index=0` 映射 `stable_ids[0]`，不能套用电商多图索引。
- 超时保留原任务及待查询动作；只有用户明确新请求才生成新幂等键。
- 用户修改或要求重新生成原图时保留 R 编号，新增 execution 项和新任务目录；不得复用旧幂等键或覆盖历史文件。
- 同次费用确认跟随方案/报价有效性；共享自动确认在每次提交前读取，不把历史 `generation_status: confirmed` 当作永久授权。
- 复刻返回仍使用 HandoffReturn 统一结构，不创建另一套交接协议。

## 稳定编号

- 主图使用 `M1...Mn`；详情图使用 `D1...Dn`
- 风格复刻使用 `R1...Rn`，独立新增用下一个未使用编号；明确复刻淘宝主图也用 R，不冒充普通电商 M 编号。
- 局部返工、失败重试和跨轮次恢复都保留原编号
- 删除后保留空缺，不重排后续编号；新增图片使用同组下一个从未使用的编号
- 服务返回批内 `index` 时，使用保存的 `stable_ids[index]` 恢复编号

## 子 Skill 返回

业务子 Skill 执行完成后返回以下结构：

```yaml
HandoffReturn:
  handled_intent: commerce_image_suite
  context_updates: {}          # 本次动作更新的上下文字段
  result_updates: []           # 新增或更新的结果项
  pending_actions: []          # 待执行动作（如继续轮询、等待用户确认）
  user_message:                # 面向用户的最终回复内容
```

执行阶段不创建新草稿，只返回本次动作的更新和待办。
