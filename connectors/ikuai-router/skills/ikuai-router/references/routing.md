---
name: ikuai-routing
description: iKuai routing — static routes, traffic shunting (domain, five-tuple, L7, load-balance, updown).
---

# Routing

## 静态路由

```bash
ikuai-cli routing static list --format json
ikuai-cli routing static get <ID> --format json
ikuai-cli routing static create --name "to_lan2" --dst-addr "10.10.10.0" --gateway "10.66.0.1" --netmask "255.255.255.0" --interface wan1 --format json
ikuai-cli routing static update <ID> --name "to_lan2_bak" --priority 10 --format json
ikuai-cli routing static toggle <ID> --enabled no --format json
ikuai-cli routing static delete <ID> --yes --format json
```

## 分流规则（stream）

5 种分流，统一 CRUD 模式：

### 域名分流
```bash
ikuai-cli routing stream domain list --format json
ikuai-cli routing stream domain get <ID> --format json
ikuai-cli routing stream domain create --name "baidu" --domain "www.baidu.com,baidu.com" --interface wan2 --format json
ikuai-cli routing stream domain update <ID> --name "baidu_wan1" --interface wan1 --format json
ikuai-cli routing stream domain toggle <ID> --enabled no --format json
ikuai-cli routing stream domain delete <ID> --yes --format json
```

### 五元组分流
```bash
ikuai-cli routing stream five-tuple list --format json
ikuai-cli routing stream five-tuple get <ID> --format json
ikuai-cli routing stream five-tuple create --name "web_wan2" --protocol tcp --dst-port "80,443" --interface wan2 --format json
ikuai-cli routing stream five-tuple update <ID> --dst-port "8080,8443" --format json
ikuai-cli routing stream five-tuple toggle <ID> --enabled no --format json
ikuai-cli routing stream five-tuple delete <ID> --yes --format json
```

### L7 协议分流
```bash
ikuai-cli routing stream l7 list --format json
ikuai-cli routing stream l7 get <ID> --format json
ikuai-cli routing stream l7 create --name "dns_wan2" --app-proto "DNS" --interface wan2 --format json
ikuai-cli routing stream l7 update <ID> --name "dns_wan1" --interface wan1 --format json
ikuai-cli routing stream l7 toggle <ID> --enabled no --format json
ikuai-cli routing stream l7 delete <ID> --yes --format json
```

### 负载均衡
```bash
ikuai-cli routing stream load-balance list --format json
ikuai-cli routing stream load-balance get <ID> --format json
ikuai-cli routing stream load-balance create --name "lb_wan1" --interface wan1 --mode 0 --weight 1 --isp-name all --format json
ikuai-cli routing stream load-balance update <ID> --weight 2 --format json
ikuai-cli routing stream load-balance toggle <ID> --enabled no --format json
ikuai-cli routing stream load-balance delete <ID> --yes --format json
```

### 上下行分离
```bash
ikuai-cli routing stream updown list --format json
ikuai-cli routing stream updown get <ID> --format json
ikuai-cli routing stream updown create --name "split" --upiface wan1 --downiface wan2 --format json
ikuai-cli routing stream updown update <ID> --protocol tcp --dst-port "80,443" --format json
ikuai-cli routing stream updown toggle <ID> --enabled no --format json
ikuai-cli routing stream updown delete <ID> --yes --format json
```

常用对象字段使用逗号分隔，例如 `--src-addr "192.168.1.10,192.168.1.11"`、`--dst-port "80,443"`、`--app-proto "DNS,HTTP"`。
