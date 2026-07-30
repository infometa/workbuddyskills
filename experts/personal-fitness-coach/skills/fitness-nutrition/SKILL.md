---
name: fitness-nutrition
description: >
  健身动作库与营养查询。通过 wger API 搜索 690+ 动作（按肌群/器械/名称），
  通过 USDA FoodData Central 查询 38万+ 食物营养数据。
  离线计算器：BMI、TDEE、1RM、宏量分配、体脂率。纯 Python，无 pip 依赖。
platforms: [linux, macos, windows]
version: 1.0.0
authors:
  - haileymarshall (original)
license: MIT
---

# Fitness & Nutrition

健身动作库 + 营养查询 + 身体计算器，训练计划所需数据全部在这里。

## When to Use

触发此 skill 当用户：
- 制定训练计划（需要查动作）
- 问动作怎么做（需要动作详情）
- 问饮食/营养（需要食物数据或宏量计算）
- 需要计算 BMI / TDEE / 1RM / 体脂率 / 宏量分配

## Procedure

### 动作查询（wger API）

wger 公开端点无需认证。始终加 `language=2&status=2` 获取已审核英文动作。

**按名称搜索：**

```bash
QUERY="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
curl -s "https://wger.de/api/v2/exercise/search/?term=${ENCODED}&language=english&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
for s in data.get('suggestions',[])[:10]:
    d=s.get('data',{})
    print(f'  ID {d.get(\"id\",\"?\"):>4} | {d.get(\"name\",\"N/A\"):<35} | Category: {d.get(\"category\",\"N/A\")}')
"
```

**获取动作详情：**

```bash
EXERCISE_ID="$1"
curl -s "https://wger.de/api/v2/exerciseinfo/${EXERCISE_ID}/?format=json" \
  | python3 -c "
import json,sys,html,re
data=json.load(sys.stdin)
trans=[t for t in data.get('translations',[]) if t.get('language')==2]
t=trans[0] if trans else data.get('translations',[{}])[0]
desc=re.sub('<[^>]+>','',html.unescape(t.get('description','N/A')))
print(f'Exercise  : {t.get(\"name\",\"N/A\")}')
print(f'Category  : {data.get(\"category\",{}).get(\"name\",\"N/A\")}')
print(f'Primary   : {\", \".join(m.get(\"name_en\",\"\") for m in data.get(\"muscles\",[])) or \"N/A\"}')
print(f'Secondary : {\", \".join(m.get(\"name_en\",\"\") for m in data.get(\"muscles_secondary\",[])) or \"none\"}')
print(f'Equipment : {\", \".join(e.get(\"name\",\"\") for e in data.get(\"equipment\",[])) or \"bodyweight\"}')
print(f'How to    : {desc[:500]}')
imgs=data.get('images',[])
if imgs: print(f'Image     : {imgs[0].get(\"image\",\"\")}')
"
```

**按肌群/器械筛选：**

```bash
FILTER="$1"  # e.g. "muscles=4" or "category=11" or "equipment=3"
curl -s "https://wger.de/api/v2/exercise/?${FILTER}&language=2&status=2&limit=20&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
print(f'Found {data.get(\"count\",0)} exercises.')
for ex in data.get('results',[]):
    print(f'  ID {ex[\"id\"]:>4} | muscles: {ex.get(\"muscles\",[])} | equipment: {ex.get(\"equipment\",[])}')
"
```

### 营养查询（USDA FoodData Central）

使用 `USDA_API_KEY` 环境变量，未设置则回退到 `DEMO_KEY`。
DEMO_KEY = 30次/小时，免费注册 = 1000次/小时。

```bash
# 搜索单种食物
python3 scripts/nutrition_search.py "chicken breast"

# 搜索多种食物
python3 scripts/nutrition_search.py "rice" "eggs" "broccoli"
```

### 身体计算（离线）

```bash
python3 scripts/body_calc.py bmi <体重kg> <身高cm>
python3 scripts/body_calc.py tdee <体重kg> <身高cm> <年龄> <M|F> <活动量1-5>
python3 scripts/body_calc.py 1rm <重量> <次数>
python3 scripts/body_calc.py macros <TDEE> <cut|maintain|bulk>
python3 scripts/body_calc.py bodyfat <M|F> <颈围cm> <腰围cm> [臀围cm] <身高cm>
```

公式出处见 `references/FORMULAS.md`。

## 中文适配规则

wger 和 USDA 返回的数据都是英文，必须：

1. **动作名**：保留英文原名 + 附带中文常用名（如 Bench Press/卧推）
2. **动作描述**：翻译为中文后输出，不直接给用户看英文原文
3. **食物名**：翻译为中文（如 chicken breast → 鸡胸肉）
4. **肌群名**：用中文（如 Pectoralis major → 胸大肌）

## Pitfalls

- wger 默认返回所有语言 → 必须加 `language=2` 筛英文
- wger 包含未审核用户提交 → 必须加 `status=2` 只取已审核
- USDA `DEMO_KEY` 30次/小时 → 批量查询加 `sleep 2` 或注册免费 Key
- USDA 数据是每 100g → 提醒用户按实际份量换算
- BMI 不区分肌肉和脂肪 → 肌肉型用户高 BMI 不是问题
- 体脂率公式误差 ±3-5% → 建议DEXA扫描获取精确值
- 1RM 公式在 >10 次时准确度下降 → 用 3-5 次的数据估算最准
- wger 的搜索端点用 `term` 不是 `query`
