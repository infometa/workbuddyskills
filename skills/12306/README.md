# 12306 火车票查询

[OpenClaw](https://github.com/openclaw/openclaw) Skill — 查询中国铁路 12306 列车时刻表和余票信息。

## 安装

```bash
npx skills add kirorab/12306-skill
```

## 功能

- 查询任意两站间的列车时刻表和余票
- 输出为 HTML 页面（Apple 风格）或 Markdown 表格
- 丰富的筛选条件：车次类型、出发/到达时间、耗时、可购票状态、座位类型
- 站点数据使用 12306 官方数据源，自动缓存 7 天
- 支持城市名（自动解析到主站）或精确站名

## 依赖

- Node.js >= 18

## 用法

```bash
# 查询北京到上海的所有列车（默认今天）
node scripts/query.mjs 北京 上海

# Markdown 表格输出（适合终端/聊天）
node scripts/query.mjs 北京 上海 -t G -f md

# 上午出发的高铁，1小时内，二等座有票
node scripts/query.mjs 上海 杭州 -t G --depart 06:00-12:00 --max-duration 1h --seat ze

# 仅可购票，18点前到达
node scripts/query.mjs 深圳 长沙 --available --arrive -18:00

# JSON 输出
node scripts/query.mjs 广州 武汉 --json
```

## 参数

| 参数 | 说明 |
|------|------|
| `-d, --date <YYYY-MM-DD>` | 出行日期（默认今天） |
| `-t, --type <G\|D\|Z\|T\|K>` | 车次类型筛选，可组合（如 `GD`） |
| `--depart <HH:MM-HH:MM>` | 出发时间范围 |
| `--arrive <HH:MM-HH:MM>` | 到达时间范围 |
| `--max-duration <duration>` | 最长耗时（如 `2h`、`90m`、`1h30m`） |
| `--available` | 仅显示可购票车次 |
| `--seat <types>` | 按座位类型有票筛选（`swz,zy,ze,rw,dw,yw,yz,wz`） |
| `-f, --format <html\|md>` | 输出格式：`html`（默认，保存文件）或 `md`（Markdown 表格） |
| `-o, --output <path>` | 输出文件路径（仅 html 模式） |
| `--json` | JSON 输出 |

## 座位类型

| 缩写 | 含义 |
|------|------|
| swz | 商务座/特等座 |
| zy | 一等座 |
| ze | 二等座 |
| rw/dw | 软卧/动卧 |
| yw | 硬卧 |
| yz | 硬座 |
| wz | 无座 |

## 站点查询

```bash
node scripts/stations.mjs 杭州
node scripts/stations.mjs 香港西九龙
```

## 数据来源

直接调用 12306 官方 API，无需任何 API Key。
