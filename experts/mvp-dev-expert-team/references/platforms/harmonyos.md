# 鸿蒙 HarmonyOS NEXT — 平台开发规范

## 开发框架
- **语言**：ArkTS（TypeScript 扩展）
- **UI 框架**：ArkUI 声明式
- **IDE**：DevEco Studio
- **API 版本**：API 12+（2026 年基准）

## 项目结构
```
entry/
├── src/main/
│   ├── ets/                   # ArkTS 源码
│   │   ├── entryability/      # Ability 入口
│   │   ├── pages/             # 页面
│   │   ├── components/        # 组件
│   │   ├── model/             # 数据模型
│   │   ├── utils/             # 工具
│   │   └── common/            # 公共资源
│   └── resources/             # 资源文件
│       ├── base/              # 默认资源
│       ├── zh/                # 中文
│       └── en/                # 英文
```

## 核心能力

### Stage 模型
- UIAbility：页面容器
- ExtensionAbility：后台服务
- UIAbility 生命周期：Create → WindowStage → Foreground → Background → Destroy

### 数据管理
- 首选项：`@ohos.data.preferences`（轻量 KV）
- 关系型数据库：`@ohos.data.relationalStore`
- 分布式数据：`@ohos.data.distributedDataObject`

### 网络请求
- HTTP：`@ohos.net.http`
- WebSocket：`@ohos.net.webSocket`
- 证书校验必须配置

### 推送
- Push Kit：`@ohos.push`
- 通知：`@ohos.notification`

## 设计规范

### 尺寸
- 设计稿基准：720vp
- 安全区域：`expandSafeArea` 属性
- 响应式断点：sm(320vp) / md(600vp) / lg(840vp)

### 组件
- 使用系统组件为主：Text / Button / List / Grid / Tabs
- 自定义组件 `@Component` + `@Builder`
- 状态管理：`@State` / `@Prop` / `@Link` / `@Provide` / `@Consume`

### 交互
- 手势：Tap / LongPress / Pan / Pinch / Rotation / Swipe
- 动画：`animateTo` / `animation` 属性动画
- 转场：`pageTransition` 页面转场

## 部署
- HAP 包签名 + 发布
- App Gallery Connect 上架
- 企业内部分发：`@ohos.bundle.innerBundleManager`
- 天工计划激励：2026年新应用上架奖励

## AI 能力集成
- DevEco 内置 AI 辅助编码
- MindSpore Lite 端侧推理
- 混元大模型 API 接入
