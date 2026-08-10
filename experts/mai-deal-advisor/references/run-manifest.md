# 本地运行清单

每个标准工作流都必须创建或更新 `outputs/run-manifest.json`。它记录本次工作实际生成了什么、使用了什么来源、运行了哪些校验门，以及当前产物是否可交付。它不是项目报告，也不替代质检记录。

## 数据边界

- 清单和清单引用的本地产物均保留在用户当前工作目录。
- `data_boundary` 固定为 `local_only`，表示用户文件、生成产物和运行记录不回传 MAI，不表示所有可选查询都离线完成。
- 调用港交所披露易等公开端点前取得用户确认，并在 `external_queries` 记录服务名称、股票代码和日期范围；不得记录密钥或上传用户文件。
- 不把用户材料、对话内容、清单或产物发送给 MAI；只有用户主动申请人工复核时，才按用户确认的摘要另行提交。
- 清单不得写入访问令牌、账号密码或其他密钥。

## 字段定义

| 字段 | 含义 |
|---|---|
| `schema_version` | 运行清单结构版本，当前为 `1.0` |
| `package_version` | 专家包版本，当前为 `1.3.1` |
| `workflow_id` | 来自问题路由表的稳定工作流编号 |
| `artifacts` | 本次创建或更新的文件及其类型和状态 |
| `source_status` | 信息截止日、报告期和来源定位记录 |
| `gate_status` | 各适用校验门是否运行、退出码及结果 |
| `acceptance_status` | 路由表所列验收条件及其完成状态 |
| `manual_checks` | SVG 视觉预览等无法由当前脚本替代的必需人工检查 |
| `deliverable_status` | `READY`、`DRAFT_WITH_BLOCKERS` 或 `UNVERIFIED` |
| `open_issues` | 尚未解决的事实缺口、冲突和拦截项 |
| `human_review_requested` | 用户是否主动要求 MAI 人工复核 |
| `data_boundary` | 固定为 `local_only` |
| `external_queries` | 用户确认后向公开端点发送的最小查询参数；未查询时为空数组 |

## 最小示例

```json
{
  "schema_version": "1.0",
  "package_version": "1.3.1",
  "workflow_id": "project_triage",
  "artifacts": [
    {
      "path": "outputs/project-triage.md",
      "type": "project_triage",
      "status": "created"
    }
  ],
  "source_status": {
    "cutoff_date": null,
    "reporting_period": null,
    "provenance": []
  },
  "gate_status": {},
  "acceptance_status": [
    {
      "condition": "项目阶段、资料缺口和下一步三件事已填写",
      "status": "pending"
    }
  ],
  "manual_checks": [],
  "deliverable_status": "UNVERIFIED",
  "open_issues": [],
  "human_review_requested": false,
  "data_boundary": "local_only",
  "external_queries": []
}
```

## 更新时点

1. 选择工作流后立即创建清单，初始状态为 `UNVERIFIED`。
2. 每生成一个标准产物，就更新 `artifacts`。
3. 每轮校验后，更新 `gate_status`、`acceptance_status`、`manual_checks`、`open_issues` 和 `deliverable_status`。
4. 运行公开端点查询后更新 `external_queries`，写明用户确认状态和最小查询参数。
5. 交付时确认清单中的文件路径真实存在，且状态与对用户的表述一致。
