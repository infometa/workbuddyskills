## 场景一：明确关键词搜索

直接搜索一个类别或地点，不涉及特定位置的周边搜索。

**URL 格式：**

```
https://mapapi.qq.com/web/claw/nearby-search.html?keyword={关键词}
```

- **域名**：`map.qq.com`
- **路由**：`/web/claw/nearby-search.html`
- **参数**：`keyword` = 搜索关键词

### 执行步骤

1. **提取关键词**：从用户输入中识别出核心搜索词，去掉"搜"、"找"等修饰词
2. **生成 URL**：拼接 `https://mapapi.qq.com/web/claw/nearby-search.html?keyword={关键词}`
3. **返回链接给用户**

### 示例

| 用户输入   | 提取关键词 | 生成 URL                                                           |
| ---------- | ---------- | ------------------------------------------------------------------ |
| 搜美食     | 美食       | `https://mapapi.qq.com/web/claw/nearby-search.html?keyword=美食`   |
| 找酒店     | 酒店       | `https://mapapi.qq.com/web/claw/nearby-search.html?keyword=酒店`   |
| 天安门在哪 | 天安门     | `https://mapapi.qq.com/web/claw/nearby-search.html?keyword=天安门` |
| 找个加油站 | 加油站     | `https://mapapi.qq.com/web/claw/nearby-search.html?keyword=加油站` |

### 回复模板

```
🔍 已为你生成腾讯地图搜索链接：

https://mapapi.qq.com/web/claw/nearby-search.html?keyword={关键词}

点击链接即可查看搜索结果。
```
