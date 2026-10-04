# 神台词范式库（golden-lines）

> **状态：v6.0.0 空骨架（待填充）。** 录入规范见 `INDEX.md` 第 3 节。
> 本库只存「句式模板 + 改写示例」，**不照搬原文**，规避版权。仅供采样，不参与评分。

## 使用说明

神台词的价值不在原句，而在**句式结构与情绪杠杆**。本库按"使用场景"分区，每条提炼可复用的句式模板与原创改写示例。

## 分区（待填充）

### A. 打脸 / 反击类
> 场景：身份揭晓、实力碾压、反将一军。

<!-- 待填充。示例字段格式：
- id: HL-GL001
  scene: 打脸高潮
  pattern: 先抑后扬，用对方的轻视句式原样回敬
  template: "你不是说我【对方贬低词】吗？那现在【现状反转】，又算什么？"
  example: "你不是说我连这间公司的门都进不来吗？那现在坐在你对面签字的，又是谁？"
  source_type: 都市逆袭/近年
  note: 句式短促，落点放在反问，配合停顿
-->

### B. 深情 / 救赎类
> 场景：追妻、告白、生死关头的情感爆发。

<!-- 待填充 -->

### C. 立威 / 宣言类
> 场景：主角立场宣告、绝境立誓、气场全开。

<!-- 待填充 -->

### D. 反转 / 揭底类
> 场景：真相揭晓、伏笔回收时的点睛台词。

<!-- 待填充 -->

### E. 英文海外专区（English / Overseas）
> 场景：海外 / DramaBox 类海外竖屏爆款。提炼自 53 部真实海外短剧素材，按打脸/深情/立威/反转四类各录英文骨架若干。
> 录入约定：`template` 与 `example` 用英文（template=抽象骨架，example=基于骨架的原创示范句，**非原文照抄**）；`pattern` 与 `note` 用中文讲解。

**E-1 打脸 / 反击（揭身份、财力碾压、原话反弹）**

- id: HL-EN001
  scene: 仪式现场揭身份打脸
  pattern: 公开舞台登台亮真身，"身份+打脸"双杀，落点放在反派从趾高气扬到当场石化
  template: "Please welcome the new [head] of [大集团]. — [反派的笑容当场凝固]"
  example: "Please welcome the new chairman of Hale Industries. — Across the room, the man who'd fired her last week went white."
  source_type: 英文复仇逆袭/海外爆款
  note: 把最大爆点压到公共场合释放，围观群众越多越爽；常作中后段高潮或付费墙

- id: HL-EN002
  scene: 财力轻飘碾压
  pattern: 对反派炫耀的"巨款"不屑一顾，用一个更高量级的物件作比，暗示真实身家
  template: "[一笔巨款]? That wouldn't even cover the [某奢侈品的零件] of this [car/house]."
  example: "Two hundred grand? That wouldn't even cover the rims on this car."
  source_type: 英文豪门马甲/海外爆款
  note: 阶层碾压的瞬间快感，让反派如跳梁小丑；中段冲突反复可用

- id: HL-EN003
  scene: 原话反弹打脸
  pattern: 把反派早先羞辱自己的措辞，原样奉还，扬眉吐气
  template: "You called me [对方的贬低词]? [现状反转] — turns out you were describing yourself."
  example: "You called me trash? I just bought the building you're standing in — turns out you were describing yourself."
  source_type: 英文逆袭打脸/海外爆款
  note: 句式落点在"原话回敬"，配合停顿和反派表情特写

- id: HL-EN004
  scene: 经济独立反击势利眼
  pattern: 被贴"拜金/被包养"标签时当场反击，强调"我自己挣的"
  template: "So it just took [a check] to buy me? I [earned] every cent myself — you're the one for sale."
  example: "So it just took a check to buy me? I earned every cent myself. You're the one who's for sale."
  source_type: 英文校园逆袭/海外爆款
  note: 先抑后扬，撕掉施舍标签；适合当众围观场景放大爽感

**E-2 深情 / 救赎（守护承诺、非血缘父爱、契约转真）**

- id: HL-EN005
  scene: 契约转真心求婚
  pattern: 撕掉"这是合约/表演"的前提，强调"这次是真的我在问你"
  template: "This isn't a [performance]. This isn't a [contract]. This is me — asking you, for real."
  example: "This isn't a show for the cameras. This isn't the deal we signed. This is me, asking you to stay. For real."
  source_type: 英文契约甜宠/海外爆款
  note: 假戏变真的爆点，结尾高潮释放；前面铺越多"假"，这一句越炸

