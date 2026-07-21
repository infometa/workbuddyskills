# 创意组件枚举值参考

> 来源：`mkt-api-idl/v3/common/enum.xml`
> 适用：`dynamic_creatives/add` 及相关接口的 `creative_components` 字段

---

## 顶层字段枚举

### delivery_mode（投放模式）
| 枚举值 | 含义 |
|--------|------|
| `DELIVERY_MODE_COMPONENT` | 组件化创意 |
| `DELIVERY_MODE_CUSTOMIZE` | 自定义创意 |

### dynamic_creative_type（创意形式匹配方式）
| 枚举值 | 含义 |
|--------|------|
| `DYNAMIC_CREATIVE_TYPE_PROGRAM` | 程序化创意 |
| `DYNAMIC_CREATIVE_TYPE_COMMON` | 指定创意形式 |

### live_promoted_type（视频号推广形式）
| 枚举值 | 含义 |
|--------|------|
| `LIVE_PROMOTED_TYPE_SHORT_VIDEO` | 短视频推广 |
| `LIVE_PROMOTED_TYPE_NATIVE_VIDEO` | 直播实时画面 |

### configured_status（客户设置的广告状态）
| 枚举值 | 含义 |
|--------|------|
| `AD_STATUS_NORMAL` | 有效 |
| `AD_STATUS_SUSPEND` | 暂停 |

> **注意**：ADX 程序化广告不可填写此字段

---

## action_button / main_jump_info / brand — jump_info.page_type

