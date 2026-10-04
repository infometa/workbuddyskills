# MBTI 测评渲染模板（byte-stable 唯一权威源）

> **本文件是 career-personality skill 两道渲染链路（题目卡片 / 测评报告）的唯一权威源。**
>
> **每次触发本 skill（含派生触发："再来一份""朋友也要测""给同事也来一套""试试换个 UI""重置再来一遍"等）都必须重新 `Read` 本文件**，然后按下述步骤渲染，**禁止**把"上一轮的卡片"复制过来改 ID 后缀（如 `-friend` / `-v2`）当新产物输出，**禁止**凭记忆/凭印象自绘卡片或报告。
>
> ## 渲染步骤（强制）
>
> 1. **题目卡片（§T1）**：`Read references/questions.md` 解析 `## 题库` 段 44 题 `questions` 数组（字段：`id/question/prompt/options[{option,dimension,content}]`，顺序 id 1→44，不可增删改字段）；再 `Read` 本文件，把 §T1 代码块中 `/*__QUESTIONS_JSON__*/` 占位符**替换**为该数组的 JSON 字面量，其余字符原样保留，作为 Visualizer `widget_code` 输出。
> 2. **测评报告（§T2）**：调用 `python scripts/calculate_mbti.py --answers '<remap 后 JSON>' --compact` 得到报告 JSON；再 `Read` 本文件，把 §T2 代码块中 `/*__REPORT_JSON__*/` 占位符**替换**为该 JSON 字面量，其余字符原样保留，作为 Visualizer `widget_code` 输出。
> 3. **byte-stable 校验（强制）**：除两处数据占位符被替换外，模板中所有 CSS / 类名 / ID / HTML 结构 / 文案 / JS 逻辑必须与模板**逐字符一致**。每次渲染结果（同一数据）必须 byte-equal。

## 题目卡片模板（§T1）

下方代码块内容为题目卡片完整 HTML。**只替换 `/*__QUESTIONS_JSON__*/`**：

