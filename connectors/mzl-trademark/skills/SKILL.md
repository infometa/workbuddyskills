---
name: mzl-trademark-skill
description: 摩知轮商标查询技能 —— 按条件检索商标（文本）与以图搜图（图形近似），覆盖中国及 110+ 海外国家/地区
version: "1.0.0"
author: "摩知轮"
---

# 摩知轮商标查询 Skill

本 Skill 让 AI 通过 MCP 工具检索商标数据，覆盖**中国及 110+ 海外国家/地区商标局**。
提供两个工具：`trademark_search`（按条件文本检索）与 `trademark_image_search`（上传图样以图搜图）。

用户首次连接会跳转浏览器登录摩知轮账号完成授权（OAuth）。查询按类型消耗账号积分，仅**成功返回结果**才扣。

## 可用工具

### trademark_search — 商标信息查询

按商标名称 / 申请人 / 申请号 / 注册号 / 尼斯类别 / 法律状态 / 日期范围等条件检索，返回分页结果。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `country` | string[] | ✅ | 国家/地区商标局，决定检索范围，至少一个。**只查中国传 `["中国"]`**（结果不含任何海外记录）；查海外传目标国家可多选，如 `["美国","欧盟","日本"]`。用**中文国名**（与图形检索的两位代码不同口径）。不在可选值内的名称会被后端忽略，全被忽略时返回 `total=0` 而非报错 |
| `markname` | string | - | 商标名称（模糊） |
| `marknameKeyword` | string | - | 商标名称（精确匹配） |
| `companyname` | string | - | 申请人名称（中文）。检索海外时申请人多以英文登记，应改用 `companyenname` |
| `companyenname` | string | - | 申请人英文名称（检索海外国家时通常用本字段） |
| `agentname` | string | - | 代理机构 |
| `applynos` | string[] | - | 申请号列表 |
| `regNums` | string[] | - | 注册号列表 |
| `types` | number[] | - | 尼斯分类类别 1–45 |
| `lawstatusList` | string[] | - | 法律状态数组（如「已注册」「等待实质审查」「无效」） |
| `applyyear` | string | - | 申请年份 `yyyy` |
| `applyDateSpan` | string | - | 申请日期范围 `yyyy-MM-ddTOyyyy-MM-dd` |
| `dateRegistrationSpan` | string | - | 注册日期范围，格式同上 |
| `fuzzyContent` | string | - | 综合模糊搜索：商标名/申请号/注册号/申请人/代理机构 |
| `order` | string | - | 排序字段，缺省按 `id` |
| `pageNum` | number | - | 页码，从 1 开始，默认 1 |
| `pageSize` | number | - | 每页条数 1–100，默认 20 |

**使用要点**
- `country` **必须显式传**，AI 不要省略。用户说「查商标」但没说国家时，默认理解为只查中国，传 `["中国"]`。
- 检索范围完全由 `country` 决定，与账号权限/配额/计费无关。
- 检索海外时，申请人条件优先用 `companyenname`。

**使用示例**
- 「查茅台在第 33 类中国的注册情况」→ `{ "markname": "茅台", "country": ["中国"], "types": [33] }`
- 「星巴克在美国和欧盟的商标」→ `{ "markname": "星巴克", "country": ["美国","欧盟"] }`
- 「申请号 1643458 是谁的」→ `{ "applynos": ["1643458"], "country": ["中国"] }`

### trademark_image_search — 商标图形近似查询（以图搜图）

