---
name: incident-investigation
description: 针对特定安全事件进行多产品关联调查，溯源攻击链路，评估影响范围
triggers:
  - "事件调查"
  - "入侵分析"
  - "应急响应"
  - "溯源分析"
  - "这个IP做了什么"
  - "查一下这个告警"
  - "incident investigation"
  - "investigate this alert"
products: [cwp, waf, cfw, bh]
template: references/template/incident_response.md
---

# 安全事件调查

## 适用场景

用户发现可疑安全事件（如入侵告警、异常 IP 活动、恶意文件等），需要跨产品关联调查，还原攻击链路，评估影响范围。适用于应急响应、入侵溯源、事件复盘等场景。

**前置条件**：需要用户提供调查线索（IP 地址、告警 ID、主机 UUID、时间范围等至少一项）。

## 重要参考
进行溯源时候，首先要考虑进程链上下文推测入侵源，主机安全旗舰版可以根据事件调查（DescribeAlarmIncidentNodes）查询进程时序链路。
DescribeAlarmIncidentNodes 接口必须在CWP旗舰版开通时才能使用。

## 执行脚本 - Phase 1: 初始摸排

根据用户提供的线索类型选择对应查询。以 IP 地址为例：

```python
import sys,os,json,glob
_R=os.environ.get("CODEBUDDY_PLUGIN_ROOT") or (glob.glob(os.path.expanduser("~/.workbuddy/plugins/marketplaces/*/plugins/tc-sec"))+[""])[0]
sys.path.insert(0,os.path.join(_R,"skills","tc-sec","scripts"))
import wf
T=wf.T; PY=wf.PY

start,end=wf.time_range(7,"d")
target_ip="<用户提供的可疑IP>"

cmds=[
    [PY,T,"cwp","DescribeBruteAttackList","--Filters",json.dumps([{"Key":"SrcIp","Values":[target_ip]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"cwp","DescribeAttackEvents","--Filters",json.dumps([{"Key":"SrcIp","Values":[target_ip]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"cwp","DescribeMalWareList","--Filters",json.dumps([{"Key":"Ip","Values":[target_ip]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"waf","DescribeAttackOverview","--FromTime",start,"--ToTime",end,"--output","json"],
    [PY,T,"cfw","DescribeBlockByIpTimesList","--StartTime",start,"--EndTime",end,"--Ip",target_ip,"--output","json"],
]

wf.out(wf.batch(cmds))
```

## 执行脚本 - Phase 2: 深入调查

根据 Phase 1 结果，对受影响主机进行深入检查：

```python
import sys,os,json,glob
_R=os.environ.get("CODEBUDDY_PLUGIN_ROOT") or (glob.glob(os.path.expanduser("~/.workbuddy/plugins/marketplaces/*/plugins/tc-sec"))+[""])[0]
sys.path.insert(0,os.path.join(_R,"skills","tc-sec","scripts"))
import wf
T=wf.T; PY=wf.PY

affected_uuid="<从Phase1结果中提取的受影响主机UUID>"

cmds=[
    [PY,T,"cwp","DescribeAssetProcessInfoList","--Filters",json.dumps([{"Key":"Uuid","Values":[affected_uuid]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"cwp","DescribeAssetPortInfoList","--Filters",json.dumps([{"Key":"Uuid","Values":[affected_uuid]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"cwp","DescribeAssetUserList","--Filters",json.dumps([{"Key":"Uuid","Values":[affected_uuid]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"cwp","DescribeReverseShellEvents","--Filters",json.dumps([{"Key":"Uuid","Values":[affected_uuid]}]),"--Limit","100","--Offset","0","--output","json"],
    [PY,T,"bh","DescribeOperationEvent","--Limit","50","--Offset","0","--output","json"],
]

wf.out(wf.batch(cmds))
```

## 执行脚本 - Phase 3: 进程链溯源（CWP 旗舰版）

从 Phase 1/2 拿到的 `Uuid`（**直接从告警事件字段取，不要另发 DescribeMachineList**）和时间范围，
批量调 `DescribeAlarmVertexId` → `DescribeAlarmIncidentNodes` → `DescribeVertexDetail` 构建进程链树。

