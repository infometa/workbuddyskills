---
title: "JavaScript SDK FAQ"
code: "javascript_sdk_faq"
source: "Feishu MCP"
doc_id: "FVlZw0Q3wig1svk13CEcGlQonHd"
fetched_at: "2026-04-20T17:29:40Z"
---

# 集成 & 初始化 SDK
## SDK 集成方式
### 自动集成（npm）
```shell
npm install thinkingdata-browser --save
```

### 手动集成
- 同步加载或异步加载

## SDK 兼容性说明
- 运行环境需为浏览器，暂不兼容 IE 8 及以下版本

# SDK 数据上报策略
## 网络请求方式参数（send_method）

| 方式 | 请求方式 | 介绍 |
|------|----------|------|
| image | get | 拼接数据在图片请求后面，跨域兼容 |
| ajax | post | 使用 XMLHttpRequest，可发送大量数据 |
| beacon | post | 浏览器后台发送，不阻塞页面卸载 |

## 立即上报
- normal 模式未开启批量上报时立即上报
- debug 或 debugOnly 模式立即上报
- 手动调用 flush() 接口

## 批量上报
```javascript
var config = {
    appId: 'APP_ID',
    serverUrl: 'SERVER_URL',
    send_method: 'ajax',
    batch: {
        size: 5,
        interval: 5000,
        maxLimit: 200
    }
};
```

# SDK 缓存机制
## 存储内容
- 访客 ID、设备 ID、事件数据等
- 使用 localStorage 存储

## 缓存数量限制
- 默认最大缓存 500 条

# 访客 ID（#distinct_id）
## 默认格式
- 时间戳16进制-随机数16进制-UA16进制-屏幕宽高处理-时间戳16进制

## 手动设置
```javascript
ta.identify("your_distinct_id");
```

## 长度限制
- 最大长度 128 位

# Debug 模式
## mode 三种取值
- normal：Normal 模式
- debug：数据在 TE Debug 模式中看到
- debug_only：只校验，不入库

# 自动采集
## ta_page_show
- 页面打开、刷新、标签切换回当前页时触发
- 监听 visibilitychange 事件，document.hidden = false

## ta_page_hide
- 页面关闭、标签切换、最小化时触发
- 监听 visibilitychange 事件，document.hidden = true

## ta_pageview
- 需调用 quick() 方法手动上报
- 与 ta_page_show 区别：ta_page_show 自动采集，ta_pageview 需手动调用

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

## 页面公共属性
```javascript
ta.setPageProperty({ page_id: "page10001" });
```

## 属性优先级
- 用户自定义 > 页面公共 > 动态公共 > 静态公共

# 预置属性
## 设备 ID（#device_id）
- 默认和访客 ID 一致

## IP 地址（#ip）
- 服务端从请求头解析
- 可手动上报 #ip

# 常见问题
## 报错 Cannot read properties of undefined (reading 'getOptTracking')
- SDK 接口在初始化前被调用，需在初始化后调用

## 报错 net::ERR_BLOCKED_BY_ORB
- 默认使用 image 模式上传，可设置 imgUseCrossorigin: true

## 如何在 pagehide 中上报数据
- 使用 trackWithBeacon 方法

# 已知问题
详见文档完整内容。