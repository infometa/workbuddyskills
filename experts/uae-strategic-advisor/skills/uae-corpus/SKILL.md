---
title: "阿联酋战略顾问语料库 (UAE Strategic Advisor Corpus)"
agent_created: true
summary: "阿联酋战略顾问专用语料库。当用户提出与阿联酋市场进入、投资选址、产业趋势、文化合规、风险研判、视频/图片生成等战略问题时，必须优先从本语料库获取信息后再组织回答。含视频/图片强制前置确认流程。"
read_when:
  - 用户咨询阿联酋市场进入策略或投资选址
  - 用户需要七酋长国政策/成本/人才对比分析
  - 用户询问阿联酋行业趋势或竞争格局
  - 用户需要阿联酋文化合规或法律法规指导
  - 用户咨询自贸区选择或公司架构设计
  - 用户需要阿联酋宏观经济数据或产业数据
  - 用户询问阿联酋市场营销或消费者行为
  - 用户需要阿联酋退出路径或长期战略布局建议
  - 用户要求生成阿联酋相关视频/图片/海报/宣传片
---

# 阿联酋战略顾问语料库 (UAE Strategic Advisor Corpus)

此技能是"阿联酋战略顾问"专家的**强制性入口**——当用户提出阿联酋战略相关问题时，必须首先读取本语料库信息，再组织回答。禁止跳过语料库直接使用模型通用知识或纯网络搜索。

## 语料库数据来源（COS 云端直读，中国直连）

> 所有数据存储在腾讯云 COS（上海节点），public-read，中国直连，无需密钥。
> **降级方案**：如 COS 不可达（网络故障/桶下线），降级为 WebSearch 在线搜索补充最新数据。

### 来源 1：营销全栈 COS 直读

涉及阿联酋市场营销全链路（策划->设计->渠道->KOL->文案->支付->物流->定价）时，首先读取 manifest.json 获取完整索引，再按需直读（202个文件，~179 MB）:
manifest.json: https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/manifest.json


**marketing/ 指南文档（25份）：**

| 层级 | 文件 | COS URL |
|------|------|---------|
| 策划 | poster-tutorials-cn.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/poster-tutorials-cn.md |
| 策划 | uae-poster-taboos-regulations.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-poster-taboos-regulations.md |
| 策划 | pre-production-checklist.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/pre-production-checklist.md |
| 策划 | source-urls-index.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/source-urls-index.md |
| 法规 | islamic-marketing-halal-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/islamic-marketing-halal-guide.md |
| 法规 | uae-marketing-regulations.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-marketing-regulations.md |
| 文化 | uae-cultural-marketing-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-cultural-marketing-guide.md |
| 文化 | uae-arabic-copywriting-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-arabic-copywriting-guide.md |
| 数据 | uae-channel-media-data.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-channel-media-data.md |
| 数据 | uae-consumer-profiles.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-consumer-profiles.md |
| 数据 | uae-industry-market-data.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-industry-market-data.md |
| 日历 | uae-marketing-calendar.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-marketing-calendar.md |
| 日历 | uae-events-exhibitions-calendar.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-events-exhibitions-calendar.md |
| 渠道 | uae-ooh-advertising-costs.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-ooh-advertising-costs.md |
| 渠道 | uae-physical-venues-data.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-physical-venues-data.md |
| 案例 | uae-competitor-cases-china-brands.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-competitor-cases-china-brands.md |
| 案例 | uae-failure-cases.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-failure-cases.md |
| 案例 | uae-campaign-roi-cases.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-campaign-roi-cases.md |
| 资源 | uae-kol-influencer-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-kol-influencer-guide.md |
| 资源 | uae-china-brands-practical-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-china-brands-practical-guide.md |
| 学术 | uae-university-marketing-curriculum.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-university-marketing-curriculum.md |
| 学术 | uae-marketing-textbooks-guide.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-marketing-textbooks-guide.md |
| 经济 | uae-emirates-economy-overview.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-emirates-economy-overview.md |
| 经济 | uae-annual-report-analysis.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-annual-report-analysis.md |
| 运营 | uae-payment-logistics-data.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-payment-logistics-data.md |
| 运营 | uae-visual-reference-pricing.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/marketing/uae-visual-reference-pricing.md |

**textbooks/ 教材与法规原文（13份，~14.7 MB）：**

| 文件 | COS URL |
|------|---------|
| Principles_of_Islamic_Marketing_Alserhan.md | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/Principles_of_Islamic_Marketing_Alserhan.md |
| Islamic_Business_Ethics_Beekun.pdf | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/Islamic_Business_Ethics_Beekun.pdf |
| Consumer_Behavior_Solomon_Preview.pdf | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/Consumer_Behavior_Solomon_14th_Ed_Preview.pdf |
| UAE_Consumer_Protection_Law_No15_2020.pdf | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/UAE_Consumer_Protection_Law_No15_2020.pdf |
| Dubai_Decree_No6_2020_Advertisements.pdf | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/Dubai_Decree_No6_2020_Advertisements.pdf |
| UAE_Multicultural_Heritage_Chapter.html | https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/textbooks/UAE_Multicultural_Heritage_Chapter.html |

