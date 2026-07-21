# 唯品会扫码登录 API 接口文档

> 本文档包含唯品会扫码登录相关的 API 接口说明。

## 接口列表

### 1. 初始化二维码登录信息 (/qrLogin/initQrLogin)

获取二维码登录的 TOKEN。

| 项目 | 说明 |
|------|------|
| **接口地址** | `https://passport.vip.com/qrLogin/initQrLogin` |
| **请求方法** | POST |
| **Content-Type** | application/x-www-form-urlencoded |
| **前置条件** | 已登录/未登录，均能访问 |

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| whereFrom | string | 否 | 请求来源标识（联登请求来源标识，取页面URL的whereFrom参数值透传） |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 结果码，200 表示成功，500 表示失败 |
| msg | string | 结果描述 |
| qrToken | string | 二维码登录 TOKEN，如 `10000-ab04ec99a724418385445f6e73fd19a4` |

#### 响应示例 - 成功

```json
{
  "qrToken": "10000-ab04ec99a724418385445f6e73fd19a4",
  "msg": "",
  "code": 200
}
```

#### 响应示例 - 失败

```json
{
  "qrToken": null,
  "msg": "",
  "code": 500
}
```

---

### 2. 获取二维码图片 (/qrLogin/getQrImage)

根据 qrToken 获取二维码图片。

| 项目 | 说明 |
|------|------|
| **接口地址** | `https://passport.vip.com/qrLogin/getQrImage` |
| **请求方法** | GET |
| **响应格式** | 图片流 |
| **前置条件** | 已登录/未登录，均能访问 |

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| qrToken | string | 是 | 二维码登录 TOKEN |

#### 响应结果

返回二维码图片流（PNG/JPG 格式）

#### 请求示例

```
https://passport.vip.com/qrLogin/getQrImage?qrToken=10000-5fc39232c4924137831d9d9bec72393b
```

---

### 3. 轮询检测二维码状态 (/qrLogin/checkStatus)

轮询检测二维码的扫码状态。

| 项目 | 说明 |
|------|------|
| **接口地址** | `https://passport.vip.com/qrLogin/checkStatus` |
| **请求方法** | POST |
| **Content-Type** | application/x-www-form-urlencoded |
| **前置条件** | 已登录/未登录，均能访问 |

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| qrToken | string | 是 | 二维码登录 TOKEN |
| whereFrom | string | 否 | 请求来源标识 |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 结果码，200 表示成功，500 表示失败 |
| msg | string | 结果描述 |
| status | string | 二维码状态（code=200时有值） |
| redirectUrl | string | 登录成功后跳转路径 |

#### 状态码说明

| 状态值 | 说明 |
|--------|------|
| NOT_SCANNED | 未扫描 |
| SCANNED | 已扫描 |
| CONFIRMED | 已确认（即已登录成功，需要跳转回来源页面） |
| INVALID | 已失效（需提示更新二维码） |

#### 响应示例 - 成功

```json
{
  "status": "CONFIRMED",
  "code": 200,
  "msg": "",
  "redirectUrl": null
}
```

#### 响应示例 - 失败

```json
{
  "msg": "",
  "code": 500,
  "status": null,
  "redirectUrl": null
}
```

---

## 扫码登录流程

```
┌─────────────┐     1. initQrLogin      ┌──────────────┐
│   智能体    │ ───────────────────────> │   登录前端    │
│   (Claw)    │                          │ (passport)   │
└─────────────┘                          └──────────────┘
       │                                        │
       │ 2. 返回 qrToken                        │
       │ <──────────────────────────────────────┤
       │                                        │
       │ 3. getQrImage(qrToken)                 │
       │ ──────────────────────────────────────>│
       │                                        │
       │ 4. 返回二维码图片                       │
       │ <──────────────────────────────────────┤
       │                                        │
       ▼                                        │
┌─────────────┐                                │
│  展示二维码  │                                │
└─────────────┘                                │
       │                                       │
       │                                       │ 5. 用户扫码
       │                               ┌───────▼───────┐
       │                               │   唯品会APP   │
       │                               └───────┬───────┘
       │                                       │ 6. 确认登录
       │                                       │
       │ 7. checkStatus(qrToken)               │
       │ ─────────────────────────────────────>│
       │ (轮询直到 CONFIRMED/INVALID)           │
       │                                       │
       │ 8. 返回状态                            │
       │ <─────────────────────────────────────┤
       │                                        │
       ▼                                        │
┌─────────────┐                               │
│  登录成功    │                               │
│ Cookie已设置 │                               │
└─────────────┘                               │
```

---

## 注意事项

1. **二维码有效期**: 二维码通常有效期为 3 分钟，过期后状态会变为 `INVALID`
2. **轮询频率**: 建议每秒轮询一次，避免频繁请求
3. **Cookie 保持**: 轮询过程中需要保持 Cookie，登录成功后 Cookie 中会自动包含登录凭证
4. **登录成功处理**:
   - 当 status 为 `CONFIRMED` 时，表示登录成功
   - 优先使用后端返回的 `redirectUrl` 进行跳转
   - 如果 `redirectUrl` 为空，取 Cookie 中的来源 URL 做跳转

---
