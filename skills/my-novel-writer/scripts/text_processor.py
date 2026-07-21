"""
中文文本处理模块 - 改进摘要提取算法
"""

import re
from typing import List, Tuple, Optional


class ChineseTextProcessor:
    """中文文本处理器"""

    # 常用标点符号
    PUNCTUATIONS = "，。！？；：、""''（）【】《》——…"

    # 停用词列表
    STOP_WORDS = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "他"
    }

    @staticmethod
    def count_chinese_words(text: str) -> int:
        """统计中文字数（精确）"""
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars)

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """提取句子"""
        sentence_end = re.compile(r'[。！？；]')
        sentences = sentence_end.split(text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """提取关键词（基于词频）"""
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        word_freq = {}
        for word in words:
            if len(word) >= 2 and word not in ChineseTextProcessor.STOP_WORDS:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_n]

    @staticmethod
    def extract_summary(text: str, max_length: int = 200) -> str:
        """提取摘要 - 改进版算法"""
        sentences = ChineseTextProcessor.extract_sentences(text)
        if not sentences:
            return text[:max_length]

        # 计算每句话的重要性得分
        scored_sentences = []
        keywords = set([k for k, _ in ChineseTextProcessor.extract_keywords(text, top_n=15)])

        for i, sentence in enumerate(sentences):
            score = 0

            # 位置得分：开头和结尾的句子更重要
            if i == 0:
                score += 3
            elif i == len(sentences) - 1:
                score += 2

            # 关键词得分
            for keyword in keywords:
                if keyword in sentence:
                    score += 1

            # 长度得分：太短或太长的句子适当降低
            length = len(sentence)
            if 20 <= length <= 100:
                score += 1

            # 包含特定词汇加分
            important_patterns = ["于是", "但是", "因为", "所以", "然而", "突然", "只见"]
            for pattern in important_patterns:
                if pattern in sentence:
                    score += 0.5

            scored_sentences.append((sentence, score))

        # 按得分排序，选取句子
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # 选择得分最高的句子，保持原始顺序
        selected = []
        selected_indices = set()
        for sentence, _ in scored_sentences:
            if len("".join(selected)) + len(sentence) <= max_length:
                # 找到这句话在原始列表中的位置
                for idx, orig_sentence in enumerate(sentences):
                    if orig_sentence == sentence and idx not in selected_indices:
                        selected_indices.add(idx)
                        selected.append((idx, sentence))
                        break

        # 按原始顺序排序
        selected.sort(key=lambda x: x[0])
        summary = "".join([s[1] for s in selected])

        return summary if summary else text[:max_length]

    @staticmethod
    def extract_hook(text: str) -> Optional[str]:
        """提取章节结尾的钩子（悬念）"""
        sentences = ChineseTextProcessor.extract_sentences(text)
        if len(sentences) < 2:
            return None

        # 最后3句话中寻找悬念词
        last_sentences = sentences[-3:]
        hook_keywords = ["突然", "然而", "就在这时", "却", "没想到", "竟然", "居然", "危机", "危险", "神秘", "却发现"]

        for sentence in reversed(last_sentences):
            for keyword in hook_keywords:
                if keyword in sentence:
                    # 返回这句话的最后一个分句
                    return sentence[-50:] if len(sentence) > 50 else sentence

        return sentences[-1][-50:] if len(sentences[-1]) > 50 else sentences[-1]

    @staticmethod
    def analyze_text(text: str) -> dict:
        """文本分析"""
        word_count = ChineseTextProcessor.count_chinese_words(text)
        sentences = ChineseTextProcessor.extract_sentences(text)
        keywords = ChineseTextProcessor.extract_keywords(text, top_n=10)

        return {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "keywords": [k for k, _ in keywords],
            "has_hook": ChineseTextProcessor.extract_hook(text) is not None
        }


def quick_summary(text: str, max_length: int = 200) -> str:
    """快速摘要函数"""
    return ChineseTextProcessor.extract_summary(text, max_length)


def count_words(text: str) -> int:
    """统计字数"""
    return ChineseTextProcessor.count_chinese_words(text)


def extract_last_hook(text: str) -> Optional[str]:
    """提取章节钩子"""
    return ChineseTextProcessor.extract_hook(text)