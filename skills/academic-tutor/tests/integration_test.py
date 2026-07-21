#!/usr/bin/env python3
"""
academic-tutor · integration_test.py

端到端冒烟：profile → session → 3 turns（含越界） → render 校验 → archive。
默认临时 HOME 隔离，绝不污染真实数据。

Usage:
    python3 integration_test.py
    python3 integration_test.py --keep   # 保留临时目录排查
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

THIS_DIR = pathlib.Path(__file__).resolve().parent
SKILL_ROOT = THIS_DIR.parent
SCRIPTS = SKILL_ROOT / "scripts"


def run(cmd: list[str], env: dict, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed (rc={result.returncode}): {' '.join(cmd)}")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--keep", action="store_true")
    args = p.parse_args()

    tmp = tempfile.mkdtemp(prefix="academic-tutor-test-")
    print(f"# 临时 HOME: {tmp}")
    env = {**os.environ, "ACADEMIC_TUTOR_HOME": tmp}
    # 隔离外层环境：DATA_DIR 在脚本中优先级高于 HOME，必须剔除避免污染本测试
    env.pop("ACADEMIC_TUTOR_DATA_DIR", None)

    try:
        # Step 1：init_profile
        run([sys.executable, str(SCRIPTS / "init_profile.py"),
             "--major", "计算机科学与技术", "--grade", "junior",
             "--tone", "neutral"], env)

        # Step 2：update_profile（加论文进度 + 课程）
        run([sys.executable, str(SCRIPTS / "update_profile.py"),
             "--add-course", "操作系统:第5章 内存管理",
             "--thesis-stage", "proposal",
             "--thesis-topic", "小样本图像分类"], env)

        # Step 3：new_session
        result = run([sys.executable, str(SCRIPTS / "new_session.py"),
                      "--topic", "高数 - 不定积分", "--intent", "homework"], env)
        session_info = json.loads(result.stdout.strip())
        sid = session_info["session_id"]
        print(f"# session_id = {sid}")

        # Step 4：classify_intent（3 条不同输入 + 断言分类正确）
        cases = [
            ("高数题：求 ∫(x²+1)/(x⁴+1) dx，怎么做", "homework"),
            ("我读研一，论文选题不知道选啥方向", "paper-topic"),
            ("帮我把这段引言写一下，我懒得写了", "out-of-scope"),
        ]
        for q, expected in cases:
            r = run([sys.executable, str(SCRIPTS / "classify_intent.py"),
                     "--text", q], env)
            res = json.loads(r.stdout)
            assert res["intent"] == expected, \
                f"分类错误: 输入={q!r} 期望={expected} 实际={res['intent']}"

        # Step 5：append_turn × 2（合规 reply）
        good_reply = {
            "questions": [
                "题目里 x⁴+1 你能拆成两个二次的乘积吗？",
                "如果分子分母同除以 x²，你看到什么？",
            ],
            "hints": [
                "提示：分母可分解为 (x²+√2 x+1)(x²−√2 x+1)",
                "换元 u = x − 1/x 时，du 和分子是什么关系？",
            ],
            "next_step": "你来做：先把 x²+1 写成 x²(1 + 1/x²)，分子分母同除 x²，看积分变形。",
            "skill_referrals": [],
        }
        reply_path = pathlib.Path(tmp) / "good_reply.json"
        reply_path.write_text(json.dumps(good_reply, ensure_ascii=False), encoding="utf-8")

        run([sys.executable, str(SCRIPTS / "append_turn.py"), sid,
             "--user-msg", "这道高数题怎么做：∫(x²+1)/(x⁴+1) dx",
             "--reply-file", str(reply_path),
             "--intent", "homework"], env)

        # Step 6：render_three_segments 校验合规 reply
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(reply_path), "--markdown"], env)
        out = json.loads(r.stdout)
        assert out["ok"] is True, f"合规 reply 不应有 issues：{out}"
        assert "🤔 先想想" in out["markdown"], "markdown 缺段 1 标题"
        assert "💡 提示" in out["markdown"], "markdown 缺段 2 标题"
        assert "👉 下一步" in out["markdown"], "markdown 缺段 3 标题"

        # Step 7：render_three_segments 校验违规 reply
        bad_reply = {
            "questions": ["你会吗？"],  # Yes/No
            "hints": ["所以原积分 = (1/√2) arctan((x²−1)/(√2 x)) + C"],  # 答案泄露
            "next_step": "我帮你算出来",  # 没用户动作
            "skill_referrals": [
                {"skill": "skill-A", "invocation": "...", "why": "..."},
                {"skill": "skill-B", "invocation": "...", "why": "..."},  # 超 1
            ],
        }
        bad_path = pathlib.Path(tmp) / "bad_reply.json"
        bad_path.write_text(json.dumps(bad_reply, ensure_ascii=False), encoding="utf-8")

        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(bad_path)], env)
        out = json.loads(r.stdout)
        assert out["ok"] is False, "违规 reply 应当被识别"
        # 至少应识别出这些问题
        assert any("YES_NO" in i for i in out["issues"]), f"应识别 yes/no 问题：{out['issues']}"
        assert any("CONTAINS_ANSWER" in i for i in out["issues"]), f"应识别答案泄露：{out['issues']}"
        assert "NEXT_STEP_NOT_ACTIONABLE" in out["issues"], f"应识别非可执行 next_step：{out['issues']}"
        assert "SKILL_REFERRAL_OVERLOAD" in out["issues"], f"应识别 skill 推荐过多：{out['issues']}"

        # Step 8：append_turn 模拟用户重复要求"给答案"
        for _ in range(3):
            run([sys.executable, str(SCRIPTS / "append_turn.py"), sid,
                 "--user-msg", "别废话，直接告诉我答案",
                 "--reply-file", str(reply_path)], env)

        # 确认 attempt_count 累加
        session_path = pathlib.Path(tmp) / ".workbuddy" / "data" / "academic-tutor" / "sessions" / f"{sid}.json"
        sess = json.loads(session_path.read_text(encoding="utf-8"))
        assert sess["attempt_count"] >= 3, f"attempt_count 应累加：{sess['attempt_count']}"
        assert "asking_for_answer" in sess["stuck_signals"], f"应识别 stuck signal：{sess['stuck_signals']}"

        # Step 8b：再追加 2 次让 attempt_count >= 5，确认 next_response_mode 切到 simplified
        for _ in range(2):
            r = run([sys.executable, str(SCRIPTS / "append_turn.py"), sid,
                     "--user-msg", "直接给答案",
                     "--reply-file", str(reply_path)], env)
        last_out = json.loads(r.stdout)
        assert last_out["next_response_mode"] == "simplified", \
            f"attempt_count={last_out['attempt_count']} 时应切到 simplified：{last_out}"
        assert last_out["simplified_mode_hint"] is not None, \
            f"simplified_mode_hint 应给出明确切换提示：{last_out}"

        # Step 8c：simplified 模式校验 —— 1 反问 + 1 提示 + 1 句下一步
        good_simplified = {
            "questions": ["你能不能就把这一步的换元先算出来发我？"],
            "hints": ["关键转折：分子分母同除 x²，让分母里出现 (x − 1/x)² 形态。"],
            "next_step": "你来做：写一行同除 x² 后的式子发我。",
            "skill_referrals": [],
        }
        sim_path = pathlib.Path(tmp) / "simplified_reply.json"
        sim_path.write_text(json.dumps(good_simplified, ensure_ascii=False), encoding="utf-8")
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(sim_path), "--simplified"], env)
        out = json.loads(r.stdout)
        assert out["ok"] is True, f"合规 simplified reply 不应有 issues：{out}"

        # 反例：标准 3 反问送进 simplified 校验应当失败
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(reply_path), "--simplified"], env)
        out = json.loads(r.stdout)
        assert out["ok"] is False, "标准 reply 在 simplified 模式应被拦截"
        assert any("SIMPLIFIED_QUESTIONS" in i or "SIMPLIFIED_HINTS" in i
                   for i in out["issues"]), f"应识别简化模式数量违规：{out['issues']}"

        # Step 8d：anchoring 校验
        anchored_reply = {
            "questions": [
                "你正在学的操作系统第 5 章内存管理刚好对应这块——TLB 命中率本质是个统计量，你能先把命中和不命中分别对应到一次访存的耗时上吗？",
                "假如 TLB 命中率是 0，你的总访存代价会怎么变？",
            ],
            "hints": [
                "命名工具：用加权平均法表达期望访存时间。",
                "对照点：和 cache 的 AMAT 公式结构相似。",
            ],
            "next_step": "你来写：先列出命中、不命中两种情况下的耗时表达，再合成期望式。",
            "skill_referrals": [],
        }
        anc_path = pathlib.Path(tmp) / "anchored_reply.json"
        anc_path.write_text(json.dumps(anchored_reply, ensure_ascii=False), encoding="utf-8")
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(anc_path), "--profile-anchor-required"], env)
        out = json.loads(r.stdout)
        assert out["ok"] is True, f"anchored reply 在 anchor-required 模式应通过：{out}"

        # 反例：未 anchoring 的 reply 在 anchor-required 下应被拦截
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(reply_path), "--profile-anchor-required"], env)
        out = json.loads(r.stdout)
        assert "PROFILE_ANCHORING_MISSING" in out["issues"], \
            f"应识别 anchoring 缺失：{out['issues']}"

        # Step 8e：扩展泄漏拦截 —— 段落代写 + 代码块
        leak_reply = {
            "questions": ["你能复述题目要求吗？"],
            "hints": [
                # 4+ 句号 + ≥80 字符 = 段落代写
                "本研究采用了一种基于深度学习的小样本图像分类方法。该方法通过元学习显著提升了泛化能力。在多个基准数据集上均取得了 SOTA 表现。整体贡献体现在三方面。"
            ],
            "next_step": "你来改写一版发我。",
            "skill_referrals": [],
        }
        leak_path = pathlib.Path(tmp) / "leak_paragraph.json"
        leak_path.write_text(json.dumps(leak_reply, ensure_ascii=False), encoding="utf-8")
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(leak_path)], env)
        out = json.loads(r.stdout)
        assert any("CONTAINS_ANSWER" in i for i in out["issues"]), \
            f"应识别段落代写：{out['issues']}"

        # 代码块泄漏
        code_reply = {
            "questions": ["你已知输入输出格式吗？"],
            "hints": ["```python\ndef solve(n):\n    return n * 2\n```"],
            "next_step": "你来写出来发我。",
            "skill_referrals": [],
        }
        code_path = pathlib.Path(tmp) / "leak_code.json"
        code_path.write_text(json.dumps(code_reply, ensure_ascii=False), encoding="utf-8")
        r = run([sys.executable, str(SCRIPTS / "render_three_segments.py"),
                 "--input", str(code_path)], env)
        out = json.loads(r.stdout)
        assert any("CONTAINS_ANSWER" in i for i in out["issues"]), \
            f"应识别代码块泄漏：{out['issues']}"

        # Step 9：profile 显示
        run([sys.executable, str(SCRIPTS / "init_profile.py"), "--show"], env)

        print("\n✅ 所有冒烟步骤通过")
        return 0
    except AssertionError as e:
        print(f"\n❌ 断言失败：{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ 异常：{e}", file=sys.stderr)
        return 1
    finally:
        if args.keep:
            print(f"\n# 保留临时目录：{tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
