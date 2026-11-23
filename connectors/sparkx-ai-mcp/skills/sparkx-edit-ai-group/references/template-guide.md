# Template guide - recommending a platform template by campaign purpose

Many users don't know how to set up a managed group: goal, ACOS, personality and a dozen
action-space switches, each of which should be on or off depending on what the campaigns
are *for*. The platform ships **system templates** that already encode the right settings
for common purposes. This guide is how you lead the user to the right one.

**Recommend, never force.** A template is an expert starting point, not a requirement. The
user can take it, pick another, or set everything up themselves - and can change any single
setting after applying one.

## When to recommend

| Situation | Recommend? |
|---|---|
| Creating a group and the user only gave the campaigns, not how to set it up | Yes |
| The user asks how a group should be set up ("这个组该怎么设", "帮我看看设置") | Yes |
| Editing, and the user is hand-changing several action-space switches at once | Mention it once; if they don't take it, do what they asked |
| Changing a single value (target ACOS, budget, personality, one switch) | **No** - just make the change |
| The user already gave a full configuration, named a template, or said not to use one | **No** |
| The user already declined a recommendation in this conversation | **No** - don't raise it again |

Every recommendation ends with three choices: **use this template / pick another / set it up
myself**. If they choose to set it up themselves, continue with the normal workflow and don't
push templates again.

## Purpose -> template

Template names are exact - use them to look up the id (see "Applying"). The "why" column is
the **only** source for explaining why a template is set the way it is; say it in the user's
language, but don't add claims about switches beyond what it says.

| Purpose | Template (exact name) | Fits when | Before applying | Why it is set this way (tell the user) |
|---|---|---|---|---|
| New product, build keyword relevance | 新品期产品建立和关键词相关性 | New product needs purchases on relevant terms and needs demand validated | Standard product with enough budget: core keywords, exact; otherwise auto + broad + exact | 开启出价优化、收词和否词，让 AI 尽快试出能出单的词并收进来；暂不开启结构优化，先让每个活动充分跑出数据，不急着关停活动或商品。 |
| Find new keywords / ASINs | 广告拓词 | Discover more valuable keywords / ASINs | Auto / broad / phrase / expanded ASIN / category targeting | 开启收词和否词：跑出来的好词自动收进来，无效词自动否掉，持续发现新流量。 |
| Push keyword rank, maximise orders | 推关键词排名（ACoS优先） | Core keywords, more orders on a limited budget, any placement | One keyword per campaign, exact match. Check the keyword is worth pushing first | 关闭预算重新分配：推排名期 ACOS 本来偏高，不能让 AI 按 ACOS 把预算挪走，否则单量不够、排名推不上去。保留出价优化，在位置不限的前提下控制成本；投放词由你精选，不让 AI 加减词。 |
| Push keyword rank, hold a placement | 推关键词排名（展示位优先） | Spend concentrated on a specific placement, e.g. top of search | One keyword per ad group, low bid + high placement adjustment set up beforehand | 在“ACoS优先”的基础上再关闭出价优化：出价和位置溢价由你定，AI 不动价，避免打乱占位策略。仍不满足时，可以改用“关键词卡位”功能或人工接管。 |
| Win traffic from competitor detail pages | 争夺竞品详情页关联位置 | Shoppers jump from a competitor page to ours and buy | Target specific competitor ASINs, low bid + high product-page adjustment, expanded targeting off | 关闭预算重新分配和收词、否词：投放的竞品 ASIN 是精选的，预算和定向保持稳定，靠低出价加高详情页溢价拿位置。 |
| Win competitor orders / cross-sell | 抢竞品订单/内部交叉购买 | Compete head-on with target competitors, any placement | Target specific ASINs, expanded targeting off | 开启预算重新分配，预算自动流向表现好的竞品定向；关闭收词和否词，定向的 ASIN 由你精选。 |
| Defend brand search traffic | 品牌防守 | Keep the brand's own search traffic | Brand terms, broad; switch to exact (or 关键词卡位) to hold a specific placement | 关闭预算重新分配和收词、否词：品牌流量要稳定守住，不因 ACOS 波动挪走预算，也不需要加减词。要抢特定位置时，建议改用精准匹配或“关键词卡位”。 |
| Defend own detail pages | 详情页流量防守 | Stop shoppers leaving our main product pages | Target own ASINs, expanded off; **product-page adjustment must be set beforehand** | 和品牌防守一样：关闭预算重新分配和收词、否词，让自家页面上的防守位稳定占住，不因 ACOS 波动挪走预算。详情页位置溢价需提前设好。 |
| Low-cost orders from broad traffic | 低成本捡漏 | Fill in low-cost orders from cheap, broad traffic | Low bids; auto / broad / phrase / category | 关闭出价优化，防止 AI 为抢流量把低价组的出价越抬越高；开启否词和收词，泛流量里不出单的词自动否掉，出单的词收出来单独投。 |
| Cover scattered long-tail terms | 持续覆盖长尾流量（契合Cosmo算法） | Keep reaching small, scattered, cheap terms | Bids between low-cost and normal | 和低成本捡漏一样不让 AI 抬价；另外开启定向暂停 / 补充：长尾词零散，让 AI 持续淘汰无效词、补充新词。 |
| Mature product, lower ACOS steadily | 稳定期产品持续优化ACoS | Keep orders steady while testing lower ACOS | If budget goes unspent, the ACOS target is too tight - loosen it | AI 能力全部开启，在不影响出单的前提下全面优化 ACOS。如果预算花不完，说明 ACOS 目标定得太紧，需要放宽。 |
| B2B product, weak weekends - keep total budget | B端属性产品（总预算不变） | Promotion stage, needs absolute order volume | **New SP group only** - see the note below | 周末转化低，周末自动降预算，省下的预算挪到周一、周二的高转化时段，总预算不变。 |
| B2B product, weak weekends - cut cost | B端属性产品（成本控制） | Steady or declining stage, wants lower cost | Tell the user overall orders will drop too. **New SP group only** - see the note below | 周末转化低，周末自动降预算，省下的预算不再补回，整体成本和单量都会下降。 |

