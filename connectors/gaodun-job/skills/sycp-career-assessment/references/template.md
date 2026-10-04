<!--
  ⚠️ 本文件为 sycp-career-assessment/SKILL.md 的 §5.1 / §5.2 模板本体（byte-stable），
  由 SKILL.md 在渲染测评卡片前按需读取。2026-08-20 优化：60 个 option-btn 的重复 inline style
  收敛为 <style> 块内的 .option-btn / .option-btn.selected 两条 class 规则（输出体积 -49%），
  submit-btn 保留 inline style，内嵌 JS 逻辑未改动。渲染时只能替换 {...} 占位符，
  模板稳定性要求（§5.3 / §5.4）依然适用于本文件内容。
-->
### 5. 固定渲染模板（关键：byte-stable）

为保证不同用户每次触发本 skill 看到的样式一致，答题卡片与结果卡片**必须严格按下述固定 HTML 模板输出**，模型不得自行设计布局、不得改写 class、不得调整色值/字号/间距/圆角，**只能**对模板中标记为 `{...}` 的占位符做数据替换。模板字段对齐 `references/questions.md` 与评分脚本返回 JSON。

#### 5.1 答题卡片模板（10 题全量展示）

> 占位符：`{qid}` 题号 1-10、`{question}` 题干、`{prompt}` 提示语、`{optX}` 与 `{contentX}` 分别为该题 6 个选项字母与内容文本（X = A/B/C/D/E/F）。
> 模型必须为 10 道题**逐题**渲染完整的 `question-row`，禁止省略、禁止用占位省略号（如 `A. 办公室/秘书部...`）替代真实 content。

