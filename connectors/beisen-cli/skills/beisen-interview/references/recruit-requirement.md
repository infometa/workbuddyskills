# 招聘面试 - 招聘需求命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

## bs_search_requirements_list — 查询招聘需求列表

```bash
beisen-cli interview recruitRequirement bs_search_requirements_list --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `requirementStatus` | integer | ❌ | 需求状态，默认不限：20=审批中、30=审批未通过、40=进行中、50=已关闭、60=已完成、70=已暂停、80=审批已终止 |
| `requirementName` | string | ❌ | 需求名称，默认不限 |
| `requirementCode` | integer | ❌ | 需求编号，默认不限 |
| `createBy` | integer | ❌ | 需求提出人（即需求创建人）用户 ID，默认不限 |

### 参数示例

```bash
# 查询全部需求
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{}'

# 查询进行中的需求
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{"requirementStatus":40}'

# 按名称模糊查询
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{"requirementName":"Java"}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "items": [ { "需求条目字段" } ],
    "total": 5
  },
  "message": null
}
```

- `data.items`：需求列表
- `data.total`：符合条件的需求总数
- 各条目通常含 `requirementId`、`requirementCode`、`requirementName`、`requirementStatus`/`requirementStatusName`、`department`、`dutyUser`、`requirementCount` 等字段（以实际返回为准）

## getRecruitRequirementDetail — 获取招聘需求详情

```bash
beisen-cli interview recruitRequirement getRecruitRequirementDetail --data '{"requirementId":"<id>"}'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `requirementId` | string | ✅ | 需求 ID，GUID 格式 |

### 返回结构（data 字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `requirementId` | string | 需求 ID |
| `requirementCode` | integer | 需求编号 |
| `requirementName` | string | 需求名称 |
| `requirementStatusName` | string | 需求状态名称 |
| `department` | string | 需求部门名称 |
| `dutyUser` | string | 需求负责人姓名 |
| `requirementCount` | integer | 招聘人数 |
| `createDate` | string | 需求提出时间 |
| `expectedArrivalDate` | string | 期望到岗时间 |
| `jobDescription` | string | 工作职责 |
| `qualification` | string | 任职资格 |
| `relationJobId` | string | 已关联职位 ID（多个以逗号分隔） |
| `sentOfferCount` | integer | 已发 Offer 数 |
| `acceptedOffers` | integer | 已接受 Offer 数 |
| `pendingEntryCount` | integer | 待入职人数 |
| `accumulateArriveCount` | integer | 已到岗人数 |

### 注意事项

- `requirementId` 必须从 `bs_search_requirements_list` 返回中提取，严禁编造
- 需求列表与详情包含部门、负责人等内部信息（L1 内部数据），正常展示
- 需求进展可结合 `sentOfferCount`/`acceptedOffers`/`pendingEntryCount`/`accumulateArriveCount` 向用户说明招聘完成情况