- id: HL-EN006
  scene: 非血缘父爱觉醒
  pattern: 当被提醒"孩子不是你亲生"时，主角主动认下别人的孩子
  template: "[He's not your son.] — I don't care. I'm staying."
  example: "He's not even your blood. — He called me Dad. That makes him mine. I'm not going anywhere."
  source_type: 英文萌宝/海外爆款
  note: 催泪爆点，把"父爱"从血缘里解放出来；常配医院/认亲场景

- id: HL-EN007
  scene: 唯一性告白
  pattern: 用对某人独有的生理/情绪反应证明真心，比直白"我爱你"更有记忆点
  template: "You're the only [person] I don't [feel X around]. So yes — it has to be you."
  example: "You're the only one I don't freeze around. Everyone else, I shut down. So yes — it has to be you."
  source_type: 英文强宠/海外爆款
  note: 用"特例"证明唯一，强于直白告白；适合有缺陷/恐女症人设的关系升温点

**E-3 立威 / 宣言（护短宣战、占有宣示、狠话）**

- id: HL-EN008
  scene: 护短宣战
  pattern: 把"动我的人=与我整个势力为敌"挑明，撑腰最高规格
  template: "If anyone harms [her] again, you make an enemy of the entire [family]. I'll show no mercy."
  example: "Touch her again, and you don't just answer to me — you answer to everyone who carries my name. No mercy."
  source_type: 英文黑帮强权/海外爆款
  note: 极致撑腰快感，被护者感动+施害者恐惧；可反复释放

- id: HL-EN009
  scene: 霸道占有宣示
  pattern: 危险与保护并存的主权宣言，强调"只有我能碰"
  template: "You are mine now. Mine to protect. No one touches my [woman] but me."
  example: "You're mine now. Mine to keep safe, mine to answer for. Nobody lays a hand on what's mine."
  source_type: 英文强宠占有/海外爆款
  note: 黑帮/Alpha 男主标志句；危险感正是甜点，配合护短行动

- id: HL-EN010
  scene: 强者狠话立威
  pattern: 用云淡风轻的一句话给威胁者下"死亡通知"，反差制造压迫感
  template: "Enjoy [this moment] while it lasts. My enemies don't last long in this life."
  example: "Enjoy the view from up there. People who cross me have a way of disappearing."
  source_type: 英文复仇黑帮/海外爆款
  note: 留白式威慑，狠在轻描淡写；一句立住"惹他=找死"人设

**E-4 反转 / 揭底（马甲曝光、认亲撞脸、追悔虚拟语气）**

- id: HL-EN011
  scene: 马甲身份揭晓
  pattern: 用旁人或自己的一句话点破"低贱身份"其实是顶级身份的伪装
  template: "Your [flash-marriage husband] is [a billionaire CEO]? — The whole room went silent."
  example: "Wait — the janitor you've been mocking owns this entire hospital? The cafeteria went dead quiet."
  source_type: 英文马甲反转/海外爆款
  note: 信息差总爆发，碾压式打脸；卡在揭晓前一秒做付费墙

- id: HL-EN012
  scene: 撞脸认亲悬置
  pattern: 旁观者首次见到孩子撞脸男主，抛出认亲钩子，观众握信息差
  template: "Why does [that kid] look just like [you when you were young]?"
  example: "Funny... that little boy has your exact eyes. Why does he look just like your baby photos?"
  source_type: 英文萌宝/海外爆款
  note: 观众已知=男主未知的延迟快感；开场埋钩、中段付费点引爆

- id: HL-EN013
  scene: 追悔虚拟语气
  pattern: 男主用"If I had known…"的虚拟语气追悔，悔在"早知道"，配身份反转最佳
  template: "If I had known you were [dying / the heir / pregnant], I would never have [let you go]."
  example: "If I'd known you were the one keeping this whole family afloat, I never would have signed those papers."
  source_type: 英文追悔莫及/海外爆款
  note: "火葬场"核心句，必须"事已成定局"才说，且永远慢观众半拍

- id: HL-EN014
  scene: 重生/觉醒断情反转
  pattern: 受害者宣告与过去心软的自己彻底告别，标志觉醒/重生引擎启动
  template: "I once let my love blind me. No matter what [背叛者] did, I forgave [them]. That ends now."
  example: "I used to forgive him every single time. The fates gave me one more chance — and this time, I forgive nothing."
  source_type: 英文重生复仇/海外爆款
  note: 重生流开场觉醒句，与圣母旧我切割；为后续精准反杀定调

---
（A/B/C/D 中文专区待按 INDEX 规范逐条录入；E 英文海外专区已录入 14 条。）