```html
<style>
    /* === 答题卡片静态样式 === */
    .sycp-assessment-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
    .sycp-assessment-card h2{font-size:22px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
    .sycp-assessment-card .subtitle{font-size:14px;color:#6B7280;margin:0 0 16px 0;}
    .sycp-assessment-card .progress-row{display:flex;align-items:center;gap:12px;margin:0 0 20px 0;}
    .sycp-assessment-card .progress-bar{flex:1;height:8px;background:#F5F6F8;border-radius:4px;position:relative;overflow:hidden;}
    .sycp-assessment-card .progress-bar-inner{height:100%;width:0;background:#4E8CFF;border-radius:4px;transition:width 0.2s;}
    .sycp-assessment-card .progress-text{font-size:13px;color:#6B7280;min-width:48px;text-align:right;}
    .sycp-assessment-card .question-row{padding:16px 0;border-top:1px solid #F0F1F3;}
    .sycp-assessment-card .question-row:first-of-type{border-top:none;}
    .sycp-assessment-card .question-header{display:flex;align-items:baseline;gap:8px;margin-bottom:4px;}
    .sycp-assessment-card .question-number{font-size:14px;font-weight:600;color:#4E8CFF;flex-shrink:0;}
    .sycp-assessment-card .question-text{font-size:15px;color:#1A1D24;font-weight:500;line-height:1.5;flex:1;}
    .sycp-assessment-card .question-prompt{font-size:13px;color:#9CA3AF;line-height:1.4;margin-bottom:12px;}
    .sycp-assessment-card .answer-options{display:grid;grid-template-columns:1fr;gap:8px;}
    .sycp-assessment-card .card-footer{text-align:center;margin-top:20px;}
    .sycp-assessment-card .answers-output{margin-top:16px;}
    .sycp-assessment-card .footer-hint{margin-top:16px;font-size:12px;color:#9CA3AF;text-align:center;}
    .sycp-assessment-card .incomplete-tip{padding:14px;background:#FFF5EB;border:1px solid #F0D5A3;border-radius:8px;font-size:13px;color:#3A3F47;line-height:1.6;text-align:left;}
    .sycp-assessment-card .option-btn{width:100%;padding:12px 14px;background:#F5F6F8;border:1px solid #E5E7EB;border-radius:8px;color:#3A3F47;font-size:14px;font-family:inherit;text-align:left;cursor:pointer;box-sizing:border-box;outline:none;display:block;line-height:1.5;transition:background 0.15s,border-color 0.15s,color 0.15s,box-shadow 0.15s;}
    .sycp-assessment-card .option-btn.selected{background:#E8F1FF;border-color:#4E8CFF;color:#1E4FB8;box-shadow:inset 3px 0 0 #4E8CFF;}

    /* === 结果卡片静态样式 === */
    .sycp-result-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
    .sycp-result-card .result-header{text-align:center;padding-bottom:20px;border-bottom:1px solid #F0F1F3;margin-bottom:20px;}
    .sycp-result-card .result-header h2{font-size:24px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
    .sycp-result-card .score-display{font-size:28px;font-weight:600;color:#1A1D24;margin-bottom:8px;}
    .sycp-result-card .score-display .score-max{font-size:16px;color:#9CA3AF;font-weight:400;}
    .sycp-result-card .summary{font-size:14px;color:#6B7280;line-height:1.5;}
    .sycp-result-card .tag-detail .section{margin-bottom:20px;}
    .sycp-result-card .section-title{font-size:15px;font-weight:600;color:#1A1D24;margin-bottom:8px;padding-left:10px;border-left:3px solid #4E8CFF;}
    .sycp-result-card .section-body{font-size:14px;color:#3A3F47;line-height:1.7;white-space:pre-wrap;}
    .sycp-result-card .footer-hint{margin-top:20px;font-size:12px;color:#9CA3AF;text-align:center;border-top:1px solid #F0F1F3;padding-top:16px;}
</style>
<div class="sycp-assessment-card assessment-card">
    <h2>生涯测评</h2>
    <div class="subtitle">共 10 题，请根据真实想法选择 A/B/C/D/E/F 中的一个</div>
    <div class="progress-row">
        <div class="progress-bar"><div class="progress-bar-inner"></div></div>
        <span class="progress-text">0 / 10</span>
    </div>
    <!-- ↓ 以下 question-row 必须为 10 道题逐题重复输出，不得省略、不得用省略号替代 content -->
    <div class="question-row" data-qid="{qid}">
        <div class="question-header">
            <div class="question-number">{qid}</div>
            <div class="question-text">{question}</div>
        </div>
        <div class="question-prompt">{prompt}</div>
        <div class="answer-options">
            <button class="option-btn" data-tag="A">A. {contentA}</button>
            <button class="option-btn" data-tag="B">B. {contentB}</button>
            <button class="option-btn" data-tag="C">C. {contentC}</button>
            <button class="option-btn" data-tag="D">D. {contentD}</button>
            <button class="option-btn" data-tag="E">E. {contentE}</button>
            <button class="option-btn" data-tag="F">F. {contentF}</button>
        </div>
    </div>
    <!-- ↑ 重复 10 次：qid=1..10，每次从 questions.md 取对应题 -->
    <div class="card-footer">
        <button class="submit-btn" style="padding:10px 32px;background:#4E8CFF;border:1px solid #4E8CFF;border-radius:8px;color:#FFFFFF;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;outline:none;transition:background 0.15s,border-color 0.15s;">提交</button>
    </div>
    <div class="answers-output"></div>
    <div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>
</div>
<script>
    (function(){
        try{
            /* === 嵌入数据：6 个标签档案（与 references/tag_profiles.md 一一对应，禁止改写） === */
            var TAG_PROFILES={
                "A":{"name":"公考/央国企","section_1_title":"天选公考/央国企圣体","section_1":"【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n","section_2_title":"大学四年规划","section_2":"公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩","section_3_title":"备考路径","section_3":"备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸","section_4_title":"寄语","section_4":"志当存高远，慎始而敢行！"},
                "B":{"name":"自由职业","section_1_title":"独步天下的自由职业者","section_1":"【独步天下的自由职业者】\n生性自由的你，做自己的老板吧！","section_2_title":"大学四年规划","section_2":"自由职业者的大学四年规划：\n绩点：大学四年不挂科\n技能：通过英语四六级、国家计算机二级考试\n提升：学习商科证书，如ACCA、CFA，提升商业思维、经营意识\n论文：写完毕业论文并通过答辩","section_3_title":"实践路径","section_3":"实践：\n大一--探索个人兴趣与能力优势，参加兼职、实习\n大二--思考兴趣/能力变现方式，尝试变现\n大三--了解国家及学校创业政策，申请创业启动资金\n大四--成立工作室，拓展业务，美美做老板","section_4_title":"寄语","section_4":"真正的自由，不是随心所欲，而是自我主宰！"},
                "C":{"name":"打工人","section_1_title":"天选打工人","section_1":"【天选打工人】\n成为CEO走向人生巅峰不是梦！","section_2_title":"大学四年规划","section_2":"打工人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级考试、国家计算机二级考试\n证书：考取ACCA、CFA、CPA等专业证书\n身份：竞选学生会/社团主席\n背提：参加专业相关或名企商赛\n论文：写完毕业论文并通过答辩","section_3_title":"实习路径","section_3":"实习：\n大一--明确职业规划\n大二--参加目标岗位寒暑假实习\n大三--参加名企目标岗位实习\n大四--提升求职技巧，参加校招，收获offer","section_4_title":"寄语","section_4":"打工人，打工魂，打工人都是人上人！！"},
                "D":{"name":"留学","section_1_title":"留学届的翘楚","section_1":"【留学届的翘楚】\n你的目标是星辰大海，跨越重洋你会看到更广阔的天地！","section_2_title":"大学四年规划","section_2":"留学人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n外语：考雅思/托福，达到梦想院校申请标准\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩","section_3_title":"申请路径","section_3":"申请：\n大一--收集留学信息，了解不同国家/院校要求、费用\n大二--明确留学国家/院校/专业目标\n大三--准备留学申请材料，依据要求考GRE/GMAT\n大四--提交留学申请；拿到梦校offer，完成签证准备","section_4_title":"寄语","section_4":"放眼望乾坤，身行万里半天下；探手取知识，必成一大家!"},
                "E":{"name":"保研/考研","section_1_title":"保研考研大赢家","section_1":"【保研考研大赢家】\n学术大咖！不读研读博你都亏了","section_2_title":"大学四年规划","section_2":"保研/考研人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n科研：参加学科竞赛、科研项目，争取获奖、发表论文\n论文：写完毕业论文并通过答辩","section_3_title":"备考路径","section_3":"备考：\n大一--收集考研信息，了解保研考研政策\n大二--明确目标院校/专业，了解招生简章与考核内容\n大三--保研人准备保研材料；考研人系统复习各科知识点\n大四--保研人申请保研资格；考研人参加初试复试，摘取胜利果实","section_4_title":"寄语","section_4":"登峰造极的成就源于自律，保研/考研人，加油！！！"},
                "F":{"name":"躺平","section_1_title":"躺平族代言人","section_1":"【躺平族代言人】\n躺平也是一种人生态度，我还能再躺几年！","section_2_title":"毕业任务","section_2":"想要大学顺利毕业，躺平族也要完成一些任务哦：\n绩点：不挂科，60分万岁\n学分：按时参加必修与辅修课，修满毕业所需学分\n技能：通过英语四六级、国家计算机二级考试\n论文：写完毕业论文并通过答辩","section_3_title":"额外任务","section_3":"额外任务：\n\n规划：发现自己的兴趣与使命所在\n升学：了解考研/保研、留学等升学路径，探索升学意向\n就业：了解考公、央国企、校招等就业路径，探索就业意向\n提升：了解证书、科研、实习、兴趣变现，探索提升方向","section_4_title":"寄语","section_4":"躺平其实只是不再向外拼命内卷，而是向内自我探索，给足时间发掘自己热爱的事物。追求美好的生活，没有时间限制，任何时候开始都不晚。"}};

            /* === 嵌入数据：选项→标签 映射（10 题×6 选项，与 references/questions.md 一一对应） === */
            var OPTION_TO_TAG={
                "1":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "2":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "3":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "4":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "5":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "6":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "7":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "8":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "9":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"},
                "10":{"A":"A","B":"B","C":"C","D":"D","E":"E","F":"F"}
            };

            /* === 评分常量 === */
            var TAGS=["A","B","C","D","E","F"];
            var PRIORITY={"E":1,"A":2,"D":3,"C":4,"B":5,"F":6};
            var TOTAL=10;

            /* === 工具函数 === */
            function esc(s){ if(s===undefined||s===null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

            /* === 找卡片 === */
            var cards=document.querySelectorAll('.sycp-assessment-card');
            if(!cards.length) return;
            var card=cards[cards.length-1];

            var answers={};
            var rows=card.querySelectorAll('.question-row');
            var barInner=card.querySelector('.progress-bar-inner');
            var barText=card.querySelector('.progress-text');
            var submit=card.querySelector('.submit-btn');
            var out=card.querySelector('.answers-output');

            function refresh(){
                var n=Object.keys(answers).length;
                barText.textContent=n+' / '+TOTAL;
                barInner.style.width=(n/TOTAL*100)+'%';
            }

            /* === 选项点击：互斥切换 + 记录答案 === */
            for(var i=0;i<rows.length;i++){
                (function(row){
                    var qid=row.getAttribute('data-qid');
                    var btns=row.querySelectorAll('.option-btn');
                    for(var j=0;j<btns.length;j++){
                        (function(btn){
                            btn.onclick=function(){
                                for(var k=0;k<btns.length;k++){
                                    var b=btns[k];
                                    b.className=b.className.replace(/\s*selected/g,'');
                                    b.style.background='#F5F6F8';
                                    b.style.borderColor='#E5E7EB';
                                    b.style.color='#3A3F47';
                                    b.style.boxShadow='none';
                                }
                                btn.className=btn.className+' selected';
                                btn.style.background='#E8F1FF';
                                btn.style.borderColor='#4E8CFF';
                                btn.style.color='#1E4FB8';
                                btn.style.boxShadow='inset 3px 0 0 #4E8CFF';
                                answers[qid]=btn.getAttribute('data-tag');
                                if(out) out.innerHTML='';
                                refresh();
                            };
                        })(btns[j]);
                    }
                })(rows[i]);
            }

            /* === 提交：算分 + 渲染结果卡片 === */
            submit.onclick=function(){
                var n=Object.keys(answers).length;
                if(n<TOTAL){
                    var miss=0;
                    for(var i=1;i<=TOTAL;i++){ if(!answers[String(i)]){ miss=i; break; } }
                    var missRow=card.querySelector('.question-row[data-qid="'+miss+'"]');
                    try{ if(missRow && missRow.scrollIntoView) missRow.scrollIntoView({behavior:'smooth',block:'center'}); }catch(e){}
                    out.innerHTML='<div class="incomplete-tip"><b style="color:#E89B3F;">还有 '+(TOTAL-n)+' 题未答（从第 '+miss+' 题起未答），请补完再提交。</b></div>';
                    return;
                }
                /* 1) 统计 6 标签计数 */
                var counts={A:0,B:0,C:0,D:0,E:0,F:0};
                for(var i=1;i<=TOTAL;i++){
                    var qid=String(i);
                    var ans=answers[qid];
                    var m=OPTION_TO_TAG[qid];
                    if(m && m[ans]){ counts[m[ans]]++; }
                }
                /* 2) 找胜出标签：最大计数 + PRIORITY 升序 */
                var maxCount=0;
                for(var k=0;k<TAGS.length;k++){ if(counts[TAGS[k]]>maxCount) maxCount=counts[TAGS[k]]; }
                var candidates=[];
                for(var k=0;k<TAGS.length;k++){ if(counts[TAGS[k]]===maxCount) candidates.push(TAGS[k]); }
                var dominant=null;
                var bestP=999;
                for(var m=0;m<candidates.length;m++){
                    var p=PRIORITY[candidates[m]];
                    if(p<bestP){ bestP=p; dominant=candidates[m]; }
                }
                /* 3) display_score：胜出标签百分比取整 ROUND_HALF_UP */
                var domCount=counts[dominant];
                var ds=Math.round(domCount*100/TOTAL);
                /* 4) 胜出标签名称与固定文案 summary */
                var domName=TAG_PROFILES[dominant].name;
                var summary='用户在 10 道题中，'+domName+' 方向选了 '+domCount+' 次（最多），生涯测评结果为：'+domName+'。';

                /* 5) 拼接 4 段 section */
                var prof=TAG_PROFILES[dominant];
                var sectionsHtml='';
                for(var s=1;s<=4;s++){
                    var tk='section_'+s+'_title';
                    var bk='section_'+s;
                    sectionsHtml+='<div class="section"><div class="section-title">'+esc(prof[tk])+'</div><div class="section-body">'+esc(prof[bk])+'</div></div>';
                }

                /* 6) 拼整张结果卡片 HTML（顶部无大字母、无「各方向得分」区块） */
                var html=
                    '<div class="sycp-result-card">'+
                        '<div class="result-header">'+
                            '<h2>'+esc(domName)+'</h2>'+
                            '<div class="score-display">'+ds+'<span class="score-max"> / 100</span></div>'+
                            '<div class="summary">'+esc(summary)+'</div>'+
                        '</div>'+
                        '<div class="tag-detail">'+sectionsHtml+'</div>'+
                        '<div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>'+
                    '</div>';

                /* 7) 写入 .answers-output 区域 + 进度条满 */
                out.innerHTML=html;
                barText.textContent=TOTAL+' / '+TOTAL;
                barInner.style.width='100%';
                try{ out.scrollIntoView({behavior:'smooth',block:'start'}); }catch(e){}
            };

            refresh();
        }catch(e){}
    })();
</script>
```

