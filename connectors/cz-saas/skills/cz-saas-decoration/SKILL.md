---
name: cz-saas-decoration
display_name: 装修需求分诊
display_name_en: Decoration Request Triage
description: 当商户只说「帮我装修一下」「店铺改一改」而没说清具体改什么时，用本技能判断该走哪条流程。它只做分诊与路由，具体做法分别在 cz-saas-page-makeover / cz-saas-navigation-config / cz-saas-store-decoration / cz-saas-content-ai-readable / cz-saas-publish-safety 五个技能里。触发词：帮我装修、店铺改一改、整体优化一下、想弄得好看点、弄得好看点、感觉不太行、看怎么改、不知道从哪改、从哪开始、装修该从哪开始。
description_zh: 装修需求说不清时的分诊台。用五个问题定位真实诉求，再转给对应的专项技能，避免一上来就动手改错东西。
description_en: Triage for vague decoration requests — ask five questions to locate the real need, then hand off to the matching specialist skill.
examples_zh:
  - "帮我把店铺装修一下，弄得好看点"
  - "店铺整体感觉不太行，你看看怎么改"
examples_en:
  - "Help me make my store look better"
  - "The store feels off overall — what would you change?"
version: 1.0.0
author: "驰在科技"
---

# 装修需求分诊

「帮我装修一下」不是一个能直接执行的需求。
这份技能只做一件事：**在动手之前，把它拆成一个具体动作。**

---

## 一、先问三个问题，别急着调工具

| 问什么 | 为什么问 |
| --- | --- |
| **改哪一块？** 首页 / 某个活动页 / 底部导航 / 门店 / 还是都改 | 决定走哪条流程，走错会改到不该改的地方 |
| **改成什么样？** 换图换字，还是整体重排 | 「换内容」和「换结构」的路径完全不同 |
| **现在有什么问题？** 不好看 / 转化低 / AI 客服答不出来 / 门店不统一 | 决定要不要连带做内容与配置的调整 |

**不要跳过提问直接改。** 「整体优化」这四个字最危险 —— 它会诱导你改结构，
而商户可能只是觉得图太旧。改结构意味着重排全部 identity，出错面最大。

---

## 二、路由表

| 商户说的 | 走哪个技能 |
| --- | --- |
| 换轮播图、改文案、加一块、删一块、调顺序、新建活动页 | `cz-saas-page-makeover` |
| 底部导航、个人中心菜单、浮窗、开屏广告 | `cz-saas-navigation-config` |
| 多门店不一样、继承总部、单店配置、恢复默认 | `cz-saas-store-decoration` |
| AI 客服答不出来、顾客搜不到、内容怎么写 | `cz-saas-content-ai-readable` |
| 发布、上线、下线、撤回、恢复上一版 | `cz-saas-publish-safety` |
| 工具怎么调、报错了怎么办、授权失效 | `cz-saas-cli` |

一个需求常常跨两个技能。典型：「首页太旧，而且顾客问营业时间答不出来」
→ 先 `cz-saas-page-makeover` 改结构，再用 `cz-saas-content-ai-readable` 重写那段文案。

---

## 三、分诊之后的三条通用铁律

不管走哪条路，这三条都成立：

1. **改线上页面先复制副本。** `decoration_copy_page` → 改副本 → 发布副本。原页面全程不动。
2. **identity 只能从 `decoration_get_page` 拿，不能编。**
3. **动手前先把原值读出来。** 页面能回滚，**五类配置不能** —— 配置类改动前必须 `decoration_get_config` 留档。

---

## 四、如果商户只有一句话，这样回应

> 想先确认三件事再动手：
> ① 您说的是首页，还是某个具体活动页？
> ② 是想换图换文案，还是整体重新排一遍？
> ③ 现在是觉得不好看，还是顾客来了不转化？
>
> 我先看一眼现在的页面，再给您一个具体方案 —— 不会直接改线上。

「先看一眼」对应 `decoration_list_pages` + `decoration_get_page`，都是只读，零风险。
带着现状去问，比空口问效率高一倍。
