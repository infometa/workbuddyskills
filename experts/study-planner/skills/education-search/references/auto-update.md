# 版本更新说明

## 自动更新机制

**触发时机**：每天第一次查询时自动检查版本

**当前版本**：1.0.8
**更新地址**：https://clawhub.ai/kayy123/education-search

---

## 执行指令

### 1. 版本检查（每天第一次查询时执行）

```bash
# 执行版本检查
bash ~/.openclaw/workspace/skills/education-search/scripts/auto_update.sh check
```

**返回值**：
- `UPDATE_AVAILABLE:1.0.5` - 有新版本可用
- `NO_UPDATE` - 已是最新版本

### 2. 自动更新（如果有新版本）

```bash
openclaw skills update education-search
```

### 3. 更新成功提示

```
✅ 已自动更新到最新版本 X.X.X
```

### 4. 手动更新命令

```bash
openclaw skills update education-search
```

---

## 自动更新流程

1. 每天第一次查询时，执行版本检查脚本
2. 如果检测到新版本，执行 `openclaw skills update education-search`
3. OpenClaw 自动下载并安装最新版本
4. 安装后立即生效，无需重启
5. 向用户显示更新成功提示

---

## 版本检查脚本

**位置**：`scripts/auto_update.sh`

**功能**：
- 检查最后检查日期（每天最多一次）
- 对比本地版本和远程版本
- 返回更新状态

**相关文件**：
- `.last_check_date` - 记录最后检查日期
- `.clawhubignore` - 忽略临时文件

---
