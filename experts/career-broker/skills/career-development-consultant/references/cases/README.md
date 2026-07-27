# 案例库 v1.0

> **位置**：`skills/career-development-consultant/references/cases/`
> **用途**：教练 skill 在 T2（案例陪伴）调用时召回案例的真源
> **状态**：v1.0 草稿（7 条种子案例，等待补充）

---

## 文件清单

| 文件 | 角色 | 维护频率 |
|---|---|---|
| `all_cases.json` | 所有案例的真源 | 高频追加 |
| `tag_definitions.md` | 受控标签词表（5 个轴） | 低频扩展 |
| `README.md`（本文件） | 使用说明 | 极少改 |

---

## 设计原则

### 1. 单文件 + 双轴标签（不是多文件分库）

**为什么不按场景分多个文件？**
- 一条案例往往同时落在多个场景上（如"3-5 年瓶颈期 + 跨BG活水"）
- 多文件分库 → 同一条案例要么放多份（冗余），要么放一份漏召回
- 单文件 + 多轴标签 → 自然解决

### 2. 5 个标签轴

详见 `tag_definitions.md`：
- `stage_tags`：阶段轴（用户在哪个司龄/角色阶段）
- `event_tags`：事件轴（用户正在经历什么）
- `scene_tags`：场景轴（用户的卡点类型，5 维度）
- `persona_tags`：画像轴（用户的个性/态度）
- `span_tags`：跨度轴（案例的转型跨度）

### 3. 受控词表，不允许自由文本

- 所有标签必须从 `tag_definitions.md` 选
- 遇到新场景 → 先扩 `tag_definitions.md`，再去打标
- **不允许在 `all_cases.json` 里写自由文本标签**

---

## 召回逻辑（教练流 T2 调用时）

教练在对话中推断用户当前状态后，按精度从高到低降级：

```
精度 1（最高）: stage + scene + persona 三轴交集
精度 2:        scene + persona 双轴交集
精度 3:        event + persona 双轴交集
精度 4:        scene 单轴
精度 5（兜底）: 全库 summary 相似度
```

**关键原则**：永远要给出"虽然不太一样、但也许有启发"的内容——不要因为没精确命中就空召回。

---

## 与旧文件的关系（兼容期）

当前并存 3 个相关文件，**不删旧的**，避免破坏 `search_cases.py`：

| 文件 | 状态 | 动作 |
|---|---|---|
| `skills/career-broker-core/references/case-library.json` | ⚠️ 旧主源（7 条平铺数据）| 保留，将来废弃 |
| `skills/career-broker-core/references/case-library-scenario-index.json` | ⚠️ 旧场景反查表 | 保留，将来废弃 |
| `skills/career-development-consultant/references/cases/all_cases.json` | ✅ 新主源 | **新文件以此为准** |
| `skills/career-development-consultant/references/cases/tag_definitions.md` | ✅ 新词表 | **打标必读** |
| `scripts/search_cases.py` | ⚠️ 还在读旧 case-library.json | 下一轮决定是否改 |

**迁移路径**：
- 阶段 1（当前）：新旧并存，新文件作为讨论/扩充的工作面
- 阶段 2：改 `search_cases.py` 读 `all_cases.json`，按 5 轴召回
- 阶段 3：废弃旧 `case-library.json` 和 `scenario-index.json`

---

## 怎么加新案例

1. 打开 `tag_definitions.md`，确认 5 个轴的标签是否够用
   - 不够 → 先在词表加新标签，再去 §2
2. 打开 `all_cases.json`，复制一条案例作为模板
3. 填写：
   - `case_id`（命名规范见词表 §6）
   - `code_name`（脱敏代号，不允许真名）
   - `is_real`（true=一手访谈 / false=二手脑补）
   - 5 个轴的标签（每个轴至少 1 个）
   - `basic`（level / tenure_years / domain_path）
   - `story.before / during / after`
   - `key_quotes`（一手访谈才有，二手脑补留空数组）
   - `advice.scene_specific / anti_consensus / by_persona`
   - `summary_30char`（30 字内一句话概括，给召回兜底用）
4. 如标记低质量，加 `_quality_note` 字段说明

---

## 当前案例分布（v1.0）

**总数**：7 条（3 真访谈 + 4 二手脑补）

| 阶段轴 | 案例数 |
|---|---|
| 3-5年瓶颈期 | 1 |
| 5-10年中坚期 | 3 |
| 10年+资深期 | 3 |

**严重缺口**：
- ⚠️ `新人前90天` / `转正前后` 0 条
- ⚠️ `1-2年成长期` 0 条
- ⚠️ `产假休假回归` 0 条
- ⚠️ `🚪被卡型` 画像 0 条
- ⚠️ `🍃混合型` 画像 0 条

→ 后续访谈/脑补优先补这些缺口。
