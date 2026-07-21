# 领券接口 tencentClaimCoupon

- **adapter**：`ACOTADigitalProducts`
- **procedure**：`tencentClaimCoupon`
- **调用方**：外部服务商
- **原始内网地址（仅文档留痕）**：`http://10.211.144.113:9080/airchina/activity/tencentClaimCoupon.do`

## 请求参数（放在 req 字段里）

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| areaCode | String | 是 | 手机号国家码 | `86` |
| mobileNo | String | 是 | 接收短信手机号 | `188xxxxx63` |
| veriCode | String | 是 | 验证码（由 sendSMSVeriCodeActivity 发出） | `123456` |

请求示例：

```json
{
  "mobileNo": "188xxxxx63",
  "areaCode": "86",
  "veriCode": "123456"
}
```

## 响应参数（resp 解密后）

| 参数 | 类型 | 父节点 | 说明 |
|------|------|--------|------|
| code | string | resp | `"00000000"` 成功 |
| msg | string | resp | 状态文言 |
| couponList | array | resp | 优惠券列表 |
| couponCardCode | string | couponList[] | 优惠券 code |
| couponAmount | string | couponList[] | 优惠券金额 |
| couponName | string | couponList[] | 优惠券名称 |
| couponTypeCode | string | couponList[] | 优惠券类型 code |

响应示例：

```json
{
  "resp": {
    "msg": "优惠券已发放至您的账户，请您前往个人中心-优惠券中查看。",
    "code": "00000000",
    "couponList": [
      {
        "couponName": "成人+儿童测试券",
        "couponAmount": "10",
        "couponTypeCode": "ECT999",
        "couponCardCode": "3c426d99eebb477ba33d5fff793b526a"
      },
      {
        "couponName": "成人+儿童测试券",
        "couponAmount": "10",
        "couponTypeCode": "ECT999",
        "couponCardCode": "26308d72c2ab436fae6b63880684eb98"
      }
    ]
  }
}
```