| 枚举值 | 含义 | page_spec 字段 |
|--------|------|---------------|
| `PAGE_TYPE_OFFICIAL` | 官方落地页 | `official_spec.page_id` |
| `PAGE_TYPE_H5` | 自定义落地页（H5链接） | `h5_spec.page_url` |
| `PAGE_TYPE_H5_PROFILE` | H5 Profile页 | `h5_profile_spec.page_id` |
| `PAGE_TYPE_WECHAT_MINI_PROGRAM` | 微信小程序 | `wechat_mini_program_spec.{mini_program_id, mini_program_path}` |
| `PAGE_TYPE_WECHAT_MINI_GAME` | 微信小游戏 | `wechat_mini_game_spec.mini_game_id`；若用户提供了监测链接（如 `?state=xxx`），填入 `wechat_mini_game_spec.mini_game_tracking_parameter` |
| `PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE` | 微信视频号直播间 | `wechat_channels_watch_live_spec.wechat_channels_account_id`（`export/xxx` 格式）。**填写规则**：当投放目标/载体为视频号直播（`MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE` / `MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE`）且已知视频号账号时，脚本会自动补全该字段；Agent 传 `page_spec: {}` 即可，**不要手动填写 `wechat_channels_account_id`** |
| `PAGE_TYPE_WECHAT_CHANNELS_PROFILE` | 视频号主页 | `wechat_channels_profile_spec.username`（`v2_xxx@finder` 格式，必填）。`wechat_channels_account_id`（`export/xxx` 格式）由后端自动补全，**不要手动填写** |
| `PAGE_TYPE_WECHAT_CHANNELS_SHOP_PRODUCT` | 微信小店商品页 | `wechat_channels_shop_product_spec.{product_id, shop_id}` |
| `PAGE_TYPE_WECHAT_SHOP` | 微信小店店铺页 | `wechat_shop_spec.shop_id` |
| `PAGE_TYPE_WECHAT_CONSULT` | 微信客服 | `wechat_consult_spec.page_url` |
| `PAGE_TYPE_WECOM_CONSULT` | 企业微信名片页 | — |
| `PAGE_TYPE_WECHAT_CHANNELS_FOLLOW_ACCOUNT` | 微信视频号关注账号 | — |
| `PAGE_TYPE_WECHAT_CHANNELS_RESERVE_LIVE` | 微信视频号直播预约 | — |
| `PAGE_TYPE_WECHAT_OFFICIAL_ACCOUNT_DETAIL` | 微信公众号详情页 | `wechat_official_account_detail_spec.app_id` |
| `PAGE_TYPE_WECHAT_APPOINTMENT_CARD` | 微信一键预约 | — |
| `PAGE_TYPE_XJ_WEB_H5` | **蹊径 H5 网页落地页**（用户提到"蹊径"时用此类型） | `xj_web_h5_spec.page_id` |
| `PAGE_TYPE_XJ_ANDROID_APP_H5` | 蹊径 Android App 下载页 | `xj_android_app_h5_spec.page_id` |
| `PAGE_TYPE_XJ_IOS_APP_H5` | 蹊径 iOS App 下载页 | `xj_ios_app_h5_spec.page_id` |
| `PAGE_TYPE_XJ_QUICK` | 蹊径极速版落地页 | `xj_quick_spec.page_id` |
| `PAGE_TYPE_ANDROID_APP` | Android 应用 | `android_app_spec.android_app_id` |
| `PAGE_TYPE_IOS_APP` | iOS 应用 | `ios_app_spec.ios_app_id` |
| `PAGE_TYPE_FENGYE_ECOMMERCE` | 枫叶单品页 | `fengye_ecommerce_spec.page_id` |
| `PAGE_TYPE_QQ_APP_MINI_PROGRAM` | QQ 小程序 | `qq_app_mini_program_spec.{mini_program_id, mini_program_path}` |
| `PAGE_TYPE_QQ_MINI_GAME` | QQ 小游戏 | `qq_mini_game_spec.mini_game_id` |
| `PAGE_TYPE_APP_DEEP_LINK` | 应用 Deep Link | `app_deep_link_spec.{android_deep_link_url, ios_deep_link_url, universal_link_url, ...}` |
| `PAGE_TYPE_APP_MARKET` | 应用市场 | `app_market_spec.android_app_id` |
| `PAGE_TYPE_ANDROID_QUICK_APP` | 安卓快应用 | `android_quick_app_spec.quick_app_url` |
| `PAGE_TYPE_WECHAT_CANVAS` | 微信原生推广页 | `wechat_canvas_spec.canvas_id` |
| `PAGE_TYPE_WECHAT_SIMPLE_CANVAS` | 微信简版原生页 | `wechat_simple_canvas_spec.canvas_id` |
| `PAGE_TYPE_WECHAT_CANVAS_MINI_PROGRAM` | 微信原生页-小程序 | `wechat_canvas_mini_program_spec.canvas_id` |
| `PAGE_TYPE_WECHAT_FOCUS_DAILOG` | 微信一键关注页 | — |
| `PAGE_TYPE_WECHAT_CHANNELS_FEED` | 微信视频号动态 | `wechat_channels_feed_spec.feed_id` |
| `PAGE_TYPE_ANDROID_DIRECT_DOWNLOAD` | 安卓一键下载 | `android_direct_download_spec.{app_id, download_url}` |
| `PAGE_TYPE_SEARCH_BRAND_AREA` | 搜索品牌专区 | — |
| `PAGE_TYPE_APP_HARMONY` | 鸿蒙 AppStore 下载页 | `app_harmony_spec.app_id` |

---

## label 组件

### list[].type（标签类型）
| 枚举值 | 含义 |
|--------|------|
| `LABEL_TYPE_CUSTOMIZETEXT` | 自定义文字标签 |
| `LABEL_TYPE_COMMON` | 普通标签 |
| `LABEL_TYPE_PROMOTIONAL` | 节点营销标签 |
| `LABEL_TYPE_ICON` | 角标 |
| `LABEL_TYPE_UNKNOWN` | 未知（禁止使用） |

---

## show_data 组件

### conversion_data_type（数据外显转换数据类型）
| 枚举值 | 含义 |
|--------|------|
| `CONVERSION_DATA_ADMETRIC` | 转换目标量 |
| `CONVERSION_DATA_DEFAULT` | 不使用 |
| `CONVERSION_DATA_FRIEND_PLAY` | 好友在玩量 |
| `CONVERSION_DATA_APP_DOWNLOAD` | 应用下载量 |
| `CONVERSION_DATA_ONSHOP` | 商品下单量 |
| `CONVERSION_DATA_FRIEND_FOLLOW` | 好友关注量 |
| `CONVERSION_DATA_PRODUCT_DATA` | 商品数据 |

