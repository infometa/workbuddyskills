---
name: vipshop-img-product
description: 唯品会（vip.com）图片搜索商品技能。当用户想通过图片搜索相似商品时触发，包括但不限于：以图搜图、拍照搜商品、图片搜索、找同款等。返回商品名称、价格、品牌、图片、链接等结构化信息。
---

# 唯品会图片搜索商品

> ⚠️ **重要规范**：AI 必须先加载本 skill 规范（use_skill），再执行任何脚本或返回结果，不得绕过 skill 规范自行处理数据。

## 概述
唯品会（vip.com）图片搜索商品技能。当用户想通过图片搜索相似商品时触发，包括但不限于：以图搜图、拍照搜商品、图片搜索、找同款等。返回商品名称、价格、品牌、图片、链接等结构化信息。

**功能特性**：本地图片上传、智能分类识别、相似商品搜索、结构化输出

**重要提示**：需要用户先通过 `vipshop-user-login` skill 登录唯品会账户。

## 使用场景
- 用户想通过本地图片搜索相似商品时
- 用户想找同款商品时
- 用户上传本地图片询问商品信息时
- 拍照搜商品时

## 触发示例
用户输入以下内容可触发本 skill：
- "帮我用这张图片搜索相似商品"
- "以图搜图"
- "这个图片帮我找同款"
- "帮我搜一下这张图片里的商品"
- "拍照搜商品"
- "上传图片搜索"
- "找同款"
- "图片搜商品"

## 工作流程

### 步骤 1：检测登录状态
在执行搜索前，AI 必须先检测登录状态：
- 检查 `~/.vipshop-user-login/tokens.json` 是否存在且有效
- **如果已登录**：直接执行步骤2
- **如果未登录**：自动触发 `vipshop-user-login` skill 完成登录流程

### 步骤 2：接收输入
需要用户提供本地图片文件路径。

### 步骤 3：执行脚本

**首次搜索（使用本地图片文件）**
```bash
python3 scripts/img_search.py --image /path/to/image.jpg
```

**获取下一页**
用户回复"下一页"时，AI 应缓存图片URL、分类类型、检测区域，并使用上一次请求返回的 pageToken 直接调用第3步接口：
```bash
python3 scripts/img_search.py --image-url "图片URL" --category-type "分类类型" --rect "检测区域" --page-token "上一次返回的pageToken"
```

**分页参数说明**：
- `--image-url`：首次搜索返回的 `图片URL` 字段
- `--category-type`：首次搜索返回的 `识别分类.类型` 字段
- `--rect`：首次搜索返回的 `识别分类.检测区域` 字段
- `--page-token`：上一次请求返回的 `商品分析.下一页token` 字段

**支持的图片格式**：jpg、jpeg、png、gif、bmp、webp

### 步骤 4：展示结果
解析 JSON 数据并格式化输出，展示搜索结果。

**⚠️ 重要规则**：
- **必须完整展示** Python 脚本返回的所有数据，不得对数据进行截断、省略或选择性隐藏
- 显示字段：商品ID、商品名称、品牌、特卖价、划线价、折扣、卖点、图片、商品链接
- 如果返回了多条商品记录，必须全部展示，不能只展示前几条

## 输出格式

```json
{
  "code": 1,
  "msg": "success",
  "图片URL": "/xupload.vip.com/xxx.jpg",
  "识别分类": {
    "类型": "UPPERBODY",
    "名称": "上装",
    "检测区域": "109,306,548,768",
    "所有分类": [...]
  },
  "商品分析": {
    "总计": 10,
    "下一页token": "xxx",
    "商品列表": [
      {
        "商品ID": "xxx",
        "商品名称": "商品名称",
        "品牌": "品牌名",
        "特卖价": "99.00",
        "划线价": "199.00",
        "折扣": "5折",
        "卖点": ["卖点1", "卖点2"],
        "图片": "https://...",
        "商品链接": "https://passport.vip.com/exchangeTokenFromApp?..."
      }
    ]
  },
  "原始数据": {...}
}
```

**字段说明**：
- **特卖价**：`price.salePrice`
- **划线价**：`price.marketPrice`
- **折扣**：`price.saleDiscount`
- **卖点**：从 `labels` 字段提取所有 `value` 值
- **下一页token**：用于分页，有值时可通过 `--page-token` 参数获取下一页

## 输出格式示例

