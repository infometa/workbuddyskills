# 鹅厂职业经纪人（career-broker v0.2.0）

腾讯员工的职业发展顾问。帮你梳理经历与特质、澄清去留和转型方向，并对接课程、经验文章、内部案例和真实活水机会。

---

## 功能清单（一图看全）

```
┌─ 🪞 职业画像（PP）─────────────────────────────────┐
│  · 拉自评历史（近 3 期完整 + 更早期 LLM 汇总）       │
│  · 拉 TAPD 工作记录 + 工蜂代码语言（可选）           │
│  · 三轴提炼：技能 / 经历 / 软性素质                  │
│  · 输出 profile.json + profile_compact.json          │
└────────────────────────────────────────────────────┘

┌─ 💬 职业发展问答（QA · 内部双路由）────────────────┐
│  · 敏感词前置过滤（人员统计/薪酬/他人隐私等 8 类）   │
│  · 活水/职业发展规则：走活水知识库                  │
│  · 学习成长与职业资源问题：走学堂小Q                │
│  · 内部路由不暴露给用户，直接给经纪人口吻答案        │
└────────────────────────────────────────────────────┘

┌─ 🧬 测评解读（AC）─────────────────────────────────┐
│  · 基于职业 DNA 结果码解读 8 锚 / 6 维 / 心理状态     │
│  · 只解读用户真实贴回的结果码，不编测评、不拼链接     │
│  · 方向倾向只到画像层，具体资源交给 CC / LJ           │
└────────────────────────────────────────────────────┘

┌─ 🧭 职业发展咨询（CC）─────────────────────────────┐
│  · 4 段式对话：建连接 → 找真问题 → 拉选项 → 落小行动 │
│  · 用户主动要时才给方向 / 案例 / 课程 / 行动计划      │
│  · 课程资源必须来自真实 QLearning 返回               │
│  · 收尾只给 1 个诊断 + 1 个下一步                    │
└────────────────────────────────────────────────────┘

┌─ 🧰 司内资源获取──────────────────────────────────┐
│  · QLearning：真实课程资源                          │
│  · km：经验文章 / 实战复盘                           │
│  · case library：内部案例参考                        │
│  · recruit-mcp：活水问询知识库 + 真实在招活水机会     │
│  · 没有真实数据源时不给假课名、假文章、假岗位         │
└────────────────────────────────────────────────────┘
```

---

## 用户原话路由示例

| 用户说什么 | 经纪人怎么处理 |
|---|---|
| “帮我做画像 / 看看我自己” | 构建职业画像 |
| “活水有试用期吗” | 查活水规则并直接回答 |
| “卡住了 / 给点职业建议 / 想做测评” | 进入职业发展咨询或测评解读 |
| “去留两难 / 想换赛道 / 不知道下一步” | 陪你澄清目标和选择约束 |
| “帮我找课程 / 经验文章 / 类似案例” | 获取司内学习与经验资源 |
| “看看有什么岗 / 推荐活水机会” | 获取真实在招活水机会 |

---

## 安装（两步起步）

1. 装本插件 → `skills/career-broker-core/references/setup/02-career-broker-install.md`
2. 装自评 MCP → `skills/career-broker-core/references/setup/01-self-assess-plugin.md`

> **省事路径**：如果你打算把课程、活水机会、经验文章这些司内资源都用上，推荐先看 `skills/career-broker-core/references/setup/00-mcp-bundle.md`。QLearning / recruit-mcp / km 共用一份太湖 PAT，先检测复用，别重复申请。

剩下的依赖按需引导——agent 用到时主动提示，不用一次装齐：

| 依赖 | 何时需要 | 教程 |
|---|---|---|
| TAPD（司内版） | 画像构建用到时 | `skills/career-broker-core/references/setup/03-tapd-connector.md` |
| Gongfeng | 画像构建用到时（产品/HR 岗可跳过） | `skills/career-broker-core/references/setup/04-gongfeng-connector.md` |
| QLearning | 课程资源 + 学堂问答 | `skills/career-broker-core/references/setup/05-qlearning-mcp.md` |
| recruit-mcp | 活水问询 + 画像 basic + 活水机会推荐 | `skills/career-broker-core/references/setup/06-recruit-mcp.md` |
| km | 经验文章 / 实战复盘 | `skills/career-broker-core/references/setup/07-km-mcp.md` |

---

## 目录结构

```
career-broker/
├── .workbuddy-plugin/
│   └── plugin.json                        插件清单（必须）
├── avatars/
│   └── expert.png                         专家头像
├── agents/
│   └── career-broker.md                   主入口 agent
├── skills/
│   ├── career-broker-core/                共享规范、安装教程、公共脚本
│   ├── profile-perception/                职业画像（PP · 先认识你）
│   ├── career-qa/                         职业问答（QA · 答你关心的事）
│   ├── ai-career-agent/                   测评解读（AC · 看见冰山下）
│   ├── career-development-consultant/     职业发展咨询（CC · 陪你想清楚）
│   └── liveflow-job-recommender/          活水机会推荐（LJ · 真实在招机会）
└── README.md                              说明文档
```

---

## 数据存储

所有用户数据落本地：`~/.workbuddy/career-broker/<rtx>/`

```
profile.json                完整画像
profile_compact.json        缩略版（给下游 skill 消费）
profile_summary.md          可读摘要
job_recommendations/        活水机会推荐历史
prefs/<rtx>-prefs.json      用户偏好（活水意向）
history/                    画像版本归档
memory.md                   长期职业记忆
```

---

## 隐私

- **P0 仅本地**：自评原文 / TAPD 详情 / 简历附件 / 测评 DNA → 永不上云
- **P1 脱敏共享**：LLM 提炼后的 skill_tags / domain_tags / trait_tags → 可上 WorkBuddy 云作专家记忆
- **P2 公开**：推荐过的岗位 / 偏好（用户授权后）→ 首版只本地

---

## 主要触发关键词

```
职业经纪人 / 职业发展 / 我适合什么 / 我想活水 /
帮我看看自己 / 我做过什么 / 卡住了 / 给点建议 /
司内资源 / 课程资源 / 经验文章 / 内部案例 / 活水机会 /
做个测评 / 看看我自己
```
