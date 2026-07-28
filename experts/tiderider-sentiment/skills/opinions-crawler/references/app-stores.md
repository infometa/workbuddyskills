# 商店平台评分与评论抓取方案

OpenCLI 当前未内置 Apple App Store / Google Play / 国内应用商店的适配器。本文档提供三种替代方案，按推荐度排序。

## 方案一：appstore-review-cli（强烈推荐）

[appstore-review-cli](https://pypi.org/project/appstore-review-cli/) 是专为 App Store 和 Google Play 评分评论设计的 CLI 工具，无需 API Key、无需账号。

### 安装

```bash
pip install appstore-review-cli

# 需要 Google Play 支持时
pip install appstore-review-cli[google]

# 需要 pandas DataFrame 输出时
pip install appstore-review-cli[pandas]
```

### Apple App Store

#### 搜索应用，获取 App ID

```bash
appstore-reviews search "微信"
appstore-reviews search "TikTok" --limit 5
```

输出结果包含 `app_id`（数字 ID），用于后续命令。

#### 获取评分和评论

```bash
# 获取 2 星及以下的差评（最近 30 天）
appstore-reviews reviews 414478124 --stars 2 --days 30

# 过滤含特定关键词的评论（如 crash、bug）
appstore-reviews reviews 414478124 --keywords crash,freeze,bug --stars 2

# 按最有帮助排序
appstore-reviews reviews 414478124 --stars 2 --sort votes

# 获取 3 星中评（最有价值的反馈区间）
appstore-reviews reviews 414478124 --min-stars 3 --stars 3

# 翻页（每页 50 条，最多 10 页 = ~500 条，这是 Apple 的限制）
appstore-reviews reviews 414478124 --stars 2 --pages 5

# 指定国家/地区
appstore-reviews reviews 414478124 --stars 2 --country jp      # 日本
appstore-reviews reviews 414478124 --stars 2 --country de      # 德国
```

#### 导出数据

```bash
# JSON 格式
appstore-reviews reviews 414478124 --stars 2 --pages 5 --format json > reviews.json

# CSV 格式
appstore-reviews reviews 414478124 --stars 2 --pages 5 --format csv > reviews.csv
```

#### 竞品对比

```bash
# 同时拉取两个 App 的差评并对比
appstore-reviews compare 414478124 310633997 --stars 2 --pages 3

# JSON 输出便于后续分析
appstore-reviews compare 414478124 310633997 --stars 2 --format json
```

#### 版本对比

```bash
# 自动检测最近两个版本
appstore-reviews version-diff 414478124 --pages 5

# 指定版本号
appstore-reviews version-diff 414478124 --old 8.0.0 --new 8.1.0 --pages 5
```

#### 评分趋势

```bash
# 按周聚合
appstore-reviews trend 414478124 --period week --pages 5

# 按月聚合，只看差评
appstore-reviews trend 414478124 --period month --stars 2

# 导出
appstore-reviews trend 414478124 --period week --format csv > trend.csv
```

### Google Play

大部分命令与 App Store 相同，增加 `--store google` 参数。

#### 搜索应用，获取包名

```bash
appstore-reviews --store google search "微信"
appstore-reviews --store google search "TikTok"
```

输出结果包含包名（如 `com.tencent.mm`）。

#### 获取评分和评论

```bash
# 基础用法（将 app_id 替换为包名）
appstore-reviews --store google reviews com.tencent.mm --stars 2 --days 30

# 按关键词过滤
appstore-reviews --store google reviews com.zhiliaoapp.musically --keywords crash,bug

# 翻页
appstore-reviews --store google reviews com.tencent.mm --stars 2 --pages 5

# 导出
appstore-reviews --store google reviews com.tencent.mm --stars 2 --pages 5 --format json
```

#### 竞品对比 & 趋势

```bash
# 对比
appstore-reviews --store google compare com.tencent.mm com.alibaba.android.rimet --stars 2

# 趋势
appstore-reviews --store google trend com.tencent.mm --period week --pages 5
```

### 通用参数速查

| 参数 | 说明 | 示例 |
|------|------|------|
| `--stars N` | 评分 ≤ N 星 | `--stars 2`（1-2星差评） |
| `--min-stars N` | 评分 ≥ N 星 | `--min-stars 4`（4-5星好评） |
| `--days N` | 最近 N 天 | `--days 30` |
| `--keywords w1,w2` | 关键词过滤 | `--keywords crash,bug,login` |
| `--pages N` | 翻页数（1-10） | `--pages 5` |
| `--sort date\|votes` | 排序方式 | `--sort votes` |
| `--country CODE` | 国家/地区 | `--country jp` |
| `--format json\|csv` | 输出格式 | `--format json` |

### 数据字段说明

每条评论包含以下字段：

| 字段 | 说明 |
|------|------|
| `rating` | 评分（1-5） |
| `title` | 评论标题 |
| `content` | 评论正文 |
| `author` | 评论者用户名 |
| `version` | 评论时的 App 版本 |
| `date` | 评论日期 |
| `votes` | 有用/没用投票数 |
| `country` | 评论者国家/地区 |

---

## 方案二：OpenCLI browser 命令 + 手动抓取

如果上述工具不满足需求，或需要抓取国内应用商店（如华为、小米、应用宝等），可使用 OpenCLI 的浏览器操控能力。

### 打开商店页面

```bash
# Google Play
opencli browser open "https://play.google.com/store/apps/details?id=com.tencent.mm"

# Apple App Store（网页版）
opencli browser open "https://apps.apple.com/cn/app/id414478124"

# 华为应用市场
opencli browser open "https://appgallery.huawei.com/app/C100123456"
```

### 获取页面状态

```bash
opencli browser state    # 返回结构化 DOM 快照
```

### 提取评分数据

```bash
# 根据选择器提取内容
opencli browser get --selector ".score"              # 评分数字
opencli browser get --selector ".review-count"       # 评论总数
opencli browser get --selector ".rating-bar"         # 星级分布
```

### 截图保存

```bash
opencli browser screenshot --output ./store_screenshot.png
```

### 滚动加载更多评论

```bash
opencli browser scroll --amount 500    # 向下滚动 500px
opencli browser state                  # 重新获取加载后的内容
```

### 注意事项

- 商店页面的 DOM 结构可能随时变化，选择器需要定期更新
- Google Play 网页版对非登录用户限制较多，部分数据可能需要登录
- 国内应用商店的反爬机制各不相同，有些可能需要验证码

---

## 方案三：为商店编写 OpenCLI 自定义适配器

如果需要长期、频繁抓取商店数据，可以为特定商店编写 OpenCLI 自定义适配器，将其变成可复用的 CLI 命令。

### 自动生成（推荐先尝试）

```bash
# 自动探索并生成适配器
opencli generate "https://play.google.com/store/apps/details?id=com.tencent.mm" --site googleplay --goal reviews
```

### 手动编写 L 形

如果自动生成失败，手动探索并创建 YAML 适配器：

```bash
# 1. 用 browser 探索页面结构
opencli browser open "https://play.google.com/store/apps/details?id=com.tencent.mm"
opencli browser eval "document.querySelector('.score').textContent"

# 2. 创建适配器文件 ~/.opencli/clis/googleplay/reviews.yaml
```

YAML 适配器模板：

```yaml
site: googleplay
name: reviews
description: Google Play 应用评论
domain: play.google.com
strategy: public
browser: true

args:
  limit:
    type: int
    default: 20

pipeline:
  - navigate: "https://play.google.com/store/apps/details?id=${{ args.app_id }}"
  - evaluate: |
      (async () => {
        const limit = ${{ args.limit }};
        // 滚动加载评论
        // DOM 抓取逻辑
        return results;
      })()

columns: [rating, title, content, author, date]
```

然后作为命令使用：

```bash
opencli googleplay reviews --app_id com.tencent.mm --limit 50 -f json
```

### 调试技巧

- 先用 `browser eval` 探索 DOM 结构：`document.querySelector('...').innerHTML`
- `data-test` 属性最稳定，其次是语义化的 class 名
- 去重用 `new Set()` 防止重复产品
- 先小规模验证（limit=5），确认无误后再扩大规模

---

## 国内应用商店补充

对于华为应用市场、小米应用商店、OPPO软件商店、vivo应用商店、应用宝等国内平台：

| 商店 | 网页版地址 | 建议方案 |
|------|-----------|---------|
| 华为应用市场 | appgallery.huawei.com | OpenCLI browser 或自定义适配器 |
| 小米应用商店 | app.mi.com | OpenCLI browser |
| 应用宝 | sj.qq.com | OpenCLI browser |
| OPPO软件商店 | store.oppo.com | OpenCLI browser |
| vivo应用商店 | apps.vivo.com | OpenCLI browser |

**注意**：国内应用商店的网页版功能通常不如 App 端完善，评论数据可能展示不全。对于深度分析需求，建议优先使用 Apple App Store 和 Google Play 的数据（覆盖最核心的用户群体）。

---

## 完整工作流示例

### 竞品商店舆情监控

```bash
# 1. 拉取竞品差评
appstore-reviews reviews 414478124 --stars 2 --days 30 --pages 5 --format json > wechat_bad.json
appstore-reviews reviews 310633997 --stars 2 --days 30 --pages 5 --format json > whatsapp_bad.json

# 2. 对比两个 App
appstore-reviews compare 414478124 310633997 --stars 2 --format json > compare.json

# 3. 查看评分趋势
appstore-reviews trend 414478124 --period week --pages 5 --stars 2 --format csv > trend.csv
appstore-reviews trend 310633997 --period week --pages 5 --stars 2 --format csv >> trend.csv

# 4. Google Play 版本
appstore-reviews --store google reviews com.tencent.mm --stars 2 --days 30 --pages 5 --format json > wechat_gp_bad.json
```
