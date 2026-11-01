# 扩展能力

主流程之外的 CLI 能力集中在这里：先判断场景，再按对应命令调用。

## 发布后高级设计师：调整页面或重新设计

**入口**：发布成功结果的 `nextActions` 包含 `ADVANCED_DESIGNER_POLISH` 时，在原发布结果和正式访问链接后，将「高级设计师：调整页面设计，也可以重新设计方案。」与已有 Agent 友好、继续创作选项汇总为同一道选择题，按原宿主提问规则收答。

用户只选择高级设计师时，原样提示：「请告诉我想调整哪些页面、具体想怎么改；也可以重新设计方案。」已有具体要求时不重复问，将用户原话写入 content；只有选项名称或附件时先收集要求，不默认补写需求。用户主动提供参考附件时沿用现有本地文件上传规则。

```text
superun-ai chat design <sessionId> --input <需求JSON文件> --timeout 600
```

JSON 只含 content 或 message；也可用互斥的 --message，附件使用可重复的 --file。通过原运行包装器只提交一次，复用现有等待、业务问答和异常恢复规则；--no-wait 返回后按本次 nextActions 继续查询，不重复发送。

**这是独立能力**：即使用户要求「重新设计方案」，仍用 chat design（advanced_designer_polish）。它与 4 选 1／风格选择阶段同名的高级设计师及「再来一版」不同，不调用 style append，不套用风格候选、额度或费用指引。上面的专用指引适用于这个新动作；其他修改仍沿用原 chat send 规则。

沿用既有项目执行模式，不自动从本地开发切换到云端。完成后展示本次实际结果和研发预览，并说明重新上线后才会更新正式网站；仅用户明确要求上线时才继续原发布流程。当前 CLI 没有 design 命令时按现有更新流程处理，不能改用 style append 或普通 send 假装执行了这项能力。

## Agent 友好：把项目接入用户的 AI 应用

**场景**：本次目标版本已部署成功且站点已公开（`publicStatus=1`）、没有在途任务和待回答问题。入口出现在发布完成引导里，与「继续创作」并列；CLI 会拒绝未上线或部署中的项目，如实转达。

**使用**：

```text
superun-ai chat agent-friendly <sessionId> --timeout 600
```

| 目的 | 参数 |
|---|---|
| 触发准备接入能力 | 不加其他参数；后端用同源技能 `skill.superun_mcp.integrate` 真实生成 |
| 只查询或等待已有任务 | `--status`，可带 `--message-id`；只读，不重复生成 |
| 读取所选方式的完整原文 | `--method skill` 或 `--method connector`；只展示，不安装 |
| 受理后立即返回 | `--no-wait` |

就绪后只问一次接入方式（技能／连接器），选定后在一个文本代码块里原样展示原文：不摘要、不截断、不改写其中的 URL、不生成文件。生成期间出现真实提问按 [交互回复](interactions.md) 回答，答完用 `--status` 回到本流程。接入指令安装的是目标应用的运行时 CLI `superun-cli`（命令 `superun`），不是本套件的 `superun-ai-cli`。

## 安全扫描

**场景**：用户在研发完成菜单里明确选择后执行。默认扫描全部可用检查项，不加费用提示、二次确认或检查项选择；讨论是否需要扫描不触发，也不因研发完成自动执行。

**使用**：

```text
superun-ai chat security <sessionId> --timeout 600
```

`--check <category>` 指定范围（可重复），`--no-wait` 受理后返回，报告失败用 `--retry-report <reviewId>` 重试、不重扫。结果在 `securityReview`；完成、消息结束或修复启动都不代表通过，按 `reportResult` 给简洁摘要，不展开正文、不给报告或 PDF 下载链接。
