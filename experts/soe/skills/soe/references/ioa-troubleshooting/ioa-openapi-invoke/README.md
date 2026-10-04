# iOA OpenAPI 调用技能 · 使用手册（面向人）

> 本文件是**给人看的**使用说明。Agent 的执行入口是同级的 `SKILL.md`（被自动加载的就是它）；本 README 不参与技能加载，仅供安装、配置、排障参考。
>
> 技能名：`ioa-openapi-invoke`　|　定位：让你针对**自己的 iOA 系统**，用自然语言或命令行调用**任意**云规范开放 API。

---

## 目录
1. [它能做什么](#一它能做什么)
2. [环境准备](#二环境准备)
3. [配置你自己的 iOA 地址与凭证](#三配置你自己的-ioa-地址与凭证)
4. [两种使用方式](#四两种使用方式)
5. [命令速查](#五命令速查)
6. [一句话授权](#六一句话授权)
7. [用自然语言调用其它接口](#七用自然语言调用其它接口)
8. [常见接口示例](#八常见接口示例)
9. [安全须知](#九安全须知)
10. [故障排查 FAQ](#十故障排查-faq)

---

## 一、它能做什么

- **一句话授权**：说「给张三授权 OA系统」，自动查账号 → 查资源 → 存在则授权 / 缺失则告知。
- **自然语言调用任意接口**：查账号、查终端、查资源、查 EDR 事件、查合规、创建账号、加黑名单、解绑资源…… 凡是 `references/api-docs/云规范接口/` 里有的接口都能调。
- **多客户隔离**：每个客户一份配置，互不串环境。
- **自动签名与解析**：TC3-HMAC-SHA256 签名、响应/错误识别、敏感字段 RSA 加密全自动。
- **读写保护**：写操作默认拦截，需显式确认，避免误操作生产系统。

适用：iOA 7.x+ 私有化部署（默认），亦兼容 SaaS。

---

## 二、环境准备

```bash
cd <技能目录>            # 本工具内置于专家技能 references/tools/openapi-invoke/
pip install -r requirements.txt   # requests, cryptography
```

---

## 三、配置你自己的 iOA 地址与凭证

需要 3 项信息：

| 项 | 含义 | 从哪来 |
|---|---|---|
| `base_url` | iOA 后台地址 | 你登录控制台的地址，私有化形如 `https://内网域名:8443` |
| `secret_id` / `secret_key` | API 凭证 | 控制台 **系统设置 → 第三方对接 → API接口管理 → 添加API凭证** |
| `service` | 签名服务名 | 私有化留空（自动 `capi`）；SaaS 填 `ioa` |

> 凭证等价于该管理员的权限，务必保密。

### 方式 A：向导生成（推荐）
```bash
cd scripts
python ioa_cli.py init --customer mycompany
```
按提示输入即可，结束自动测连通。加 `--encrypt` 可加密存储凭证。

### 方式 B：手动编辑
复制 `configs/sample.json` 为 `configs/mycompany.json` 填好即可。

### 方式 C：环境变量（不落盘，适合 CI）
```bash
export IOA_BASE_URL=https://ioa.your-company.com:8443
export IOA_SECRET_ID=AKIDxxxx
export IOA_SECRET_KEY=xxxxxxxx
```

配置好后先验通：
```bash
python ioa_cli.py test --config ../configs/mycompany.json
```

---

## 四、两种使用方式

### 1）作为 CodeBuddy 技能（自然语言，推荐）
本工具内置于 `ioa-troubleshoot-expert` 专家技能（`references/tools/openapi-invoke/`），在专家会话中**直接说需求**即可，命中触发词会自动加载并执行，例如：
- “用 iOA 给账号 张三 授权 OA系统”
- “查一下 iOA 里 lisi 这个账号”
- “列出最近的 EDR 高危事件”
- “把这台设备加黑名单”

### 2）命令行直接调用
见下方[命令速查](#五命令速查)。

---

## 五、命令速查

```bash
cd scripts
```

| 子命令 | 作用 | 示例 |
|---|---|---|
| `init` | 向导生成客户配置 | `python ioa_cli.py init --customer A` |
| `test` | 连通性 + 签名测试 | `python ioa_cli.py test --config ../configs/A.json` |
| `grant` | 一句话授权 | `python ioa_cli.py grant --account 张三 --resource OA系统 --config ../configs/A.json` |
| `call` | 调用任意接口 | 见下 |
| `encrypt` | 单独加密一段文本 | `python ioa_cli.py encrypt --text 'Pwd@1' --config ../configs/A.json` |
| `pubkey` | 取后台公钥 | `python ioa_cli.py pubkey --config ../configs/A.json` |

`call` 参数：

| 参数 | 说明 |
|---|---|
| `--action` | 接口动作，如 `Assets/Account/DescribeLocalAccounts`（不含 `/capi`）|
| `--body` / `--body-file` | 请求体 JSON（字符串或文件）|
| `--confirm-write` | 放行写操作（默认拦截非只读动作）|
| `--pwd-field` | 对 body 中指定字段做后台 RSA 加密后再发 |
| `--version` | 覆盖 `X-TC-Version`（默认 2022-06-01）|
| `--raw` | 原样打印完整响应（含 RequestId）|
| `--config` | 客户配置文件 |

---

## 六、一句话授权

```bash
python ioa_cli.py grant --account 张三 --resource OA系统 --config ../configs/mycompany.json
```

| 情形 | 结果 |
|---|---|
| 账号✅ 资源✅ | 🎉 授权成功 |
| 资源不存在 | ❌ 告知资源不存在（并列相似资源），不授权 |
| 账号不存在 | ❌ 告知账号不存在，停止 |
| 同名资源多项 | ⚠️ 提示加 `--resource-area` 指定资源组 |

参数：`--resource` 可多次或逗号分隔；`--resource-area` 消歧；`--expire` 到期时间戳（0=永久）；`--dry-run` 只预览不下发。

---

## 七、用自然语言调用其它接口

Agent（或你本人）按 5 步把任意需求翻译成 `call`：

1. **找接口**：查 `references/接口调用速查.md` 的「意图→Action」表；没有就到 `references/api-docs/云规范接口/版本：2022-06-01/`（技能内置全量文档）检索对应 `.md`。
2. **构造 body**：查询类用 `Condition`（`Filters`/`FilterGroups`/`Sort`/分页）；写类按文档示例。
3. **名称→ID**：用户给名字、接口要 ID 时，先用一次只读 `call` 把名字换成 ID（账号名→AccountId、资源名→ServiceId、资源组名→AreaId、终端→DeviceId…）。
4. **发起调用**：只读直接调；写操作加 `--confirm-write` 并先复述确认；含密码加 `--pwd-field`。
5. **解读响应**：成功取 `Data`；失败按 `API 错误(Code): Message` 处理。

> 一句话总结：**没有“调不了的接口”，只是 body 不同。**

---

## 八、常见接口示例

完整可套用示例（含 body 模板）见 [`references/接口调用速查.md`](references/接口调用速查.md) 第 6/7 节。这里给两个最常用的：

查账号：
```bash
python ioa_cli.py call --action Assets/Account/DescribeLocalAccounts \
  --body '{"Condition":{"PageNum":1,"PageSize":10,"FilterGroups":[{"Filters":[{"Field":"UserId","Operator":"eq","Values":["zhangsan"]}]}]},"ShowFlag":1}' \
  --config ../configs/mycompany.json
```

设备加黑名单（写操作）：
```bash
python ioa_cli.py call --action NGN/AddBlackDevices \
  --body '{"device_ids":["DEVICE_MID"]}' --confirm-write \
  --config ../configs/mycompany.json
```

---

## 九、安全须知

- 凭证即管理员权限，勿提交真实 `secret_key`；优先环境变量或 `--encrypt` 加密存储。`.gitignore` 已忽略 `configs/*.json`（除 sample）。
- `base_url` 仅指向你自己的 iOA 后台，由你显式提供；技能不连接其它内网地址。
- 写操作默认拦截，执行前请确认目标客户与参数，再加 `--confirm-write`。
- 多客户务必核对 `--config`，避免操作下发到错误环境。
- `verify_ssl` 默认 `false` 兼容自签名证书；用可信证书时建议置 `true`。

---

## 十、故障排查 FAQ

| 现象 | 可能原因 / 处理 |
|---|---|
| 401 鉴权失败 | SecretId/SecretKey 错误；本机与服务器时钟不同步（需 ±5 分钟内）；缺 `X-TC-Version` |
| 响应是 `CommonRsp` 之类异常格式 | API 版本号没传对，确认 `api_version=2022-06-01` |
| 连接失败 / 超时 | `base_url` 不可达、端口不对、证书问题（私有化设 `verify_ssl:false`）|
| SaaS 调用签名错 | 把配置 `service` 设为 `ioa` |
| 写操作被拦截 | 这是保护机制，确认无误后加 `--confirm-write` |
| 找不到接口 | 到 `references/api-docs/云规范接口/版本：2022-06-01/` 按目录检索后用 `call` |
