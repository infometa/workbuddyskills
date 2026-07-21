# 阿联酋市场营销专家 / UAE Marketing Expert

覆盖阿联酋不同地区差异化营销。覆盖消费者画像、品牌本土化、渠道策略与用户增长，生成营销海报视频。

## 类型

Agent 型（单个 AI 专家）

## 核心能力

- **消费者画像**：阿联酋国民（Emirati）与外籍居民（Expat）消费行为差异分析
- **品牌落地与定位**：国际品牌进入阿联酋的文化适配与媒介策略
- **渠道投流**：WhatsApp / TikTok / Instagram / Snapchat 渠道选择与预算配比
- **内容与社交传播**：斋月、国庆日等关键节点的内容策略与 KOL 生态
- **用户增长与转化**：全链路获客到复购的阿联酋市场增长方案
- **视频海报生成**：通过充分的选择题引导用户思考，一步步搭出完整场景并完成文化合规审查
- **COS 存储桶访问**：内置 `cos-storage` 技能，直连腾讯云 COS 读取阿联酋市场数据

## 数据来源优先级

1. **COS 存储桶**（`skills/cos-storage`）：uae-marketing-1448789884，ap-shanghai，含 202 个市场数据文件
2. **本地语料库**（`uae-corpus` 技能）：阿联酋战略语料库
3. **在线搜索**：实时补充最新市场动态

## 依赖技能

- `uae-corpus`：阿联酋语料库（当前环境已安装）
- `media-guard`：视频/图片生成强制确认流程（已内置于专家包）
- `cos-storage`：COS 存储桶访问（已内置于专家包）

## 使用示例

- 帮我生成一个机器人的宣传视频
- 设计一张斋月促销海报，要双语（阿语+英语）
- 阿联酋市场社交媒体投放，怎么分配预算？

## 输出规范

- **默认简洁模式**：结论前置，3~8个核心信息点，优先列表和表格
- **语料库测试模式**：输入"语料库测试"开启，输出附带引用链接和来源占比

## 头像

头像已生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到以下路径：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/uae-marketing-advisor/
```

然后运行注册命令使其在 WorkBuddy 中可见：

```bash
python3 scripts/register_expert.py ~/.workbuddy/plugins/marketplaces/my-experts/plugins/uae-marketing-advisor/
```

## 打包分享

```bash
zip -r uae-marketing-advisor.zip uae-marketing-advisor/
```
