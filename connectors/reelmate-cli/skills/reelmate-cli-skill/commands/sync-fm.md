# sync-fm

将剧集数据同步到已关联的喵影账号。

## 用法

```text
reelmate sync-fm EPISODE_ID [--workspace WORKSPACE_ID] [--set uid=FILMORA_UID]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate sync-fm EPISODE_ID` | 将指定剧集同步到关联的喵影账号 |

## `reelmate sync-fm EPISODE_ID`

### 作用

向关联的 Filmora 账号提交剧集同步。

### 参数

- `EPISODE_ID`（必填）：要同步的剧集 ID。
- `--workspace WORKSPACE_ID`：工作区作用域。
- `--set uid=FILMORA_UID`：关联的喵影账号 UID；省略时查询当前项目关联账号并使用首个。
- `--json`：输出 JSON。

### 输出

返回同步任务或同步结果。

### 示例

```bash
reelmate sync-fm EPISODE_ID --workspace WORKSPACE_ID \
  --set uid=FILMORA_UID --json
```

## 注意事项

- 没有可用关联账号时命令会在本地提示，不发送无效同步请求。
- 同步会改变远端数据，执行前确认目标剧集和账号。
