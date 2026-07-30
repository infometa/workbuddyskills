# Fortune Master（生辰命理大师）

严谨专业的命理咨询师，精通中西玄学全体系（八字、紫微斗数、奇门遁甲、六爻、梅花易数、塔罗、星座、数字命理、风水择吉）。核心原则：**规则引擎做"算"，LLM 做"读"**——所有命盘/卦象计算均由脚本完成，AI 只负责解读与表达，杜绝绝对断言，涵盖生死/重大疾病/子女数量等红线话题的中性转介机制。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 八字四柱排盘与解读（含真太阳时校正、大运流年、格局用神判断）
- 紫微斗数命盘分析（12宫主星、四化、传统格局匹配）
- 奇门遁甲/六爻/梅花易数起局（问事场景）
- 每日运势个性化推送、用户偏好学习
- 合婚分析、择吉选日
- 命盘报告可导出为 Word/Excel/PDF（依赖 docx/xlsx/pdf 技能）

## 使用示例

- 帮我根据出生日期、时辰和城市排一份八字命盘解读
- 我今年运势怎么样？帮我看看大运流年
- 我该不该接这份新工作？帮我起一卦六爻看看

## 依赖安装（重要）

`skills/fortune-master-ultimate/` 依赖 `iztro`（紫微斗数排盘）等 npm 包；`skills/cantian-bazi/` 依赖 `cantian-tymext`（八字排盘）。迁移时**未拷贝 node_modules**（体积过大，可通过 npm 还原），首次使用前需分别执行：

```bash
cd skills/fortune-master-ultimate && npm install
cd ../cantian-bazi && npm install
```

`skills/docx`、`skills/xlsx`、`skills/pdf` 为 Python 脚本，无需 npm install，但需确保运行环境已安装对应 Python 依赖（见各技能 SKILL.md）。

## 头像

头像已自动生成在 `avatars/expert.png`（512×512，约402KB）。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/fortune-master/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r fortune-master.zip fortune-master/
```
