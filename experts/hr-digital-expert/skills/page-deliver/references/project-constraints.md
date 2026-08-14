# 项目合规约束

> 代码生成完成后的硬约束清单。agent 在阶段4 步骤5（代码合规检查）逐条自查并修复违规。
>
> 每条约束的结构固定：**约束陈述 → 适用条件 → 检查方法 → 违规判定 → 修复算法 → 自检清单**。
> agent 必须按这个顺序机械执行，不靠自由发挥。
>
> 后续新增约束往这里加（C2 / C3 …），不再散落到 `SKILL.md` / `step0-requirement.md`。

---

## C1. 文件上传存储路径

### 约束

服务端文件上传存储路径**必须**为 `/data/services/resources/{真实projectId}/`，其中 `{真实projectId}` 是当前项目的 project ID（从 `.deploy-state.json` 读取，**不是字面字符串 `{project_id}`**）。

**禁止**使用任何其他路径，包括但不限于：
- `/tmp/`、`/tmp/uploads/`
- `./uploads/`、`./public/uploads/`
- `/data/services/apps/{projectId}/uploads/`（apps 目录是代码部署区，不是资源存储区）
- 任何前端可写、无固定前缀的相对路径

### 适用条件：项目是否包含文件上传功能

逐项检查，**任一命中**即视为"项目有上传功能"，必须执行本约束的检查与修复：

1. `package.json` 的 `dependencies` 含上传中间件：`multer` / `formidable` / `busboy`
2. `server.js` / `app.js` / `index.js`（Node）或 `app.py` / `main.py` / `server.py`（Python）含上传信号：`multer(` / `upload` / `formData` / `multipart` / `文件上传`
3. 代码含 `mkdirSync` / `os.makedirs` + 形如上传目录的路径字符串

**三项全不命中** → 项目无上传功能，跳过本约束，直接判 PASS。

### 检查方法

**Step 1：取真实 projectId**

```bash
echo '{"projectDir":"<project_dir_abs>"}' | node "$PD" state show --input -
```

从返回的 `data.projectId` 取值（kebab-case，如 `summer-hiking-poster-20260601-192630`）。这就是修复时要填入路径的"真实 projectId"。

**Step 2：定位上传目录定义**

扫描服务端入口文件（`server.js` / `app.js` / `index.js` / `app.py` / `main.py` / `server.py`），grep 以下关键词定位上传目录的赋值/定义：
- `UPLOAD_DIR` / `uploadDir` / `upload_dir`
- `multer` / `destination`
- `mkdirSync` / `makedirs`
- `/data/services/resources` / `uploads`

**Step 3：逐个比对路径字面量**

对每个定位到的上传目录定义，检查其路径值属于下面哪种情况。

### 违规判定（两种）

**违规 A — 用了禁止路径**：上传目录被赋值为禁止值（`/tmp/`、`./uploads/`、`/data/services/apps/.../uploads/` 等）。

**违规 B — 字面占位符未替换**：路径含字面字符串 `{project_id}`（文档示例语法，模型生成代码时漏替换）。容器会真的创建一个名为 `{project_id}` 的目录，所有项目共用一个目录，数据串台。

> ⚠️ 区分：路径里出现 `/data/services/resources/${projectId}/`（JS 模板字符串变量）或 `/data/services/resources/<真实projectId>/`（已替换的真实值）→ **合规**。只有字面 `{project_id}` 才是违规 B。

### 修复算法

修复值 = `` `/data/services/resources/${真实projectId}/` ``（Step 1 取到的值）。

- **违规 A**：用 `replace_in_file` / `Edit` 把禁止路径字符串整段替换成修复值。
  - 例：`const UPLOAD_DIR = '/tmp/uploads/';` → `` const UPLOAD_DIR = `/data/services/resources/${projectId}/`; ``
  - 若代码里 `projectId` 变量未定义，补一行从 state/env 取值，或直接内联真实 projectId 字面量。
- **违规 B**：用 `replace_in_file` / `Edit` 把路径上下文里的字面 `{project_id}` 替换成 `${projectId}`（变量引用）或真实 projectId 字面量。
  - **只替换路径字符串内的 `{project_id}`**，不要全局替换——文档/注释里可能合法地出现这个词。
- **补 mkdir**：确保服务端启动时有 `fs.mkdirSync(UPLOAD_DIR, { recursive: true })`（Node）或 `os.makedirs(UPLOAD_DIR, exist_ok=True)`（Python）。缺失则补上，否则容器内目录不存在会导致上传 500。
- **避免字面量重复**：若项目有多处上传目录（如 `UPLOAD_DIR` + `AVATAR_DIR`），不要各自内联同一份真实 projectId 字面量——抽一个变量统一引用，既避免重复也方便后续改 projectId：

  ```js
  // ✅ 推荐：抽变量
  const PROJECT_ID = 'summer-hiking-poster-20260601-192630'; // 从 state 读取的真实值
  const UPLOAD_DIR = `/data/services/resources/${PROJECT_ID}/`;
  const AVATAR_DIR = `/data/services/resources/${PROJECT_ID}/avatars/`;
  ```

  ```js
  // ❌ 不推荐：两处都内联同一字面量，改 projectId 要改多处
  const UPLOAD_DIR = '/data/services/resources/summer-hiking-poster-20260601-192630/';
  const AVATAR_DIR = '/data/services/resources/summer-hiking-poster-20260601-192630/';
  ```

### 自检清单（修复后逐项确认）

