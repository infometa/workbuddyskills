# 医学英文术语发音处理

医学内容里全是英文缩写（EGFR、NSCLC、ORR…），TTS 引擎常读错——这是医学播客最刺耳的问题。本文档记录已验证的解决方案。

## 核心结论（实测得出）

| 方案 | 效果 | 结论 |
|------|------|------|
| 原样保留 `EGFR-TKI` | 引擎尝试当单词拼读，含糊不清 | ❌ |
| **字母间加空格 `E G F R T K I`** | **逐字母清晰朗读** | ✅ **采用** |
| 中文谐音 `衣871阿尔` | 不专业、易出错 | ❌ |
| SSML `<say-as interpret-as="characters">` | **edge-tts 不支持**，标签被当文本念出（实测 6.4s 的句子变 30.2s） | ❌ |

**实测数据**：`EGFR-TKI 治疗 NSCLC…` 原样 8.7s vs 空格分隔 10.4s——变慢即说明字母被逐个念出。

> ⚠️ **重要**：edge-tts 的 `Communicate` 只接受纯文本，参数仅 `text/voice/rate/volume/pitch`，**没有 SSML 支持**。不要试图用 `<say-as>`、`<break>`、`<emphasis>` 等标签，它们会被原样念出来。

## 脚本自动处理

`generate_podcast_v2.py` 内置 `fix_pronunciation()`，合成前自动转换，**无需手工在脚本 JSON 里加空格**。

### 处理规则
1. **组合缩写优先整体匹配**：`EGFR-TKI` → `E G F R T K I`（连字符去掉，否则 `E G F R-T K I` 会连读）
2. **统一转大写**：`QoL` → `Q O L`（小写字母易被含糊处理）
3. **词边界严格匹配**：用 `(?<![A-Za-z0-9])` 前后界定，避免误伤正常文本
4. **长词优先排序**：防止 `PD` 抢先匹配掉 `PD-L1`

### 词表分类

**ALWAYS_SPLIT**（逐字母朗读）——已收录 90+ 术语：
- 组合缩写：`EGFR-TKI` `ALK-TKI` `PD-L1` `PD-1` `CAR-T` `IL-6` `CTLA-4` 等（**必须排在单个缩写之前**）
- 靶点基因：`EGFR` `TKI` `ALK` `ROS1` `KRAS` `BRAF` `MET` `RET` `HER2` `NTRK` `VEGF` 等
- 疾病分型：`NSCLC` `SCLC` `RSV` `COPD` `ARDS` 等
- 疗效终点：`ORR` `PFS` `OS` `DCR` `DOR` `CR` `PR` `SD` `PD` `AE` `SAE` `TRAE` 等
- 检测技术：`NGS` `PCR` `ctDNA` `IHC` `FISH` `CT` `MRI` `PET` `ECOG` 等
- 机构指南：`CSCO` `NCCN` `ESMO` `ASCO` `FDA` `NMPA` `WHO` `GCP` 等

**KEEP_AS_WORD**（保持原样，本身是可读单词）：
`MELODY` `HARMONIE` `MEDLEY` `FLAURA` `ADAURA` `CheckMate` `KEYNOTE` `IMpower` `MARIPOSA` `PAPILLON`
> 研究名称是英文单词，逐字母念反而奇怪。新增研究名记得加进这个集合。

### 临时扩展词表
在脚本 JSON 顶层加：
```json
{
  "extra_split_terms": ["ADAURA2", "XYZ-123"],
  "keep_as_word_terms": ["SUNRISE", "HORIZON"]
}
```

### 预检查（强烈建议）
生成音频前先跑 dry-run，肉眼确认转换结果：
```bash
python generate_podcast_v2.py --input script.json --output x.mp3 --dry-run
```
输出示例：
```
今天聊 E G F R T K I 治疗 N S C L C，关注 O R R 和 P F S 数据。
MELODY 与 HARMONIE 研究是关键证据。      ← 研究名正确保留
```

如需完全关闭自动修正：加 `--no-fix`。

## 脚本撰写建议

除了自动处理，写脚本时还应：

1. **首次出现给全称**：「EGFR-TKI，也就是表皮生长因子受体酪氨酸激酶抑制剂」——让听众第一次就听懂
2. **后续可用中文简称**：反复念字母很累，第二次起可说「这类靶向药」
3. **数字读法留意**：`95% CI` 写成「95% 置信区间」；`p<0.001` 写成「p 值小于 0.001」；`V3.2025` 说成「2025 年第三版」
4. **剂量必须精确**：`50mg` 写成「50 毫克」，不可简化或改动
5. **能用中文就用中文**：`ORR` 可直接说「客观缓解率」，比念字母自然得多——**这是最优解**

> 原则：自动修正是兜底保障，脚本层面用中文表达才是最自然的。
