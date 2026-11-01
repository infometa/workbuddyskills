# 云打印机操作与故障 FAQ

> 覆盖：装纸、添加入口、扫码打印、联网、指示灯操作、常见故障处理、驱动下载。
> 地址簿与账户见 `@//references/product-ops-setup.md`；寄件审批见 `@//references/product-ops-approval.md`；到件与国际件见 `@//references/product-ops-receipt-intl.md`。
> 配图为官方帮助中心的界面截图，均已使用 **HTTPS**，避免客户端因混合内容策略拦截。

## 1. 通用前置

**使用云打印机必须满足：** 打印机已连接 WiFi，且网络状态为**在线**，才能正常打印。绝大多数"打不出来"的问题根因都在这一步。

**「云打印管家」小程序：** 微信扫描打印机设备码进入，可用于打印设备码、调整打印浓度等操作。

**云打印机联网方法：** 见帮助中心《云打印机怎么联网》（`qusId=8106068467`）。

## 2. 指示灯与按键速查

| 操作 | 现象 | 效果 |
|---|---|---|
| 点按指示灯按键 | — | 走纸 |
| 按住 3 秒 | 指示灯闪 1 次 | 打印设备码（**需联网**） |
| 按住 5 秒 | 指示灯闪 2 次 | 校正纸张 |
| 关机后按住按键再开机，保持不松手 | **红灯**闪 3 次后松手 | **强制校正纸张**，自动走纸 2 张 |
| 关机后按住按键再开机，保持不松手 | **蓝灯**闪 3 次后松手 | **恢复出厂设置**，自动走纸 2 张 |

> ⚠️ **红灯与蓝灯极易混淆**：红灯 3 次 = 校正（不丢配置）；蓝灯 3 次 = 恢复出厂（会丢配置）。答复时必须把这两条并排说明，避免用户误重置。

## 3. 安装 / 更换打印纸

**流程：** 开盖 → 取出旧纸卷/纸轴 → 装入新纸卷 → 合盖 → **执行纸张校正**。

装纸后必须执行纸张校正——这是官方指引中的固定步骤（见 §6.3「卡纸或缺纸」处理）。

**演示视频：** https://player.youku.com/embed/XNTgyMjQ2NzY1Ng==

校正方式见 §2（长按 5 秒闪 2 次）或 §6.4（强制校正）。

## 4. 添加云打印机

两条路径对应**不同端**，不是版本差异：

### 4.1 员工端

**PC 端：** 基础设置 → 打印机设置 → 添加云打印机 → 绑定设备码

