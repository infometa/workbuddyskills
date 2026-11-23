---
name: ikuai-system
description: iKuai system config — hostname, NTP, reboot schedules, remote access, VRRP, ALG, kernel, CPU freq, backup, upgrade, files, disks, and web admin accounts.
---

# System

## 基础配置

```bash
ikuai-cli system get --format json
ikuai-cli system set --hostname "my-router" --language 1 --time-zone 8 --format json
ikuai-cli system ntp-sync --format json
```

## 定时重启

```bash
ikuai-cli system schedules list --format json
ikuai-cli system schedules get <ID> --format json
ikuai-cli system schedules create --name "weekly_reboot" --strategy week --cycle-time "7" --time "03:00" --format json
ikuai-cli system schedules update <ID> --comment "updated" --format json
ikuai-cli system schedules toggle <ID> --enabled no --format json
ikuai-cli system schedules delete <ID> --yes --format json
```

## 远程访问

```bash
ikuai-cli system remote-access get --format json
ikuai-cli system remote-access set --ssh "1" --ssh-port 22 --wan-web "1" --http-port 80 --https-port 443 --format json
```

## VRRP（高可用）

```bash
ikuai-cli system vrrp get --format json
ikuai-cli system vrrp set --type "1" --priority "150" --gateway "192.168.1.1" --enabled yes --format json
ikuai-cli system vrrp start --format json
ikuai-cli system vrrp stop --format json
```

## ALG

```bash
ikuai-cli system alg get --format json
ikuai-cli system alg set --ftp "1" --sip "1" --tftp "1" --format json
```

## 内核参数

```bash
ikuai-cli system kernel get --format json
ikuai-cli system kernel set --bbr "1" --established-timeout "3600" --format json
```

## CPU 调频

```bash
ikuai-cli system cpufreq list --format json
ikuai-cli system cpufreq mode get --format json
ikuai-cli system cpufreq mode set --mode "performance" --turbo "1" --format json
```

## 磁盘和文件

```bash
ikuai-cli system disks list --format json
ikuai-cli system files list --path "/" --format json
```

## 系统备份

```bash
ikuai-cli system backup list --format json
ikuai-cli system backup create --format json
ikuai-cli system backup delete --srcfile "<backup-file>.bak" --yes --format json
ikuai-cli system backup restore --srcfile "<backup-file>.bak" --dry-run --format json
ikuai-cli system backup-auto get --format json
ikuai-cli system backup-auto set --enabled no --strategy week --time "23:59" --cycle-time "1234567" --valid-days 30 --format json
```

## 系统升级

```bash
ikuai-cli system upgrade check --format json
ikuai-cli system upgrade get --format json
ikuai-cli system upgrade status --format json
ikuai-cli system upgrade start --dry-run --format json
```

## Web 管理账号

```bash
ikuai-cli system web-admin groups list --format json
ikuai-cli system web-admin groups get <ID> --format json
ikuai-cli system web-admin groups create --name "readonly" --ip-addr "0.0.0.0/0" --perm-config "monitoring_center:r" --format json
ikuai-cli system web-admin groups update <ID> --name "readonly-updated" --format json
ikuai-cli system web-admin groups delete <ID> --yes --format json
ikuai-cli system web-admin accounts list --format json
ikuai-cli system web-admin accounts get <ID> --format json
ikuai-cli system web-admin accounts create --username "readonly" --passwd-md5 "<md5>" --group-id <GROUP_ID> --enabled no --format json
ikuai-cli system web-admin accounts update <ID> --comment "updated" --format json
ikuai-cli system web-admin accounts delete <ID> --yes --format json
ikuai-cli system web-admin password-status --username "admin" --format json
ikuai-cli system web-admin password set --passwd-md5 "<md5>" --dry-run --format json
```
