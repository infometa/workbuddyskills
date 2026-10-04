# 能力边界与暂不可用项

## 何时使用

用户要求的能力不在 `ebuilder-form schema` 中，或命令返回 `operation_unknown` / `path_forbidden` 时读取本文件，用于**如实告知边界并给出替代路径**，而不是换接口硬试。

## 当前不在 CLI 能力范围内

| 能力 | 状态 | 替代路径 |
| --- | --- | --- |
| 新建/发布 eBuilder 应用、表单与自定义接口 | 未纳入 CLI | 在 E10 建模中心完成，CLI 只消费已发布产物 |
| 修改 List/NList 页面布局、显示列、固定条件 | 未纳入 CLI | 页面配置在 E10 端完成；CLI 的 `list.config` / `nlist.config` 只读 |
| 表单字段的新增、删除与元数据修改 | 未纳入 CLI | `fields.get` / `options.get` 只读 |
| 附件上传下载、OCR、图片与本地文件解析 | 未纳入 CLI | 本模块不涉及；其它模块（如 `weaver-e10-yepiaotong-connector`）处理文件类能力 |
| 表单数据的批量导入/导出 | 未纳入 CLI | 只能逐条走 OpenAPI / 自定义接口写操作 |
| 审批、流程流转、转办与加签 | 不属于本模块 | 走 `weaver-e10-workflow-connector` |
| 人员、部门、岗位与组织架构查询 | 不属于本模块 | 走 `weaver-e10-hrm-connector` |
| 未出现在 `ebuilder-form schema` 中的任何 operation | 一律不可用 | 先跑 `weaver-work-cli ebuilder-form schema` 核对 |

## 硬边界（违反即失败）

- 禁止绕过 `weaver-work-cli` 直接 `curl` / `fetch` 访问 E10 接口，禁止直连 `/api/bs/` 路径。
- 禁止写死默认域名；系统地址由登录态决定。
- 禁止从 `menuId`、`appId`、`listId`、`objId` 互相猜测。
- 禁止手工构造 NList 的 `customConfig`（LZW 编码），必须用 `nlist.config` 的返回值。
- 禁止手工构造或跨操作复用 continuation。
- 禁止用字段显示名当写入键；`name == id` 的自定义字段必须改用 `config.dataKey`。
- 查询全部页达到或超过 100 页预算时，请用户增加筛选条件，不得拆成多次单页查询规避。
- 不得通过 `checkRight=false` 绕过数据创建、修改或删除的权限校验。
- 写操作返回 `write_uncertain` 时立即停止，禁止自动重放。

## 失败出口

| 现象 | 处置 |
| --- | --- |
| `operation_unknown` | 该 operation 不在 schema 中，跑 `weaver-work-cli ebuilder-form schema` 核对可用清单 |
| `path_forbidden` / `origin_invalid` | 触碰了地址或域名红线，停止并说明原因，不要改写路径绕过 |
| `protocol` | 请求协议不被接受，检查是否为 CLI 未覆盖的地址形态，不要手工改协议 |
| `session_expired` | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |

## 自检命令

遇到"不知道能不能做"时，先跑：

```text
weaver-work-cli ebuilder-form --help
weaver-work-cli ebuilder-form schema
```

以 `schema` 为唯一事实来源：没有出现在 schema 中的能力，不要写成可执行步骤。