**The two B2B templates are SP only** - SB groups have no B2B action space - **and run Budget
Daypart (rule 13) in Rule mode.** Through MCP they can only be applied by **creating a new SP
group** from them - the rule is carried over as-is; say in the preview that Budget Daypart runs
as a fixed rule, not AI. Applying them to an **existing** group is rejected (see "Applying"
step 8); for that, point the user to the platform.

**These templates are built around SP** (keywords, placements, ASIN targeting). On an SB
group - **creating** a new one from the template or **editing** an existing one with it - the
server turns the template's SP-only switches off and the request succeeds; the response
summary lists the switches that were turned off - tell the user which parts won't take
effect. (Switching an SP-only switch on yourself in `aiActionSettings` for an SB group is still
rejected.) On an SD group most purposes above don't apply, and SD create rejects any template with
按表现调预算 on; don't recommend a template for SD unless the user asks for one.

### Staged create -> edit flows (SP/SB) - AI off until the final configuration is in place

**Any SP/SB flow that needs a create followed by an edit to reach its final configuration
creates the group with `aiStatus=0`.** AI must not start spending on a configuration that isn't
finished. This covers creating an SP/SB group from a template but with a switch changed. SD doesn't need it: an SD create
takes `templateId` and the changed switch together in one call. In every case:

1. Create with AI off.
2. Make the edit(s) that finish the configuration.
3. Read the group back and check it.
4. Turn AI on only if the user confirms, after seeing the read-back.

Show the whole sequence in the preview before the first call. If an edit or the read-back
fails, stop: leave the group off, don't retry blindly, and tell the user what exists and what's
missing.

**The "why" column describes how each template is designed.** The template detail (read with
`isSystemTemplate=1`, see "Applying") shows the actual switches. If the detail or the read-back
after applying contradicts the "why", report the actual setting and drop that part of the
explanation - never defend the text against the data.

### Purposes with no template

