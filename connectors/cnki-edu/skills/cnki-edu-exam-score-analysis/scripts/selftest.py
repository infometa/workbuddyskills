# -*- coding: utf-8 -*-
"""cnki-edu-exam-score-analysis 回归自测。

覆盖的都是「真实踩过的坑」——每一条都对应一次线上缺陷，防止改回去：

  * 缺「学号/姓名/班级」任一可选列时不得崩溃（此前 pick_col 传 None 会 TypeError）
  * 首个工作表是说明页 / 表头前有合并大标题行 → 要能自动绕过
  * 长表（一行一题）→ 要给出可读的错误，而不是 KeyError/TypeError
  * 缺考/超满分/负分 → 必须逐个落盘到 data_excluded，不能静默丢人
  * 分数形态判定与报告正文不得自相矛盾（正态集中时的「人数最多段」）
  * 历次成绩必须按「序号 > 日期 > 名称自然序」排，不得用裸字典序
  * 显式 --focus-class 时，逐题/知识点/个体名单要收敛到本班
  * 学科别名（道法 = 道德与法治）要能匹配到列
  * 报表单元格要转义 HTML
  * 满分必须按「用户指定 > 成绩反推 > 停下来问用户」解析：
    没给满分且反推不出唯一分制时要退出码 3 请用户给出，不得擅自按默认值出报告
    （真实踩过：语文 150 分制默认值套到 100 分制成绩表上，全班不及格）
  * 分制分布 = 100（常规）/ 150 / 10 / 5：候选分制展示时 100 排首位并标「常规」，
    --full-policy default 一律按常规 100 分制兜底（不再按学科名猜 150/120）
  * 缺逐题 / 知识点数据时，维度 3/4 与 Excel「04/05」**整块不生成**，
    不摆「数据缺失」空板块
  * **绝不编造知识点**：逐题表没有（或整列为空）「知识点」列时，不得兜底成「未标注」，
    维度 4 与 Excel「05」不生成、表格里也不留空的知识点列
  * **重复学号**按同一人合并、**保留最后一条**（不得当两个学生：人数虚高、排名重复）
  * **整列缺考/非数值的学科**不得静默丢弃：自动识别时提示，显式指定时明确失败
  * **历次考试顺序判不出只警告不阻断**：混排名称（第1次月考/期中考试/…）曾静默排错、趋势反向，
    现在必须把 `[警告]` 同时写进 stderr、`data_notes`、报告摘要 / 维度 6 与 Excel 07，
    但**报告照常产出**（不能因为维度 6 存疑就让整份报告拿不到）；名称里的中文数字
    （第一次月考）与阿拉伯数字一样要能排出先后；历次只有 1 次考试时自动退回横截面分层
  * **坏掉的 narrative.json 不拖垮主交付**：非法 JSON / 字段类型写错只降级为「无话术」，
    HTML 与 Excel 必须照常产出；narrative 与结果册已解耦（Excel 不再吃 --narrative）
  * `--focus-class` 指定的班级不存在时，封面标签同步改成「全部样本」（不写不存在的班）
  * 只分析部分学科时，合计列写「所选学科总分」而不是「全科总分」
  * **正式报告里不放「附录 · 交付物与脚本说明」**：Excel 表数、文件名、脚本路径、配色代码、
    复用命令都是内部信息，只能在对话回复里交代（报告只讲教学结论）
  * **报告与 Excel 结果册都不承载「数据说明」**：`data_notes` / `data_excluded` 不进报告正文，
    `meta.full_to_confirm` 只留学科章首小字（待确认满分）与「核心结论摘要」⚠️（历次顺序存疑）；
    Excel「01 阅读说明」也不再有 满分设定 / 分数线设定 / 数据来源 / 数据说明 / 未生成的工作表
    （用户要求 2026-10-08），只保留考试信息 + 工作表导航 + 被剔除学生逐个点名，
    其余数据质量交代一律在 analysis.json、命令行输出与**对话交付说明**里复述

用法::

    python scripts/selftest.py            # 全部用例
    python scripts/selftest.py -k 满分     # 只跑名字包含关键字的用例

退出码 0 = 全过；1 = 有失败。
"""

from __future__ import annotations

import argparse
import glob as _glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "exam_analysis.py")
BUILDER = os.path.join(HERE, "report_builder.py")
EXCEL = os.path.join(HERE, "build_excel.py")
PY = sys.executable

try:
    from openpyxl import Workbook, load_workbook
except ImportError:  # pragma: no cover
    print("[错误] 自测需要 openpyxl（用于生成测试用的 xlsx）：")
    print('       "%s" -m pip install openpyxl' % PY)
    raise SystemExit(2)


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
WORK = tempfile.mkdtemp(prefix="examscore_selftest_")
RESULTS = []


def save_xlsx(path, sheets):
    """sheets: [(sheet_name, header_row, rows), ...]"""
    wb = Workbook()
    wb.remove(wb.active)
    for name, header, rows in sheets:
        ws = wb.create_sheet(name)
        for h in header:
            ws.append(h)
        for r in rows:
            ws.append(r)
    wb.save(path)
    return path


def run_engine(data, *extra):
    cmd = [PY, ENGINE, "--data", data, "--out", os.path.join(WORK, "out.json")] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORK)


def load_out():
    with open(os.path.join(WORK, "out.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def case(fn):
    RESULTS.append(fn)
    return fn


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# --------------------------------------------------------------------------- #
# 用例
# --------------------------------------------------------------------------- #
@case
def test_optional_columns_missing():
    """缺「班级/学号/姓名」任一列都不得崩溃（P0）。"""
    variants = {
        "缺班级": (["学号", "姓名", "语文"], [["A1", "赵一", 88], ["A2", "钱二", 74]]),
        "缺学号": (["姓名", "班级", "语文"], [["赵一", "初一(3)班", 88], ["钱二", "初一(3)班", 74]]),
        "缺姓名": (["学号", "班级", "语文"], [["A1", "初一(3)班", 88], ["A2", "初一(3)班", 74]]),
        "姓名成绩最简": (["姓名", "语文"], [["赵一", 88], ["钱二", 74]]),
    }
    for name, (header, rows) in variants.items():
        fp = save_xlsx(os.path.join(WORK, "t1.xlsx"), [("成绩", [header], rows)])
        p = run_engine(fp, "--exam-name", name, "--subjects", "语文")
        check(p.returncode == 0,
              "%s 应能正常分析，实际退出码 %s：%s" % (name, p.returncode, (p.stderr or "").strip()[-200:]))
        an = load_out()
        check(an["results"]["语文"]["stats"]["count"] == 2, "%s 应统计到 2 人" % name)


@case
def test_header_and_sheet_fallback():
    """表头前有合并大标题行、首个工作表是说明页 → 要能自动绕过。"""
    # 双行：第 1 行大标题，第 2 行真表头
    wb = Workbook()
    ws = wb.active
    ws.title = "成绩"
    ws.append(["初一(3)班期中考试成绩表", None, None, None])
    ws.merge_cells("A1:D1")
    ws.append(["学号", "姓名", "班级", "语文"])
    ws.append(["A1", "赵一", "初一(3)班", 88])
    ws.append(["A2", "钱二", "初一(3)班", 74])
    p1 = os.path.join(WORK, "t2a.xlsx")
    wb.save(p1)
    r = run_engine(p1, "--exam-name", "双行表头", "--subjects", "语文")
    check(r.returncode == 0, "双行合并表头应能自动跳过大标题行，stderr=%s" % (r.stderr or "").strip()[-200:])
    check(load_out()["results"]["语文"]["stats"]["count"] == 2, "双行表头应读到 2 人")

    # 首表是说明页
    p2 = save_xlsx(os.path.join(WORK, "t2b.xlsx"), [
        ("填写说明", [["本表由教务系统导出"]], []),
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A1", "赵一", "初一(3)班", 88], ["A2", "钱二", "初一(3)班", 74]]),
    ])
    r = run_engine(p2, "--exam-name", "首表说明页", "--subjects", "语文")
    check(r.returncode == 0, "首表为说明页时应自动改用第二个工作表，stderr=%s" % (r.stderr or "").strip()[-200:])
    an = load_out()
    check(an["meta"]["source_sheet"] == "成绩", "应记录实际使用的工作表，实际=%s" % an["meta"]["source_sheet"])
    check(any("自动改用" in n for n in an["data_notes"]), "应在数据说明中交代换表")


@case
def test_long_table_error_is_readable():
    """一行一题的长表：要给可读错误，不能抛 TypeError。"""
    rows = []
    for i in range(4):
        for subj in ("语文", "数学"):
            rows.append(["A%d" % i, "学生%d" % i, "初一(3)班", subj, 1, 3, 2])
    fp = save_xlsx(os.path.join(WORK, "t3.xlsx"), [
        ("Sheet1", [["学号", "姓名", "班级", "学科", "题号", "满分", "得分"]], rows)])
    r = run_engine(fp, "--exam-name", "长表", "--subjects", "语文,数学")
    check(r.returncode != 0, "长表应明确失败")
    err = (r.stderr or "") + (r.stdout or "")
    check("Traceback" not in err, "不应抛裸异常，实际输出：%s" % err[-300:])
    check("学科列" in err or "表头" in err, "错误信息应指出问题所在，实际：%s" % err[-200:])


@case
def test_excluded_students_are_recorded():
    """缺考/超满分/负分必须逐个落盘，不能静默丢人。"""
    fp = save_xlsx(os.path.join(WORK, "t4.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A1", "赵一", "初一(3)班", 88], ["A2", "钱二", "初一(3)班", "缺考"],
          ["A3", "孙三", "初一(3)班", 999], ["A4", "李四", "初一(3)班", -5],
          ["A5", "周五", "初一(3)班", 70], ["A6", "吴六", "初一(3)班", 61],
          ["A7", "郑七", "初一(3)班", 55], ["A8", "王八", "初一(3)班", 99]])])
    r = run_engine(fp, "--exam-name", "剔除名单", "--subjects", "语文")
    check(r.returncode == 0, "应能完成分析")
    an = load_out()
    ex = an["data_excluded"]["语文"]
    names = {e["name"]: e["reason"] for e in ex}
    check(len(ex) == 3, "应有 3 条剔除记录，实际 %d 条：%s" % (len(ex), names))
    check("钱二" in names and "缺考" in names["钱二"], "缺考学生要落盘")
    check("孙三" in names and "超出" in names["孙三"], "超满分要落盘")
    check("李四" in names and "超出" in names["李四"], "负分要落盘")
    check(an["results"]["语文"]["stats"]["count"] == 5, "有效人数应为 5")
    check(any("剔除" in n for n in an["data_notes"]), "数据说明要提到剔除")


@case
def test_shape_text_matches_data():
    """分数形态的兜底文案必须与实际人数最多的分数段一致（此前硬编码 70–80%）。"""
    scores = [55, 62, 65, 66, 68, 72, 75, 78, 85, 88]
    fp = save_xlsx(os.path.join(WORK, "t5.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A%02d" % i, "学生%02d" % i, "高一(1)班", s] for i, s in enumerate(scores, 1)])])
    params = os.path.join(WORK, "p5.json")
    with open(params, "w", encoding="utf-8") as fh:
        json.dump({"subjects": {"语文": {"full": 100}}}, fh, ensure_ascii=False)
    r = run_engine(fp, "--exam-name", "形态", "--subjects", "语文", "--params", params)
    check(r.returncode == 0, "应能完成分析")
    r2 = load_out()["results"]["语文"]
    bands = r2["bands"]
    top = max(bands, key=lambda b: b["count"])["label"]
    check(top == "60–70%", "本用例 60–70%% 段人数最多，实际 %s" % top)
    check(r2["shape"]["type"] == "正态集中", "应判为 正态集中，实际 %s" % r2["shape"]["type"])
    check(top in r2["shape"]["evidence"],
          "形态依据文案必须引用真实的最多段（%s），实际：%s" % (top, r2["shape"]["evidence"]))


@case
def test_history_order_natural_sort():
    """第1次…第10次月考必须按数字排序，趋势判定不得反转。"""
    rows_m = []
    rows_h = []
    for i in range(1, 6):
        rows_m.append(["A%d" % i, "学生%d" % i, "高二(1)班", 100 + i])
    for n in range(1, 11):
        rows_h.append(["A1", "学生1", "第%d次月考" % n, 500 + n * 10, 40 - n])   # 持续进步
        rows_h.append(["A2", "学生2", "第%d次月考" % n, 600 - n * 10, 5 + n])    # 持续下滑
    fp = save_xlsx(os.path.join(WORK, "t6.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows_m),
        ("历次", [["学号", "姓名", "考试", "总分", "排名"]], rows_h)])
    r = run_engine(fp, "--exam-name", "历次", "--subjects", "数学")
    check(r.returncode == 0, "应能完成分析")
    ind = load_out()["results"]["数学"]["individuals"]
    check(ind["mode"] == "history", "应进入历次追踪模式")
    by = {x["name"]: x for x in ind["history"]}
    ex = by["学生1"]["exams"]
    check(ex[0] == "第1次月考" and ex[-1] == "第10次月考",
          "考试顺序应为 第1次→第10次，实际 %s" % ex)
    check(by["学生1"]["trend"] == "持续进步", "学生1 应判持续进步，实际 %s" % by["学生1"]["trend"])
    check(by["学生1"]["total_delta"] > 0, "学生1 total_delta 应为正，实际 %s" % by["学生1"]["total_delta"])
    check(by["学生2"]["trend"] == "持续下滑", "学生2 应判持续下滑，实际 %s" % by["学生2"]["trend"])


