# 自定义模板使用指南

> 内置模板（考研 / 雅思托福 / 期末考 / GRE-GMAT / 教资公考 / CFA-PMP / 技能学习 / 主题阅读）覆盖大部分学习场景。
> 如果你的目标不在以上范围，可通过本指南创建自定义模板。

---

## 一、何时需要自定义？

| 情况 | 是否需要自定义 | 建议做法 |
|-----|--------------|---------|
| 目标是英语类考试（如 BEC / 三笔） | ❌ 不需要 | 用 `ielts-toefl` 衍生 |
| 目标是国内学历类考试（如自考） | ❌ 不需要 | 用 `kaoyan` 或 `teacher-civilservice` 衍生 |
| 目标是某项小众职业认证（如 AWS / GA） | ❌ 不需要 | 用 `cfa-pmp` 衍生 |
| 目标是非常具体的项目（如减肥 30 天 / 健身计划） | ✅ 需要 | 创建自定义模板 |
| 目标是混合型（如 备考 + 实习准备） | ✅ 需要 | 创建自定义模板 |
| 目标是创作类（如 30 天写完小说） | ✅ 需要 | 创建自定义模板 |

---

## 二、3 种自定义方式

### 方式 1：对话式定制（最简单，推荐）

直接在对话中说：

```
我想学 [你的目标]，请帮我做计划，我没找到合适的模板
```

AI 会自动：
1. 识别为自定义场景
2. 加载 `_custom-blank.json` 空白模板
3. 询问 3 个关键问题（验证方式 / 教材资源 / 复盘需求）
4. 动态推导阶段 + 每日任务
5. 询问是否保存为永久自定义模板

### 方式 2：基于现有模板衍生

如果你的目标和某个内置模板**部分相似**：

```
基于 [内置模板名] 模板，帮我改成 [你的目标]，重点调整 [差异点]
```

示例：

```
基于 ielts-toefl 模板，帮我改成 BEC 商务英语备考，
重点调整：增加商务场景词汇 + 商务写作模板，去掉学术写作
```

AI 会读取模板 → 复用结构 → 修改内容 → 保存为新模板。

### 方式 3：手动编辑 JSON（高级用户）

复制 `_custom-blank.json` 到 `custom/` 目录（在 study-planner skill 安装目录下执行）：

```bash
mkdir -p references/templates/custom
cp references/templates/_custom-blank.json \
   references/templates/custom/my-template.json
```

按以下规则填充：

```json
{
  "id": "my-template",                    // 必填，唯一 ID
  "name": "我的私人模板",                  // 必填
  "description": "...",
  "applicable_to": ["..."],               // 适用场景
  "default_duration_days": 30,
  "total_phases": 3,                      // 推荐 3 阶段
  "phase_templates": [
    {
      "phase": 1,
      "name": "阶段名称",
      "duration_ratio": 0.3,              // 时长占比，三阶段加起来 = 1.0
      "description": "本阶段核心目标",
      "weekly_pattern": [                 // 每周日历模板
        {
          "day": "Mon",
          "tasks": ["任务1", "任务2", "任务3"]
        }
      ]
    }
  ],
  "methodology_injection": {              // 注入哪些方法论
    "ebbinghaus": true,
    "pomodoro": true,
    "pareto": false,
    "feynman": true
  },
  "special_notes": ["...", "..."]          // 关键提醒
}
```

---

## 三、自定义模板的存放位置

```
study-planner/references/templates/
├── kaoyan.json                          # 内置（不要修改）
├── ielts-toefl.json                     # 内置
├── ...
├── _custom-blank.json                   # 内置空白模板（不要修改）
└── custom/                              # 👈 自定义模板放这里
    ├── bec.json                         # 你的自定义
    ├── novel-writing-30days.json        # 你的自定义
    └── fitness-plan.json                # 你的自定义
```

> 自定义模板**优先级高于内置模板**，但 `id` 不能重名。

---

## 四、好的自定义模板长什么样？

### 反例（太空洞）

```json
{
  "phase_templates": [
    {
      "phase": 1,
      "weekly_pattern": [
        { "day": "Mon", "tasks": ["学习"] }
      ]
    }
  ]
}
```

❌ 任务过于笼统，AI 没法基于此生成具体每日计划。

### 正例（足够具体）

```json
{
  "phase_templates": [
    {
      "phase": 1,
      "name": "基础肌肉建立",
      "weekly_pattern": [
        {
          "day": "Mon",
          "tasks": [
            "胸+三头：卧推 4×10 / 哑铃飞鸟 3×12 / 绳索下压 3×15",
            "有氧 20 分钟",
            "拉伸 10 分钟"
          ]
        }
      ]
    }
  ]
}
```

✅ 具体到动作 / 组数 / 强度，AI 可以直接生成。

---

## 五、自定义模板分享

如果你的自定义模板特别好用，欢迎：

1. 分享到 KM / 公司内部知识库
2. 提交到 study-planner 的 GitHub 仓库（PR 到 `templates/community/`）
3. 通过 `skill-creator` 打包成独立的 Skill 发布

> 优秀的自定义模板会被纳入下一版内置模板。

---

## 六、常见问题

**Q: 我可以创建多少个自定义模板？**
A: 没有数量限制，但建议 ≤ 20 个，否则 AI 匹配模板时会增加噪音。

**Q: 自定义模板会被升级覆盖吗？**
A: 不会。`custom/` 目录下的文件不在 Skill 升级范围内。

**Q: 我能让 AI 智能选择模板吗？**
A: 可以。AI 会按以下顺序匹配：
   1. `custom/` 中你的自定义模板
   2. `templates/` 中内置模板
   3. `_custom-blank.json` 兜底动态生成