### conversion_target_type（数据外显转化目标量类型）

| 枚举值 | 含义 |
|--------|------|
| `CONVERSION_TARGET_DEFAULT` | 不使用 |
| `CONVERSION_TARGET_GET` | 领取 |
| `CONVERSION_TARGET_RESERVE` | 预约 |
| `CONVERSION_TARGET_BOOK` | 预定 |
| `CONVERSION_TARGET_BUY` | 购买 |
| `CONVERSION_TARGET_APPLY` | 申请 |
| `CONVERSION_TARGET_CONSULT` | 咨询 |
| `CONVERSION_TARGET_DOWNLOAD` | 下载 |
| `CONVERSION_TARGET_PLAYING` | 在玩 |
| `CONVERSION_TARGET_CLICK` | 查看 |
| `CONVERSION_TARGET_SEE` | 了解 |
| `CONVERSION_TARGET_INVOLVE` | 参与 |
| `CONVERSION_TARGET_OPEN` | 打开 |
| `CONVERSION_TARGET_PURCHASE` | 抢购 |
| `CONVERSION_TARGET_BROWSE` | 浏览 |
| `CONVERSION_TARGET_TRY` | 试玩 |
| `CONVERSION_TARGET_DRIVE` | 试驾 |
| `CONVERSION_TARGET_ENTER` | 进入 |
| `CONVERSION_TARGET_READ` | 阅读 |
| `CONVERSION_TARGET_FOLLOW` | 关注 |
| `CONVERSION_TARGET_USE` | 使用 |
| `CONVERSION_TARGET_EXPERIENCE` | 体验 |
| `CONVERSION_TARGET_SETUP` | 开通 |
| `CONVERSION_TARGET_SECKILL` | 秒杀 |
| `CONVERSION_TARGET_ADD_WECOM` | 加企微 |
| `CONVERSION_TARGET_LIKE` | 想看 |
| `CONVERSION_TARGET_DONATION` | 捐款 |
| `CONVERSION_TARGET_GOOD_DEED` | 做好事 |
| `CONVERSION_TARGET_MEITUAN_RANK` | 美团榜单 |

---

## floating_zone 组件

### floating_zone_type（浮层卡片类型）
| 枚举值 | 含义 |
|--------|------|
| `FLOATING_ZONE_TYPE_IMAGE_TEXT` | 图文复合类型 |
| `FLOATING_ZONE_TYPE_SINGLE_IMAGE` | 单图类型 |
| `FLOATING_ZONE_TYPE_MULTI_BUTTON` | 多按钮类型 |
| `FLOATING_ZONE_TYPE_SLIDER_CARD` | 轮播卡片类型 |
| `FLOATING_ZONE_TYPE_UNKNOWN` | 历史数据（禁止使用） |

### floating_zone_info_type（浮层信息类型）
| 枚举值 | 含义 |
|--------|------|
| `FLOATING_ZONE_INFO_DEFAULT` | 默认 |
| `FLOATING_ZONE_INFO_TYPE_NORMAL` | 常规 |
| `FLOATING_ZONE_INFO_TYPE_PRODUCT` | 直播商品 |

---

## text_link 组件

