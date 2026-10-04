---
name: fbs-work
description: 说明福帮手事项与人工帮助的接续方式；当前默认资源仅提供指引，不自动保存或提交资料。
metadata:
  ai.workbuddy.description_zh: 仅说明事项与帮助接续条件；工具未开放时不查询、保存或提交资料。
  ai.workbuddy.description_en: Explain case and assistance prerequisites; unavailable tools do not query, save or submit user materials.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 事项与帮助接续

本页事项CRUD/帮助工具仍为support_readiness=guidance_only，未在本轮OAuth Gateway暴露；管理系统本人网页已有的事项流程与此不同。画像已支持获准的本人既有CASE事实，但不因此开放member_case_*或member_request_*。先遵守[公共路由](../fbs-connector/SKILL.md)，缺工具仅给已核实的本人门户入口。

以下工具只有后续单独审定并在本轮真实开放时才适用：member_case_list/get、member_case_create、member_case_link；当前不尝试它们。已存在事项可按[画像协议](../fbs-profile/references/profile-purpose-and-provenance.md)复用同意范围内事实，不改变事项本身或关联服务。不得把聊天、打开文件或沉默当保存许可。

用户希望人工协助时，`member_request_entry` 只提供填写入口；`member_request_list/get` 只查本人已提交需求与公开回复。用户在网页选择资料范围及联系许可；不代提交、不自动联系工作人员。

服务目录目前只有网页/API。拟议 `member_service_catalog_list/get` 未通过能力门不能调用；提供已核实入口，不把目录当订单。成果引用不表示正文已上传或支持跨设备下载。

事项结果反馈只在本人会员事项页面由账号持有人主动提交；事项归档、服务调用成功、结算或工具回执都不能推断为已解决。连接器不提供或代调结果反馈写入工具，不自动选择结果、不从聊天文本生成反馈；不提交、不勾选用途同意或撤回均不作负面解释。若之后真实开放只读反馈字段，按服务返回的 `OWNER_REPORTED` 明示为本人自报，不提升成客观验证结果或服务信用。
