import sys
from src.plagiarism import read_file, normalize_text, calc_similarity

def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <原文文件> <抄袭版文件> <答案文件>")
        return

    orig_path = sys.argv[1]
    plag_path = sys.argv[2]
    ans_path = sys.argv[3]

    score = 0.0

    try:
        orig_text = normalize_text(read_file(orig_path))
        plag_text = normalize_text(read_file(plag_path))
        score = calc_similarity(orig_text, plag_text)
    except Exception as e:
        # 文件不存在、权限不足、路径是文件夹等
        score = 0.0
        print(e)

    try:
        with open(ans_path, "w", encoding="utf-8") as f:
            f.write(f"{score:.2f}")
        print(f"结果已保存在 {ans_path}，分数为：{score:.2f}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

