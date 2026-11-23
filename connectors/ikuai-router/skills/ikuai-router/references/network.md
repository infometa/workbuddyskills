---
name: ikuai-network
description: iKuai network config — DNS, DHCP, VLAN, NAT/DNAT, WAN, LAN, PPPoE, DMZ, DNS proxy.
---

# Network

## DNS

```bash
ikuai-cli network dns get --format json
ikuai-cli network dns set --dns1 223.5.5.5 --dns2 119.29.29.29 --format json
ikuai-cli network dns stats --format json

# DNS 代理
ikuai-cli network dns proxy list --format json
ikuai-cli network dns proxy create --domain "example.com" --dns-addr "8.8.8.8" --parse-type ipv4 --comment "office dns" --format json
ikuai-cli network dns proxy update <ID> --domain "example.com" --dns-addr "1.1.1.1" --parse-type ipv4 --enabled yes --format json
ikuai-cli network dns proxy delete <ID> --yes --format json
```

## DHCP

```bash
ikuai-cli network dhcp list --format json
ikuai-cli network dhcp get <ID> --format json
ikuai-cli network dhcp create --name "Office" --interface lan1 --phy-ifnames "all" --addr-pool "192.168.1.100-192.168.1.200" --gateway "192.168.1.1" --netmask "255.255.255.0" --lease 120 --dns1 "223.5.5.5" --format json
ikuai-cli network dhcp update <ID> --dns1 "8.8.8.8" --format json
ikuai-cli network dhcp toggle <ID> --enabled no --format json
ikuai-cli network dhcp delete <ID> --yes --format json
ikuai-cli network dhcp clients --format json
ikuai-cli network dhcp restart --format json
ikuai-cli network dhcp start --format json
ikuai-cli network dhcp stop --format json

# 静态绑定
ikuai-cli network dhcp static list --page 1 --page-size 50 --format json
ikuai-cli network dhcp static create --name "Printer" --ip "192.168.1.50" --mac "AA:BB:CC:DD:EE:FF" --interface lan1 --gateway "192.168.1.1" --format json
ikuai-cli network dhcp static update <ID> --dns1 "223.5.5.5" --comment "printer" --format json
ikuai-cli network dhcp static toggle <ID> --enabled no --format json
ikuai-cli network dhcp static delete <ID> --yes --format json

# 接入控制
ikuai-cli network dhcp access-mode get --format json
ikuai-cli network dhcp access-mode set --mode 0 --format json
ikuai-cli network dhcp access-rule list --format json
ikuai-cli network dhcp access-rule create --name "allow-printer" --mac "AA:BB:CC:DD:EE:FF" --comment "printer" --format json
ikuai-cli network dhcp access-rule delete <ID> --yes --format json

# DHCPv6
ikuai-cli network dhcp6 clients --format json
ikuai-cli network dhcp6 access-mode get --format json
ikuai-cli network dhcp6 access-mode set --mode 0 --format json
ikuai-cli network dhcp6 access-rule list --format json
ikuai-cli network dhcp6 access-rule create --name "allow-v6" --mac "AA:BB:CC:DD:EE:FF" --enabled yes --format json
ikuai-cli network dhcp6 access-rule update <ID> --name "allow-v6-new" --mac "AA:BB:CC:DD:EE:FF" --enabled yes --format json
ikuai-cli network dhcp6 access-rule toggle <ID> --enabled no --format json
ikuai-cli network dhcp6 access-rule delete <ID> --yes --format json
```

## WAN / LAN / 接口

```bash
ikuai-cli network wan list --format json
ikuai-cli network wan-vlan list --format json
ikuai-cli network lan list --format json
ikuai-cli network physical list --format json
```

## VLAN

```bash
ikuai-cli network vlan list --key vlan_name --pattern IoT --filter 'enabled==yes' --format json
ikuai-cli network vlan create --name "IoT" --vlan-id 100 --interface lan1 --ip "10.0.100.1" --netmask "255.255.255.0" --format json
ikuai-cli network vlan update <ID> --comment "iot vlan" --format json
ikuai-cli network vlan toggle <ID> --enabled no --format json
ikuai-cli network vlan delete <ID> --yes --format json
```

## NAT / DNAT / DMZ

```bash
ikuai-cli network nat list --format json
ikuai-cli network nat create --name "allow_office" --action filter --in-interface any --out-interface any --src-addr "192.168.1.0/24" --protocol any --format json
ikuai-cli network nat update <ID> --comment "office nat" --format json
ikuai-cli network nat toggle <ID> --enabled no --format json
ikuai-cli network nat delete <ID> --yes --format json

ikuai-cli network dnat list --format json
ikuai-cli network dnat create --name "web_forward" --lan-addr "192.168.1.10" --lan-port 80 --wan-port 8080 --protocol tcp --interface all --format json
ikuai-cli network dnat update <ID> --comment "web forward" --format json
ikuai-cli network dnat toggle <ID> --enabled no --format json
ikuai-cli network dnat delete <ID> --yes --format json

ikuai-cli network dmz list --format json
ikuai-cli network dmz create --name "safe_dmz_test" --interface "203.0.113.254" --lan-addr "192.168.1.250" --protocol tcp --excl-port "80,443,18440" --enabled no --format json
ikuai-cli network dmz update <ID> --name "safe_dmz_test" --interface "203.0.113.254" --lan-addr "192.168.1.250" --protocol tcp --excl-port "80,443,18440" --enabled no --format json
ikuai-cli network dmz toggle <ID> --enabled no --format json
ikuai-cli network dmz delete <ID> --yes --format json
```

## PPPoE

```bash
ikuai-cli network pppoe get --format json
ikuai-cli network pppoe set --comment "maintenance" --mtu 1480 --mru 1480 --lcp-echo-interval 10 --lcp-echo-failure 3 --maxconnect 0 --format json
```
