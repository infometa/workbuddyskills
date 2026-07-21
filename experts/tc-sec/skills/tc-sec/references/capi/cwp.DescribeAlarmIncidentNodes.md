# # 该接口仅支持分析木马、高危命令、恶意请求三种类型，否则不调用 DescribeAlarmIncidentNodes
# cwp.DescribeAlarmIncidentNodes — 进程链溯源入口

## 入参（三个必填）

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `Uuid` | string | 是 | 告警事件的 `Uuid` 字段（机器 UUID）。**不要另发 `DescribeMachineList` 查 UUID**——告警事件（DescribeMalWareList、DescribeBashEventsNew、DescribeReverseShellEvents 等）返回的每条记录都带 `Uuid` 字段，直接取即可。若只有 IP，先用 run.py 或 wf.page 拿告警数据，从返回里取 Uuid |
| `AlarmVid` | string | 是 | 由 `alarm_vid.py` 计算（见下方）|
| `AlarmTime` | int | 是 | 告警事件 `CreateTime` 转 Unix 时间戳：`python3 scripts/time_util.py ts "<CreateTime>"` |
| `TableId` | int | 否 | 告警来源表 ID，通常不传 |

```bash
python3 scripts/tccli_cli.py cwp DescribeAlarmIncidentNodes \
  --Uuid "<uuid>" \
  --AlarmVid "<vid>" \
  --AlarmTime <unix_ts> \
  --output json
```

## ✅ AlarmVid 计算：一律调用 `scripts/alarm_vid.py`（禁止手写 md5）

**推荐 —— 从告警事件 JSON 直接算**（workflow 里最常用）：
```bash
python3 scripts/alarm_vid.py event --uuid <uuid> --type 木马 --event '{"FilePath":"/tmp/x.sh"}'
python3 scripts/alarm_vid.py event --uuid <uuid> --type 高危命令 --event '{"Pid":12345,"BashCmd":"curl evil.com"}'
python3 scripts/alarm_vid.py event --uuid <uuid> --type 恶意请求 --event '{"Domain":"evil.example.com"}'
```

**已知具体字段**（三个类型分别有 CLI 子命令，快速验证/调试用）：
```bash
python3 scripts/alarm_vid.py bash   <uuid> <pid> <bashcmd>
python3 scripts/alarm_vid.py malreq <uuid> <domain>
python3 scripts/alarm_vid.py trojan <uuid> <filepath>
```

**Python 模块调用**（workflow 脚本内批量计算，无需起子进程）：
```python
from alarm_vid import compute_alarm_vid
vid = compute_alarm_vid(machine_uuid, "木马", event_dict)   # 字段缺失返回空串
```

> ⚠️ **禁止**在 workflow / 报告脚本里 `import hashlib` 自行拼接 md5 计算 AlarmVid —— 顺序/编码/str 转换任一处错都会导致图谱查不到、且难排查。所有 AlarmVid 计算必须走 `alarm_vid.py`（脚本 CLI 或 `compute_alarm_vid` 函数二选一）。

---

## 计算规则（仅作原理说明，实际使用请调脚本）

⭐ 不同告警类型的 AlarmVid 计算方式不同：
- **高危命令**: `md5(uuid + pid + bashcmd)`
- **恶意请求**: `md5(uuid + domain)`
- **木马**:     `md5(uuid + filepath)` — filepath 是木马文件的完整路径（`FilePath` 字段）

> 不是每个告警都能查到事件图谱数据（需要有足够的进程链支撑），查不到是正常情况，不影响其他溯源流程。

---

## 返回结构

顶层返回 `IncidentNodes[]`，每项对应一个事件（通常只有一项）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `IncidentId` | string | 事件 ID，**透传给 `DescribeVertexDetail` 的 `IncidentId` 入参** |
| `TableName` | string | 事件所在分区表名，格式为 `incidents_YYYYMM`（如 `incidents_202628`），**透传给 `DescribeVertexDetail` 的 `TableName` 入参**。注意：这是入侵事件表，不是告警表；`DescribeVertexDetail` 返回的 `AlarmInfo.AlarmId` 前缀（如 `events_malware_0003`、`events_hostlogin_202628`）才是告警表名，两者不同 |
| `VertexCount` | int | 节点总数 |
| `Vertex[]` | 数组 | 节点列表，每项含以下字段 |

### `Vertex[]` 单项字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `Vid` | string | 节点 ID，**作为 `DescribeVertexDetail` 的 `VertexIds` 元素** |
| `ParentVid` | string | 父节点 ID，用于构造进程链树（空串或不在集合内 → 该节点为根） |
| `Type` | int | 节点类型（与 `DescribeVertexDetail` 的 Type 一致：1=进程、2=网络、3=文件、4=SSH） |
| `IsLeaf` | bool | 是否叶子节点 |
| `IsAlarm` | bool | 该节点是否命中告警 |
| `IsWeDetect` | bool | 是否为微步检测命中 |
| `ProcNamePrefix` | string | 进程名截断预览 |
| `ProcNameMd5` | string | 进程名 MD5 |
| `CmdLinePrefix` | string | 命令行截断预览（完整命令行需调 `DescribeVertexDetail`） |
| `CmdLineMd5` | string | 命令行 MD5 |
| `FilePathPrefix` | string | 文件路径截断预览 |
| `FilePathMd5` | string | 文件路径 MD5 |
| `AddressPrefix` | string | 网络地址截断预览 |
| `AddressMd5` | string | 网络地址 MD5 |

### 典型取值方式（workflow 脚本）

```python
# resp 是 DescribeAlarmIncidentNodes 的返回 dict
for inc in resp.get("IncidentNodes", []):
    incident_id = inc["IncidentId"]
    table_name  = inc["TableName"]
    vids        = [v["Vid"] for v in inc.get("Vertex", [])]
    # 再用 incident_id + table_name + vids 调 DescribeVertexDetail
```

---

## 拼接细节（易错点，脚本已全部处理）

- **顺序严格**：`uuid + pid + bashcmd`，不是 `pid + uuid + ...`；`uuid + domain`，不是 `domain + uuid`；`uuid + filepath`。
- **pid 必须 str()**：告警返回的 `Pid` 常为 int，直接拼会 TypeError；脚本已内建 `str()` 保护。
- **filepath 用完整路径**：来自告警事件里的 `FilePath` 字段，不是 `FileName`、不是目录，是文件全路径。
- **domain 原样拼**：不加协议、不加端口、不 strip 后缀点。
- **字段缺失一律回空串**：`compute_alarm_vid` 在缺关键字段时返回 `""`，调用方需判空跳过。
- **编码固定 utf-8**：脚本内已固定 `.encode("utf-8")`。