> 注：模板顶部**必须包含一个 `<style>` 块**，把**所有静态元素**（答题卡片：`.sycp-assessment-card` / `h2` / `.subtitle` / `.progress-row` / `.progress-bar` / `.progress-bar-inner` / `.progress-text` / `.question-row` / `.question-header` / `.question-number` / `.question-text` / `.question-prompt` / `.answer-options` / `.option-btn`（含 `.selected` 选中态）/ `.card-footer` / `.answers-output` / `.footer-hint` / `.incomplete-tip`；结果卡片：`.sycp-result-card` / `.result-header` / `h2` / `.score-display` / `.score-max` / `.summary` / `.section` / `.section-title` / `.section-body` / `.footer-hint`）的 CSS（背景/边框/圆角/padding/字号/字色/布局）写死在 `<style>` 块内，**不依赖平台 Visualizer 注入**。`<style>` 块的 CSS 文本在所有用户、所有触发轮次中必须逐字节一致，禁止为某用户改色值/间距/圆角/字号。`section-body` 的 `white-space:pre-wrap` 已写入 `.section-body` 规则，HTML 里不加 inline style。`.option-btn` 的默认样式与选中态（`.option-btn.selected`）均由 `<style>` 块 class 规则控制，元素本身不带 inline style（2026-08-20 优化：60 个按钮的重复 inline style 收敛为 2 条 class 规则，渲染输出体积 -49%）。
>
> **option-btn 样式由 `<style>` 块 class 规则承载，submit-btn 保留 inline style**。原因：实测 WorkBuddy 平台 Visualizer **不会自动接管** `.option-btn` / `.submit-btn` 的样式或行为；所有交互必须由模板底部内嵌的 `<script>` 块自己实现。option-btn 有 60 个重复实例（10 题 × 6 选项），把样式收敛为 `<style>` 块内的 `.option-btn` / `.option-btn.selected` 两条 class 规则可显著减少渲染输出体积（约 -49%，输出 token 减半）；submit-btn 仅 1 个实例，保留 inline `style="padding:10px 32px;background:#4E8CFF;border:1px solid #4E8CFF;border-radius:8px;color:#FFFFFF;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;outline:none;transition:background 0.15s,border-color 0.15s;"`。`<script>` 点选时写入的 inline style 值（`#F5F6F8` / `#E5E7EB` / `#3A3F47` / `none` 与选中态 `#E8F1FF` / `#4E8CFF` / `#1E4FB8` / `inset 3px 0 0 #4E8CFF`）与 class 规则一致，视觉等价，故 script 保持零改动。
>
> **所有交互由模板底部内嵌 `<script>` 块实现（关键）**：实测 WorkBuddy 平台 Visualizer 不会接管 `.option-btn` / `.submit-btn` 的 click 事件，也不会自动切换 `.selected` class。因此模板**必须**在 `</div>` 之后包含一段自包含的 `<script>`（用 IIFE + try/catch 包裹，不依赖外部 JS 库），完成以下交互：
> 1. **绝对不要用 `document.currentScript.previousElementSibling`**——在 widget 沙箱里 `currentScript` 可能为 `null`，第一行就抛 TypeError 被 try/catch 吞掉，整个脚本静默失败。改用 `document.querySelectorAll('.sycp-assessment-card')[cards.length-1]` 全局查找卡片容器（取最后一个匹配，防止页面有多个 sycp 卡片时拿到错的）；
> 2. **不要用 `Array.prototype.forEach` / `NodeList.forEach` / `addEventListener` / `classList.add`/`remove`**——部分 widget 沙箱对 ES5+ 方法支持不稳定。改用传统的 `for(var i;i<len;i++)` 循环 + 闭包 IIFE `(function(el){...})(el[i])` 帮每轮保留变量；用 `btn.onclick = function(){...}`（不是 `addEventListener`）绑事件；用 `el.className = el.className.replace(/\s*selected/g,''); el.className = el.className+' selected';` 替代 `classList`；
> 3. **嵌入计算数据**（关键，提交后算分+渲染结果卡片）：`<script>` 顶部必须嵌入 3 个常量对象，所有数据来自 skill 自带的 `references/questions.md` 与 `references/tag_profiles.md`：
     >    - **`TAG_PROFILES`**：6 个标签档案字典 `{A:{name,section_1_title,section_1,...,section_4_title,section_4}, B:..., F:...}`，每个字段值与 `tag_profiles.md` 原文字符串完全一致（含 `\n` 换行，4 段文案不得改写、不得截断、不得自行撰写）。`section_X` 内的换行用 JS 字符串字面量 `\n` 表示，HTML 渲染时由 `.section-body` 的 `white-space:pre-wrap` 还原。
