---
name: ikuai-wireless
description: iKuai wireless — blacklist/whitelist rules, VLAN rules, AC management.
---

# Wireless

## 黑白名单

```bash
ikuai-cli wireless blacklist list --format json
ikuai-cli wireless blacklist get <ID> --format json
ikuai-cli wireless blacklist create --name "block1" --mac "00:11:22:33:44:55" --format json
ikuai-cli wireless blacklist update <ID> --comment "updated" --format json
ikuai-cli wireless blacklist toggle <ID> --enabled no --format json
ikuai-cli wireless blacklist delete <ID> --yes --format json
```

## 无线 VLAN

```bash
ikuai-cli wireless vlan list --format json
ikuai-cli wireless vlan get <ID> --format json
ikuai-cli wireless vlan create --name "iot_vlan" --vlan-id 100 --mac "00:11:22:33:44:55" --format json
ikuai-cli wireless vlan update <ID> --comment "updated" --format json
ikuai-cli wireless vlan toggle <ID> --enabled no --format json
ikuai-cli wireless vlan delete <ID> --yes --format json
```

## AC 管理

```bash
ikuai-cli wireless ac get --format json
ikuai-cli wireless ac start --format json
ikuai-cli wireless ac stop --format json
ikuai-cli wireless ac ap-list --format json
ikuai-cli wireless ac ap-get <ID> --format json
ikuai-cli wireless ac ap-update <ID> --ssid1 "NewSSID" --enc1 wpa2 --key1 "<example-wifi-key>" --format json
```
