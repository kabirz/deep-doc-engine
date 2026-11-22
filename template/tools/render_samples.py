"""render_samples.py — 从成品 PDF 渲染代表性页面为 PNG 供视觉终审"""
import io, sys, os, json, pymupdf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "Linux外设总线通信协议深度详解.pdf")
OUT = os.path.join(ROOT, "_shots")
os.makedirs(OUT, exist_ok=True)

doc = pymupdf.open(PDF)
n = len(doc)
pages = {1: "cover", 2: "toc1", 18: "toc-end", 19: "ch01"}
try:
    tp = json.load(open(os.path.join(ROOT, "_toc_pages.json"), encoding="utf-8"))
    vals = sorted(tp.values())
    for p in vals[5:50:max(1, len(vals) // 8)]:
        pages[p] = "mid%d" % p
except Exception as e:
    print("toc json skip:", e)
for p in (n // 4, n // 2, 3 * n // 4, n - 2, n):
    pages[p] = "q%d" % p

for p, name in sorted(pages.items()):
    if not (1 <= p <= n):
        continue
    pg = doc[p - 1]
    pix = pg.get_pixmap(dpi=110)
    fp = os.path.join(OUT, "p%03d_%s.png" % (p, name))
    pix.save(fp)
    print(fp, "%dx%d" % (pix.width, pix.height))
doc.close()
print("done", n, "pages total")
