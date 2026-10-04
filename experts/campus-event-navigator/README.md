# Campus Event Navigator

当前版本：1.1.0

“活动操盘手”是面向学生组织者的校园活动策划与执行顾问，支持从活动想法、策划、筹备和现场流程推进到数据复盘。

## 类型

Agent 型（单个 AI 专家）

## 首发场景

- 社团招新、宣讲和摊位活动
- 新生破冰、班级团建和见面会
- 迎新晚会、迎新节目和志愿服务
- 小型讲座、比赛、工作坊和经验分享会

## 核心能力

- 建立一页式活动 Brief 并比较活动方案
- 倒排里程碑、任务、人员、预算和物料
- 生成精简 RACI、RAID、岗位卡和候补方案
- 设计宣传节奏、报名文案和活动前提醒
- 生成分钟级 Run of Show、检查表和应急预案
- 开展活动就绪检查、数据统计和复盘交接

## 使用示例

- 帮我策划一场面向新生的社团招新活动
- 根据6个人的特长安排活动分工和时间表
- 帮我检查这份活动策划书的执行风险和遗漏

## 内置 Skill

`campus-event-playbook` 提供校园活动工作流、模板、安全边界和确定性指标计算脚本。

指标脚本要求 Python 3.10 及以上。示例：

```bash
python skills/campus-event-playbook/scripts/event_metrics.py --input event-data.json --pretty
```

脚本只统计输入数据，不代表校方审批、安全认证或最终举办决定。未提供 `readiness` 时返回 `not_evaluated`，不会把未评估误判为缺失或阻断。具体学校制度使用 `references/school-rule-verification.md` 记录官方来源、适用范围与待确认事项。

## 头像

头像位于 `avatars/expert.png`。如需替换：

- 格式：PNG 或 JPG
- 尺寸：512×512 px
- 大小：不超过 500KB

## 安装位置

将专家目录放到：

```text
$WORKBUDDY_CONFIG_DIR/plugins/marketplaces/my-experts/plugins/campus-event-navigator/
```

未设置 `WORKBUDDY_CONFIG_DIR` 时使用：

```text
~/.workbuddy/plugins/marketplaces/my-experts/plugins/campus-event-navigator/
```

完成后使用专家管理器的注册脚本注册。
