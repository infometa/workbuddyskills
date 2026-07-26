# -*- coding: utf-8 -*-
"""
signals_config.py — 可配置中心（光模块信号监控）

本文件是系统唯一的「可配置项」入口。监控指标与因果链的发现由
**老梨研究院（司天监）** 负责，产出后通过本文件注入系统。本系统只负责「用」。

字段说明：
  name            信号名（与 Layer1 监控表、因果链节点一致）
  end             所属端（供给 / 需求 / 技术）
  chain           归属因果链（供给 / 需求 / 技术）
  base_sign       触发时的方向（利好景气度 +1 / 利空 -1）—— 即 Layer1 解读列
  distance        距离（浅 1.0 / 中 0.6 / 深 0.3）—— 时间新鲜度折扣
  trigger         触发规则
  source          数据源
  interpretation  解读（base_sign 的依据）

前序/后序判定（动态，非固定字段）：
  每次运行时，Layer2 对每条链找出触发的信号中 chain_index 最大者（最靠近结局），
  该信号 = 后序（进景气度），之前的触发信号 = 前序（不进景气度）。
  CHAINS 字典的节点顺序即 chain_index 依据。
"""
from __future__ import annotations

# ── 距离折扣：时间新鲜度（离现在多久） ───────────────────────────────
DISTANCE_DISCOUNT = {"浅": 1.0, "中": 0.6, "深": 0.3}

# ── 模式因子：数据源精度（影响置信度 S，不影响景气度水位） ──────────────
MODE_FACTOR = {"专业": 1.0, "部分": 0.8, "纯网": 0.6}

# ── R：命中率可靠度 = f(累计期数) ──
def r_from_periods(n: int) -> float:
    """累计运行期数 → R 值。每跑一期 +1，不管预测对没对。"""
    if n < 8:
        return 0.3
    if n <= 24:
        return 0.6
    return 0.9

# ── 置信度档位阈值 ──
CONF_HIGH = 0.66   # > 0.66 → 高
CONF_MID = 0.33    # > 0.33 → 中；否则低

# ── 三条因果链（节点顺序 = 时间由远及近） ──
CHAINS = {
    "供给": ["MOCVD设备订单", "InP衬底价格/供给", "硅光晶圆产能与良率",
            "EML缺口(200G)", "DSP交期(200G)", "光芯片价格(25G/50G/100G)",
            "VCSEL产能利用率"],
    "需求": ["数据中心新建项目数", "800G/1.6T导入进度", "英伟达GPU季度出货",
            "四大云厂合计Capex", "光模块出口量(800G/1.6T)", "旭创/新易盛营收增速"],
    "技术": ["1.6T/3.2T路线进展", "CPO交换机商用时间表", "LPO商用进度",
            "硅光渗透率", "线性驱动方案", "主要云厂CPO部署口径"],
}

