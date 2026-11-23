---
name: cz-saas-navigation-config
display_name: 五类导航配置
display_name_en: Navigation Configuration
description: 配置驰在灵枢 SaaS 的五类导航与入口：小程序底部导航、H5 底部导航、个人中心菜单、浮窗、开屏广告。含「先读再写」的硬前置、配置没有回滚通道这条关键事实、总部与门店的作用范围判断、以及改错后的手工还原方法。触发词：底部导航、tabbar、导航栏、菜单配置、个人中心菜单、我的页面入口、浮窗、悬浮图标、开屏、启动页、广告位、改导航、加个入口、删掉这个按钮。
description_zh: 用对话调整小程序与 H5 的底部导航、个人中心菜单、浮窗和开屏。这类配置没有回滚通道，本技能用「先读出来、再改、留原值」的方式保证改错也能还原。
description_en: Configure mini-program and H5 tab bars, member-center menus, floating buttons and splash ads — with a read-before-write workflow that makes every change recoverable.
examples_zh:
  - "把底部导航第二个改成「门店」，跳门店列表"
  - "个人中心菜单里的「会员卡」挪到第一个"
  - "开屏广告换成这张图，链接指向新品页"
  - "把这个浮窗关掉"
examples_en:
  - "Change the second tab to \"Stores\" and link it to the store list"
  - "Move the \"Member Card\" entry to the top of the member-center menu"
  - "Replace the splash ad image and point it to the new arrivals page"
version: 1.0.0
author: "驰在科技"
---

# 五类导航配置

导航是顾客进店后的第一条路。配错的后果很直接：顾客点不到该点的入口，或者点了跳到空白页。
这份技能的核心不是「怎么调接口」，而是**这类配置改错了怎么救** —— 因为它没有回滚通道。

调用语法见 `cz-saas-cli`；页面装修见 `cz-saas-page-makeover`；门店作用范围见 `cz-saas-store-decoration`。

---

## 一、五类配置是什么

| type | 含义 | 顾客在哪看到 |
| --- | --- | --- |
| `MP_NAVIGATION` | 小程序底部导航 | 小程序每页底部常驻 |
| `H5_NAVIGATION` | H5 底部导航 | H5 商城每页底部 |
| `USER_CENTER_MENU` | C 端个人中心菜单 | 「我的」页面的功能入口列表 |
| `FLOAT_NAVIGATION` | 浮窗 | 页面上的悬浮按钮 |
| `SPLASH_AD` | 开屏广告 | 打开 App / 小程序的首屏 |

读：`decoration_get_config --type MP_NAVIGATION`
写：`decoration_save_config --type MP_NAVIGATION --configJson '...'`
复位：`decoration_reset_config --type MP_NAVIGATION --storeId <门店id>`

---

## 二、最重要的一条：配置没有回滚通道

**`SYS_CONFIG` 类变更的 `rollbackable` 恒为 `false`，`decoration_rollback` 对它直接 400。**

也就是说：导航配置写错了，**没有任何工具能一键撤回**。唯一的还原依据是你在写之前读出来的那份原值。

所以这条不是建议，是前置条件：

```
① decoration_get_config --type XXX        ← 先把原值读出来
② 把原值留在对话里（贴出来，或存成文件）
③ 在原文基础上改（改字段，不要重写整份）
④ decoration_save_config                  ← strict，先看后果再确认
```

**第 ② 步经常被跳过，然后出事。** 读出来不落地，上下文一压缩就没了，等于没读。

如果商户没有备份、你也确实没读，还有一条兜底：`decoration_reset_config` 恢复继承总部配置
（仅门店级有效）—— 但那会丢掉门店所有的自配内容，属于「用大代价换可用」。

---

## 三、configJson 是字符串，不是对象

```bash
# ✅ 正确
cz-saas call decoration_save_config --type MP_NAVIGATION \
  --configJson '{"list":[{"text":"首页","icon":"...","link":"/pages/index"}]}'

# ❌ 错误：传了 JSON 对象，会被当成非法参数
cz-saas call decoration_save_config --type MP_NAVIGATION --json '{"type":"MP_NAVIGATION","configJson":{"list":[]}}'
```