| Purpose | What to do |
|---|---|
| Control cost, maximise profit | Closest is 稳定期产品持续优化ACoS. Recommend it and say the difference: profit maximisation watches TACOS and net gross profit, not just ACOS |
| SD remarketing (views / purchases audiences) | No template. SD groups have only 预算重新分配 and 定向收割; suggest both off - remarketing budget follows the purchase cycle, not ACOS, and the audiences are hand-picked. Then continue with the normal workflow |
| Purpose can't be determined | Recommend nothing; ask |

### Things a template can't do

- **Protected words** (for model-fit products such as auto parts: brand / vehicle model / year
  roots must not be auto-negated). Word lists are not settable through MCP - after applying,
  tell the user to add them in the platform.
- **One switch different from the template.** It depends on the path:
  - **Editing an existing SP/SB group**: one call does it. Pass `templateId` plus
    `aiActionSettings` containing just that switch - the server merges current config <-
    template <- your values.
  - **Creating SP/SB**: don't send `aiActionSettings` with `templateId` - on create, yours
    replaces the template's whole action-space config. Create from the template, then change the
    switch in a plain edit (no `templateId`), following the staged-flow rule above: create with
    AI off, edit, read back, then turn AI on only once the user confirms.
  - **Creating SD**: pass the switch together with `templateId` in the one create call.
- **Bid tiers** (the same terms split into high / mid / low bid campaigns): one group per tier.
  Fixed bids per tier: after applying, turn off 按表现调价. Bids allowed to float within a band:
  keep it on, and give each group a 竞价范围 that doesn't overlap the others.

## Identifying the purpose

The purpose is what the recommendation rests on - get it wrong and you recommend the opposite
setup. Take it from the most reliable source available:

1. **The user says it** ("这几个是推排名的") - use it as stated, no need to confirm the purpose.
2. **A naming convention** (campaign names containing "Brand", "Rank", "Low"...) - confirm the
   convention with the user once, then reuse it.
3. **Inferred from campaign structure** - state the inference and the evidence, and **get the
   user's confirmation before recommending on it.**
4. **Can't tell** - ask; don't recommend.

### Structural signals (all verified readable via `get_entity_metadata`)

| Signal | How to read it | Leans towards |
|---|---|---|
| Manual, exactly one exact keyword per ad group | `keyword` filtered by `adGroupId`; `meta.total` = 1 and `matchType` = `exact` | 推关键词排名（ACoS优先）; with a high `topOfSearch` adjustment and low bid -> （展示位优先） |
| ASIN targeting, no expanded targeting, high product-page adjustment | `target.targetMatchType` = `asinSameAs` and no `asinExpandedFrom` in the campaign; `placement` `productPage` `multiplier` | `targetText` is a competitor ASIN -> 争夺竞品详情页关联位置; own ASIN (in `asin` entity) -> 详情页流量防守 |
| ASIN targeting, no expanded targeting, no notable adjustment | as above | 抢竞品订单/内部交叉购买 |
| Keywords contain the brand | `keyword.keywordText` contains `asin.asinBrand` (case-insensitive) | 品牌防守 - spelling variants come from the user |
| Auto / broad / phrase / category with bids clearly below the store's other campaigns | `campaign.targetingType`, `keyword.matchType`, `keywordBid` / `targetBid` | 低成本捡漏 or 持续覆盖长尾流量 - if you can't separate them, ask |
| Auto / broad / phrase at normal bids | as above | 广告拓词 or 新品期产品建立和关键词相关性 - ask whether the product is new |
| SD targets with a `lookback` audience | `target.targetText` | SD remarketing (no template) |
| None of the above | - | 稳定期产品持续优化ACoS, only after asking the business goal |

Reading notes:
- Use `keywordBid`; `keywordCurrentBid` can read back `0`.
- `placement.multiplier` is a percentage string: `"50.00"` = +50%, valid range 0–900. A
  negative or out-of-range value, or `null`, means the adjustment is unavailable - leave that
  campaign out of any high / low comparison.