@case
def test_history_order_unknown_warns_not_blocks():
    """名称既无序号也无日期 → 顺序不可判定：**只警告不阻断**，报告照常出且显著标注。

    规则（用户 2026-10-08 定）：不因为维度 6 的顺序存疑就让整份报告拿不到；
    但告警必须同时出现在 stderr、data_notes、报告维度 6 与摘要，Excel 07 也要标注。
    """
    rows_h = []
    for sid, nm, base, step in (("A1", "学生1", 500, 40), ("A2", "学生2", 620, -40)):
        for i, e in enumerate(("开学摸底", "期中考试", "期末考试")):
            rows_h.append([sid, nm, e, base + step * i, 1])
    fp = save_xlsx(os.path.join(WORK, "t7.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A1", "学生1", "高二(1)班", 100], ["A2", "学生2", "高二(1)班", 70]]),
        ("历次", [["学号", "姓名", "考试", "总分", "排名"]], rows_h)])
    r = run_engine(fp, "--exam-name", "历次无序号", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "顺序判不出**只警告不阻断**，实际退出码 %s：%s"
          % (r.returncode, ((r.stderr or "") + (r.stdout or ""))[-300:]))
    err = (r.stderr or "") + (r.stdout or "")
    check("[警告]" in err, "应打印 [警告]，实际：%s" % err[-300:])
    check("无法判断先后顺序" in err, "要说明是顺序问题，实际：%s" % err[-300:])
    check("--history-order" in err, "要给出补救命令，实际：%s" % err[-300:])
    check("Traceback" not in err, "不应抛裸异常")
    an = load_out()
    check(an["meta"]["history_order_source"] == "unknown", "应记录 history_order_source=unknown")
    check(an["meta"]["history_order_reliable"] is False, "应标记 history_order_reliable=False")
    check(any("无法判断先后顺序" in n for n in an["data_notes"]), "告警要进 data_notes")
    check(an["results"]["数学"]["individuals"]["mode"] == "history",
          "仍按历次追踪渲染（不因顺序存疑退回横截面）")
    # 报告：摘要与维度 6 都要有醒目提示（不能静默）
    hp = os.path.join(WORK, "t7.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"), "--out", hp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "").strip()[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("历次考试的先后顺序无法判定" in htm, "报告维度 6 要有醒目告警")
    check("note red" in htm, "告警要用醒目样式（note red）")
    check("⚠️ 历次考试的" in htm, "「核心结论摘要」也要有这条 ⚠️（不能只靠维度 6）")
    check("数据说明" not in htm and "待核对的历次考试顺序" not in htm,
          "报告已无「数据说明」章节，顺序告警只出现在摘要与维度 6")
    # 显式指定顺序后：告警消失、趋势判定正确
    r2 = run_engine(fp, "--exam-name", "历次指定序", "--subjects", "数学", "--full", "数学=100",
                    "--history-order", "开学摸底,期中考试,期末考试")
    check(r2.returncode == 0, "--history-order 应能跑完，stderr=%s" % (r2.stderr or "")[-300:])
    an2 = load_out()
    check(an2["meta"]["history_order_source"] == "explicit", "显式顺序应记 explicit")
    check(an2["meta"]["history_order_reliable"] is True, "显式顺序应视为可靠")
    check(not any("无法判断先后顺序" in n for n in an2["data_notes"]), "显式顺序后不应再有告警")
    by = {x["name"]: x for x in an2["results"]["数学"]["individuals"]["history"]}
    check(by["学生1"]["exams"][0] == "开学摸底" and by["学生1"]["exams"][-1] == "期末考试",
          "顺序应按显式给定，实际 %s" % by["学生1"]["exams"])
    check(by["学生1"]["trend"] == "持续进步", "学生1 应判持续进步，实际 %s" % by["学生1"]["trend"])
    check(by["学生2"]["trend"] == "持续下滑", "学生2 应判持续下滑，实际 %s" % by["学生2"]["trend"])


@case
def test_history_mixed_names_warns():
    """「第1次月考 / 期中考试 / 第2次月考 / 期末考试」混排 → 只警告不阻断（曾静默排错）。"""
    rows_h = []
    plan = [("第1次月考", 500), ("期中考试", 540), ("第2次月考", 560), ("期末考试", 600)]
    for i in range(1, 4):
        for e, t in plan:
            rows_h.append(["A%d" % i, "学生%d" % i, e, t + i * 5, 1])
    fp = save_xlsx(os.path.join(WORK, "t7b.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A%d" % i, "学生%d" % i, "初二(1)班", 80 + i] for i in range(1, 4)]),
        ("历次", [["学号", "姓名", "考试", "总分", "排名"]], rows_h)])
    r = run_engine(fp, "--exam-name", "混排历次", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "混排考试名应只警告不阻断，实际退出码 %s：%s"
          % (r.returncode, ((r.stderr or "") + (r.stdout or ""))[-200:]))
    err = (r.stderr or "") + (r.stdout or "")
    check("期中考试" in err and "期末考试" in err, "告警里要列出混排的考试名称，实际：%s" % err[-300:])
    check("[警告]" in err, "应是 [警告] 而不是 [需确认]；实际：%s" % err[-300:])
    an = load_out()
    check(an["meta"]["history_order_source"] == "unknown", "混排名称应判为 unknown")
    check(an["results"]["数学"]["individuals"]["mode"] == "history", "报告照常出")


@case
def test_history_cn_numeral_order():
    """「第一次月考 / 第二次月考 / 第三次月考」要能排出先后。

    中文数字的字典序与数值序不一致（三 < 二 in Unicode），不解析就会把
    「第三次」排到「第二次」前面 —— 顺序一旦反转，趋势判定与进步榜全错。
    """
    rows_h = []
    for i, e in enumerate(("第一次月考", "第二次月考", "第三次月考")):
        rows_h.append(["A1", "学生1", e, 500 + i * 40, 1])
        rows_h.append(["A2", "学生2", e, 620 - i * 40, 1])
    fp = save_xlsx(os.path.join(WORK, "t7c.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A1", "学生1", "高一(2)班", 100], ["A2", "学生2", "高一(2)班", 70]]),
        ("历次", [["学号", "姓名", "考试", "总分", "排名"]], rows_h)])
    r = run_engine(fp, "--exam-name", "中文数字历次", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["history_order_source"] == "seq", "名称里的中文数字应能解析成序号")
    by = {x["name"]: x for x in an["results"]["数学"]["individuals"]["history"]}
    check(by["学生1"]["exams"] == ["第一次月考", "第二次月考", "第三次月考"],
          "顺序应为 第一次→第二次→第三次，实际 %s" % by["学生1"]["exams"])
    check(by["学生1"]["trend"] == "持续进步", "学生1 应判持续进步，实际 %s" % by["学生1"]["trend"])
    check(by["学生2"]["trend"] == "持续下滑", "学生2 应判持续下滑，实际 %s" % by["学生2"]["trend"])


@case
def test_focus_class_scope():
    """逐题统计按「班级层 + 年级层」两层并列，并**逐班**给出每道小题得分率（用户要求 2026-10-10/11）。

    班级层 = 主分析班级（显式 --focus-class，未指定时引擎默认取第一个班）；
    年级层恒为全部样本。小题分分析**不再下到每个学生**（用户要求 2026-10-11）。
    """
    rows_m, rows_q = [], []
    for tag, cls, n in (("1", "高一(1)班", 6), ("2", "高一(2)班", 8)):
        for i in range(1, n + 1):
            rows_m.append(["A%s%02d" % (tag, i), "%s班学生%d" % (tag, i), cls, 60 + i])
        for i in range(1, n + 1):
            rows_q.append(["A%s%02d" % (tag, i), "数学", 1, 10, 5, "集合"])
    fp = save_xlsx(os.path.join(WORK, "t8.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows_m),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], rows_q)])

    # 本用例成绩最高 68 分，反推不出唯一满分（70/75/80 都可能）→ 引擎会要求确认，故显式给满分
    FULL = ["--full", "数学=100"]
    r = run_engine(fp, "--exam-name", "范围", "--subjects", "数学", "--focus-class", "高一(1)班", *FULL)
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "").strip()[-200:])
    an = load_out()
    rk = an["results"]["数学"]["individuals"]["ranking"]
    check(len(rk) == 6, "本班范围排名应为 6 人，实际 %d" % len(rk))
    check({x["cls"] for x in rk} == {"高一(1)班"}, "排名不应含其他班")
    check(an["meta"]["individual_scope_is_focus"] is True, "meta 应标记为本班范围")
    n1 = an["results"]["数学"]["questions"][0]["n"]
    check(n1 == 6, "逐题作答人数应为本班 6 人，实际 %d" % n1)

    # 未显式指定主分析班级 → engine 默认取第一个班（有 data_note 提示）；
    # 维度 3 的班级层就是该班，年级层恒为全部样本（用户要求 2026-10-10：两层并列）
    r = run_engine(fp, "--exam-name", "范围默认班", "--subjects", "数学", *FULL)
    an2 = load_out()
    check(len(an2["results"]["数学"]["individuals"]["ranking"]) == 6,
          "未指定班级时应默认第一个班 6 人，实际 %d"
          % len(an2["results"]["数学"]["individuals"]["ranking"]))
    check(an2["meta"]["individual_scope"] == "高一(1)班", "默认主分析班级应为高一(1)班")
    check(an2["meta"]["two_level_questions"] is True, "多班数据应标记为「班级层+年级层」两层")
    q0 = an2["results"]["数学"]["questions"][0]
    check(q0["n"] == 6 and q0["n_all"] == 14,
          "逐题应同时给出班级层 6 人与年级层 14 人，实际 %s/%s" % (q0["n"], q0["n_all"]))
    check(q0["two_scope"] is True, "应标记该题的班级层与年级层不同源")
    byc = {c["cls"]: c for c in q0.get("by_class") or []}
    check(set(byc) == {"高一(1)班", "高一(2)班"},
          "逐题应**按班给出每道小题的得分率**，实际 %s" % sorted(byc))
    check(byc["高一(1)班"]["n"] == 6 and byc["高一(2)班"]["n"] == 8,
          "各班作答人数应为 6 / 8，实际 %s/%s"
          % (byc["高一(1)班"]["n"], byc["高一(2)班"]["n"]))


@case
def test_subject_alias():
    """列名「道法」+ --subjects「道德与法治」要能匹配（此前整科被静默跳过）。"""
    fp = save_xlsx(os.path.join(WORK, "t9.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "道法", "语文"]],
         [["A1", "赵一", "初二(1)班", 88, 90], ["A2", "钱二", "初二(1)班", 74, 65]])])
    r = run_engine(fp, "--exam-name", "别名", "--subjects", "道德与法治")
    check(r.returncode == 0, "别名应能匹配到列，stderr=%s" % (r.stderr or "").strip()[-200:])
    an = load_out()
    check(an["meta"]["subjects"] == ["道德与法治"], "学科名应保留用户给定的写法")
    check(an["results"]["道德与法治"]["stats"]["count"] == 2, "应统计到 2 人")
    check(an["results"]["道德与法治"]["column"] == "道法", "应记录真实列名")


@case
def test_html_escaped():
    """报表单元格要转义 HTML（姓名里出现 < 之类字符时不能破版）。"""
    fp = save_xlsx(os.path.join(WORK, "t10.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A1", "张三<b>x", "初三(1)班", 88], ["A2", "李四&五", "初三(1)班", 70]])])
    r = run_engine(fp, "--exam-name", "转义", "--subjects", "语文")
    check(r.returncode == 0, "应能完成分析")
    html_path = os.path.join(WORK, "t10.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", html_path, "--no-excel"],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功")
    htm = open(html_path, encoding="utf-8").read()
    check("&lt;b&gt;" in htm, "姓名中的 < 应被转义")
    check("张三<b>x" not in htm, "不应出现未转义的原始标签")
    check("&amp;" in htm, "& 应被转义")
    check("李四&amp;五" in htm, "第二个学生应出现在表格中")
    # 「班内/样本成绩排名」表此前取错层级一直是空表，这里锁死它必须有数据行
    seg = htm.split("排名（")[-1].split("</table>")[0]
    check(seg.count("<tr>") >= 2, "排名表必须有数据行，实际 tbody 为空")


