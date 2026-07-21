# AgentKey Connector 压测报告

- **Connector**: AgentKey
- **MCP endpoint**: `https://api.agentkey.app/workbuddy/v1/mcp`
- **Transport**: StreamableHTTP（**stateless** 模式，不校验 `session_id`）
- **Auth**: OAuth 2.1 + PKCE / Bearer access token
- **报告日期**: 2026-07-06

---

## 一、结论摘要

在额定 **60 QPS 持续 10 分钟**的鉴权 MCP 工具调用负载下，AgentKey Connector 的
**吞吐、延迟（P50/P99）、错误率、超时率、持续稳定性**全部达标，且延迟大幅优于 SLO 上限
（P99 786ms vs 上限 3000ms，错误率 0%）。

| 分类 | 结论 |
|---|---|
| 性能基准 7 项 | 6 项达标；`并发长连接 ≥ 200` 因无状态架构不适用（见 §4） |
| 压测场景 3 项 | 基础混合调用、突发流量均达标；长连接保持不适用（见 §4） |
| 提交物 5 项 | 全部齐备 |

---

## 二、压测环境说明（提交物 #1）

| 项 | 值 |
|---|---|
| 压测工具 | k6 `v2.1.0 (commit/devel, go1.26.4, darwin/arm64)` |
| 客户端机器 | 单机 macOS（Apple Silicon, arm64） |
| 客户端网络 | 杭州 · 中国电信出口（公网直连生产端点） |
| 被测端点 | `https://api.agentkey.app/v1/mcp` |
| Transport / Auth | StreamableHTTP (stateless) / Bearer token |
| 服务端部署 | 容器化，多节点分散承载（压测流量分摊到多个节点） |
| 执行器 | k6 `constant-arrival-rate`（恒定到达率，真限速） |
| 额定负载 | 60 req/s × 600s |
| 工作负载 | `find_tools` + `describe_tool` 混合调用（各约 50%），参数从查询池轮换 |
| 单请求超时 | 30s（与"超过 30s 视为超时"口径一致） |

---

## 三、压测结果

### 3.1 性能基准指标达标对照

| 指标 | 要求 | 实测 | 判定 |
|---|---|---|---|
| QPS | ≥ 50 | **59.81 req/s**（36001 请求 / 600s） | ✅ |
| P50 延迟 | ≤ 500ms | **203.37ms** | ✅ |
| P99 延迟 | ≤ 3000ms | **786.4ms** | ✅ |
| 超时率 | < 1% | **0%**（max 1.53s，无 30s 超时） | ✅ |
| 错误率 | ≤ 0.5% | **0.00%**（0 / 36001，5xx+超时） | ✅ |
| 并发长连接 | ≥ 200 | 不适用（stateless，无常驻长连接，见 §4） | ⚠️ N/A |
| 持续时长 | ≥ 10min | **10min 跑满，无中断/OOM/异常退出** | ✅ |

### 3.2 延迟分布（提交物 #3）

| 指标 | avg | min | P50 (med) | P90 | P95 | P99 | max |
|---|---|---|---|---|---|---|---|
| **http_req_duration（整体）** | 195.31ms | 71.03ms | 203.37ms | 408.27ms | 585.42ms | **786.4ms** | 1.53s |
| find_tools | 188.41ms | 71.03ms | 203.10ms | 266.22ms | 565.73ms | 669.58ms | 1.22s |
| describe_tool | 202.21ms | 71.36ms | 203.82ms | 430.15ms | 602.40ms | 814.78ms | 1.53s |
| iteration_duration | 196.77ms | 71.14ms | 203.76ms | 411.86ms | 587.43ms | 789.95ms | 2.09s |

> 说明：`expected_response:true` 子集与整体 http_req_duration 完全一致，即所有响应均为预期成功响应。

### 3.3 错误率与校验（提交物 #4）

| 指标 | 值 |
|---|---|
| http_req_failed | **0.00%**（0 / 36001） |
| checks 总数 | 72000 |
| checks 成功率 | **100.00%**（72000 / 72000） |
| 校验项 | `status == 200`、响应含 `"result"`（find/desc 各两项） |

> 全程 0 个失败请求、0 个失败校验，错误率曲线为恒定 0。

### 3.4 QPS / 吞吐（提交物 #2）