**用户展示格式：**
```
🔍 图片搜索结果

📸 图片分类：上装

| 序号 | 商品图片 | 商品名 | 品牌 | 特卖价 | 划线价 | 折扣 | 卖点 |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---|
| 1 | ![商品图](图片URL) | [耐克运动T恤](商品链接) | 耐克 | ¥99.00 | ¥199.00 | 5折 | 透气舒适、运动休闲 |
| 2 | ![商品图](图片URL) | [商品名称](商品链接) | 品牌 | ¥XX.XX | ¥XX.XX | X折 | 卖点1、卖点2 |
| ... |

💡 可回复"查询第X个商品"查看任意商品详细信息！
📄 想看更多商品？可以回复"下一页"查看
```

**商品名超链接说明**：
- 商品名必须使用 Markdown 链接格式：`[商品名](商品链接)`
- 商品链接从脚本返回的 `商品链接` 字段获取

## 示例

### 示例 1：通过本地图片搜索商品
**用户输入：** "帮我用这张图片搜索相似商品 /path/to/image.jpg"

**执行：** `python3 scripts/img_search.py --image /path/to/image.jpg`

**输出：**
```json
{
  "code": 1,
  "msg": "success",
  "识别分类": {...},
  "商品分析": {...}
}
```

### 示例 2：未登录
**用户输入：** "帮我搜索图片"

**执行：** `python3 scripts/img_search.py --image /path/to/image.jpg`

**输出：**
```json
{
  "code": -1,
  "msg": "login_required",
  "message": "需要登录唯品会账户",
  "action": "请先登录唯品会账户后再使用图片搜索"
}
```

## AI 行为规范

### 未登录处理
当检测到用户未登录时，AI **必须**：
1. 立即自动触发登录流程
2. 登录成功后自动继续执行搜索

### 禁止行为
- ❌ 不要只返回错误信息让用户自己处理
- ❌ 不要等待用户再次请求登录
- ❌ 不要使用 `原始数据` 字段进行二次整理展示

### 正确行为
- ✅ 检测到未登录时立即自动触发登录流程
- ✅ 登录成功后自动继续执行搜索
- ✅ 严格按照 Python 脚本返回的 `商品分析` 字段内容进行展示

## 实现要求

### 脚本位置
`scripts/img_search.py`（使用 Python 标准库，无外部依赖）

### 图片验证
- 检查文件是否存在
- 检查文件格式是否支持

### 接口调用
1. **图片上传接口**
   - URL: `https://mapi-file-tx.vip.com/xupload/picture/new_upload_inner_applet.jsps`
   - 方式: POST (multipart/form-data)
   - 参数: app_name, client, source_app, api_key, app_version, mobile_platform, union_mark, mobile_channel, mars_cid, warehouse, fdc_area_id, province_id, wap_consumer, picture(文件)

2. **分类识别接口**
   - URL: `https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/search/img/category/v1`
   - 方式: GET
   - 参数: api_key, app_name, app_version, client, imgUrl, mars_cid 等

3. **商品搜索接口**
   - URL: `https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/image/product/list/v1`
   - 方式: POST
   - 参数: api_key, app_name, categoryType, imgUrl, rect, mars_cid, pageToken(可选，用于分页), limit(固定为10) 等

## 注意事项

1. **登录要求**：必须先通过 `vipshop-user-login` skill 登录
2. **图片格式**：仅支持 jpg、jpeg、png、gif、bmp、webp 格式
3. **网络要求**：需要正常网络连接
4. **依赖库**：仅 Python 标准库（urllib、json、os）

## 技术细节

- **实现语言**：Python 3
- **数据格式**：JSON（脚本输出）→ 格式化文本（AI 展示）
- **编码支持**：UTF-8，支持中文
- **异常处理**：完整的网络异常和 API 错误处理
- **依赖库**：仅使用 Python 标准库

## 常见问题

**Q: 支持哪些图片格式？**
A: 支持 jpg、jpeg、png、gif、bmp、webp 格式。

**Q: 需要登录才能使用吗？**
A: 是的，必须先通过 `vipshop-user-login` skill 登录。

**Q: 搜索结果有多少个商品？**
A: 每页返回最多10个相似商品，可通过 pageToken 获取更多。

**Q: 如何获取更多商品？**
A: 使用返回的 `下一页token`，通过 `--page-token` 参数获取下一页数据。

**Q: 支持直接传入图片URL吗？**
A: 不支持，仅支持本地图片文件上传方式。
