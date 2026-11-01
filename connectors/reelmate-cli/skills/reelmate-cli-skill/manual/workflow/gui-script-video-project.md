# GUI 环节 1：项目创建

只在当前包为 `project` 或 `missing` 含 `sp_id` 时读取。契约见 [_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/1 | 定位或创建并绑定制片工坊项目 | `workspace show` 有 `workspace_id`；重新 `workflow detect` 后 `stage` 不再是 `project` |

已有项目时定位并绑定，不重复创建。多个候选让用户选择。

需要新建时按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`。创作模式固定为制片工坊（`creation_mode=1`），复述展示名、不弹选择器。剧目类型与画面比例必须按 [_hard-gate.md](_hard-gate.md) 用网页展示名列出全部枚举（国内仿真人剧、海外仿真人剧、2D/3D动漫；`9:16 竖屏`、`16:9 横屏`），不查目录，也不要列出 Web「自定义」。

```bash
reelmate workspace create NAME --space SPACE_ID \
  --set creation_mode=1 --set sp_type=SP_TYPE --set ratio=RATIO \
  --dry-run --json
reelmate workspace create NAME --space SPACE_ID \
  --set creation_mode=1 --set sp_type=SP_TYPE --set ratio=RATIO \
  --idempotency-key KEY --json
reelmate deeplink project --workspace SP_ID --set creation_mode=1 --json
reelmate workflow detect --scope studio --workspace SP_ID --json
```

`SP_ID` 取创建响应的 `data.workspace_id`。`SPACE_ID` 来自账号、工作区信息或用户提供。
