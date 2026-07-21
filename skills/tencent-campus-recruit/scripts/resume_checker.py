"""
腾讯校招简历诊断规则引擎
纯方法论检查，不涉及硬编码的岗位信息。
用法: python resume_checker.py "简历文本内容"
输出: JSON 格式的检查结果列表
"""
import sys
import json
import re


def configure_output_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows terminals with legacy encodings."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


configure_output_encoding()


def check_education(text):
    """R001: 检查是否包含教育背景"""
    keywords = ["大学", "学院", "本科", "硕士", "博士", "学士", "研究生", "毕业", "专业", "GPA", "学历"]
    found = any(k in text for k in keywords)
    return {
        "id": "R001", "name": "教育背景", "severity": "error",
        "passed": found,
        "message": "[OK] 包含教育背景信息" if found else "[ERROR] 未检测到教育背景，建议补充学校、专业、毕业时间"
    }


def check_project(text):
    """R002: 检查是否包含项目经历"""
    keywords = ["项目", "开发", "设计", "实现", "负责", "参与", "搭建", "研发", "完成"]
    found = sum(1 for k in keywords if k in text) >= 2
    return {
        "id": "R002", "name": "项目经历", "severity": "error",
        "passed": found,
        "message": "[OK] 包含项目经历描述" if found else "[ERROR] 项目经历不够突出，建议用STAR法则详细描述2-3个核心项目"
    }


def check_skills(text):
    """R003: 检查是否包含技能列表"""
    keywords = ["技能", "熟悉", "精通", "掌握", "熟练", "了解", "技术栈", "工具", "语言"]
    found = any(k in text for k in keywords)
    return {
        "id": "R003", "name": "技能列表", "severity": "warning",
        "passed": found,
        "message": "[OK] 包含技能描述" if found else "[WARN] 建议添加技能列表，明确列出掌握的技术/工具"
    }


def check_star(text):
    """R004: 检查项目是否使用 STAR 结构"""
    has_situation = any(k in text for k in ["背景", "问题", "需求", "面临", "挑战", "场景", "痛点"])
    has_action = any(k in text for k in ["设计", "实现", "开发", "优化", "搭建", "采用", "使用", "通过"])
    has_result = any(k in text for k in ["提升", "增长", "降低", "减少", "达到", "实现了", "效果", "%", "倍"])
    score = sum([has_situation, has_action, has_result])
    if score >= 3:
        msg = "[OK] 项目描述具有STAR结构要素"
    elif score >= 2:
        msg = "[WARN] 部分使用了STAR结构，建议补充缺失的要素（情境/行动/结果）"
    else:
        msg = "[WARN] 建议使用STAR法则：情境(S)→任务(T)→行动(A)→结果(R)"
    return {"id": "R004", "name": "STAR结构", "severity": "warning", "passed": score >= 2, "message": msg}


def check_quantified(text):
    """R005: 检查是否有量化成果"""
    patterns = [r'\d+%', r'\d+倍', r'\d+万', r'\d+人', r'提升\d+', r'增长\d+', r'减少\d+', r'降低\d+', r'覆盖\d+']
    found = any(re.search(p, text) for p in patterns)
    return {
        "id": "R005", "name": "量化成果", "severity": "suggestion",
        "passed": found,
        "message": "[OK] 包含量化数据" if found else "[TIP] 建议添加量化成果，如'提升XX%'、'覆盖XX万用户'"
    }


def check_weak_verbs(text):
    """R006: 检查常见弱表达"""
    weak_patterns = {
        "参与了": "建议改为具体职责，如'负责XX模块的设计与实现'",
        "协助": "建议明确你的独立贡献",
        "沟通能力强": "建议用具体事例佐证",
        "学习能力强": "建议用具体学习经历佐证",
    }
    issues = [f"「{p}」→ {s}" for p, s in weak_patterns.items() if p in text]
    if issues:
        return {"id": "R006", "name": "表达优化", "severity": "suggestion", "passed": False,
                "message": "[TIP] 发现可优化的表达：\n" + "\n".join(f"  - {i}" for i in issues)}
    return {"id": "R006", "name": "表达优化", "severity": "suggestion", "passed": True,
            "message": "[OK] 未发现常见弱表达"}


def check_length(text):
    """R007: 检查篇幅"""
    n = len(text)
    if n < 200:
        return {"id": "R007", "name": "篇幅", "severity": "warning", "passed": False,
                "message": f"[WARN] 内容偏少（{n}字），建议补充更多项目经历"}
    if n > 3000:
        return {"id": "R007", "name": "篇幅", "severity": "warning", "passed": False,
                "message": f"[WARN] 内容偏长（{n}字），建议精简至1页"}
    return {"id": "R007", "name": "篇幅", "severity": "warning", "passed": True,
            "message": f"[OK] 长度适中（{n}字）"}


def check_resume(text):
    checks = [check_education(text), check_project(text), check_skills(text),
              check_star(text), check_quantified(text), check_weak_verbs(text), check_length(text)]
    passed = sum(1 for c in checks if c["passed"])
    return {
        "summary": {
            "total": len(checks), "passed": passed, "score": round(passed / len(checks) * 100),
            "errors": sum(1 for c in checks if not c["passed"] and c["severity"] == "error"),
            "warnings": sum(1 for c in checks if not c["passed"] and c["severity"] == "warning"),
            "suggestions": sum(1 for c in checks if not c["passed"] and c["severity"] == "suggestion"),
        },
        "details": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请提供简历文本作为参数"}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(check_resume(sys.argv[1]), ensure_ascii=False, indent=2))
