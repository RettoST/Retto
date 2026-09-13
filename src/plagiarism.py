import re
import difflib

"""
读取文本文件内容。
考虑编码可能是gbk或者utf-8
"""
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="gbk") as f:
                return f.read()
        except UnicodeDecodeError: # 如果两者都读不了就强行读
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

"""
去除文本中的空白字符（空格、换行、制表符等）。
"""
def normalize_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", "", text)

"""
计算的相似度，返回 0.00-1.00
"""
def calc_similarity(orig, plag):
    # 两段都空认为完全相似
    if not orig and not plag:
        return 1.00
    # 一空一不空就完全不相同
    if not orig or not plag:
        return 0.00

    matcher = difflib.SequenceMatcher(None, orig, plag)
    ratio = matcher.ratio()

    # 确保结果在0-1
    if ratio < 0.00:
        return 0.00
    if ratio > 1.00:
        return 1.00
    return ratio