```html
<style>
#mbti-card{font-family:var(--font-sans);color:var(--color-text-primary);max-width:680px;margin:0 auto}
#mbti-card .q-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:2px}
#mbti-card .q-title{font-size:18px;font-weight:500;margin:0}
#mbti-card .q-sub{font-size:13px;color:var(--color-text-secondary);margin:2px 0 12px}
#mbti-card .q-count{font-size:13px;font-weight:500;color:var(--color-text-secondary)}
#mbti-card .q-track{height:6px;border-radius:999px;background:var(--color-background-secondary);overflow:hidden;margin-bottom:16px}
#mbti-card .q-track i{display:block;height:100%;width:0;border-radius:999px;background:var(--color-text-info);transition:width .2s}
#mbti-card .q-sec{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:12px 16px;margin:14px 0}
#mbti-card .q-sec-t{font-size:14px;font-weight:500;margin:0 0 4px}
#mbti-card .q-sec-d{font-size:12px;color:var(--color-text-secondary);line-height:1.6;margin:0}
#mbti-card .q-item{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:12px 16px;margin-top:10px;scroll-margin-top:12px}
#mbti-card .q-item.miss{border-color:var(--color-text-danger);box-shadow:0 0 0 1px var(--color-text-danger)}
#mbti-card .q-top{display:flex;gap:10px;align-items:flex-start}
#mbti-card .q-num{flex:none;min-width:26px;height:26px;border-radius:999px;background:var(--color-background-secondary);color:var(--color-text-secondary);font-size:13px;font-weight:500;display:flex;align-items:center;justify-content:center;margin-top:1px}
#mbti-card .q-body{flex:1;min-width:0}
#mbti-card .q-text{font-size:14px;font-weight:500;line-height:1.5;margin:0}
#mbti-card .q-prompt{font-size:12px;color:var(--color-text-tertiary);line-height:1.6;margin:4px 0 10px}
#mbti-card .q-opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#mbti-card .q-opt{font-family:inherit;font-size:13px;line-height:1.5;text-align:left;padding:9px 12px;border-radius:var(--border-radius-md);cursor:pointer;background:#F5F6F8;border:1px solid #E5E7EB;color:#3A3F47;transition:background .15s,border-color .15s,color .15s}
#mbti-card .q-opt:hover{border-color:var(--color-border-secondary)}
#mbti-card .q-opt.on{background:#E8F1FF;border:1px solid #4E8CFF;color:#1E4FB8;box-shadow:inset 3px 0 0 #4E8CFF}
#mbti-card .q-foot{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:16px;flex-wrap:wrap}
#mbti-card .q-tip{font-size:13px;color:var(--color-text-danger);display:none}
#mbti-card .q-submit{font-family:inherit;font-size:14px;font-weight:500;padding:10px 22px;border-radius:var(--border-radius-md);cursor:pointer;background:#4E8CFF;color:#FFFFFF;border:1px solid #4E8CFF;transition:background .15s}
#mbti-card .q-submit:hover{background:#3A78E0}
@media (max-width:560px){#mbti-card .q-opts{grid-template-columns:1fr}}
</style>
<div id="mbti-card">
  <div class="q-head"><h2 class="q-title">MBTI 职业性格测评</h2><span class="q-count" id="mbtiCount">0 / 44</span></div>
  <p class="q-sub">共 44 题，请根据真实感受选择"A"或"B"</p>
  <div class="q-track"><i id="mbtiBar"></i></div>
  <div id="mbtiList"></div>
  <div class="q-foot">
    <span class="q-tip" id="mbtiTip"></span>
    <button type="button" class="q-submit" id="mbtiSubmit">提交测评</button>
  </div>
</div>
<script>
(function(){
  var QUESTIONS = /*__QUESTIONS_JSON__*/;
  var SECTIONS=[
    {name:"第一部分 外倾-内倾（E/I）",desc:"下面列举了若干情境，请根据你通常的思考和行为方式选择最接近的答案。选 A 即倾向外倾（E），选 B 即倾向内倾（I）。请按顺序回答本部分全部 11 题。",ids:[1,2,3,4,5,6,7,8,9,10,41]},
    {name:"第二部分 实感-直觉（S/N）",desc:"下面列举了若干情境，请根据你通常接收信息的方式选择最接近的答案。选 A 即倾向实感（S），选 B 即倾向直觉（N）。请按顺序回答本部分全部 11 题。",ids:[11,12,13,14,15,16,17,18,19,20,42]},
    {name:"第三部分 思维-情感（T/F）",desc:"下面列举了若干情境，请根据你通常做决策的方式选择最接近的答案。选 A 即倾向思维（T），选 B 即倾向情感（F）。请按顺序回答本部分全部 11 题。",ids:[21,22,23,24,25,26,27,28,29,30,43]},
    {name:"第四部分 判断-知觉（J/P）",desc:"下面列举了若干情境，请根据你通常的生活方式选择最接近的答案。选 A 即倾向判断（J），选 B 即倾向知觉（P）。请按顺序回答本部分全部 11 题。",ids:[31,32,33,34,35,36,37,38,39,40,44]}
  ];
  var QMAP={},i;
  for(i=0;i<QUESTIONS.length;i++){QMAP[QUESTIONS[i].id]=QUESTIONS[i];}
  var ANSWERS={},pos=0;
  var list=document.getElementById('mbtiList'),count=document.getElementById('mbtiCount'),bar=document.getElementById('mbtiBar'),tip=document.getElementById('mbtiTip'),submit=document.getElementById('mbtiSubmit');
  var html='';
  SECTIONS.forEach(function(sec){
    html+='<div class="q-sec"><p class="q-sec-t">'+sec.name+'</p><p class="q-sec-d">'+sec.desc+'</p></div>';
    sec.ids.forEach(function(id){
      pos++;
      var q=QMAP[id],opts='';
      for(var k=0;k<q.options.length;k++){
        var o=q.options[k];
        opts+='<button type="button" class="q-opt" data-pos="'+pos+'" data-v="'+o.option+'">'+o.option+'. '+o.content+'</button>';
      }
      html+='<div class="q-item" id="q-'+pos+'"><div class="q-top"><span class="q-num">'+pos+'</span><div class="q-body"><p class="q-text">'+q.question+'</p><p class="q-prompt">'+q.prompt+'</p><div class="q-opts">'+opts+'</div></div></div></div>';
    });
  });
  list.innerHTML=html;
  var optBtns=list.querySelectorAll('.q-opt');
  for(i=0;i<optBtns.length;i++){
    optBtns[i].onclick=function(){
      var p=this.getAttribute('data-pos');
      var sib=this.parentNode.querySelectorAll('.q-opt');
      for(var j=0;j<sib.length;j++){sib[j].classList.remove('on');}
      this.classList.add('on');
      ANSWERS[p]=this.getAttribute('data-v');
      var done=0;
      for(var n=1;n<=44;n++){if(ANSWERS[n])done++;}
      count.textContent=done+' / 44';
      bar.style.width=Math.round(done/44*100)+'%';
      tip.style.display='none';
    };
  }
  submit.onclick=function(){
    var miss=null,missCount=0;
    for(var n=1;n<=44;n++){
      if(!ANSWERS[n]){if(!miss)miss=n;missCount++;}
    }
    if(missCount>0){
      tip.textContent='还有 '+missCount+' 题未作答，请先完成第 '+miss+' 题';
      tip.style.display='block';
      var el=document.getElementById('q-'+miss);
      if(el){
        el.classList.add('miss');
        el.scrollIntoView({behavior:'smooth',block:'center'});
        setTimeout(function(){el.classList.remove('miss');},1600);
      }
      return;
    }
    var sorted={};
    for(var m=1;m<=44;m++){sorted[m]=ANSWERS[m];}
    sendPrompt('[MBTI测评提交] 我的答案如下：'+JSON.stringify(sorted));
  };
})();
</script>
```

