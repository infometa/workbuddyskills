# Interview flow

## Opening

Use Traditional Chinese for NGO-facing questions. Keep explanations short. Prefer a single clickable question per turn.

## Question map

| Stage | Goal | Default question | Selection |
|---|---|---|---|
| Track | Classify broadly | 這個工作問題主要屬於哪些方向？ | Multi-select + primary |
| Organization | Establish issuer identity | 這道題目由哪個機構提出？（會顯示在賽題上） | Single free-text answer, with「暫不公開」choice |
| Pain | Identify one problem | 你目前最想解決的工作痛點是甚麼？ | Single-select |
| Current method | Understand today | 目前你們通常怎樣處理這個問題？ | Single-select; multi-select only when several methods are genuinely used |
| Frequency / effort | Establish baseline | 這個情況大約多久發生一次？ | Single-select ranges |
| Outcome | Define desired change | 你希望日常工作變成甚麼樣？可多選。 | Multi-select; faithfully join selected phrases into `desired_outcome` |
| Success | Define evidence | 出現甚麼可觀察的改變，便算真的有幫助？可多選。 | Multi-select → `success_criteria[]` |
| Materials | Identify inputs | 完成這項工作通常會用到哪些資料？可多選。 | Multi-select → `materials[]` |
| Boundaries | Protect data | 哪些內容不能公開或必須由人確認？可多選。 | Multi-select → `boundaries[]` |
| Title | Name the brief | 以下哪個題目名稱最合適？ | Single-select |
| Confirmation | Submit for review | 是否確認提交審批？ | Single-select |

## Dynamic choice patterns

### Track to organization

After the primary track is confirmed, ask once for the issuing organization. Keep it lightweight:

- 直接輸入機構名稱（一行即可）
- 暫不公開（賽題會顯示「未公開機構」）

If the user chooses not to disclose, store `organization_name: "未公開機構"` and note it in `internal_metadata.fit_reasons` or scope notes is NOT required — anonymity is acceptable. Ask `organization_intro` only if the user volunteers context; do not push.

### Track to pain

Generate pains that describe work friction, not solutions.

Example for report/document + data tracks:
- 資料分散，整理和匯總很花時間
- 經常重複複製、貼上和調整格式
- 不同同事記錄方式不一致
- 容易遺漏數據、服務重點或必填內容
- 其他（自己描述）

### Pain to current method

Example for fragmented data:
- 由同事逐份打開文件，再人工匯總
- 在 Excel、Word 或表格之間複製貼上
- 先各自整理，再由一位同事統一核對
- 暫時沒有固定做法，每次臨時處理
- 其他（自己描述）

### Current method to baseline

Prefer ranges when exact numbers are not known:
- 每天都會發生
- 每週 1–3 次
- 每月 1–3 次
- 只在特定活動或報告期發生
- 不確定／其他

### Pain to outcome

Example for fragmented, repetitive reporting:
- 把分散資料整理成統一結構
- 減少重複輸入和複製貼上
- 在輸出前提示缺失資料
- 保留人工檢查後再輸出的步驟
- 其他（自己描述）

### Outcome to success

- 完成時間明顯縮短
- 遺漏或錯誤減少
- 不同同事的輸出更一致
- 新同事也能按相同步驟完成
- 其他（自己描述）

## Choice rules

- All NGO-facing questions, choices, previews, and process reminders must use Traditional Chinese.
- Show 3–4 generated choices plus Other.
- Use multi-select where several answers can truthfully coexist: tracks, current methods (if genuinely multiple), outcomes, success criteria, materials, and boundaries.
- Use single-select for the primary pain, primary track, frequency/baseline, trial scenario, title, and approval confirmation.
- Keep labels concrete and mutually distinguishable.
- Do not select choices on the user's behalf.
- Do not generate organization-specific facts without evidence; organization identity must come from the user's own answer.
- If the user types a complete answer, extract it and skip redundant questions.