### link_name_type（文字链名称类型）
| 枚举值 | 含义 |
|--------|------|
| `NOT_USED` | 不使用（仅公众号流量可用） |
| `VIEW_DETAILS` | 查看详情 |
| `GET_COUPONS` | 领取优惠 |
| `MAKE_AN_APPOINTMENT` | 预约活动 |
| `BUY_NOW` | 立即购买 |
| `GO_SHOPPING` | 去逛逛 |
| `ENTER_MINI_PROGRAM` | 进入小程序 |
| `ENTER_MINI_GAME` | 进入小游戏 |
| `APPLY_NOW` | 立即申请 |
| `BOOK_NOW` | 立即预定 |
| `RESERVATION_BUY` | 预约购买 |
| `CONSULT_NOW` | 立即咨询 |
| `BOOK_DRIVE` | 预约试驾 |
| `ENTER_OFFICIAL_ACCOUNTS` | 了解公众号 |
| `PLAY_NOW` | 立即玩 |
| `OPEN_MINI_GAME` | 打开游戏 |
| `DOWNLOAD_APP` | 下载应用 |
| `DOWNLOAD_GAME` | 下载游戏 |
| `CHECK_IT_OUT` | 去看看 |
| `GET_SAMPLES` | 领取小样 |
| `TRY_NOW` | 立即体验 |
| `GET_IT_NOW` | 立即领取 |
| `BUY_ASAP` | 立即抢购 |
| `DOWNLOAD_NOW` | 立即下载 |
| `VIEW_APPS` | 查看应用 |
| `MORE_INFO` | 了解更多 |
| `GET_VOUCHERS` | 领券 |
| `FOLLOW_OFFICIAL_ACCOUNT` | 关注公众号 |
| `READ_NOVELS` | 阅读小说 |
| `WATCH_LIVE` | 观看直播 |
| `RESERVE_NOW` | 立即预约 |
| `OPEN_APP` | 打开应用 |
| `ALREADY_INSTALL` | 已安装 |
| `RESERVE_LIVE` | 预约直播 |
| `SETUP_NOW` | 立即开通 |
| `SECKILL_NOW` | 立即秒杀 |
| `TRY_PLAY_NOW` | 立即试玩 |
| `INSTALL_NOW` | 立即安装 |
| `FOLLOW_CHANNELS` | 关注视频号 |
| `MORE_ABOUT_CHANNELS` | 了解视频号 |
| `GET_FOR_FREE` | 免费领取 |
| `WATCH_VIDEO` | 观看视频 |
| `CONTACT_CUSTOMER_SERVICE` | 联系客服 |
| `CONTACT_BUSINESS` | 联系商家 |
| `PICK_GIFT` | 选购好礼 |
| `SELECT_GIFT` | 甄选好礼 |
| `GIVING_GIFT` | 去送礼 |
| `GIVE_FRIEND` | 送朋友 |
| `LINK_NAME_TEXT_TEMPLATE` | 文字链模版（自定义文案） |

---

## end_page 组件

### end_page_type（结束页类型）
| 枚举值 | 含义 |
|--------|------|
| `END_PAGE_AVATAR_NICKNAME_HIGHLIGHT` | 突出头像及昵称 |
| `END_PAGE_DESCRIPTION_HIGHLIGHT` | 突出文案 |

---

## playable_page 组件

### status（试玩页状态）
| 枚举值 | 含义 |
|--------|------|
| `PLAYABLE_PAGE_STATUS_ONLINE` | 已上线 |
| `PLAYABLE_PAGE_STATUS_OFFLINE` | 已下线 |
| `PLAYABLE_PAGE_STATUS_AUDIT` | 审核中 |
| `PLAYABLE_PAGE_STATUS_REJECTED` | 审核未通过 |

---

## 素材管理枚举

> 适用：`images/add`、`images/get`、`videos/add`、`videos/get` 等素材接口

### upload_type（图片上传方式）
| 枚举值 | 含义 |
|--------|------|
| `UPLOAD_TYPE_FILE` | 文件流上传 |
| `UPLOAD_TYPE_BYTES` | Base64 编码上传 |

### image_usage（图片用途）
| 枚举值 | 含义 |
|--------|------|
| `IMAGE_USAGE_DEFAULT` | 默认用途 |
| `IMAGE_USAGE_MARKETING_PENDANT` | 营销挂件 |
| `IMAGE_USAGE_SHOP_IMG` | 店铺图片 |

### image type（图片格式）
| 枚举值 | 含义 |
|--------|------|
| `TYPE_JPG` | JPG 格式 |
| `TYPE_PNG` | PNG 格式 |
| `TYPE_GIF` | GIF 格式 |

### video type（视频格式）
| 枚举值 | 含义 |
|--------|------|
| `TYPE_MP4` | MP4 格式 |
| `TYPE_MOV` | MOV 格式 |
| `TYPE_AVI` | AVI 格式 |

