---
description: HTML 长图预览页的填充规范、占位符清单、封面区块处理与截图说明。执行流程第 7 步时读取。
---

# HTML 长图预览页规范

## 一、不要从零写

直接用 `assets/longimage-template.html` 复制一份再逐项替换占位符。原因：

- 三方案必须版式一致，手写必然走形
- 模板已内置深浅阅读适配、打印样式、封面兜底容器

```bash
cp ~/.workbuddy/skills/xdjz-xiaohongshu-viral-post-generator/assets/longimage-template.html \
   ./小红书笔记-<商品名>-<YYYYMMDD-HHMM>.html
```

替换后务必全文搜索一遍 `{{`，确认没有残留未替换的占位符。

---

## 二、占位符清单

### 全局

| 占位符 | 内容 | 示例 |
|--------|------|------|
| `{{PRODUCT_NAME}}` | 目标商品名（用户提供的原文） | 山茶修护精华油 |
| `{{PRODUCT_SPEC}}` | 规格；用户没给则填「待确认」 | 30ml |
| `{{PRICE}}` | 售价，纯数字不带符号；用户没给则填「待确认」 | 189 |
| `{{SELLING_POINTS}}` | 核心卖点，顿号分隔；用户没给则填「待确认」 | 锁水保湿、质地清爽 |
| `{{MISSING_FIELDS}}` | 待确认项，用 `<span class="tag warn">待确认</span>` 标注；无则填 `<span class="tag ok">信息完整</span>` | 成分表 <span class="tag warn">待确认</span> |
| `{{GEN_TIME}}` | 生成时间 | 2026-09-14 21:40 |

### 挂车表 `{{CART_ROWS}}`

一行一档，直接用 HTML `<tr>`（四列：档位 / 商品 / 售价 / 为什么选它）：

```html
<tr><td><span class="tag role-main">主推</span></td><td>山茶修护精华油</td><td>¥189</td><td>本次笔记主角，卖点与方案主打点一致</td></tr>
```

role 样式只有两种：`role-main`（主推）/ `role-match`（搭配）。**没有第三档**——禁止「引流凑单」档位与 `role-trial` 样式。

档位约束：挂车表与每套方案的挂车清单**只保留「主推」+「搭配」**；没有第二款真实在售商品时，只保留主推一行，不要为凑满虚构。

售价列**必须给参考区间**（最低 / 中位 / 最高），不允许只写「待确认」；用户本店售价未录入时另标「待补录」。口径与写法见 references/xiaodie-data-rules.md 第四节。

### 挂车表说明 `{{CART_NOTE}}`

挂车表 `</table>` 之后**必须**跟一段 `.cart-note` 说明，写清参考价的数据来源、样本口径与「实际挂车价以店铺为准」：

```html
<p class="cart-note">同类商品参考价区间（取小红书店铺同源供应链：淘宝 / 天猫 / 京东 / 酒类垂直电商在售与历史价，样本为进口干型雪莉 Fino 750ml 同类商品，共 12 个价格点）：<b>最低 ¥155</b> ｜ <b>中位数 ¥230</b> ｜ <b>最高 ¥298</b>。注：¥155 为京东「买 2 件」单件到手促销价，常规在售中位数约 ¥230；实际挂车价请以店铺为准。</p>
```

### 商品信息卡的命名

商品信息卡里凡提到数据源，一律写「小蝶记账（小程序）数据中心」，禁止「帐套」。见 references/xiaodie-data-rules.md 第一节。

### 每套方案（P1 / P2 / P3）

| 占位符 | 内容 |
|--------|------|
| `{{Pn_NAME}}` | 方案名，用钩子名，如「痛点共鸣」 |
| `{{Pn_HOOK}}` | 一句话钩子说明 |
| `{{Pn_COVER}}` | 封面区块，见下节 |
| `{{Pn_TITLE}}` | 笔记标题，≤20 字 |
| `{{Pn_TITLE_LEN}}` | 标题字数，纯数字 |
| `{{Pn_BODY}}` | 正文全文，支持换行（`white-space: pre-line`） |
| `{{Pn_TAGS}}` | 话题标签，见下方格式 |
| `{{Pn_CART}}` | 挂车清单，见下方格式 |
| `{{Pn_HOOLLINE}}` | 封面主文案（对比表用） |
| `{{Pn_CORE}}` / `{{Pn_STYLE}}` / `{{Pn_FOCUS}}` / `{{Pn_FIT}}` | 对比表项：核心钩子 / 正文风格 / 挂车侧重 / 适合场景 |

### 合规区

