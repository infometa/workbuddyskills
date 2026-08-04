# 社媒管理 SOP

目标：管理 TikTok / Instagram 等社媒账号——发布内容、运营评论、收发私信、看数据、经营自己的 TikTok Shop 店铺。

## 前提：账号绑定

所有社媒操作都基于已绑定的账号。先 social_accounts(action="list") 查询已绑定列表：

- 无绑定账号，且要操作的是 Instagram / YouTube / Facebook 等非 TikTok 平台 → MCP 内暂不支持这些平台的绑定，引导用户去出海匠网页端（https://www.chuhaijiang.com）完成绑定，绑定好后回来用 list 确认可见再继续
- 无绑定账号，要操作的是 TikTok（达人账号）→ **优先用授权链接绑定**，扫码是用户明确要求时才用的兜底：
  1. 调 social_accounts(action="get_tiktok_auth_url") 拿 auth_url；把链接发给账号持有人（不必是当前对话的用户本人——云手机、代运营场景很常见），提醒在任意浏览器打开登录确认即可
  2. 链接绑定无需轮询：对方确认授权后账号自动加入团队，稍等一下用 list 检查是否出现
  3. 只有用户明确说想扫码时才走 login_qrcode：
     a. 先提醒用户打开手机 TikTok App 准备好（二维码几分钟内有效，提前准备减少换码）
     b. 调 social_accounts(action="login_qrcode")，**展示二维码的方式严格按返回结果里 hint 给出的决策阶梯执行**——阶梯细节、渲染命令、有效期、轮询与过期语义都以 hint 为准，它随服务端更新、每次调用都是最新版，不要凭记忆或本文档做；hint 会要求拿到二维码后立刻开始轮询 login_check，**不要等用户确认看到码再轮询**——没轮询过的码，用户真扫时会被判定已过期
     c. 核心纪律：**确认用户真的看到了二维码，再让他扫**；各级都走不通时不要自行变通（如复述二维码内容），引导用户去出海匠网页端（https://www.chuhaijiang.com → 账号管理 → 连接 TikTok）完成绑定
     d. 绑定成功后用 list 确认，再继续原操作
- 有多个账号 → 操作前和用户确认用哪个

## 发布流程（social_publish）

发布走的是存储 bucket 字段，不是 URL——upload_and_publish 只认 bucket_name + bucket_key（字段映射见 upload_file 工具说明）。

1. **备齐素材（把文件送进出海匠存储）**：
   - 本地文件：upload_file(file_name) 拿预签名上传地址 → 用 shell 执行 PUT 上传（命令模板见 upload_file 工具说明）→ 记下返回的 bucket 字段
   - AI 生成的素材：check_task 返回的结果 URL **不能直接发布**，先下载到本地，再走上面的 upload_file + PUT
2. **组装发布内容**：bucket 字段 + video_title + publications（账号、标题文案、话题标签、定时时间）；多文件/轮播用 media_items
3. **发布前必须确认**：把账号、素材、文案、发布时间完整展示给用户，拿到明确同意再调 social_publish(action="upload_and_publish")——发布是不可撤回的外发动作
4. **有限跟踪结果**：upload_and_publish 返回 session_token 后，先等 **10 秒**再调用 social_publish(action="session")；每次间隔至少 **10 秒**，本次发布流程最多查 **5 次**。一旦进入任一终态（成功、失败或取消）立刻停止。第 5 次仍非终态，就告知用户“发布已提交，平台仍在处理；你可以等一段时间后让我再查”，不要继续轮询或重发 upload_and_publish。用户之后明确要求查询状态时再单独查询；发布成功后，把每个成功发布目标返回的 `platform_url` 视频链接反馈给用户。**进行中的发布在 records 里查不到，不要用 records 判断"发没发出去"**。失败或取消时如实反馈状态；后续要查这条帖子的其他数据，用 session/records 里的 publication_id 或 platform_video_id 走 detail

## 评论运营（social_comments）

