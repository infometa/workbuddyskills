---
name: ikuai-advanced
description: iKuai advanced services — FTP, HTTP, Samba file servers and SNMPD config.
---

# Advanced Services

## FTP

```bash
ikuai-cli advanced ftp config-get --format json
ikuai-cli advanced ftp config-set --open-ftp 1 --ftp-port 21 --ftp-access 1 --format json
ikuai-cli advanced ftp list --format json
ikuai-cli advanced ftp create --username "user1" --password "<example-password>" --permission rw --home-dir "/test-001" --format json
ikuai-cli advanced ftp update <ID> --permission ro --format json
ikuai-cli advanced ftp toggle <ID> --enabled no --format json
ikuai-cli advanced ftp delete <ID> --yes --format json
```

FTP/HTTP/Samba 用户 CRUD 需路由器挂载外接存储。

## HTTP

```bash
ikuai-cli advanced http list --format json
ikuai-cli advanced http create --name "www" --port 8080 --ssl 0 --autoindex 0 --download 0 --home-dir "/test-001" --format json
ikuai-cli advanced http update <ID> --download 1 --format json
ikuai-cli advanced http toggle <ID> --enabled no --format json
ikuai-cli advanced http delete <ID> --yes --format json
```

## Samba

```bash
ikuai-cli advanced samba config-get --format json
ikuai-cli advanced samba config-set --enabled yes --workgroup WORKGROUP --wsdd2 1 --access 1 --format json
ikuai-cli advanced samba list --format json
ikuai-cli advanced samba create --name "share1" --username "user1" --password "<example-password>" --permission rw --guest yes --home-dir "/test-001" --format json
ikuai-cli advanced samba update <ID> --permission ro --format json
ikuai-cli advanced samba toggle <ID> --enabled no --format json
ikuai-cli advanced samba delete <ID> --yes --format json
```

## SNMPD

```bash
ikuai-cli advanced snmpd get --format json
ikuai-cli advanced snmpd get --wide --format json
ikuai-cli advanced snmpd set --enabled yes --listen-port 161 --version 2 --community public --rw ro --format json
```