>    - **`OPTION_TO_TAG`**：10 题选项→标签映射 `{qid:{A:tag, B:tag, C:tag, D:tag, E:tag, F:tag}}`。当前 10 题题库每个题 A-F 与 tag 一一对应（A→A,B→B...），但**必须按真实映射写入**——若未来题库改为"题 1 A→B, B→A"等，需同步更新此映射。映射来源：`references/questions.md` 各 `## 题目 N` 小节选项表的 `标签` 列。
>    - **`PRIORITY`**：平局优先级 `{E:1, A:2, D:3, C:4, B:5, F:6}`（数值越小越优先），与 `scripts/calculate_sycp.py` 的 `PRIORITY` 表逐字节一致。
>    - **`TOTAL=10`**：总题数（与题库实际题数一致）。
> 4. 每次答题后把 `answers[qid] = btn.getAttribute('data-tag')` 写入内存，并刷新 `.progress-text` 为 `已答题数 / 10`、给 `.progress-bar-inner` 设 `style.width = (已答/total*100)+'%'`；
> 5. 给 `.submit-btn` 绑 `click`：
     >    - **未答完**（`Object.keys(answers).length < TOTAL`）：在 `.answers-output` 区域显示一个 `.incomplete-tip`（橙色 `#FFF5EB` 底，提示「还有 N 题未答（从第 X 题起未答）」），并用 `scrollIntoView({behavior:'smooth',block:'center'})` 滚动聚焦到第一个未答的 `.question-row`（`scrollIntoView` 必须用 try/catch 包裹，避免沙箱不支持抛错）。**不弹窗、不显示答案串、不退化为其他行为**。
