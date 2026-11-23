# 项目请求

使用 `project list` 获取全部项目，默认输出 Markdown 表格，需要机器可读数据时加 `--json`。通过 `token` 相关指令管理项目凭证。实际操作某个项目时，选择该项目对应的 token，使用 `req --token-id <凭证ID>` 调用项目接口完成操作。

使用 `req` 前先选择对应项目和角色的凭证，并用 `token info <凭证ID>` 在线查验；没有可用凭证时先创建。凭证绑定一个项目和角色，`req` 按凭证自动携带项目上下文，项目接口不需要也不能通过 `project_id` 等参数切换项目。`req` 使用项目 API Token，不会自动刷新 OAuth；重新运行 `auth login` 不会恢复过期或已撤销的项目 API Token。

先用 `token list` 选择凭证。以下路径仅演示参数写法，执行前必须替换成已确认的业务接口，不直接运行示例路径。

```sh
heyincli req --token-id <token-id> --method GET \
  --path '/api/items/{id}/' --path-params '{"id":123}' \
  --query '{"page":1}'

heyincli req --token-id <token-id> --method POST \
  --path '/api/items/' --body '{"name":"示例"}'
```

| 参数 | 用法 |
| --- | --- |
| `--token-id` | 必填，本地项目凭证 ID |
| `--method` | 必填，大写 `GET` 或 `POST` |
| `--path` | 必填，以 `/api/` 开头；可包含 `{name}` 占位符 |
| `--path-params` | JSON 对象，逐一填写路径占位符；不能多填或漏填。值不能为空，仅使用英文字母、数字、下划线、连字符、波浪号及非开头的点号 |
| `--query` | JSON 对象，值为字符串、数字、布尔值或这些类型的数组 |
| `--body` | POST 使用合法 JSON；省略表示 `null`；GET 不可使用 |
| `--test-env` | 本次请求是否使用测试环境，默认 `false`；测试环境使用 `--test-env` 或 `--test-env=true`，生产环境省略或使用 `--test-env=false`。布尔值必须用 `=` 连接 |

JSON 参数按当前 Shell 正确引用。查询分页通过 `--query` 的 JSON 对象传递业务接口规定的参数。

`--test-env` 对 GET 和 POST 均适用。根据用户目标选择请求环境，同一任务的查询、写入和回读使用同一环境；接口要求的查询参数和请求体仍需照常填写。

## 结果与失败处理

成功时标准输出直接是平台响应的 `data` JSON。例如平台返回 `{"code":0,"msg":"","data":{"list":[],"total":0}}` 时，CLI 输出 `{"list":[],"total":0}`，直接读取 `.list`；成功与否以退出码判断。

失败时检查非零退出码和标准错误；CLI 不输出业务错误信封，API 错误以 `API request failed (HTTP ..., code ...)` 表示。遇到 `code 4001010011` 时按 [版本管理](version-management.md) 强制更新。

POST 不会自动重试。写入出现超时、断连、响应异常或输出失败时，先使用相应查询接口核实实际状态；不能因命令失败就重复提交。无法核实时停止写入并说明尚未确认的对象和操作。

## 项目查询

查询项目概况，或处理参与者、表单与质疑、源文件、知情同意、随访、ePRO、eTMF、药物、监查、分析、日志及数据导出时，阅读 `heyin-project` 技能，按目标选择对应业务说明。

## 项目设置

查询或维护项目通用设置、中心、角色权限、成员及申请邀请、eSource/SD、AI 配置、通知配置、功能配置、eTMF、RTSM、方案设计时，阅读 `heyin-project-settings` 技能，按目标选择对应的领域说明。
