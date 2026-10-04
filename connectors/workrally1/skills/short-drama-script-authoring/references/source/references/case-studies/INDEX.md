# 案例库索引

头部 SKILL.md 步骤 2 通过本索引定位案例文件。每个题材对应一个 `{题材}-success.md`。

## 案例文件命名约定

```
{题材}-success.md      ← 成功案例库（爆款拉片）
{题材}-failure.md      ← 失败案例库（避坑，可选）
{题材}-trends.md       ← 市场趋势（动态更新，可选）
```

## 当前案例

| 案例文件 | 题材 | 状态 |
|---|---|---|
| `revenge-success.md` | 复仇/打脸 | 模板（公式已填，具体拉片待补） |

## 待补充案例（对应 12 题材）

国内 9 类：

- [ ] `counterattack-success.md` 都市逆袭
- [ ] `ceo-romance-success.md` 霸总甜宠
- [ ] `female-lead-success.md` 大女主
- [ ] `war-god-success.md` 战神归来
- [ ] `hidden-identity-success.md` 马甲隐藏
- [ ] `rebirth-success.md` 重生穿越
- [ ] `family-saga-success.md` 豪门认亲
- [ ] `ancient-fantasy-success.md` 古装玄幻

海外 3 类：

- [ ] `werewolf-success.md` 狼人吸血鬼（参考 海外）
- [ ] `contract-marriage-success.md` 先婚后爱
- [ ] `win-back-success.md` 追妻火葬场

## 单个案例文件标准结构

```
# 《作品名》拉片分析

## 基础信息
- 题材 / 市场 / 集数 / 平台
- 数据：播放量、完播率、付费率（若有）

## 一句话爆款逻辑

## 五元素分析
（按 frameworks/five-elements.md 模板）

## 节奏曲线
（标出每 5 集情绪值与压/放类型，付费点位置）

## 关键桥段拆解（5-10 个）
- 桥段：场景 / 戏剧功能 / 情绪类型 / 可复用要素

## 可复用模板
- 人物配置 / 关系结构 / 桥段模板

## 局限与不可复制点
```

## 扩展建议

- 每个题材至少 3 个爆款 + 1 个反面案例
- 案例库季度更新一次
- 完整剧本全文等大语料放 `assets/raw/`，不进上下文，用脚本检索
- 单个案例文件 < 8000 字，超过拆分（基础 + 桥段集 + 对白集）
