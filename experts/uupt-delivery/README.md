# UUPT Delivery

uu跑腿同城配送专家

## 类型

Agent 型（单个 AI 专家）

## 功能

UU跑腿同城配送服务。支持跑腿配送和帮忙服务两种订单类型，包括订单询价、发单下单、查询订单、取消订单、跑男实时追踪。

## 使用示例

- 帮我送个钥匙，从楷林国际到西吴河新居，联系电话15136279330
- 帮我在楷林国际4楼布置会议场地，我的电话是15136279330
- 帮我送个文件，从楷林国际到高新万达广场，联系电话15136279330

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\Administrator\.workbuddy\plugins\marketplaces\my-experts\plugins/uupt-delivery/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r uupt-delivery.zip uupt-delivery/
```
