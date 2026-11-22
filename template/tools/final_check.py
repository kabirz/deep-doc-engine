"""final_check.py — 页数断言 ≥400 + 打印缩放比验证（h2 实测字号/18.75pt ≈ 1.0）"""
import sys, statistics
sys.path.insert(0, os_dir := __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import nch
import pymupdf

H2_PT = 18.75

def main(min_pages=400):
    doc = pymupdf.open(nch.OUT_PDF)
    n = len(doc)
    print("页数: %d（要求 ≥%d）" % (n, min_pages))
    if n < min_pages:
        print("!! 页数不足"); sys.exit(1)
    sizes = []
    for pno in range(min(n, 400)):
        for blk in doc[pno].get_text("dict").get("blocks", []):
            for line in blk.get("lines", []):
                txt = "".join(s["text"] for s in line["spans"])
                t = txt.strip()
                if not (t.startswith("第") and "章" in t[:14]):
                    continue
                sz = max(s["size"] for s in line["spans"])
                if 17.0 <= sz <= 20.0:      # h2 字号门控（25px=18.75pt）
                    sizes.append(sz)
    if not sizes:
        print("!! 没找到 h2 章标题（18.75pt 门控内），缩放无法验证"); sys.exit(1)
    med = statistics.median(sizes)
    ratio = med / H2_PT
    print("h2 门控命中 %d 个章标题，实测字号中位 %.2fpt / 设计 %.2fpt = 缩放 %.3f（要求 0.96~1.04）" % (
        len(sizes), med, H2_PT, ratio))
    ok = 0.96 <= ratio <= 1.04
    print("缩放比: %s" % ("PASS" if ok else "FAIL —— 整本被缩小，需修超宽元素（跑 _overflow_probe.py）"))
    doc.close()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    mp = 400
    for a in sys.argv[1:]:
        if a.startswith("--min="):
            mp = int(a.split("=")[1])
    main(mp)
