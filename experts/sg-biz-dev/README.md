# 新加坡商务拓展专家 (Singapore BD Expert)

专注新加坡商务拓展，覆盖客户/渠道/供应商/园区/展会/市场进入全链路资源对接，辅助中国企业出海新加坡决策。

## 类型

Agent 型（单个 AI 专家）

## 功能

- **客户与合作伙伴寻源**：通过 ACRA、行业协会等渠道定位潜在客户
- **渠道与供应链对接**：匹配新加坡及东南亚经销商、代理商、供应商
- **园区与政策分析**：解读 JTC、EDB 产业园区规划和招商优惠政策
- **展会与商务活动**：追踪 SECB 展会排期和行业峰会
- **市场进入路径**：公司注册、工作签证、银行开户等全流程指导
- **招商与投资机会**：分析 GeBIZ 招标、GIP 投资移民、政府资助计划

## 数据源

内置 Skill `sg-biz-data` 包含：
- 新加坡政府开放数据平台（data.gov.sg）API 参考
- ACRA 企业注册查询指南
- GeBIZ 政府招标平台使用说明
- EDB / Enterprise Singapore 资助计划清单
- JTC 产业园区完整目录
- 新加坡主要展馆、展会信息
- 行业协会、商会、银行、专业服务机构速查表

## 使用示例

- "帮我查找新加坡XX行业的潜在客户和合作伙伴"
- "中国企业进入新加坡市场需要关注哪些园区和招商政策？"
- "新加坡XX行业有哪些主要的展会和渠道商？"

## 输出风格

默认简洁模式：3~8 个核心信息点，列表形式，结论优先。
标准格式：【查询结果】→【数据来源】→【可选扩展指令】

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到以下路径：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/sg-biz-dev/
```

然后运行注册命令使其在 WorkBuddy 中可见：

```bash
python3 scripts/register_expert.py ~/.workbuddy/plugins/marketplaces/my-experts/plugins/sg-biz-dev/
```

## 打包分享

```bash
zip -r sg-biz-dev.zip sg-biz-dev/
```
