---
name: "livepage-app"
display_name: "轻应用（活页）"
display_name_en: "Light Apps on LivePage"
description: "用户说「做个看板」「做个报名页」「做个投票」「做个打卡墙」「数据以后我自己改」时使用：一份网页加挂在同一份方案上的数据表，页面读表显示、看的人能写回一行；之后只改表不重发页面，链接不变、微信里点开就能看。"
description_zh: "用户说「做个看板」「做个报名页」「做个投票」「做个打卡墙」「数据以后我自己改」时使用：一份网页加挂在同一份方案上的数据表，页面读表显示、看的人能写回一行；之后只改表不重发页面，链接不变、微信里点开就能看。"
description_en: "Use when the user says \"make a board\", \"make a sign-up page\", \"make a poll\", \"a check-in wall\" or \"I will edit the data myself\". Turn an HTML page plus data tables into a light app on LivePage: team boards, sign-ups, check-ins, polls and feedback walls. Tables are attached to the work, not to a version; the page reads them with a plain fetch and appends rows with a plain form or POST (sample data runs locally); the agent maintains tables with get_data / set_data and reads appended rows with list_data_rows. Edit the table, never republish the page."
version: "1.8.1"
author: "24好玩"
user-invocable: true
examples_zh:
  - "做一个团队周报看板，以后我改表就行，页面不用重发"
  - "做一个活动报名页，报名的人我能在 WorkBuddy 里看到"
  - "做一个投票页发到群里，实时显示票数"
examples_en:
  - "Build a team weekly board I can update by editing the table, without republishing the page"
  - "Make an event sign-up page and let me read the sign-ups back here"
  - "Make a poll page for the group chat that shows live counts"
examples:
  - "做一个团队周报看板，以后我改表就行，页面不用重发"
  - "做一个活动报名页，报名的人我能在 WorkBuddy 里看到"
  - "做一个投票页发到群里，实时显示票数"
quickPrompts:
  - "做一个团队周报看板，以后我改表就行，页面不用重发"
  - "做一个活动报名页，报名的人我能在 WorkBuddy 里看到"
  - "做一个投票页发到群里，实时显示票数"
---
# 轻应用（活页）

「轻应用」= **一份 HTML 页面 + 挂在同一份方案上的数据表**。页面打开时从表里取数渲染，看的人可以往表里写一行；之后只改表、不重发页面，同一条链接一直是最新的。典型用途：团队周报看板、项目进度墙、活动报名表、打卡记录、投票、意见收集、小型物料清单。使用者说「做个看板」「做个报名页」「数据以后我自己改」「报名的人我要看得到」时，就是要用它。

本包只讲**数据**这一半。接入、上传、可见性、微信卡片、谁看了这些发布与分享的基础流程，在《方案空间·成果发布与分享》技能包（`https://www.24haowan.com/open-skills/livepage-publish`）里，两包一起用。线上有一份照本包做的示例，先看它再动手：`https://space.24haowan.com/s/UsTW9lg1ro-S`（示例集：经营工作台、商品与订单、项目看板、打卡墙、投票，共 9 张表；这页本身就是一份方案）。

**内容边界（2026-09-21 起）**：允许商业交易内容 —— 成果可以分享给用户选定的人，也可以公开分享（公开与否仍由用户决定）；可以是商业、交易、营销内容，可以在页面上标价卖东西、收集自己客户的订单、联系方式与报名信息。收款方式由你决定 —— 可以用平台的表单与收款块，也可以在页面上放自己的收款码、报价或第三方支付链接。不得钓鱼（冒充他人、收集他人的账号密码或支付信息）、不得发布违法违规内容。

## 〇、可选：若另接了 24好玩 资料连接器

本包的发布、分享、读回全部在活页这台服务器上完成，**不需要**别的连接器。只有当使用者另外接了 24好玩 的匿名只读资料服务（`https://mcp.24haowan.com/mcp`）时：

