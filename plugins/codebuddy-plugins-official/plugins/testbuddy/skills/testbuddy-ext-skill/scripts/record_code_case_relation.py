"""
保存代码和用例的关联关系
"""

import argparse
import json
import os


def record_code_case_relation(design_path, file_path, case_uid, function=None, line=None):
    """保存代码和用例的关联关系"""
    if not os.path.exists(design_path):
        raise Exception(f"测试设计目录不存在: {design_path}")
    storage_file = os.path.join(design_path, "code_case_relations.json")
    # 读取现有数据
    relations = {}
    if os.path.exists(storage_file):
        with open(storage_file, "r", encoding="utf-8") as f:
            try:
                relations = json.load(f)
                if not isinstance(relations, dict):
                    raise Exception("code_case_relations.json中的数据结构不为map")
            except json.JSONDecodeError:
                raise Exception("code_case_relations.json中的数据结构不为map")
    # 构建新的关联数据
    new_relation = {"file": file_path}
    if function:
        new_relation["function"] = function
    elif line:
        new_relation["line"] = line
    # 检查是否已存在相同case_uid
    if case_uid in relations:
        if relations[case_uid] == new_relation:
            print(f"关联关系已存在，跳过: case_uid={case_uid}, relation={new_relation}")
            return
        else:
            print(f"更新关联关系: case_uid={case_uid}, 旧={relations[case_uid]} -> 新={new_relation}")
    else:
        print(f"新增关联关系: case_uid={case_uid}, relation={new_relation}")
    # 保存或更新关联
    relations[case_uid] = new_relation
    # 写回文件
    with open(storage_file, "w", encoding="utf-8") as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)
    print(f"关联关系已保存到: {storage_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="保存代码和用例的关联关系")
    parser.add_argument("--design-path", required=True, help="测试设计目录")
    parser.add_argument("--file", required=True, help="代码文件路径（项目内的相对路径）")
    parser.add_argument("--function", required=False, help="函数名（类成员函数格式：ClassName.functionName）")
    parser.add_argument("--line", required=False, help="行号")
    parser.add_argument("--case", required=True, help="用例节点UID")
    args = parser.parse_args()

    if not args.function and not args.line:
        parser.error("必须指定 --function 或 --line 其中之一")

    record_code_case_relation(args.design_path, args.file, args.case, function=args.function, line=args.line)
