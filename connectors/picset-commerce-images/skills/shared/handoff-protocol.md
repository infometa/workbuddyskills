# Picset 公共交接协议

## 用途

让主 Skill 和所有已实现的子 Skill 使用同一份会话事实、素材角色、视觉系统、稳定结果编号和待处理动作。不要为不同子 Skill 复制或改名这些字段。

## HandoffContext

```yaml
HandoffContext:
  active_intent:
  pending_actions: []
  product:
    name:
    purpose:
    verified_facts: []
    uncertain_facts: []
    selling_points: []
    target_audience:
    scenarios: []
  brand:
    requirements: []
    copy_tone:
  assets:
    - id:
      role: product_truth | brand_asset | style_reference | supporting_material
      description:
      local_path:
      registered_url:
  platform:
    name:
    market:
    language:
    main_ratio:
    detail_ratio:
  visual_system:
  suite_draft:
  results:
    - id: M1 | D1
      status: planned | estimated | submitted | generated | failed
      artifact:
      batch_id:
  execution:
    batches:
      - batch_id:
        image_type: main | detail
        stable_ids: []
        request_id:
        task_id:
        status: planned | estimated | submitted | partial_success | success | failed
  unsupported_actions: []
```

缺失字段保持为空或空列表。不要用推测填满结构。

`local_path` 只用于当前机器读取用户授权的文件；本地附件先用于建立并展示 `SuiteDraft`。草稿确认后只做快速积分报价；只有报价后的新消息明确确认积分，才上传并由 MCP 登记后写入 `registered_url`。不要把 STS、SK、OAuth 或其他服务凭据写进交接结构。

`SuiteDraft` 维护彼此独立的 `draft_confirmation` 与 `generation_confirmation`：前者确认后只能用 `quote_commerce_image_credits({ batches })` 一次报价全部执行批次；报价回合不得获取 STS、上传、登记或生成。后者只能在完整报价后由一条新的明确积分确认消息更新；确认后才上传、登记并提交生成。报价不锁定积分，生成提交按实时积分执行且不再要求确认。

## 素材角色和优先级

按以下优先级解决冲突：

1. 商品原图定义商品身份、外观和结构真实性。将它标记为 `product_truth`。
2. 品牌规范优先于自动风格。将品牌标志、色彩和字体规范标记为 `brand_asset`。
3. 风格参考图只定义视觉方向，不能覆盖商品原图或已确认商品事实。将它标记为 `style_reference`。
4. 场景、道具和补充信息素材标记为 `supporting_material`，不能改变商品身份。

精修能力未来上线后，只有经过用户确认的精修结果才能替代原商品图成为新的 `product_truth`。

## 事实等级

- 把用户明确提供、可核对资料证明或用户确认的信息放入 `verified_facts`。
- 把无法从图片可靠确认的材质、数值性能、认证、兼容性、医疗效果、销量排名和保证性承诺放入 `uncertain_facts`。
- 对可见外观只使用保守观察，不从"金属质感"推导"铝合金材质"。
- 交接时保留事实等级。子 Skill 不得把 `uncertain_facts` 升级为卖点或图片文案。

## 稳定结果编号

- 主图使用 `M1...Mn`；独立详情图和详情长图使用 `D1...Dn`。
- 创建编号后保持稳定。局部返工、失败重试和跨 Agent 交接都使用原编号。
- 删除后保留编号空缺，不自动重排后续图片。
- 新增图片使用同组下一个从未使用的编号；不要复用已删除编号。
- 套图中的指定图片返工继续由套图子 Skill 处理，不转给普通单图 Agent。

## 交接输入

主 Skill 在路由前传递完整 `HandoffContext`，尤其保留：

- 当前用户意图和待执行动作；
- 商品、品牌和素材事实；
- 平台推荐和用户覆盖值；
- 当前 `SuiteDraft` 与冻结的 `VisualSystem`；
- 所有稳定编号、结果、失败项和产物引用。
- 每个执行批次的稳定编号、幂等 `request_id`、服务 `task_id` 和真实状态。

## 子 Skill 返回

子 Skill 返回以下逻辑字段，供主 Skill更新同一会话上下文：

```yaml
HandoffReturn:
  handled_intent:
  updated_suite_draft:
  updated_visual_system:
  result_updates: []
  pending_actions: []
  unresolved_facts: []
  user_message:
```

不要创建第二份草稿或视觉系统。局部返工只返回被点名编号的 `result_updates`；全局变化返回更新后的草稿和待重新确认状态。

服务返回批内 `index` 时，必须用该批次保存的 `stable_ids[index]` 恢复 M/D 编号。成功项交付给公共客户端的字段固定为 `{"id": stable_ids[item.index], "image_url": item.image_url}`；不得使用 `stable_id`、`url`，也不得按完成顺序、成功顺序或重试顺序重新编号。
