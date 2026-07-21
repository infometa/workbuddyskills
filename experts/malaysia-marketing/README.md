# 大马营销通 · Malaysia Marketing Expert

马来西亚市场营销智能分析专家，专注消费者洞察、品牌定位、广告投放、社交媒体与本地文化策略。

## 类型

Agent 型（单个 AI 专家）

## 核心能力

- **消费者画像与行为洞察**：基于种族、宗教、收入分层的马来西亚消费者分析
- **品牌定位与本地化策略**：含清真（Halal）合规、多语言本地化建议
- **社交媒体与内容传播**：Facebook / Instagram / TikTok / WhatsApp 等平台策略
- **广告投放与渠道规划**：Google / Meta / TikTok Ads 及本地线下渠道
- **用户增长与留存**：结合本地支付（Touch n Go、GrabPay、FPX、DuitNow）与电商生态（Shopee、Lazada、TikTok Shop）的转化路径设计
- **营销海报与短视频生成**：自动生成符合马来西亚文化合规要求的促销海报与短视频

### 输出规范

- 默认简洁模式：3~8 个核心信息点，列表化，结论先行
- 详细模式：用户明确要求时输出完整分析框架
- 语料库测试模式：输入"语料库测试"或"测试模式"进入，附引用来源与内容来源占比

## 使用示例

- 分析马来西亚消费者画像与购买行为趋势
- 帮我生成一张产品在马来西亚的促销海报
- 马来西亚市场社交媒体投放，TikTok 和 Facebook 怎么分配预算？

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512x512 px
- 大小：单张不超过 500KB

## 内置语料库

本专家包内置完整语料库（`corpus/` 目录），包含 70 篇 HTML/PDF 文件，覆盖 19 个主题领域：

- 数字支付与金融科技、电商平台与生态、数字经济与政策
- 人口统计、社交媒体与广告、消费者洞察与世代
- 零售与物流、清真产业与出口、KOL/KOC 达人营销
- 节庆消费、电子钱包与数字银行、外卖与出行
- 行业垂直领域、电竞与游戏等

所有文件均可离线读取，无需联网或 API Key。`corpus/manifest.json` 是语料库的完整索引，记录了全部 70 个文件的原始 URL、COS 路径（cos_key）与下载状态。

### COS 在线存储桶（备选方案）

即使无本地 `corpus/` 目录，也可通过 COS 存储桶在线访问全部语料：

- 存储桶：`malaysia-marketing-1448789884.cos.ap-shanghai.myqcloud.com`（public-read，无需 Key）
- 索引文件：`https://malaysia-marketing-1448789884.cos.ap-shanghai.myqcloud.com/manifest.json`
- 单文件下载：`https://malaysia-marketing-1448789884.cos.ap-shanghai.myqcloud.com/{cos_key}`

### 两个版本

| 版本 | 包含 corpus/ 文件 | 大小 | 适用场景 |
|------|-------------------|------|----------|
| **Full**（完整版） | 70 篇语料文件 | ~27 MB（压缩包）/ ~42 MB（解压后） | 需要离线访问语料的环境 |
| **Lite**（精简版） | 仅 manifest.json 索引 | < 1 MB（压缩包） | 在线环境，通过 COS 访问语料 |

## 安装

将专家包目录放到以下路径：

```
~/.workbuddy/experts/malaysia-marketing/
```

然后在 WorkBuddy 中即可看到该专家并开始对话，无需额外注册命令。

## 打包分享

```bash
# 完整版（含语料库）
zip -r malaysia-marketing.zip malaysia-marketing/

# 精简版（仅保留 corpus/manifest.json 索引，不含语料文件）
zip -r malaysia-marketing-lite.zip malaysia-marketing/ -x "malaysia-marketing/corpus/*"
zip malaysia-marketing-lite.zip malaysia-marketing/corpus/manifest.json
```
