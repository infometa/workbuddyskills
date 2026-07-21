# 真实场景示例

## 场景 1：记录一个 Bug（文本 + 单选 + 图片）

用户说："帮我记一下这个 bug，登录页在 Safari 下白屏，模块是前端，严重程度严重。"

```json
{
  "add_records": [
    {
      "values": {
        "fABCD1": "登录页在 Safari 浏览器下加载后白屏，其他浏览器正常。复现步骤：Safari 14+ 访问 /login → 页面空白，控制台报 CSS 解析错误。",
        "fABCD2": [{"text": "前端"}],
        "fABCD3": [{"text": "严重"}],
        "fABCD4": [{"user_id": "wangwu"}],
        "fABCD5": [{"title": "safari-bug-screenshot.png", "image_base64": "iVBORw0KGgoAAAANSUhEUg...（纯base64）"}]
      }
    }
  ]
}
```

## 场景 2：记录一条任务（文本 + 日期 + 成员 + 单选 + 空图片）

用户说："加一条任务，完成支付模块单元测试，3月20日前，负责人 lisi，状态未开始，暂无附件。"

```json
{
  "add_records": [
    {
      "values": {
        "fTITLE": "完成支付模块单元测试，覆盖率达到 80%",
        "fDUEDATE": "1742400000000",
        "fOWNER": [{"user_id": "lisi"}],
        "fSTATUS": [{"text": "未开始"}],
        "fATTACH": []
      }
    }
  ]
}
```

> **关于负责人（成员字段）**：
> - 有 userid 时用 `[{"user_id": "账号名"}]`，userid 通常就是企业微信登录账号
> - 没有 userid 只知道姓名时用 `["张三"]`，但匹配不上时不会写入
> - 暂不指定负责人时传 `[]` 空数组
>
> **关于图片/附件字段**：
> - 暂无图片时传 `[]` 空数组即可，不会报错
> - 有图片时传 `[{"title": "filename.png", "image_base64": "纯base64字符串"}]`，注意不带 `data:image/...;base64,` 前缀

## 场景 3：批量添加多条客户记录

用户说："帮我把这三条线索录进去：张伟/科技公司/跟进中，陈静/贸易公司/初步接触，刘洋/制造业/已成交。"

```json
{
  "add_records": [
    {
      "values": {
        "fCUST_NAME": "张伟",
        "fCOMPANY": "北京某科技有限公司",
        "fSTAGE": [{"text": "跟进中"}],
        "fSOURCE": [{"text": "展会"}]
      }
    },
    {
      "values": {
        "fCUST_NAME": "陈静",
        "fCOMPANY": "上海某贸易有限公司",
        "fSTAGE": [{"text": "初步接触"}],
        "fSOURCE": [{"text": "冷呼"}]
      }
    },
    {
      "values": {
        "fCUST_NAME": "刘洋",
        "fCOMPANY": "广州某制造有限公司",
        "fSTAGE": [{"text": "已成交"}],
        "fSOURCE": [{"text": "老客户转介绍"}]
      }
    }
  ]
}
```

## 场景 4：更新一条已有记录

用户说："把 record_id 是 REC_20250301 的那条任务状态改成已完成，进度 100%。"

```json
{
  "update_records": [
    {
      "record_id": "REC_20250301",
      "values": {
        "fSTATUS": [{"text": "已完成"}],
        "fPROGRESS": 100
      }
    }
  ]
}
```

## 场景 5：批量更新多条记录

用户说："把这几条审批记录都标为已通过：REC_001、REC_002、REC_003。"

```json
{
  "update_records": [
    {"record_id": "REC_001", "values": {"fSTATUS": [{"text": "已通过"}], "fAPPROVER": [{"user_id": "manager_a"}]}},
    {"record_id": "REC_002", "values": {"fSTATUS": [{"text": "已通过"}], "fAPPROVER": [{"user_id": "manager_a"}]}},
    {"record_id": "REC_003", "values": {"fSTATUS": [{"text": "已通过"}], "fAPPROVER": [{"user_id": "manager_a"}]}}
  ]
}
```

## 场景 6：记录一条销售订单（多字段混合类型）

用户说："新增一条订单，客户是北京某科技，产品是企业版，金额 58000，签约日期今天，负责人赵六，合同链接发给你了。"

```json
{
  "add_records": [
    {
      "values": {
        "fCUSTOMER": "北京某科技有限公司",
        "fPRODUCT": [{"text": "企业版"}],
        "fAMOUNT": 58000,
        "fSIGN_DATE": "1741622400000",
        "fSALES": [{"user_id": "zhaoliu"}],
        "fCONTRACT": [{"text": "合同文件", "link": "https://doc.example.com/contract/2025-001"}]
      }
    }
  ]
}
```

## 场景 7：记录一次会议纪要

用户说："帮我记一下今天下午的需求评审会，参会人产品+开发+测试，决议是优先做支付模块。"

```json
{
  "add_records": [
    {
      "values": {
        "fMEETING_TITLE": "支付模块需求评审会",
        "fDATE": "1741622400000",
        "fPARTICIPANTS": "产品、开发、测试",
        "fSUMMARY": "确定优先开发支付模块，目标 3 月底完成联调，4 月初上线。遗留问题：退款流程待产品补充文档。",
        "fDOC_LINK": [{"text": "评审文档", "link": "https://doc.example.com/meeting/20250310"}]
      }
    }
  ]
}
```

## 场景 8：同一请求中同时添加和更新

用户说："新增一条'用户反馈收集'的任务，同时把'旧官网下线'那条（REC_OLD_001）标为已完成。"

```json
{
  "add_records": [
    {
      "values": {
        "fTITLE": "用户反馈收集与分析",
        "fSTATUS": [{"text": "未开始"}],
        "fPRIORITY": [{"text": "高"}]
      }
    }
  ],
  "update_records": [
    {
      "record_id": "REC_OLD_001",
      "values": {
        "fSTATUS": [{"text": "已完成"}],
        "fPROGRESS": 100
      }
    }
  ]
}
```
