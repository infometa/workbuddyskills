# Personal Fitness Coach

私人健身教练 —— 专业务实、安全第一，帮你制定可执行的训练计划、动作指导与饮食方案。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 训练计划制定（减脂/增肌/增力/体态矫正/维持健康）
- 动作指导（wger 动作库查询 + 中文讲解）
- 饮食营养建议（USDA 营养数据 + TDEE/宏量计算）
- 身体数据计算（BMI/TDEE/1RM/体脂率）
- 训练记录追踪

## 使用示例

- 嘿，我是你的私人健身教练，先聊聊你的情况吧？
- 我想减脂，帮我制定一份训练计划
- 增肌每天要吃多少蛋白质？

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/personal-fitness-coach/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r personal-fitness-coach.zip personal-fitness-coach/
```
