# 产品操作 · 到件、出库与国际件

> 覆盖：到件异常判定与处理、高拍仪出库、顺丰国际 ICRM 号获取。
> 端与菜单名：管理端=**系统设置**／增值服务；员工端=**基础设置**；前台（收发室）端=**系统设置**。答复必须指明端。
> 相关操作见 `@//references/product-ops-setup.md`（地址与账户）、`@//references/product-ops-approval.md`（寄件审批）、`@//references/printer-ops-faq.md`（打印机）。
> 配图为官方帮助中心截图，已统一为 HTTPS。

## 1. 到件与出库

### 1.1 到件异常

#### 判定机制

派件员通过【快递100收件端】APP 扫码入库后，系统用**面单上的收件手机号**匹配组织架构中的对应收件人。以下手机号不匹配的情况都会导致到件异常：

| # | 原因 |
|---|---|
| 1 | OA（企微、飞书、钉钉、云之家）用户**首次登录时未绑定手机号**，系统无法匹配 |
| 2 | 员工在组织架构中登记的手机号与快递收件号码**不一致** |
| 3 | 派件员扫码时**识别面单手机号错误** |
| 4 | 面单手机号为**隐私号**（如 130\*\*\*\*0000），系统按手机**尾号**匹配；企业内存在两个或以上同尾号员工时无法判断，判为到件异常 |

若以上情况都不存在，需确认是否**快递员派错件**。

#### 处理方式

管理员可在管理端**手动选择收件人**：到件列表中找到对应订单，点击右侧【修改】按钮，修改实际收件人。

![到件列表-修改实际收件人](https://file.kuaidi100.com/downloadfile/rqyFLInvSwgIsTLbHroDb10_kQUjp9icqOIdCWCX4NTy1OkzaWXE1CQke9DJ8dNhptCTWVXo0a6Xov_o5528uQ)

> 同一尾号冲突（原因 4）是最容易被忽略的一类，尤其是大企业尾号重复概率不低。排查时可先问「面单是不是隐私号」。

### 1.2 高拍仪出库

授权第三方高拍仪操作包裹出库，高拍仪通过**扫描员工身份码或包裹物流码**出库。

**绑定方式：** 前台（收发室）端 → 系统设置 → 高拍仪出库 → 绑定高拍仪 → 生成授权码 → 将该授权码绑定到高拍仪的管理界面。

![收发室-系统设置-高拍仪出库](https://file.kuaidi100.com/downloadfile/6HvlYW2o5gF795wQajmn29mYNtoSe3mUMx4EhE4kcq3QOP0XzGYL5T8LeZMU3bT0dpeFHT1owY_kCCfHIvhQvQ)

---

## 2. 顺丰国际 ICRM 号获取

顺丰国际下单需先获取 **ICRM 号**，才能对接顺丰国际开放平台下单。

1. **进入顺丰开放平台控制台**：`https://buac.sf-express.com/login`，使用顺丰提供的**企业账号**登录。
2. **开发者对接** → 新建应用 → 输入应用名称创建应用。

![顺丰开放平台-开发者对接](https://file.kuaidi100.com/downloadfile/kTtLXPnY_PYBceL9UErt2eZs9xgq0pWBf6ybvXquo3XMGKqWoUWkdoeU_VWNPDrqw8SFsrr6LtxshoHgu4-d9g)

![输入应用名称创建应用](https://file.kuaidi100.com/downloadfile/W4AeewwSbiHqHdAlXMMPNgc4HWMGmUYBdUfa0RNLE7RyCMLGZTldd_tHAb0IY1vTKcd_ac_niES7B9auFMCsUw)

![应用创建完成](https://file.kuaidi100.com/downloadfile/W4AeewwSbiHqHdAlXMMPNgc4HWMGmUYBdUfa0RNLE7RyCMLGZTlddzaGO3fyNcrfqx92RhFRmAeG3xEd5UrI4A)

3. **给新建应用添加国际件接口**：点【关联 API】。

![应用详情-关联API](https://file.kuaidi100.com/downloadfile/W4AeewwSbiHqHdAlXMMPNgc4HWMGmUYBdUfa0RNLE7RyCMLGZTldd7ZumeqJa44AVgbpzLGKFF78GzC1fjSqkw)

选择「国际件 API - 国际快递业务场景接入」，勾选「创建物流订单」「取消物流订单」后点关联。

![选择国际件API与业务场景](https://file.kuaidi100.com/downloadfile/Lw_1t_noV1i-abgK3ZHG6kAC7KFCs1wuyzWUTWbX45VPxu9NnM0W39shJWD1AzIJ6APg6fFZQojjuBX6PDrHyw)

![勾选创建物流订单、取消物流订单](https://file.kuaidi100.com/downloadfile/Lw_1t_noV1i-abgK3ZHG6kAC7KFCs1wuyzWUTWbX45VPxu9NnM0W3-HIOUt5dA7fqNLayop1XLVVsTWV0HPLDA)

4. **上线接口**：对刚关联的两个接口点【测试】→ 点【提交测试】。测试完过一会儿状态会变为「待上线」，需等待；未变化可多重测几次。

![接口测试与提交测试](https://file.kuaidi100.com/downloadfile/Lw_1t_noV1i-abgK3ZHG6kAC7KFCs1wuyzWUTWbX45VPxu9NnM0W30CqHeH0x3CDC26WhsZkuoBocI0GWLrVmw)

5. **绑定月结**：应用列表点应用详情 → 点【绑定月结】→ 将月结账号绑定进去。

![应用列表-点击应用详情](https://file.kuaidi100.com/downloadfile/Lw_1t_noV1i-abgK3ZHG6kAC7KFCs1wuyzWUTWbX45VPxu9NnM0W31aZdthPO2gEA3HoA0b2CdTmC38v26W73Q)

![应用详情-绑定月结](https://file.kuaidi100.com/downloadfile/6ifWBC7zn0YUIWsuRbRzUUfMqLFc5CZY6gpM8JHSJ2OVQrsMc9rE-n15zvLyCS_I_X4MjtpTfnvuEThPZBp4og)

6. **IUOP 注册**：`https://ibu-icas.sf-express.com/`，注册后进入【管理中心】→【基本资料】，其中**用户编号即为 ICRM 号**（ICRM 开头）。
7. **联系顺丰**在 IUOP 完成月结绑定。
8. 以上完成后，在**快递100 管理端 → 快递公司设置**中绑定顺丰国际月结。

> 第 4 步「待上线」需要等待，是最容易误判为失败的一步；第 7 步依赖顺丰侧人工操作，需提示用户预留时间。


---
