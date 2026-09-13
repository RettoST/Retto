import os
import sys
import time
import tempfile
import subprocess
import pytest

# 确保能找到 main.py 和 plagiarism.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
from plagiarism import read_file, normalize_text, calc_similarity

DATA_DIR = os.path.join(PROJECT_ROOT, "tests")
MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")

# 模拟命令行运行 main.py
def run_main(orig, plag, ans):
    return subprocess.run(
        [sys.executable, MAIN_PY, orig, plag, ans],
        capture_output=True, text=True, timeout=5
    )

# 读取答案文件内容
def read_answer(path):
    with open(path, "r", encoding="utf-8") as f:
        return float(f.read().strip())


def test_big_file():
    orig = os.path.join(DATA_DIR, "big.txt")
    plag = os.path.join(DATA_DIR, "big_add.txt")
    
    if not os.path.exists(orig) or not os.path.exists(plag):
        pytest.skip("big.txt 或 big_add.txt 不存在")

    ans = tempfile.mktemp(suffix=".txt")
    start = time.time()
    result = run_main(orig, plag, ans)
    elapsed = time.time() - start

    assert result.returncode == 0, "程序崩溃了"
    assert elapsed < 5.0, f"大文件耗时 {elapsed:.2f} 秒，超过 5 秒限制！"
    
    score = read_answer(ans)
    assert 0.0 <= score <= 1.0
    os.remove(ans)
    print(f"\n[大文件测试] 耗时 {elapsed:.2f} 秒，相似度 {score:.2f}")


@pytest.mark.parametrize("orig_name, plag_name", [
    ("orig.txt", "orig_add.txt"),
    ("poem.txt", "poem_add.txt"),
    ("poem2.txt", "poem2_add.txt"),
    ("orig2.txt", "orig2_0.8_add.txt"),
    ("orig2.txt", "orig2_0.8_del.txt"),
    ("orig2.txt", "orig2_0.8_dis_1.txt"),
    ("orig2.txt", "orig2_0.8_dis_10.txt"),
    ("orig2.txt", "orig2_0.8_dis_15.txt"),
])
def test_normal_files(orig_name, plag_name):
    """正常情况：随便测测，只要不崩、分数合法就行"""
    orig = os.path.join(DATA_DIR, orig_name)
    plag = os.path.join(DATA_DIR, plag_name)
    
    if not os.path.exists(orig) or not os.path.exists(plag):
        pytest.skip(f"{orig_name} 或 {plag_name} 不存在")

    ans = tempfile.mktemp(suffix=".txt")
    
    # 增加计时
    start = time.time()
    result = run_main(orig, plag, ans)
    elapsed = time.time() - start

    assert result.returncode == 0, f"{orig_name} vs {plag_name} 崩溃"
    
    score = read_answer(ans)
    os.remove(ans)

    # 打印结果
    print(f"\n[正常测试] {orig_name} vs {plag_name} -> 耗时 {elapsed:.4f}s, 相似度 {score:.2f}")


def test_empty_and_missing():
    # 文件不存在
    ans1 = tempfile.mktemp(suffix=".txt")
    r1 = run_main("no_such_file.txt", "no_such_file.txt", ans1)
    assert r1.returncode == 0
    if os.path.exists(ans1): os.remove(ans1)

    # 空文件
    empty = tempfile.mktemp(suffix=".txt")
    with open(empty, "w", encoding="utf-8") as f:
        f.write("")
    
    orig = os.path.join(DATA_DIR, "orig.txt")
    if os.path.exists(orig):
        ans2 = tempfile.mktemp(suffix=".txt")
        r2 = run_main(orig, empty, ans2)
        assert r2.returncode == 0
        if os.path.exists(ans2): os.remove(ans2)
    
    os.remove(empty)


# 覆盖率补充。。。。
class TestCoverageDirect:

    # 测试标准化
    def test_cov_normalize(self):
        assert normalize_text("  a\n b  ") == "ab"
        assert normalize_text("") == ""
        assert normalize_text("   \t\n") == ""
        assert normalize_text(None) == ""

    # 测试短文本的
    def test_cov_similarity_short(self):
        assert calc_similarity("abc", "abc") == 1.0
        assert calc_similarity("", "") == 1.0
        assert calc_similarity("", "abc") == 0.0
        assert calc_similarity("abc", "") == 0.0
        assert calc_similarity("abc", "xyz") < 0.15

    # 测试长文本的相似度
    def test_cov_similarity_long(self):
        """长文本走 n-gram 分支，覆盖率关键"""
        a = "测试文本内容" * 20000      # 12 万字符，超过阈值
        b = "测试文本内容" * 20000
        score = calc_similarity(a, b)
        assert score > 0.99

    def test_cov_similarity_long_partial(self):
        a = "测试文本内容" * 20000
        b = a[: len(a) // 2] + "插入的内容" + a[len(a) // 2:]
        score = calc_similarity(a, b)
        assert 0.0 <= score <= 1.0

    # 测试读取
    def test_cov_read_file_utf8(self):
        path = os.path.join(DATA_DIR, "orig.txt")
        if not os.path.exists(path):
            pytest.skip("orig.txt 不存在")
        text = read_file(path)
        assert isinstance(text, str)
        assert len(text) > 0

    # 测试gbk读取
    def test_cov_read_file_gbk(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        with open(path, "w", encoding="gbk") as f:
            f.write("今天天气很好，适合出去玩。")
        try:
            text = read_file(path)
            assert "天气" in text
        finally:
            os.remove(path)

    # 测试读不到文件
    def test_cov_read_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_file("/nonexistent/file.txt")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])