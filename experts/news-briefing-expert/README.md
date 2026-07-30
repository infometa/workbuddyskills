# News Briefing Expert

你的私人新闻主编。AI、财经、科技、社会、国际全领域覆盖，多源交叉验证后整理成结构化简报，星级标重要度，每条留原文链接可溯源。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 全领域覆盖：AI、财经、科技、社会、国际，取数统一走 online-search（ProSearch），按领域配关键词与垂类参数
- 多源交叉验证：关键事实 ≥2 独立来源核实，单一来源标"待核实"，识别旧闻新用/深伪/谣言
- 信源权威分级：S/A/B/C/D 五级取信，不是什么链接都往简报里塞
- 结构化简报：🔥头条 + 📊分类表格 + ⭐星级重要度 + ✓/⚠️验证标记 + 溯源声明
- 条条可溯源：每条必留原文链接，摘要≠原文
- 客观中立：争议事件多方并列，不带立场

## 使用示例

- 做一份今日新闻简报，AI + 财经 + 国际各几条，带重要度
- 今天有什么值得关注的热点？
- 追踪一下「英伟达」最近一周的新闻进展

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/news-briefing-expert/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r news-briefing-expert.zip news-briefing-expert/
```
