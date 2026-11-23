---
name: ikuai-objects
description: iKuai network objects — IP, IPv6, MAC, port, protocol, domain, time object groups for rule references.
---

# Objects

7 种对象组：ip, ip6, mac, port, proto, domain, time

每种支持 create/list/get/update/delete + refs 查询：

```bash
# List
ikuai-cli objects ip list --page 1 --page-size 20 --format json
ikuai-cli objects mac list --page 1 --page-size 20 --format json

# Create（--value 逗号分隔，自动转为 group_value 数组）
ikuai-cli objects ip create --name "servers" --value "192.168.1.10,192.168.1.11" --format json
ikuai-cli objects mac create --name "printers" --value "AA:BB:CC:DD:EE:FF" --format json
ikuai-cli objects port create --name "web_ports" --value "80,443,8080" --format json
ikuai-cli objects domain create --name "blocked" --value "ads.example.com,track.example.com" --format json
ikuai-cli objects time create --name "office" --type weekly --weekdays "12345" --start-time "09:00" --end-time "18:00" --format json

# Get
ikuai-cli objects ip get <ID> --format json

# Update
ikuai-cli objects ip update <ID> --name "servers_v2" --value "192.168.1.10,192.168.1.12" --format json
ikuai-cli objects time update <ID> --name "office_v2" --type weekly --weekdays "1234567" --start-time "08:30" --end-time "18:30" --format json

# Delete
ikuai-cli objects ip delete <ID> --yes --format json

# 查看引用该对象的规则
ikuai-cli objects ip refs --group-name "servers" --format json
```

List 仅支持 `--page/--page-size`；不支持 `--filter`、`--order`、`--order-by`。

复杂对象内容仍可用 `--data` 传完整 JSON body。
