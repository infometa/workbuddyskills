# 生产就绪审计清单（prod-fix）

> 本清单由 `commands/prod-fix.md` 引用，用于「生产 k8s 发布失败后恢复重发」场景。
> `anydev publish` 成功后，COS 归档的代码会被生产流水线拉取、按项目根目录的 Dockerfile 构建镜像并部署到生产 k8s。这一步失败的根因几乎都落在 Dockerfile 或其依赖文件上，故 prod-fix 在重发前先做本审计。

## 用法约定

- `SKILL_DIR` = page-deliver skill 目录；`PD` = `${SKILL_DIR}/bin/page-deliver.js`
- 模板单一来源：`${SKILL_DIR}/assets/templates/dockerfile/Dockerfile.node.tmpl` 与 `Dockerfile.python.tmpl`（与 `pack-upload.js` 内置 fallback 一致，不要另造模板）
- 所有 `state update` 命令必须带 `projectDir` + `fields`
- 审计顺序：按下表逐项检查并**静默自动修复**；只有遇到「停下问用户」的项才中止后续部署

## 审计输出约定

- **静默进行**：审计与自动修复过程**不向用户输出技术细节清单**（端口、入口、Dockerfile 等用户不理解）。用户只需看到最终的部署结果。
- **仅在涉及业务功能改动时才打断用户**：如需新增/改写业务代码、或入口完全缺失无法推断，才停下用用户能理解的话询问，不要堆技术细节。
- 非业务功能的问题（端口、入口、Dockerfile、依赖文件、state flag 同步等）一律静默自动修复。

## 检查项

### 1. Dockerfile 存在

- **检查**：项目根目录是否有 `Dockerfile`
- **模板位置**：`${SKILL_DIR}/assets/templates/dockerfile/`
  - node → `Dockerfile.node.tmpl`
  - python → `Dockerfile.python.tmpl`
- **自动修复**：缺则按 `projectType` 从模板 `cp` 到项目根,并且做合适的新增/校正使得项目可以启动
  ```bash
  cp "${SKILL_DIR}/assets/templates/dockerfile/Dockerfile.<node|python>.tmpl" "<project_dir>/Dockerfile"
  ```
- ⚠️ 在已有 Dockerfile 基础上**只新增/校正，不要动已有的正确内容**

### 2. 依赖文件存在

- **检查**：node 项目要有 `package.json`；python 项目要有 `requirements.txt`
- **自动修复**：
  - node 缺 `package.json` → 停下问用户（无法推断依赖）
  - python 缺 `requirements.txt` → 扫描代码 `import`/`from ... import` 生成基础依赖（flask、gunicorn、pymongo、python-dotenv、requests 等），写入项目根，并提示用户补全版本号

### 3. 端口一致

- **检查**：
  - Dockerfile `ENV PORT` 与 `EXPOSE` 一致，且端口 = 3000（生产固定，不要改动）
  - node：`server.js` 用 `process.env.PORT` 读取端口，而非硬编码数字
  - python：`app.run`/gunicorn `--bind` 用 `0.0.0.0:3000`
- **自动修复（不告诉用户）**：Dockerfile 端口行不符 → 按模板校正（`ENV PORT=3000` + `EXPOSE 3000 [9999]`）；代码硬编码端口（如 `app.listen(8080)`）→ 直接改为读取 `process.env.PORT`（node：`const PORT = process.env.PORT || 3001;`，python：gunicorn `--bind 0.0.0.0:3000`）。端口属非业务功能改动，静默修复
- **`ENV PORT` 有兜底**：`pack-upload.js` 打包时会把 Dockerfile 的 `ENV PORT` **强制归一**为 `3000`（缺失则补上），漏改也不会带错值上生产。但 `EXPOSE` 行、gunicorn `--bind` 与代码硬编码端口**不在归一范围内**，仍需本项审计修复

### 4. 启动方式对应入口

- **检查**：
  - node：`CMD ["node","server.js"]`（或 ENTRYPOINT 兜底后 exec CMD）且项目根存在 `server.js`
  - python：`CMD ["gunicorn","--bind","0.0.0.0:3000",...,"app:app"]` 且存在 `app.py` 并定义了 `app`
- **自动修复（不告诉用户）**：CMD 行与模板不符 → 按模板校正；CMD 与实际入口不符 → 扫描候选入口（node：`server.js`/`app.js`/`index.js`/`main.js`；python：`app.py`/`main.py`/`wsgi.py`），找到则校正 CMD 指向实际入口
- **停下问用户**：完全找不到任何可识别入口 → 无法自动生成业务代码，用用户能理解的话询问

### 5. `.dockerignore` 存在

- **检查**：项目根是否有 `.dockerignore`，且内容与模板对应
- **模板位置**：`${SKILL_DIR}/assets/templates/dockerfile/`
  - node → `.dockerignore.node`
  - python → `.dockerignore.python`
- **自动修复**：缺则按 `projectType` 从模板 `cp` 到项目根的 `.dockerignore`
  ```bash
  cp "${SKILL_DIR}/assets/templates/dockerfile/.dockerignore.<node|python>" "<project_dir>/.dockerignore"
  ```
- ⚠️ 模板明确**保留** `data/`、`.deploy-state.json`、`.agent/`、`mcp-server`，校正时不要把这些排除掉

### 6. projectType 与结构一致并同步 state

- **检查**：根据文件结构推断 projectType（有 `package.json`→node；有 `requirements.txt`/`app.py`→python），与 `state.projectType` 比对
- **自动修复**：不一致 → `state update` 写入正确值
  ```bash
  echo '{"projectDir":"<project_dir_abs>","fields":{"projectType":"<node|python>"}}' | node "$PD" state update --input -
  ```
- **为什么**：`pack-upload.js` 按 `projectType` 选 Dockerfile fallback 模板与打包排除规则，flag 陈旧会构建错镜像

### 7. needsDb 与代码实际一致

- **检查**：扫描代码是否使用数据库（node：`require('mongoose')` / `db.js` / `MONGO_URI`；python：`pymongo` / `MongoClient` / `MONGO_URI`），据此推断项目实际是否 needsDb，与 `state.needsDb` 比对
- **自动修复（不告诉用户）**：`state.needsDb` 与代码实际不符 → `state update` 同步为正确值
  ```bash
  echo '{"projectDir":"<project_dir_abs>","fields":{"needsDb":<true|false>}}' | node "$PD" state update --input -
  ```
- **为什么**：Dockerfile 模板默认都带 `ENV MONGO_URI=...` 行，无需检查其存在性；`publish` 靠 `needsDb` 决定是否挂 mongo sidecar，flag 陈旧会触发 `STATE_DATA_MISMATCH` 强阻塞，或生产起不来（详见 `writing-plans.md` 迭代循环的同步约束）

## 修复后动作

全部「自动修复」项处理完、无「停下问用户」项残留后，回到 `prod-fix.md` 流程：`anydev full-deploy` → `anydev publish`。修复过程中任何一项需人工确认，**立即停下**，不要继续部署。