@case
def test_full_score_inferred_by_data():
    """没给满分时按成绩分布反推分制（100 / 150 / 10 / 5 分制都要认得）。"""
    rows = []
    plan = [
        ("语文", [88, 95, 76, 91, 66]),        # 最高 95 → 100 分制
        ("数学", [132, 145, 120, 108, 99]),    # 最高 145 → 150 分制
        ("体育", [9, 8.5, 10, 7, 6]),          # 最高 10  → 10 分制
        ("科学", [5, 4, 3, 5, 2]),             # 最高 5   → 5 分制
    ]
    for i in range(5):
        rows.append(["A%d" % (i + 1), "学生%d" % (i + 1), "初一(3)班"] + [p[1][i] for p in plan])
    fp = save_xlsx(os.path.join(WORK, "t12.xlsx"), [
        ("成绩", [["学号", "姓名", "班级"] + [p[0] for p in plan]], rows)])
    r = run_engine(fp, "--exam-name", "满分反推", "--subjects", "语文,数学,体育,科学")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "").strip()[-200:])
    an = load_out()
    want = {"语文": 100, "数学": 150, "体育": 10, "科学": 5}
    for s, f in want.items():
        got = an["results"][s]["full"]
        check(got == f, "%s 应反推为 %g 分制，实际 %g" % (s, f, got))
        check(an["results"][s]["full_source"] == "inferred", "%s 的满分来源应标为 inferred" % s)
    # 反推出来的满分必须带「待确认」标记，不能当作用户确认过的满分
    conf = {x["subject"]: x for x in an["meta"]["full_to_confirm"]}
    check(set(conf) == set(want), "四个学科都应进入待确认清单，实际 %s" % list(conf))
    check(any("满分" in n and "核对" in n for n in an["data_notes"]), "数据说明要提示核对满分")
    check("[需确认]" in (r.stdout or ""), "stdout 要打印待确认提示，便于 Agent 转达用户")


@case
def test_full_score_unresolved_stops_and_asks():
    """推断不出满分时必须停下来请用户给出（退出码 3），不得擅自按默认值跑完。"""
    fp = save_xlsx(os.path.join(WORK, "t13.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A1", "赵一", "初一(3)班", 68], ["A2", "钱二", "初一(3)班", 61],
          ["A3", "孙三", "初一(3)班", 65]])])
    r = run_engine(fp, "--exam-name", "满分缺失", "--subjects", "数学")
    check(r.returncode == 3, "应以便于识别的退出码 3 停下，实际 %s" % r.returncode)
    err = (r.stderr or "") + (r.stdout or "")
    check("请确认实际满分" in err or "满分" in err, "错误信息要说明缺满分，实际：%s" % err[-300:])
    check("--full" in err, "要给出补救命令，实际：%s" % err[-300:])
    check("常规" in err, "要告诉用户常见分制（100 为常规），实际：%s" % err[-300:])
    check("Traceback" not in err, "不应抛裸异常")
    # 用 --full-policy default 才允许继续，且一律按常规 100 分制
    r2 = run_engine(fp, "--exam-name", "满分缺失默认", "--subjects", "数学", "--full-policy", "default")
    check(r2.returncode == 0, "--full-policy default 应能跑完")
    an = load_out()
    check(an["results"]["数学"]["full"] == 100, "default 策略应取常规 100 分制，实际 %g" % an["results"]["数学"]["full"])
    check(an["meta"]["full_to_confirm"], "即使用默认值也要登记为待确认")


