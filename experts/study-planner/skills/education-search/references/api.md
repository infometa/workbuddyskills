# 搜题 API 文档

## 接口信息

**接口地址**: `http://edu-openapi.baidu.com/EduServer/exercise_search`

**请求方式**: POST

**Content-Type**: `application/json`

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | ✅ | - | 搜索内容 |
| `k` | ❌ | 10 | 返回结果数量 |
| `search_type` | ❌ | 1 | 搜索类型：1=试题试卷，2=教辅资料，3=备考课程 |
| `public_ip` | ❌ | - | 外网 IP |
| `internal_ip` | ❌ | - | 内网 IP |
| `hostname` | ❌ | - | 主机名 |
| `origin_query` | ❌ | - | 用户原始查询内容 |

## 请求示例

```bash
curl -X POST 'http://edu-openapi.baidu.com/EduServer/exercise_search' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "数学",
    "k": 3,
    "search_type": 2,
    "public_ip": "1.2.3.4",
    "internal_ip": "192.168.1.2",
    "hostname": "myhost",
    "origin_query": "考研数学"
  }'
```

## 返回格式

返回结构：`{"exercises": [...]}`

### exercises 数组字段

| 字段 | 说明 |
|------|------|
| `id` | 习题 ID |
| `exercise_category_id` | 分类 ID |
| `exercise_subject_id` | 科目 ID |
| `material_type` | 类型（1=题目，2=答案/试卷） |
| `title` | 标题 |
| `exercise_category_name` | 分类名称 |
| `exercise_subject_name` | 科目名称 |
| `pdf_url` | PDF/资源链接 |
| `weight` | 相关度分数 |