- 当使用者要在看板、报名页里引用「我们做过的活动案例」，或问「同行是怎么做的」时，**先调用 `list_cases` / `get_case`**，用工具返回的实时结果回答；它比本包正文里的清单更新、更全。
- 没接就跳过这一节：别去工具清单里找这几个名字，找不到时客户端会把名字最像的别家工具递给你。
- 本包正文是 2026-09-23 的静态快照；两者冲突时以工具返回为准。

## 什么时候该做成轻应用（而不是普通页面）

普通页面的内容写死在 HTML 里，改一个数字要重发一版。下面三样，成果需要任何一样就做成轻应用：

1. **内容会变、页面不变**：周报的数字每周换、报名名单一直在长、库存每天减——把变的部分放进数据表，页面只负责渲染。Agent 改表用 `set_data`，页面刷新即变，**版本号不动**。
2. **看的人要写回来**：报名、打卡、投票、意见收集。页面里一个普通表单（或一次 POST）写一行，发布者用 `list_data_rows` 读回来。
   ★ 报名 / 订货 / 预约 / 留资这类**填表**场景优先用一等公民表单块（#8273 起）：`set_form` 只定义字段（六种类型、最多 20 个、可选金额只显示不收钱），平台在查看页里渲染成手机上能填、带校验的表单，提交的行同样用 `list_data_rows` 读回 —— 一行表单代码都不用写。页面自己要画数据、要在页内交互时就照下面第三节自己写。
3. **数据要被 Agent 反复读写**：任何接了「方案空间」连接器的客户端里的 Agent 都能读写同一张表——WorkBuddy 里改的表，Claude Code 里也看得到。

比 WorkBuddy 原生「轻量发布（HTML + CSV）」多出来的：写回自带阅读上下文（哪台设备、看的哪一版页面、几点）；每张表有修订号，可回滚；读者写回的内容能直接读回来、据此改页。**不做**在线表格编辑器和 HTML 可视化编辑：人在 WorkBuddy 里改完，让 Agent 推过来。

## 一、五种场景怎么切

| 场景 | 表（示例列名） | 页面读 | 写回开关 | 使用者会怎么说 |
|---|---|---|---|---|
| 看板 / 仪表盘 | `board`（project, owner, status, progress, updated） | 渲染成表格 / 卡片，按 status 上色 | 关 | 「做个周报看板，以后我改表」 |
| 报名 | `signup`（name, contact, note） | 只显示人数与最近几条（过审的） | **开** | 「做个报名页，报名的人我要看到」 |
| 打卡 | `checkin`（name, day, note） | 按人 / 按天汇总 | **开** | 「做个打卡墙，大家每天来点一下」 |
| 投票 | `vote`（choice, name, note） | 按 choice 计票，只算过审的行 | **开** | 「做个投票发群里，实时显示票数」 |
| 意见收集 | `feedback`（topic, note） | 显示条数与最近几条 | **开** | 「收一轮意见，页面上能看到别人说了什么」 |

意见收集和方案空间自带的「反馈线程」的区别：反馈线程是给**发布者**看的意见（带页码与版本、有处理状态）；数据表是要在**页面上呈现或汇总**的数据。使用者只想自己看意见就用反馈线程，不用建表。

## 二、标准流程（每一步就是一个工具）