- [ ] 所有上传目录路径均为 `/data/services/resources/{真实projectId}/` 形式
- [ ] 代码中不再出现字面 `{project_id}` 占位符（grep `'{project_id}'` / `"{project_id}"` 无结果）
- [ ] 不再出现 `/tmp/`、`./uploads/`、`/data/services/apps/.../uploads` 等禁止路径
- [ ] 服务端启动时有 `mkdirSync` / `makedirs` 创建该目录
- [ ] 重新 grep 上传关键词，确认无违规残留

自检全绿 → C1 PASS。任一项未过 → 继续修复直到全绿。

---

## C2. MongoDB 数据库名约束

### 约束

项目使用 MongoDB 时，连接的数据库名**必须**为当前项目的业务库，即 `MONGO_URI` 后拼接的库名必须是**真实 projectId**（从 `.deploy-state.json` 读取），使每个项目的数据隔离在独立库中。

**禁止**连接到 MongoDB 默认库/保留库，包括但不限于：
- `test`（MongoDB 未指定库名时的默认库，所有项目数据混在一起）
- `admin` / `local` / `config`（MongoDB 系统库）
- 其他与 projectId 无关的固定库名（如 `myapp`、`mydb`、`data` 等）

### 适用条件：项目是否使用 MongoDB

逐项检查，**任一命中**即视为"项目使用 MongoDB"，必须执行本约束的检查与修复：

1. `package.json` 的 `dependencies` 含 `mongoose` / `mongodb`（Node），或代码含 `pymongo` / `MongoClient`（Python）
2. 服务端代码含 `mongoose.connect(` / `MongoClient(` / `createConnection(`
3. 代码含 `MONGO_URI` 环境变量引用

**三项全不命中** → 项目不使用 MongoDB，跳过本约束，直接判 PASS。

### 检查方法

**Step 1：取真实 projectId**

```bash
echo '{"projectDir":"<project_dir_abs>"}' | node "$PD" state show --input -
```

从返回的 `data.projectId` 取值（kebab-case，如 `summer-hiking-poster-20260601-192630`）。

**Step 2：定位 MongoDB 连接串定义**

扫描服务端文件（`server.js` / `app.js` / `index.js` / `db.js` / `app.py` / `main.py`），grep 以下关键词：
- `mongoose.connect` / `createConnection` / `MongoClient`
- `MONGO_URI` / `mongodb://` / `mongodb+srv://`
- `dbName`

**Step 3：逐个提取连接串中的库名**

连接串形如 `mongodb://host:27017/<dbName>` 或 `mongodb+srv://host/<dbName>`。对每个连接定义，提取 `<dbName>` 部分比对。若连接串未写库名（如裸 `mongodb://host:27017`），MongoDB 会默认连 `test` 库 —— 视为违规。

### 违规判定（三种）

**违规 A — 连了默认/保留库**：库名为 `test` / `admin` / `local` / `config`，或连接串未指定库名（隐式落到 `test`）。

**违规 B — 连了与 projectId 无关的固定库名**：库名为 `myapp` / `mydb` / `data` 等字面量，多项目部署到同一 mongo 实例时数据互相串台。

**违规 C — 库名字面量与真实 projectId 不一致**：硬编码了形如 `summer-hiking-poster-20260601-192630` 的库名但与当前项目实际 projectId 不符（通常是从别的项目/示例抄来的）。

> ⚠️ 区分：`` `${process.env.MONGO_URI}/${PROJECT_ID}` ``（模板标准写法，PROJECT_ID 为项目常量或从 state 读取）→ **合规**。`process.env.MONGO_URI` 本身是 `mongodb://{projectId}-mongo:27017` 不含库名，**必须拼接 `/${projectId}` 才合规**。

### 修复算法

修复值 = 连接串的库名部分改为真实 projectId（Step 1 取到的值），推荐通过变量引用而非散落字面量：

```js
// ✅ 推荐（模板标准写法）
const PROJECT_ID = '<真实projectId>';
const MONGO_URI = process.env.MONGO_URI && `${process.env.MONGO_URI}/${PROJECT_ID}`;
await mongoose.connect(MONGO_URI);
```

- **违规 A**：把 `test` 等库名替换为真实 projectId；连接串未写库名的，补上 `/${projectId}`。
  - 例：`mongoose.connect('mongodb://mongo:27017/test')` → 按上方推荐写法重写。
- **违规 B**：把固定库名替换为真实 projectId（变量引用）。
- **违规 C**：把不一致的库名字面量替换为真实 projectId；若同文件多处出现，抽 `PROJECT_ID` 常量统一引用（同 C1 的"避免字面量重复"原则）。
- **Python**：`MongoClient(uri).get_database('<真实projectId>')` 或 URI 中直接带库名，同样禁止 `test` 等库。

### 自检清单（修复后逐项确认）

- [ ] 所有 MongoDB 连接串的库名均为真实 projectId（或引用其变量）
- [ ] 代码中不再出现连 `test` / `admin` / `local` / `config` 库的连接串
- [ ] 不存在未指定库名的裸连接串（`mongodb://host:port` 后直接 connect）
- [ ] `MONGO_URI` 引用处均拼接了 `/${PROJECT_ID}` 或等价真实库名
- [ ] 重新 grep `mongodb://` / `mongoose.connect` / `MongoClient`，确认无违规残留

自检全绿 → C2 PASS。任一项未过 → 继续修复直到全绿。
