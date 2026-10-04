# 资料来源与设计参考

- 资料类型：来源说明与设计记录
- 整理日期：2026-07-17
- 适用范围：说明本 Skill 的规则来自哪里、采用了什么、拒绝了什么

## 资料分级

| 类型 | 定义 | 可否直接作为技术事实 |
|---|---|---|
| 官方原始资料 | 厂商或学校发布的具体支持文章、手册、版本说明 | 可以，但需匹配型号、版本和日期 |
| 官方资料摘要 | 对官方内容的压缩整理 | 可以作为入口，关键操作仍回查原文 |
| 专家经验规则 | 分流顺序、追问方式、授权与停止条件 | 不可以冒充厂商结论 |
| 社区设计参考 | 其他 Skill 的工作流、报告格式和安全设计 | 只借鉴结构，事实与命令必须另行验证 |

## 官方来源

- Microsoft Windows 支持：https://support.microsoft.com/zh-cn/windows
- Windows 版本运行状况：https://learn.microsoft.com/zh-cn/windows/release-health/
- Microsoft 365 支持：https://support.microsoft.com/zh-cn/microsoft-365
- Apple Mac 支持：https://support.apple.com/zh-cn/mac
- macOS 使用手册：https://support.apple.com/zh-cn/guide/mac-help/welcome/mac
- WPS 学堂：https://www.wps.cn/learning/
- Adobe 帮助中心：https://helpx.adobe.com/cn/support.html
- Microsoft Windows 安全中心与 PUA 防护：https://support.microsoft.com/zh-cn/topic/8f68fb65-ebb4-3cfb-4bd7-ef0f376f3dc3
- Windows 启动应用：https://support.microsoft.com/kb/115a420a-0bff-4a6f-90e0-1934c844e473
- Chrome 垃圾广告与恶意软件：https://support.google.com/chrome/answer/2765944?hl=zh-hans&co=GENIE.Platform=Desktop
- Edge 弹窗与浏览器默认值：https://support.microsoft.com/zh-cn/microsoft-edge/ 和 https://support.microsoft.com/zh-cn/edge/microsoft-edge-notification-browser-defaults
- Apple Safari 弹窗与垃圾软件：https://support.apple.com/zh-cn/ht203987
- Mozilla 浏览器劫持：https://blog.mozilla.org/firefox/your-browser-is-hijacked-now-what
- 其他品牌、驱动和浏览器入口见 `trusted-sources.md`

## 社区设计参考

### troubleshooting-it-issues

- 来源：https://github.com/tejasashinde/troubleshooting-it-issues
- 许可证：Apache-2.0
- 采用：最小充分诊断、问题范围识别、置信度、最低风险步骤、迭代排障、交接摘要。
- 未采用：把社区 Skill 本身当作技术事实来源；它不含型号、版本和官方知识库。

### PC Health Check

- 来源：https://clawhub.ai/coolfzb/pc-health-check
- 页面标注许可证：MIT
- 采用：只读数据采集、快速与完整模式、JSON 输出、报告与解释分离。
- 未直接复制：原脚本和固定风险阈值。本包的脚本独立实现，默认不采集事件日志，不根据单一百分比或端口直接下故障结论。

### IT 远程诊断助手

- 来源：https://github.com/CaoJun1015/diaohuo-assistant/tree/main/skills/it-remote-diagnose
- 仓库许可证：MIT
- 采用：一次聚焦一个关键问题、按结果选择分支、排查结束生成交接摘要。
- 明确拒绝：错误码到单一根因的一对一映射；“更新所有驱动”、关闭系统服务、使用第三方优化工具等通用方案。

### Guru IT Troubleshooting 模板

- 来源：https://app.getguru.com/card/ip9EqkRT/Knowledge-Agent-Skill-Template-IT-Troubleshooting-Issues
- 类型：提示词模板，不是可直接安装的 Agent Skill 包。
- 采用：受管设备意识、知识不足时升级、管理员权限和组织策略不由用户侧绕过。
- 调整：不采用“所有问题只能依赖知识库”的绝对限制，保留模型处理常见低风险问题的能力。

### OpenClaw Health Monitor

- 来源：https://clawhub.ai/jordan-thirkle/windows-health-monitor
- 采用：诊断包可能含敏感元数据、保存和分享前检查、默认关闭额外采集、危险命令必须显式警示。
- 未采用：OpenClaw 专用命令和服务修复流程。

### Computer 与 IT Ops Toolkit

- 来源：https://clawhub.ai/openlang-cn/skills/computer
- 来源：https://clawhub.ai/microsnow/it-ops-toolkit
- 仅参考：系统、CPU、内存、磁盘、网络和设备等诊断维度。
- 不采用：未提供实现的 `computer` 命令、过时 Windows 命令、压力测试、内核调优、强制结束进程、服务器运维和远程凭据流程。

## 使用限制

- 社区来源只证明某种设计已被实践，不证明其中每条技术结论正确。
- 任何驱动、固件、BIOS、恢复、错误码、兼容性和学校网络配置都必须回到官方原始资料。
- 来源无法访问、版本不匹配或官方结论冲突时，不继续推断，先补充信息或转专业支持。