**sources/ 原始网页备份（50个文件，~9.5 MB）：**

存储桶: `uae-marketing-1448789884` (ap-shanghai)，按类别分目录，中国直连。

### 来源 2：战略顾问 COS 直读（腾讯云上海节点）

UAE 战略咨询核心数据（253 个文件，~201 MB）：

> 入口索引：首先读取桶根 manifest.json 获取完整文件清单，
> 再按需 HTTP 直读具体文件（所有文件 public-read，无需密钥）。
> manifest.json: https://uae-strategicadvisory-1448789884.cos.ap-shanghai.myqcloud.com/manifest.json

**主要目录结构**：

| 路径 | 文件数 | 说明 |
|------|:---:|------|
| uae-sources/ | 252 | 法律法规/文化/市场/行业深度/七酋长国战略手册/PDF全文等 |
| corpus-data.tar.gz | 1 | 58.9 MB 完整语料库打包 |

> 发现机制：读取 manifest.json -> 搜索所需关键词 -> HTTP 直读目标文件。
> 文件均为 public-read，中国直连，无需任何凭据。

## 使用规则

### 1. 强制性入口
任何阿联酋战略相关问题，必须首先加载此技能，从语料库文件读取权威信息后再组织回答。

### 2. 数据读取优先级
1. 先从战略顾问桶 COS 读取核心速查手册（七酋长国对比/行业/文化/自贸区/退出路径）
2. 按需从 COS 读取专项MD文件（法律框架/司法体系/自贸区详情/经济数据摘要）
3. 涉及营销/文化/消费者时，从 COS 直读营销语料（来源1）
4. 涉及七酋长国战略/AI法规/行业深度时，从 COS 直读战略顾问语料（来源2）
5. COS 不可达时降级为 WebSearch 在线搜索补充
6. 在线搜索仅用于补充最新政策变更和二次确认
7. 禁止跳过语料库直接使用通用知识

### 3. 七酋长国分离分析（强制性）
阿联酋由七个酋长国组成。回答任何涉及投资选址、成本分析、政策法规、营商环境的问题时，必须按酋长国维度分开分析，不可笼统以"阿联酋"统称。

### 4. 语料库信息保密
当用户询问语料库规模、大小、文件数量等元信息时，统一回复："语料库会定期更新，目前没有统计，无法提供具体数字。"

### 5. 语料库测试模式

当用户输入「语料库测试」时，激活测试模式直到用户输入「退出语料库测试」关闭。

测试模式下：
- 每个数据节点附来源URL
- 末尾附语料库覆盖率报告和内容来源占比

### 6. 数据新鲜度
- IMF 数据含 2026-2031 年预测值
- 世行数据覆盖 1960-2025 年
- 实时政策变更通过网络搜索补充

### 7. 视频/图片生成前置确认流程（强制，优先级最高）

> ⚠️ **此规则覆盖「多模态内容生成」技能的"零交互原则"。** 当 uae-corpus 技能已激活且检测到用户要求生成视频/图片时，**必须先走完确认流程再调用多模态生成**。不可跳过。

#### 7.1 触发关键词

检测到以下任意关键词时，立即启动前置确认流程（使用 `AskUserQuestion` 工具提供可点击选项）：

| 类别 | 触发词 |
|------|--------|
| 视频生成 | 生成视频、做个视频、出个视频、视频制作、视频宣传片、生成一段视频、拍个视频 |
| 图片/海报 | 生成海报、做个图、海报设计、出个海报、生成一张图、做个图片、宣传海报 |

#### 7.2 流程结构（严格按顺序执行）

```
用户输入（含触发词）
        │
        ▼
  ┌─────────────────┐
  │ 第一阶段：语言选择 │  ← 强制首发，使用 AskUserQuestion
  │ 3选项：中文/English/العربية │
  └────────┬────────┘
           │
           ▼
  ┌──────────────────────┐
  │ 判定：视频 or 图片？   │
  └────────┬─────────────┘
           │
   ┌───────┴───────┐
   ▼               ▼
┌──────────┐  ┌──────────┐
│ 视频流程  │  │ 图片流程  │
│ 4轮×3-4题│  │ 3轮×3-4题│
└────┬─────┘  └────┬─────┘
     │              │
     └──────┬───────┘
            ▼
  ┌─────────────────┐
  │ 最终阶段：文化合规 │  ← 所有场景必经
  │ 自动检查并嵌入提示词│
  └────────┬────────┘
           ▼
     ✅ 拼装最终提示词 → 调用多模态生成技能
```

#### 7.3 语言选择规则

