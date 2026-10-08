---
title: "小程序 SDK FAQ"
code: "miniprogram_sdk_faq"
source: "Feishu MCP"
doc_id: "wikcnFKi1tU3gBHjbIqVy4M6GGe"
fetched_at: "2026-04-20T17:29:39Z"
---

# 集成 SDK
## SDK 集成方式说明
- 目前只支持本地集成暂不支持 NPM

## SDK 兼容性说明
- 支持平台：微信小程序、支付宝小程序、字节跳动小程序、百度小程序等

# 初始化 SDK
## 推荐 SDK 初始化位置
- 在小程序启动脚本中初始化，如微信小程序的 app.js

## 常见问题
### 延迟初始化会导致初始化后首次自动采集事件无法上报
### 设备无网络 SDK 初始化不会失败

# SDK 数据上报策略
## 实时上报
- 默认采集后立即上报，失败重试 3 次

## 定时批量上报
```javascript
var config = {
    appId: "APP_ID",
    serverUrl: "SERVER_URL",
    enableBatch: true,
    batchConfig: {
       size: 20,
       interval: 10000,
       storageLimit: 100
     }
};
TDAnalytics.init(config);
```

## 数据上报失败原因
- 需要将 serverUrl 配置为小程序访问域名白名单

# SDK 缓存机制
## 存储内容
- 访客 ID、设备 ID、事件数据等
- 调用小程序原生 setStorage 接口存储

## 缓存数量限制
- 默认最大缓存 200 条

# 访客 ID（#distinct_id）
## 默认格式
- 随机数-当前时间戳，如 2267955649-1679397798804

## 长度限制
- 最大长度 128 位

# Debug 模式
## debugMode 三种取值
- none：Normal 模式
- debug：数据在 TE Debug 模式中看到，参与分析
- debugOnly：只校验，不入库

# 自动采集事件
## ta_mp_launch
- 小程序冷启动初始化完成时触发
- 监听 onLaunch 回调

## ta_mp_view
- 小程序启动、后台回到前台、页面切换时触发
- 监听 Page onShow 事件

## ta_mp_share
- 点击小程序页面分享按钮后触发
- 需要配置 onShareAppMessage

## ta_mp_show
- 小程序启动、后台回到前台时触发
- 监听 onShow 事件

## ta_mp_hide
- 前台切换到后台时触发
- 监听 onHide 事件
- #duration 为 onShow 到 onHide 时差

# 公共事件属性
## 静态公共事件属性
```javascript
ta.setSuperProperties({ channel: "渠道名", user_name: "用户名" });
```

## 动态公共事件属性
```javascript
ta.setDynamicSuperProperties(function () {
    return { gold_coin: getGold() };
});
```

## 属性优先级
- 用户自定义 > 动态公共 > 静态公共

# 预置属性
## 设备 ID（#device_id）
- 默认和访客 ID 一致

## IP 地址（#ip）
- 服务端从请求头解析
- 可手动上报 #ip

# 已知问题
## 微信小程序
- login 方法报错 TypeError: e.trim is not a function，需要传字符串

## 淘宝小程序
- 3.3.4 Uncaught TypeError，需升级 SDK 到 3.5.1