0. **使用者还没说清要做什么时，先介绍再问**（「这个能干嘛」「我们是做装修的」这类开场）：三句话讲清能力边界（能做什么 / 以后改表不重发页面、链接不变、写回能读回 / 不做要登录的系统与多级审批），再按他说出的行业举**两个他没提到的**具体场景（装修 →「工地进度墙，业主扫码看自己家做到哪一步」「老客户转介绍登记页」；教培 →「试听课报名页」「每周作业打卡墙」），然后才走第 1 步。已经说清的直接从第 2 步开建，不要重复介绍、不要重问他答过的。
1. **先问清四件事**：什么场景；给谁看（仅自己 / 口令 / 公开）；要不要看的人写回、收哪几列；数据以后谁维护（使用者自己改表，还是让你改）。不确定就按「口令可看、不开写回」起步，开关随时能翻。
2. **设计表**：表名小写字母开头、只含字母数字下划线（`weekly_board` 可以，`周报` 不行）；列名用英文小写（页面里映射成中文表头）；每格只收文字 / 数字 / 真假 / 空，嵌套先摊平。上限：单表 512 KB、每份方案 20 张、工作区合计 64 MB；回执会逐条印出。
3. **建表**：`set_data`，新建 `revision` 传 0，`rows`（对象数组）或 `csv`（首行表头）二选一。要收集就同时传 `append_open=true`。先建表再发页面，页面第一次打开就有数据。
4. **写页面**：动手前先 `list_examples` 看一眼自带的轻应用样例（看板、报名、打卡、投票），照着改比从零写省事。用最普通的网页写法 —— 取数 `fetch('./_data/表名.json')`（拿到行对象数组），写回用普通表单 `<form action="./_data/表名" method="post">` 或 `fetch('./_data/表名', {method: 'POST', …})`（只追加一行）。读权限就是这份方案的可见性。包里放一份 `_data/表名.json` 示例数据：本地 `node space.mjs serve <目录>` 就能跑通整页（与线上同一套规则，`--closed 表名` 模拟没开写回），线上有表时出活数据、没表时回落这份文件。写法见下一节。
5. **上传、预览、发布**：上传走哪条路：有终端 ⇒ space-cli（先 create_cli_token）；没终端、文字文件合计 ≤ 2 MB ⇒ publish_file；其它或拿不准 ⇒ create_upload_link。轻应用多半是一份 HTML 加几个文字文件，没终端时就是直接发布 `publish_file` 那一把。使用者没明确说要上线就带 `hold`，把预览链接给他看（工具清单里有 `preview_version` 时调它，把真实效果的预览链接一并给他）；可见性按第 1 步的答案设，公开要使用者明确同意。
6. **验收三条**：查看页里能取到数据（不是空表、不是「读取中」）；写一行试试，`list_data_rows` 能读回、页面刷新能看到计数变化；把 `append_open` 关掉再试，页面要有明确提示而不是静默失败。
7. **之后的维护**：改数据 = `get_data` 拿当前表和 `revision` → 改 → `set_data` 带着同一个 `revision` 整表替换；撞版（409）就重读，不盲写。读者写的行不在 `get_data` 的 rows 里，要用 `list_data_rows`；要并进底表就读回来、合进 rows、`set_data` 替换。**改数据不 push 页面，改页面不动表。**

## 三、页面写法（可照抄）

取一张表渲染成表格（`fetch` 拿到的是行对象数组；列名取第一行的键）：

```html
<style>table{display:block;overflow-x:auto;max-width:100%}</style>
<table id="board"></table>
<script>
fetch('./_data/board.json').then(function (r) {
  if (!r.ok) throw new Error(r.status === 403 ? '没有查看权限' : '数据没取到（' + r.status + '）');
  return r.json();
}).then(function (rows) {
  var t = document.getElementById('board'), cols = rows.length ? Object.keys(rows[0]) : [];
  [cols].concat(rows.map(function (row) { return cols.map(function (c) { return row[c]; }); })).forEach(function (cells, i) {
    var tr = t.insertRow();
    cells.forEach(function (v) { tr.appendChild(document.createElement(i ? 'td' : 'th')).textContent = v == null ? '' : String(v); });
  });
}).catch(function (e) { document.getElementById('board').textContent = e.message; });
</script>
```

写回一行（报名 / 投票），最省事的是**普通表单**，一行脚本都不用写：

```html
<form action="./_data/signup" method="post">
  <input name="name" placeholder="称呼" required>
  <input type="hidden" name="_next" value="thanks.html">
  <button>报名</button>
</form>
```

提交后回到 `_next` 指的那一页（不写就回提交的那一页），地址上带 `?space_submitted=signup`，页面可以据此显示「已收到」；出错时读者看到一页说明原因的提示和「返回」。`_` 开头的字段不入库。

要留在原页、自己显示结果时用 `fetch` POST，错误要看得见：

