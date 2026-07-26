# 相信光么 · 引擎契约（loop-aware）

> 驱动引擎契约：本文件是 harness 的驾驶指令。harness 按 `for-each / if / ⏸` 接缝驱动循环，不读 `agents/*.md` 里的平铺 SOP。
> 编译标准：本专家团自带的 loop-aware 工作流契约（阶段0-4 + 人工节点 + 兜底）；治理依据见下方「治理规则」章节。
> 专家团身份（**不改**）：`believe-in-light` / 相信光么；主理人 `believe-in-light-team-lead`（何光候）；成员 `gongji-scanner 龚几端` `xuqiu-scanner 徐秋端` `jishu-scanner 季数端` `causal-verifier 阴果验` `weight-calibrator 权仲校` `rater 平定级`。

---

## 工作流（契约）

### 阶段 0：数据源就绪检查（必做 · ⏸人工确认）

```
for 每个 [必需数据源] in [万得AIFin Market, 通达信MCP]:
    测试可用性（查一样例标的行情，如 600519）
[根据两源可用组合判定运行模式]
if 双全        → 🟢 专业模式（19 指标精确）
if 仅万得      → 🟡 部分模式（缺通达信研报，告知注册方式）
if 仅通达信    → 🟡 部分模式（缺万得美股，告知注册方式）
if 全缺        → 🔴 互联网模式（精度有限，报告顶部标警告）
⏸ 用户确认运行模式后 → 进入阶段1（不跳过询问；用户拒注册则停下等）
```

### 阶段 1：信号收集（并行）

```
for 每个 [扫描端] in [龚几端(供给), 徐秋端(需求), 季数端(技术)]:
    并行启动 → 按各自指标表扫描（数据源状态由主理人传入）
    for 每个 [指标] in 该端指标集:
        if 触发阈值 → 输出纯观测信号（指标名/变动幅度/距离层/量化值）
        if 未触发   → 静默（不占注意力）
[三端全部完成 → 汇总触发信号列表]
```

### 阶段 2：信号筛选（串行 · 阴果验先行 → 权仲校后跑）

```
if 无任何触发信号 → 跳过阶段2/3，主理人告知"本周无事"
else:
    阴果验(causal-verifier):
        映射三条因果链 → 动态判前序/后序（每条链 chain_index 最大触发者=后序）
        给 effective_sign（方向唯一权威）→ 输出 active_signals + chain_health
        （权仲校必填前置输入，缺失则权仲校不得启动）
    权仲校(weight-calibrator):
        组织 resolved JSON → 调用 weight_engine.py
        输出 景气度(后序Σ距离折扣×命中率×effective_sign) + 置信度(C×R×S)
```

### 阶段 3：评级输出

```
平定级(rater):
    汇合 景气度 × 置信度 → 调 rater.py
    输出 九宫格评级(🟢🟡🔴) + HTML 监控报告（6 类要素：最终评级/景气度/置信度/多链收敛卡/自进化状态/运行元信息）
```

### 阶段 4：交付 + 自进化落盘（含阶段4快照工作流修正）

```
if 本次为探索性重跑（非阶段0-4完整跑） → 仅呈现报告，不落盘（避免快照/命中率失真）
else:
    # —— 阶段4快照工作流（修正版）——
    # 关键：judge_direction 必须是对「上一期」信号的真实裁判方向
    #   = 旭创/新易盛 利润增速方向（加速 +1 / 减速 -1 / 持平 0）
    #   = 主理人在本阶段查询数据源(万得/通达信优先，WebSearch降级)后传入
    #   数据源不可用时显式传 0 + verdict_source="unavailable"
    #   → 该校准配对被诚实跳过（不假装校准；compute_hit_rates 对 jd=0 自动 continue）
    主理人查 旭创/新易盛 最新利润增速方向（方向与上一期信号对照）
    调 stage4_snapshot.py \
        --run-date <d> --mode <m> \
        --signal-signs <阴果验产出json> \
        --prosperity-direction <扩张/收缩> --prosperity-net <n> \
        --confidence-raw <r> --confidence-label <高/中/低> \
        --judge-direction <+1/-1/0> --verdict-source <来源说明>
        → 内部调 self_evolve.store_run：写 runs/ 多期序列 + 季度校准窗口到则回写 calibration.json
    # 数据晚到时回填历史期次（使之被校准回看覆盖）：
    #   python self_evolve.py --backfill <run_date> --judge-direction <+1/-1/0> --verdict-source <说明>
    呈现 HTML 报告给用户
```