- 评论是先同步后查询的：拉不到评论先 sync 再 list。sync 是异步的，刚 sync 完立刻 list 拿到空结果，先等几秒重试一次，别急着下"没有评论"的结论
- 拉取帖子评论，按情感/主题归类，给用户运营建议
- 回复评论也是外发动作：批量回复前把回复内容清单给用户确认
- 处理不当评论分两种：自己账号发的用删除（delete），**他人发的评论删不掉，用隐藏（hide）**让其对外不可见；隐藏可随时恢复，删除不可逆——两者都逐条和用户确认

## 私信运营（social_messages）

层级是：渠道（一个绑定的社媒账号，如一个 WhatsApp 号）→ 会话（与一个联系人/群的对话）→ 消息。定位目标会话按 channels → conversations → list 逐层走。

- 典型场景：客户咨询分流（用 AI 洞察标签 kol/b2b/buyer/fan 筛会话）、批量查未读、代写回复
- **发私信是外发动作**：发送前把目标会话、消息内容给用户确认；回复多个会话时列清单一次确认
- 读消息时的 mark_as_read 会向对方发已读回执（如 WhatsApp 蓝勾）——只想看不想让对方知道已读时不要带这个参数
- 改会话备注（remark）在 WhatsApp 上会同步改写对方联系人的显示名——这是对外可见的变更，批量打标签前先让用户确认命名方式
- 私信媒体不走 upload_file，用 social_messages 的 upload 专用通道（工具说明里有字段映射）
- 发送失败提示发送窗口关闭（20510）时如实告知用户：平台限制超时未回复的会话不能主动发消息，不是故障
- **渠道列表为空 ≠ 用户没绑账号**：私信要求绑定授权包含私信权限。逐条排查引导——早期绑定的账号需重新授权绑定；TikTok 只有 Business 账号支持私信（个人账号可在 TikTok App 内免费切换，切换后重新扫码）；Instagram/Facebook 要在出海匠控制台绑定

## 店铺经营（social_seller）

前提是 TikTok Shop **卖家授权**——和达人账号绑定是两套授权，扫码绑定管不到它；没有卖家店铺账号时调 social_accounts(action="get_tiktok_shop_auth_url") 拿授权链接发给店铺持有人，对方打开确认后用 social_accounts(list) 确认可见——不必再引导去网页端手动操作。绑的是达人橱窗号不用传 type（默认跨境档）；绑的是店铺/渠道号，跟用户确认店铺所在区域再传 type，用户可能直接报的是产品页上的账号类型名，对应关系：**跨境店铺账号**（美国/巴西/墨西哥）→cross-border（不传也是这档）；**墨西哥本土店铺账号**→mx-local（功能上和跨境档一样）；**美国本土店铺账号**→domestic；**日本本土店铺账号**→local-jp；**欧洲本土店铺账号**（德国/西班牙/法国/英国/爱尔兰/意大利）→local-eu。

- 典型场景：每日店铺健康检查（daily_report 传昨天日期）、多店对比（shops_overview）、库存/滞销盘点（products + product_detail 看 SKU 库存）
- daily_report 是"取报告"不是"算报告"：status=generating 时等 5-10 秒再取，**每次调用都计费**，拿到 ready 结果就复用，不要高频轮询
- **长时间 generating 是静默输入错误**，不是慢：先停下检查账号是不是卖家类型、日期是不是严格 YYYY-MM-DD，修正输入而不是继续重试烧钱
- 给用户呈现日报时注意口径：战报是当日实时订单口径，经营分析是 T-2 口径，两块数字对不上是正常的，主动说明
- 别拿 social_seller 做选品调研——那是 search 的活；这里只管用户自己的店

## 数据分析（social_analytics）

- 账号维度：粉丝增长、主页访问、整体互动趋势
- 内容维度：单帖播放/点赞/评论/分享，找出表现最好的内容模式
- 产出建议用表格 + 一段结论（什么内容类型在涨、建议多发什么）

## 辅助工具（social_tools）

发布相关的辅助能力（如话题/音乐查询等），按工具返回的说明使用。

## 注意

- 发布、回复、删除、解绑都是有外部影响的动作：**没有用户明确确认不执行**
- upload_file 返回的访问 URL（cdn_url / signed_url）是给 ai_generate 当参考素材或给用户预览用的；发布用的是 bucket 字段，两者不要混
- 用户要"定时发布"时确认平台是否支持该参数，不支持就明说，不要假装成功