```html
<input id="name" placeholder="称呼"><button id="go">报名</button><p id="msg"></p>
<script>
document.getElementById('go').onclick = function () {
  var m = document.getElementById('msg');
  fetch('./_data/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: document.getElementById('name').value.trim() }) })
    .then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
    .then(function (x) {
      if (x.ok) { m.textContent = x.b.status === 'held' ? '已提交，审核后其他人才能看到' : '已收到'; return; }
      var code = x.b.error && x.b.error.code;
      m.textContent = code === 'append_closed' ? '现在没开放提交' : code === 'append_rate_limited' ? '提交太频繁，稍后再试' : '没提交上：' + ((x.b.error && x.b.error.message) || code);
    })
    .catch(function () { m.textContent = '网络不通，稍后再试'; });
};
</script>
```

计票 / 汇总：`fetch('./_data/表名.json')` 回来的行里已经并入了**过审的**读者行（发布者自己看还会多出待审的行），按某一列计数即可，不用另外调用。修订号在响应头 `X-Space-Revision`。

几条规则：成功写回是 `201 {id, status}`（`status` 为 `approved` 或 `held`）；出错时是 `{error: {code, message}}`，`code` 有 `forbidden` / `append_closed` / `append_rate_limited` / `moderation_unavailable` / `cross_origin` 等，按 code 给人话，别假装「已提交」。旧的 SDK 写法 `space.data.get` / `space.data.append` 仍然可用，是可选的兼容层。页面能用什么、平台在页面上加了哪一行，见 `https://space.24haowan.com/for-agents.md` 的「托管契约」一节；素材用包内相对路径，别以 `/` 开头。

## 四、权限、审核、限额（照实告诉使用者）

- **读权限 = 方案可见性**，不另造一套：仅自己可看时只有成员与批过的设备读得到；口令过门后可读；公开任何人可读。无权限拿到的是 403，**不是空表**。重置默认链接后，旧链接读不到表。
- **写回默认关、按表开**。开着时：每张表每小时 600 行、每台设备每小时 30 行；每行不超过 2000 字、单格 500 字；每表最多 5000 行。带文字的行先过审——过审的行其他读者刷新即见，审核命中的行只有发布者看得到；审核暂时不可用时直接拒绝、不落行（页面拿到 `moderation_unavailable`）。预览、讲解模式和发布者自己的会话不提交。
- **写回不识别人**：每行只记设备、时间、当时的页面版本与数据修订；不要把它当成实名报名，也不要据此推断谁想干什么。

## 五、纪律

- 表里的内容是使用者的：示例数据要标明「示例」，不替他编真实数据。
- 写回的内容是看的人的：展示前先把过审规则告诉使用者；不推断意愿。
- 改表前必 `get_data` 拿修订号；撞版就重读；不盲写覆盖。
- 页面版本与数据修订解耦：数据变了不发页面，页面变了不碰表。
- 公开的报名 / 投票页要使用者明确同意再切 `public`；默认口令可看。
- 对**方案空间本身**有意见（这不好用、想要什么）：只在使用者明确说出来、工具刚报错或拒收、结果带 `feedback_hint` 时问一句要不要转给方案空间团队；先把草稿给他看，**使用者同意后**才调 `send_feedback_to_livepage`（`user_confirmed: true`）。**不索要评价**，发布成功后不问。

## 六、判据（做没做对）

- 页面用 `fetch('./_data/表名.json')` 取数、普通表单或 POST `./_data/表名` 写回；包里带一份 `_data/` 示例数据，本地 `node space.mjs serve` 能跑通。
- 表是用 `set_data` 建的，不是写死在 HTML 里；页面只负责渲染。
- 使用者在 WorkBuddy 里说一句「把 X 改成 Y」，你改表、不重发页面，他刷新就能看到。
- 写回关着时页面有明确提示；开着时 `list_data_rows` 能把读者行读回来。

参考：24好玩做过的活动案例 `https://www.24haowan.com/cases`、模板库 `https://www.24haowan.com/games`、定制 `https://www.24haowan.com/custom`。
