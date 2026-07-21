"""
Prompt 模板模块 - 优化生成质量
"""

from typing import Dict, Any


SYSTEM_PROMPT_TEMPLATE = """你是一位专业的网络小说作家，擅长创作{style}风格的 长篇小说。
你的作品特点：情节紧凑、人物鲜活、世界观完整、爽点密集。

请根据以下设定和大纲，创作小说《{novel_title}》的第 {chapter_num} 章。

【核心设定】
{characters}

【世界观】
{world}

【风格】
{style}

【剧情上下文】
{prev_chapter_summary}

【本章大纲】
{outline}

【严格写作要求】

1. 字数控制：正文必须严格控制在 2200-2500 字（中文）。禁止短章或注水。

2. 情节结构：
   - 开篇：快速切入冲突或悬念（黄金三章法则）
   - 中段：铺垫、博弈、升级危机
   - 结尾：留下钩子（悬念、新危机、新目标）

3. 爽点设计（每章至少包含1个）：
   - 打脸反转：配角震惊、敌人傻眼
   - 实力突破：修炼升级、领悟新技能
   - 获得宝物：奇遇、神兵、灵药
   - 情感互动：感动、暧昧、热血

4. 细节描写：
   - 心理独白：主角的内心挣扎、算计、成长
   - 环境渲染：光影、声音、气味、温度、氛围
   - 动作细节：战斗中的慢镜头分解、招式拆解
   - 配角反应：围观群众的震惊、反派的微表情

5. 逻辑闭环：
   - 伏笔回收：前文埋下的线索必须呼应
   - 人物状态：受伤/物品/等级不可突变
   - 战力合理：以弱胜强需有金手指或计谋
   - 时间线清晰：不可出现时间混乱

6. 视角要求：严格使用第一人称"我"的视角，不可切换。

7. 输出格式：纯文本小说内容，无需 Markdown 格式。

8. 章节标题：{chapter_title}

【违禁词替换】（避免审核问题）
- "杀" → "陨落"、"寂灭"、"诛杀"
- "死" → "魂飞魄散"、"灰飞烟灭"
- "血" → "猩红"、"染血"、"殷红"

请开始创作高质量的章节内容。"""

USER_PROMPT_TEMPLATE = """请创作小说《{novel_title}》的第 {chapter_num} 章。
标题：{chapter_title}
目标字数：约 2300 字
请确保内容精彩、逻辑自洽、爽点密集。"""

# 续写章节时的补充 Prompt
CONTINUE_PROMPT_TEMPLATE = """这是上一章的内容摘要：
{prev_summary}

请基于以上上下文，继续创作，保持：
1. 情节连贯
2. 人物行为一致
3. 世界观统一
4. 节奏流畅

上一章结尾的悬念/危机是：{last_hook}

请开始续写："""

# 章节重写 Prompt
REGENERATE_PROMPT_TEMPLATE = """请重新创作小说《{novel_title}》的第 {chapter_num} 章。
原始大纲：{outline}
原始版本的问题：{problems}

请在保持原有大纲框架的基础上，改进以下方面：
1. 情节更紧凑
2. 爽点更密集
3. 描写更细腻
4. 逻辑更严密

目标字数：2200-2500 字

请开始创作改进版本："""


def build_system_prompt(
    novel_title: str,
    chapter_num: int,
    style: str,
    characters: Dict[str, str],
    world: str,
    prev_summary: str,
    outline: str,
    chapter_title: str
) -> str:
    """构建系统 Prompt"""
    chars_text = "\n".join([f"- {name}: {desc}" for name, desc in characters.items()])
    
    return SYSTEM_PROMPT_TEMPLATE.format(
        novel_title=novel_title,
        chapter_num=chapter_num,
        style=style,
        characters=chars_text or "（暂无人物设定）",
        world=world or "（暂无世界观设定）",
        prev_chapter_summary=prev_summary or "（这是第一章，无需前文摘要）",
        outline=outline or "（暂无大纲）",
        chapter_title=chapter_title
    )


def build_user_prompt(
    novel_title: str,
    chapter_num: int,
    chapter_title: str
) -> str:
    """构建用户 Prompt"""
    return USER_PROMPT_TEMPLATE.format(
        novel_title=novel_title,
        chapter_num=chapter_num,
        chapter_title=chapter_title
    )


def build_continue_prompt(
    novel_title: str,
    prev_summary: str,
    last_hook: str
) -> str:
    """构建续写 Prompt"""
    return CONTINUE_PROMPT_TEMPLATE.format(
        novel_title=novel_title,
        prev_summary=prev_summary,
        last_hook=last_hook
    )


def build_regenerate_prompt(
    novel_title: str,
    chapter_num: int,
    outline: str,
    problems: str
) -> str:
    """构建重写 Prompt"""
    return REGENERATE_PROMPT_TEMPLATE.format(
        novel_title=novel_title,
        chapter_num=chapter_num,
        outline=outline,
        problems=problems or "情节平淡、爽点不足"
    )


# 生成质量检查清单
QUALITY_CHECKLIST = {
    "word_count": {
        "min": 2200,
        "max": 2500,
        "description": "字数控制在 2200-2500"
    },
    "structure": {
        "required_sections": ["开篇冲突", "中段发展", "结尾钩子"],
        "description": "包含完整的起承转合"
    },
    "style": {
        "first_person": True,
        "description": "使用第一人称"
    },
    "elements": {
        "required": ["心理描写", "环境渲染", "爽点"],
        "description": "包含必要元素"
    }
}