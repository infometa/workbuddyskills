# TeachAny Packaging & Publishing（精简版）

## ⚠️ 发布路径选择（强制，任何发布前必读）

```
发布前先跑凭据检测 ──→ 有 SSH/GH_TOKEN ──→ auto-publish.sh（维护者直推）
                     └─→ 无凭据 ──→ publish_course.sh（Worker API，零配置）
```

**硬规则**：
- **先检测，再发布**。不要先 `git commit` 再发现推不上去。
- **无凭据环境（CI / agent / 远程服务器）只能用 `publish_course.sh`**。
- **批量升级 N 门课件后**：逐门跑 `publish_course.sh`，不要试图一次 `git push` 全部。
- 违反以上规则会导致：commit 卡在本地无法推送，课件永久丢失，无补救手段。

## 仓库说明

`weponusa/teachany` 是轻量主站与 Skill 仓库；真实课件统一放入 `weponusa/teachany-courseware`（本地路径：`~/CodeBuddy/一次函数/teachany-courseware`）。

- 课件目录：`community/<course-id>/index.html`、`manifest.json`、`PLAN.md`、`assets/`
- GitHub Pages 地址：`https://weponusa.github.io/teachany-courseware/community/<course-id>/`

## 发布前检查

```bash
node "$TEACHANY_SKILL/scripts/validate-courseware.cjs" "$COURSE_DIR"
```

## 发布路径（二选一）

### ① 普通用户 / 社区投稿（默认，零配置）

**不需要 GitHub 账号或 token**，走 Cloudflare Worker 自动 PR 流程：

```bash
# 单个课件
bash "$TEACHANY_SKILL/scripts/publish_course.sh" "$COURSE_DIR" <course-id>

# 批量发布
for id in <id1> <id2> <id3>; do
  bash "$TEACHANY_SKILL/scripts/publish_course.sh" "$REPO/community/$id" "$id"
done
```

课件提交到 `teachany-community.pages.dev`，Worker 验证后自动合并到仓库并部署。

> ⚠️ **在 CI / agent / 远程服务器等无 GitHub 凭据的环境中，必须且只能使用此路径。**
> 禁止在这类环境中使用 `auto-publish.sh`——它需要 SSH key 或 GH_TOKEN，缺失时 commit 卡在本地，课件永久丢失，没有任何补救手段。

### ② 仓库维护者直推（仅限本地 Mac，已配置 SSH）

需要 SSH 或 GH_TOKEN，一条命令完成注册 + 挂树 + 推送：

```bash
bash "$TEACHANY_SKILL/scripts/auto-publish.sh" <course-id>
```

等价手动步骤：
```bash
cd ~/CodeBuddy/一次函数/teachany-courseware
python3 scripts/rebuild-index.py
git add -A
git commit -m "feat: 新增课件 <course-id>"
git push origin main
```

GitHub Actions 自动部署，约 1-2 分钟后可访问：
`https://weponusa.github.io/teachany-courseware/community/<course-id>/`

## 凭据检测（在发布前运行）

```bash
# 检测当前环境是否有 GitHub push 权限
ssh -T git@github.com -o ConnectTimeout=5 2>&1 | grep -q "successfully" && echo "✅ SSH OK" || echo "❌ 无 SSH，请用 publish_course.sh"
```

若无 SSH 且无 GH_TOKEN → 只能用 `publish_course.sh`，不要尝试其他路径。

## Gitee 同步（可选，维护者）

```bash
GIT_SSH_COMMAND='ssh -p 22 -o BatchMode=yes -o ConnectTimeout=20' git push gitee main
```
