# 背书匠 · 原版阅读页（Skill 适配副本）

此目录是用户提供的 `aibg_recite_standalone` Vue/Vite 前端副本。原卡片、翻转、挖空虚线及点词显示代码与样式保留；本副本只增加 `material.js` 注入入口、TypeScript 分页数据适配器，以及导入文本/页码的少量连接代码。外部下载目录中的原文件未修改。Skill 日常生成页面使用旁边的 `recitation-original-dist` 预构建资源，无须安装依赖；只有修改此源码后才需运行 `npm ci && npm run build` 并同步更新预构建资源。

从背书匠 Web 项目中单独提取出来的**阅读/背诵页**,可以脱离原项目独立运行。

## 运行

```bash
npm install
npm run dev      # 开发预览(http://localhost:5188)
npm run build    # 产出生产构建到 dist/
```

无需后端、无需登录:所有接口由 `src/utils/api.js` 中的本地 mock 提供,内置一篇示例文档(《岳阳楼记》+ 数学公式笔记,含富文本、表格、公式、插图块)。

## 包含什么

```
src/
├── main.js                  # 入口
├── App.vue                  # 演示壳:提供 props、处理事件、fit() 视口缩放、未保存弹框
├── style.css                # 全局样式(与原项目一致)
├── views/RecitePage.vue     # ★ 阅读页本体(保留原交互；增加导入页数据的少量适配)
├── components/
│   ├── CzModal.vue          # 挖空设置弹框(AI / 规则 / 模板)—— 原样
│   ├── AiMask.vue           # AI 处理遮罩 —— 原样
│   ├── AppIcon.vue          # 图标组件 —— 原样
│   └── ToastMessage.vue     # Toast 提示 —— 原样
├── utils/api.js             # mock 接口层(替代后端,见下)
├── utils/recitation-material.ts # 确认后的分页原文/挖空偏移适配
└── assets/icons/            # AppIcon 用到的 SVG
```

## Mock 接口层

`src/utils/api.js` 导出 `bookApi` / `readConfigApi`,方法签名与返回结构(`{ code, msg, data }`)和真实后端保持一致:

| 方法 | 说明 | 本地实现 |
|------|------|----------|
| `getChapterList` | 章节目录 | 内置示例书籍 |
| `getDetail` | 章节内容块(TXT/TABLE/IMG) | 内置示例数据 |
| `saveBook` | 保存/新增 | 写回内存,刷新后还原 |
| `batchWordHollow` | AI 挖空 | 本地关键词提取(按密度) |
| `generateBlock` | AI 分块 | 本地按句切分(按 maxChars) |
| `aiGenerateBlockTitle` | AI 块标题 | 取块内容前几个字 |
| `uploadImg` / `objToUrl` | 图片上传/取 URL | dataURL 内存缓存 |
| `getConfigWordHollow` / `updateWordHollow` | 挖空配置 | 内存保存 |

数据保存在内存中,刷新页面即恢复初始示例数据。

## 接回真实后端

本 Skill 使用预构建静态页，不需要把浏览器直接接到鉴权后端。若以后恢复实时后端能力，应另行设计服务端代理和鉴权边界，不能把 Token 放入页面文件。

## 演示壳与原项目 App.vue 的差异

- 原项目 App.vue 里与阅读页无关的部分(登录、文档列表、侧边栏、分类/分享/反馈弹框、WebSocket)全部去掉,对应事件(`go-home`、`open-share` 等)在壳里以 toast 提示响应。
- 未保存弹框改用壳内简易实现(逻辑与原项目一致:调用 RecitePage 暴露的 `confirmSave()` / `cancelEdit()`)。
- 「+ 添加材料」会新建一个空材料并自动进入编辑模式,保存后由 mock 落地成新书籍。