>    - **全答完**：用嵌入的 `OPTION_TO_TAG` 统计 6 标签计数；按 `PRIORITY` 升序取胜出标签；计算 `display_score = round(dominant_count*100/TOTAL)`；从 `TAG_PROFILES[dominant]` 取胜出标签的 4 段文案（含 `\n`）；拼接完整结果卡片 HTML（含 `h2` 方向名 / `score-display` / `summary` / 4 段 `section` / `footer-hint`，**不含顶部大字母、不含「各方向得分」区块**），写入 `.answers-output` 区域；最后把 `.progress-bar-inner` 宽度设为 `100%`、`.progress-text` 文本设为 `10 / 10`、并 `scrollIntoView` 滚动聚焦到结果卡片。
> 6. 进度条初始宽度 0%、文本 `0 / 10`；每次答题后实时刷新；提交后满 100%。`<script>` 文本在所有用户、所有触发轮次中必须逐字节一致（仅含上面 §5.1 列出的 IIFE 逻辑、`TAG_PROFILES` / `OPTION_TO_TAG` / `PRIORITY` 数据嵌入，**不含用户答案、不含时间戳、不含 `Math.random()` 等运行时变量**）。
>
> **进度条动态更新**：用 `.progress-bar-inner` 内部 div 实现（CSS `height:100%; width:0; background:#4E8CFF; transition:width 0.2s;`），`<script>` 在答题时给 `.progress-bar-inner` 设 `style.width`。所有用户的进度条初始态（`0 / 10`、宽度 0%）与更新逻辑必须一致。
>
> **submit-btn 始终可点击、始终可见**，不加 `disabled`；提交按钮的样式由 `<button class="submit-btn" style="...">提交</button>` inline `style` 写死。
>
> **结果卡片不依赖平台 Visualizer 注入**：结果卡片的 DOM 结构、class 名、`<style>` 块 CSS 全部与 §5.2 模板保持一致，由 `<script>` 在渲染时拼接 HTML 写入 `.answers-output`，不依赖平台接管。

