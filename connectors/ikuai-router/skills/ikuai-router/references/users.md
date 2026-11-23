---
name: ikuai-users
description: iKuai user management — auth accounts CRUD, online sessions, kick, auth packages CRUD.
---

# Users

## 在线用户

```bash
ikuai-cli users online --format json
ikuai-cli users online get <ID> --format json
ikuai-cli users kick <ID> --yes --format json
```

## 认证账号

```bash
ikuai-cli users accounts list --format json
ikuai-cli users accounts get <ID> --format json
ikuai-cli users accounts create --username "guest1" --password "<example-password>" --format json
ikuai-cli users accounts update <ID> --comment "updated" --format json
# defaults: ppptype=any, upload=0, download=0, share=1, expires=0
ikuai-cli users accounts delete <ID> --yes --format json
```

常用 flags：`--enabled`, `--ppptype`, `--packages`, `--upload`, `--download`, `--start-time`, `--expires`, `--share`, `--ip-type`, `--auto-mac`, `--auto-vlanid`, `--bind-vlanid`, `--bind-ifname`, `--comment`

## 套餐管理

```bash
ikuai-cli users packages list --format json
ikuai-cli users packages get <ID> --format json
ikuai-cli users packages create --name "month-card" --time "1m" --price 100 --up-speed 500 --down-speed 1000 --format json
ikuai-cli users packages update <ID> --price 120 --format json
ikuai-cli users packages delete <ID> --yes --format json
```

`--time` 格式：`30d`(天), `1m`(月), `24h`(小时)