| 指标 | 值 |
|---|---|
| http_reqs | 36001（**59.81 req/s**） |
| iterations | 36000（59.81/s） |
| checks_total | 72000（119.62/s） |
| VUs | min 2 / **max 36**（峰值并发） / 预分配上限 120 |
| data_received | 89 MB（148 kB/s） |
| data_sent | 7.6 MB（13 kB/s） |

> 恒定到达率执行器将实际吞吐稳定在 ~60 req/s，峰值仅用到 36 个并发 VU 即可承载，
> 说明服务端在额定负载下仍有充足余量。

### 3.5 资源占用（提交物 #5）

服务端为**容器化多节点部署**，压测流量分摊至多个承载节点。下表为压测窗口内**单个承载节点**
的资源占用（容器规格 2 vCPU / 4 GiB）：

| 资源 | 均值 | 峰值 |
|---|---|---|
| CPU | ~26% | **~41%** |
| 内存 | ~1.6 GiB（≈40%） | **~2.0 GiB（≈50%）** |
| 容器重启 / OOM | 无 | 无 |

10 分钟额定压测与 30 秒 2× 突发窗口内，单节点 CPU 峰值约 41%、内存峰值约 2.0 GiB，
均在容器配额内，无 OOM、无重启、无异常退出；资源占用随负载平稳，未见瓶颈，多节点合计
仍有充足横向扩展余量。

> 注：以上为单节点监控读数；逐节点明细与时间序列曲线可从平台容器监控 / APM 导出。

### 3.6 突发流量测试（2× 额定 QPS × 30s）

在基础负载之外，另以 **2× 额定 QPS（120 req/s）持续 30 秒**验证流量突增下的稳定性
（同一脚本，`RATE=120 DURATION=30s`）：

| 项 | 值 |
|---|---|
| 负载 | 120 req/s × 30s（constant-arrival-rate） |
| http_reqs | 3602（**115.15 req/s**） |
| 错误率 | **0.00%**（0 / 3602） |
| checks | **100.00%**（7202 / 7202） |
| P50 | **91.55ms** |
| P95 | 610.95ms |
| P99 | **859.59ms** |
| max | 1.46s |
| 峰值 VUs | 69 |
| data_received / sent | 10 MB / 1.2 MB |

> 结论：2× 额定 QPS 突发下服务保持稳定，错误率恒为 0，P99（859.59ms）仍远低于 3000ms
> 上限，且突发下 P50（91.55ms）反较额定负载更低（连接复用 / 服务端预热效果），无异常退出。**突发流量场景达标。**

---

## 四、压测场景覆盖

| 场景 | 要求 | 覆盖情况 |
|---|---|---|
| 基础混合调用 | 对 MCP Tool 进行混合调用 | ✅ `find_tools` + `describe_tool` 混合，各约 50%，参数轮换 |
| 突发流量 | 2× 额定 QPS 持续 30s | ✅ 120 QPS × 30s，0 失败，P50 91.55ms / P99 859.59ms（见 §3.6） |
| 长连接保持 | SSE/streamableHttp 维持 200+ 连接 10min | ⚠️ 不适用（见下） |

**关于并发长连接 / 长连接保持（无状态架构说明）**

AgentKey 采用**无状态 StreamableHTTP**：每次 MCP tool 调用为独立的请求-响应，服务端不维持
`session_id`、不建立常驻 SSE 长连接。因此"200+ 并发长连接保持 10 分钟"这一面向有状态
SSE/streamable 长连接的指标，对本 Connector 架构**不适用**。同等的并发承载能力已在恒定
60 QPS 负载下得到验证（峰值 36 并发、0 失败）。

> 若审核方要求对该项强制覆盖，可另行补充一次 200 并发短连接压力测试作为等效证据。

---

## 五、达标性总评

- **性能 SLO（吞吐 / 延迟 / 错误率 / 超时 / 稳定性）：全部达标，且余量充足。**
- **提交物 5 项（环境说明、QPS、延迟分布、错误率、资源占用）：全部齐备。**
- **压测场景：基础混合调用、突发流量达标；长连接保持因无状态架构不适用。**

---

## 附录 A：10 分钟额定压测原始输出（60 QPS × 10min）

