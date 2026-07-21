"""
文章交付质量验证器（validate-article）- 生产版
================================================
程序化检查成品文章，不依赖 LLM 判断。
返回 pass/fail + 具体 issue 列表。

参数：
- article_text（必填）：成品文章全文（Markdown 格式）
- brief_file（可选）：Creative Brief 文件路径
- phase（可选）："pre-illustrate" / "pre-delivery"
- min_links（可选）：最少超链接数，默认 3
- min_words（可选）：最少字数，默认 800
- max_words（可选）：最大字数，默认 5000
- expected_images（可选）：预期配图数
"""

import json
import re
import sys
import os
from collections import Counter


def handle(params: dict):
    """validate-article handler 入口"""
    article_text = params.get("article_text", "")
    brief_file = params.get("brief_file", "")
    phase = params.get("phase", "pre-delivery")
    min_links = params.get("min_links", 3)
    min_words = params.get("min_words", 800)
    max_words = params.get("max_words", 5000)
    expected_images = params.get("expected_images")

    if not article_text:
        print(json.dumps({
            "status": "error",
            "error_code": "MissingArticle",
            "error_message": "缺少 article_text 参数"
        }, ensure_ascii=False))
        return

    issues = []
    stats = {}

    # 预处理：分离正文和交付附件区域
    appendix_split = re.split(r'^##\s*(?:📋\s*)?交付附件', article_text, maxsplit=1, flags=re.MULTILINE)
    body_text = appendix_split[0]

    # ============================================
    # 检查 1：超链接数量与质量
    # ============================================
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]*)\)')
    all_links = link_pattern.findall(body_text)

    valid_links = []
    empty_links = []

    for text, url in all_links:
        url_stripped = url.strip()
        # 跳过图片类链接
        if url_stripped and (url_stripped.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
                            or 'cos.' in url_stripped or '/image/' in url_stripped):
            continue
        # 空链接
        if not url_stripped or url_stripped in ('#', 'undefined', 'null', 'javascript:void(0)'):
            empty_links.append((text, url_stripped))
            continue
        # 有效外链
        if url_stripped.startswith(('http://', 'https://')):
            valid_links.append((text, url_stripped))

    stats["total_links"] = len(all_links)
    stats["valid_links"] = len(valid_links)
    stats["empty_links"] = len(empty_links)

    if empty_links:
        for text, url in empty_links:
            issues.append({
                "severity": "FAIL",
                "category": "空链接",
                "detail": f"发现空链接：[{text}]({url or '空'}) — 必须移除或填入真实 URL"
            })

    if len(valid_links) < min_links:
        issues.append({
            "severity": "FAIL",
            "category": "链接不足",
            "detail": f"有效外链 {len(valid_links)} 个，最低要求 {min_links} 个。需补充数据来源超链接。"
        })

    # 检查 1b：重复链接
    # 阈值策略（v2 优化，2026-07-02）：
    #   - 单一 URL 引用 ≥4 次：FAIL（防止懒惰引用/来源单一化）
    #   - 单一 URL 引用 2-3 次：WARN（同源多论据溯源属正常写作习惯）
    #   - pre-illustrate 阶段：全部 WARN（此时正在写作，不做硬约束）
    url_counter = Counter(url for _, url in valid_links)
    duplicate_urls = {url: count for url, count in url_counter.items() if count > 1}
    stats["duplicate_link_count"] = len(duplicate_urls)

    if duplicate_urls:
        dup_details = [f"[{url[:60]}...] 出现 {count} 次" if len(url) > 60
                       else f"[{url}] 出现 {count} 次"
                       for url, count in list(duplicate_urls.items())[:5]]
        max_dup = max(duplicate_urls.values())
        if phase == "pre-delivery" and max_dup >= 4:
            severity = "FAIL"
        else:
            severity = "WARN"
        issues.append({
            "severity": severity,
            "category": "重复链接",
            "detail": f"同一 URL 被多次引用：{'; '.join(dup_details)}"
        })

    # ============================================
    # 检查 2：配图占位符残留
    # ============================================
    placeholder_pattern = re.compile(r'\[IMAGE:\d+:[^\]]*\]')
    remaining_placeholders = placeholder_pattern.findall(article_text)
    actual_images = re.findall(r'!\[[^\]]*\]\([^)]+\)', article_text)
    stats["actual_images"] = len(actual_images)
    stats["remaining_placeholders"] = len(remaining_placeholders)

    if remaining_placeholders and phase == "pre-delivery":
        issues.append({
            "severity": "FAIL",
            "category": "配图未替换",
            "detail": f"发现 {len(remaining_placeholders)} 个未替换的配图占位符：{remaining_placeholders[:3]}"
        })

    if expected_images is not None:
        if len(actual_images) < expected_images:
            issues.append({
                "severity": "WARN",
                "category": "配图数量",
                "detail": f"实际配图 {len(actual_images)} 张，预期 {expected_images} 张"
            })

    # ============================================
    # 检查 3：AI 图标注
    # ============================================
    ai_caption_pattern = re.compile(r'AI\s*生成示意图[，,]\s*仅供参考')
    ai_captions_count = len(ai_caption_pattern.findall(article_text))
    stats["ai_captions"] = ai_captions_count

    # ============================================
    # 检查 4：字数
    # ============================================
    clean_text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', article_text)
    clean_text = re.sub(r'\[[^\]]*\]\([^)]+\)', '', clean_text)
    clean_text = re.sub(r'[#*_`~>|\-\[\]]', '', clean_text)
    clean_text = re.sub(r'\n{2,}', '\n', clean_text)
    clean_text = re.sub(r'---+', '', clean_text)

    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
    english_words = len(re.findall(r'[a-zA-Z]+', clean_text))
    word_count = chinese_chars + english_words
    stats["word_count"] = word_count

    if word_count < min_words:
        issues.append({
            "severity": "WARN",
            "category": "字数不足",
            "detail": f"正文约 {word_count} 字，低于最低要求 {min_words} 字"
        })
    elif word_count > max_words:
        issues.append({
            "severity": "WARN",
            "category": "字数超标",
            "detail": f"正文约 {word_count} 字，超过上限 {max_words} 字"
        })

    # ============================================
    # 检查 5：结构完整性
    # ============================================
    h1_count = len(re.findall(r'^#\s+.+', article_text, re.MULTILINE))
    h2_count = len(re.findall(r'^##\s+.+', article_text, re.MULTILINE))
    stats["h1_count"] = h1_count
    stats["h2_count"] = h2_count

    if h1_count == 0:
        issues.append({
            "severity": "WARN",
            "category": "缺少标题",
            "detail": "文章没有 H1 标题（# 标题）"
        })

    # ============================================
    # 检查 6：开篇质量
    # ============================================
    boilerplate_phrases = [
        "随着.*的发展", "众所周知", "在当今社会",
        "不言而喻", "毋庸置疑", "在.*时代背景下"
    ]
    lines = article_text.strip().split('\n')
    body_start = ""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('!'):
            body_start = stripped[:200]
            break

    for phrase in boilerplate_phrases:
        if re.search(phrase, body_start):
            issues.append({
                "severity": "WARN",
                "category": "开篇套话",
                "detail": f"开篇包含套话模式：'{phrase}'"
            })
            break

    # ============================================
    # 检查 7：Brief URL 交叉验证
    # ============================================
    if brief_file and os.path.isfile(brief_file):
        try:
            with open(brief_file, 'r', encoding='utf-8') as f:
                brief_content = f.read()
            brief_urls = re.findall(r'https?://[^\s\)）\]]+', brief_content)
            article_urls = [url for _, url in valid_links]
            brief_urls_set = set(brief_urls)
            used_urls = set(article_urls) & brief_urls_set
            stats["brief_urls_total"] = len(brief_urls_set)
            stats["brief_urls_used"] = len(used_urls)

            if brief_urls_set and len(used_urls) / len(brief_urls_set) < 0.3:
                issues.append({
                    "severity": "WARN",
                    "category": "Brief URL 引用率低",
                    "detail": f"Brief 提供 {len(brief_urls_set)} 个 URL，文章仅引用 {len(used_urls)} 个"
                })
        except Exception:
            pass

    # ============================================
    # 检查 8：交付附件完整性（pre-delivery）
    # ============================================
    if phase == "pre-delivery":
        has_appendix_header = bool(re.search(r'##\s*(?:📋\s*)?交付附件', article_text))
        has_data_sources = bool(re.search(r'###\s*数据来源', article_text))
        has_image_sources = bool(re.search(r'###\s*配图来源', article_text))

        stats["has_appendix"] = has_appendix_header
        stats["has_data_sources"] = has_data_sources
        stats["has_image_sources"] = has_image_sources

        if not has_appendix_header:
            issues.append({
                "severity": "FAIL",
                "category": "缺少交付附件",
                "detail": "MD 产物缺少「## 📋 交付附件」区块"
            })
        else:
            if not has_data_sources:
                issues.append({
                    "severity": "FAIL",
                    "category": "附件缺数据来源",
                    "detail": "交付附件缺少「### 数据来源」区块"
                })
            if not has_image_sources:
                issues.append({
                    "severity": "FAIL",
                    "category": "附件缺配图来源",
                    "detail": "交付附件缺少「### 配图来源」区块"
                })

    # ============================================
    # 汇总评分
    # ============================================
    fail_count = sum(1 for i in issues if i["severity"] == "FAIL")
    warn_count = sum(1 for i in issues if i["severity"] == "WARN")

    score = max(0, 100 - fail_count * 15 - warn_count * 5)
    status = "pass" if fail_count == 0 and score >= 85 else "fail"

    result = {
        "status": status,
        "score": score,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "issues": issues,
        "stats": stats,
        "phase": phase,
    }

    # 摘要输出到 stderr
    summary_icon = "✅" if status == "pass" else "⛔"
    print(f"\n{summary_icon} 文章质量验证 [{phase}] — {status.upper()} (score={score})", file=sys.stderr)
    if issues:
        print(f"   问题列表 ({fail_count} FAIL / {warn_count} WARN):", file=sys.stderr)
        for i in issues:
            icon = "❌" if i["severity"] == "FAIL" else "⚠️"
            print(f"   {icon} [{i['category']}] {i['detail']}", file=sys.stderr)
    print(f"   统计：字数={stats.get('word_count',0)} / 外链={stats.get('valid_links',0)} / 配图={stats.get('actual_images',0)}", file=sys.stderr)

    # JSON 结果输出到 stdout
    print(json.dumps(result, ensure_ascii=False))
