---
name: cz-saas-page-makeover
display_name: 微页面装修改版
display_name_en: Mini Page Makeover
description: 用对话改驰在灵枢 SaaS 的微页面：换轮播图、改文案、加区块、调顺序、新建活动页。含「复制副本再改」的安全路径、组件级与整页级工具的选择判据、identity 不能编、发布前的内容门禁自检。触发词：装修、改首页、改版、换图、换轮播、改文案、改标题、标题改、换到首屏、首屏、加个区块、商品列表、删掉这块、调顺序、挪到最、新建页面、活动页、落地页、专题页、微页面。
description_zh: 用一句话完成微页面的改图、改字、加减区块与顺序调整，并按「先复制副本、再改、最后发布」的安全路径操作，改坏了随时能退。
description_en: Revise Chizai LingShu mini pages by conversation — swap banners, edit copy, add or reorder blocks, and create campaign pages safely via a copy-and-edit workflow.
examples_zh:
  - "把首页第一张轮播图换成这张，文案改成「双十一预热」"
  - "首页太旧了，帮我重新排一下，主打秋季新品"
  - "在小助手端首页加一个商品列表，放在第二位"
  - "把「门店活动」这块挪到最上面"
examples_en:
  - "Swap the first banner on the home page and set the copy to \"Double 11 teaser\""
  - "The home page feels dated — restructure it around autumn new arrivals"
  - "Add a product list to the assistant home page as the second block"
version: 1.0.0
author: "驰在科技"
---

# 微页面装修改版

商户说「首页太旧了」「换个图」「加一块」，你要动的是微页面的组件树。
这份技能解决一件事：**改对、说得清、退得回**。

工具走 `cz-saas call <tool>`，调用语法与风险档见技能 `cz-saas-cli`；发布与撤回见 `cz-saas-publish-safety`。

---

## 一、三条不能破的前提

**1. 装修是「草稿 → 发布」两段，不是直接改线上。**
所有写工具落在草稿。唯一让顾客看见的动作是 `decoration_publish_page`。
所以改错在任何时刻都还有救 —— 除非你已经发布了。

**2. 改线上页面的默认动作是「先复制」，不是「直接改」。**
```
decoration_copy_page(pageId=首页) → 得到副本草稿 → 在副本上改 → 发布副本 → （可选）下线旧页
```
原页面整个过程纹丝不动。改不好就丢掉副本，零损失。
只有一种情况可以直接改：这个页面本来就是草稿（`status=DRAFT`）。

**3. identity 只能拿，不能编。**
`decoration_get_page` 返回的 `identities` 是稳定标识；`index` 只是数组位置，增删一块之后全体位移。
所有组件级操作认 `identity`。自己编一个只会拿到 `IDENTITY_NOT_FOUND`，服务端不会猜你的意思。

---

## 二、工具选型：粒度选错就是事故

| 你要做的事 | 用哪个 | 不能用的 |
| --- | --- | --- |
| 换某个区块的图 / 改某段文案 | `decoration_update_block` | `decoration_update_page` |
| 加一块 / 删一块 | `decoration_add_block` / `decoration_remove_block` | — |
| 调顺序 | `decoration_reorder_blocks` | — |
| 改页面标题 / 封面 / 分组 | `decoration_update_page`（只传该字段） | — |
| 整棵树按模板替换 | `decoration_update_page` 传完整 `pageItemData` | — |

**用整页 PUT 改一个区块的后果：没传到的组件等于被删掉。** 这类事故不报错，只会「少了几块」，
你会在复核时发现页面莫名其妙空了，然后去怀疑缓存。

`decoration_update_block` 默认按 key 浅合并 —— 换图只传图片字段即可，其余字段原样保留。
`replace=true` 是整体替换 setting，除非确实要清空重填，否则不要用。

---

## 三、标准作业流程

```
① 看现状    decoration_list_pages            找目标页（首页 = status=PUBLISHED 且 homePage=true）
② 定策略    改线上页 → decoration_copy_page  复制成草稿
            新建页   → decoration_list_templates → decoration_apply_template（优先）
③ 取契约    decoration_get_component_schema  不传 type = 全部摘要；传 type = 完整字段定义
④ 动结构    decoration_add_block / remove_block / reorder_blocks
⑤ 填内容    decoration_update_block          只传要改的字段
⑥ 自检      decoration_get_page              复核整棵树，看 warnings 有没有 CONTENT_EMPTY
⑦ 发布      向商户讲清后果 → decoration_publish_page
```

**第 ③ 步不能省。** 字段名凭记忆拼是这类任务最高的失败率来源，而且失败是静默的：
服务端丢弃契约外字段并返回 `UNKNOWN_FIELD` 告警，不报错。你会以为图换上了，其实没有。

**`decoration_reorder_blocks` 的 `identities` 必须是当前全部组件的完整排列。**
只给一部分会被拒绝 —— 这是刻意设计，因为少给一个等于悄悄删掉一个组件。
正确做法：取全部 identity，在数组里搬家，整体传回。

---

## 四、页面结构：首屏决定一切

微页面的实际阅读深度通常只有 1.5 屏。

**首屏（前 2 个组件）必须回答三件事**：这是谁、卖什么、为什么现在看。
- 一张有信息量的主图（不是纯装饰的氛围图）
- 一句话说清主营与差异点（`TEXT` 的 `textarea`）
- 一个明确动作入口（`NAVIGATOR` / 商品列表 / 领券）

