# 默认音色池：按场景选，不随机

**不要用 `--random-voice`，也不要每次现搜。** 下面 20 个是 Breeze 官方公共音色（`voice_type = default`、`visibility = public`），任何账户都能直接用。先按场景查表，命中即用；表里没有合适项时才去 `voice list` 找。

选音色的顺序：

1. 用户明确指定 → 核实后直接用
2. 用户描述了场景（"讲题的""播客感的"）→ 查下面的场景表
3. 什么都没说 → 用「知识讲解」那一对，按内容语种定男声或女声
4. 都不合适 → `breeze voice list --voice-type default --language zh --gender <male|female> --page-size 100 --output json` 再挑，并向用户说明为什么没用默认池

## 场景 → 音色映射

| 场景 | 男声 | 女声 |
| --- | --- | --- |
| 知识讲解 / 课程 / 讲题 | 深思先生 | 知绘小姐 |
| 企业宣传 / 品牌片 | 铁血守望者 | 清雅引路人 |
| 新闻 / 严肃说明 / 政策解读 | 幕府谋臣 | 香农小姐 |
| 纪录片 / 人文旁白 | 麦田 | 青史执笔人 |
| 播客 / 访谈 / 闲聊 | 温谈 | 邻家暖心 |
| 电商 / 快节奏口播 / 资讯 | 市井百晓生 | 率真生活家 |
| 有声书 / 文学 / 故事 | 纸影说书匠 | 午夜留声机 |
| 健康 / 运动 / 冥想引导 | 暖心健身教练 | 静心向导 |
| 科技 / AI 助理 / 产品演示 | 虚空执事 | 干练安全官 |
| 儿童 / 亲子 / 动画 | 灵动小满 | 灵动雨珠 |

## 男声（10）

| 音色 | voice_id | 年龄感 | 音色标签 | 适合 |
| --- | --- | --- | --- | --- |
| 深思先生 | `voc_reys5un5t4ed` | 成年 | calm, measured, articulate | 偏低、温和清楚的普通话男声，通用讲解首选 |
| 铁血守望者 | `voc_pd36639843sk` | 中年 | authoritative, steady, passionate | 浑厚有阅历感，宣传片、史诗叙事 |
| 幕府谋臣 | `voc_srr3pqyvrajd` | 中年 | authoritative, calm, precise | 克制、精准，新闻与严肃说明 |
| 麦田 | `voc_xhfrasjwjgad` | 中年 | warm, sincere, reflective | 温柔深沉，文学朗诵与抒情旁白 |
| 温谈 | `voc_4zu675fmv6g5` | 中年 | friendly, steady | 平实亲切，播客与对谈 |
| 市井百晓生 | `voc_c58f48zyezh4` | 青年 | bright, rhythmic, passionate | 语速快而清楚，适合交代复杂信息 |
| 纸影说书匠 | `voc_7bp6w9rf637t` | 年长 | precise, rhythmic, refined | 咬字讲究，有说书感 |
| 暖心健身教练 | `voc_pyum6u5hhakh` | 青年 | warm, articulate, measured | 磁性男中音，鼓励感，健康与运动 |
| 虚空执事 | `voc_w45se56jp6xm` | 青年 | bright, precise, refined | 规整、精确停顿，AI 助理与科技演示 |
| 灵动小满 | `voc_nbvjkwrm633w` | 儿童 | bright, precise, articulate | 清亮跳跃，儿童与动画 |

## 女声（10）

| 音色 | voice_id | 年龄感 | 音色标签 | 适合 |
| --- | --- | --- | --- | --- |
| 知绘小姐 | `voc_rc894j8q2auu` | 青年 | bright, articulate, friendly | 明亮干脆、自信亲近，讲解首选 |
| 清雅引路人 | `voc_jgkfvjryu84b` | 青年 | articulate, precise, compassionate | 干净有分寸，品牌与专题片 |
| 香农小姐 | `voc_b86bfwct4cjn` | 青年 | refined, calm, precise | 清冷克制有条理，新闻与严肃说明 |
| 青史执笔人 | `voc_3nw7zw44cxek` | 中年 | calm, precise, articulate | 沉稳叙述，纪录片与人文 |
| 邻家暖心 | `voc_p36dbdewwvae` | 青年 | warm, gentle, friendly | 生活气息，Vlog 与温情播客 |
| 率真生活家 | `voc_enjt9va5bdr5` | 青年 | playful, measured, friendly | 轻快不油腻，生活类口播 |
| 午夜留声机 | `voc_t4b9j5dh8dyr` | 青年 | calm, refined, articulate | 低缓有质感，有声书与夜读 |
| 静心向导 | `voc_gwm7kudgccrq` | 青年 | authoritative, warm, gentle | 贴耳气声、语速极慢，冥想与助眠 |
| 干练安全官 | `voc_kcb2gbgwh6xw` | 中年 | articulate, calm, energetic | 语速快、咬字清，播报与客服 |
| 灵动雨珠 | `voc_uejhdugavcdu` | 儿童 | bright, precise, articulate | 清脆跳跃，儿童绘本与动画 |

## 使用方式

CLI：

```sh
breeze tts --text "……" --voice voc_reys5un5t4ed --format mp3 --file out.mp3 --agent
```

视频工程 `script.json`：

```json
{ "voices": { "narrator": { "voice_id": "voc_reys5un5t4ed", "model_id": "breeze-tts-2" } } }
```

视频只能配 `breeze-tts-2` / `breeze-tts-2-multilingual`，其它模型不返回词级时间戳。

## 核实与试听

`voc_` 才能配音，`gvi_` 是预览，必须先 `voice preview save` 换成 `voc_`。写进工程前核实一次：

```sh
breeze voice get voc_reys5un5t4ed --output json
breeze voice play voc_reys5un5t4ed
```

`voice get` 返回 `not_found` 说明该音色在当前账户不可见（极少数情况），退回 `voice list --voice-type default` 重新挑，并把替换结果告诉用户。

## 组合规则

- **一条片子只用一套音色。** 中途换音色，语气与语速都会变，观众会听出来。
- **多人对话**最多 2–3 个音色，各自固定角色，不要按段落轮换。
- 音色定了再批量合成：文本、音色、指令任一变化都会让缓存失效、重新计费。
- 音色与 [念法指令](instruction.md) 搭配使用；音色定"是谁在说"，指令定"这次怎么说"。
