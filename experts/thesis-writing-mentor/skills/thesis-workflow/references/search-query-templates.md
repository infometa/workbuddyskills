# 分库检索式模板

## 使用边界

- 先把研究问题拆为对象、现象/暴露、情境、理论和方法五组概念，再为每组维护中英文同义词；并非每次都必须把五组全部放入首轮检索。
- 下列字段名、运算符和界面可能随数据库版本、机构入口、语言和检索模式变化，**必须以各数据库当前官方检索说明及用户实际界面为准**。若粘贴后报错，保留概念组并按官方帮助调整语法，不猜测字段代码。
- 不主动登录、访问、抓取或绕过知网、万方、维普及其他付费或机构授权数据库。用户在其有权使用的入口自行粘贴、检索和导出，专家只生成检索式、解释字段并整理回填材料。
- 可粘贴不等于检索结果已核验。实际使用的检索式、日期、筛选条件和命中数写入 `output-templates.md` 的“检索审计记录”。

## 同一研究问题示例

**研究问题**：大学生社交媒体使用与睡眠质量之间存在怎样的关系？

| 概念组 | 中文词 | 英文词 |
|---|---|---|
| 对象 | 大学生、高校学生、本科生 | university student*, college student*, undergraduate* |
| 现象/暴露 | 社交媒体、社交网络、社交平台 | social media, social networking, social network site* |
| 结果 | 睡眠质量、睡眠、睡眠障碍 | sleep quality, sleep, sleep disturbance* |
| 情境 | 高校、大学校园 | universit*, college*, campus |
| 理论/方法（按需） | 问卷、横断面、访谈 | survey, cross-sectional, interview* |

首轮通常组合“对象 AND 现象 AND 结果”；情境和方法用于结果过多时收窄，理论词用于验证特定解释框架。不要为了形式完整一次加入所有词而漏检。

## 字段对照总表

| 数据库 | 常用字段/入口 | 字段含义 | 常用逻辑 |
|---|---|---|---|
| 知网 | `SU`、`TKA`、`KY`、`TI` | 主题、篇关摘、关键词、题名；具体代码以专业检索帮助为准 | 专业检索常见 `*` 表示 AND、`+` 表示 OR；以当前帮助为准 |
| 万方 | 主题、题名、关键词、摘要、作者、作者单位、刊名 | 高级检索字段通常通过下拉框选择 | 行间选择“与/或/非”；同义词在同一输入框用界面支持的 OR 方式组合 |
| 维普 | 任意字段、题名或关键词、题名、关键词、文摘、作者、机构、刊名 | 高级检索字段通常通过下拉框选择 | 行间选择“与/或/非”；运算符以当前界面帮助为准 |
| PubMed | `[tiab]`、`[Mesh]`、`[pt]`、`[dp]` | 题名/摘要、MeSH 主题词、出版类型、出版日期 | `AND`、`OR`、`NOT`，括号控制组合 |
| Web of Science Core Collection | `TS=`、`TI=`、`AB=`、`AK=`、`PY=` | 主题、题名、摘要、作者关键词、年份 | `AND`、`OR`、`NOT`、`NEAR/x`；短语用引号 |
| Scopus | `TITLE-ABS-KEY()`、`TITLE()`、`ABS()`、`AUTHKEY()`、`PUBYEAR` | 题名摘要关键词、题名、摘要、作者关键词、年份 | `AND`、`OR`、`AND NOT`、`W/n`、`PRE/n` |
| Google Scholar | 引号、`OR`、`intitle:`、`site:`、减号 | 精确短语、并列词、题名限定、站点限定、排除词 | 功能较少；字段和括号支持不应等同专业数据库 |

## 知网

### 字段选择

- `SU=主题`：适合首轮主题检索。
- `TKA=篇关摘`：通常覆盖篇名、关键词、摘要等范围，适合较宽检索；代码和覆盖范围以当前专业检索说明为准。
- `KY=关键词`：适合验证作者关键词。
- `TI=题名`：精度高、召回低，适合锁定核心文献。

### 可粘贴模板

```text
SU=(【对象词1】+【对象词2】)*SU=(【现象词1】+【现象词2】)*SU=(【结果词1】+【结果词2】)
```

若当前专业检索要求每个表达式只写一次字段，可改用：

```text
SU=(【对象词1】+【对象词2】)*(【现象词1】+【现象词2】)*(【结果词1】+【结果词2】)
```

### 同题示例

```text
SU=(大学生+高校学生+本科生)*SU=(社交媒体+社交网络+社交平台)*SU=(睡眠质量+睡眠+睡眠障碍)
```

结果过多时把结果概念切到篇关摘或题名进行对照检索，并记录实际可运行版本；不要在未见当前界面时声称某一字段代码永久有效。

## 万方

### 字段选择

高级检索常见字段包括主题、题名、关键词、摘要、作者、作者单位和刊名。机构入口可能只支持在输入框中填写词组并用行间关系组合，因此优先给“逐行可粘贴”方案。

### 可粘贴模板

```text
第1行｜字段：主题｜内容：【对象词1】 OR 【对象词2】
第2行｜关系：与｜字段：主题｜内容：【现象词1】 OR 【现象词2】
第3行｜关系：与｜字段：主题｜内容：【结果词1】 OR 【结果词2】
```

### 同题示例

```text
第1行｜字段：主题｜内容：大学生 OR 高校学生 OR 本科生
第2行｜关系：与｜字段：主题｜内容：社交媒体 OR 社交网络 OR 社交平台
第3行｜关系：与｜字段：主题｜内容：睡眠质量 OR 睡眠 OR 睡眠障碍
```

若当前界面不接受输入框内的 `OR`，拆成更多行并把同组行关系设为“或”；不得擅自套用其他数据库字段代码。

