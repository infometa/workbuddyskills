# 查询品牌简介页 (profiles/get)


品牌简介页是腾讯广告中的一种落地页类型，用于展示品牌信息。创建创意时，如果 `brand` 组件采用"H5 品牌简介页"形态，需要先通过本接口查询品牌简介页 ID（`page_id`）。

---

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | integer | 是 | 广告主账号ID |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10，最大 100 |

## 响应参数

| 字段名 | 类型 | 说明 |
|--------|------|------|
| data.list[].page_id | integer | 品牌简介页 ID，用于 jump_info 中的 page_id |
| data.list[].name | string | 品牌简介页名称 |
| data.page_info.total_number | integer | 总数量 |

## 请求示例

```bash
node get-profiles.mjs '{"account_id": 12345678}'
```

## 响应示例

```json
{
  "code": 0,
  "data": {
    "list": [
      { "page_id": 53561511, "name": "品牌简介页示例" }
    ],
    "page_info": { "total_number": 1, "page": 1, "page_size": 10 }
  }
}
```

## 在 brand 组件中使用

查询到 `page_id` 后，在创意的 `brand` 组件中按如下方式填写：

```json
"brand": [{
  "value": {
    "jump_info": {
      "page_type": "PAGE_TYPE_H5_PROFILE",
      "page_spec": {
        "h5_profile_spec": {
          "page_id": 53561511
        }
      }
    }
  }
}]
```

> 注意：此形态的 brand 组件只填 `jump_info`，**不填** `brand_name` 和 `brand_image_id`。
