# 产品操作 · 地址与账户配置

> 覆盖：公务件地址簿、下单页不显示快递公司、钱包余额预警、系统管理员。
> 端与菜单名：管理端=**系统设置**／增值服务；员工端=**基础设置**；前台（收发室）端=**系统设置**。答复必须指明端。
> 相关操作见 `@//references/product-ops-approval.md`（寄件审批）、`@//references/product-ops-receipt-intl.md`（到件与国际件）、`@//references/printer-ops-faq.md`（打印机）。
> 配图为官方帮助中心截图，已统一为 HTTPS。

## 1. 公务件地址簿

员工寄公务件的地址簿可以提前设置到地址簿中。

**新增地址簿的限制**

- 公务寄件：地址**必须从办公地点中选择**，不能随意填写。
- 外勤寄件：创建地址簿时可选择「外勤寄件」，**外勤寄件不受办公地址限制，可选择任意地址**。

![新增寄件地址弹窗：办公地点下拉可选「外勤寄件」](https://file.kuaidi100.com/downloadfile/Im32z6MywROXp1WO6n9lyaZKtG-NlJarNkzrTRWBB4ZB5iDitOQaVxWj0Uh3cnZOLBOMNJ05L4euJ-IfOJFG1w)

**默认地址**

地址簿创建之后可以设置默认地址。下单时，寄件人地址**优先取默认地址**。

**其他操作**

寄件地址支持**导出**与**删除**。

![地址簿列表：支持导出与删除](https://file.kuaidi100.com/downloadfile/Im32z6MywROXp1WO6n9lyaZKtG-NlJarNkzrTRWBB4ZB5iDitOQaV4oz5wOg4Js1ArwWECJfEX_lU2oFh7pieA)

---

## 2. 下单页没有显示快递公司

### 2.1 寄私人件

- 私人件**仅支持快递100 提供的官方运力**，目前为**京东、德邦、顺丰**三家。
- 下单后由快递员上门揽件，**直接与快递员线下面对面结算**。
- 私人寄件**不支持使用企业的合作月结账号**。

> 因此私人件看不到企业已绑定的其他月结快递公司属正常现象，不是配置错误。

### 2.2 寄公务件

前提：已在【合作快递公司】添加该快递公司的月结账号。若仍未显示，按顺序排查：

**第 1 步：确认下单区域**

企业有多个办公地点或收发点时，先确认下单选择的区域/收发点，与绑定了该快递公司的区域是否一致。不一致则重新选择下单区域。

![下单区域选择](https://file.kuaidi100.com/downloadfile/tBFZ0ca4OFXP4h2DsBcfOABRIto9fEBJObvV08GU6wt9RhteQ1mKhRisCKRVoPVhDsJCJTOofcblmQGlm-Q30g)

**第 2 步：确认快递公司已授权给收发点**

到【办公地点设置】→【收发点设置】，找到对应收发点，点击编辑，**勾选新添加的快递公司**。完成后员工寄公务件即可选择该快递公司走月结。

![收发点编辑：勾选已添加的快递公司](https://file.kuaidi100.com/downloadfile/YCCAIcsGzR4Cbh0DCpB8qJXev2DVSPhSXtEBwdACrL6olsQ0w9QDkm0jbFy2IUTlKhv25y01Jhqk9dMajOyelg)

> 单一办公地点和收发点的企业，问题通常就在第 2 步——月结账号加了，但没授权给收发点。

---

## 3. 账户与权限

### 3.1 钱包余额预警

**预警余额设置位置：** 管理端 → 增值服务 → 钱包充值

![增值服务-钱包充值](https://file.kuaidi100.com/downloadfile/yB75skrhrmxofIlLUbqeN2lrCL8UxPOniGn1zrXczJEuk4cCCN2hBXW0uqh4tYHfsvgzqA9jkckggNVcuf_BvA)

**提醒触发时机**

1. 钱包余额**初次少于**预警余额时；
2. 余额有增加但**仍少于**预警余额时（**包括取消订单退款导致的余额变化**）。

以上两种情况都会提醒管理员。

> 注意第 2 条：余额增加也可能触发提醒，因为增加后仍未超过预警线。用户容易误以为"钱变多了为什么还提醒"。

### 3.2 系统管理员添加

**入口：** 管理端 → 系统设置 → 系统管理员添加

在此处添加或删除系统管理员，方便多人同步管理。**此处添加的管理员拥有应用所有权限。**

![系统设置-系统管理员添加](https://file.kuaidi100.com/downloadfile/OegvcLv-6RRcU2BcUM6XMTKMvg7nLMwaMtiZN6fyX0FzkkbmibNnN2A4yBWh7CJkCdoYlEcBSzyoWSrM7hK7_g)

![添加管理员弹窗](https://file.kuaidi100.com/downloadfile/OegvcLv-6RRcU2BcUM6XMTKMvg7nLMwaMtiZN6fyX0FzkkbmibNnN5o1hUdvIeLKIbwVP2iMERE0IAt1TKqR-w)

**⚠️ OA 管理员不可在此删除**

OA（企业微信、飞书、钉钉、云之家）管理员**默认同步系统管理员权限**，在系统内**不支持删除**。若需删除该管理员，必须到对应 OA 后台删除其 OA 管理权限。

---