```python
import sys,os,json,glob,subprocess
from concurrent.futures import ThreadPoolExecutor
_R=os.environ.get("CODEBUDDY_PLUGIN_ROOT") or (glob.glob(os.path.expanduser("~/.workbuddy/plugins/marketplaces/*/plugins/tc-sec"))+[""])[0]
sys.path.insert(0,os.path.join(_R,"skills","tc-sec","scripts"))
import wf
T=wf.T; PY=wf.PY
TU=os.path.join(_R,"skills","tc-sec","scripts","time_util.py")

uuid="<从Phase1告警事件的Uuid字段直接取>"
start,end=wf.time_range(7*24,"h")
ts_e=int(subprocess.check_output([PY,TU,"ts",end]).strip())
ts_s=int(subprocess.check_output([PY,TU,"ts",start]).strip())

r=wf.exec([PY,T,"cwp","DescribeAlarmVertexId","--Uuid",uuid,"--StartTime",str(ts_s),"--EndTime",str(ts_e),"--output","json"])
alarm_vids=r.get("AlarmVertexIds") or []

def query_chain(vid):
    return wf.exec([PY,T,"cwp","DescribeAlarmIncidentNodes","--Uuid",uuid,"--AlarmVid",vid,"--AlarmTime",str(ts_e),"--output","json"])

with ThreadPoolExecutor(max_workers=5) as ex:
    chain_results=list(ex.map(query_chain,alarm_vids[:20]))

incidents={}
for r in chain_results:
    for inc in r.get("IncidentNodes",[]):
        iid=inc.get("IncidentId")
        if iid and iid not in incidents:
            incidents[iid]=inc

for iid,inc in incidents.items():
    vids=[v["Vid"] for v in inc.get("Vertex",[]) if v.get("Vid")]
    if not vids: continue
    det=wf.exec([PY,T,"cwp","DescribeVertexDetail",
        "--IncidentId",iid,"--TableName",inc["TableName"],
        "--VertexIds",json.dumps(vids),"--output","json"])
    details={d["VertexId"]:d for d in det.get("VertexDetails",[])}
    # 构造父子映射，渲染 ASCII 树
    vid_map={v["Vid"]:v for v in inc.get("Vertex",[])}
    children={}
    roots=[]
    for v in inc.get("Vertex",[]):
        p=v.get("ParentVid","")
        if not p or p not in vid_map: roots.append(v["Vid"])
        else: children.setdefault(p,[]).append(v["Vid"])
    def render(vid,prefix="",is_last=True):
        v=vid_map.get(vid,{}); d=details.get(vid,{})
        connector="└───" if is_last else "├───"
        t=d.get("Time") or ""
        if t=="1970-01-01 08:00:00": t="(SSH)"
        tp=v.get("Type",0)
        if tp==1: label=f"{d.get('CmdLine') or v.get('CmdLinePrefix') or ''}"
        elif tp==4: label=f"SSH src={d.get('SrcIP','')} user={d.get('User','')}"
        elif tp==3: label=f"FILE {d.get('FilePath') or v.get('FilePathPrefix','')}"
        elif tp==2: label=f"NET {d.get('Address') or v.get('AddressPrefix','')}:{d.get('DstPort','')}"
        else: label=vid[:12]
        alarm=""
        for a in (d.get("AlarmInfo") or []):
            alarm+=f"  [Alarm:{a.get('AlarmId','')}]"
        line=f"{prefix}{connector}{t}  {label}{alarm}"
        kids=children.get(vid,[])
        child_prefix=prefix+("    " if is_last else "│   ")
        return line+"\n"+"".join(render(k,child_prefix,i==len(kids)-1) for i,k in enumerate(kids))
    tree="".join(render(r,is_last=i==len(roots)-1) for i,r in enumerate(roots))
    print(f"\n=== IncidentId={iid} TableName={inc['TableName']} Vertices={inc['VertexCount']} ===")
    print(tree)
```

> - `Uuid` 从告警事件字段直接取（DescribeMalWareList/DescribeBashEventsNew/DescribeReverseShellEvents 每条都带 `Uuid`），**无需查 DescribeMachineList**。
> - `DescribeAlarmVertexId` 比逐条算 AlarmVid 更简单，一次返回主机时间窗内所有告警 vid。
> - `AlarmTime` 传 `0` 时即使 vid 正确也会返回空进程链，**必须传落在时间窗内的时间戳**（传 EndTime 最稳）。
> - 旗舰版未开通时 `DescribeAlarmIncidentNodes` 返回 Error，如实标注即可。



Phase 1 每个查询结果需检查 TotalCount，若超过 Limit 用 `wf.page` 带 filter 分页补全（以下代码紧接 Phase 1 执行脚本）：

```python
res["cwp.DescribeBruteAttackList"]=wf.page("cwp","DescribeBruteAttackList","BruteAttackList",filters=[{"Key":"SrcIp","Values":[target_ip]}],workers=3)
res["cwp.DescribeAttackEvents"]=wf.page("cwp","DescribeAttackEvents","List",filters=[{"Key":"SrcIp","Values":[target_ip]}],workers=3)
res["cwp.DescribeMalWareList"]=wf.page("cwp","DescribeMalWareList","MalWareList",filters=[{"Key":"Ip","Values":[target_ip]}],workers=3)
```

## 输出格式

使用 `references/template/incident_response.md` 模板，重点填充：

- 事件概述：事件类型、发现时间、涉及资产
- 攻击时间线：按时间顺序还原攻击链路
- 影响范围：受影响的主机、服务、数据
- IoC 指标：攻击源 IP、恶意文件 Hash、异常进程等
- 处置建议：隔离、清除、加固、监控等措施

## 注意事项

- 此工作流为交互式，需要根据每阶段结果动态调整后续查询
- CFW DescribeBlockByIpTimesList 的 Ip 为必传参数，必须提供具体 IP
- WAF DescribeAttackOverview 的 FromTime/ToTime 为必传参数，该 API 返回全局攻击概览（不支持按 IP 过滤），用于提供同时段攻击背景上下文
- Phase 2 中 CWP 资产查询 API 均无必传参数（Filters 为可选），但建议通过 Uuid 过滤
- BH DescribeOperationEvent 返回全局操作事件（不支持按主机/IP 过滤），分析时需根据事件中的资产信息与调查目标进行关联匹配，过滤无关事件
- 报告中需明确区分"已确认事实"和"分析推断"
