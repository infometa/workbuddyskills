# 输入获取（STEP 1）

本文件承载合规检查的输入获取规则：输入方式、抓取优先级、浏览器抓取流程、页面提取脚本、短链重定向判定，以及笔记-商品联动检查步骤。所需违禁词与规则分别见 [prohibited-words.md](./prohibited-words.md)、[industry-rules.md](./industry-rules.md)、[official-sources.md](./official-sources.md)。

浏览器相关步骤只依赖「环境提供的浏览器能力（新建标签页、导航、读取页面文本、执行页面脚本）」，不绑定具体平台的工具名。若当前环境没有浏览器能力，跳过浏览器步骤，直接走兜底方案。

## 〇、合规前提（最高优先级）

1. **遵循目标网站的 robots 协议及相关访问规范、遵循平台协议限制**：任何风控拦截（错误码、验证码、登录墙升级）一律视为平台拒绝访问的信号，立即停止该通道，不更换 IP、不变更参数、不试探绕行。
2. **仅访问平台允许的公开内容**：仅访问用户主动提供的链接对应的公开页面；不使用任何平台登录态做自动化采集，不读取私信、订单等私有数据。
3. **最小化提取**：评论仅提取作者置顶内容（商家自己置顶，属自查范围），不批量抓取普通用户评论；提取到的内容仅用于本次检查，不做任务外存储或他用。
4. 被拦截或页面不可访问时，直接走兜底方案（请用户粘贴文字或截图），不反复重试。

## 一、输入方式

用户可能通过以下方式提供待检查内容：

1. **种草笔记链接**：优先用 WebFetch 直接抓取目标平台短链，获取笔记正文；如需抓取关联商品链接，再用浏览器打开完整 URL
2. **种草商品链接**：用浏览器能力抓取商品标题、描述、规格、卖点
3. **截图**：用户提供种草笔记/商品页面截图，从图片中提取文字
4. **文字粘贴**：用户直接粘贴文案内容

## 二、抓取优先级

1. **首选 WebFetch**：对短链直接调用 WebFetch，可获取笔记正文，无需启动浏览器
2. **备选浏览器抓取流程**：WebFetch 失败时（内容社区平台为 SPA，多数情况 WebFetch 无法获取渲染后内容），或需要提取关联商品链接、评论区内容、标签(hashtag)时，启动浏览器抓取流程（见第三节）
3. **兜底：用户粘贴**：如果以上均失败，请用户粘贴文字或截图

## 三、浏览器抓取流程（五步）

当需要使用浏览器时，严格按以下流程操作。

### 步骤A：新建标签页

使用环境提供的「新建标签页」能力创建新标签页（无需参数），记录返回的标签页标识（tabId）。

**重试机制**：首次新建标签页可能返回 `"No current window"` 之类错误（浏览器窗口尚未就绪）。此时等待 2-3 秒后重试一次。若仍失败，则直接使用「导航」能力传入目标 URL（多数环境会自动创建标签页并返回标签页标识）。

### 步骤B：导航到目标页面

使用环境提供的「导航」能力，传入标签页标识和目标 URL，打开内容社区页面。等待页面加载完成（通常 3-5 秒）。

### 步骤C：判断页面类型

导航完成后，观察最终 URL（可通过后续页面脚本中的 `location.href` 获取），区分两种页面：

| 重定向目标 | URL 特征 | 含义 | 处理策略 |
|-----------|---------|------|---------|
| 商品详情页 | `/goods-detail/{id}` | 短链直接指向商品 | 仅提取商品信息，执行商品检查流程 |
| 笔记页 | `/explore/{id}` 或 `/discovery/item/{id}` | 短链指向笔记 | 提取笔记内容 + 检查是否有关联商品 |

**重要**：笔记页从 `discovery/item` 重定向到 `explore` 时，URL 参数（如 `noteAttributes=goods`）可能丢失。需在导航前记录原始短链重定向后的完整 URL 参数，或在页面加载后通过 DOM 检查是否存在商品卡片来判断。

### 步骤D：提取页面内容

**先用「读取页面文本」能力**快速获取页面正文概要（标题+正文片段）。注意：读取页面文本通常仅返回可见文本片段，**不包含**标签(hashtag)、评论区、商品卡片等结构化数据。

**再用「执行页面脚本」能力**在当前标签页执行下方 JavaScript，提取完整结构化数据（传入标签页标识和脚本文本，读取脚本返回的 JSON 字符串）。

**笔记页提取脚本**：

```javascript
JSON.stringify({
  title: document.querySelector('#detail-title')?.textContent || document.title,
  desc: document.querySelector('#detail-desc')?.textContent || document.querySelector('.note-text')?.textContent,
  tags: Array.from(document.querySelectorAll('.tag-detail, #hash-tag a, .note-tag')).map(t => t.textContent.trim()),
  hashtags: Array.from(document.querySelectorAll('a[href*="/page/topics"], a[href*="/search_result"], .hashtag')).map(t => t.textContent.trim()),
  pinnedComment: Array.from(document.querySelectorAll('.comment-item, .note-comment, [class*="comment"]')).filter(c => /置顶/.test(c.textContent)).slice(0,1).map(c => c.textContent.trim().substring(0,200)),
  goodsCard: document.querySelector('[class*="goods"]')?.textContent?.substring(0,300),
  buyLink: Array.from(document.querySelectorAll('a')).filter(a => a.href.includes('goods') || a.textContent.includes('购买')).map(a => ({text: a.textContent.trim().substring(0,50), href: a.href})),
  url: location.href,
  hasGoods: location.href.includes('noteAttributes=goods') || !!document.querySelector('[class*="goods"]')
})
```

