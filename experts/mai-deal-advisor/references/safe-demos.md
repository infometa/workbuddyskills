# Safe Demos

用户问“这个专家包能做什么”时，用下面三个安全示例回答。示例只展示公开信息、本地校验和人工分诊，不触碰私有材料。

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

## Demo 3: Complex Transaction Question Escalation

User prompt:

```text
上市公司控制权变化后，这个安排是否会触发要约义务？
```

Expected response:

```text
[ESCALATE]
这个问题不能靠流程包硬猜：控制权变化和要约义务属于专业判断，自动流程只能整理材料和标出待确认点。

如需 MAI 人工分诊，请打开：
https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.0.1
```