正确姿势是**先读后改**：`decoration_get_config` 拿到的就是完整配置，
在它基础上改你要动的那几项，再整体序列化成字符串写回。

凭印象拼一份新配置的风险在于：商户之前配好的入口会被整体覆盖。
顾客第二天发现底部的「我的」不见了，而你无法解释它是怎么没的。

---

## 四、作用范围：总部还是门店

| 传参 | 作用范围 | 确认时必须说清 |
| --- | --- | --- |
| 不传 `storeId` | **总部**，影响全部门店 | 「所有门店的底部导航都会变」 |
| 传 `storeId` | 单店 | 「只有这一家店会变，其它店不受影响」 |

**改门店配置前先看一眼 `inherited`。**
`decoration_get_config --type XXX --storeId 123` 返回 `inherited=true`，说明这家店当前用的是总部配置。

这时候改它，等于**让门店脱离总部的统一管理**。这件事本身没错，但商户得知道 ——
很多商户的真实意图是「总部改一下，所有店跟着变」，结果改成了单店，其它店纹丝不动。

反过来，如果商户说「只有这家店要不一样」，那就要传 `storeId`，并且告诉他以后总部改这个类型，这家店不会再跟着变。

---

## 五、strict 动作怎么讲给商户听

`decoration_save_config`、`decoration_reset_config`、`decoration_copy_hq_to_store` 都是 strict：
不带 `--confirm` 时 CLI 打印后果并以退出码 **3** 结束 —— 这不是错误，是拦截。

**必须说清三件事**：

1. **影响范围**：总部还是这家店 / 哪个端（小程序、H5、还是两端都变）
2. **是否可逆**：**不能一键撤回**（这点必须讲，不能含糊成「可以改回来」）
3. **怎么改回来**：需要拿你读出来的原值手工写回

示例（改总部底部导航）：
> 这次改的是**总部**的小程序底部导航，所以**所有门店**的小程序底部都会跟着变。
> 这个配置**没有一键撤销**——如果改完发现不对，我需要用刚才读出来的原配置手工写回去。
> 原配置我已经记下来了。要现在改吗？

示例（改单店）：
> 这家店现在用的是**总部统一配置**。改完之后它就脱离总部管理了，
> 以后你在总部调整底部导航，这家店**不会跟着变**。确认要单独配吗？

**商户不同意就不要执行。** 不要用「已为您优化」绕过确认，也不要在下一轮换个参数偷偷执行。

---

## 六、常见配置错误

| 现象 | 真因 | 修法 |
| --- | --- | --- |
| 保存成功但 C 端没变 | 改的是总部，但门店有自己的配置（`inherited=false`） | 检查该门店 `decoration_get_config --storeId` |
| 改完所有门店都变了 | 没传 `storeId`，写到了总部 | 这是预期行为；要回退只能手工写回原值 |
| 门店改了没生效 | 配置写到了总部，但门店配置优先 | 改门店要传 `storeId` |
| `400` 提示 JSON 非法 | `configJson` 传了对象或转义错误 | 序列化成字符串，注意引号嵌套 |
| 导航项点进去是白页 | `link` 指向的页面不存在或未发布 | `decoration_list_pages` 确认页面状态 |
| 图标不显示 | 图标 url 为空 / 失效 / 相对路径 | 用完整 https 地址 |

---

## 七、改完怎么验收

不要只看「保存成功」就回话。至少确认两件事：

1. **读回来对一遍**：`decoration_get_config --type XXX`，看条目数、顺序、跳转链接是否如预期
2. **告诉商户去哪亲眼看**：小程序/H5 下拉刷新或重新进入；开屏广告要重启小程序才看得到

配置类改动**不需要发布**，保存即生效 —— 这点要和页面装修区分开，
不要跟商户说「我先存草稿，你确认后我再发布」，那会让他误以为还没生效。
