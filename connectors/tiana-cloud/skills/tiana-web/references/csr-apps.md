# Tiana 应用要求

> Serverless Web 联动候选：以下 publish/status、归档和管控 channel 行为需配套 CLI、Web、Gateway、Agent、MGR、Control 及 app_web 验证版本。尚未发布，执行前核验实际环境能力；不把源码候选描述为线上已部署。

## 入口与路由

使用平台渲染的固定 [index.html 模板](index.html) 和哈希路由。该参考文件与 CLI/Web 的服务端模板一致：服务端先将 `__TIANA_BOOTSTRAP_SCRIPT__` 替换为 `/web/<实际 web_id>/_tiana/bootstrap.js`，再将 `__TIANA_BOOTSTRAP_DATA__` 替换为应用运行时 JSON；浏览器收到的是已完成替换的 HTML。

哈希深链接在直接打开或刷新后也应恢复当前路由；若页面数据需异步读取，应在读取完成后恢复该路由对应的状态。服务端先检查登录会话和应用访问权限，再返回此 HTML。未登录的托管请求跳转到所属环境的 Console 登录页，经绑定应用和固定站点回跳地址的短时授权码返回站点，站点后端兑换独立的 host-only 会话。回跳保留哈希片段；站点退出只注销站点会话。授权通过后，文档加载当前归档的 JavaScript 和 CSS。

应用与 Console 使用独立 origin；同一环境的多个应用共享站点 origin，路径划分不提供浏览器同源隔离。Bootstrap、session、logout 和 connection 使用站点同源入口。

模板提供 `<div id="app"></div>`。`entry` 指定的模块按正常方式启动并渲染应用。需要数据库连接时，调用 `window.tiana.connection()` 获取连接元信息，使用 `window.tiana.auth` provider 提供动态凭据；凭据只保存在内存中。加载指示器是临时的，与应用样式隔离。

## 确认账号与数据库

已确认 CLI 具备本流程命令时直接使用。命令缺失时按[开始使用](../../tiana/references/getting-started.md)安装匹配版本。

1. 复用本轮已完成的账号和额度检查；尚未检查时执行 `tiana status`。需要登录时，按分步登录流程展示链接并确认完成，不读取或输出凭据。
2. 项目已记录且已核实可用的数据库实例 ID 可直接复用，无需列举实例。否则用 `tiana sqlite list/show` 查找；确实没有可用数据库时执行一次 `tiana sqlite create NAME --wait`，保存完整实例 ID。中断后核实原请求和实例，不重复创建。
3. 复用已提供的实际表结构；缺少时执行 `tiana sqlite shell INSTANCE -e "SELECT name, sql FROM sqlite_schema WHERE type='table' ORDER BY name LIMIT 100" --format json`。将表结构和迁移文件保存在项目中。对已核对的 SQL 文件执行 `tiana sqlite shell INSTANCE -f schema.sql --format json`。`-e` 接受一条语句，多语句使用 `-f`。动态数据按 [JavaScript 数据库连接](../../tiana-sqlite/references/js-sdk.md)使用参数化 SQL。
4. 复用项目中已记录、已核实的 Web ID；未记录时先用 `tiana web list --json` 查找并核实，重名时依据实际 ID 确认归属；首次创建时执行一次 `tiana web create "应用名称" -m "应用描述" --entry assets/app.js --database-instance-id DATABASE_ID --json`，保存返回的 `data.id`。Web ID 仅由 MGR 生成；CLI 不生成或提交 Web ID；描述为可选元数据（`-m`/`--description`，最多 1024 个 UTF-8 字节），名称仅用于展示，不能用名称推导 ID，不能自行指定 ID。结果未知时保持名称、描述和所有创建参数不变，重复同一条 create 命令恢复原请求，不删除待完成记录、不另发创建请求。成功后继续构建、预览或发布时复用该 ID，不重复创建。
5. 将非敏感 Web ID 和数据库 ID 保存在项目交付记录中。entry 仅能在 create 指定，包括省略后的纯文件托管类型；创建后不可修改，publish/serve/update 都不能覆盖。数据库、Git、名称、描述可用带 expected_revision 的 web update 修改。