- "Clearly below" has no agreed number. Say what you see ("most of these bids are under half
  the store's typical bid") and let the user confirm.
- Counting keywords per ad group is one call per ad group. With many campaigns, check a
  representative few and say so.

**Mixed purposes in one group:** recommend splitting into one group per purpose, each with its
own template. Never apply one template to campaigns with different purposes.

## What to say (fixed order)

1. **Purpose and evidence** - what these campaigns are for, and how you know.
2. **The template and one line on what it is for** - use the template's own description
   (`remark` from the template list).
3. **Why it is set this way** - from the table above.
4. **Before applying** - what to prepare.
5. **What the user decides** - the target ACOS, always; plus the budget on SD; plus AI on/off
   if they haven't said.
6. **The three choices** - use it / pick another / set it up myself.

Example (Chinese user):

> 这 5 个活动是低出价的自动 / 广泛活动（依据：出价明显低于店铺其他活动，且都是自动 / 广泛匹配），适合**“低成本捡漏”**模板：用低价补充泛流量订单。
> **为什么这样设：**这个模板会限制 AI 上调出价，避免为了抢流量把低价组的出价越抬越高；同时自动否掉不出单的词、把出单的词收出来。
> **套用前：**保持低出价，覆盖自动 / 广泛 / 词组 / 类目定向。
> **需要你定：**目标 ACOS。
> **你可以：**用这个模板 / 换一个 / 自己逐项设置。

## Applying

1. **Look the id up by exact name every time** - `get_ai_group_template(applyFlag=1,
   searchName=<name>)`, then exact-match `templateName` in the result. Don't hard-code ids. If
   no system template matches (renamed or removed), say so and fall back to the normal
   workflow. If the user has their own template with the same name, ask which one they mean.
   Carry the list item's `isSystemTemplate` (1 for these) into every later call.
2. **Read the detail** - `get_ai_group_template(templateId=..., isSystemTemplate=1)` for a
   system template (without the flag it returns `Template_Not_Exist`). Show what it sets: goal,
   target ACOS, personality, the action-space switches, and any automation rule in Rule mode
   (`status=1`). A template with detail `status=2` is archived - the write tools reject it; say
   so and pick another.
3. **Pass `acos` explicitly.** Show the template's `acos` and ask whether to keep it or use the
   user's own target - the template doesn't know the user's margin. On an existing group, also
   show the group's current target ACOS.
4. **AI status is never taken from a template** (a template's `status` means normal / paused /
   archived, not AI on/off). **A new group that one create call fully configures starts on by
   default** - SP, SB and SD alike; leave `aiStatus` / `status` out unless the user asked
   otherwise. An existing group keeps its current status - send it only when the user asked for
   a change. **Staged flows are the exception** - see "Staged create -> edit flows" above. On
   **SD, applying a template to an existing group needs its AI already on** - groups with AI
   off are skipped; turn AI on in a separate edit first.
5. **On create, don't send `aiActionSettings` with `templateId`** - see "Things a template can't
   do" for the create / edit difference.
6. **On an existing group, applying a template overwrites what the template contains** -
   priority is your params > the template's values > the group's current config. Settings the
   template doesn't carry (including automation rules it doesn't contain, and AI on/off) stay
   as they are. Say so in the preview, show the current target ACOS,
   and ask whether to keep it.
7. **After applying, read the group back** (`entity='aiGroup'`) and show the user what is
   actually in effect: goal, target ACOS, AI 人格 as its number only (e.g. "AI 人格：4", never a
   text label), AI status and each action-space switch.
   Point out anything that differs from the preview.
8. **If the call rejects the template**, relay the error and offer the alternatives: set it up
   manually, or apply the template in the platform. On create, check by name whether the group
   was made before retrying - create is not idempotent. **Rule-mode rejection on an SP/SB edit**
   (the template has automation rules with `status=1`, e.g. the two B2B templates): the error
   lists three ways out - create a new group from the template, apply it in the platform, or
   retry with explicit `aiAutomation` in AI mode (which drops the template's rules). Show all
   three and wait for the user's choice before retrying.
