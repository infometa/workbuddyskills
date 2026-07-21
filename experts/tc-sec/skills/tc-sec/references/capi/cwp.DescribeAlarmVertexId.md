# cwp.DescribeAlarmVertexId — 按主机+时间窗批量获取告警点 vid

> 给定主机 UUID 和时间范围，返回该主机在时间窗内所有告警点的 vid 列表（`AlarmVertexIds`）。
> 返回的 vid 可直接作为 `DescribeAlarmIncidentNodes` 的 `--AlarmVid` 参数，无需逐条告警手算 md5。

## 入参

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `Uuid` | string | 是 | 主机 UUID，从告警事件的 `Uuid` 字段获取 |
| `StartTime` | int | 是 | 时间窗起始 Unix 时间戳：`python3 scripts/time_util.py ts "<时间>"` |
| `EndTime` | int | 是 | 时间窗结束 Unix 时间戳 |

## 返回

| 字段 | 类型 | 说明 |
|------|------|------|
| `AlarmVertexIds` | []string | 告警点 vid 列表，可直接传给 `DescribeAlarmIncidentNodes --AlarmVid` |

## 与 DescribeAlarmIncidentNodes 的配合

**重要约束（实测）**：`DescribeAlarmIncidentNodes` 的 `--AlarmTime` 不能传 `0`，必须传落在时间窗内的时间戳（传 `EndTime` 或区间中点均可），传 `0` 时即使 vid 正确也返回空进程链。

```python
start, end = wf.time_range(24, "h")   # 或自定义时间范围
ts_start = int(subprocess.check_output([wf.PY, scripts_path+"/time_util.py", "ts", start]).strip())
ts_end   = int(subprocess.check_output([wf.PY, scripts_path+"/time_util.py", "ts", end]).strip())

# Step 1: 批量拿告警 vid（无需逐条算 AlarmVid md5）
r = wf.exec([wf.PY, wf.T, "cwp", "DescribeAlarmVertexId",
    "--Uuid", uuid, "--StartTime", str(ts_start), "--EndTime", str(ts_end),
    "--output", "json"])
alarm_vids = r.get("AlarmVertexIds") or []

# Step 2: 并发查进程链，AlarmTime 传 EndTime
from concurrent.futures import ThreadPoolExecutor
def query_chain(vid):
    return wf.exec([wf.PY, wf.T, "cwp", "DescribeAlarmIncidentNodes",
        "--Uuid", uuid, "--AlarmVid", vid, "--AlarmTime", str(ts_end),
        "--output", "json"])

with ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(query_chain, alarm_vids))
# 过滤出有进程链数据的
chains = [r for r in results if any(n.get("IncidentId") for n in r.get("IncidentNodes", []))]
```

## 与 alarm_vid.py 的选择

| 场景 | 推荐方式 |
|------|---------|
| 已知具体告警事件（有 Uuid/Pid/BashCmd/FilePath/Domain）| `alarm_vid.py` / `compute_alarm_vid()`（精确定位单条告警） |
| 按主机+时间窗批量拉全部告警的进程链 | `DescribeAlarmVertexId`（无需告警详情，一次批量获取） |

## 注意事项

- 返回的 vid 是"告警点 vid"，与 `DescribeAlarmIncidentNodes` 的返回值 `Vertex[].Vid` 是不同层次的 id，**不能**当 `DescribeVertexDetail` 的 `VertexIds` 使用（那需要先调 DescribeAlarmIncidentNodes 拿到节点集合）。
- 时间窗越长返回的 vid 越多，建议按调查需要控制窗口（如 24h/7d），避免并发请求过多。
