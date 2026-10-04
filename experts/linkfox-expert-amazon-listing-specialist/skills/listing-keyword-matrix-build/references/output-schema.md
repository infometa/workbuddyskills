# listing-keyword-matrix-build 输出契约

> 传输层见 `skill-output-protocol`：`Saved full response: <绝对路径> (N bytes)`  
> 载荷层：**裸 JSON**，禁止 `type: "skill-output"` envelope。

## 推荐形状

```jsonc
{
  "asin": "B07JB964VX | NEW",
  "region": "US",
  "time_window": "latelyDay_30",
  "total": 20,
  "keywords": [
    {
      "keyword": "collapsible travel cup",
      "keywordPopularityRank": 853201,
      "productNaturalRank": 31,
      "weeklySearchVolume": 8000,
      "clickToPurchaseConversionRate": 0.08,
      "value_score": 34.6,
      "source": "SIF | category_node | product_feature",
      "field": "Title | Bullet 1 | seed_keywords",
      "trafficCharacteristicMarkers": ["isAccurateTailKw", "nfPosition"],
      "is_growing": false,
      "is_long_tail": true,
      "reason": "搜索排名 #853201 · 转化 8% · 自然位 #31"
    }
  ],
  "scored_table": [
    {
      "keyword": "collapsible travel cup",
      "text": "collapsible travel cup",
      "value_score": 34.6,
      "search_volume_rank": 853201,
      "natural_rank": 31,
      "conversion_score": 8.0,
      "source": "SIF | category_inferred",
      "field": "Title",
      "is_growing": false,
      "is_long_tail": true,
      "markers": ["isAccurateTailKw", "nfPosition"],
      "reason": "..."
    }
  ],
  "raw_matrix": {
    "natural_traffic": [],
    "sp_ads": [],
    "brand_ads": [],
    "video_ads": [],
    "ac_recommended": [],
    "conversion_top": [],
    "long_tail": [],
    "growing": [],
    "declining": [],
    "multi_variant": [],
    "category_seed": []
  },
  "stats": {
    "source_mode": "asin_sif | asin_sellersprite_backup | category_seed",
    "category_node": {"name": "Single-Serve Brewers"},
    "total_raw_keywords": 100,
    "unique_keywords": 99,
    "filtered_count": 1,
    "scored_count": 20,
    "coverage_warning": null
  }
}
```

## 字段说明

| 字段 | 消费者 | 说明 |
|------|--------|------|
| `keywords[]` | 前端 `keyword-schema` / KeywordDataTable | 必须含 `keyword` + 至少一个流量信号字段 |
| `scored_table[]` | listing-title/bullet/search-terms writer | `text` 与 `keyword` 同值，供 `kw.text` 读取 |
| `raw_matrix` | 诊断 / 报告 | 16 维分层原始条目 |
| `stats.source_mode` | 编排 skill / 报告 | `asin_sif` 可展示 SIF 数值；`asin_sellersprite_backup` 可展示 SellerSprite backup 数值但需标注来源；`category_seed` 禁止展示搜索量/排名/value_score |
| `stats.coverage_warning` | 编排 skill | `low_keyword_coverage` / `sif_no_data` / `all_filtered` / `seed_only` |

## 文件名

`linkfox-listing-keyword-matrix-build-<timestamp>.json`（由 `resolve_data_path` 生成）
