# 招聘流程

## 职位与待办

`get_job_list` 查职位，`get_job_detail` 取唯一职位的 JD、HC 和配置，`position_portrait` 取已有画像。职位同名先消歧，未返回画像不补造。

“我的待办”默认查当前用户负责且招聘中的职位；已知筛选值为 status=招聘中、isMyCharge=我负责的，使用前核对实时 Schema。团队范围按用户要求和服务端权限确定。

- `apply_status_resume_count` 提供状态聚合，具体名单用 `search_resumes`；不同范围的总数不能直接叠加。搜索方法见 [候选人与简历](candidates.md)。
- 待筛选按当前租户“待处理”等实际状态定位，不凭习惯猜环节编码。
- 待面评默认检查最近两周的最新轮次：明确“待评价”且逾期至少 2 天列为关注项，展示统计范围。无时间/状态字段时说明无法计算，不补 0 天。
- 已有面试结果待流转：最新轮次明确通过/不通过，且当前大环节仍为面试；待定和已进后续阶段的记录不计入。
- 按岗位相关证据与已有评估排序；系统分未返回不等于权限故障，也不是淘汰理由。看板仅给事项、数量、范围和建议，不自动执行后续动作。

报表字段含义不清时按 [分析与人才洞察](analytics.md) 查字段定义，不能用未知列或无范围汇总拼待办。

## 创建职位

使用 `upsert_position` 新增职位；它不负责修改。顶层 position 必填，内部必填 positionName、postType（字符串编码）、recruitTypes（整数编码数组）；originalPrompt 按工具定义携带用户原话。

| 编码字段 | 按名称读取的 MCP 资源模板 |
| --- | --- |
| postType | dict://JT/{dictName} |
| recruitTypes | meta://recruitType/{recruitTypeName} |
| education | dict://G%2FJD/{dictName} |
| workPlaces | dict://D%2FHP%2FHR/{dictName} |
| workTypes | dict://RD/{dictName} |

先读取必要字典再组成 position，不传中文代替编码，也不复制示例编码。使用宿主资源/模板能力；名称按模板编码，路径已有 %2F 保留，不二次编码整个 URI。普通资源列表为空不代表无模板资源，有 nextCursor 时按需翻页。无资源能力或无匹配则停止；多匹配先让用户选定。

educationAbove 为布尔值，recruitNum 为正整数；salary 单位 K，如 25-50、30-0；workYears 单位年，如 1-3、1-0、0-3。workPlaces/workTypes 为字符串数组，subject 为专业，workContent 为职责，serviceCondition 为任职要求。未说明的可选要求省略，不为填表增加门槛。

展示可读职位内容及字典匹配结果，具体内容已获授权后创建。成功须有明确结果及可识别职位，可用只读查询核对；只有一句“成功”或一个 URL 而无创建证据时不宣称已创建，结果未知不重复提交。

## 修改、刷新和发布职位

`job_operate` 只接受 update/refresh/publish，返回操作页链接；用户在页面完成最终操作。update 只传一个 jobId，refresh/publish 可用英文逗号传多个 jobIds。无明确职位范围时先补齐，不能因 Schema 将 jobIds 标可选而执行无范围操作。

## 面试

`interview_schedule` 必填 originalPrompt、整数 operateType、resumeCodeStr；人选编码来自已确认记录，多人英文逗号分隔。

- 普通面试 operateType=1：interviewPattern 为现场/电话/视频；选视频须有 interviewAgoraSystem（大易/钉钉/飞书）。interviewPlaceName 可模糊匹配地点。
- interviewerCodes 为逗号分隔的面试官编码；mainInterviewerCode 必须在其中。使用 interviewerKeyword 时须先有 interviewStage（面试/初试/复试/终试）；匹配不唯一先消歧。
- AI 面试 operateType=2：除公共字段，仅支持可选开始时间和时长，不传面试官、阶段、地点或普通面试类型字段。
- 两类均可传 interviewBeginTime（yyyy-mm-dd hh:mm）和 interviewTimeLong（整数分钟）。相对日期按当前日期与用户时区解释，有歧义先确认。

success、operateUrl、echo 表示预填结果，交付“已预填，请打开链接完成最终排期确认”。echo 可供后续校对，不是成功人选名单；无权限简历会跳过，不能声称全员已安排。改期/取消需另查真实能力，不凭 echo 推导接口或重发安排请求代替取消。

`get_video_interview_info` 用于已有面试的入口，先辨认候选人/面试官身份，不能相互错发链接。

## 岗位要求变更与协作动作

取得唯一职位的 JD/画像、流程人选和相关面试，按新要求列出“仍符合 / 受影响 / 待核实”。未写入简历的经历不直接判为不符合。给出要求差异、人选及面试影响、JD 建议、沟通草稿和动作清单；需补充人选时按新要求搜索，排除已在该职位流程中的相同人选。

| 工具 | 执行与完成标准 |
| --- | --- |
| add_resume_remark | 对已授权人选写入确定备注，未知结果先查记录 |
| contact_candidate | check/get 为检查或模板阶段；实际发送前明确对象、渠道/模板和正文，实际发送成功才报已发送；各阶段副作用以真实定义为准 |
| resumes_jump_link | 用于流程推进，不能用于只读详情；需明确人选、当前/目标环节，只有状态变化证据才称已流转 |
| urge_biz | 明确事项、对象集合和范围，调用前只读排除已完成对象；新增对象或内容超出原授权时补充确认；没有待催对象则不调用 |

已知面评催办使用 type=interview_eval 与 resumeCodeStr，按当前 Schema 核对。分析与草稿不自动触发动作；用户已授权的具体动作继续执行。能力缺失时给真实页面入口或草稿，不用浏览器写入等其他通道绕过。
