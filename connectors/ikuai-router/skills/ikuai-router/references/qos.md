---
name: ikuai-qos
description: iKuai QoS bandwidth control — IP-based and MAC-based bandwidth limiting rules.
---

# QoS

## IP 限速

```bash
ikuai-cli qos ip list --format json
ikuai-cli qos ip create --name "limit100" --ip-addr "192.168.9.0/24" --upload 1000 --download 1000 --interface wan1 --format json
ikuai-cli qos ip get <ID> --format json
ikuai-cli qos ip update <ID> --name "limit100u" --upload 1200 --download 1300 --comment "updated" --format json
ikuai-cli qos ip toggle <ID> --enabled no --format json
ikuai-cli qos ip delete <ID> --yes --format json
```

`--upload` 和 `--download` 使用 Kbps 数值；`--ip-addr` 支持逗号分隔多 IP。

## MAC 限速

```bash
ikuai-cli qos mac list --format json
ikuai-cli qos mac create --name "limitmac" --mac-addr "00:11:22:33:44:55" --upload 500 --download 500 --interface wan1 --format json
ikuai-cli qos mac get <ID> --format json
ikuai-cli qos mac update <ID> --name "limitmacu" --upload 800 --download 900 --comment "updated" --format json
ikuai-cli qos mac toggle <ID> --enabled no --format json
ikuai-cli qos mac delete <ID> --yes --format json
```

`--mac-addr` 支持逗号分隔多 MAC。
