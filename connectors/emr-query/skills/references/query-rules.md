# EMR 只读查询 — 总限制规则

> 本文件对当前保留的 48 个只读接口统一生效，使用前必过。

---

## 一、能力边界（最高优先级）

### ✅ 允许：只读查询
- 所有 `Describe*` / `Inquiry*` / `Inquire*` 接口
- 文档总数 48 个，分布在 9 大分类中

### ⛔ 禁止：任何写接口
`Create*` · `Modify*` · `Terminate*` · `Run*` · `Delete*` · `ScaleOut*` · `Add*` · `Set*` · `Mount*` · `Uninstall*` · `Install*` · `Sync*` · `Attach*` · `Resize*` · `Deploy*` · `Reset*` · `Convert*` · `StartStop*`

---

## 二、认证与工具

1. **统一调用工具**：官方 `tccli`
2. **凭证来源**：`tccli auth login` 或已有 `~/.tccli/default.credential`
3. **简单参数模板**：
   ```bash
   tccli emr <Action> --region <region> --version 2019-01-03 --cli-unfold-argument --Param1 value1
   ```
4. **复杂参数模板**：
   ```bash
   tccli emr <Action> --generate-cli-skeleton > /tmp/<Action>.json
   tccli emr <Action> --region <region> --version 2019-01-03 --cli-input-json file:///tmp/<Action>.json
   ```
5. **Region**：由用户指定；未指定则确认
6. **密钥纪律**：禁止在命令行显式传 `--secretId` / `--secretKey` / `--token`

---

## 三、调用纪律

| 规则 | 说明 |
|------|------|
| 可查必查 | ID 类参数先通过 `DescribeInstancesList` 等只读接口获取，禁止编造 |
| 必传参数校验 | 调用前确认必传参数齐全；嵌套参数优先用 skeleton |
| 先 help 再下手 | 参数不确定时先执行 `tccli emr <Action> help --detail` |
| 不重试原则 | 失败后先报告错误码与 Message；用户明确要求时再重查 1 次 |
| 频率控制 | 1 秒内不超过 20 次；高频接口按官方限频执行 |
| 大结果截断 | 单次默认展示 20 条，必要时提示翻页参数 |
| 敏感参数不回显 | 输出中不要回显密钥、Token、Cookie 等敏感值 |

---

## 四、统一错误处理

### 返回值结构

成功：
```json
{"TotalCnt":1,"InstancesList":[...],"RequestId":"xxx"}
```

失败：
```json
{"Response":{"Error":{"Code":"<code>","Message":"<msg>"},"RequestId":"xxx"}}
```

### 错误码分类处理

| 错误码前缀 | 含义 | 处理 |
|-----------|------|------|
| `AuthFailure.*` | CAM 权限不足 | 提示授权 `emr:<Action>` |
| `UnauthorizedOperation` | 未授权操作（可能需资源级授权） | 检查 `qcs::emr` 资源权限 |
| `InvalidParameter.*` | 参数格式 / 范围错误 | 先看 `help --detail` 和接口文件 |
| `MissingParameter` | 缺少必传参数 | 用 skeleton 或接口文件补齐 |
| `UnknownParameter` | 参数名不存在 | 按 `tccli emr <Action> help` 修正 |
| `ResourceNotFound.*` | 资源不存在 | 检查实例 / 集群 / 节点 ID 是否真实存在 |
| `FailedOperation` | 集群类型或业务状态不匹配 | 检查集群类型、调度器、SL/HBase/TKE 前提 |
| `InternalError` | 内部错误 | 报告 `RequestId`，由用户决定是否重试 |
| `LimitExceeded` | 频率限制 | 延迟后重试 |

---

## 五、决策流程

```text
用户请求查 X → X 是 Describe*/Inquiry*？
  ├─ 否 → 拒绝：emr-query 仅支持只读查询
  └─ 是 → 在 48 接口文档中？
            ├─ 否 → 说明当前 skill 未收录
            └─ 是 → 查对应接口文件
                      ↓
            参数简单？ ── 是 ──→ 用 --cli-unfold-argument
                          │
                          否
                          ↓
                先 generate-cli-skeleton 再 file:///tmp/<Action>.json 调用
                          ↓
                        成功 → 展示摘要 + RequestId
                        失败 → 按 §四 处理
```

---

## 六、频率限制总览

| 接口 | 限频 |
|------|------|
| `DescribeHiveQueries` | 100 次/秒 |
| `DescribeImpalaQueries` | 100 次/秒 |
| 其余多数接口 | 20 次/秒 |

> 维度：`API + 接入地域 + 子账号`

---

## 七、实测状态（2026-06-30）

> 当前连接器主调用路径已切到官方 `tccli`，状态检查使用 `DescribeInstancesList`；文档范围已收敛为当前可直接调用的 48 个接口。

| 状态 | 数量 | 说明 |
|------|------|------|
| OK | 37 | 返回成功，可直接调用 |
| PARAM | 9 | 调用到达接口，但当前参数模板仍不完整或不正确 |
| DEPRECATED | 1 | 已废弃接口 |
| RESOURCE | 1 | 需要真实业务资源 ID |

### 使用建议
- 优先通过 `tccli emr <Action> help --detail` 确认参数名是否发生变化。
- 对 `Page` / `PageSize`、`Offset` / `Limit` 这类分页参数不要想当然复用。
- 嵌套对象优先用 skeleton 文件，不要手写超长参数串。
- 对 `PARAM` 接口，先按最新报告补齐已知缺失字段，再进入业务级联调。
