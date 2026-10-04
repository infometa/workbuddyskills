"""进件主体一致性比对脚本（沙箱执行）.

确定性的归代码：企业名称的「抽取」由进件识别 Skill 的 LLM 完成（写入 intake_files.companySubjects），
本脚本只做「比对」——核验各进件材料中的企业主体名称是否与尽调对象一致。

用法（沙箱内）：
    echo '{"benchmark": "...", "subjects": [...]}' | python calculate.py

输入（stdin JSON）:
    {
      "benchmark": "XX有限责任公司",
      "subjects": [
        {"fileName": "营业执照.pdf", "names": ["XX有限责任公司"]},
        {"fileName": "购销合同.pdf", "names": ["XX有限公司", "YY贸易有限公司"]}
      ]
    }

输出（stdout JSON）:
    {
      "consistent": false,
      "issues": [
        {"fileName": "购销合同.pdf", "subjectName": "YY贸易有限公司",
         "benchmark": "XX有限责任公司", "note": "名称不一致（归一化后仍不同）"}
      ]
    }
"""

import json
import sys
from difflib import SequenceMatcher

# 公司类型后缀：归一化时去除，避免「XX有限公司」与「XX有限责任公司」被判为不一致
SUFFIXES = ['有限责任公司', '有限公司', '股份有限公司', '股份公司', '集团']


def normalize(name: str) -> str:
    """归一化企业名称：去首尾空格 + 去全/半角空格 + 去公司类型后缀."""
    n = (name or '').strip().replace(' ', '').replace(' ', '')
    for suffix in sorted(SUFFIXES, key=len, reverse=True):
        if n.endswith(suffix):
            n = n[:-len(suffix)]
            break
    return n


def name_match(a: str, b: str) -> bool:
    """企业名称匹配：归一化后精确匹配，或相似度 >= 0.9（容忍少量错别字）."""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    ratio = SequenceMatcher(None, na, nb).ratio()
    return ratio >= 0.9


def check_subjects(benchmark: str, subjects: list) -> dict:
    """比对各文件企业主体名称与基准名称.

    Args:
        benchmark: 尽调对象企业名称（项目 enterpriseName）
        subjects: [{fileName, names: [企业名称列表]}]

    Returns:
        {consistent: bool, issues: [{fileName, subjectName, benchmark, note}]}
    """
    issues = []
    for s in subjects:
        file_name = s.get('fileName', '')
        names = s.get('names', []) or []
        for name in names:
            if name_match(name, benchmark):
                continue
            issues.append({
                'fileName': file_name,
                'subjectName': name,
                'benchmark': benchmark,
                'note': '名称不一致（归一化后仍不同）',
            })
    return {
        'consistent': len(issues) == 0,
        'issues': issues,
    }


def main() -> None:
    """主入口：从 stdin 读取比对输入，输出比对结果到 stdout."""
    data = json.load(sys.stdin)
    benchmark = data.get('benchmark', '')
    subjects = data.get('subjects', []) or []
    result = check_subjects(benchmark, subjects)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
