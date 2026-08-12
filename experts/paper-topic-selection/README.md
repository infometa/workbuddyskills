# 选题顾问（WANFANG TOPIC）

基于万方数据学术资源的一站式论文选题顾问。

## 类型
Team 型（多角色协作团队）

## 功能
- 🔍 检索文献 / 找领域专家
- 💡 推荐 3-5 个选题方向
- 📊 评估选题新颖性与可行性
- ✏️ 生成论文标题
- 📈 生成领域发展报告
- 🔥 灵感 / 热点词推荐

## 头像
头像目录为 `avatars/`，可替换为 512×512 PNG/JPG（≤500KB）。

## 依赖配置（APP_KEY）

本专家团的 `bin/wanfang_topic_cli.py`、`bin/wanfang_api_validator.py` 调用万方选题 API 时，需要万方开放平台的 **AppKey**。

> ⚠️ 包内已内置万方 AppKey（主用 `108_9288c3c77544491b_3a14cd`），开箱即可调用 API，无需设置环境变量。若对外分发此包，密钥会随包暴露；如需重新外部化，可改回从环境变量 `${APP_KEY}` 读取。

### 1. 获取 AppKey
联系万方数据（WANFANG）开放平台 / 你的接口负责人申请 `X-Ca-AppKey`，获得主用密钥（与可选的备用密钥）。

### 2. 设置环境变量
- Linux / macOS（终端，临时）：
  ```bash
  export APP_KEY="你的真实AppKey"
  ```
- Windows（PowerShell，临时）：
  ```powershell
  $env:APP_KEY="你的真实AppKey"
  ```
- 持久化：将上述命令写入 shell 配置文件（如 `~/.bashrc`、`~/.zshrc`）或系统环境变量设置中。

### 3. 调用示例（bin/ 脚本）
```bash
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action find_all
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action read_paper --type HIGH
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action assess \
  --title "标题" --abstract "摘要"
```

> 注：执行上述脚本时 `python` 与 `python3` 二选一即可，两者等价（取决于你的环境将哪个命令指向 Python 3）。
```

### 4. 连通性验证
```bash
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action read_paper --type HIGH
```
返回含 `pageInfo` 的论文列表，即说明 `APP_KEY` 配置正确、网络可达。