### system_status（视频转码状态）
| 枚举值 | 含义 |
|--------|------|
| `MEDIA_STATUS_VALID` | 转码完成，可用 |
| `MEDIA_STATUS_PROCESSING` | 转码中 |
| `MEDIA_STATUS_INVALID` | 转码失败 |

### source_type — 图片来源
| 枚举值 | 含义 |
|--------|------|
| `SOURCE_TYPE_LOCAL` | 本地上传 |
| `SOURCE_TYPE_API` | API 上传 |
| `SOURCE_TYPE_MUSE` | 妙思生成 |
| `SOURCE_TYPE_QUICK_DRAW` | 快速绘图 |
| `SOURCE_TYPE_VIDEO_SNAPSHOTS` | 视频截图 |
| `SOURCE_TYPE_TCC` | 创意中心 |

### source_type — 视频来源
| 枚举值 | 含义 |
|--------|------|
| `SOURCE_TYPE_LOCAL` | 本地上传 |
| `SOURCE_TYPE_API` | API 上传 |
| `SOURCE_TYPE_TCC` | 创意中心 |
| `SOURCE_TYPE_VIDEO_MAKER_XSJ` | 小视界制作 |
| `SOURCE_TYPE_DERIVE` | 派生视频 |
| `SOURCE_TYPE_DERIVATION` | 派生视频（旧值） |
| `SOURCE_TYPE_HUXUAN` | 互选视频 |
| `SOURCE_TYPE_HUXUAN_DERIVE` | 互选派生视频 |

### status（素材状态，图片/视频通用）
| 枚举值 | 含义 |
|--------|------|
| `ADSTATUS_NORMAL` | 正常 |
| `ADSTATUS_DELETED` | 已删除 |

### similarity_status（相似度检测状态，图片/视频通用）
| 枚举值 | 含义 |
|--------|------|
| `SIMILARITY_STATUS_DEFAULT` | 默认状态 |
| `SIMILARITY_STATUS_SIMILAR` | 存在相似素材 |
| `SIMILARITY_STATUS_UNIQUE` | 无相似素材 |

### first_publication_status（首发状态，图片/视频通用）
| 枚举值 | 含义 |
|--------|------|
| `FIRST_PUBLICATION_STATUS_DEFAULT` | 默认状态 |
| `FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION` | 首次发布 |

### quality_status（质量状态，图片/视频通用）
| 枚举值 | 含义 |
|--------|------|
| `QUALITY_STATUS_DEFAULT` | 默认质量 |
| `QUALITY_STATUS_LOW_QUALITY` | 低质量 |

### aigc_flag（AIGC 标识，图片/视频通用）
| 枚举值 | 含义 |
|--------|------|
| `AIGC_FLAG_UNKNOWN` | 未知 |
| `AIGC_FLAG_NOT_AI` | 非 AI 生成 |
| `AIGC_FLAG_USE_MUSE_AI` | 妙思 AI 生成 |
| `AIGC_FLAG_USE_OTHERS_AI` | 其他 AI 生成 |

### filtering 操作符（素材查询通用）
| 操作符 | 含义 |
|--------|------|
| `EQUALS` | 等于 |
| `CONTAINS` | 包含 |
| `IN` | 包含于（支持多值） |
| `LESS` | 小于 |
| `LESS_EQUALS` | 小于等于 |
| `GREATER` | 大于 |
| `GREATER_EQUALS` | 大于等于 |

---

## 审核相关枚举

> 适用：`dc_review_result/get` 接口

### element_type（元素类型）
| 枚举值 | 含义 |
|--------|------|
| `ELEMENT_TYPE_TEXT` | 文本 |
| `ELEMENT_TYPE_IMAGE` | 图片 |
| `ELEMENT_TYPE_VIDEO` | 视频 |
| `ELEMENT_TYPE_URL` | 落地页URL |

### review_status（审核状态）
| 枚举值 | 含义 |
|--------|------|
| `AD_STATUS_NORMAL` | 审核通过 |
| `AD_STATUS_PENDING` | 审核中 |
| `AD_STATUS_DENIED` | 审核不通过 |
| `AD_STATUS_PARTIALLY_NORMAL` | 部分通过（组件级别） |
