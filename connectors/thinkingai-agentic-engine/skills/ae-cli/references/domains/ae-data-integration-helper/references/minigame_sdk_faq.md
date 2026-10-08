---
title: "小游戏 SDK FAQ"
code: "minigame_sdk_faq"
source: "Feishu MCP"
doc_id: "wikcnvfJGsMHmKJIsEIhx0T2lyj"
fetched_at: "2026-04-20T17:29:39Z"
---

# 集成 SDK
## SDK 集成方式说明
- 目前只支持本地集成暂不支持 NPM

## SDK 兼容性说明
- 支持平台：微信小游戏、支付宝小游戏、字节跳动小游戏、百度小游戏等
- 支持引擎：CocosCreator、Egret 白鹭引擎、Laya 引擎

# 初始化 SDK
## 推荐 SDK 初始化位置
- 在小游戏的启动脚本中初始化，如微信小游戏的 game.js

## 常见问题
### 延迟初始化会导致自动采集事件时间延迟
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
       size: 5,
       interval: 5000,
       storageLimit: 200
     }
};
TDAnalytics.init(config);
```

## 数据上报失败原因
- 需要将 serverUrl 配置为小游戏访问域名白名单

# SDK 缓存机制
## 存储内容
- 访客 ID、设备 ID、事件数据等
- 调用小游戏原生 setStorage 接口存储

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

## 开启 Debug 模式看不到数据原因
- 确认模式正确打开
- 确认设备 ID 已在 TE 后台配置
- 确认 appId、serverUrl 正确

# 自动采集
## ta_mg_show
- 小游戏启动、后台回到前台时触发
- 监听 onShow 事件

## ta_mg_hide
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
## 淘宝小游戏
- 3.4.4 版本 Batch 模式循环发送问题

## OPPO 小游戏
- module is not defined 报错

## TikTok
- #scene 属性类型不合法