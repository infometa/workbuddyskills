# 每日行程契约

仅 mode=itinerary 读取，与[通用方案契约](plan-contract.md)合用；单项比选不加载本文件。

先查 travel-query.js；缺交通、酒店、景区时只执行回执给出的 completionRequests 批处理一次，并发查询且不重新提槽。只合并当前需求；不因只返回度假套餐就改成 selection，也不用套餐标题里的酒店/景点代替独立资源。补查仍无结果时明示缺项，不循环试查。

decisionFiles 的 itinerary-overview-v2 是行程首轮首页：categories 分为 transport、hotel、scenery、travel、sourcePlan，每类的 comparisons/focusRows 都是机械摘要；scheduleSignals 标出交通时刻、跨日、景点开放时间等已知/未知数量。先用交通抵离边界、住宿位置和景点开放信息排出每日节奏。只有某一类硬条件或排期字段在首页不足时，才读取 candidateGroups 中同 key 的 files；不默认展开所有类别，不读取旧 evidenceChunkFiles。接口原始攻略只作分析证据，不能覆盖最终 days，也不要求在最终 MD/HTML 中另设“接口参考行程”区块。

批处理回执已把主查询和补查的 decisionFiles、snapshotFilePaths 合并好。只读其 allowedReads，继续使用本行程契约，不再加载 selection 契约；一次写 plan，不对合并结果做第二轮全表复盘。

## 行程字段与约束

- `summary` 按回执 planLimits.summary，完整行程通常200–400字、动态硬上限500字。它概括总体节奏、主要选择和关键风险；详细每日说明仍放 days/interpretation，不机械截断，也不把所有资源逐项塞进 summary。
- `days` 必填，1–31天、日期连续、符合用户需求。每天仅 date（YYYY-MM-DD）、title（最多80字）、segments（1–16项）。不能固定兜底两三天。
- `segments` 仅 kind/ref/note/startTime/endTime；note 必填、最多500字，解释安排与取舍，资源事实由程序回填。
- transport/back 引用 flight/train/bus，分别为去程/返程；hotel 引用 hotel；morning/afternoon/daytime/optional 引用 scenery/travel。night 可引用景点或仅安排休息；tip/food 可不带 ref，但不补造商家事实。
- 当前为单目的地，最多一段去程和一段返程；多城市或复杂联程先确认范围、拆独立子行程，不硬塞。
- 每日安排要使用已返回且本次需要的交通、住宿、景点。可选 `resourceExceptions` 最多3项，各仅 {category,reason}，category 为 hotel/scenery/transport，reason 最多500字，仅引用用户明确已安排或不需要的部分；“未返回/赶时间”不是例外。例外不隐藏已返回资源。

## 日期与时间

去返程核对实际城市/机场/车站与用户出发地，跨日到达按接口日期，不能只看时钟；不一致的接驳时间和费用需明确确认。逐日核对开放时间、建议游玩时长、片区、住宿与活动量。

startTime/endTime 是拟安排活动时段，格式 HH:mm；transport/back 禁止填写，班次时刻只取接口。上午/下午/晚上标签要与时刻一致；跨午夜活动拆到次日或暂列备选，不能伪造营业时间。

首日每个活动都检查抵达时间，末日活动在返程前结束并留出接驳余量。缺日期/时刻的相关活动只列 optional 或先补查，不能删时间字段规避校验；接驳未知不能保证赶得上。备选保留在详细计划，不进入确定游玩路线。

## 结构示例

此例假设用户已说明带孩子、首日晚上到、次日返程。按真实证据和需求替换全部内容：

```json
{
  "version": 1,
  "snapshotIds": ["本次接口快照的完整 snapshotId"],
  "mode": "itinerary",
  "userRequest": "9月5日到6日带孩子出游，第一天晚上到，想早点休息，第二天玩完再回来。",
  "summary": "首日以入住休息为主，核心游玩留到次日；预订前先确认机场接驳。",
  "rationales": [{"text": "晚间抵达后不再安排白天景点，给同行孩子留出休息时间。", "refs": ["去程资源ref"]}],
  "confirmations": [{"text": "机场接驳耗时和酒店晚到入住安排待确认。", "refs": []}],
  "interpretation": {
    "customerFocus": "您希望带孩子玩得轻松些，第一天又是晚上才到，我更建议先入住休息，把游玩留到第二天。",
    "sections": [{"title": "第一晚先休息，第二天再玩", "paragraphs": [{"text": "您第一天晚上才到，之后还要去酒店。第一晚不再加景点，能少赶一段路；去酒店要多久，这次还没有查到，预订前需要确认。", "refs": ["去程资源ref"]}]}],
    "nextSteps": [{"text": "先确认机场到酒店怎么走，以及酒店能否办理晚到入住，再决定是否预订。", "refs": []}]
  },
  "days": [
    {"date": "2026-09-05", "title": "抵达与入住", "segments": [
      {"kind": "transport", "ref": "去程资源ref", "note": "抵达后前往酒店，接驳耗时待确认。"},
      {"kind": "hotel", "ref": "酒店资源ref", "note": "提前确认晚到入住。"},
      {"kind": "night", "note": "入住后休息，不再安排额外景点。"}
    ]},
    {"date": "2026-09-06", "title": "核心景点与返程", "segments": [
      {"kind": "morning", "ref": "景点资源ref", "startTime": "09:00", "endTime": "11:00", "note": "这是拟安排时段，预约和接驳仍需确认。"},
      {"kind": "back", "ref": "返程资源ref", "note": "按班次时间倒推前往机场的出发时间。"}
    ]}
  ]
}
```

HTML与完整MD保持“一句话建议、推荐节奏、为什么这样排、预算边界、下单前确认、每日详细计划”、完整资源区和详细专家解读，不自行改变排版。聊天只展示行程节奏、主要预订选择和必要提醒，不再复制全部资源。预算区逐项展示起价，不汇总未知口径。