#### 5.2 结果卡片模板（提交后展示）

> **结果卡片不再单独渲染**：实际渲染流程中，结果卡片**不是**由模型另起一段输出，而是由 §5.1 模板底部内嵌 `<script>` 在 `submit-btn` 点击时直接拼接 HTML 写入 `.sycp-assessment-card .answers-output` 区域（见 §5.1 注与 §3 提交流程）。本节作为**契约参考**：当模型按 §5.1 渲染答题卡片时，`<script>` 拼接结果卡片 HTML 必须严格遵循本节定义的 DOM 结构、class 名、`<style>` 规则、占位符来源与顺序——保证用户看到的最终结果卡片与"模型另起一段渲染"时的样式逐字节一致。
>
> 占位符全部来自嵌入 `<script>` 的算法计算结果（与 `scripts/calculate_sycp.py` 的 `calculate_scores` 逐字段对齐）：`{dominant_name}`、`{display_score}`、`{section_X_title}` / `{section_X}`（X = 1..4）、`{analysis_summary}`。**结果卡片不再展示顶部大字母（`dominant-letter`）与「各方向得分」6 行 `stat-row`**；禁止模型自行命名占位符、禁止把胜出标签以外的字段塞进结果卡片。
>
> `section_1..section_4` **必须原样取自 `TAG_PROFILES[dominant]`**（即 `references/tag_profiles.md` 的 `section_X` 字段原文字符串），含 `\n` 换行符；模型不得改写、不得截断、不得自行撰写；HTML 拼接时直接 `<div class="section-body">...</div>` 输出，由 `.section-body { white-space:pre-wrap; }` 规则保留换行。