# ── 19 个监控信号（Layer1 全集） ──
# base_sign 默认值由老梨研究院判定；此处为可运行的初始假设。
SIGNALS = [
    # ── 供给端（7） ──
    {"name": "MOCVD设备订单", "end": "供给", "chain": "供给",
     "base_sign": -1, "distance": "深",
     "trigger": "增速 ≥ 30% 或转负", "source": "设备商公告",
     "interpretation": "扩产第一道门；扩产→远期供给增→利空景气"},
    {"name": "InP衬底价格/供给", "end": "供给", "chain": "供给",
     "base_sign": 1, "distance": "深",
     "trigger": "涨价 ≥ 10% 或产能释放", "source": "衬底厂商报价",
     "interpretation": "EML 原材料瓶颈；涨价→紧缺→利好景气"},
    {"name": "硅光晶圆产能与良率", "end": "供给", "chain": "供给",
     "base_sign": -1, "distance": "深",
     "trigger": "良率突破或扩产", "source": "代工厂季报",
     "interpretation": "良率突破→供给能力提升→缓解紧缺→利空景气"},
    {"name": "EML缺口(200G)", "end": "供给", "chain": "供给",
     "base_sign": -1, "distance": "中",
     "trigger": "缺口 ≥ 10% 或转盈余", "source": "万得",
     "interpretation": "缺口缩→1.6T 释放→供给缓解→利空景气"},
    {"name": "DSP交期(200G)", "end": "供给", "chain": "供给",
     "base_sign": -1, "distance": "中",
     "trigger": "变动 ≥ 20%", "source": "万得 / 供应链",
     "interpretation": "交期缩→产能缓解→利空景气"},
    {"name": "光芯片价格(25G/50G/100G)", "end": "供给", "chain": "供给",
     "base_sign": 1, "distance": "中",
     "trigger": "环比 ≥ 5%", "source": "渠道报价",
     "interpretation": "涨→紧缺→利好景气"},
    {"name": "VCSEL产能利用率", "end": "供给", "chain": "供给",
     "base_sign": 1, "distance": "中",
     "trigger": "利用率 ≥ 90% 或 < 70%", "source": "芯片厂季报",
     "interpretation": ">90%→紧张→利好景气"},

    # ── 需求端（6） ──
    {"name": "数据中心新建项目数", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "浅",
     "trigger": "新增 ≥ 5 座或停滞", "source": "行业调研",
     "interpretation": "增→中期确定→利好景气"},
    {"name": "800G/1.6T导入进度", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "中",
     "trigger": "首发或规模上量", "source": "产业链调研",
     "interpretation": "结构升级→利好景气"},
    {"name": "英伟达GPU季度出货", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "浅",
     "trigger": "QoQ ≥ 10%", "source": "万得（NVDA.O）",
     "interpretation": "增→配套光模块涨→利好景气"},
    {"name": "四大云厂合计Capex", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "浅",
     "trigger": "YoY ≥ 15%", "source": "万得（AMZN/MSFT/META/GOOGL）",
     "interpretation": "增→需求强→利好景气"},
    {"name": "光模块出口量(800G/1.6T)", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "浅",
     "trigger": "YoY ≥ 20%", "source": "万得 EDB",
     "interpretation": "月度直接数据→需求强→利好景气"},
    {"name": "旭创/新易盛营收增速", "end": "需求", "chain": "需求",
     "base_sign": 1, "distance": "浅",
     "trigger": "超/低于预期 ≥ 10%", "source": "万得（300308/300502）",
     "interpretation": "营收替代订单→利好景气"},

    # ── 技术端（6） ──
    {"name": "1.6T/3.2T路线进展", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "深",
     "trigger": "路线切换", "source": "IEEE / OIF",
     "interpretation": "路线切换→格局变动→利空现有 incumbent"},
    {"name": "CPO交换机商用时间表", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "中",
     "trigger": "挪 ≥ 1 季度", "source": "行业会议 / 厂商公告",
     "interpretation": "往前挪→威胁加大→利空景气"},
    {"name": "LPO商用进度", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "中",
     "trigger": "量产或标准冻结", "source": "行业标准组织",
     "interpretation": "上量→切 DSP→利空现有格局"},
    {"name": "硅光渗透率", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "中",
     "trigger": "跨 20% / 50%", "source": "产业链调研",
     "interpretation": "加速→路线切换→利空 incumbent"},
    {"name": "线性驱动方案", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "中",
     "trigger": "选型表态", "source": "行业白皮书",
     "interpretation": "标准化突破→加速替代→利空现有格局"},
    {"name": "主要云厂CPO部署口径", "end": "技术", "chain": "技术",
     "base_sign": -1, "distance": "中",
     "trigger": "口风转向", "source": "业绩会纪要",
     "interpretation": "远期变近期→威胁兑现→利空景气"},
]

# 索引：name → signal dict
SIGNAL_INDEX = {s["name"]: s for s in SIGNALS}


def chain_index(name: str) -> int:
    """返回信号在其因果链中的位置索引（0=最远/源头，越大越靠近结局）。
    找不到返回 -1。"""
    s = SIGNAL_INDEX.get(name)
    if not s:
        return -1
    chain_nodes = CHAINS.get(s["chain"], [])
    return chain_nodes.index(name) if name in chain_nodes else -1


def resolve(name: str) -> dict:
    """查信号定义；找不到返回 None。"""
    return SIGNAL_INDEX.get(name)
