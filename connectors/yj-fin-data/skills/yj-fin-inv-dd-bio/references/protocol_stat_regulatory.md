# 临床方案翻译、统计设计与监管路径框架

> 适用场景：用户要求翻译临床方案/研究者手册、解读统计设计、分析监管路径或 DDI 机制。

---

## 一、方案全文翻译术语表模板

翻译英文临床方案/研究者手册时，保持结构一致，附中英术语对照表：

| 英文 | 中文 | 备注 |
|------|------|------|
| Investigator's Brochure | 研究者手册 | IB |
| Informed Consent Form | 知情同意书 | ICF |
| Eligibility Criteria | 入选/排除标准 | — |
| Dose-Limiting Toxicity | 剂量限制性毒性 | DLT |
| Maximum Tolerated Dose | 最大耐受剂量 | MTD |
| Progression-Free Survival | 无进展生存期 | PFS |
| Overall Survival | 总生存期 | OS |
| Response Evaluation Criteria in Solid Tumors | 实体瘤疗效评价标准 | RECIST v1.1 |
| Independent Review Committee | 独立评审委员会 | IRC/BICR |

输出为结构化中文文本，保留原表格、章节编号、脚注。

---

## 二、统计设计解读维度

1. **α 分配与消耗**：期中分析消耗少量 α，最终分析保留大部分。Lan-DeMets / O'Brien-Fleming 边界控制整体一类错误。
2. **事件成熟度**：OS 终点需 65~70% 死亡事件成熟；样本量是为主要终点设计，次要终点可能效力不足。
3. **HR 解读**：HR<1 表示实验组风险更低；需结合 CI 与 p 值。
4. **随访时长**：长随访提高成熟度但延迟读出。
5. **非比例风险**：见 `clinical_readout_framework.md` 第三节。

---

## 三、监管路径分析

| 路径 | 要点 |
|------|------|
| IIT（研究者发起试验）→ NDA | 中国 NMPA 32 号令框架；IIT 数据可支撑注册但需补质量体系 |
| NMPA 优先审评/突破性疗法 | 加速通道条件 |
| FDA 资格认定 | Rare Pediatric Disease、Breakthrough、Fast Track |
| EU CTIS | 分步骤监测：试验启动状态 → 首例患者入组日期 |

**输出纪律**：监管结论对照官方法规，禁止推测未披露状态；本文件为方法论参考，非法律/监管意见。

---

## 四、DDI（药物相互作用）机制分析

- **CYP3A 底物/抑制剂**：经 CYP3A 代谢的药物与强 CYP3A 抑制剂联用需减量；与诱导剂联用降低暴露。
- **HLA-B*5801**：特定等位基因与严重皮肤不良反应相关，用药前需基因检测。
- 输出时需标注机制路径（酶/转运体/免疫遗传），并给出临床用药建议（需对照 NCCN/官方指南验证）。

---

## 五、置信度与来源

- 方案/法规类：🟢（官方方案文件、NMPA/FDA 公告）。
- DDI/机制类：🟡（文献+标签，需对照指南）。
- 未披露的监管状态：🔴 标注"待核实"。