@case
def test_full_common_convention():
    """常规分制为 100 分：default 兜底=100；候选项按「常见度」展示；不得静默猜分制。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ea_mod", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # ① 候选分制展示顺序：100（常规）→ 150 → 10 → 5 → 其余升序
    got = mod.sort_full_candidates([5, 10, 100, 150, 80])
    check(got == [100, 150, 10, 5, 80], "候选排序应为 [100,150,10,5,80]，实际 %s" % got)
    txt = mod.full_candidates_text([80, 100])
    check(txt.startswith("100 分制（常规）"), "常规 100 分制要排首位并标注，实际 %s" % txt)
    txt2 = mod.full_candidates_text([70, 75, 80])
    check(txt2 == "70 分制、75 分制、80 分制", "非常见分制应升序且不加标注，实际 %s" % txt2)

    # ② default 策略：语文也按常规 100（不再是 150）；汇总列仍按 750
    check(mod.DEFAULT_FULL.get("语文", mod.DEFAULT_FULL_COMMON) == 100,
          "default 策略下语文应为常规 100 分制")
    check(mod.DEFAULT_FULL_COMMON == 100, "常规分制应为 100")

    # ③ 反推仍然只认「唯一候选」，100 与 150 都说得通时必须停下
    r = run_engine(save_xlsx(os.path.join(WORK, "t16.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A1", "赵一", "初一(3)班", 88], ["A2", "钱二", "初一(3)班", 95]])]),
        "--exam-name", "常规反推", "--subjects", "语文")
    check(r.returncode == 0, "最高 95 → 唯一候选 100，应能直接跑完，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["results"]["语文"]["full"] == 100, "最高 95 应反推 100 分制")
    check(an["results"]["语文"]["full_source"] == "inferred", "反推的满分要标 inferred 待确认")


@case
def test_full_score_user_specified_wins():
    """用户显式给满分（--full / params.json）时不得再去推断或询问。"""
    fp = save_xlsx(os.path.join(WORK, "t14.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]],
         [["A1", "赵一", "初一(3)班", 68, 88], ["A2", "钱二", "初一(3)班", 61, 74]])])
    r = run_engine(fp, "--exam-name", "用户满分", "--subjects", "数学,语文", "--full", "数学=120")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "").strip()[-200:])
    an = load_out()
    check(an["results"]["数学"]["full"] == 120, "数学应为用户指定的 120")
    check(an["results"]["数学"]["full_source"] == "user", "满分来源应为 user")
    check(all(x["subject"] != "数学" for x in an["meta"]["full_to_confirm"]),
          "用户指定的学科不应出现在待确认清单")
    check(an["results"]["语文"]["full"] == 100, "语文最高 88 → 应反推 100")


@case
def test_missing_sections_not_rendered():
    """缺逐题/知识点数据时，维度 3/4 与 Excel 04/05 **整块不生成**，不摆「数据缺失」空板块。"""
    rows = [["A%d" % i, "学生%d" % i, "初一(3)班", 60 + i * 3, 70 + i * 2] for i in range(1, 7)]
    qrows = [["A%d" % i, "语文", 1, 10, 5 + i % 2, "积累"] for i in range(1, 7)]

    # ① 完全没有逐题数据
    fp = save_xlsx(os.path.join(WORK, "t15a.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "无逐题", "--subjects", "语文,数学", "--full", "语文=100,数学=100")
    check(r.returncode == 0, "应能完成分析")
    hp = os.path.join(WORK, "t15a.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "").strip()[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("逐题得分率</h3>" not in htm, "维度 3 整节（含标题）不应出现")
    check("知识点掌握热力图</h3>" not in htm, "维度 4 整节（含标题）不应出现")
    check("数据缺失" not in htm, "不应出现「数据缺失」占位板块")
    check("完整 6 维度分析" not in htm, "章节名不应虚报「完整 6 维度」")
    # 那行「本节未生成」小字已按要求删除（用户要求 2026-10-11）：
    # 缺失原因属于内部交代，只进对话交付说明，报告正文保持干净
    check("本节未生成" not in htm, "不应再出现「本节未生成」说明小字")
    check("知识点" not in htm, "完全没有知识点数据时，全文不应出现「知识点」字样")
    xp = os.path.join(WORK, "t15a.xlsx")
    p = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "Excel 生成应成功")
    from openpyxl import load_workbook
    names = load_workbook(xp).sheetnames
    check(not any(n.startswith("04") for n in names), "缺逐题数据时 04 表不应生成，实际 %s" % names)
    check(not any(n.startswith("05") for n in names), "缺知识点数据时 05 表不应生成，实际 %s" % names)
    ws = load_workbook(xp)["01 阅读说明"]
    labels = [str(ws.cell(r, 1).value) for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value]
    check("未生成的工作表" not in labels,
          "阅读说明里不再交代「未生成的工作表」（用户要求 2026-10-08）")
    check("04 逐题得分率" not in labels and "05 知识点优先级" not in labels,
          "04/05 未生成时，导航也不该列这两张表，实际 %s" % labels)
    check("未纳入统计的学生" not in " ".join(labels),
          "全员计入统计时不该出现「未纳入统计的学生」（否则指着一个并不存在的表）")

    # ② 有逐题数据 → 要正常出现
    fp2 = save_xlsx(os.path.join(WORK, "t15b.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], qrows)])
    r = run_engine(fp2, "--exam-name", "有逐题", "--subjects", "语文,数学", "--full", "语文=100,数学=100")
    check(r.returncode == 0, "应能完成分析")
    hp2 = os.path.join(WORK, "t15b.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp2, "--no-excel"], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功")
    htm2 = open(hp2, encoding="utf-8").read()
    check("逐题得分率</h3>" in htm2, "有逐题数据时维度 3 应出现")
    check("知识点掌握热力图</h3>" in htm2, "有知识点数据时维度 4 应出现")
    # 跨学科的「TOP3 共性错题」按学科分别成表，表上方标学科名（用户要求 2026-10-11）
    check("【语文】TOP3 共性错题" in htm2,
          "跨学科共性错题应按学科分别成表并在表上方标学科名，实际未出现")

    # ③ 有逐题但**没有知识点列**（用户要求 2026-10-11）：
    #    涉及知识点的地方一律不显示该列 / 该节，但其他内容照常显示；
    #    跨学科 TOP3 与教学建议的「知识点薄弱点」都退回按**小题得分率**给出。
    qrows2 = [["A%d" % i, "语文", 1, 10, 5 + i % 2] for i in range(1, 7)]
    fp3 = save_xlsx(os.path.join(WORK, "t15c.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分"]], qrows2)])
    r = run_engine(fp3, "--exam-name", "无知识列样本",
                   "--subjects", "语文,数学", "--full", "语文=100,数学=100")
    check(r.returncode == 0, "应能完成分析")
    hp3 = os.path.join(WORK, "t15c.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp3, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功")
    htm3 = open(hp3, encoding="utf-8").read()
    check("逐题得分率</h3>" in htm3, "有逐题数据时维度 3 应正常出现（不能被知识点缺失拖没）")
    check("知识点掌握热力图</h3>" not in htm3, "无知识点数据时维度 4 整节不应出现")
    check("知识点" not in htm3, "无知识点数据时全文不应出现「知识点」字样")
    check("本节未生成" not in htm3, "不应出现「本节未生成」说明小字")
    check("各学科 · 薄弱试题 TOP3" in htm3,
          "无知识点时跨学科应退回按试题得分率给出 TOP3，实际未出现")
    check("【语文】薄弱试题 TOP3" in htm3,
          "薄弱试题 TOP3 应按学科分别成表并在表上方标学科名，实际未出现")
    check("薄弱题讲评优先级（按小题得分率）" in htm3,
          "教学建议应退回按小题得分率给讲评清单，实际未出现")


@case
def test_report_ranking_table_not_empty():
    """报告里的「样本/班内成绩排名」表必须有真实数据行（曾因取错层级长期为空表）。"""
    fp = save_xlsx(os.path.join(WORK, "t11.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A%d" % i, "学生%d" % i, "高一(1)班", 60 + i * 3] for i in range(1, 8)])])
    # 本用例最高 81 分，反推不出唯一满分（80/100 都可能）→ 显式指定
    r = run_engine(fp, "--exam-name", "排名表", "--subjects", "语文", "--full", "语文=100")
    check(r.returncode == 0, "应能完成分析")
    html_path = os.path.join(WORK, "t11.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", html_path, "--no-excel"],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功")
    htm = open(html_path, encoding="utf-8").read()
    an = load_out()
    n = len(an["results"]["语文"]["individuals"]["ranking"])
    check(n == 7, "ranking 应有 7 人，实际 %d" % n)
    seg = htm.split("排名（")[-1].split("</table>")[0]
    check(seg.count("<tr>") >= n, "排名表应渲染 %d 行，实际 %d 行" % (n, seg.count("<tr>")))
    check("学生1" in seg and "学生7" in seg, "排名表应包含首末学生")


@case
def test_excel_missing_openpyxl_is_friendly():
    """缺少 openpyxl 时，build_excel 要给出安装指引而不是裸 ModuleNotFoundError。"""
    # 候选「没装 openpyxl 的解释器」：受管 versions/ 下的裸解释器 + 当前解释器兜底。
    # 用 glob 动态发现——**不写死用户名绝对路径**（用户要求 2026-10-12），
    # 换机器 / 换 Python 版本都不用改代码。
    cands = sorted(_glob.glob(os.path.join(
        os.path.expanduser("~"), ".workbuddy", "binaries", "python", "versions",
        "*", "python.exe")))
    cands.append(sys.executable)
    bare = None
    for exe in cands:
        if not os.path.exists(exe):
            continue
        probe = subprocess.run([exe, "-c", "import openpyxl"], capture_output=True, text=True)
        if probe.returncode != 0:
            bare = exe
            break
    if bare is None:
        raise AssertionError("环境里找不到未安装 openpyxl 的解释器，本用例无法验证（可忽略）")
    with open(os.path.join(WORK, "min.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": {"exam_name": "t", "subjects": []}, "results": {}}, fh)
    p = subprocess.run([bare, EXCEL, "--analysis", os.path.join(WORK, "min.json"),
                        "--out", os.path.join(WORK, "min.xlsx")],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    out = (p.stdout or "") + (p.stderr or "")
    check("Traceback" not in out, "不应抛裸异常，实际：%s" % out[-200:])
    check("pip install openpyxl" in out, "应给出安装指引，实际：%s" % out[-200:])


@case
def test_no_kp_no_fabrication():
    """逐题表没有（或空的）知识点列时**不得凭空造出「未标注」知识点**（曾直接进摘要成假结论）。"""
    rows = [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i] for i in range(1, 7)]

    # ① 逐题表压根没有「知识点」列
    q1 = [["A%d" % i, "数学", 1, 10, 5 + i % 3] for i in range(1, 7)]
    fp = save_xlsx(os.path.join(WORK, "t17a.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分"]], q1)])
    r = run_engine(fp, "--exam-name", "无知识点列", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    R = load_out()["results"]["数学"]
    check(R["knowledge_points"] == [], "不得造出知识点，实际 %s" % R["knowledge_points"])
    check(all((q["kp"] or "") == "" for q in R["questions"]), "题目的 kp 必须留空")
    check(R["questions"], "逐题得分率（维度 3）仍应算出")

    hp = os.path.join(WORK, "t17a.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("未标注" not in htm, "报告里不得出现「未标注」这种编造的知识点")
    check("逐题得分率</h3>" in htm, "维度 3 应出现")
    check("知识点掌握热力图</h3>" not in htm, "无知识点时维度 4 整节不应出现")

    xp = os.path.join(WORK, "t17a.xlsx")
    p = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "Excel 生成应成功，stderr=%s" % (p.stderr or "")[-200:])
    from openpyxl import load_workbook
    wb = load_workbook(xp)
    check(not any(n.startswith("05") for n in wb.sheetnames), "无知识点时 05 表不应生成")
    check(any(n.startswith("04") for n in wb.sheetnames), "有逐题数据时 04 表仍应生成")
    ws = wb["04 逐题得分率"]
    alltxt = " ".join(str(ws.cell(r_, c).value) for r_ in range(1, ws.max_row + 1)
                      for c in range(1, ws.max_column + 1) if ws.cell(r_, c).value)
    check("未标注" not in alltxt, "Excel 里也不得出现「未标注」")
    check("知识点" not in str(ws.cell(3, 3).value or ""), "无知识点数据时 04 表不应保留空的「知识点」列")

    # ② 有「知识点」列但整列为空 → 同样不得编造
    q2 = [["A%d" % i, "数学", 1, 10, 5 + i % 3, ""] for i in range(1, 7)]
    fp2 = save_xlsx(os.path.join(WORK, "t17b.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], q2)])
    r = run_engine(fp2, "--exam-name", "知识点列空", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析")
    an = load_out()
    check(an["results"]["数学"]["knowledge_points"] == [], "整列为空时不得造知识点")
    check(any("整列为空" in n for n in an["data_notes"]), "数据说明要交代知识点列整列为空")

    # ③ 部分题有知识点 → 只统计有归属的，其余不参与（也不算「未标注」）
    q3 = [["A%d" % i, "数学", 1, 10, 5, "有理数"] for i in range(1, 7)] + \
         [["A%d" % i, "数学", 2, 10, 7, ""] for i in range(1, 7)]
    fp3 = save_xlsx(os.path.join(WORK, "t17c.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], q3)])
    r = run_engine(fp3, "--exam-name", "部分知识点", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析")
    an = load_out()
    kps = an["results"]["数学"]["knowledge_points"]
    check([k["kp"] for k in kps] == ["有理数"], "只应聚合有归属的知识点，实际 %s" % [k["kp"] for k in kps])
    check(any("没有知识点归属" in n for n in an["data_notes"]), "要说明有多少题没有知识点归属")


@case
def test_kp_placeholder_is_not_a_kp():
    """「知识点」列**整列只填 -、/ 、「无」这类占位符** → 等同于没有知识点数据。

    这是最容易骗过判据的一种输入：列在、每行都有字，但一个真知识点都没有。
    此前会造出名字叫「-」的知识点，Excel「05 知识点优先级」也就凭空出现了。
    """
    rows = [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i] for i in range(1, 7)]

    # ① 六种占位符各一条 → 知识点数据视为「没有」
    q1 = [["A%d" % i, "数学", 1, 10, 5 + i % 3, ph]
          for i, ph in zip(range(1, 7), ["-", "/", "无", "—", "N/A", "未标注"])]
    fp = save_xlsx(os.path.join(WORK, "t17d.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], q1)])
    r = run_engine(fp, "--exam-name", "占位符输入", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["results"]["数学"]["knowledge_points"] == [],
          "占位符不得被当成知识点，实际 %s" % [k["kp"] for k in an["results"]["数学"]["knowledge_points"]])
    check(an["meta"]["has_knowledge_points"] is False, "meta 也要判成「没有知识点数据」")

    hp = os.path.join(WORK, "t17d.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("知识点掌握热力图</h3>" not in htm, "无知识点数据时维度 4 整节不应出现")

    xp = os.path.join(WORK, "t17d.xlsx")
    p = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "Excel 生成应成功，stderr=%s" % (p.stderr or "")[-200:])
    wb = load_workbook(xp)
    check(not any(n.startswith("05") for n in wb.sheetnames),
          "没有知识点数据时 05 表不得出现，实际 %s" % wb.sheetnames)
    check(any(n.startswith("04") for n in wb.sheetnames), "有逐题数据时 04 表仍应生成")
    nav = " ".join(str(wb["01 阅读说明"].cell(r_, c).value or "")
                   for r_ in range(1, wb["01 阅读说明"].max_row + 1)
                   for c in range(1, 3))
    check("05" not in nav, "「01 阅读说明」的工作表导航里也不得列出 05")

    # ② 占位符与真知识点混排 → 只聚合真的那个，05 表照常生成
    q2 = [["A%d" % i, "数学", 1, 10, 5, "有理数"] for i in range(1, 7)] + \
         [["A%d" % i, "数学", 2, 10, 7, "-"] for i in range(1, 7)]
    fp2 = save_xlsx(os.path.join(WORK, "t17e.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], q2)])
    r = run_engine(fp2, "--exam-name", "占位符混排", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析")
    an = load_out()
    check([k["kp"] for k in an["results"]["数学"]["knowledge_points"]] == ["有理数"],
          "只应聚合真知识点，实际 %s" % [k["kp"] for k in an["results"]["数学"]["knowledge_points"]])
    check(an["meta"]["has_knowledge_points"] is True, "有真知识点时应判为 True")


@case
def test_duplicate_sid_merged_last_wins():
    """重复学号按同一人合并、**取最后一条**（此前会当两个学生：人数虚高、排名出现同一人两次）。"""
    fp = save_xlsx(os.path.join(WORK, "t18.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A1", "张三", "初一(3)班", 60], ["A1", "张三", "初一(3)班", 90],
          ["A2", "李四", "初一(3)班", 80], ["A3", "王五", "初一(3)班", 70]])])
    r = run_engine(fp, "--exam-name", "重复学号", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["student_count"] == 3, "重复学号应合并为 3 人，实际 %d" % an["meta"]["student_count"])
    rk = an["results"]["数学"]["individuals"]["ranking"]
    check(len(rk) == 3, "排名不应出现重复学号，实际 %d 条" % len(rk))
    check(sum(1 for x in rk if x["sid"] == "A1") == 1, "A1 只应出现一次")
    a1 = [x for x in rk if x["sid"] == "A1"][0]
    check(a1["score"] == 90, "应取最后一条成绩（90），实际 %s" % a1["score"])
    check(any("重复学号" in n for n in an["data_notes"]), "数据说明要交代合并了重复学号")


@case
def test_all_blank_subject_column_reported():
    """整列缺考/非数值的学科不得被静默丢弃——要么提示、要么明确失败。"""
    fp = save_xlsx(os.path.join(WORK, "t19.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i, "缺考"] for i in range(1, 7)])])
    # 自动识别：语文整列无分 → 不进分析，但必须说明
    r = run_engine(fp, "--exam-name", "整列缺考", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["subjects"] == ["数学"], "只应分析数学，实际 %s" % an["meta"]["subjects"])
    check(any("语文" in n and ("没有" in n or "缺" in n) for n in an["data_notes"]),
          "数据说明必须点名语文列没有分数，notes=%s" % an["data_notes"])
    # 显式点名一个整列无分的学科 → 明确失败，并说清原因
    r2 = run_engine(fp, "--exam-name", "整列缺考显式", "--subjects", "语文")
    check(r2.returncode != 0, "整列无分的学科应明确失败")
    err = (r2.stderr or "") + (r2.stdout or "")
    check("Traceback" not in err, "不应抛裸异常：%s" % err[-200:])
    check("空" in err or "没有任何可解析的分数" in err, "要说明整列为空，实际：%s" % err[-300:])


@case
def test_broken_narrative_does_not_block():
    """narrative.json 写坏 / 字段类型写错 → 只降级为「无话术」，HTML 必须照常产出。"""
    fp = save_xlsx(os.path.join(WORK, "t20.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文"]],
         [["A%d" % i, "学生%d" % i, "初二(1)班", 60 + i * 3] for i in range(1, 8)])])
    r = run_engine(fp, "--exam-name", "坏话术", "--subjects", "语文", "--full", "语文=100")
    check(r.returncode == 0, "应能完成分析")
    ana = os.path.join(WORK, "out.json")

    # ① 非法 JSON
    bad = os.path.join(WORK, "bad1.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write('{"summary": [')
    hp = os.path.join(WORK, "t20a.html")
    p = subprocess.run([PY, BUILDER, "--analysis", ana, "--narrative", bad, "--out", hp, "--no-excel"],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "narrative 坏不应让渲染失败，实际退出码 %s：%s" % (p.returncode, (p.stderr or "")[-300:]))
    check(os.path.exists(hp), "HTML 必须产出")
    check("Traceback" not in ((p.stdout or "") + (p.stderr or "")), "不应抛裸异常")
    check("警告" in (p.stdout or ""), "应打印降级警告，实际：%s" % (p.stdout or "")[-200:])
    # ② 字段类型写错（improvement 写字符串、summary 写字符串、子项写数字）
    bad2 = os.path.join(WORK, "bad2.json")
    with open(bad2, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"summary": "不是数组", "improvement": "字符串",
                             "subject_notes": {"语文": {"stats": 123, "bands": ["正常"]}},
                             "data_notes_extra": "单条字符串"}, ensure_ascii=False))
    hp2 = os.path.join(WORK, "t20b.html")
    p2 = subprocess.run([PY, BUILDER, "--analysis", ana, "--narrative", bad2, "--out", hp2, "--no-excel"],
                        capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p2.returncode == 0, "类型写错也不应崩，实际 %s：%s" % (p2.returncode, (p2.stderr or "")[-300:]))
    check(os.path.exists(hp2), "HTML 必须产出")
    check("Traceback" not in ((p2.stdout or "") + (p2.stderr or "")), "不应抛裸异常")
    htm2 = open(hp2, encoding="utf-8").read()
    check("单条字符串" not in htm2,
          "报告已无「数据说明」章节，narrative 的 data_notes_extra 不应出现在报告里")
    check("正常" in htm2, "合法的字符串列表型 subject_notes.bands 应被采纳")

    # ③ Excel 结果册已与 narrative 解耦（不再吃 --narrative，也不再承载数据说明）
    xp = os.path.join(WORK, "t20.xlsx")
    p3 = subprocess.run([PY, EXCEL, "--analysis", ana, "--out", xp],
                        capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p3.returncode == 0, "Excel 生成应成功，实际 %s" % p3.returncode)
    check(os.path.exists(xp), "Excel 文件必须产出")
    check("Traceback" not in ((p3.stdout or "") + (p3.stderr or "")), "不应抛裸异常")

    # ④ 坏 narrative 里合法的 data_notes_extra 也不再进结果册（报告与 Excel 都不承载数据说明）
    from openpyxl import load_workbook
    txt = " ".join(str(c.value) for w in load_workbook(xp).worksheets
                   for row in w.iter_rows() for c in row if c.value)
    check("单条字符串" not in txt,
          "narrative 的 data_notes_extra 已废弃，不应出现在 Excel 结果册任何工作表里")


@case
def test_single_exam_history_falls_back():
    """历次表只有 1 次考试 → 自动退回横截面分层，不冒充「个体追踪（历次成绩）」。"""
    fp = save_xlsx(os.path.join(WORK, "t21.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i] for i in range(1, 7)]),
        ("历次", [["学号", "考试", "总分"]],
         [["A%d" % i, "第1次月考", 500 + i] for i in range(1, 7)])])
    r = run_engine(fp, "--exam-name", "单次历次", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    ind = an["results"]["数学"]["individuals"]
    check(ind["mode"] == "cross-section", "单次历次应退回横截面，实际 %s" % ind["mode"])
    check(not ind["history"], "不应有 history 行")
    check("进步榜" not in ind["lists"], "单次考试不应产生进步榜")
    check(any("只包含 1 次考试" in n for n in an["data_notes"]), "数据说明要交代原因")
    hp = os.path.join(WORK, "t21.html")
    subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                    "--out", hp, "--no-excel"], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    htm = open(hp, encoding="utf-8").read()
    check("个体追踪（横截面分层）" in htm, "章节标题应写横截面分层")
    check("个体追踪（历次成绩）" not in htm, "不应写「历次成绩」")


@case
def test_missing_focus_class_label():
    """--focus-class 指定不存在的班级时，封面标签不得写这个班（统计范围是全部样本）。"""
    fp = save_xlsx(os.path.join(WORK, "t22.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i] for i in range(1, 5)] +
         [["B%d" % i, "他班%d" % i, "初一(4)班", 65 + i] for i in range(1, 4)])])
    r = run_engine(fp, "--exam-name", "班级不存在", "--subjects", "数学",
                   "--focus-class", "初一(9)班", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["focus_class"] == "全部样本",
          "范围已回退全部样本，封面标签不应写不存在的班，实际 %s" % an["meta"]["focus_class"])
    check(an["meta"]["focus_class_requested"] == "初一(9)班", "要保留用户原本指定的班级名")
    check(an["meta"]["individual_scope"] == "全部样本", "个体名单范围应为全部样本")
    hp = os.path.join(WORK, "t22.html")
    subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                    "--out", hp, "--no-excel"], capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    htm = open(hp, encoding="utf-8").read()
    check("分析班级：全部样本" in htm, "封面「分析班级」应写全部样本")
    check(any("初一(9)班" in n and "不存在" in n for n in an["data_notes"]), "数据说明要解释原因")


@case
def test_partial_subjects_total_label():
    """只分析部分学科时，结果册里不得写「全科总分」（那是所选学科合计）。"""
    fp = save_xlsx(os.path.join(WORK, "t23.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文", "英语"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 70 + i, 75 + i, 80 + i] for i in range(1, 7)])])
    FULL = ["--full", "数学=100,语文=100,英语=100"]

    r = run_engine(fp, "--exam-name", "部分学科", "--subjects", "数学,语文", *FULL)
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["partial_subjects"] is True, "应识别为「只分析了部分学科」")
    check(an["meta"]["total_label"] == "所选学科总分", "术语应为「所选学科总分」，实际 %s" % an["meta"]["total_label"])
    check(any("所选学科" in n for n in an["data_notes"]), "数据说明要解释这不是学校层面的全科总分")
    xp = os.path.join(WORK, "t23a.xlsx")
    subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                   capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    from openpyxl import load_workbook
    ws = load_workbook(xp)["06 学生成绩与排名"]
    hdr = [str(ws.cell(3, c).value or "") for c in range(1, ws.max_column + 1)]
    check("所选学科总分" in hdr, "06 表头应为「所选学科总分」，实际 %s" % hdr)
    check("全科总分" not in hdr, "06 表头不应出现「全科总分」")

    # 全科都分析了 → 恢复「全科总分」
    r2 = run_engine(fp, "--exam-name", "全科", *FULL)
    check(r2.returncode == 0, "应能完成分析")
    an2 = load_out()
    check(an2["meta"]["partial_subjects"] is False, "三科全分析时不应标 partial")
    check(an2["meta"]["total_label"] == "全科总分", "全科时应写「全科总分」")


@case
def test_no_appendix_in_report():
    """正式报告里不得出现「附录 · 交付物与脚本说明」这类内部交付信息。

    老师/家长看的报告只讲教学结论；Excel 表数、文件名、脚本路径、配色代码、复用命令
    属于内部信息，只能在对话回复里交代（用户要求：2026-10-08）。
    """
    fp = save_xlsx(os.path.join(WORK, "t24.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 60 + i % 40, 65 + i % 35] for i in range(1, 26)])])
    r = run_engine(fp, "--exam-name", "期末质量检测", "--subjects", "数学,语文",
                   "--full", "数学=100,语文=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    hp = os.path.join(WORK, "t24.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    for bad in ("附录", "交付物与脚本说明", "exam_analysis.py", "report_builder.py",
                "build_excel.py", "analysis.json", "结果册.xlsx", "图表配色",
                "individuals.", "results."):
        check(bad not in htm, "正式报告里不应出现内部交付信息「%s」" % bad)
    check("id='appendix'" not in htm and "#appendix" not in htm, "不应残留附录锚点")
    # 正文要正常结束在「教学改进建议」，且仍有页脚
    check("教学改进建议" in htm, "正文应包含教学改进建议")
    check("</footer>" in htm, "报告末尾应保留一行页脚")


@case
def test_report_drops_datanotes_section_and_cover_fields():
    """封面内部字段与整节「数据说明」都不进报告；关键提示不丢（章首小字 / 摘要 ⚠️ / Excel 01）。"""
    rows = [["A%d" % i, "学生%d" % i, "初一(3)班", 60 + i, 70 + i] for i in range(1, 7)]
    rows.append(["A9", "缺考者", "初一(3)班", "缺考", 71])
    fp = save_xlsx(os.path.join(WORK, "t25.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]], rows)])
    # 语文不给满分（最高 76 → 唯一 100 分制，章首要标「待确认」）；数学显式给，只为跑通
    r = run_engine(fp, "--exam-name", "范围字段", "--subjects", "数学,语文", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    hp = os.path.join(WORK, "t25.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()

    # ① 封面不再列「满分设定 / 数据来源」这类内部字段
    # （「统计范围」不在此列——它是维度 3/4 小字的正常用语，本来就要出现在正文里）
    for bad in ("满分设定", "数据来源"):
        check(bad not in htm, "封面不应再有「%s」" % bad)
    # ② 整个「数据说明」章节不再出现（含剔除名单表与「数据完整」兜底文案）
    for bad in ("数据说明", "datanotes", "未纳入统计的学生", "待确认的满分", "数据完整，未发现"):
        check(bad not in htm, "报告不应再有「%s」" % bad)
    # ②b 内部术语不得出现在报告里（用户 2026-10-08 要求全库清掉该词）
    check((chr(0x53e3) + chr(0x5f84)) not in htm, "报告里不得出现内部术语")
    # ③ 但关键提示不能丢：章首满分小字仍标「待确认」，封面基本字段还在
    check("待确认" in htm, "章首满分小字仍要标「待确认」")
    check("样本人数" in htm and "考试名称" in htm, "封面基本字段应保留")

    # ④ 剔除名单改由 Excel「01 阅读说明」逐个点名
    xp = os.path.join(WORK, "t25a.xlsx")
    p2 = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                        capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p2.returncode == 0, "Excel 生成应成功")
    from openpyxl import load_workbook
    ws = load_workbook(xp)["01 阅读说明"]
    txt = " ".join(str(ws.cell(rr, cc).value) for rr in range(1, ws.max_row + 1)
                   for cc in (1, 2, 3) if ws.cell(rr, cc).value)
    check("缺考者" in txt, "被剔除的学生要在 Excel「01 阅读说明」里点名")


@case
def test_excel_drops_policy_and_notes_sections():
    """Excel「01 阅读说明」不得再有 满分设定 / 分数线设定 / 数据来源 / 数据说明 / 未生成的工作表
    / 主表工作表 / 统计范围。

    用户要求 2026-10-08：结果册只放分析结果与教学要用的事实；统计范围、来源、数据质量交代
    属于内部信息，只在 analysis.json、命令行输出与对话交付说明里出现。
    同时确认「设定信息没丢，只是换了位置」——满分与三条分数线仍逐列写在「02 学科总览」。
    """
    rows = [["A%d" % i, "学生%d" % i, "初一(3)班", 60 + i, 70 + i] for i in range(1, 7)]
    rows.append(["A9", "缺考者", "初一(3)班", "缺考", 71])
    fp = save_xlsx(os.path.join(WORK, "t26.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]], rows)])
    # 语文不给满分（最高 76 → 唯一 100 分制，会落进 meta.full_to_confirm，产生满分相关 data_note）
    r = run_engine(fp, "--exam-name", "结果册瘦身", "--subjects", "数学,语文", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["data_notes"], "本用例需要 data_notes 非空（缺考者 + 满分待确认）")

    xp = os.path.join(WORK, "t26.xlsx")
    p = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "Excel 生成应成功，stderr=%s" % (p.stderr or "")[-200:])
    from openpyxl import load_workbook
    wb = load_workbook(xp)

    # ① 被点名的栏目一个都不能有（按「项目」列的标签精确判定）
    labels = [str(wb["01 阅读说明"].cell(rr, 1).value)
              for rr in range(1, wb["01 阅读说明"].max_row + 1)
              if wb["01 阅读说明"].cell(rr, 1).value]
    for bad in ("满分设定", "分数线设定", "数据来源", "未生成的工作表",
                "主表工作表", "统计范围"):
        check(bad not in labels, "阅读说明里不应再有「%s」，实际 %s" % (bad, labels))
    check(not any(x.startswith("数据说明") for x in labels),
          "阅读说明里不应再有「数据说明」栏目，实际 %s" % labels)
    # 内部信息（源文件名 / 工作表名）也不该从别的行漏出来
    sheet_name = str(an["meta"].get("source_sheet") or "")
    check(sheet_name and sheet_name not in labels,
          "工作表名「%s」属内部信息，不该作为栏目出现在阅读说明里：%s" % (sheet_name, labels))
    # 「学生名单范围」只讲对账事实（多少人、是否全计入），不复述合计列的设定
    pairs = {str(wb["01 阅读说明"].cell(rr, 1).value): str(wb["01 阅读说明"].cell(rr, 2).value)
             for rr in range(1, wb["01 阅读说明"].max_row + 1)
             if wb["01 阅读说明"].cell(rr, 1).value}
    check((chr(0x53e3) + chr(0x5f84)) not in pairs.get("学生名单范围", ""),
          "「学生名单范围」不该复述设定，实际：%s" % pairs.get("学生名单范围"))

    # ② data_notes 全文不得落进任何工作表（不只是 01）
    all_txt = " ".join(str(c.value) for w in wb.worksheets
                       for row in w.iter_rows() for c in row if c.value)
    for n in an["data_notes"]:
        check(n not in all_txt, "data_notes 不应写进结果册：%s" % n[:28])
    # ②b 内部术语不得出现在结果册任何单元格里
    check((chr(0x53e3) + chr(0x5f84)) not in all_txt, "结果册里不得出现内部术语")

    # ③ 设定信息没丢：满分 / 及格线 / 优秀线 / 低分线仍逐列写在「02 学科总览」
    hdr = [str(c.value) for c in wb["02 学科总览"][3]]
    for col in ("满分", "及格线", "优秀线", "低分线"):
        check(col in hdr, "02 学科总览里应保留「%s」列，实际 %s" % (col, hdr))

    # ④ 对账要用的信息仍在：被剔除学生逐个点名
    check("缺考者" in all_txt, "剔除名单仍要在「01 阅读说明」逐个点名（班主任对名单要用）")
    # ⑤ 安全提示仍在：满分未经用户确认时置顶点名（满分错了整册的数据基准都错）
    check("待确认的满分" in all_txt, "满分待确认时必须仍在阅读说明里置顶点名")


@case
def test_no_internal_jargon_in_skill_files():
    """技能内所有交付文案、脚本与文档都不得再出现某个内部术语（用户 2026-10-08 要求）。

    理由：交付物里出现它会让老师看到内部术语；文档里出现则会被下一次照抄进报告。
    该词用码点拼出来，免得这个用例自己命中自己。
    """
    kw = chr(0x53E3) + chr(0x5F84)
    root = os.path.dirname(HERE)
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", ".idea")]
        for fn in filenames:
            if not fn.endswith((".md", ".py", ".txt", ".yaml", ".yml", ".json")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    txt = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            if kw in txt:
                hits.append(os.path.relpath(p, root))
    check(not hits, "以下文件仍含该内部术语，请改写：%s" % hits)


@case
def test_delivered_wording_has_no_jargon():
    """真实链路跑一遍：命令行输出里也不得出现该内部术语（老师会看到这些提示）。"""
    fp = save_xlsx(os.path.join(WORK, "t27.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]],
         [["A%d" % i, "学生%d" % i, "初一(3)班", 60 + i, 70 + i] for i in range(1, 5)])])
    r = run_engine(fp, "--exam-name", "用语检查", "--subjects", "数学,语文",
                   "--focus-class", "初一(3)班", "--full", "数学=100,语文=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    kw = chr(0x53E3) + chr(0x5F84)
    out = (r.stdout or "") + (r.stderr or "")
    check(kw not in out, "命令行输出里不得出现内部术语，实际输出片段：%s"
          % [ln for ln in out.splitlines() if kw in ln][:3])


@case
def test_two_level_questions_and_class_matrix():
    """维度 3 的两层逐题统计 + **各班每题得分率**（用户要求 2026-10-10/11）。

    ① 班级层（本班）与年级层（全部样本）数字各自正确、互不相同；
    ② 每题带 by_class：每个班级在该题上的得分率；
    ③ **不再有学生个体矩阵**（小题分分析不下到每个学生）；
    ④ Excel：04 表为双层且带各班列；不再有「09/10 学生小题」两张表。
    """
    rows_m, rows_q = [], []
    for tag, cls, sc in (("1", "初一(1)班", 8), ("2", "初一(2)班", 2)):
        for i in range(1, 4):
            sid = "S%s0%d" % (tag, i)
            rows_m.append([sid, "学生%s0%d" % (tag, i), cls, 70])
            for q in (1, 2):
                rows_q.append([sid, "数学", q, 10, sc, "集合"])
    fp = save_xlsx(os.path.join(WORK, "t28.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows_m),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], rows_q)])
    r = run_engine(fp, "--exam-name", "两层逐题", "--subjects", "数学",
                   "--focus-class", "初一(1)班", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["two_level_questions"] is True, "应标记为两层逐题")
    q1 = an["results"]["数学"]["questions"][0]
    check(abs(q1["rate"] - 0.8) < 1e-6, "班级层得分率应为 0.8，实际 %s" % q1["rate"])
    check(abs(q1["rate_all"] - 0.5) < 1e-6, "年级层得分率应为 0.5，实际 %s" % q1["rate_all"])
    check(q1["n"] == 3 and q1["n_all"] == 6,
          "作答人数应为 3 / 6，实际 %s/%s" % (q1["n"], q1["n_all"]))

    byc = {c["cls"]: c for c in q1.get("by_class") or []}
    check(set(byc) == {"初一(1)班", "初一(2)班"}, "应逐班给出该题得分率，实际 %s" % sorted(byc))
    check(abs(byc["初一(1)班"]["rate"] - 0.8) < 1e-6, "一班该题得分率应为 0.8")
    check(abs(byc["初一(2)班"]["rate"] - 0.2) < 1e-6, "二班该题得分率应为 0.2")
    check(byc["初一(1)班"]["n"] == 3 and byc["初一(2)班"]["n"] == 3,
          "各班作答人数应各 3 人")

    # 学生个体小题矩阵已按要求下线：引擎里不应再有这个字段
    check("student_questions" not in an["results"]["数学"], "小题分分析不应再落到每个学生")
    check("student_questions_status" not in an["meta"], "meta 不应再有学生个体小题状态")

    xp = os.path.join(WORK, "t28.xlsx")
    p = subprocess.run([PY, EXCEL, "--analysis", os.path.join(WORK, "out.json"), "--out", xp],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "Excel 生成应成功，stderr=%s" % (p.stderr or "")[-200:])
    from openpyxl import load_workbook
    wb = load_workbook(xp)
    names = wb.sheetnames
    check(not any("学生小题" in n for n in names), "不应再有学生小题表，实际 %s" % names)
    check("09 年级班级排名" in names, "应有年级班级排名表，实际 %s" % names)
    ws4 = wb["04 逐题得分率"]
    hdr = [ws4.cell(3, c).value for c in range(1, ws4.max_column + 1)]
    check("本班得分率" in hdr and "年级得分率" in hdr,
          "04 表应为班级 / 年级双栏，实际表头 %s" % hdr)
    check("初一(1)班得分率" in hdr and "初一(2)班得分率" in hdr,
          "04 表应逐班给出得分率列，实际表头 %s" % hdr)


@case
def test_no_sid_no_class_detail():
    """逐题表没有「学号」列 → 只出班级 / 年级两层（同源），也不逐班分列（不造假、不摆空表）。"""
    fp = save_xlsx(os.path.join(WORK, "t29.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], [["A1", "赵一", "初一(3)班", 70]]),
        ("逐题", [["学科", "题号", "满分", "得分", "知识点"]],
         [["数学", 1, 10, 7, "集合"], ["数学", 2, 10, 6, "函数"]])])
    r = run_engine(fp, "--exam-name", "无学号逐题", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["two_level_questions"] is False, "无学号时不应标成两层")
    q0 = an["results"]["数学"]["questions"][0]
    check(not q0.get("by_class"), "无学号时无法分班，by_class 应为空")
    check(an["results"]["数学"]["questions"], "班级 / 年级层的逐题统计仍应生成")


@case
def test_single_class_shows_one_level_only():
    """单班样本 + 逐题表带学号：班级层与年级层是**同一批人** → 只呈现一套，不摆两份重复表。"""
    rows_m, rows_q = [], []
    for i in range(1, 5):
        sid = "B%02d" % i
        rows_m.append([sid, "学生%d" % i, "初三(1)班", 80])
        for q in (1, 2):
            rows_q.append([sid, "数学", q, 10, 8, ""])
    fp = save_xlsx(os.path.join(WORK, "t30.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows_m),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], rows_q)])
    r = run_engine(fp, "--exam-name", "单班单层", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    check(an["meta"]["two_level_questions"] is False, "单班样本不应标成两层（两层是同一批人）")
    check(an["results"]["数学"]["questions"][0]["two_scope"] is False,
          "单班样本 two_scope 应为 False")
    check(not an.get("grade_overview"), "单班样本不生成「年级班级排名」")


@case
def test_four_rates_are_exclusive_partition():
    """四率（优秀 / 良好 / 合格 / 不合格）必须互斥且相加 100%（用户要求 2026-10-11）。

    分档：优秀 ≥85%｜良好 70–85%｜合格 60–70%｜不合格 <60%。
    构造 10 人：分数率 0.9/0.9/0.8/0.8/0.65/0.65/0.5/0.5/0.5/0.5
      → 优秀 2、良好 2、合格 2、不合格 4（各占 20%/20%/20%/40%）。
    """
    vals = [90, 90, 80, 80, 65, 65, 50, 50, 50, 50]
    rows = [["A%02d" % i, "学生%02d" % i, "初一(1)班", v] for i, v in enumerate(vals, 1)]
    fp = save_xlsx(os.path.join(WORK, "t31.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "四率", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    st = an["results"]["数学"]["stats"]
    for key, exp in (("excellent_rate", 0.2), ("good_rate", 0.2),
                     ("qualified_rate", 0.2), ("fail_rate", 0.4)):
        check(abs(st[key] - exp) < 1e-6, "%s 应为 %.2f，实际 %s" % (key, exp, st[key]))
    total = st["excellent_rate"] + st["good_rate"] + st["qualified_rate"] + st["fail_rate"]
    check(abs(total - 1.0) < 1e-6, "四率相加必须为 100%%，实际 %s" % total)
    # 累计的及格率（≥60%）与四率不同层：本用例 = 0.6
    check(abs(st["pass_rate"] - 0.6) < 1e-6, "及格率（≥60%%）应为 0.6，实际 %s" % st["pass_rate"])


@case
def test_grade_overview_ranks_classes():
    """年级层：总分按班级排名 + 每个学科按班级排名 + 全年级四率（用户要求 2026-10-11）。"""
    rows = []
    # 一班总分明显高、二班居中、三班最低；数学上二班反超一班（验证「学科排名 ≠ 总分排名」）
    plan = [("初一(1)班", 99, 50), ("初一(2)班", 70, 60), ("初一(3)班", 55, 40)]
    for cls, m, c in plan:
        for i in range(1, 5):
            rows.append(["%s-%d" % (cls, i), "%s学生%d" % (cls, i), cls, m, c])
    fp = save_xlsx(os.path.join(WORK, "t32.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "年级排名", "--subjects", "语文,数学",
                   "--full", "语文=100,数学=100", "--focus-class", "初一(1)班")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    go = an["grade_overview"]
    check(bool(go), "多班样本应生成年级层总览")
    tot = {x["cls"]: x["rank"] for x in go["by_total"]}
    check(tot.get("初一(1)班") == 1 and tot.get("初一(3)班") == 3,
          "总分排名应为一班第 1、三班第 3，实际 %s" % tot)
    math_rank = {x["cls"]: x["rank"] for x in go["by_subject"]["数学"]}
    check(math_rank.get("初一(2)班") == 1,
          "数学应二班第 1（学科排名可与总分排名不同），实际 %s" % math_rank)
    gs = go["grade_stats"]["数学"]
    check(gs["count"] == 12, "全年级数学有效人数应为 12，实际 %s" % gs["count"])
    check(abs(gs["score_rate"] - 0.5) < 1e-6,
          "全年级数学得分率应为 (50+60+40)/3/100=0.5，实际 %s" % gs["score_rate"])

    # 渲染侧（用户要求 2026-10-11）：② 格内显示**平均分**而不是得分率；
    # ④ 分数段写成**实际分数区间**（不是百分数），且不留「满分 分」这种拼接残渣。
    hp = os.path.join(WORK, "t32.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("数学平均分（名次）" in htm, "班级学科排名表头应写「平均分（名次）」")
    check("得分率（名次）" not in htm, "不应再用「得分率（名次）」做表头")
    # 分数段一律显示**具体分数区间**（用户要求 2026-10-11）
    check("满分 分" not in htm, "分数区间末档不应拼成「满分 分」")
    check("90 – 100 分" in htm, "分数段应换算成实际分数区间（如「90 – 100 分」）")
    check("分数段（分数）" in htm, "分数段列应显示具体分数")
    check("分数段（占满分比例）" not in htm, "不应再用「分数段（占满分比例）」做表头")
    # ④ 全年级各学科分数段：按学科分别成表，表上方标学科名
    check("【语文】分数段分布" in htm and "【数学】分数段分布" in htm,
          "全年级分数段应按学科分别成表并在表上方标学科名")
    # 维度 5 对比分析：逐班分数段表也显示具体分数区间
    check("初一(1)班 分数段分布" in htm, "维度 5 应逐班给出分数段分布表")


@case
def test_history_summary_grade_and_class():
    """历次成绩对比：历次年级总分 + 历次各科四率 + 历次班级（用户要求 2026-10-11）。"""
    hist = []
    for i in range(1, 5):
        sid = "H%02d" % i
        cls = "初二(1)班" if i <= 2 else "初二(2)班"
        for exam, delta in (("第1次月考", 0), ("第2次月考", 6), ("期中考试", 12)):
            hist.append([sid, "学生%d" % i, cls, exam,
                         exam, 70 + delta + i, 72 + delta + i, 74 + delta + i])
    fp = save_xlsx(os.path.join(WORK, "t33.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "语文", "数学"]],
         [["H%02d" % i, "学生%d" % i, "初二(1)班" if i <= 2 else "初二(2)班", 80, 80]
          for i in range(1, 5)]),
        ("历次", [["学号", "姓名", "班级", "考试", "序号", "总分", "语文", "数学"]], hist)])
    r = run_engine(fp, "--exam-name", "历次对比", "--subjects", "语文,数学",
                   "--full", "语文=100,数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    an = load_out()
    hs = an["history_summary"]
    check(bool(hs), "有历次表应生成历次对比")
    check(hs["has_subject_detail"] is True, "历次表带学科列时应标记为有学科明细")
    check(hs["exams"] == ["第1次月考", "第2次月考", "期中考试"],
          "考试次序应正确，实际 %s" % hs["exams"])
    gt = hs["grade"]["total"]
    check(len(gt) == 3 and gt[0]["mean"] < gt[-1]["mean"], "历次年级总分应逐次上升")
    gmath = hs["grade"]["subjects"]["数学"]
    check(len(gmath) == 3, "历次年级数学应有 3 次记录，实际 %d" % len(gmath))
    check(abs(gmath[0]["mean"] - 76.5) < 1e-6,
          "首次数学均分应为 (75+76+77+78)/4=76.5，实际 %s" % gmath[0]["mean"])
    check(set(hs["by_class"]) == {"初二(1)班", "初二(2)班"},
          "历次班级应分班给出，实际 %s" % sorted(hs["by_class"]))
    check("数学" in hs["by_class"]["初二(1)班"]["subjects"], "历次班级应有各学科数据")
    check(all("fail_rate" in x for x in gmath), "历次各科应给出四率")

    # 渲染侧（用户要求 2026-10-11）：历次年级各学科四率、历次班级各学科
    # 都**按学科分别成表**并在表上方标学科名；总分单独一张表。
    hp = os.path.join(WORK, "t33.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    check("【语文】历次四率</h4>" in htm and "【数学】历次四率</h4>" in htm,
          "历次年级各学科四率应按学科分别成表并在表上方标学科名")
    check("总分（各班）" in htm, "历次班级应有总分表")
    check("【语文】历次四率（各班）" in htm and "【数学】历次四率（各班）" in htm,
          "历次班级各学科应按学科分别成表并在表上方标学科名")
    check("科目" not in htm.split("（三）历次班级")[-1].split("</table>")[0],
          "历次班级表不应再混一列「科目」")
    # 序号体系（用户要求 2026-10-11）：h2 → 一、｜h3 → （一）｜h4 → 1.
    check(re.search(r"<h2 id='history'>[一二三四五六七八九十]+、历次成绩对比（年级 / 班级）</h2>",
                    htm), "章节标题应用中文序号「一、」（非「1.」）")
    check(re.search(r"<h3>（[一二三四五六七八九十]+）历次班级 · 总分与各学科</h3>", htm),
          "h3 层级应用「（三）」这种中文括号序号")
    check(re.search(r"<h2 id='improve'>[一二三四五六七八九十]+、教学改进建议</h2>", htm),
          "教学改进建议章节也应用中文序号")
    check(not re.search(r"<h[23]>\d+\. ", htm) and ">① " not in htm
          and not re.search(r"<h[234]>[一二三四五六七八九十]+、", htm),
          "不应残留旧序号（h2/h3 的阿拉伯点号 / 带圈数字 / 手写中文序号）")


@case
def test_grade_question_table_sorted_by_qno():
    """维度 3 年级层逐题表：题号列按**题号升序**排列（用户要求 2026-10-11）。

    数据里故意乱序给题号（10 / 2 / 1 / 3），渲染后年级层表格必须按 1 → 2 → 3 → 10 排。
    """
    rows_m, rows_q = [], []
    for tag, cls in (("1", "初一(1)班"), ("2", "初一(2)班")):
        for i in range(1, 4):
            sid = "Q%s0%d" % (tag, i)
            rows_m.append([sid, "学生%s0%d" % (tag, i), cls, 70])
            for q in (10, 2, 1, 3):
                rows_q.append([sid, "数学", q, 10, 5, "集合"])
    fp = save_xlsx(os.path.join(WORK, "t34.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows_m),
        ("逐题", [["学号", "学科", "题号", "满分", "得分", "知识点"]], rows_q)])
    r = run_engine(fp, "--exam-name", "题号排序", "--subjects", "数学",
                   "--focus-class", "初一(1)班", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    hp = os.path.join(WORK, "t34.html")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--no-excel"], capture_output=True, text=True,
                       encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])
    htm = open(hp, encoding="utf-8").read()
    seg = htm.split("年级层 · 逐题得分率（全部样本")[-1].split("</table>")[0]
    order = re.findall(r"第(\d+)题", seg)
    check(order == ["1", "2", "3", "10"],
          "年级层逐题表应按题号升序（1,2,3,10），实际 %s" % order)
    # 顺带校验序号体系：同一个用例里 h4 依次为 1./2.（h3 为「（三）逐题得分率」）
    check("<h4>1. 班级层 · 逐题得分率（初一(1)班）</h4>" in htm
          and "<h4>2. 年级层 · 逐题得分率（全部样本 6 人）</h4>" in htm,
          "h4 层级应从 1. 起顺序编号")
    check(re.search(r"<h3 id='数学-3'>（[一二三四五六七八九十]+）逐题得分率</h3>", htm)
          is not None, "h3 层级应用中文括号序号（如「（三）逐题得分率」）")
    check(not re.search(r"<h3[^>]*>[^<]*维度", htm),
          "h3 标题里不应再重复写「维度 N ·」（与新序号功能重复会造成错位）")

    # 班级层同样按**题号升序**（用户要求 2026-10-11：所有含题号列的表格）
    seg_c = htm.split("班级层 · 逐题得分率")[-1].split("</table>")[0]
    order_c = re.findall(r"第(\d+)题", seg_c)
    check(order_c == ["1", "2", "3", "10"],
          "班级层逐题表也应按题号升序（1,2,3,10），实际 %s" % order_c)
    # 讲评优先级仍在：表里应有 P1…（只是不再靠行序表达）
    check("P1" in seg_c and "P4" in seg_c, "班级层表仍应标注讲评优先级 P1…Pn")

    # 高低分清单不套 <b>（用户要求 2026-10-11：「第6题（共性错题）」直接写）
    check("<li><b>第" not in htm, "得分高低清单项不应把「第N题（等级）」套上 <b>")
    # 也不得自带 <li>（用户要求 2026-10-11：「<li> 这个符号去掉，HTML 和 PDF 都改」）——
    # ulist() 会给每项加壳并先 esc()，清单项自己再拼一层 <li> 就会被转义成字面文本印在页面上。
    check("&lt;li&gt;" not in htm, "报告里不得出现被转义成字面文本的 <li>（清单项自带 <li> 导致双重包裹）")
    check("&lt;/li&gt;" not in htm and "&lt;b&gt;" not in htm,
          "报告里不得出现任何被转义成字面文本的标签")
    # 目录不用 <ol>（<ol> 会自动生成 1./2./3. 序号；条目里已有「一、二、…」）
    toc_seg = htm.split("<nav class='toc'>")[-1].split("</nav>")[0]
    check("<ol>" not in toc_seg and "<ul>" in toc_seg,
          "目录应改用 <ul>（去掉自动生成的 1./2./3. 序号）")
    # 报告不指向「随附的结果册」——PDF 是单独一份，手上不一定有那份 xlsx
    check("随附的结果册" not in htm,
          "报告不应写「完整数据见随附的结果册」（PDF 里并没有那份 xlsx）")


@case
def test_student_id_column_follows_data():
    """学生名单表：姓名与学号**各占一列**；数据没有真学号时「学号」列整列不出现。

    用户要求 2026-10-11。同时守住「不拿 #N 兜底编号冒充学号」——
    此前没有学号列时，结果册 06 的「学号」列会显示 #1/#2/#3，看起来像学号但其实不是。
    """
    rows = [["S%02d" % i, "学生%02d" % i, "初一(1)班", 60 + i, 70 + i] for i in range(1, 9)]
    fp_with = save_xlsx(os.path.join(WORK, "t39a.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]], rows)])
    fp_without = save_xlsx(os.path.join(WORK, "t39b.xlsx"), [
        ("成绩", [["姓名", "班级", "数学", "语文"]], [r[1:] for r in rows])])
    for fp, tag, want in ((fp_with, "有学号", True), (fp_without, "无学号", False)):
        # 考试名不能带「学号」二字，否则会把它自己带进报告、污染下面的断言（踩过一次）
        # 两科：单科时结果册不生成「08 学生学科均衡性」（偏科诊断至少需要两科），这里要断言 08 的表头
        r = run_engine(fp, "--exam-name", "名单测试", "--subjects", "数学,语文",
                       "--full", "数学=100,语文=100")
        check(r.returncode == 0,
              "[%s] 应能完成分析，stderr=%s" % (tag, (r.stderr or "")[-200:]))
        an = load_out()
        check(an["meta"].get("has_student_id") is want,
              "[%s] meta.has_student_id 应为 %s" % (tag, want))
        hp = os.path.join(WORK, "t39_%s.html" % tag)
        xp = os.path.join(WORK, "t39_%s.xlsx" % tag)
        p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                            "--out", hp, "--excel-out", xp, "--excel"],
                           capture_output=True, text=True, encoding="utf-8", cwd=WORK)
        check(p.returncode == 0,
              "[%s] 渲染应成功，stderr=%s" % (tag, (p.stderr or "")[-200:]))
        htm = open(hp, encoding="utf-8").read()
        # 只看表格单元格里的「学号」（表头），避免被正文文案里的字样误判
        cell = re.search(r">\s*学号\s*<", htm) is not None
        check(cell == want,
              "[%s] 报告学生排名表的「学号」列应%s出现" % (tag, "该" if want else "不"))
        check(re.search(r">#\d+<", htm) is None,
              "[%s] 不应出现 #N 兜底编号冒充学号" % tag)
        wb = load_workbook(xp)
        for sheet in ("06 学生成绩与排名", "08 学生学科均衡性"):
            hdr = [c.value for c in wb[sheet][3]]
            check(("学号" in hdr) == want,
                  "[%s] %s 表头的「学号」列应%s出现，实际表头=%s"
                  % (tag, sheet, "该" if want else "不", hdr[:5]))


@case
def test_balance_sheet_needs_two_subjects():
    """单科分析（模式 A）时结果册不生成「08 学生学科均衡性」。

    偏科诊断 = 个人最强科得分率 − 最弱科得分率；只有一科时人人都是 0，
    生成出来是一张只有表头、一行数据都没有的空表。缺数据的表整表不生成，
    与 04/05/09/10 保持一致（01 阅读说明的工作表导航里也不出现 08）。
    """
    fp = save_xlsx(os.path.join(WORK, "t45.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学", "语文"]],
         [["S%02d" % i, "学生%02d" % i, "初一(1)班", 60 + i, 70 + i] for i in range(1, 9)])])
    for subs, full, want in (("数学", "数学=100", False), ("数学,语文", "数学=100,语文=100", True)):
        r = run_engine(fp, "--exam-name", "均衡测试", "--subjects", subs, "--full", full)
        check(r.returncode == 0, "[%s] 应能完成分析，stderr=%s" % (subs, (r.stderr or "")[-200:]))
        xp = os.path.join(WORK, "t45_%s.xlsx" % want)
        p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                            "--out", os.path.join(WORK, "t45_%s.html" % want),
                            "--excel-out", xp, "--excel"],
                           capture_output=True, text=True, encoding="utf-8", cwd=WORK)
        check(p.returncode == 0, "[%s] 渲染应成功，stderr=%s" % (subs, (p.stderr or "")[-200:]))
        wb = load_workbook(xp)
        has08 = "08 学生学科均衡性" in wb.sheetnames
        check(has08 == want,
              "[%s] 「08 学生学科均衡性」应%s生成，实际工作表=%s"
              % (subs, "该" if want else "不", wb.sheetnames))
        nav_txt = "\n".join(str(c.value) for row in wb["01 阅读说明"].iter_rows() for c in row
                            if c.value is not None)
        check(("08 学生学科均衡性" in nav_txt) == want,
              "[%s] 「01 阅读说明」的导航里也应%s出现 08" % (subs, "该" if want else "不"))


@case
def test_excel_band_scores_and_pdf_export():
    """交付细节（用户要求 2026-10-11）：

    ① 结果册「03 分数段分布」以**具体分数**为主列——「分数段（分数）」排在「分段（占满分比例）」之前，
       末档按 min(hi, 1) 收成满分、写成「90 – 100 分」，不能拼成「满分 分」；
    ② 结果册单元格不留 Markdown 的 ``**``（Excel 不渲染，只会显示成字面星号）；
    ③ PDF 必须关掉浏览器页眉页脚——否则每页页脚会印出 ``file:///C:/…`` 的本地路径与打印时间。
    """
    rows = [["S%02d" % i, "学生%02d" % i, "初一(1)班" if i <= 5 else "初一(2)班", 60 + i * 4]
            for i in range(1, 11)]
    fp = save_xlsx(os.path.join(WORK, "t40in.xlsx"), [
        ("成绩", [["学号", "姓名", "班级", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "分段与导出", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    hp = os.path.join(WORK, "t40.html")
    xp = os.path.join(WORK, "t40.xlsx")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", hp, "--excel-out", xp, "--excel", "--pdf"],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-200:])

    wb = load_workbook(xp)
    hdr = [c.value for c in wb["03 分数段分布"][3]]
    check("分数段（分数）" in hdr and "分段（占满分比例）" in hdr,
          "03 表应有「分数段（分数）」与「分段（占满分比例）」两列，实际 %s" % hdr)
    check(hdr.index("分数段（分数）") < hdr.index("分段（占满分比例）"),
          "「分数段（分数）」应排在比例档之前，实际 %s" % hdr)
    body = list(wb["03 分数段分布"].iter_rows(min_row=4, values_only=True))
    ranges = [row[2] for row in body]
    check(all(isinstance(v, str) and re.match(r"^\d+(\.\d+)? – \d+(\.\d+)? 分$", v) for v in ranges),
          "03 表「分数段（分数）」格内应全是分数区间（如「0 – 60 分」），实际 %s" % ranges[:5])
    check("90 – 100 分" in ranges,
          "03 表分数区间要按该科满分换算（数学满分 100 时末档应为「90 – 100 分」），实际 %s" % ranges)
    check(not any(isinstance(v, str) and "满分 分" in v for row in body for v in row),
          "03 表不应出现「满分 分」这种拼接残渣")
    marks = [(n, v[:40]) for n in wb.sheetnames for row in wb[n].iter_rows(values_only=True)
             for v in row if isinstance(v, str) and "**" in v]
    check(not marks, "结果册单元格不应残留 Markdown 星号，实际命中 %s" % marks[:3])

    # PDF：本机没有 Edge/Chrome 时脚本会降级为警告（不算失败）；有就顺带校验页眉页脚
    pdf = os.path.join(WORK, "t40.pdf")
    if os.path.exists(pdf) and os.path.getsize(pdf) > 1024:
        try:
            from pypdf import PdfReader
        except ImportError:
            return
        t = "\n".join((pg.extract_text() or "") for pg in PdfReader(pdf).pages)
        check("file://" not in t,
              "PDF 页脚不应带 file:// 本地路径（浏览器页眉页脚没关掉）")


# --------------------------------------------------------------------------- #
# 交付物「不暴露接口元数据」闸门（用户要求 2026-10-12）
#
# 交付物会被老师 / 家长 / 教研组打开，也会被转发。凡是**生成侧**的东西都不能跟着出门：
#   · 文件属性里的生成工具痕迹（Excel 的 creator=openpyxl、PDF 的 UA / Skia 引擎版本）
#   · 正文里内联的接口数据（analysis.json 的字段名、内联 JSON）
#   · 页脚里的工具 / 技能标识
#   · 文档里写死的个人绝对路径（含用户名）
# 下面五个用例把这几条钉死；改脚本时只要碰坏任一条，自测立刻红。
# --------------------------------------------------------------------------- #
@case
def test_pdf_info_scrub_keeps_length_and_clears_generator():
    """PDF 元数据清理必须**等长替换**：清掉生成侧标识，但不动一个字节的长度。

    长度不变 → xref / xref stream 里的对象偏移全部保持有效（否则 PDF 直接打不开）。
    这里用构造的 Info 片段做单测；集成效果见 test_pdf_delivered_has_no_generator_traces。
    """
    sys.path.insert(0, HERE)
    import report_builder as RB
    fake = (b"%PDF-1.4\n1 0 obj\n<</Title <FEFF1234>\n"
            b"/Creator (Mozilla/5.0 \\(Windows NT 10.0; Win64; x64\\) AppleWebKit/537.36"
            b" HeadlessChrome/155.0.0.0 Safari/537.36)\n"
            b"/Producer (Skia/PDF m155)\n"
            b"/CreationDate (D:20261012024800+00'00')>>\nendobj\n")
    fp = os.path.join(WORK, "t50_meta.pdf")
    with open(fp, "wb") as fh:
        fh.write(fake)
    RB.scrub_pdf_metadata(fp)
    out = open(fp, "rb").read()
    check(len(out) == len(fake), "清理必须等长（长度 %d → %d）" % (len(fake), len(out)))
    for kw in (b"Mozilla", b"HeadlessChrome", b"Skia/PDF", b"AppleWebKit", b"Windows NT"):
        check(kw not in out, "应清掉生成侧标识：%s" % kw.decode())
    check(b"/Creator" in out and b"/Producer" in out, "Info 的键结构要保留（值抹空）")
    check(b"/CreationDate" in out, "生成时间等中性字段不受影响")
    check(RB.pdf_metadata_leaks(fp) == [], "回读不应再有残留")
    # 幂等：重复调用不得越界或继续缩短
    RB.scrub_pdf_metadata(fp)
    check(len(open(fp, "rb").read()) == len(fake), "重复清理也应保持长度不变")


@case
def test_pdf_delivered_has_no_generator_traces():
    """真实链路：交付的 PDF 里不得残留浏览器 UA / 渲染引擎版本等生成侧元数据。"""
    rows = [["S%02d" % i, "学生%02d" % i, "初一(3)班", 60 + i] for i in range(1, 8)]
    fp = save_xlsx(os.path.join(WORK, "t51.xlsx"),
                   [("成绩", [["学号", "姓名", "班级", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "PDF元数据", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    html_path = os.path.join(WORK, "t51.html")
    pdf_path = os.path.join(WORK, "t51.pdf")
    subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                    "--out", html_path, "--pdf", "--pdf-out", pdf_path, "--no-excel"],
                   capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    if not (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024):
        return  # 本机没有 Edge/Chrome：跳过（不算失败，也不误报）
    raw = open(pdf_path, "rb").read()
    for kw in (b"Mozilla", b"HeadlessChrome", b"Skia/PDF", b"AppleWebKit", b"Windows NT"):
        check(kw not in raw, "PDF 属性残留生成侧标识：%s" % kw.decode())
    # 结构完好性：xref 表里每个在用对象偏移都要指向「N 0 obj」
    m = re.search(rb"startxref\s+(\d+)", raw)
    check(bool(m), "PDF 应有 startxref")
    tbl = raw[int(m.group(1)):]
    mt = re.match(rb"xref\s+0 (\d+)\s+", tbl)
    if mt:
        n = int(mt.group(1))
        body = tbl[mt.end():]
        bad = 0
        for num in range(min(n, 400)):
            ent = body[num * 20:num * 20 + 20]
            if len(ent) < 18 or ent[17:18] != b"n":
                continue
            off = int(ent[:10])
            if not re.match(rb"^\d+ 0 obj", raw[off:off + 20]):
                bad += 1
        check(bad == 0, "等长清理后 xref 偏移应全部有效，实际失配 %d 个" % bad)


@case
def test_deliverables_expose_no_internal_fields():
    """交付物正文不得出现接口字段名、内联数据与工具标识（用户要求 2026-10-12）。

    ① HTML：无 `<script>`、无内联 JSON、无引擎字段名、页脚不带工具标识；
    ② Excel：全部单元格无引擎字段名；文档属性里没有库名；
    ③ 页脚只留考试名与时间。
    """
    rows = [["S%02d" % i, "学生%02d" % i, "初一(3)班", 60 + i, 70 + i] for i in range(1, 12)]
    fp = save_xlsx(os.path.join(WORK, "t52_in.xlsx"),
                   [("成绩", [["学号", "姓名", "班级", "数学", "语文"]], rows)])
    r = run_engine(fp, "--exam-name", "元数据闸门", "--subjects", "数学,语文",
                   "--focus-class", "初一(3)班", "--full", "数学=100,语文=100")
    check(r.returncode == 0, "应能完成分析，stderr=%s" % (r.stderr or "")[-200:])
    html_path = os.path.join(WORK, "t52.html")
    xls_path = os.path.join(WORK, "t52_out.xlsx")
    p = subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                        "--out", html_path, "--excel-out", xls_path],
                       capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    check(p.returncode == 0, "渲染应成功，stderr=%s" % (p.stderr or "")[-300:])
    htm = open(html_path, encoding="utf-8").read()

    # ① HTML
    check("<script" not in htm.lower(), "报告不得内联脚本 / 接口数据")
    for key in ("meta.", "data_notes", "full_to_confirm", "individual_scope",
                "two_level_questions", "has_student_id", "analysis.json",
                "narrative.json", "score_rate", "by_class", "json"):
        check(key not in htm, "报告正文不得出现接口字段名 / 数据：%s" % key)
    for brand in ("WorkBuddy", "Skill", "skill"):
        check(brand not in htm, "页脚不得带生成工具标识：%s" % brand)
    foot = re.search(r"<footer>(.*?)</footer>", htm, re.S)
    check(bool(foot), "报告应有页脚")
    check("元数据闸门" in foot.group(1), "页脚应保留考试名，实际：%s" % foot.group(1)[:60])

    # ② Excel：单元格 + 文档属性
    wb = load_workbook(xls_path)
    all_txt = " ".join(str(c.value) for w in wb.worksheets
                       for row in w.iter_rows() for c in row if c.value)
    for key in ("meta.", "data_notes", "analysis.json", "narrative.json", "openpyxl"):
        check(key not in all_txt, "结果册单元格不得出现内部标识：%s" % key)
    props = wb.properties
    check((props.creator or "") == "", "Excel creator 不该是库名，实际 %r" % props.creator)
    check((props.lastModifiedBy or "") == "",
          "Excel lastModifiedBy 该为空，实际 %r" % props.lastModifiedBy)
    import zipfile
    with zipfile.ZipFile(xls_path) as z:
        core = z.read("docProps/core.xml").decode("utf-8")
    check("openpyxl" not in core, "docProps/core.xml 不得出现库名 openpyxl")


@case
def test_no_personal_absolute_path_in_skill_files():
    """技能文件里不得写死个人目录（用户名）——换机器即失效，且属内部环境信息。

    用户要求 2026-10-12：统一写成 `$HOME/...` 形式。判据用变量拼装，
    免得这个用例自己的源码命中自己。
    """
    seg = "Users"
    pat = re.compile(r"[A-Za-z]:[\\/]" + seg + r"[\\/]")
    root = os.path.dirname(HERE)
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", ".idea")]
        for fn in filenames:
            if not fn.endswith((".md", ".py", ".txt", ".yaml", ".yml", ".json")):
                continue
            path = os.path.join(dirpath, fn)
            try:
                txt = open(path, "r", encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if pat.search(txt):
                hits.append(os.path.relpath(path, root))
    check(not hits, "以下文件写死了个人绝对路径，请改成 $HOME 形式：%s" % hits)


@case
def test_delivery_docs_exclude_json_drafts():
    """.json 底稿不交付（用户要求 2026-10-12）。

    交付只给 HTML + PDF + Excel 三件套；`analysis.json` / `narrative.json` 是中间产物，
    归档到 `<交付目录>/.底稿/`，`present_files` 不传。SKILL.md 与 report-spec.md 都要写明；
    report-spec 的交付清单表里这两行的「默认」列必须是 ❌。
    没有这道闸门时，下次改动很容易把「三件套 + 底稿」的说法又抄回来。
    """
    root = os.path.dirname(HERE)
    for rel in ("SKILL.md", os.path.join("references", "report-spec.md")):
        txt = open(os.path.join(root, rel), encoding="utf-8").read()
        check(".底稿" in txt, "%s 未写明 .json 底稿归档到 .底稿/" % rel)
        check("不交付" in txt, "%s 未写明 .json 底稿不交付" % rel)
    spec = open(os.path.join(root, "references", "report-spec.md"), encoding="utf-8").read()
    for name in ("`analysis.json`", "`narrative.json`"):
        line = next((l for l in spec.splitlines() if l.startswith("| " + name)), "")
        check(line != "", "report-spec 交付清单里应保留 %s 一行（只是标为非交付）" % name)
        check(line.rstrip().endswith("| ❌ |"),
              "report-spec 交付清单里 %s 的「默认」列应为 ❌，实际=%r" % (name, line))


@case
def test_report_footer_has_no_tool_branding():
    """报告页脚只留考试名与生成时间，不带任何工具 / 技能标识（用户要求 2026-10-12）。"""
    rows = [["S%02d" % i, "学生%02d" % i, "初一(3)班", 70] for i in range(1, 5)]
    fp = save_xlsx(os.path.join(WORK, "t53.xlsx"),
                   [("成绩", [["学号", "姓名", "班级", "数学"]], rows)])
    r = run_engine(fp, "--exam-name", "页脚检查", "--subjects", "数学", "--full", "数学=100")
    check(r.returncode == 0, "应能完成分析")
    html_path = os.path.join(WORK, "t53.html")
    subprocess.run([PY, BUILDER, "--analysis", os.path.join(WORK, "out.json"),
                    "--out", html_path, "--no-excel"],
                   capture_output=True, text=True, encoding="utf-8", cwd=WORK)
    htm = open(html_path, encoding="utf-8").read()
    foot = re.search(r"<footer>(.*?)</footer>", htm, re.S)
    check(bool(foot), "报告应有页脚")
    txt = foot.group(1)
    for bad in ("WorkBuddy", "Skill", "skill", "脚本", "生成器", "引擎"):
        check(bad not in txt, "页脚不得出现「%s」，实际：%s" % (bad, txt[:80]))
    check("页脚检查" in txt, "页脚应保留考试名")


@case
def test_cnki_citation_links_title_not_author():
    """知网文献引用：链接必须挂在篇名上，作者名不得作为 <a> 载体（2026-10-21 复盘）。

    防止「把 (作者，年) 染成链接」这类错挂——统一用 report_builder.cnki_ref，
    作者署名纯文本、篇名才是可点击元素；此规则是 _shared.md 干净输出红线的一部分。
    """
    from report_builder import cnki_ref
    url = ("https://ix.cnki.net/read/article/readonline?dbcode=CMFD"
           "&tablename=CMFD202601&filename=1026206441.nh&fileSourceType=1")
    out = cnki_ref("何倩", "2025",
                   "基于认知负荷理论的高中数学解析几何教学策略研究", url)
    # 作者名不得被 <a> 包裹（不能是链接文本，也不能紧邻 </a>）
    check("何倩</a>" not in out and "</a>何倩" not in out,
          "作者名不得作为链接载体，实际：%s" % out)
    # 篇名必须是可点击元素，且指向知网在线阅读页
    check('href="%s"' % url in out, "篇名应指向知网在线阅读页，实际：%s" % out)
    check("基于认知负荷理论的高中数学解析几何教学策略研究</a>" in out,
          "篇名应是 <a> 的可点击文本，实际：%s" % out)
    # 篇名链接无下划线
    check("text-decoration:none" in out, "篇名链接须 text-decoration:none，实际：%s" % out)
    # 作者署名在 <a> 之外（纯文本、可见）
    prefix = out.split("<a", 1)[0]
    check("何倩，2025" in prefix, "作者署名应作为纯文本位于 <a> 之前，实际：%s" % out)


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description="cnki-edu-exam-score-analysis 回归自测")
    ap.add_argument("-k", default=None, help="只跑名字包含关键字的用例")
    args = ap.parse_args(argv)

    picked = [f for f in RESULTS if not args.k or args.k in f.__name__]
    print("=" * 72)
    print("考试成绩分析 Skill 自测：共 %d 个用例（工作目录 %s）" % (len(picked), WORK))
    print("=" * 72)
    failed = 0
    for fn in picked:
        try:
            fn()
            print("  [PASS] %s" % fn.__name__)
        except AssertionError as exc:
            failed += 1
            print("  [FAIL] %s\n          %s" % (fn.__name__, exc))
        except Exception as exc:  # pragma: no cover
            failed += 1
            print("  [ERROR] %s\n          %s: %s" % (fn.__name__, type(exc).__name__, exc))
            if os.environ.get("SELFTEST_TRACE"):
                import traceback
                traceback.print_exc()
    print("-" * 72)
    print("%d/%d 通过" % (len(picked) - failed, len(picked)))
    if not os.environ.get("KEEP_SELFTEST_DIR"):
        shutil.rmtree(WORK, ignore_errors=True)
    else:
        print("工作目录保留：%s" % WORK)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