![员工端-基础设置-打印机设置](https://file.kuaidi100.com/downloadfile/-o3SSjHXdGtVu0Oz9IirQW_LwCIgzMVc_jau81lFvcgQStVQHv6NN79QKJE2TFwjkNYYL7f-3SM5kWH1C8pEeQ)

![添加云打印机-绑定设备码](https://file.kuaidi100.com/downloadfile/-o3SSjHXdGtVu0Oz9IirQW_LwCIgzMVc_jau81lFvcgQStVQHv6NN7l2xoSLAGl2yqEPJ4RdnwnJ7NruR9Q19w)

**手机端：** 个人中心 → 打印机 → 添加打印机 → 绑定设备码

![员工端手机-个人中心-打印机](https://file.kuaidi100.com/downloadfile/1Hfec2UZpuiV7CCVe5UgZXdFpqbwwY0ZAA4aS2b2TvXuRIr6O3nNh5QSzBmFJA85Sh_Ihfa4Zwg2wMhAj4fnsg)

### 4.2 前台（收发室）端

**PC 端：** 系统设置 → 打印机设置 → 添加云打印机 → 绑定设备码

![前台端-系统设置-打印机设置](https://file.kuaidi100.com/downloadfile/ifKIv_bigW82nToFUrzESVl1FLt5CLSSn4JQ8rr38TgTzNvaC_87DaLOcp5miG1Skm8v9a9GVQRi5Jwm-AWJmA)

![添加云打印机-绑定设备码](https://file.kuaidi100.com/downloadfile/Pb-RJUDhziz8_eptY87VpfesdFhJcU4_P3H3s2jmUS_S-LzDcO43ReUGTK-qrwj5jz7LgKiK1FKyafaW56KKJw)

**手机端：** 个人中心 → 打印机 → 添加打印机 → 绑定设备码

![前台端手机-个人中心-打印机](https://file.kuaidi100.com/downloadfile/Pb-RJUDhziz8_eptY87VpfesdFhJcU4_P3H3s2jmUS_S-LzDcO43ReuR70PNt8t2Bw-dClmeW4wqrrm_hDCMZg)

### 4.3 绑定设备码

查看打印机**底部或侧边**的二维码，在系统内操作绑定即可。

若二维码磨损或不便查看，可按指示灯按键 3 秒（闪 1 次）打印设备码，或用微信扫描设备码进入「云打印管家」小程序操作。**打印设备码需打印机联网。**

## 5. 扫码打印（员工免添加打印机）

管理员**下载打印机二维码**并张贴在打印机旁边，员工通过 OA 扫一扫即可直接打印，**员工自己无需添加打印机**。

![管理员下载打印机二维码](https://file.kuaidi100.com/downloadfile/Pb-RJUDhziz8_eptY87VpfesdFhJcU4_P3H3s2jmUS_S-LzDcO43RQ1GbgxxJzFGH7HChScnZqFINOA46AbllQ)

![员工 OA 扫一扫直接打印](https://file.kuaidi100.com/downloadfile/Pb-RJUDhziz8_eptY87VpfesdFhJcU4_P3H3s2jmUS_S-LzDcO43Rfy2U0D_rj0gs8WxJYPIAPN2OsMQio3jpQ)

**限制与注意**

- **网页端用户暂不支持此功能**（仅 OA 端可用扫一扫）。
- 企业有多个收发室时，员工打印需**扫描对应收发室的打印机二维码**，扫错会打到别的收发室。

## 6. 常见故障

### 6.1 云打印一单出多张纸

按顺序处理，**每一步无效再进入下一步**：

1. **再打一单**，确认是必现问题还是偶发问题。
2. **校正纸张**后再次打印（长按指示灯 5 秒闪 2 次，或用小程序校准）。

![纸张校正](https://file.kuaidi100.com/downloadfile/i85S53BfUgugHju-VqzWJWH293IQjX8la8YofD967E83UW6qIL2XRFSFxx4QN33n0k0O-s6L8KZ9oTthcgljHA)

3. **重置打印机**（关机后按住按键再开机，蓝灯闪 3 次后松手）。
4. 以上都无效，收集以下 5 项自检结果：
   - 是打印某一单有问题，还是所有订单都有问题
   - 是单一同事操作有问题，还是全部同事都有问题
   - 电脑端和手机端打印是否都有问题
   - 员工端和管理端打印是否都有问题
   - 公司其他打印机同一时间有没有反馈同样问题

**报障需提供：设备码 + 问题单号 + 上述自检结果**，一并反馈快递100 排查。

> 第 4 步的 5 项自检决定了是设备问题、账号问题还是服务端问题，缺项会拖长排查周期，务必收集齐。

### 6.2 指示灯蓝灯正常，但系统显示离线

1. **先打一单试试。** 若能正常打印，说明是**系统获取打印机状态滞后**，对实际打印功能没有影响，稍后会自行恢复。
2. 若不能正常打印，**重置打印机**（蓝灯闪 3 次后松手）。
3. 重置后仍不能打印，**断开打印机网络重新连接**。

> 顺序很重要：先验证能否打印，再谈离线。多数情况只是状态同步延迟，不必重置。

### 6.3 卡纸或缺纸

1. 卡纸或缺纸时，**开盖重新装纸并校正纸张**（小程序校准，或长按指示灯 5 秒闪 2 次）。

![小程序校准纸张流程：云打印管家 → 打印机设置 → 校准纸张](https://file.kuaidi100.com/downloadfile/0aXSJzYmN5cO50sw8m_FMYgY7pqJHShy4kDfXfOMNJcRMjzM8tp8IFzY4gyy-EM8iiQJYXieTGzWac8biKcKdA)

2. 打印头长期未清理也会导致卡纸。若出现卡纸或**印刷不完整**，用**酒精清理打印头和滚轮**；平时需定期清理。

### 6.4 强制校正纸张

1. 将打印机**电源关闭**。
2. **按住**指示灯按键，再**打开电源**，**期间不松手**。
3. 指示灯会进入不同闪烁状态，等待**红灯**闪烁 3 次后松手。
4. 打印机自动走纸 2 张，校正完成。

**演示视频：** https://player.youku.com/embed/XNTgyMTAwMDE4NA==

> 与 §2 的「长按 5 秒校正」是两种方式：日常校正用长按 5 秒；纸张规格变化或走纸异常时用强制校正。

### 6.5 恢复出厂设置

1. 将打印机**电源关闭**。
2. **按住**指示灯按键，再**打开电源**，**期间不松手**。
3. 指示灯会进入不同闪烁状态，等待**蓝灯**闪烁 3 次后松手。
4. 打印机自动走纸 2 张，重置完成。

**演示视频：** https://player.youku.com/embed/XNTgyMTAwMTgyOA==

> 恢复出厂会清除已配网与相关配置，重置后需重新联网。执行前先确认用户愿意重新配网。

### 6.6 调整打印浓度

微信扫描打印机设备码进入「云打印管家」小程序，在小程序内调整。

![云打印管家小程序-浓度调整](https://file.kuaidi100.com/downloadfile/u09vZdw14wHoyfbVkK9H6qjV1BQKBmsdluca9d7F8h1M5KK_urNBIdzr6GYFG2jr66908ouJgwICNNa-lClrmw)

### 6.7 打印设备码

两种方式：

- 微信扫描打印机设备码进入「云打印管家」小程序操作；
- 按住指示灯按键 3 秒（指示灯闪 1 次），**需打印机联网**。

![云打印管家小程序-打印设备码](https://file.kuaidi100.com/downloadfile/VZU_sgGbaO1yW5CTn68YEwJsSiKPCV4qZqfLsyMfCB0tfNy1xgdHL6iNrskaItPvXFJc1Pi-dHDAXpfDCSxJVw)

若设备码本身已磨损且打印机未联网，两种方式都不可用，需按设备机身信息联系厂商。

## 7. 热敏打印机驱动下载

| 品牌 | 下载地址 |
|---|---|
| 快递100 | https://www.kuaidi100.com/cloud/driver.shtml |
| Qrprt 启锐 | https://www.qrprt.com/ ⚠️ 原 `/download` 页已失效（404），需从官网「下载 / 服务支持」重新找入口 |
| Gainscha 佳博 | https://cn.gainscha.com/qudong.html |
| Hprt 汉印 | https://cn.hprt.com/XiaZai.html |
| Xprinter 芯烨 | https://www.xprinter.net/companyfile/6/ |
| KM 快麦 | https://dyj.kuaimai.com/qdxz/index.html#km_download |
| biaotop 标拓 | http://www.biaotop.cn/ ⚠️ 原下载页已失效（404）；该站 HTTPS 证书异常，只能用 HTTP 访问 |
| deli 得力 | https://www.nbdeli.com/services/download.html |
| 打印猿 | https://www.daprt.com/col.jsp?id=106 |
| chiteng 驰腾 | https://www.ctaiot.com/download |

> 启锐、标拓的原始下载页已失效，需从品牌官网重新查找入口；其余品牌链接可直接前往。

## 8. 未收录问题的处理

1. 先按「能否打印 → 是否在线 → 是否单台设备」三步定位，再对照本文档匹配。
2. 无法匹配时，请用户提供**设备码 + 问题单号 + 现象描述**，引导至快递100 客服，不猜测故障原因。