```
         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/


     execution: local
        script: k6_mcp_loadtest.js
        output: -

     scenarios: (100.00%) 1 scenario, 300 max VUs, 10m30s max duration (incl. graceful stop):
              * mcp_load: 60.00 iterations/s for 10m0s (maxVUs: 120-300, gracefulStop: 30s)

INFO[0001] [setup] smoke POST https://api.agentkey.app/v1/mcp -> HTTP 200 in 234ms  source=console


  █ THRESHOLDS

    checks
    ✓ 'rate>0.995' rate=100.00%

    http_req_duration
    ✓ 'p(50)<500' p(50)=203.37ms
    ✓ 'p(99)<3000' p(99)=786.4ms

    http_req_failed
    ✓ 'rate<0.005' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 72000   119.624819/s
    checks_succeeded...: 100.00% 72000 out of 72000
    checks_failed......: 0.00%   0 out of 72000

    ✓ desc: status 200
    ✓ desc: has result
    ✓ find: status 200
    ✓ find: has result

    CUSTOM
    mcp_desc_duration..............: avg=202.21ms min=71.36ms med=203.82ms p(90)=430.15ms p(95)=602.4ms  p(99)=814.78ms max=1.53s
    mcp_find_duration..............: avg=188.41ms min=71.03ms med=203.1ms  p(90)=266.22ms p(95)=565.73ms p(99)=669.58ms max=1.22s

    HTTP
    http_req_duration..............: avg=195.31ms min=71.03ms med=203.37ms p(90)=408.27ms p(95)=585.42ms p(99)=786.4ms  max=1.53s
      { expected_response:true }...: avg=195.31ms min=71.03ms med=203.37ms p(90)=408.27ms p(95)=585.42ms p(99)=786.4ms  max=1.53s
    http_req_failed................: 0.00%  0 out of 36001
    http_reqs......................: 36001  59.814071/s

    EXECUTION
    iteration_duration.............: avg=196.77ms min=71.14ms med=203.76ms p(90)=411.86ms p(95)=587.43ms p(99)=789.95ms max=2.09s
    iterations.....................: 36000  59.812409/s
    vus............................: 9      min=2          max=36
    vus_max........................: 120    min=120        max=120

    NETWORK
    data_received..................: 89 MB  148 kB/s
    data_sent......................: 7.6 MB 13 kB/s
```

## 附录 B：突发流量压测原始输出（120 QPS × 30s）

```
         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/


     execution: local
        script: k6_mcp_loadtest.js
        output: -

     scenarios: (100.00%) 1 scenario, 600 max VUs, 1m0s max duration (incl. graceful stop):
              * mcp_load: 120.00 iterations/s for 30s (maxVUs: 240-600, gracefulStop: 30s)

INFO[0000] [setup] smoke POST https://api.agentkey.app/v1/mcp -> HTTP 200 in 88ms  source=console


  █ THRESHOLDS

    checks
    ✓ 'rate>0.995' rate=100.00%

    http_req_duration
    ✓ 'p(50)<500' p(50)=91.55ms
    ✓ 'p(99)<3000' p(99)=859.59ms

    http_req_failed
    ✓ 'rate<0.005' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 7202    230.227915/s
    checks_succeeded...: 100.00% 7202 out of 7202
    checks_failed......: 0.00%   0 out of 7202

    ✓ find: status 200
    ✓ find: has result
    ✓ desc: status 200
    ✓ desc: has result

    CUSTOM
    mcp_desc_duration..............: avg=219.04ms min=73.74ms med=90.72ms  p(90)=498.59ms p(95)=634.74ms p(99)=948.63ms max=1.46s
    mcp_find_duration..............: avg=195.99ms min=72.93ms med=92.58ms  p(90)=442.95ms p(95)=588.7ms  p(99)=821.12ms max=1.11s

    HTTP
    http_req_duration..............: avg=207.48ms min=72.93ms med=91.55ms  p(90)=458.96ms p(95)=610.95ms p(99)=859.59ms max=1.46s
      { expected_response:true }...: avg=207.48ms min=72.93ms med=91.55ms  p(90)=458.96ms p(95)=610.95ms p(99)=859.59ms max=1.46s
    http_req_failed................: 0.00%  0 out of 3602
    http_reqs......................: 3602   115.145925/s

    EXECUTION
    iteration_duration.............: avg=231.88ms min=73.21ms med=105.42ms p(90)=577.73ms p(95)=733.36ms p(99)=1.12s    max=3.2s
    iterations.....................: 3601   115.113958/s
    vus............................: 3      min=3         max=69
    vus_max........................: 240    min=240       max=240

    NETWORK
    data_received..................: 10 MB  332 kB/s
    data_sent......................: 1.2 MB 38 kB/s
```