## 维普

### 字段选择

高级检索常见字段包括任意字段、题名或关键词、题名、关键词、文摘、作者、机构和刊名。首轮可用“题名或关键词”或“任意字段”，结果过多时收窄到题名/关键词。

### 可粘贴模板

```text
第1行｜字段：题名或关键词｜内容：【对象词1】 OR 【对象词2】
第2行｜关系：与｜字段：题名或关键词｜内容：【现象词1】 OR 【现象词2】
第3行｜关系：与｜字段：题名或关键词｜内容：【结果词1】 OR 【结果词2】
```

### 同题示例

```text
第1行｜字段：题名或关键词｜内容：大学生 OR 高校学生 OR 本科生
第2行｜关系：与｜字段：题名或关键词｜内容：社交媒体 OR 社交网络 OR 社交平台
第3行｜关系：与｜字段：题名或关键词｜内容：睡眠质量 OR 睡眠 OR 睡眠障碍
```

若当前界面使用不同字段名或不接受输入框内 `OR`，按官方帮助拆行组合并在审计记录中保存最终式。

## PubMed

### 字段选择

- `[tiab]`：Title/Abstract，自由词首轮检索。
- `[Mesh]`：MeSH 主题词；先在 MeSH Database 核对当前主题词，不凭中文直译假设存在。
- `[pt]`：出版类型；仅在研究设计需要时添加。
- `[dp]`：出版日期；年份限制优先使用界面过滤器或明确日期范围。

### 可粘贴模板

```text
((【对象自由词1】[tiab] OR 【对象自由词2】[tiab] OR "【已核验对象MeSH】"[Mesh]))
AND ((【现象自由词1】[tiab] OR 【现象自由词2】[tiab] OR "【已核验现象MeSH】"[Mesh]))
AND ((【结果自由词1】[tiab] OR 【结果自由词2】[tiab] OR "【已核验结果MeSH】"[Mesh]))
```

未核验 MeSH 时删除对应占位，不把占位直接提交。

### 同题示例

```text
(("university student"[tiab] OR "university students"[tiab] OR "college student"[tiab] OR "college students"[tiab] OR undergraduate*[tiab]))
AND (("social media"[tiab] OR "social networking"[tiab] OR "social network site"[tiab] OR "social network sites"[tiab] OR "Social Media"[Mesh]))
AND (("sleep quality"[tiab] OR sleep[tiab] OR "sleep disturbance"[tiab] OR "sleep disturbances"[tiab] OR "Sleep"[Mesh]))
```

粘贴后查看 PubMed 的 Search Details，确认自动映射未改变原意，并把实际解析式写入检索审计。

## Web of Science Core Collection

### 字段选择

`TS=` 通常覆盖题名、摘要、作者关键词及 Keywords Plus 等主题字段；需要提高精度时分别使用 `TI=`、`AB=` 或 `AK=`。具体覆盖范围以当前产品帮助为准。

### 可粘贴模板

```text
TS=((【对象词1】 OR 【对象词2】) AND (【现象词1】 OR 【现象词2】) AND (【结果词1】 OR 【结果词2】))
```

### 同题示例

```text
TS=(("university student*" OR "college student*" OR undergraduate*) AND ("social media" OR "social networking" OR "social network site*") AND ("sleep quality" OR sleep OR "sleep disturbance*"))
```

如需年份，使用当前高级检索支持的年份字段或结果页筛选，并在审计记录中保存筛选条件。

## Scopus

### 字段选择

`TITLE-ABS-KEY()` 适合主题检索；`TITLE()`、`ABS()`、`AUTHKEY()` 用于收窄。邻近算符是否需要及其当前规则以官方帮助为准。

### 可粘贴模板

```text
TITLE-ABS-KEY((【对象词1】 OR 【对象词2】) AND (【现象词1】 OR 【现象词2】) AND (【结果词1】 OR 【结果词2】))
```

### 同题示例

```text
TITLE-ABS-KEY(("university student*" OR "college student*" OR undergraduate*) AND ("social media" OR "social networking" OR "social network site*") AND ("sleep quality" OR sleep OR "sleep disturbance*"))
```

使用 `PUBYEAR` 或结果页年份筛选时，把筛选式或筛选值写入审计记录，不在后续报告中省略。

## Google Scholar

### 字段选择

Google Scholar 适合发现线索，不替代专业数据库的可复现检索。引号限定短语，`OR` 连接同义词，`intitle:` 限定题名，`site:` 仅用于明确官方或机构站点，减号用于排除明显歧义。其排序、覆盖和查询解释不透明，命中数只能作为近似记录。

### 可粘贴模板

```text
("【对象短语1】" OR "【对象短语2】") ("【现象短语1】" OR "【现象短语2】") ("【结果短语1】" OR "【结果短语2】")
```

题名收窄模板：

```text
intitle:"【核心短语】" "【第二概念】" 【第三概念】
```

### 同题示例

```text
("university students" OR "college students" OR undergraduates) ("social media" OR "social networking") ("sleep quality" OR "sleep disturbance")
```

题名收窄示例：

```text
intitle:"social media" "sleep quality" students
```

发现候选后用 DOI、出版者页面或可信学术来源核验身份；Google Scholar 摘要片段不得直接升级为 M2 或 F。

## 检索交付检查

- 每个数据库均保留“原始概念组—生成式—实际运行式—筛选条件—结果数”的对应关系。
- 至少说明宽检索与窄检索的差别，不把无结果直接解释为“没有研究”。
- 中英文检索分别依据学科用语构建，不做逐词机械翻译。
- 任何需要登录、订阅、验证码或机构权限的步骤都停在用户操作边界，由用户合法检索并回填 RIS/ENW/NoteExpress 等材料。
