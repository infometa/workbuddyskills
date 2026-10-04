# 内置能力说明

本专家包独立提供以下能力，不需要安装、调用或推荐其他 Skill：

1. 基于用户目标、材料和作答的轻量学习诊断，以及本会话训练目标。
2. CET-4、CET-6、考研英语一/二 A/B 节作文练习模拟反馈。
3. 一般作文、英文邮件和摘要的任务、结构、连贯、句法、词汇与语域诊断。
4. 阅读理解的主旨、细节、推断、词义、态度、篇章结构、证据定位和干扰项分析。
5. 用户材料驱动的语境词汇、搭配、词形、辨析、回忆和新语境使用训练。
6. 从真实错误出发的语法识别、改错、产出和新语境验收。
7. CET 汉译英、考研英译中及通用双向翻译的证据反馈、重译和参考译法。
8. CET-4/CET-6 阅读、写作、翻译文本题型训练；不含听力和真实口语评测。
9. 英文范文逐句/逐段精读、长难句拆解、上下文词义和表达迁移。
10. “诊断—用户作答—证据反馈—重练—复盘”的统一训练闭环。
11. 当前会话内的错误卡、薄弱项、重练结果和下一步学习卡。
12. 总词数、排除词数、有效词数、句数、段落和语言比例统计。
13. CET/考研作文批改 HTML 报告。
14. 课程独立作业的拆题、批注、局部示范和重写反馈，不提供可直接提交的完整成品。

## 文件分工

- `agents/english-writing-coach.md`：职业定位、首轮介绍、核心能力、稳定判断和关键边界。
- `SKILL.md`：总入口、最少输入、训练模式、状态、统计、报告、失败和重评。
- `references/learning-foundation.md`：轻量诊断、统一训练闭环、错误标签和会话内学习卡。
- `references/task-routing.md`：完整场景路由与诚信分流。
- `references/exam-writing-review.md`：CET 与考研作文评分流程。
- `references/scoring-sources.md`：来源登记、版本、风险和包内规则边界。
- `references/scoring-calibration.md`：作文档内取分锚点和一致性规则。
- `references/general-writing-diagnosis.md`：一般写作、邮件、摘要和独立作业训练。
- `references/reading-comprehension.md`：阅读题型、证据、干扰项和原创题检查。
- `references/vocabulary-learning.md`：语境词汇选择、三级掌握度和会话内复习。
- `references/grammar-training.md`：语法知识地图和四步专项闭环。
- `references/translation-training.md`：CET、考研与通用翻译分流和反馈。
- `references/cet-text-training.md`：CET 文本题型范围、官方结构来源和版权边界。
- `references/intensive-reading.md`：精读与表达迁移。
- `references/output-templates.md`：按任务加载的交付模板。
- `references/report-schema.md`：考试作文批改 HTML 报告数据契约。
- `references/quality-and-safety-checklist.md`：跨场景质量、来源、隐私和诚信检查。
- `scripts/text_metrics.py`：可重复的文本统计与排除文本处理。
- `scripts/render_report.py`：严格校验并转义的作文批改 HTML 报告渲染。
- `tests/`：脚本与 v1.3 场景规则回归测试。

## 适用限制

- 轻量诊断不等于标准化水平测试，不输出无依据的 CEFR、CET 总分或词汇量。
- 模拟分数用于练习反馈，不等于官方成绩或报道分。
- CET 作文依据 2016 年修订版公开大纲摘要；考研作文在未获得当年大纲时使用历史公开框架并明确限制。
- CET 文本题型结构依据 2026-07-19 核验的官方页面；页面更新后应重新核验。
- CET 阅读有可靠答案时可报告本组正确率，但不换算报道分；翻译没有完整量表时不给伪精确官方分。
- IELTS、TOEFL、高考、GRE、专四和专八只做非量化诊断。
- 图片 OCR、真实听力、口语和发音评测不在当前范围；文字口语组织不等于口语评测。
- 当前无跨会话持久化或调度能力，不承诺自动词库、间隔复习提醒或长期成长曲线。
- 3000 词以上文本分段处理。
- HTML 仅支持可给出稳定数字结果的 CET/考研作文批改。
- 文件型产物只在用户明确要求后生成，不覆盖原文件。
