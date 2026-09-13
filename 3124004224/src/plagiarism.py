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


# 超过这个长度切换到 n-gram
LONG_TEXT = 50000

# n-gram 的 n 值，中文用 4 比较合适
NGRAM_SIZE = 4

# rolling hash 参数
HASH_BASE = 131
HASH_MOD = (1 << 61) - 1


"""
用 rolling hash 生成 n-gram 哈希集合。
"""
def _ngram_hashes_rolling(text, n):
    
    length = len(text)
    if length < n:
        return {hash(text)} if text else set()

    result = set()
    base = HASH_BASE
    mod = HASH_MOD

    # 计算第一个 n-gram 的哈希
    h = 0
    for i in range(n):
        h = (h * base + ord(text[i])) % mod
    result.add(h)

    # 滑动窗口
    power = pow(base, n - 1, mod)
    for i in range(n, length):
        h = (h - ord(text[i - n]) * power) % mod
        h = (h * base + ord(text[i])) % mod
        result.add(h)

    return result

"""n-gram + Jaccard 相似度，O(n)"""
def _ngram_jaccard(a, b, n=NGRAM_SIZE):
    set_a = _ngram_hashes_rolling(a, n)
    set_b = _ngram_hashes_rolling(b, n)

    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0

    inter = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0
    return inter / union

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

    max_len = max(len(orig), len(plag))

    if max_len <= LONG_TEXT:
        score = difflib.SequenceMatcher(None, orig, plag).ratio()
    else:
        score = _ngram_jaccard(orig, plag)

    # 确保结果在0-1
    if score < 0.00:
        return 0.00
    if score > 1.00:
        return 1.00
    return score