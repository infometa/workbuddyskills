---
name: ikuai-log
description: iKuai system logs — view and clear log records (system, arp, auth, dhcp, pppoe, web, ddns, notice, wireless, url-visits).
---

# Log

日志命令，每种有 list + delete：

```bash
# 查看
ikuai-cli log system list --format json
ikuai-cli log arp list --format json
ikuai-cli log auth list --format json
ikuai-cli log dhcp list --format json
ikuai-cli log pppoe list --format json
ikuai-cli log web list --format json
ikuai-cli log ddns list --format json
ikuai-cli log notice list --format json
ikuai-cli log wireless list --format json
ikuai-cli log url-visits list --format json --page 1 --page-size 20
ikuai-cli log url-visits list --format json --pattern example.com --starttime 1761842000 --stoptime 1761843000

# 清除（破坏性操作）
ikuai-cli log system delete --yes --format json
ikuai-cli log dhcp delete --yes --format json
ikuai-cli log url-visits delete --yes --format json
# ... 同理其他 <type> delete
```