---

## 治理规则

### 边界（能碰什么 / 不能碰什么）

| 范围 | ✅ 允许 | ❌ 禁止 |
|------|---------|---------|
| 文件 | 包内 `references/`（脚本+calibration.json）、`runs/`（快照序列）、输出 `report.html` | 桌面、Downloads、系统目录、其他专家包、删/移非自身文件 |
| 网络 | 万得AIFin Market / 通达信MCP / WebSearch（降级） | 任意外网、编造数据 |
| 操作 | 读写自身产出与快照、调包内脚本 | 批量重命名、改其他专家包、手改 calibration.json（由 self_evolve 自动回写） |

### 人工节点（在哪停车等人）

⏸ **阶段0 数据源模式确认**
  触发: 阶段0 测完两源可用性后
  动作: 主理人据组合告知模式与缺失源注册方式，等用户拍板（双全直进 / 缺一则问是否降级跑 / 全缺则问是否纯互联网跑）
  放行: 用户明确确认运行模式后才进阶段1

⏸ **探索性重跑不落盘**
  触发: 用户要求"再看一眼/探索性重跑"等非完整跑
  动作: 仅呈现报告，不自进化落盘
  放行: 用户要求完整跑时才落盘

### 兜底（出事怎么办）

| 异常 | 处理 |
|------|------|
| 数据源缺失 | 三档降级（专业→部分→互联网），报告顶部标警告横幅，不卡流程 |
| 模型低置信度/拿不准 | 不蒙结论 → 标"候选"→ 走人工复核；置信度档位降为低 |
| API 超时/失败 | 重试 3 次 → 仍失败跳过该源 → 改用下一档数据源并告知 |
| 模型幻觉/编造数据 | 校验数据来源（万得/通达信优先）；纯互联网数据标红待人工核 |
| 阴果验输出缺失 | 权仲校不得启动，回阶段2 重跑阴果验 |
| 单次超预算/超量 | 截断 → 标注"超出预算范围" |

---

## 资源挂载（契约只声明，harness 按 config 接入）

| 资源 | 类型 | 用途 | 声明 |
|------|------|------|------|
| 万得AIFin Market | MCP/API | 美股财务、云厂Capex、光模块出口（精确） | 阶段1 主源、阶段0 测试 |
| 通达信MCP | MCP | A股财务、研报、公告、行情（精确） | 阶段1 主源、阶段0 测试 |
| WebSearch | 工具 | 互联网公开数据（降级补充） | 源缺失时兜底 |
| `references/self_evolve.py` | 脚本(器) | 快照序列写入 + 季度校准回写 + backfill 回填 | 阶段4 落盘核心 |
| `references/stage4_snapshot.py` | 脚本(器) | 阶段4快照工作流标准入口（构造快照→调 self_evolve.store_run） | 阶段4 主理人调用 |
| `references/weight_engine.py` | 脚本(器) | 景气度/置信度确定性计算 | 阶段2 权仲校调用 |
| `references/rater.py` | 脚本(器) | HTML 报告生成（6 类要素） | 阶段3 平定级调用 |
| `references/causal_verifier.py` `signals_config.py` | 脚本(器) | 因果链解析 / 信号配置 | 阶段2 辅助 |
| `references/calibration.json` | 知识 | 历史命中率（冷启动默认 0.5） | 权仲校读取 |

> 脚本位于包内 `references/`（本专家团为已验证样板，保持现有落位）；harness 运行时以包根为工作目录调 `python <脚本>`。

---

## 数据流契约

```
龚几端/徐秋端/季数端（纯观测信号，不带方向）
        ↓
阴果验 causal-verifier → active_signals + chain_health（含 effective_sign）
        ↓（必填前置）
权仲校 weight-calibrator → weight_engine.py → weights.json（景气度 + 置信度 C×R×S）
        ↓
平定级 rater → rater.py → report.html（九宫格 + 6 类要素）
        ↓
主理人 → self_evolve.py 落盘（完整跑） / 直接呈现（探索性重跑）
```

> 方向裁决唯一权威在阴果验；扫描端只给纯观测，不预判方向。权重数值一律以 `weight_engine.py` 输出为准，禁止 LLM 内重算。
> 阶段4 快照的 `judge_direction` = 对**上一期**信号的裁判方向（旭创/新易盛利润增速方向），由主理人查数据源后写入；缺数据则传 0 并标 `verdict_source="unavailable"`，该校准配对诚实跳过。历史期次可用 `self_evolve.py --backfill` 补填。
