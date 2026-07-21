# MVP开发专家团

一句话变产品。7人全栈AI专家团队——用户描述想法、确认一次三文档，其余全自动完成。

## ⛔ P0 绝对规则

本专家团强制执行三条绝对规则，所有产出必须通过：

1. **禁止 emoji 作为功能图标** → 唯一图标库 **Lucide**（lucide-react / lucide-vue-next / 内联 SVG）
2. **禁止紫色→粉色渐变主视觉** → 纯色 + 品牌色光晕替代
3. **禁止 AI 模板味** → 真实文案 + Design Token + 手工级细节

每个 Phase 的门禁都会检测这三条规则，违反即退回重做。

## 🎨 设计系统

对齐行业设计系统标准：
- **四层 Token 体系**：A1-identity → A2 → B-slot → C-extension
- **9 节 DESIGN.md 输出格式**：Visual Theme → Color → Typography → Components → Layout → Depth → Do's & Don'ts → Responsive → Agent Guide
- **Craft 工艺规范**：排版精规、色彩精规、动效精规、反 AI 套路检查
- **每屏 ≤2 处强调色**、**ALL CAPS ≥0.06em 字距**、**150ms 动效收敛值**

## 类型

Team 型（多角色协作团队），由项目总监统筹 7 位领域专家。

## 团队成员

- 大湾区靓仔（项目总监）— 统筹协调
- 许清楚（产品经理）— 需求分析、竞品调研
- 颜好看（UI/UX设计师）— UI/UX 设计，反AI模板质量把控
- 高见远（首席架构师）— 技术选型、系统架构
- 贾思敏（前端工程师）— 前端开发 + 自检修复
- 贝洛奇（后端工程师）— 后端API + 数据库
- 严过关（测试工程师）— 分层测试、质量门禁
- 卜宕机（运维工程师）— 自动部署、交付整合

## 工作流程

需求澄清 → 并行调研（三文档）→ 用户确认三文档 → Spec 自动锁定 → 设计 → 并行开发+自检 → 测试 → 部署交付。确认后自动推进，仅遇技术不可行或严重缺陷时通知用户。

## 使用示例

- "我想从零做一个团队协作工具"
- "帮我开发一个电商小程序"
- "我有个产品想法，帮我做成MVP"

## 环境变量

### 专家包运行所需（无需额外配置）

专家包本身不依赖任何环境变量，安装后即可使用。

### 生成项目可能使用的环境变量模板

专家团生成的 MVP 项目可能包含以下环境变量，具体取决于项目类型和技术选型。这些是**项目运行时配置**，不是专家包自身的依赖：

**认证与安全**
- `JWT_SECRET` — JWT 签名密钥（运行 `openssl rand -hex 32` 生成）
- `WX_SECRET` — 微信小程序密钥（微信生态项目）
- `SESSION_SECRET` — 会话加密密钥

**数据库与存储**
- `DATABASE_URL` — 数据库连接字符串（PostgreSQL/MySQL）
- `COS_SECRET_ID` / `COS_SECRET_KEY` — 腾讯云 COS 对象存储密钥
- `REDIS_URL` — Redis 连接字符串（缓存/队列场景）

**第三方服务**
- `RESEND_API_KEY` — Resend 邮件服务 API Key
- `STRIPE_SECRET_KEY` — Stripe 支付密钥（海外支付场景）
- `TRTC_APP_ID` / `TRTC_SECRET_KEY` — 腾讯实时音视频密钥（直播场景）

> 以上环境变量由生成的项目按需使用，专家团会在部署阶段（Phase 4）根据实际技术栈提示用户配置对应变量。

## 安装

1. 下载专家包
2. 解压到 ~/.codebuddy/plugins/marketplaces/my-experts/plugins/mvp-dev-expert-team/
3. 重启 WorkBuddy，在专家列表中即可看到"MVP开发专家团"
4. 点击开始对话，输入你的产品想法即可启动
