# 使用模板工程

模板目录来自本次 `tiana web list-template --json` 实际返回的数据。每页 `data.items` 含 name、display_name、description、status 和变量摘要；CLI 的 `--after` 查询下一页。选择符合用户核心功能与数据结构的工程；没有匹配项时按通用 Web 方法制作。

新应用默认由 Agent 创建所需的 SQLite 和 Git，按当前应用命名并保存 CLI 返回的实际实例 ID；用户明确指定已有实例时核实后复用。保存资源回执后执行：

```sh
tiana web init-template NAME --dir PROJECT_DIR --json
```

成功结果的 `data.directory` 是工程根目录，`data.metadata_path` 是元信息文件。CLI 负责下载校验和解压，工程仍保留占位符、SQL 和原始文件。下载失败先核对实际结果，再重新运行；不用链接地址当作创建成功依据。

## metadata.json 和变量

读取根部 metadata.json、README、依赖锁文件及构建脚本，按实际工程开发。元信息示例：

```json
{
  "name": "notes",
  "display_name": "记事本",
  "description": "个人笔记、文件夹、全文搜索和自动保存。",
  "variables": [
    {
      "name": "SQLITE_INSTANCE_ID",
      "placeholder": "__TIANA_SQLITE_INSTANCE_ID_f832a54c__",
      "description": "Agent 为本次应用创建或按用户指定复用的 SQLite 实例 ID",
      "files": ["source.json"]
    },
    {
      "name": "GIT_INSTANCE_ID",
      "placeholder": "__TIANA_GIT_INSTANCE_ID_a7c93e5b__",
      "description": "Agent 为本次应用创建或按用户指定复用的 Git 实例 ID",
      "files": ["source.json"]
    }
  ],
  "schema": "schema.sql",
  "seeds": "seed.sql"
}
```

variables 中每项给出完整随机占位符、用途和全部出现文件，路径相对于工程根目录。按 description 取实际值，逐个修改 files 中所有出现位置；相同变量保持同值。常见 WEB_ID、SQLITE_INSTANCE_ID、GIT_INSTANCE_ID 从本次资源回执或已核实的项目绑定取得，APP_NAME 使用用户应用名称。其他变量按自己的说明确定，不能猜实例 ID 或把自己的凭据当作变量。

六个内置模板通过 source.json 的 database_instance_id、git_instance_id 保存替换后的 ID；schema/seeds、Git 推送和 Web 项目绑定使用这组实际资源。

JSON 中要正确转义字符串，SQL 中按实际语法处理，源码中保留原语言的字符串语法；不能用未经转义的 shell 字符串拼接批量替换。替换后检查声明文件没有残留占位符、所有 JSON 能解析、清单绑定与资源回执一致。metadata.json 的变量声明可以保留用于说明模板来源，实际应用文件使用真实值。

## SQLite 初始化

在完成变量替换后，保持本次已确认的 SQLite 实例和分支，按顺序：

1. schema 未配置或相应文件不存在时跳过建表；存在时先阅读核对 SQL，再执行 `tiana sqlite shell INSTANCE -f SCHEMA_PATH --format json`。
2. seeds 未配置或相应文件不存在时跳过灌数；存在时阅读核对 SQL，再执行 `tiana sqlite shell INSTANCE -f SEEDS_PATH --format json`。

两项独立判断：schema 缺文件不阻止执行存在的 seeds。用户提供已有库时先查看相应表结构和数据，保证初始化符合当前任务，不把重复灌数当作恢复方法。指定分支时，两次调用都加相同 `--branch NAME`。

SQL 返回失败、断线或未知结果时停止后续发布，用独立只读查询核对已完成的结构与数据，不自动重放写入。初始化成功后进行应用定制、依赖安装、源码同步、构建及发布；工程 README 中的步骤与实际帮助一起核对。

## 模板图标

模板的源 `icon.png` 是用户应用的初始图标，保留图片并复用工程的静态资源复制配置。变量替换时不把 PNG 当文本处理。若下载模板没有源图标，按[应用图标](csr-apps.md#应用图标)由 Agent 自动生成并保存。干净构建后确认产物根目录 `icon.png` 可以解码，再发布；以后更新模板本身不会直接改变已有用户应用的图标。

## 构建和来源

模板 `source.repository`、`source.commit` 说明下载包的源工程来源，区别于用户应用自己的 Git 提交。创建用户仓库后记录实际 git_instance_id；提交和构建按 [源码流程](../../tiana-git/references/source-releases.md)。按下载工程的 README 和构建脚本确定命令、入口与产物目录。若脚本接收源码提交号并输出 TIANA_PROJECT_PARAMS，核对其中的 entry、database_instance_id、git_instance_id 和 source_commit，再用于配置 MGR Web 项目；database_instance_id 必须与本次执行 schema/seeds 的 SQLite 一致。核对模块、资源及 MGR Web 项目的 SQLite/Git 绑定后执行 `web publish`，再用 publish_id 查询状态。
