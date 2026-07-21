# COS 存储桶总览

## 访问规则（强制）

| 桶 | 角色 | 读 | 写 |
|----|------|:--:|:--:|
| **brazil-financeandtaxation** | 🟢 巴西主语料库 | ✅ 默认 | ✅ 默认 |
| **brazil-businessdevelopment** | 🔵 仅 CNPJ 提取 | ✅ CNPJ时 | ❌ 禁止 |
| **uae-marketing** | 🟡 UAE 营销 | ✅ 交叉引用 | — |
| **uae-strategicadvisory** | 🟡 UAE 战略 | ✅ 交叉引用 | — |

核心原则：
1. 巴西语料读/写 → 一律走 brazil-financeandtaxation，不走错桶
2. CNPJ 查询 → 走 brazil-businessdevelopment
3. 上传语料 → 只传到 brazil-financeandtaxation
4. 访问任何桶前 → 先 list_objects 扫描，即使看起来无关也要扫

## 桶详情

| 存储桶 | 用途 | 文件数 | 大小 |
|--------|------|:---:|:---:|
| brazil-businessdevelopment-1448789884 | 巴西 CNPJ 企业登记数据 | 11 | 13.45 GB |
| brazil-financeandtaxation-1448789884 | 🟢 巴西财税语料全库（主桶） | 503 | 3.12 GB |
| uae-marketing-1448789884 | 阿联酋营销全栈 | 157 | 104.6 MB |
| uae-strategicadvisory-1448789884 | 阿联酋战略顾问 | 253 | 200.7 MB |

所有桶均为 public-read，读取无需凭据。写入需各自环境自行配置 COS 凭据。
