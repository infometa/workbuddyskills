# CAT Network Quality Analyst · 网络质量分析专家

基于腾讯云 CAT（Cloud Automated Testing，云拨测）平台的网络质量分析专家，精通错误分析、性能分析、整体分析、抓包分析、多任务对比分析，自动生成专业分析报告。

## 典型对话

- 帮分析一下云拨测任务 task-xxxxxxxx 最近 24 小时的错误情况
- 生成这个拨测任务的整体分析报告
- 对指定错误记录做抓包深度分析
- 以任务 task-aaaabbbb 作为基准，task-ccccdddd、task-eeeeffff 为对比对象，进行多任务对比分析

## 依赖说明

本专家在运行时依赖一个**外部 SkillHub 技能包**（不随本仓库分发）：

- 技能包名：`@tencent-adm/cat-network-quality-analysis-v1-0-1`
- 安装方式：专家会在首次需要时自动检测并安装，无需用户介入：`npx skillhub install @tencent-adm/cat-network-quality-analysis-v1-0-1`

## 凭证配置

分析执行需要读取腾讯云 API 密钥，**出于安全考虑禁止通过对话发送密钥**，请在终端自行配置以下任一组环境变量：

- `CAT_SECRET_ID` / `CAT_SECRET_KEY`
- `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY`

密钥申请入口：[腾讯云 API 密钥管理](https://console.cloud.tencent.com/cam/capi)

配置详细指引请参见 agent prompt `agents/cat-network-quality-analyst.md` 中的「技能依赖 · Step 5 — 检查腾讯云凭证」部分。

## 报告命名规范

- 路径格式：`{task_id}/{task_id}_{report_type}_{timestamp}.pdf`
- `report_type` 取值：`error_report` / `overall_report` / `pcap_report` / `performance_report` / `multi_task_report`
- `timestamp` 格式：`YYYYMMDD_HHmmss`
