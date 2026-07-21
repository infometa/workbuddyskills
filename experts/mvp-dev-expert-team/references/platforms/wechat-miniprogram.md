# 微信小程序 — 平台开发规范

## 开发框架选型

| 框架 | 优势 | 适用场景 | 学习成本 |
|------|------|----------|----------|
| 原生 WXML | 性能最优，API 完整 | 复杂交互、性能要求高 | 中 |
| Taro 3 | 跨端（微信/支付宝/字节/H5） | 多端统一 | 低 |
| uni-app | 生态丰富，插件多 | 快速开发、简单业务 | 低 |
| Remax | React 语法，运行时方案 | React 技术栈团队 | 中 |

## 页面规范

### 导航栏
- 自定义导航栏需计算安全区高度：`statusBarHeight + 44px`
- 页面滚动时导航栏样式变化需节流处理
- 返回按钮默认存在，首页可配置 `navigationStyle: 'custom'`

### TabBar
- 数量：2-5 个
- 图标尺寸：81×81px（推荐）
- 文字最多 4 个汉字
- 使用 `wx.switchTab` 跳转

### 页面尺寸
- 设计稿基准：750rpx
- 安全区域：iPhone X+ 底部 34px
- 建议使用 `env(safe-area-inset-bottom)` 适配

## 核心能力接入

### 微信支付
```
1. 后端调用统一下单 API → 获取 prepay_id
2. 前端调用 wx.requestPayment → 弹出支付
3. 后端接收支付回调 → 更新订单状态
4. 前端轮询订单状态 → 确认支付结果
```

### 用户授权
- 手机号：`<button open-type="getPhoneNumber">` + 后端解密
- 用户信息：已废弃直接获取，需用户手动填写
- 地理位置：`wx.authorize({scope: 'scope.userLocation'})`

### 分享
- 页面分享：`onShareAppMessage` 返回标题/路径/图片
- 分享到朋友圈：`onShareTimeline`（仅 Android）
- 分享图片建议：5:4 比例，500×400px

### 订阅消息
- 一次性订阅：`wx.requestSubscribeMessage`
- 长期订阅：需微信认证 + 类目审核
- 模板 ID 最多 3 个/次

## 性能优化

### 包体积
- 主包 ≤ 2MB，总包 ≤ 20MB
- 分包加载：`subPackages` 配置
- 图片走 CDN，不放在包内
- 代码压缩 + Tree-shaking

### 渲染优化
- `setData` 数据量控制在 256KB 以内
- 列表使用 `wx:key` + 虚拟列表
- 避免频繁 `setData`，合并更新
- 图片懒加载：`lazy-load` 属性

### 体验指标
- 首屏渲染 < 1.5s
- 页面切换 < 300ms
- 帧率 ≥ 50fps
- 内存 < 300MB

## 审核要点
- 不能有引导关注公众号的弹窗
- 不能有诱导分享
- 虚拟支付（iOS）禁用
- 用户隐私合规（隐私弹窗 + 协议）