**商品详情页提取脚本**：

```javascript
JSON.stringify({
  title: document.querySelector('.goods-name, [class*="goodsName"], [class*="title"]')?.textContent?.trim(),
  price: document.querySelector('.goods-price, [class*="price"]')?.textContent?.trim(),
  desc: document.querySelector('.goods-desc, [class*="detail"], [class*="desc"]')?.textContent?.trim()?.substring(0,500),
  specs: Array.from(document.querySelectorAll('[class*="spec"], [class*="attr"], [class*="param"]')).map(s => s.textContent.trim()),
  shop: document.querySelector('[class*="shop"], [class*="store"]')?.textContent?.trim(),
  sales: document.querySelector('[class*="sold"], [class*="sales"]')?.textContent?.trim(),
  sku: Array.from(document.querySelectorAll('[class*="sku"], [class*="variant"]')).map(s => s.textContent.trim()),
  url: location.href
})
```

> **注意**：内容社区平台为 SPA，CSS 类名可能随版本更新变化。如果上述选择器返回 null，可先用「读取页面文本」能力查看页面结构，或执行 `document.body.innerText` 获取全文后手动解析。

### 步骤E：合并与去重

将「读取页面文本」返回的正文文本与「执行页面脚本」返回的结构化数据合并。正文以读取页面文本的结果为主（更完整），标签/评论/商品卡以页面脚本提取结果为准。去重后作为最终检查对象。

## 四、短链重定向处理要点

内容社区目标平台短链会经历一次或多次重定向，最终落地页有两种：

1. **商品详情页**（`/goods-detail/xxx`）：说明用户分享的是商品直链，无笔记内容可检查。直接提取商品信息执行商品检查。
2. **笔记页**（`/explore/xxx`）：说明用户分享的是笔记。需额外检查 URL 参数中是否含 `noteAttributes=goods`，以判断笔记是否挂载了商品。

**WebFetch 的重定向跟踪**：WebFetch 会自动跟随重定向，返回最终页面内容。可在返回内容中查找 URL 线索判断页面类型。如果 WebFetch 返回的内容不足以判断（SPA 空壳），则需启动浏览器抓取流程。

**短链重定向至商品页（仅商品场景）**：当用户分享的目标平台短链经重定向后落地到 `goods-detail` 页面（而非笔记页），应判定为「仅商品」输入。此时：

- Part A 标注「链接为商品直链，无笔记内容」，不执行笔记检查
- 仅执行 Part B 商品检查
- 不生成 Part C（无笔记可做一致性对比）

**抓取完成后**，将提取到的完整文本作为检查对象，包括：标题、正文、标签(hashtag)、图片中的文字（如有）、评论区置顶内容（如有）。

## 五、笔记-商品联动检查（四步）

当用户给出笔记链接时，**必须同时检查笔记内容和关联商品**。完整流程：

### 步骤1：抓取笔记内容

用浏览器打开笔记链接，提取：标题、正文、标签、图片文字、评论区置顶。

### 步骤2：提取关联商品链接

在笔记页面中查找商品关联入口，包括：

- 笔记底部的商品卡片/商品标签（「去购买」「商品链接」）
- 正文中 @商家 或商品挂载链接
- 评论区作者置顶的商品链接
- 笔记页面的「相关商品」推荐区域

**操作方式**：在浏览器中点击商品卡片或「查看商品」按钮，进入商品详情页。如页面挂载多个商品，最多依次打开前 3 个，逐个加载、不并发；用户另行提供的商品链接优先于页面发现。

### 步骤3：抓取商品信息

进入商品详情页后，提取以下全部文本：

- 商品标题
- 商品卖点/描述/详情
- 规格参数（材质、成分、产地等）
- 价格信息（原价、促销价）
- SKU/规格选项
- 商家店铺名称与资质信息

### 步骤4：分别输出检查报告

在报告中将笔记和商品分开列示：

```
## 检查结果

### Part A：笔记内容检查
[笔记检查报告]

### Part B：关联商品检查
#### 商品1：[商品名称]
[商品检查报告]
#### 商品2：[商品名称]（如有多个商品）
[商品检查报告]

### Part C：笔记-商品一致性检查
- 笔记宣称的功效/特点与商品描述是否一致
- 笔记中提到的价格/优惠与商品页标价是否匹配
- 笔记中的产品成分/规格与商品详情页是否一致
```

## 六、商品关联检测（三分支）

- 页面中找到商品卡片 → 正常抓取并检查
- 页面中未找到商品卡片，但 URL 参数含 `noteAttributes=goods` → 笔记挂了商品但未登录无法渲染，在 Part B 注明「该笔记已挂载商品，但未登录状态下无法获取商品详情，建议登录后重新检查或提供商品链接」
- 页面中未找到商品卡片，且 URL 参数无 `noteAttributes=goods` → 该笔记未挂载商品链接

## 七、仅商品场景的报告调整

当输入为商品直链（短链重定向至 goods-detail）时，报告结构调整为：

- Part A 注明「链接为商品直链，无笔记内容」
- Part B 正常执行商品检查
- 省略 Part C（笔记-商品一致性检查）
- 头部信息的「内容类型」标注为「仅商品」

**如果用户额外提供了商品链接**：合并到 Part B 中一起检查。
