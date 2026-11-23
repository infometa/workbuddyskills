---
name: ikuai-batch
description: Batch iKuai operations — router initialization, bulk DHCP bindings, config export, multi-step workflows.
---

# Batch Operations

Multi-command workflows using `--format json` output and shell scripting.

## Router Initialization

```bash
#!/bin/bash
set -e

ROUTER="https://192.168.1.1"
TOKEN="<your-token>"

# 1. Auth
ikuai-cli auth set-url "$ROUTER"
ikuai-cli auth set-token "$TOKEN"
ikuai-cli auth status --format json

# 2. Set hostname
ikuai-cli system set --hostname "office-gw"

# 3. Configure DNS
ikuai-cli network dns set --dns1 223.5.5.5 --dns2 119.29.29.29

# 4. Verify
ikuai-cli system get --format json
ikuai-cli network dns get --format json
```

## Bulk DHCP Static Bindings

```bash
#!/bin/bash
# Read CSV: ip,mac,comment
while IFS=',' read -r ip mac comment; do
  ikuai-cli network dhcp static create \
    --name "$comment" --ip "$ip" --mac "$mac"
  echo "Bound $ip -> $mac"
done < bindings.csv
```

## Config Snapshot (Export)

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
DIR="backup-$DATE"
mkdir -p "$DIR"

ikuai-cli system get --format json              > "$DIR/system.json"
ikuai-cli network dns get --format json         > "$DIR/dns.json"
ikuai-cli network dhcp list --format json       > "$DIR/dhcp.json"
ikuai-cli network dhcp static list --format json > "$DIR/dhcp-static.json"
ikuai-cli network nat list --format json        > "$DIR/nat.json"
ikuai-cli network vlan list --format json       > "$DIR/vlan.json"
ikuai-cli security acl list --format json       > "$DIR/acl.json"
ikuai-cli vpn wireguard list --format json      > "$DIR/wireguard.json"
ikuai-cli system schedules list --format json   > "$DIR/schedules.json"

echo "Snapshot saved to $DIR/"
```

## Health Check Script

```bash
#!/bin/bash
echo "=== System ==="
ikuai-cli monitor system --format json | jq '{cpu,mem_used,mem_total,uptime}'

echo "=== Interfaces ==="
ikuai-cli monitor interfaces --format json | jq '.'

echo "=== Online Clients ==="
ikuai-cli monitor clients-online --format json | jq 'length'

echo "=== Connections ==="
ikuai-cli monitor connections --format json | jq '.'
```