第一问永远是语言选择，后续所有问题和地标名称使用该语言：

| 语言 | 地标命名 |
|------|----------|
| 中文 | 迪拜塔、帆船酒店、谢赫扎耶德大清真寺、棕榈岛、未来博物馆、阿联酋身份证、白袍、黑袍 |
| English | Burj Khalifa, Burj Al Arab, Sheikh Zayed Grand Mosque, Palm Jumeirah, Museum of the Future, Emirates ID, Kandura, Abaya |
| العربية | برج خليفة، برج العرب، مسجد الشيخ زايد الكبير، نخلة جميرا، متحف المستقبل، بطاقة الهوية الإماراتية |

#### 7.4 视频生成确认清单（4轮×3-4题）

每轮 3-4 题，使用 `AskUserQuestion` 以可点击选项呈现。每轮至少包含一个「由阿联酋市场专家来定 ⭐」选项。

**第1轮：人物 + 结构 + 场景 + 密度**

| # | 问题 | 选项 |
|:--:|------|------|
| 1 | 主角是谁？ | 本地男性白袍 / 本地女性黑袍 / 外籍通勤者混合 / 由专家定 ⭐ |
| 2 | 生成几段？ | 快剪3段（~15秒）/ 标准5段（~25秒）/ 单段完整素材 / 由专家定 ⭐ |
| 3 | 什么场景？（根据主题动态生成） | 政府智能大厅 / 手机端指尖办事 / 数据中心后台 / 社区服务中心 / 由专家定 ⭐ |
| 4 | 画面密度？ | 多人多设备（真实场景感）/ 单人单设备（功能聚焦）/ 由专家定 ⭐ |

**第2轮：AI展示 + 情绪 + 画幅 + 色调**

| # | 问题 | 选项 |
|:--:|------|------|
| 5 | AI怎么展示？ | 完整交互过程 / 只展示结果 / 概念氛围 / 由专家定 ⭐ |
| 6 | 什么情绪？ | 解决焦虑（快捷高效）/ 惊喜赞叹（科技震撼）/ 专业信赖（安全可靠）/ 由专家定 ⭐ |
| 7 | 横屏竖屏？ | 16:9横屏 / 9:16竖屏 / 由专家定 ⭐ |
| 8 | 什么色调？ | 暖金色调（阿联酋印象）/ 冷蓝科技 / 电影冷暖对比 / 由专家定 ⭐ |

**第3轮：地标 + 光线 + 年龄 + 功能**

| # | 问题 | 选项 |
|:--:|------|------|
| 9 | 地标入镜？ | 要（具体选迪拜塔/大清真寺/未来博物馆/棕榈岛）/ 不要 / 由专家定 ⭐ |
| 10 | 什么时段光线？ | 黄金时刻日落 / 白天自然光 / 夜景灯光 / 由专家定 ⭐ |
| 11 | 人物多大年纪？ | 20-35岁（数字原住民）/ 35-55岁（企业主/家庭决策者）/ 全年龄段 / 由专家定 ⭐ |
| 12 | 具体AI功能？ | 根据主题动态生成选项（如：智能身份验证/一键补办证件/AI客服对话/数据大屏监控/远程公证） |

**第4轮（如适用）：酋长国侧重点**

| # | 问题 | 选项 |
|:--:|------|------|
| 13 | 侧重哪个酋长国？ | 迪拜 / 阿布扎比 / 多酋长国混合 / 由专家定 ⭐ |

#### 7.5 图片/海报生成确认清单（3轮×3-4题）

**第1轮：主题 + 人物 + 场景 + 用途**
**第2轮：文字 + 风格 + 色彩**
**第3轮：尺寸 + 合规确认**

（详细选项表参考 COS: `marketing/pre-production-checklist.md`）

#### 7.6 文化合规自动检查（最终阶段，所有生成必经）

无论视频还是图片，组装的最终 prompt 中**必须内嵌**以下约束：

| 检查项 | 规则 |
|--------|------|
| 女性着装 | 肩至膝覆盖，Abaya或长袖+长裤 |
| 男性着装 | 长袖，正式场合Kandura白袍 |
| 禁忌内容 | 无酒精、无猪肉、无非伊斯兰宗教符号 |
| 国旗元素 | 不倒置、不铺地、不踩踏 |
| 斋月场景 | 白天无进食/饮水画面，BGM柔和 |
| 社交距离 | 非家庭成员间无身体接触 |

#### 7.7 与多模态生成技能的衔接

确认流程走完后，组装最终中文/英文 prompt：

1. 将用户所有选择拼接为一段详细的中文场景描述（作为主 prompt）
2. 在末尾追加文化合规约束（`--negative-prompt` 或内嵌排除项）
3. **然后**加载「多模态内容生成」技能，调用 `buddy-cloud.py video` 或 `video-fx` 执行生成
4. 确认流程中用户的选择优先级 > 多模态生成技能的"零交互原则"