**中部按「决策顺序」排，不按「公司组织架构」排。**
顾客想知道：多少钱 → 别人说好不好 → 怎么买 → 我在哪买。
「公司简介」「发展历程」对成交没贡献，放最后或干脆不放。

**区块数控制在 6~9 个。** 超过 10 个顾客到不了底，而且每次增删都要重排 identity，维护成本陡增。

### 常用组件选型

| 目的 | 组件 | 注意 |
| --- | --- | --- |
| 主视觉（单图+跳转） | `IMAGE_LIST` | 图必须有真实 url |
| 一句主张 | `TEXT` | 正文填 `textarea`，`data_list` 放不了字 |
| 长说明 / 图文混排 | `RICH_TEXT` | 可只插图不打字（见下节） |
| 商品曝光 | `LIST_REAL` / `SALES_PRODUCT` | `data_source` 决定数据来源，custom 要自带 `data_list` |
| 引导跳转 | `NAVIGATOR` | 必须有图 |
| 公告 | `ANNOUNCEMENT` | 默认「请编写公告」不算内容 |
| 搜索 | `SEARCH_BAR` | — |
| 留白分隔 | `SPACER_LINE` / `SPACER_AREA` | 无内容要求 |
| 优惠券 | `COUPON` | 券要先在运营侧建好 |
| 门店 | `STORE` / `STORE_SEARCH` | `data_source=store` 时自动拉取免检 |

契约内共 39 种组件，分五类：基础、商城、内容、营销、其他。不确定就 `decoration_get_component_schema` 查。

---

## 五、内容门禁的两条反直觉判据

发布时全量校验，任何组件没内容都会被逐条拦下。两条判据与直觉相反：

**① 富文本只插图、不打字，算有内容。**
商户拿一张图当整段正文是常见做法。`<p><img src="..."></p>` 通过校验。
但 `src` 为空或为 `#` 的图不算 —— 「放了个图片框没传图」要拦。

**② 组件自带的默认占位文案，不算内容。**
`RICH_TEXT` 默认 `<p>请输入富文本内容</p>`、`ANNOUNCEMENT` 默认「请编写公告」，
都判成空。模板生成的页面整页都是占位文案，直接发布会被逐条列出。

所以「用模板建草稿」之后必须**逐块替换文案**，不能只改标题就发。

**内容缺失在草稿阶段只是警告**（`CONTENT_EMPTY`），不拦保存 —— 它是提醒「这块发出去是空白的」。
草稿可以存，但别带病发布。

---

## 六、新建页面：模板优先于从空页开始

```
decoration_list_templates          → 挑一个结构接近的模板
decoration_apply_template          → 生成草稿，返回 pageId
decoration_get_page                → 看模板生成了哪些组件
decoration_update_block × N        → 逐块换文案与图
decoration_get_page                → 复核 warnings
```

只有结构极简、你完全清楚要放什么时，才用 `decoration_create_page` 建空页自己搭。

`decoration_create_page` 只能建成草稿，传 `status=PUBLISHED` 会被拒绝 —— 发布是独立工具、独立授权。

---

## 七、字段写错了怎么自查

| 现象 | 真因 | 修法 |
| --- | --- | --- |
| 字段写了没生效，返回有 `UNKNOWN_FIELD` | 字段名不在契约内，被静默丢弃 | `decoration_get_component_schema` 传 type 看正确字段名 |
| `UNKNOWN_COMPONENT` | 组件 type 拼错 | 不传 type 拉全部 39 种 |
| `IDENTITY_NOT_FOUND` | identity 是编的或已失效 | 重新 `decoration_get_page` 取 |
| `REORDER_NOT_PERMUTATION` | 重排只给了部分 identity | 取全量，整体传回 |
| 发布被拦 + 逐条内容问题 | 有组件没内容（含占位文案） | 按提示逐块补，别重试 |
| `NOT_FOUND` | id 错 / 属于别的商户 / 已删除 | 用列表接口确认；跨租户一律返回「不存在」是正常设计 |

**不要做的事**：发布被拦后反复重试（结果一样，白烧配额）；改参数绕开 scope 限制；
拿 `NOT_FOUND` 当「权限不足」去猜（会得出错误结论并误导商户）。

---

## 八、做完必须交代的三句话

1. **改了哪几处**（具体到区块，不要只说「优化了首页」）
2. **现在是什么状态**（草稿，顾客还看不到 —— 除非已经发布）
3. **怎么退**（`decoration_rollback` + changeId，或改回原值）

商户拿这个判断要不要上线。少说一句，他就得自己去后台翻。

---

## 九、一次典型改版的完整骨架

> **商户**：首页太旧了，帮我改一下，主打秋季新品。

1. `decoration_list_pages` → 找到首页
2. `decoration_copy_page` → 副本草稿 P2
3. `decoration_get_page(P2)` → 看现有区块与 identities
4. `decoration_get_component_schema` → 确认 `TEXT` / `IMAGE_LIST` / `RICH_TEXT` 字段
5. `decoration_update_block(P2, 首图 identity)` → 换主图
6. `decoration_update_block(P2, 标语 identity)` → 「秋季新品上市，本周下单次日达」
7. `decoration_add_block(P2, LIST_REAL, position=2)` → 加新品列表
8. `decoration_get_page(P2)` → 复核，确认 warnings 为空
9. 复述：改了哪三处、首页会变成什么样、随时可退
10. `decoration_publish_page(P2)` → 先不带 `--confirm` 看后果 → 商户同意 → 带 `--confirm` 执行
11. （可选）`decoration_offline_page(旧首页)` 下线旧页

全程不碰线上页面，直到第 10 步。