| 占位符 | 内容 |
|--------|------|
| `{{TITLE_LEN_REPORT}}` | 如「方案1 18 字 / 方案2 19 字 / 方案3 17 字，均未超限」 |
| `{{WORD_SCAN}}` | 命中词与改写结果；无命中填 `<span class="tag ok">未命中</span>` |
| `{{COMPLIANCE_VERDICT}}` | 一句话结论 |
| `{{MISSING_NOTE}}` | 待确认项的提醒，无则填「本次商品信息均由你提供，无占位数据」。 |

---

## 三、封面区块 `{{Pn_COVER}}` 的两种形态

### A. 生成的封面图（默认路径，三张必须全部走这里）

每套方案一张 AI 生成封面，一一对应填入，不允许某张空缺或复用。图片统一放在 HTML 同级的 `covers/` 子目录，文件名 `封面-方案N-<钩子名>.png`（如 `封面-方案1-痛点共鸣.png`），用相对路径引用：

```html
<div class="cover">
  <img src="covers/封面-方案1-痛点共鸣.png" alt="方案1封面：清晨窗边，因干燥紧绷而困扰的侧影">
  <div class="overlay">
    <span class="sticker">¥189 起</span>
    <div class="hookline">干皮姐妹<br>别再乱补水了</div>
  </div>
</div>
```

要点：
- 图片**必须先裁掉生图工具自带的右下角水印**，并按 3:4 裁切（1024×1536 → 1024×1365）。原图直接嵌进去会带水印。
- `src` 用**相对路径**，保证 HTML 挪动目录时连同 `covers/` 一起走。
- `alt` 写清楚画面内容，便于用户辨认。
- 封面主文案走 `hookline` 叠加层，**不要**试图让生图模型画出中文（中文字符会糊）。
- `hookline` 内用 `<br>` 手动断行，控制在 2-3 行，总字数 ≤ 12。
- `sticker` 放价格标签或品类标签，一个就够。
- 正文里若出现商品数量（如「评测 6 款」），必须与封面图上实际数量一致。

### B. 降级：纯 CSS 排版封面（仅兜底，仅限重试后仍失败的那张）

生图不可用时用这个，**不要留空**：

```html
<div class="cover-fallback">
  <span class="sticker">¥189 起</span>
  <div class="hookline">干皮姐妹<br>别再乱补水了</div>
</div>
```

三种钩子对应的背景色（覆盖 `cover-fallback` 的 `background` 行内样式）：

| 钩子 | 渐变 |
|------|------|
| 痛点共鸣 | `linear-gradient(150deg,#F5E6DA 0%,#E8C9B0 100%)` |
| 效果反差 | `linear-gradient(90deg,#DCE4EA 0%,#DCE4EA 49%,#F0DCD3 51%,#F0DCD3 100%)` |
| 权威测评 | `linear-gradient(160deg,#F7F7F5 0%,#E7E7E2 100%)` |

降级时文字颜色须相应调整：反差/测评（浅底）用 `#23201C`，痛点（暖底）用 `#3B2A1E`。

---

## 四、话题标签与挂车清单格式

### 话题标签

```html
<span class="hashtag">#干皮护肤</span><span class="hashtag">#换季起皮</span>
```

5-8 个，3 个大词 + 3-5 个精准长尾。

### 挂车清单

```html
<div class="cart-item"><span><span class="cart-role role-main">主推</span>山茶修护精华油</span><span>¥189</span></div>
<div class="cart-item"><span><span class="cart-role role-match">搭配</span>氨基酸洁面乳</span><span>¥89</span></div>
```

`cart-item` 内**不要**嵌套 `cart-item`。

---

## 五、正文字段处理

- `{{Pn_BODY}}` 保留原始换行，CSS 已设 `pre-line`。
- 正文里的 emoji 原样保留。
- 正文如有 HTML 特殊字符（`<` `>` `&`）需转义，否则会破坏结构。

---

## 六、交付

1. 写完后用编辑器快速通读，确认无 `{{` 残留、无标签未闭合。
2. 用 `present_files` 打开 HTML，让用户当场看到。
3. 告知用户截图方式：浏览器中直接对每个 `.plan` 卡片截图即为一张 3:4 长图；或用 Cmd+P 打印该卡片区域。
4. 文件名：`小红书笔记-<商品名>-<YYYYMMDD-HHMM>.html`，放当前工作目录。

---

## 七、主题约束

模板为**浅色主题**，不要改成深色。若需要调整配色，改 `:root` 里的 CSS 变量，不要散改具体样式。
