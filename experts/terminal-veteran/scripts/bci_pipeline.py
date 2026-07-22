#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_pipeline.py — 终端老兵专家 数据自动化管线 主调度脚本

流程：
  1. bci_fetch.py     — 从IMA知识库读取月度报告
  2. bci_deidentify.py — 脱敏处理
  3. bci_format.py    — 数据格式化+增强
  4. bci_upload.py    — GitHub上传+manifest更新

使用方式：
  python3 bci_pipeline.py 202605        # 处理2026年5月数据
  python3 bci_pipeline.py 202605 --dry  # 只处理不上传（dry run）
"""

import sys
import os
import json
import tempfile

# 脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(step_name, step_func, *args, **kwargs):
    """执行管线步骤，输出结果。"""
    print(f"\n{'='*60}")
    print(f"Step: {step_name}")
    print(f"{'='*60}")
    try:
        result = step_func(*args, **kwargs)
        if result.get("status") == "error":
            print(f"❌ {step_name} 失败: {result.get('details', '')}")
            return False
        print(f"✅ {step_name} 完成: {result.get('details', '')}")
        return result
    except Exception as e:
        print(f"❌ {step_name} 异常: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 bci_pipeline.py YYYYMM [--dry]")
        print("示例: python3 bci_pipeline.py 202605")
        sys.exit(1)

    year_month = sys.argv[1]
    dry_run = "--dry" in sys.argv

    print(f"终端老兵专家 数据管线")
    print(f"目标月份: {year_month}")
    print(f"模式: {'dry run（不上传）' if dry_run else '完整执行'}")

    # Step 1: 从IMA读取
    sys.path.insert(0, SCRIPT_DIR)
    from bci_fetch import fetch_monthly_reports
    step1 = run_step("IMA知识库读取", fetch_monthly_reports, year_month)
    if not step1:
        print("\n管线中止：IMA读取失败")
        sys.exit(1)

    # Step 2: 脱敏处理
    from bci_deidentify import deidentify_content, validate_content
    step2 = run_step("脱敏处理", deidentify_content, step1)
    if not step2:
        print("\n管线中止：脱敏失败")
        sys.exit(1)

    # 校验
    validation = validate_content(step2.get("content", {}))
    if not validation["valid"]:
        print(f"\n❌ 脱敏校验失败: {validation['issues']}")
        sys.exit(1)
    print(f"\n✅ 脱敏验证通过")

    # Step 3: 格式化+增强
    from bci_format import format_monthly_data
    step3 = run_step("数据格式化+增强", format_monthly_data, step2, year_month)
    if not step3:
        print("\n管线中止：格式化失败")
        sys.exit(1)

    # 输出摘要
    files = step3.get("files", {})
    print(f"\n生成文件:")
    for fname, fcontent in files.items():
        print(f"  {fname}: {len(fcontent)} 字符")

    if dry_run:
        print("\n Dry run 模式，跳过上传")
        # 写入临时目录供检查
        tmp_dir = tempfile.mkdtemp(prefix="bci_pipeline_")
        for fname, fcontent in files.items():
            fpath = os.path.join(tmp_dir, fname)
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(fcontent)
        print(f"文件已写入临时目录: {tmp_dir}")
        return

    # Step 4: GitHub上传
    from bci_upload import upload_to_github
    step4 = run_step("GitHub上传", upload_to_github, files, year_month)
    if not step4:
        print("\n管线中止：上传失败")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"管线执行完成！")
    print(f"  月份: {year_month}")
    print(f"  生成文件: {len(files)} 个")
    print(f"  GitHub: {step4.get('details', '')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