上传一张商标图样的 Base64，检索图形近似的商标，结果按相似度从高到低排列。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `base64` | string | ✅ | 商标图样的 Base64，可含或不含 `data:image/...;base64,` 前缀，图片越清晰命中越准 |
| `cs` | string[] | ✅ | 检索的国家/地区商标局，用**两位国家代码**，至少一个。**本接口不会在留空时默认中国**，不传会直接报错「国家查询条件不能为空！」，必须显式指定；只查中国传 `["CN"]`。可选值见下 |
| `types` | number[] | - | 尼斯分类类别 1–45，不传默认全类 |
| `marknameKeyword` | string | - | 商标名称精确匹配，用于在图形结果上过滤 |
| `applynos` | string[] | - | 申请号列表过滤 |
| `groups` | string[] | - | 类似群过滤 |
| `companyname` | string | - | 申请人名称过滤 |
| `agentname` | string | - | 代理机构过滤 |
| `lawstatusList` | string[] | - | 法律状态数组过滤 |
| `preliminarySpan` | string | - | 初审公告日期范围 `yyyy-MM-ddTOyyyy-MM-dd` |
| `applyDateSpan` | string | - | 申请日期范围，格式同上 |
| `registerdateSpan` | string | - | 注册公告日期范围，格式同上 |
| `order` | string | - | 排序字段，缺省按图形相似度降序（推荐留空） |
| `orderType` | number | - | 0=升序 1=降序（默认 1） |
| `pageNum` | number | - | 页码，从 1 开始，默认 1 |
| `pageSize` | number | - | 每页条数 1–100，默认 20 |

**`cs` 支持的国家/地区代码（两位码，范围比文本检索小）**

- 亚洲：`AE`(阿联酋) `CN`(中国) `HK`(中国香港) `ID`(印尼) `IN`(印度) `JP`(日本) `KR`(韩国) `MO`(中国澳门) `MY`(马来西亚) `PH`(菲律宾) `SG`(新加坡) `TR`(土耳其) `TH`(泰国) `TW`(中国台湾)
- 美洲：`AR`(阿根廷) `BR`(巴西) `CA`(加拿大) `CL`(智利) `MX`(墨西哥) `US`(美国)
- 欧洲：`AT`(奥地利) `BX`(比荷卢) `CH`(瑞士) `DE`(德国) `DK`(丹麦) `ES`(西班牙) `EU`(欧盟) `FI`(芬兰) `FR`(法国) `GB`(英国) `GR`(希腊) `HU`(匈牙利) `IE`(爱尔兰) `IS`(冰岛) `IT`(意大利) `NO`(挪威) `PT`(葡萄牙) `RU`(俄罗斯) `SE`(瑞典)
- 大洋洲：`AU`(澳大利亚) `NZ`(新西兰)
- 国际：`WO`(世界知识产权组织／马德里)

**使用要点**
- `cs` 用**两位代码**，不是中文国名；且**不会默认中国**，必须显式传。
- 图形检索支持的国家范围明显小于文本检索，只从上表选取。

**使用示例**
- 「用这张图找中国和马德里的近似商标」→ `{ "base64": "<Base64>", "cs": ["CN","WO"] }`
- 「这个 logo 在美国、欧盟有没有近似的」→ `{ "base64": "<Base64>", "cs": ["US","EU"] }`

## 返回结果

两个工具返回一致：`content` 是人类可读文本摘要，`structuredContent` 是结构化分页数据：

```jsonc
{
  "total": 672,      // 命中总条数
  "pageNum": 1,
  "pageSize": 20,
  "list": [
    {
      "markname": "茅台", "applyno": "1643458", "regnum": "",
      "companyname": "中国贵州茅台酒厂(集团)有限责任公司",
      "marktypenums": [33], "lawstatus": "已注册",
      "applydate": "1999-03-30", "dateRegistration": "2001-09-28",
      "imgpath": "https://.../xxxx.jpg", "countryName": "中国"
    }
  ]
}
```

## 计费与错误处理

- **积分计费**：按查询类型扣积分——国内文字 1 / 国际文字 2 / 国内图形 3 / 国际图形 5。**仅成功返回结果才扣**，失败/超时/无结果不扣。积分不足时调用失败并提示「积分不足」。
- **积分不足 / 配额不可用**：工具返回 `isError: true`，`content` 内为提示文本，向用户说明并建议补充积分后重试。
- **鉴权失败**：缺少或过期的授权 → HTTP 401，WorkBuddy 会引导用户重新授权。
- **图形检索较慢**：`trademark_image_search` 需调用外部图形引擎，单次可能耗时数十秒，属正常现象，请耐心等待，勿重复提交。
