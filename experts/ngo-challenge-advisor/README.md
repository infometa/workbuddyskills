# NGO 共創卡顧問 · 卡仔

Agent 型 WorkBuddy Expert，附帶 `ngo-challenge-designer` Skill。通過點擊式自適應訪談，把 NGO 的一個真實工作痛點整理成可在 WorkBuddy 平台發佈的共創卡。

## 核心特點

- 第一題選擇賽道，第二題直接選擇痛點；
- 每次回答後動態預填下一題的 3–4 個點擊選項；
- 保留自由輸入，不把未確認選項當作事實；
- 自動形成結構化共創卡和標題；
- 明確選擇「確認提交審批」後才生成提交檔；
- 確認後自動提交至平台審批隊列；失敗時提供完整 JSON 與管理端導入兜底。

## 提交與發佈流程

> 運行前提：需 Python 3（僅使用標準庫，無第三方依賴）。

1. 訪談完成並經 NGO 明確確認後，卡仔生成並本地校驗結構化共創卡 JSON；
2. 卡仔通過公開提交腳本直接送入平台審批隊列，不需要管理員口令，也不能直接發佈；
3. 自動提交失敗時，才輸出 JSON，交由管理員在 `https://skillschallenge.edgeone.dev/admin/import` 導入；
4. 管理員審批通過後，共創卡在公開頁 `https://skillschallenge.edgeone.dev/` 顯示。

## 試用問法

- 我想把 NGO 的一個真實工作痛點整理成共創卡
- 幫我從幾個 NGO 痛點中選出最適合發佈的一張
- 幫我檢查這張 NGO 共創卡是否已經適合發佈

## 文件結構

- `.codebuddy-plugin/plugin.json`：專家展示與資源聲明
- `agents/ngo-challenge-advisor.md`：專家角色與工作流程
- `skills/ngo-challenge-designer/`：共創卡訪談 Skill（含訪談流程、共創卡結構、適配規則、示例與本地校驗腳本）
- `avatars/expert.png`：專家頭像
