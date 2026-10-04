---
title: "Cocos Creator SDK FAQ"
code: "cocoscreator_sdk_faq"
source: "Feishu MCP"
doc_id: "IeC9wKCp7i2edwkVQ9Oc3YrJnYf"
fetched_at: "2026-04-20T17:29:40Z"
---

> CocosCreator SDK 支持多平台，本文主要介绍除 Android/iOS 外其他平台的常见问题。

# 初始化 SDK
## 推荐 SDK 初始化位置
- 建议在用户同意隐私协议后再进行 SDK 初始化

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
       size: 20,
       interval: 10000,
       storageLimit: 100
     }
};
TDAnalytics.init(config);
```

# SDK 缓存机制
## 存储位置
- 小游戏：调用 setStorage 接口存储在 Storage 中
- Web/H5：使用 localStorage 存储

## 缓存数量限制
- 默认最大缓存 200 条

# 访客 ID（#distinct_id）
## 默认格式
- 随机数-当前时间戳

## 长度限制
- 最大长度 128 位

# Debug 模式
## debugMode 三种取值
- none：Normal 模式
- debug：数据在 TE Debug 模式中看到
- debugOnly：只校验，不入库

# 自动采集事件
## ta_mg_show（小游戏）
- 小游戏启动、后台回到前台时触发

## ta_page_show（Web/H5）
- 页面打开、刷新、标签切换时触发
- 监听 visibilitychange 事件

## ta_mg_hide（小游戏）
- 前台切换到后台时触发
- #duration 为时差

## ta_page_hide（Web/H5）
- 标签页关闭、刷新、切换时触发
- #duration 为时差

# 公共事件属性
## 静态公共事件属性
```javascript
TDAnalytics.setSuperProperties({ channel: "渠道名" });
```

## 动态公共事件属性
```javascript
TDAnalytics.setDynamicSuperProperties(function() {
    return { date: new Date() };
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

# 其他
## 设置时区
```javascript
var config = {
    appId: "APP_ID",
    serverUrl: "SERVER_URL",
    zoneOffset: 6
};
```

## 暂停数据上报
- setTrackStatus 方法传 PAUSE、STOP、SAVE_ONLY、NORMAL

# 常见问题
## 报错 Uncaught ReferenceError: module is not defined
- 删除 thinkingdata.mg.cocoscreator.min.js 中的 module.exports

## 打包 Android/iOS 有 ta_page_show 但没有 ta_page_hide
- 需要开启原生支持才能使自动采集生效

## 报错 TDAnalytics is not defined
- 取消 SDK 脚本的"插件"选项勾选

# 已知问题
详见文档完整内容。