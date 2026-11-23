---
name: cz-saas-store-decoration
display_name: 门店装修与继承总部
display_name_en: Store Decoration & HQ Inheritance
description: 管理连锁商户的多门店装修：看清某家店哪些是自配、哪些继承总部，把总部装修同步到门店，或让门店恢复继承。含「继承前必看总览」这条反事故前置、overwrite 的真实语义、以及总部门店 id 与普通门店 id 的区别。触发词：门店装修、门店配置、继承总部、同步总部、同步到、复制总部装修、总部的装修、统一成总部、所有门店、这家店、恢复用总部、恢复默认、覆盖门店、门店不一样、单店配置、连锁、多门店、门店首页。
description_zh: 连锁商户给门店配装修时最容易出的事故是「一次性覆盖掉门店自己精心配好的入口」。本技能用「先看总览再动手」的方式避开这类事故，并讲清 overwrite 到底覆盖什么。
description_en: Manage decoration across multiple stores — see what each store self-configured versus inherited from HQ, sync HQ decoration safely, or restore inheritance.
examples_zh:
  - "把总部的装修同步到杭州湖滨店"
  - "这家店哪些是它自己配的？哪些用的总部？"
  - "让这家店恢复用总部的底部导航"
  - "所有门店都统一成总部装修"
examples_en:
  - "Sync HQ decoration to the Hangzhou store"
  - "Which parts of this store did it configure itself?"
  - "Make this store inherit the HQ tab bar again"
version: 1.0.0
author: "驰在科技"
---

# 门店装修与继承总部

连锁商户的装修有两条独立的路：总部配一套给所有店用，门店可以自己配一套覆盖它。
**90% 的门店装修事故都出在同一件事上：门店自己精心配过，被一次「继承总部」覆盖掉，而且没有回滚。**

这份技能就是为了挡住这件事。

工具语法见 `cz-saas-cli`；五类配置细节见 `cz-saas-navigation-config`；页面装修见 `cz-saas-page-makeover`。

---

## 一、动手前必须先看总览

```bash
cz-saas call decoration_store_overview --storeId <门店id>
```

它返回：页面数 / 已发布数、五类配置各自是「门店自配」还是「继承总部」、可继承清单。

**这一步不能跳，原因有两个：**

1. 门店自己已经配过，你一次「继承总部」把它抹了 —— 商户会问「我上周配的东西呢」；
2. 门店本来就在用总部配置，你把它当成「没配过」又配一遍 —— 白干，还可能改坏。

判据就是返回里的 `inherited` 字段。**这是唯一可信的判据，不要靠猜。**

### 两个 id 别搞混

`decoration_store_overview` 的 `storeId` 是**普通门店**的 id，不是「总部门店」的 id。
两者不是一回事。真实门店 id 从 `store_list` 取。

总部视角不用这个工具：看总部页面用 `decoration_list_pages`，看总部配置用 `decoration_get_config`（不传 storeId）。

`storeId` 传空会直接报「门店不存在」，别试。

---

## 二、继承总部：overwrite 到底覆盖什么

```bash
# 安全默认：只补门店还没配的类型，门店已自配的一律不碰
cz-saas call decoration_copy_hq_to_store --storeId <门店id>

# 危险：连门店已自配的类型一起覆盖
cz-saas call decoration_copy_hq_to_store --storeId <门店id> --overwrite true
```

| overwrite | 语义 | 什么时候用 |
| --- | --- | --- |
| 不传 / `false` | 只补门店「还没配」的类型 | **绝大多数场景就是它** |
| `true` | 连门店「已自配」的类型一起覆盖 | 商户明确说要「全部统一成总部」 |

还可以用 `--types MP_NAVIGATION,USER_CENTER_MENU` 只处理指定类型，缩小爆炸半径。

**`overwrite=true` 之前，必须把「会丢掉什么」念给商户听。**
念的内容来自 `decoration_store_overview`：哪些类型是门店自配的，逐条列出来。

> 这一步会把总部的装修复制到「杭州湖滨店」，并且**覆盖门店自己已经配好的底部导航和个人中心菜单**。
> 门店之前专门设过的三个入口会消失，而且**没有一键撤销**。
> 要覆盖，还是只补门店还没配的部分？

---

## 三、恢复继承：门店配置会被删掉

```bash
cz-saas call decoration_reset_config --type MP_NAVIGATION --storeId <门店id>
```

语义等同 B 端配置页的「恢复默认」：删除门店级配置，之后门店跟着总部走。

**这是不可逆的** —— 门店自配内容直接消失，没有快照。
`decoration_reset_config` 只对门店级有效，总部级不能用（总部没有可回落的上级）。

如果商户只是想「临时用一下总部配置」，更好的做法是：先 `decoration_get_config --storeId` 把门店配置读出来留档，再 reset。

---

## 四、门店页面与总部页面

页面本身也分总部和门店：`decoration_list_pages --storeId <门店id>` 看这家店的页面。

- 改**总部**页面（不传 storeId）→ 影响所有继承总部页面的门店
- 改**门店**页面（传 storeId）→ 只影响这一家

判断某个页面是哪一层的：不传 storeId 的列表里能看到 → 总部页面；只有在 `--storeId` 列表里能看到 → 门店页面。

**给门店做专属活动页的标准路径：**

```
decoration_list_pages --storeId <门店id>      看这家店已有哪些页面
decoration_list_templates                     挑模板
decoration_apply_template --storeId <门店id>  建在该门店名下
decoration_update_block × N                   换文案与图
decoration_get_page                           复核
decoration_publish_page --storeId <门店id>    发布
```

**不要**用总部页面 + 门店覆盖的方式做单店活动 —— 那条路会在下次总部改版时被冲掉。

---

## 五、三种典型诉求怎么接

**「所有门店统一成总部装修」**
1. `store_list` 取全部门店
2. 逐店 `decoration_store_overview`，看哪些店是自配的
3. 把自配清单汇总念给商户：「这 3 家店有自己配的内容，统一后会被覆盖：A 店改过底部导航、B 店改过个人中心…」
4. 商户确认后再逐店 `--overwrite true`

**「只有这家店要不一样」**
1. `decoration_store_overview` 确认当前是继承状态
2. 直接改门店配置（传 storeId），并提醒：以后总部改这个类型，这家店不会跟着变

**「门店改坏了，先恢复成总部」**
1. 先 `decoration_get_config --storeId` 把现状读出来留档
2. `decoration_reset_config`（strict，讲清「自配内容会消失」）
3. 复核：再 `decoration_get_config --storeId` 应显示 `inherited=true`

---

## 六、出错对照

| 现象 | 真因 | 修法 |
| --- | --- | --- |
| 「门店不存在」 | `storeId` 传空，或传了总部门店的 id | 用 `store_list` 取真实门店 id |
| 继承后门店入口没了 | `overwrite=true` 覆盖了门店自配 | 无回滚，只能按留档原值手工写回 |
| 改门店没生效 | 改到了总部（漏传 storeId） | 补 `storeId` 重改 |
| 改总部后某店没变 | 该店是自配状态（`inherited=false`） | 正常行为；要同步需 `decoration_copy_hq_to_store` |
| 门店页面总部看不到 | 页面建在门店名下 | 用 `decoration_list_pages --storeId` 查 |

---

## 七、底线三条

1. **不看 overview 不继承。** 这是唯一能提前发现「会覆盖什么」的动作。
2. **`overwrite=true` 必须逐条念损失清单。** 说「会覆盖门店配置」等于没说，商户听不懂覆盖了哪几项。
3. **门店自配的内容没有快照。** 想保住就先读出来留档，读完再动手。
