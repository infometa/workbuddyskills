#!/bin/bash
# 国航 B2C 接口 curl 手工调用示例（仅供调试加密链路时参考）
# 真正跑接口请用 scripts/airchina.sh 或 scripts/airchina_client.py
# 凭证示例来自《国航B2C移动应用项目对外服务接口规范-腾讯WorkBuddyV1.0.0》

# ====== 1. 获取 accessToken（无需加密，走 query string）======
curl -X POST "https://m.airchina.com.cn:9066/airchina/gateway/ota/v2.0/auth/getAccessToken?appId=iU4qgwcjS6vWkDOTsVKX3zQe&secretKey=qOtUj1yAg3h9rYvEWsN8XluM&channel=TENCENT&subChannel=OTA" \
  -H "Content-Type: application/json" \
  -d '{}'

# 响应：
# {
#   "resp": "",
#   "securityCode": "0000",
#   "accessToken": "ad88cf07521a475fb034ab783abefe52"
# }


# ====== 2. 调用业务接口（需先用脚本算好 signString 和 AES 密文）======
# signString = MD5("lang=zh_CN&req={...}&timestamp=1597735475213")
# body = AES_ECB_PKCS5_Base64(上面那串明文, accessToken[8:24])
#
# curl -X POST "https://m.airchina.com.cn:9066/airchina/gateway/ota/v2.0/api/services/" \
#   -H "Content-Type: application/x-www-form-urlencoded" \
#   -H "channel: TENCENT" \
#   -H "subChannel: OTA" \
#   -H "appId: iU4qgwcjS6vWkDOTsVKX3zQe" \
#   -H "accessToken: ad88cf07521a475fb034ab783abefe52" \
#   -H "signString: <32位MD5>" \
#   -H "adapter: ACOTADigitalProducts" \
#   -H "procedure: sendSMSVeriCodeActivity" \
#   -H "serviceVersion: 10100" \
#   --data-raw "<AES加密后的Base64密文>"
