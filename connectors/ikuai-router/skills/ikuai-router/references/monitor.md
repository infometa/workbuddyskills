---
name: ikuai-monitor
description: Monitor iKuai router — system status, CPU, memory, disk, temperature, online clients, interface traffic, wireless stats.
---

# Monitor

## Commands

All examples use `--format json` because this skill is primarily for agents and scripts. Use table output only for human inspection.

### System Overview
```bash
ikuai-cli monitor system --format json       # Uptime, load, firmware version, WAN IP
ikuai-cli monitor cpu --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor cpu --format json --time-range day --start-time 1773215100 --end-time 1773301500 --aggregate max
ikuai-cli monitor memory --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor disk --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor temp --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor connections --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor terminals --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor network-load --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
```

Load commands (cpu, memory, disk, temp, terminals, connections, network-load) support:
- `--time-range hour|day|week|month` — time range
- `--start-time <unix>` — start timestamp
- `--end-time <unix>` — end timestamp
- `--aggregate avg|max` — calculation method

### Traffic & Network
```bash
ikuai-cli monitor network-load --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor downstream --format json --page 1 --page-size 20 --device camera --status 1
ikuai-cli monitor interfaces --format json           # WAN interface status (IP, gateway)
ikuai-cli monitor interfaces-traffic --format json   # Per-interface Bytes/s
ikuai-cli monitor interfaces-config --format json    # Interface config detail
ikuai-cli monitor interfaces-physical --format json  # Physical NIC info
ikuai-cli monitor interfaces-traffic-v6 --format json # IPv6 traffic
ikuai-cli monitor flow-shunting --format json        # Traffic shunting data
ikuai-cli monitor switch --format json               # Switch port monitoring
```

### Clients
```bash
ikuai-cli monitor clients-online --format json --page 1 --page-size 100    # Online IPv4 clients
ikuai-cli monitor clients-offline --format json                             # Historical offline
ikuai-cli monitor clients-ip6-online --format json                          # Online IPv6 clients
ikuai-cli monitor clients-ip6-offline --format json                         # Historical offline IPv6
ikuai-cli monitor traffic-summary --format json                             # Per-client traffic summary
```

Per-client commands (require `--ip` and `--mac`):
```bash
ikuai-cli monitor traffic-load --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c
ikuai-cli monitor client-protocols --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --starttime 1773304236 --stoptime 1773304246
ikuai-cli monitor client-protocols-history --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --starttime 1773304236 --stoptime 1773304246
ikuai-cli monitor client-app-protocols --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --page-size 10
```

### Application & Protocol
```bash
ikuai-cli monitor protocols --format json            # Protocol distribution
ikuai-cli monitor protocols-history --format json    # Protocol history
ikuai-cli monitor app-traffic-summary --format json --page 1 --page-size 20  # App-layer traffic summary (24h)
ikuai-cli monitor app-protocols-load --format json --page 1 --page-size 20 --order desc --order-by total_down  # Current app protocol load
ikuai-cli monitor app-protocols-history --format json --appids 2580003,2580004 --starttime 1773215100 --stoptime 1773218700  # App protocol rate history
ikuai-cli monitor app-protocols-terminals --format json --appid 2580003         # Terminals using an app
```

### Wireless
```bash
ikuai-cli monitor wireless-stats --format json    # Wireless site statistics
ikuai-cli monitor wireless-score --format json    # Quality score
ikuai-cli monitor wireless-traffic --format json --apmac 00:00:00:00:00:00
ikuai-cli monitor ssid-clients --format json --ssid iKuai01_2G
ikuai-cli monitor channel-clients --format json --channel 6
ikuai-cli monitor cameras --format json --page 1 --page-size 20 --keyword Hikvision
```

## Common Workflows

### Health Check
```bash
ikuai-cli monitor system --format json
ikuai-cli monitor cpu --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor memory --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor disk --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
ikuai-cli monitor connections --format json --time-range hour --start-time 1773300000 --end-time 1773303600 --aggregate avg
```

### Traffic Investigation
```bash
# Step 1: Find top clients
ikuai-cli monitor clients-online --format json --page-size 200
# Step 2: Drill into a specific client
ikuai-cli monitor traffic-load --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c
ikuai-cli monitor client-protocols --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --starttime 1773304236 --stoptime 1773304246
ikuai-cli monitor client-protocols-history --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --starttime 1773304236 --stoptime 1773304246
ikuai-cli monitor client-app-protocols --format json --ip 192.168.1.100 --mac 08:9b:4b:01:7e:7c --page-size 10
# Step 3: Check app-level traffic
ikuai-cli monitor app-traffic-summary --format json --page 1 --page-size 20
ikuai-cli monitor app-protocols-terminals --format json --appid 2580003
```
