---
name: ikuai-security
description: iKuai security rules — ACL, MAC filtering, L7 app rules, URL filtering, domain blacklist, peerconn, terminals.
---

# Security

面向 Agent 的建议：

- 优先使用 `--format json`，便于解析 `rowid`、`data`、`total`。
- 删除命令使用 `--yes --format json`。

## ACL（访问控制）

```bash
ikuai-cli security acl list --format json
ikuai-cli security acl get <ID> --format json
ikuai-cli security acl create --name "block_ssh" --action drop --protocol tcp --direction forward --dst-port "22" --priority 30 --enabled no --format json
ikuai-cli security acl update <ID> --name "block_ssh_u" --action drop --protocol tcp --direction forward --dst-port "2222" --priority 31 --enabled no --format json
ikuai-cli security acl toggle <ID> --enabled yes --format json
ikuai-cli security acl delete <ID> --yes --format json
```

`--src-addr`, `--dst-addr`, `--src-port`, `--dst-port` 支持逗号分隔。`--priority` 建议使用 10-50 范围。

## MAC 过滤

```bash
ikuai-cli security mac get-mode --format json
ikuai-cli security mac set-mode --acl-mac 0 --dry-run --format json
ikuai-cli security mac set-mode --acl-mac 0 --format json
ikuai-cli security mac list --format json
ikuai-cli security mac get <ID> --format json
ikuai-cli security mac create --name "allow1" --mac "00:11:22:33:44:55" --enabled no --format json
ikuai-cli security mac update <ID> --name "allow1_u" --mac "00:11:22:33:44:55" --enabled no --format json
ikuai-cli security mac toggle <ID> --enabled yes --format json
ikuai-cli security mac delete <ID> --yes --format json
```

## L7 应用层规则

```bash
ikuai-cli security l7 list --format json
ikuai-cli security l7 get <ID> --format json
ikuai-cli security l7 create --name "block_app" --action drop --app-proto "抖音短视频" --priority 30 --enabled no --format json
ikuai-cli security l7 update <ID> --name "block_app_u" --action drop --app-proto "抖音短视频" --priority 31 --enabled no --format json
ikuai-cli security l7 toggle <ID> --enabled yes --format json
ikuai-cli security l7 delete <ID> --yes --format json
```

`--priority` 建议使用 10-50 范围。

## URL 过滤

```bash
# 黑名单
ikuai-cli security url black list --format json
ikuai-cli security url black get <ID> --format json
ikuai-cli security url black create --name "block_ads" --mode 0 --domain "ads.example.com" --enabled no --format json
ikuai-cli security url black update <ID> --name "block_ads_u" --mode 0 --domain "ads.example.com" --enabled no --format json
ikuai-cli security url black toggle <ID> --enabled yes --format json
ikuai-cli security url black delete <ID> --yes --format json

# 关键词
ikuai-cli security url keywords list --format json
ikuai-cli security url keywords create --name "kw1" --mode exact --src-url "example.com" --ori-keyword "bad" --rep-keyword "good" --hit-rate 1 --priority 10 --enabled no --format json
ikuai-cli security url keywords update <ID> --name "kw1_u" --mode exact --src-url "example.com" --ori-keyword "bad" --rep-keyword "better" --hit-rate 1 --priority 11 --enabled no --format json
ikuai-cli security url keywords toggle <ID> --enabled yes --format json
ikuai-cli security url keywords delete <ID> --yes --format json

# 重定向
ikuai-cli security url redirect list --format json
ikuai-cli security url redirect create --name "redir1" --mode exact --src-url "old.com" --dst-url "192.0.2.10" --hit-rate 1 --priority 30 --enabled no --format json
ikuai-cli security url redirect update <ID> --name "redir1_u" --mode exact --src-url "old.com" --dst-url "192.0.2.11" --hit-rate 1 --priority 31 --enabled no --format json
ikuai-cli security url redirect toggle <ID> --enabled yes --format json
ikuai-cli security url redirect delete <ID> --yes --format json

# 替换
ikuai-cli security url replace list --format json
ikuai-cli security url replace create --name "rep1" --mode exact --src-url "example.com" --param-keyword "track" --rep-keyword "clean" --hit-rate 1 --priority 30 --enabled no --format json
ikuai-cli security url replace update <ID> --name "rep1_u" --mode exact --src-url "example.com" --param-keyword "track" --rep-keyword "clean2" --hit-rate 1 --priority 31 --enabled no --format json
ikuai-cli security url replace toggle <ID> --enabled yes --format json
ikuai-cli security url replace delete <ID> --yes --format json
```

`url black --mode` 使用 `0/1`；`url keywords/redirect/replace --mode` 使用 `exact/vague`。`url keywords --priority` 建议 1-32；`url redirect/replace --priority` 建议 1-63。

## 域名黑名单

```bash
ikuai-cli security domain-blacklist list --format json
ikuai-cli security domain-blacklist get <ID> --format json
ikuai-cli security domain-blacklist create --name "blocked" --domain-group "evil_group" --enabled no --format json
ikuai-cli security domain-blacklist update <ID> --name "blocked_u" --domain-group "evil_group" --enabled no --format json
ikuai-cli security domain-blacklist toggle <ID> --enabled yes --format json
ikuai-cli security domain-blacklist delete <ID> --yes --format json
```

## 连接数限制（Peerconn）

```bash
ikuai-cli security peerconn list --format json
ikuai-cli security peerconn get <ID> --format json
ikuai-cli security peerconn create --name "limit1" --limits 500 --protocol tcp --src-addr "192.168.9.0/24" --dst-port "65000" --enabled no --format json
ikuai-cli security peerconn update <ID> --name "limit1_u" --limits 501 --protocol tcp --src-addr "192.168.9.0/24" --dst-port "65001" --enabled no --format json
ikuai-cli security peerconn toggle <ID> --enabled yes --format json
ikuai-cli security peerconn delete <ID> --yes --format json
```

## 终端标注（Terminals）

```bash
ikuai-cli security terminals list --format json
ikuai-cli security terminals get <ID> --format json
ikuai-cli security terminals create --name "printer" --mac "AA:BB:CC:DD:EE:FF" --format json
ikuai-cli security terminals update <ID> --name "printer_u" --mac "AA:BB:CC:DD:EE:FF" --format json
ikuai-cli security terminals delete <ID> --yes --format json
```

`terminals` 没有 `toggle` 命令。

## 高级安全配置

```bash
ikuai-cli security advanced-get --format json
ikuai-cli security advanced-set --noping-lan 1 --dry-run --format json
ikuai-cli security advanced-set --noping-lan 1 --format json
ikuai-cli security advanced-set --noping-lan 0 --format json

ikuai-cli security secondary-route-get --format json
ikuai-cli security secondary-route-set --ttl-num 21 --dry-run --format json
ikuai-cli security secondary-route-set --ttl-num 21 --format json
ikuai-cli security secondary-route-set --ttl-num 20 --format json
```

`advanced-set` 和 `secondary-route-set` 支持使用 flags 覆盖指定字段。
