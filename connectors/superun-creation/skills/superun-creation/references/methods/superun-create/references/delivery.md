# superun 成果核对与交付

先确定用户要求的交付阶段：风格、演示、研发功能、目标版本部署、站点上线或运营查询/操作。CLI 的 COMPLETED 只结束本次操作；不把演示查看记录、停止命令返回或一次列表查询当成应用完成。

| 用户要求 | 完成所需依据 |
|---|---|
| 查状态或解释 | 正确 session/操作的 CLI 回读，明确 state 与产品阶段 |
| 风格建议/选择 | 本批真实 previewUrl、候选状态及用户决定；区分建议、已提交、选择已生效 |
| 查看演示 | chat demo 回读到对应 demo.snapshotId/messageId/url；viewed 是查看记录，不证明用户满意或功能有效 |
| 修改演示 | 具体要求已发送至原项目，并回读修改结果；不自动转入研发 |
| 开始研发 | development.started 及当前规划/业务交互；这仅证明已进入研发，不代表规划获批或功能完成 |
| 新建/修改实际功能 | 真实项目入口与明确要求的页面/功能对应，核对关键操作；本轮 COMPLETED 不证明未选择功能也已实现 |
| 真实提交/保存 | 在授权范围观察目标操作实际结果；页面成功提示本身不足以证明持久化 |
| 自动测试 / 代码审查 | 当前 autoTest/codeReview 报告、检查范围、问题与修复详情及验证证据；按 quality-checks.md 判断条件，COMPLETED 不证明通过 |
| 安全扫描 | 本次 securityReview 的 checks、stage 与报告结果；扫描完成、修复启动或消息结束都不证明通过，按 [扩展能力](extend.md) 展示摘要 |
| Agent 友好接入 | 所选方式的完整接入原文已展示，且目标 AI 应用完成一次真实只读查询；指令已准备或已复制不证明已接入 |
| 运营查询/操作 | 本轮 superun 回复中的查询结果或实际操作回执、影响范围与缺口；仅提供方案、SQL 或 COMPLETED 不证明数据库操作已完成，按 [运营方法](operations.md) 交付 |
| 发布目标版本 | 本次 encryptedId 对应记录 deployStatus=1，发布记录 updatedAt 已相对提交前更新，并核对真实入口 |
| 站点上线 | 已部署目标版本和实际 publicStatus/入口；部署成功与 public/private 是不同状态 |

## 发布结果必须看版本记录

`chat publish status` 只要没有发布进行中就可能返回 COMPLETED，即使版本未发布或已失败。检查 `publish.versions` 中目标 encryptedId 的 deployStatus（1 成功、2 进行中，其余不能称成功）、updatedAt、errorMessage/deploymentSteps，以及真实 publishUrl。versions 为空时说明没有可核对的版本，不用 demo.snapshotId 顶替。

`publish start --no-wait` 返回 ACCEPTED 和目标 encryptedId 后，按该 ID 查询。本地超时会带 waitTimedOut，旧成功记录不能证明本次操作成功。--indexing 仅控制搜索引擎索引；站点上下线使用 `chat publish visibility`，不混作访问权限或删除部署。

在已授权部署后的最终验收中，通过真实外部入口执行刚改变的关键路径。入口不可达、报错或结果不对就报告验收失败；构建、启动、其他页面成功不能抵消。未部署或缺少浏览器/访问能力时，明确仅完成源码/CLI 结果核对，不能宣称线上验收通过。

## 交付表述

使用 CLI 的真实 URL、文件与附件；没有入口时说明缺口，不猜域名路径。按当前任务保留 `要求项 | 成果/入口 | 已核对证据 | 状态/缺口`，不强制生成过程文件。

最终交付给用户：本次完成到哪个阶段、真实入口、关键核对结果、失败或未验证部分，以及继续原项目所需标识。等待用户决定时明确当前入口；不因有下一阶段可选就自动执行，也不把“待用户选择”说成整个任务已完成。

创作与发布按 [全部端入口](project-links.md) 分别读取 development.routing、publish.routing，单端直接给入口，多端完整交付所有端的有名链接并引导进入。不得只留下默认端；entryUrl 用于进入，shareUrl 用于分享，不自行拼接。研发基础地址仍使用 development.previewUrl，稳定地址随主线构建更新，不等待研发快照。预览只说明有可访问入口，不能证明功能验证或正式发布；缺失时说明缺口，不拼接地址。旧 development.snapshot 仅兼容已有结果。修改演示使用当前返回的 demo.url，不用旧链接替代。

发布操作顺序仅按 [阶段表的上线流程](creation-flow.md#用户明确要求上线时) 执行；本文件只负责结果核对。

用户可见交付由宿主完成：按 [展示协议](host-presentation.md) 实际显示问题、候选和本轮成果，允许展示的链接用 WebView/浏览器打开，缺能力时明确降级。stylePlanning 的过渡演示不展示；自动设置 demo.viewed 不证明用户看过。taskProgress.complete/activeCount 及过程事件都不能代替最终状态或实际关键路径验收。

本轮有可用预览时主动交付；每轮研发/修复后有 development.previewUrl 时，先交付 development.routing 中全部有效端入口和本轮效果再交付，有可用展示工具时实际调用，仅支持链接时提供完整链接。同一 URL 对应新轮次或新快照时仍需重新展示。当前宿主使用实际可用的展示工具；没有成功工具回执时如实报告降级，不写成已打开。