```html
<style>
.sycp-result-card{background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;padding:24px;max-width:720px;margin:0 auto;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:#3A3F47;}
.sycp-result-card .result-header{text-align:center;padding-bottom:20px;border-bottom:1px solid #F0F1F3;margin-bottom:20px;}
.sycp-result-card .result-header h2{font-size:24px;font-weight:600;color:#1A1D24;margin:0 0 8px 0;}
.sycp-result-card .score-display{font-size:28px;font-weight:600;color:#1A1D24;margin-bottom:8px;}
.sycp-result-card .score-display .score-max{font-size:16px;color:#9CA3AF;font-weight:400;}
.sycp-result-card .summary{font-size:14px;color:#6B7280;line-height:1.5;}
.sycp-result-card .tag-detail .section{margin-bottom:20px;}
.sycp-result-card .section-title{font-size:15px;font-weight:600;color:#1A1D24;margin-bottom:8px;padding-left:10px;border-left:3px solid #4E8CFF;}
.sycp-result-card .section-body{font-size:14px;color:#3A3F47;line-height:1.7;white-space:pre-wrap;}
.sycp-result-card .footer-hint{margin-top:20px;font-size:12px;color:#9CA3AF;text-align:center;border-top:1px solid #F0F1F3;padding-top:16px;}
</style>
<div class="sycp-result-card">
  <div class="result-header">
    <h2>{dominant_name}</h2>
    <div class="score-display">{display_score}<span class="score-max"> / 100</span></div>
    <div class="summary">{analysis_summary}</div>
  </div>
  <div class="tag-detail">
    <div class="section">
      <div class="section-title">{section_1_title}</div>
      <div class="section-body">{section_1}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_2_title}</div>
      <div class="section-body">{section_2}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_3_title}</div>
      <div class="section-body">{section_3}</div>
    </div>
    <div class="section">
      <div class="section-title">{section_4_title}</div>
      <div class="section-body">{section_4}</div>
    </div>
  </div>
  <div class="footer-hint">今天帮你做些什么？@引用对话文件 / 调用技能与指令</div>
</div>
```

> 注：模板顶部**必须包含 `<style>` 块**，把结果卡片**静态元素**（`.sycp-result-card` / `.result-header` / `h2` / `.score-display` / `.score-max` / `.summary` / `.section` / `.section-title` / `.section-body` / `.footer-hint`）的 CSS（背景/边框/圆角/padding/字号/字色/布局）写死在 `<style>` 块内，不依赖平台 Visualizer 注入，确保所有用户/所有前端环境看到的静态布局样式逐字节一致。`<style>` 块的 CSS 文本在所有用户、所有触发轮次中必须逐字节一致，禁止为某用户改色值/间距/圆角。`section-body` 的 `white-space:pre-wrap` 已写入 `.section-body` 规则，HTML 里不加 inline style。
>
> **结果卡片不再展示「各方向得分」区块**：结果卡片顶部**不渲染**大字母（`.dominant-letter`），也不再渲染「各方向得分」标题与 6 行 `stat-row`；报告结构固定为：`result-header`（`h2` 方向名 + `score-display` + `summary`）→ `tag-detail`（4 段 section，按 1→2→3→4）→ `footer-hint`。`tag_stats` 数据仍由评分脚本在 JSON 输出中提供（契约不变），仅前端结果卡片不再展示。
