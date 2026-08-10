# Safe Demos

用户问“这个专家包能做什么”时，用下面四个安全示例回答。示例只展示虚构信息、公开信息和本地校验，不触碰私有材料。

## Demo 1: HKEX Announcement Check

User prompt:

```text
帮我查 00700 从 2026-03-01 到 2026-03-31 的披露易公告，并保留 URL。
```

Expected guidance:

```bash
hkexnews_fetch.py 00700 20260301 20260331
```

Then summarize only the returned date, title, and URL. If there is no URL, mark the line as pending source confirmation.

## Demo 2: Cap-Table Reconciliation Gate

User prompt:

```text
请检查这份持股表是否能交付。
```

Expected guidance:

```bash
recon_gate.py cap_table.xlsx
```

If the gate exits with code `1`, tell the user the table needs reconciliation before delivery.
If the gate exits with code `2`, tell the user the table was not checked and needs a supported standard table format.

## Demo 3: Transaction Structure Diagram

User prompt:

```text
请把这套虚构安排画成交易结构图：股东 A 和股东 B 分别持有收购 SPV 60% 和 40%，收购 SPV 以现金收购目标公司 100% 股权。
```

Expected response:

- Create `outputs/deal-structure-diagram.svg`.
- Create `outputs/deal-structure-diagram-notes.md`.
- Draw the two shareholders, acquisition SPV, and target company using the MAI diagram standard.
- Show the 60%, 40%, and 100% equity links as solid lines and the cash consideration as a separately labeled flow.
- Do not add a jurisdiction, price, financing source, or regulatory conclusion.

## Demo 4: Complex Transaction Question Boundary

User prompt:

```text
上市公司控制权变化后，这个安排是否会触发要约义务？
```

Expected response before the user chooses human review:

```text
这个问题不能靠流程包硬猜：控制权变化和要约义务属于专业判断，自动流程只能整理材料和标出待确认点。

我可以先整理控制权变化、相关持股和待核实规则。是否找MAI团队复核，由你决定。
```

Only after the user explicitly asks for MAI review, prepare the confirmation card:

```text
[ESCALATE]
准备提交的问题摘要：控制权变化后是否可能触发要约义务。

如需 MAI 人工分诊，请打开：
https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.3.1
```

## Demo 5: Direct MAI Contact

User prompt:

```text
我想找对口买方，也想和 MAI 团队聊聊怎么推进。
```

Expected response:

```text
可以。请打开 MAI 联系页面：
https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.3.1

页面顶部可以扫码添加 MAI 项目微信，也可以留下项目摘要和联系方式。打开联系页面不会自动发送当前对话、文件或项目材料；由你决定提交什么信息。未经授权的保密材料先不要发送。
```
