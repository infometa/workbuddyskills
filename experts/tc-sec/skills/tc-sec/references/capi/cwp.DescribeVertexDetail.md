# cwp.DescribeVertexDetail — 溯源图节点详情

> 给定一批节点 ID（VertexIds），批量返回每个节点的完整属性与告警状态。
> 通常用于溯源图详情面板：先用 `DescribeAlarmIncidentNodes` 拿事件的节点列表，再用本接口查选中节点的详情。

## 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `IncidentId` | string | 是 | 事件 ID，用于越权校验，只允许查询本事件下的节点 |
| `TableName` | string | 是 | 事件所在的表名，与 `IncidentId` 配合定位事件所属节点集合 |
| `VertexIds` | []string | 是 | 需要查询详情的节点 ID 列表，不能为空 |

`IncidentId` 和 `TableName` 来自 `DescribeAlarmIncidentNodes` 的返回值（`IncidentId`、`TableName` 字段），直接透传即可。

## 返回结构：VertexDetails[]

每一项是一个"节点详情联合体"，通过 `Type` 字段区分类型，只有该类型对应的字段有效，其他字段为零值，调用方需按 `Type` 分支解析。

### 公共字段（所有类型均有）

| 字段 | 类型 | 说明 |
|------|------|------|
| `VertexId` | string | 节点 ID，与入参对应 |
| `Type` | int | 节点类型：1=进程、2=网络、3=文件、4=SSH |
| `Time` | string | 节点时间，格式 `2006-01-02 15:04:05`；SSH 节点实测可能返回 `1970-01-01 08:00:00`（零值），展示时需判空 |
| `AlarmInfo` | 数组 | 该节点上关联的告警信息（见下） |

### Type=1（进程节点）

| 字段 | 类型 | 说明 |
|------|------|------|
| `ProcName` | string | 进程名（完整路径，如 `/usr/bin/bash`） |
| `CmdLine` | string | 完整命令行 |
| `Pid` | string | 进程号（**字符串类型**，转整数需 `int(Pid)`） |

### Type=2（网络节点）

| 字段 | 说明 |
|------|------|
| `Address` | 对端地址 |
| `DstPort` | 目标端口 |

### Type=3（文件节点）

| 字段 | 说明 |
|------|------|
| `FileMd5` | 文件 MD5 |
| `FileContent` | 文件内容（可能为空） |
| `FilePath` | 文件路径 |
| `FileCreateTime` | 文件创建时间 |

### Type=4（SSH 节点）

| 字段 | 说明 |
|------|------|
| `SrcIP` | 登录源 IP |
| `User` | 登录用户，格式 `group:user` |

### 漏洞附加字段（仅进程 / 文件节点可能有）

命中漏洞检测时额外返回。判空规则：**只有 `HttpContent` 非空时，其余漏洞字段才有意义**（`VulName` 若带 `pcmgr:` 前缀会被后端截掉）。

| 字段 | 说明 |
|------|------|
| `HttpContent` | HTTP 请求内容（非空则为漏洞利用请求） |
| `VulName` | 漏洞名称 |
| `VulSrcIP` | 漏洞攻击源 IP |
| `VulTime` | 漏洞触发时间 |

## AlarmInfo 结构

每条告警项字段（来自真实返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `AlarmId` | string | 复合告警 ID，格式为 `{表名}:{记录ID}`，例如 `events_malware_0003:300007413050`、`events_hostlogin_202628:202628027406549`；可按 `:` 分割取两部分 |
| `Status` | int | 处理状态，与对应告警表的 Status 枚举一致（如文件节点关联木马告警，枚举与 `DescribeMalWareList.Status` 相同：4=待处理、8=文件已删除 等） |

## 调用链

```
DescribeAlarmIncidentNodes   → 拿事件节点列表（返回 IncidentId、TableName、Vertex[]{Vid, ParentVid, Type}）
DescribeVertexDetail (本接口) → 用 IncidentId + TableName + VertexIds 查选中节点的完整详情 + 告警
```

## 典型使用模式（workflow 脚本）

```python
# resp 是 DescribeAlarmIncidentNodes 的返回 dict
for inc in resp.get("IncidentNodes", []):
    incident_id = inc["IncidentId"]
    table_name  = inc["TableName"]
    vids        = [v["Vid"] for v in inc.get("Vertex", [])]
    # IncidentId 为空或节点列表为空表示无进程链数据，直接跳过
    if not incident_id or not vids:
        continue
    res = wf.exec([wf.PY, wf.T, "cwp", "DescribeVertexDetail",
        "--IncidentId", incident_id,
        "--TableName", table_name,
        "--VertexIds", json.dumps(vids),
        "--output", "json"])
    details = {d["VertexId"]: d for d in res.get("VertexDetails", [])}
```

## 解析注意事项

- **按 `Type` 分支解析**：不同类型的专属字段互斥，不要对所有节点都访问同一字段。
- **漏洞字段判空**：先判 `HttpContent` 是否非空，再读 `VulName`/`VulSrcIP`/`VulTime`，否则会误读零值。
- **`User` 字段格式**：SSH 节点的 `User` 是 `group:user`，显示时可按 `:` 分割取后半部分作为登录用户名。
- **`AlarmInfo` 可能为空数组**：节点无关联告警时 `AlarmInfo` 为 `[]`，勿假设非空。
- **与 `DescribeAlarmIncidentNodes` 的关系**：`DescribeAlarmIncidentNodes` 返回的 `Vertex[]` 只含 `ProcNamePrefix`/`CmdLinePrefix`（截断字符串）；本接口返回 `CmdLine`（完整命令行），需要完整命令行时必须调本接口。
