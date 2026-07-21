# Level Vocab Bands — english-intensive-reader

> 本文件定义各档位词汇分级规则，供 AI 在标注 `new_words` 和 `vocab_notes.level_tag` 时使用。
> **核心原则**：只标注超出当前 level 词表的词汇为"生词"，不乱标（NEVER N3 / N4）。

---

## 一、词表档位定义

| 档位 | 对应考试 | 词汇量 | 说明 |
|------|---------|--------|------|
| `cet4` | 大学英语四级 | ~4500 词 | 高中词汇 + 大学基础词汇 |
| `cet6` | 大学英语六级 | ~6000 词 | CET4 词表 + 约 1500 扩展词 |
| `kaoyan` | 考研英语 | ~5500 词 | 与 CET6 有重叠，侧重学术词汇 |
| `foreign_press` | 外刊（经济学人等）| 无上限 | 标注低频词（词频排名 > 10000）|

---

## 二、生词标注规则

### 2.1 cet4 档位
- **标注为生词**：不在 CET4 词表中的词（含 CET6 / 考研 / 外刊专属词）
- **不标注**：CET4 词表内的词，无论词义是否熟悉
- **特殊处理**：高中词汇（如 beautiful / important）一律不标注

### 2.2 cet6 档位
- **标注为生词**：不在 CET4 + CET6 合并词表中的词
- **不标注**：CET4 词表内的词（即使用户可能不熟悉）
- **原则**：CET6 备考者应已掌握 CET4 词汇，不重复标注

### 2.3 kaoyan 档位
- **标注为生词**：不在考研词表中的词（考研词表 ≈ CET4 + CET6 + 学术词汇）
- **重点标注**：学术词汇（如 paradigm / empirical / discourse）
- **不标注**：日常高频词（即使不在考研词表，如 smartphone / selfie）

### 2.4 foreign_press 档位
- **标注为生词**：词频排名 > 10000 的低频词
- **重点标注**：专业术语、政治经济词汇、文化特定词汇
- **不标注**：常见词（即使不在 CET 词表，如 pandemic / algorithm）

---

## 三、auto 档位推断算法

```
统计文章中 CET4 词表外词汇占比（排除专有名词、数字、标点）：
  < 5%   → level = cet4
  5~15%  → level = cet6
  15~25% → level = kaoyan
  > 25%  → level = foreign_press
```

**实现参考**（`scripts/segment_sentences.py` 中调用）：
```python
def detect_level(text: str) -> str:
    words = tokenize(text)
    content_words = [w for w in words if not is_proper_noun(w) and not is_number(w)]
    cet4_ratio = sum(1 for w in content_words if w.lower() in CET4_VOCAB) / len(content_words)
    outside_cet4 = 1 - cet4_ratio
    if outside_cet4 < 0.05: return "cet4"
    elif outside_cet4 < 0.15: return "cet6"
    elif outside_cet4 < 0.25: return "kaoyan"
    else: return "foreign_press"
```

---

## 四、各档位核心词汇示例

### CET4 核心词（不标注为生词）
```
ability, achieve, affect, allow, although, analysis, apply, approach,
argue, aspect, assume, available, benefit, cause, challenge, change,
claim, clear, common, compare, complex, concern, consider, contain,
context, continue, control, create, culture, data, define, describe,
develop, different, discuss, effect, environment, establish, evidence,
example, explain, factor, feature, focus, follow, form, function,
general, global, group, growth, identify, impact, important, include,
increase, indicate, individual, influence, information, involve, issue,
knowledge, language, lead, level, likely, limit, major, manage, mean,
method, model, nature, necessary, need, number, occur, offer, often,
order, organization, original, part, pattern, perform, period, place,
policy, political, possible, present, problem, process, produce, provide,
public, purpose, question, range, reason, recent, refer, relate, report,
require, research, result, role, section, significant, similar, situation,
social, society, source, specific, structure, study, suggest, support,
system, theory, traditional, type, understand, use, value, various, view
```

### CET6 扩展词（cet6 档位不标注，cet4 档位标注）
```
abstract, accumulate, acknowledge, advocate, allocate, ambiguous,
anticipate, arbitrary, articulate, assert, assess, attribute, authentic,
bureaucracy, catalyst, coherent, collaborate, commodity, compensate,
complement, comprehensive, conceive, concurrent, constitute, constraint,
contemplate, contradict, controversial, conventional, coordinate,
correlate, criterion, critique, deduce, deliberate, demonstrate,
depict, derive, designate, differentiate, diminish, discriminate,
disparity, disrupt, diverse, elaborate, eliminate, emerge, empirical,
enhance, enumerate, evaluate, evolve, explicit, facilitate, fluctuate,
formulate, fundamental, generate, hierarchy, hypothesis, implement,
implicit, incorporate, inevitable, infrastructure, inherent, initiate,
innovate, integrate, interpret, intervene, justify, legitimate,
manipulate, mechanism, minimize, modify, monitor, motivate, negotiate,
objective, obtain, optimize, perceive, persist, phenomenon, predominant,
preliminary, prioritize, prohibit, promote, proportion, pursue,
rationalize, reinforce, relevant, resolve, restrict, retain, revise,
simulate, specify, stabilize, stimulate, substitute, sufficient,
summarize, supplement, sustain, synthesize, terminate, transform,
transition, transmit, undermine, utilize, validate, verify, visualize
```