## 运行时数据库连接

SDK、参数化 SQL 和结果解析按 [JavaScript 数据库连接](../../tiana-sqlite/references/js-sdk.md)处理。应用必须使用支持 `auth` 的 SDK 和 `window.tiana.auth` provider；`window.tiana.connection()` 用于获取连接元信息。共享 provider 和 adapter，不读取 Token 快照，不保留旧 SDK、旧 Bootstrap 或实例 Token 回退路径。

CLI 本地预览优先复用已保存的 CLI 登录，通过一次性本地启动链接授权浏览器；凭据刷新和持久化锁由 CLI/SDK 负责，refresh token 不交给页面。没有可用的已保存账号时才走独立 Console 登录。配套 Web/MGR 托管 Bootstrap 也提供 `window.tiana.auth`，由现有 HttpOnly 登录会话在服务端取得并同步账号授权。账号/租户级 access token 的权限不局限于应用目标实例，业务代码应在相应信任范围内运行。用户要求验证或排查连接故障时，按 [目标托管环境核验](../../tiana-sqlite/references/js-sdk.md#核验目标托管环境)检查实际 provider 和只读 SQL 链路。模板应用常规发布后由用户检查页面；没有运行时验证结果不等于确认缺失，也不代表链路已连通。

凭据只保存在内存，不写入源码、构建产物或浏览器持久存储。skills 不读取 refresh token、不调用刷新接口、不设置管理地址；刷新和授权同步由 SDK/CLI 或运行时代理处理，部署路由由外围环境负责。鉴权失败不自动重放 SQL，写入结果不明时先用独立只读查询核实。

## 体验优化建议

### 数据预取与本地缓存

数据量不大、可在浏览器中有界保存时，尽可能使用 `prefetch + local cache`，降低 Web 应用与数据库之间 RTT 对交互的影响。优先取得首屏所需数据，再预取常用列表、筛选项和相邻页面数据；切换视图、筛选和搜索尽量复用本地结果，避免每次交互都等待 SQL。合并重复读取并复用正在进行的同一查询，控制预取范围、并发、记录数和缓存大小，避免为了预取阻塞首屏或无界加载整库。

这里的 local cache 指应用的数据缓存，默认使用内存，数据库仍是持久化权威。按账号／租户、数据库、Web ID 和查询条件区分缓存；退出登录、切换身份或数据库时清空，并丢弃旧上下文中的在途查询结果。根据数据更新频率设置过期或重新校验策略，写入确认成功后更新或失效相关缓存；协作、实时性要求高的数据继续同步，不能用旧缓存覆盖远端新数据。写入结果不明时沿用独立读取核实，不自动重放。凭据不进入数据缓存。

### 将常用小资源内嵌到 JavaScript

小图片、图标以及高频使用的 CSS、图片等资源，建议在构建时打包、编码到 JS 中，减少独立资源请求和加载等待。例如将小图片编码为 data URL 或将 SVG 内嵌，将 CSS 作为字符串随模块加载并在渲染前应用。内嵌方式须兼容平台已有 CSP，CSS 中的图片引用也要正确处理。

控制编码后的 JS 总体积、解析成本和重复内容；大图片、低频资源或内嵌后明显拖慢首屏的资源使用相对路径加载。构建后核对资源是否实际进入 JS，不能仅凭源码中的 import 判断已内嵌；入口模块自行加载 CSS：可内嵌样式，也可用相对 import.meta.url 创建 link 加载独立 CSS；平台不接受 styles 参数。只内嵌随应用发布的静态资源，不把用户数据或凭据固化到产物中。

## 构建与项目参数

输出浏览器可直接执行的 ES 模块、CSS 和资源，引用使用相对路径。Vite 库模式在顶层配置 `define: { 'process.env.NODE_ENV': JSON.stringify('production') }`，并验证产物无残留引用。入口与资源路径以实际工程的构建配置为准；入口模块自行加载 CSS。不要生成或读取 tiana.app.json，不提交 style、rendering、routing 参数。

Site 参数来自 MGR 的 web_project：name、description、固定 entry、可选 database_instance_id、git_instance_id、source_commit。实例只保存通用 Serverless 属性。首次创建可传 `--entry assets/app.js --database-instance-id DATABASE_ID --git-instance-id GIT_ID`；Git commit 可以稍后用 `web update ID --expected-revision REV --source-commit FULL_COMMIT` 录入，完整小写 40/64 位 commit 要求已有 Git 绑定。MGR 验证关联实例属于当前租户、产品正确且可用。源码构建和远端引用核验见[源码发布](../../tiana-git/references/source-releases.md)，参数更新与归档发布是分开的操作，不假称两者跨服务原子提交。

CLI 将目录打包为 ZIP Store/Deflate 的一个 `.tweb`，根目录是零字节 web.yaml 与 data/。web.yaml 预留 Web server 配置，与 Site 参数无关，目前为空。data/ 前缀不对外暴露，底层只提供 GET/HEAD 精确文件访问，没有目录索引、默认 index.html 或 SPA fallback；底层可托管 HTML，带 entry 的 Site 使用固定 CSR/hash Bootstrap。

归档和原始资源总量各最多 16 MiB、最多 4096 个资源、单路径最多 1024 个 UTF-8 字节；拒绝符号链接、特殊文件和旧清单。publish 上传前检查实际归档含固定 entry。资源 URL 为 `/web/<id>/assets/<relative_file>`；例如归档内的 `assets/app.js` 对应 `/web/<id>/assets/assets/app.js`，路由前缀与文件目录各保留一层。经过 Web→Gateway→Agent→app_web，不生成 OSS 签名直链。channel=0 透传原生 GET/HEAD，channel=1 提供 publish/status 等 HTTP 管控，协议版本保持不变。

## 应用图标

构建前检查工程根的 `icon.png` 和工程实际采用的静态资源目录，如 `public/icon.png`；依赖包和旧 dist 内的图片不算源码。用户本次明确提供新图片时使用它，否则直接复用源码图片，包括模板自带的图标，不因应用改名或每轮修改重新生成。

源码没有图标时，由执行任务的 Agent 自动生成真实 PNG：按应用标题取首个汉字或英文首字母，搭配固定配色，建议 256×256 正方形。可用 Canvas／本地图像工具绘制，汉字选择可用的中文字体，查看图片确认文字清晰、没有缺字；不把准备图片转交给用户，也不把文字预览、SVG 改扩展名当作 PNG。

图片写入源码静态资源目录，再使用现有构建复制能力将它输出到产物根目录 `icon.png`；工程没有复制能力时补充直接的构建步骤。先准备源图片、提交，再从确定提交干净构建。发布前检查产物图片能解码，确认现有 CLI 打包后为 `data/icon.png`；无需新增 CLI 参数。

配套图标服务部署后，每次发布含图标的包都会覆盖应用的独立管理图标；包里没有图标时保留当前图片。Console 单独上传不改写源码，后续含图标的发布仍以包内图片覆盖；用户要持续更换图标时同步修改源码。独立图标可在应用休眠或停用时读取，本地构建验证与目标环境的展示验收分别记录。

## 预览与发布

需要源码关联时，先按[应用源码与版本发布](../../tiana-git/references/source-releases.md)完成已授权的 Git 同步，再构建该提交的产物。纯个人静态站无需数据库或 Git 实例。

1. 用户需要本地预览时执行 `tiana web serve WEB_ID --dir DIST --port 4174`。CLI 先读取 MGR 项目和固定 entry，不能用本地参数覆盖。
2. 核验账号与配套环境。CLI 用登录账号读取 MGR 的项目参数；数据管控优先使用互斥的 `TIANA_TOKEN` / `TIANA_TOKEN_FILE`，否则使用该账号有效 access token。Endpoint、Instance、Group、Tenant Token 只要有效且作用域覆盖目标，均可用于发布；不要求签发或保存实例 Token，不读取 `instance-tokens.json`。显式凭据错误或拒绝时不回退、不重发；凭据不写入构建目录。
3. 使用保存的 Web ID 发布；CLI 负责打包，不要求用户手工生成归档：

```sh
tiana web publish WEB_ID --dir DIST --json
tiana web status WEB_ID --publish-id PUBLISH_ID --json
tiana web status WEB_ID --json
```

`publish` 经 Gateway 的业务管控 channel 上传单个归档。S3 覆盖固定 key，确认上传后返回，随后异步 reload；`uploaded: true` 不等于已激活。保存 `publish_id`、SHA256、Web/实例 ID。按同一 ID 查询的是上传回执，`REMOTE_COMMITTED` / `SUCCEEDED` 与 `uploaded: true` 表示归档上传事实；再执行不带 `--publish-id` 的当前内容查询，确认 `state: running`，且 `remote_sha256`、`serving_sha256` 都等于目标归档 SHA256，才报告目标内容正在提供服务。不要等待 `ACTIVATED`，也不能仅凭回执 `SUCCEEDED` 宣称已生效。CLI 在发送前保存不含凭据的本地回执。

结果未知时只查询，禁止自动重放 PUT。回执仅在 App 内存有界保留，重启/过期后的 `404 PUBLISH_NOT_FOUND` 表示原回执未知；检查不带 `--publish-id` 的当前内容与保存的目标 SHA256：若应用为 `running` 且两种校验和均匹配，可报告目标内容正在服务，同时保留原上传回执结果未知；不匹配时不能报告目标内容生效，不能据回执丢失宣称失败，也不自动重发。相同归档可被多次发布，摘要匹配不能识别是哪一次上传触发生效。再次明确执行 publish 会生成新 ID 并覆盖当前对象。没有 Web 版本列表、版本 URL、版本恢复、显式 reload 命令。

当前内容查询的 `state` 是应用运行状态；回执查询的 `state` 是上传操作状态。JSON 外层 `status: succeeded` 只表示这次查询成功。当前查询的 `publish` / `publish_id` 为空是合理的，不从摘要推导发布 ID。配套新版 CLI 的 `query_kind: current / receipt` 可区分两类查询；缺少该附加字段时依据是否传入 `--publish-id` 判断。

4. 托管入口使用所属环境 Site origin 的 `/web/<id>/`，Console 详情为 `/console/web/<id>`。报告 Web/实例 ID、publish_id、归档校验和、上传与激活状态，以及可选数据库/Git 关联。环境不具备候选能力时报告具体阻塞并提供本地开发地址；不自行修改部署。

## 应用列表与删除

用 `tiana web list --json` 核对当前账号拥有的 Web 应用，优先使用已保存的真实 ID。用户明确要求删除时，执行 `tiana web delete WEB_ID --force`；需要等待源站清理完成时加 `--wait --json`。不得把失败恢复、重新发布或清理本地构建目录当作删除云端应用的授权。

删除会关闭应用入口并通过 Web 实例生命周期清理当前归档，关联 SQLite、Git 不随之删除。只收到 `state: deleting` 时报告已受理；收到 `state: deleted` 才报告本次源站清理完成。空应用、上传中和已发布的应用均可删除；本地仍有未完成的 CLI 创建操作时，先按原请求恢复该操作。已受理的删除等待 Control 确认实例存储删除完成，MGR 不枚举或删除 S3 对象；公开缓存按缓存策略失效。中断后保留待完成记录，用原 ID 恢复，详情见[CLI 命令](../../tiana/references/cloud-cli.md)。

## 应用文件

配套文件存储环境中，`mount` 的第二个参数提供 `files`。先创建 WebApp 取得 ID，再本地预览；文件范围与是否发布无关。上传、下载、图片续期和 CLI 路径见[WebApp 文件存储](files.md)。
