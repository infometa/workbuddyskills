# 产品操作 · 寄件审批配置

> 覆盖：飞书审批流配置、钉钉审批流配置、打开寄件审批开关报错。
> 端与菜单名：管理端=**系统设置**／增值服务；员工端=**基础设置**；前台（收发室）端=**系统设置**。答复必须指明端。
> 相关操作见 `@//references/product-ops-setup.md`（地址与账户）、`@//references/product-ops-receipt-intl.md`（到件与国际件）。
> 配图为官方帮助中心截图，已统一为 HTTPS。

## 1. 寄件审批

### 1.1 飞书审批设置指引

**入口：** 管理端 → 寄件管理 → 寄件审批设置

**两个前置条件（不满足会卡住）**

1. 设计审批流之前，需**飞书超级管理员**在飞书后台把操作人添加为**飞书审批管理员**。
2. **2022 年 11 月 25 日之前**添加应用的企业，需企业管理员到飞书后台**升级应用权限**，否则打开寄件审批开关会报错（见 §1.3）。

**配置步骤**

1. 开启寄件审批设置。开启之后在飞书审批中设置具体审批条件即可进行寄件审批。

![寄件审批设置开关](https://file.kuaidi100.com/downloadfile/z97KLLdiHh8LdQ35h3aXwgr_K11tvsG8O90zs8kTMM0Px1kX83NOlyQ1CwI6hm1Cj3whBMP-9nIYEsgUBW32Kg)

2. 在飞书【工作台】→【审批】页面右上角点【管理后台】，会在浏览器打开页面，**需在浏览器扫码登录后再操作**。

![飞书工作台-审批-管理后台入口](https://file.kuaidi100.com/downloadfile/z97KLLdiHh8LdQ35h3aXwgr_K11tvsG8O90zs8kTMM0Px1kX83NOl50_ZasyuUd4RuugWCdKYnExNDjC9rMM7w)

![浏览器扫码登录](https://file.kuaidi100.com/downloadfile/z97KLLdiHh8LdQ35h3aXwgr_K11tvsG8O90zs8kTMM0Px1kX83NOl35h8A4-v7VVzndQBI9iGhdv1xBGBVpRFQ)

3. 在审批后台最下方找到【其他服务商提供】→【快递100寄件审批】，点编辑图标进入。

![审批后台最下方：其他服务商提供](https://file.kuaidi100.com/downloadfile/l7fgv5n1mjzyD1sxzFVi7k2rpGsOUK_I_9uFUABbaoBbwORYnq3Nrpv8COCY59G7Z916nXxEvwFRBd445CwqiA)

4. 点【流程设计】设置审批流程。

![快递100寄件审批详情](https://file.kuaidi100.com/downloadfile/l7fgv5n1mjzyD1sxzFVi7k2rpGsOUK_I_9uFUABbaoBbwORYnq3NrkZ6IRTTcFhOM2un2n_NNGuY9FtF6I6W-g)

![流程设计画布](https://file.kuaidi100.com/downloadfile/l7fgv5n1mjzyD1sxzFVi7k2rpGsOUK_I_9uFUABbaoBbwORYnq3Nrh4-hlmVrGgg2vbecNrxOQ23p1A81UaT2w)

5. 设置完成后点【发布】。

![发布审批流程](https://file.kuaidi100.com/downloadfile/Icr0TOknZjp5fOAIIj02qZItnOh3nuId3P46nuu7eS4hjXhOOPupS4ef384-P0bWyuZhLMBX_B5mWc89JEJgMQ)

**⚠️ 关键配置陷阱**

设置条件分支为「快递公司」时，必须选择**【包含以下任意】**，**不要选「完全匹配」**。选完全匹配会导致员工批量导入多家快递公司订单时**无法正常触发审批**。

![条件分支：快递公司需选「包含以下任意」](https://file.kuaidi100.com/downloadfile/Icr0TOknZjp5fOAIIj02qZItnOh3nuId3P46nuu7eS4hjXhOOPupS9NKtoAxexlGaEesa0ph10M58k9Jqxu4Ug)

**审批流转**

员工下单成功后自动触发审批流 → 员工在寄件列表【待审核】页签查看 → 管理员审核通过 → 订单进入【待寄出】。

![寄件列表-待审核页签](https://file.kuaidi100.com/downloadfile/Icr0TOknZjp5fOAIIj02qZItnOh3nuId3P46nuu7eS4hjXhOOPupS5VZ1eJwFS5fDUY4Bc0aFBiRkKG_1h8KiA)

审批人会收到审批申请。

![审批人收到的审批申请](https://file.kuaidi100.com/downloadfile/Icr0TOknZjp5fOAIIj02qZItnOh3nuId3P46nuu7eS4hjXhOOPupSw7cW7jvWboXYdR5r1ok5gnspPp7e2tDLw)

### 1.2 钉钉审批设置指引

**入口：** 管理端 → 寄件管理 → 寄件审批设置

**前置条件**

设计审批流之前，需**钉钉超级管理员**在钉钉后台把操作人添加为**钉钉审批管理员**。

**配置步骤**

1. 开启寄件审批设置。开启之后在钉钉审批中设置具体审批条件即可进行寄件审批。

![寄件审批设置开关](https://file.kuaidi100.com/downloadfile/W7dh7NPIUBZzgCYYxb9YGSzUw0txPuhUSIMKPCmR1wV7Q54BRC3T5kkl74fv-LI1Mi2woX6RbfI4cK-2jU3Ezg)

2. 在钉钉【工作台】→【OA审批】页面右上角点设置图标进入审批管理后台。

![钉钉工作台-OA审批-设置入口](https://file.kuaidi100.com/downloadfile/W7dh7NPIUBZzgCYYxb9YGSzUw0txPuhUSIMKPCmR1wV7Q54BRC3T5nDQVQfqXEcjuvGitJzxzcLu5fkkkzBcpw)

![进入审批管理后台](https://file.kuaidi100.com/downloadfile/W7dh7NPIUBZzgCYYxb9YGSzUw0txPuhUSIMKPCmR1wV7Q54BRC3T5oLxvQDtnaKBZzsXufEB8ky3FAmUFDC56A)

3. 在【表单管理】最下方找到【其他】→【快递100寄件审批】，点【编辑】进入。

![表单管理最下方：其他-快递100寄件审批](https://file.kuaidi100.com/downloadfile/Z3mT7Z8mxiqe2qRbyenS8bjXdpvHkokMdV5PSqdHpMzeNZ0N5Uki5WfSYpf_hHPbblOfy5iXk3KfNbbZM1k4uQ)

4. 点【流程设计】设置审批流程。

![快递100寄件审批详情](https://file.kuaidi100.com/downloadfile/Z3mT7Z8mxiqe2qRbyenS8bjXdpvHkokMdV5PSqdHpMzeNZ0N5Uki5SLQ_rq-W1dBoU077w4K78vDlPjNab-JAQ)

![流程设计画布](https://file.kuaidi100.com/downloadfile/Z3mT7Z8mxiqe2qRbyenS8bjXdpvHkokMdV5PSqdHpMzeNZ0N5Uki5TrioBOzcm0xyn03B57biEdo2NGDdSs52g)

5. 设置完成后点【发布】。

![发布审批流程](https://file.kuaidi100.com/downloadfile/XAlDPJ139yyPWZf2LiUIrP-HqXcMSAm4UK1zuNMqR8c1j1YpNYnV2EzCApgZMnvL6J-9cPUkVAvmiN6cQWWQkg)

**⚠️ 关键配置陷阱**

与飞书相同：条件分支为「快递公司」时必须选**【包含任意】**，**不要选「完全等于」**，否则批量导入多家快递公司订单无法触发审批。

![条件分支：快递公司需选「包含任意」](https://file.kuaidi100.com/downloadfile/Z3mT7Z8mxiqe2qRbyenS8bjXdpvHkokMdV5PSqdHpMzeNZ0N5Uki5YC9TQuU1qJfHwfVc3KhJ7aeTjya7N_kqA)

**审批流转**

员工下单成功后自动触发审批流 → 寄件列表【待审核】→ 审核通过进入【待寄出】。

![寄件列表-待审核页签](https://file.kuaidi100.com/downloadfile/XAlDPJ139yyPWZf2LiUIrP-HqXcMSAm4UK1zuNMqR8c1j1YpNYnV2O1I57DCFcOTptdhq_ojXjmwg8gK7GGzNg)

审批人会收到审批申请的工作通知。

![审批人的工作通知](https://file.kuaidi100.com/downloadfile/XAlDPJ139yyPWZf2LiUIrP-HqXcMSAm4UK1zuNMqR8c1j1YpNYnV2MXUwqBHK2jaZsvVLq3NcJYZVJJp4CGr5w)

### 1.3 打开寄件审批开关报错

**原因：** 企业当前使用的版本为旧版本，需企业 OA 管理员到管理后台**升级快递100 应用权限**。

**处理：** 到对应 OA 管理后台升级应用权限。

**企业微信**

![企微管理后台-应用管理](https://file.kuaidi100.com/downloadfile/FXBfmkx1t6C_7QtxreOvB2kE4leZlyj5ysbNIgbH0h1TQd0XNcSav5nbHWAzIgz0UC1qgQuEkhTg5GR-Cn9J3A)

![企微应用详情](https://file.kuaidi100.com/downloadfile/FXBfmkx1t6C_7QtxreOvB2kE4leZlyj5ysbNIgbH0h1TQd0XNcSavzw_ncEJQ-KcoSZF_7vtUrzDaSq0gvW2UA)

![企微权限升级](https://file.kuaidi100.com/downloadfile/g2xBgqF2eC46su3qEbxts3nOLunILVE2ZlMUGCw01WF_-Icx9gm8I52Aj8ejrUnYRB0o4zjYiLWti-hsXKWOsQ)

![企微权限确认](https://file.kuaidi100.com/downloadfile/g2xBgqF2eC46su3qEbxts3nOLunILVE2ZlMUGCw01WF_-Icx9gm8I6VW5T2pECXmfg2U04OJBpBYLRaT8jVS7w)

**飞书**

![飞书管理后台-应用管理](https://file.kuaidi100.com/downloadfile/g2xBgqF2eC46su3qEbxts3nOLunILVE2ZlMUGCw01WF_-Icx9gm8I3iWNJ48hHbXBztFD5zCSLBfaveVvKZ6aw)

![飞书权限升级](https://file.kuaidi100.com/downloadfile/g2xBgqF2eC46su3qEbxts3nOLunILVE2ZlMUGCw01WF_-Icx9gm8Iz7l25emZXEledXvFBLvgWGRtgeKoSvU6A)

> 该问题与 §1.1 的前置条件 2 是同一根因。

---