### 考研专属学术词（kaoyan 档位重点标注）
```
abdicate, aberrant, abstruse, acrimonious, adumbrate, aesthetic,
ameliorate, anachronism, antithesis, apocryphal, approbation,
arcane, arduous, articulate, ascetic, assiduous, attenuate,
auspicious, axiom, belligerent, benevolent, bifurcate, candid,
capitulate, caustic, circumspect, cogent, commensurate, compendium,
conciliatory, concomitant, confound, congruent, conjecture, connotation,
contentious, contrite, copious, corroborate, credulous, cursory,
dearth, debilitate, decorum, deference, delineate, demagogue,
deprecate, derogatory, desultory, didactic, diffident, digress,
dilettante, discern, discrepancy, disparate, dissemble, dogmatic,
ebullient, eccentric, efficacious, egregious, elusive, emulate,
endemic, ephemeral, equivocal, erudite, esoteric, exacerbate,
exculpate, exemplary, exhaustive, exigent, expedient, extraneous,
fallacious, fastidious, fervent, flagrant, forthright, frugal,
garrulous, germane, grandiose, gratuitous, gregarious, guile,
hackneyed, hegemony, heretical, hypocritical, iconoclast, idiosyncratic,
impetuous, implacable, incisive, incongruous, indolent, inept,
inexorable, ingenuous, inimical, insidious, intransigent, inveterate,
irascible, laconic, loquacious, lucid, magnanimous, malevolent,
mendacious, meticulous, mitigate, mundane, nefarious, obdurate,
obsequious, obtuse, ominous, opaque, ostensible, ostentatious,
paradigm, parochial, pedantic, pernicious, pertinacious, phlegmatic,
plausible, pragmatic, precarious, precipitate, precocious, predilection,
preeminent, prescient, presumptuous, prevaricate, prodigal, profligate,
propitious, prudent, querulous, recalcitrant, reclusive, redolent,
refractory, repudiate, resilient, reticent, sagacious, sanctimonious,
sardonic, scrupulous, sedulous, sycophant, taciturn, tenacious,
terse, timorous, torpid, tractable, truculent, ubiquitous, vacuous,
venerate, verbose, vindictive, volatile, wary, zealous
```

---

## 五、词性标注规范

| 词性 | 标注格式 | 示例 |
|------|---------|------|
| 名词 | `n.` | pressing n. 压力 |
| 动词 | `v.` | advocate v. 倡导 |
| 形容词 | `adj.` | ubiquitous adj. 无处不在的 |
| 副词 | `adv.` | inevitably adv. 不可避免地 |
| 介词 | `prep.` | despite prep. 尽管 |
| 连词 | `conj.` | whereas conj. 然而 |
| 短语动词 | `phr.v.` | give rise to phr.v. 导致 |
| 名词短语 | `n.phr.` | in the wake of n.phr. 在...之后 |

---

## 六、搭配标注规范

每个生词提供 2~4 个高频搭配，格式：`词 + 搭配词`

```
pressing → pressing issue / pressing need / pressing concern / pressing matter
advocate → advocate for / advocate change / strong advocate
ubiquitous → ubiquitous presence / become ubiquitous / ubiquitous technology
```

**规则**：
- 搭配必须是真实高频搭配，不编造
- 优先选择文章中出现的搭配语境
- 考研 / 外刊档位额外标注正式书面语搭配

---

## 七、构词法标注规范（word_formation）

> 融合自 gaokao-english-tutor 的构词法教学法。
> 当生词可通过词根词缀拆解时，在 `vocab_notes[i].word_formation` 字段填写拆解说明，帮助用户举一反三。

### 7.1 常见前缀

| 前缀 | 含义 | 示例 |
|------|------|------|
| `un-` | 否定 | uncomfortable / unhappy / uncertain |
| `dis-` | 否定/分离 | disagree / disappear / disconnect |
| `im- / in- / ir-` | 否定 | impossible / incorrect / irregular |
| `re-` | 重复/再次 | rebuild / reconsider / rewrite |
| `over-` | 过度 | overestimate / overload / overlook |
| `under-` | 不足 | underestimate / undermine / understate |
| `co- / com- / con-` | 共同 | cooperate / combine / connect |
| `pre-` | 在前 | predict / prevent / prepare |
| `pro-` | 支持/向前 | promote / progress / propose |
| `anti-` | 反对 | antiwar / antibody / antisocial |

### 7.2 常见后缀

| 后缀 | 词性 | 示例 |
|------|------|------|
| `-tion / -sion` | n. | education / decision / conclusion |
| `-ment` | n. | development / achievement / movement |
| `-ness` | n. | happiness / darkness / weakness |
| `-ity / -ty` | n. | ability / reality / safety |
| `-ful` | adj. | helpful / powerful / meaningful |
| `-less` | adj. | careless / helpless / useless |
| `-able / -ible` | adj. | capable / flexible / responsible |
| `-ous / -ious` | adj. | famous / serious / ambitious |
| `-ly` | adv. | quickly / seriously / obviously |
| `-ize / -ise` | v. | modernize / realize / organize |
| `-ify` | v. | simplify / clarify / justify |
| `-en` | v. | strengthen / widen / deepen |

### 7.3 填写规则

- 格式：`前缀（含义）+ 词根（含义）+ 后缀（含义）`
- 示例：`uncomfortable` → `un-（否定）+ comfort（舒适）+ -able（形容词后缀）= 不舒服的`
- 无法拆解的词（如 book / run）→ 留空，不强行拆解
- 优先标注 CET6 / 考研 / 外刊档位的生词（CET4 基础词通常无需拆解）