> §T1 说明：JS 内置 DISPLAY_ORDER（EI:1-10+41 / SN:11-20+42 / TF:21-30+43 / JP:31-40+44），按四段渲染，每题视觉编号=全局顺序号 1→44；选项按钮文本强制取 `content` 原文（前缀 `A.`/`B.`），禁止用维度字母；提交时回传视觉位置键 JSON `{"1":"A",...,"44":"B"}`（模型收到后必须按 SKILL.md §3.2.2 做 remap 再调评分脚本）。

## 测评报告模板（§T2）

下方代码块内容为测评报告完整 HTML。**只替换 `/*__REPORT_JSON__*/`**：

```html
<style>
#mbti-rpt{max-width:680px;margin:0 auto;color:var(--color-text-primary);font-size:13px;line-height:1.6}
#mbti-rpt .r-hdr{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;padding-bottom:14px;border-bottom:0.5px solid var(--color-border-tertiary)}
#mbti-rpt .r-type{font-size:30px;font-weight:500;letter-spacing:2px}
#mbti-rpt .r-hdr .r-nm{font-size:15px;font-weight:500;color:var(--color-text-secondary)}
#mbti-rpt .r-meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0 4px}
#mbti-rpt .r-mc{background:var(--color-background-secondary);border-radius:var(--border-radius-md);padding:12px 14px}
#mbti-rpt .r-mc b{display:block;font-size:24px;font-weight:500;line-height:1.3}
#mbti-rpt .r-mc span{font-size:12px;color:var(--color-text-secondary)}
#mbti-rpt .r-bar8{display:flex;gap:4px;margin:14px 0 4px}
#mbti-rpt .r-bar8 div{flex:1;border-radius:6px;padding:6px 0 4px;text-align:center;font-size:11px;line-height:1.4;background:var(--color-background-secondary);color:var(--color-text-tertiary)}
#mbti-rpt .r-bar8 .v{font-size:12px;color:var(--color-text-secondary)}
#mbti-rpt .r-bar8 div.win{background:var(--dbg);color:var(--dc)}
#mbti-rpt .r-bar8 div.win .v{color:var(--dc)}
#mbti-rpt .r-cap{font-size:11px;color:var(--color-text-tertiary);text-align:center;margin-bottom:2px}
#mbti-rpt .r-dim{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-left:3px solid var(--color-border-secondary);border-radius:var(--border-radius-lg);padding:14px 16px;margin-top:14px}
#mbti-rpt .r-dim.t-ei,#mbti-rpt .r-dim.t-sn,#mbti-rpt .r-dim.t-tf,#mbti-rpt .r-dim.t-jp{border-left-color:var(--dc)}
#mbti-rpt .r-dimh{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap}
#mbti-rpt .r-dn{font-size:13px;font-weight:500}
#mbti-rpt .r-win{font-size:12px;font-weight:500;border-radius:999px;padding:3px 12px;background:var(--dbg);color:var(--dc)}
#mbti-rpt .r-pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
#mbti-rpt .r-side .r-nm{font-size:13px;font-weight:500;display:flex;justify-content:space-between;margin-bottom:6px}
#mbti-rpt .r-side .r-pct{color:var(--color-text-secondary);font-weight:400}
#mbti-rpt .r-track{height:8px;border-radius:999px;background:var(--color-background-secondary);overflow:hidden}
#mbti-rpt .r-track i{display:block;height:100%;border-radius:999px;background:var(--color-border-secondary)}
#mbti-rpt .r-side.win .r-track i{background:var(--dc)}
#mbti-rpt .r-side.win .r-pct{color:var(--dc);font-weight:500}
#mbti-rpt .r-feat{font-size:12px;color:var(--color-text-secondary);margin-top:6px;line-height:1.6}
#mbti-rpt .r-side.win .r-feat{color:var(--dc)}
#mbti-rpt details{margin-top:12px;border-top:0.5px dashed var(--color-border-tertiary);padding-top:10px}
#mbti-rpt summary{cursor:pointer;font-size:13px;font-weight:500;color:var(--color-text-info)}
#mbti-rpt .r-txt{font-size:13px;line-height:1.75;margin:0}
#mbti-rpt .r-sec{font-size:12px;font-weight:500;margin:14px 0 6px;color:var(--color-text-info);border-left:3px solid var(--color-border-info);padding-left:8px}
#mbti-rpt .r-dim .r-sec{color:var(--dc);border-left-color:var(--dc)}
#mbti-rpt .r-duo{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#mbti-rpt .r-sc{border:0.5px solid var(--color-border-tertiary);border-left:3px solid var(--dc);border-radius:var(--border-radius-md);padding:10px 12px;background:var(--color-background-secondary)}
#mbti-rpt .r-sc .h{font-size:13px;font-weight:500;margin-bottom:4px}
#mbti-rpt .r-sc .f{font-size:12px;color:var(--dc);margin-bottom:6px;font-weight:500}
#mbti-rpt .r-sc p{font-size:12px;line-height:1.7;margin:0 0 6px;color:var(--color-text-secondary)}
#mbti-rpt .r-feats{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#mbti-rpt .r-feat2{border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-md);padding:12px 14px}
#mbti-rpt .r-feat2 .h{font-size:13px;font-weight:500;margin-bottom:6px}
#mbti-rpt .r-feat2 p{font-size:12px;line-height:1.75;margin:0;color:var(--color-text-secondary)}
#mbti-rpt .r-feat2.adv{border-left:3px solid var(--color-border-success)}
#mbti-rpt .r-feat2.adv .h{color:var(--color-text-success)}
#mbti-rpt .r-feat2.dis{border-left:3px solid var(--color-border-warning)}
#mbti-rpt .r-feat2.dis .h{color:var(--color-text-warning)}
#mbti-rpt .r-tags{display:flex;flex-wrap:wrap;gap:6px}
#mbti-rpt .r-tag{font-size:12px;border-radius:999px;padding:4px 12px;border:0.5px solid var(--color-border-tertiary);font-weight:500;color:var(--color-text-secondary);background:var(--color-background-secondary)}
#mbti-rpt .r-note{font-size:12px;color:var(--color-text-tertiary);margin-top:16px;line-height:1.7;background:var(--color-background-secondary);border:0.5px dashed var(--color-border-tertiary);border-radius:var(--border-radius-md);padding:10px 14px}
#mbti-rpt .t-ei{--dc:#185FA5;--dbg:#E6F1FB}
#mbti-rpt .t-sn{--dc:#3B6D11;--dbg:#EAF3DE}
#mbti-rpt .t-tf{--dc:#534AB7;--dbg:#EEEDFE}
#mbti-rpt .t-jp{--dc:#BA7517;--dbg:#FAEEDA}
@media (prefers-color-scheme:dark){
#mbti-rpt .t-ei{--dc:#85B7EB;--dbg:#0C447C}
#mbti-rpt .t-sn{--dc:#C0DD97;--dbg:#27500A}
#mbti-rpt .t-tf{--dc:#AFA9EC;--dbg:#3C3489}
#mbti-rpt .t-jp{--dc:#FAC775;--dbg:#633806}
}
@media (max-width:560px){#mbti-rpt .r-pair,#mbti-rpt .r-duo,#mbti-rpt .r-feats,#mbti-rpt .r-meta{grid-template-columns:1fr}}
</style>
<div id="mbti-rpt"></div>
<script>
(function(){
  var R = /*__REPORT_JSON__*/;
  if(!R||!R.dominant_type||!R.role_detail){return;}
  var PAIR_CLS={EI:'t-ei',SN:'t-sn',TF:'t-tf',JP:'t-jp'};
  var PAIR_OF={E:'EI',I:'EI',S:'SN',N:'SN',T:'TF',F:'TF',J:'JP',P:'JP'};
  var h='';
  h+='<div class="r-hdr"><span class="r-type">'+R.dominant_type+'</span><span class="r-nm">'+R.role_detail.name+'</span></div>';
  var wins=R.dimension_pairs.map(function(p){return p.result;}).join(' · ');
  h+='<div class="r-meta">';
  h+='<div class="r-mc"><b>'+R.display_score+'</b><span>倾向强度</span></div>';
  h+='<div class="r-mc"><b>'+R.role_detail.proportion+'%</b><span>人群占比</span></div>';
  h+='<div class="r-mc"><b>'+wins+'</b><span>胜出维度</span></div>';
  h+='</div>';
  var letters=['E','I','S','N','T','F','J','P'];
  h+='<div class="r-bar8">';
  for(var i=0;i<8;i++){
    var L=letters[i],pair=PAIR_OF[L],cls='';
    var dp=R.dimension_pairs.filter(function(x){return x.pair===pair;})[0];
    if(dp&&dp.result===L){cls='win '+PAIR_CLS[pair];}
    h+='<div class="'+cls+'">'+L+'<span class="v">'+R.dimension_counts[L]+'</span></div>';
  }
  h+='</div><div class="r-cap">胜出维度标色 · 数值=该端答对题数</div>';
  R.dimension_pairs.forEach(function(p){
    var cls=PAIR_CLS[p.pair];
    h+='<div class="r-dim '+cls+'">';
    h+='<div class="r-dimh"><span class="r-dn">'+p.dimension_name+'</span><span class="r-win">胜出：'+p.result+' '+p.result_name+'</span></div>';
    h+='<div class="r-pair">';
    h+=side(p,1,p.option1,p.name1,p.score1,p.percent1,p.option1_detail,cls);
    h+=side(p,2,p.option2,p.name2,p.score2,p.percent2,p.option2_detail,cls);
    h+='</div>';
    h+='<details><summary>维度解读</summary>';
    h+='<p class="r-sec">胜出端特质</p><p class="r-txt">'+p.result_traits+'</p>';
    h+='<p class="r-sec">维度解读</p><p class="r-txt">'+p.dimension_description+'</p><p class="r-txt">'+p.dimension_prompt+'</p>';
    h+='<p class="r-sec">两端详情对比</p><div class="r-duo">';
    h+='<div class="r-sc"><div class="h">'+p.option1_detail.name+'</div><div class="f">'+p.option1_detail.feature+'</div><p>'+p.option1_detail.traits+'</p><p>'+p.option1_detail.characteristics+'</p></div>';
    h+='<div class="r-sc"><div class="h">'+p.option2_detail.name+'</div><div class="f">'+p.option2_detail.feature+'</div><p>'+p.option2_detail.traits+'</p><p>'+p.option2_detail.characteristics+'</p></div>';
    h+='</div></details>';
    h+='</div>';
  });
  h+='<div class="r-dim"><p class="r-sec">特点分析</p><div class="r-feats">';
  h+='<div class="r-feat2 adv"><div class="h">优势</div><p>'+R.role_detail.advantages+'</p></div>';
  h+='<div class="r-feat2 dis"><div class="h">缺点</div><p>'+R.role_detail.disadvantages+'</p></div>';
  h+='</div></div>';
  h+='<div class="r-dim"><p class="r-sec">职业推荐</p><p class="r-txt">'+R.analysis.summary+'</p><div class="r-tags">';
  R.analysis.recommendations.forEach(function(t){h+='<span class="r-tag">'+t+'</span>';});
  h+='</div></div>';
  h+='<div class="r-note">本报告基于 MBTI 职业性格测评（44 题）计算结果生成，供职业规划参考，不构成绝对结论。</div>';
  document.getElementById('mbti-rpt').innerHTML=h;
  function side(p,n,opt,name,score,percent,detail,cls){
    var s='<div class="r-side '+(p.result===opt?'win':'')+'">';
    s+='<div class="r-nm">'+opt+' '+name+'<span class="r-pct">'+score+' 题 · '+percent+'%</span></div>';
    s+='<div class="r-track"><i style="width:'+percent+'%"></i></div>';
    s+='<div class="r-feat">'+detail.feature+'</div>';
    s+='</div>';
    return s;
  }
})();
</script>
```

> §T2 说明：数据源为 `calculate_mbti.py --compact` 输出 JSON（唯一数据来源）。渲染结构固定：标题区 → 指标卡（3 个 .r-mc）→ 8 字母计数条（.r-bar8，胜出格带 `win t-xx` 双类）→ 4 个维度卡（EI/SN/TF/JP，主题类 t-ei/t-sn/t-tf/t-jp，胜出端 .r-side 带 win，details 内固定三段：胜出端特质 / 维度解读 / 两端详情对比）→ 特点分析（优势/缺点）→ 职业推荐（summary + tags）→ 底部 note。8 端详情（option1_detail/option2_detail 共 8 端，各含 name/feature/traits/characteristics）必须全部渲染，禁止只展示胜出端。
