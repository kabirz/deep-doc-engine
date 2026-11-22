"""toc_pages.py — 从已打印的 PDF 提取各章真实起始页，写 _toc_pages.json
用法：python toc_pages.py <pdf路径> [--verify]
--verify：与已有 _toc_pages.json 比对，全部一致才通过（两遍打印稳定性校验）
"""
import os, re, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nch
import pymupdf

H2_TOL = 1.0

def scan(pdf):
    doc = pymupdf.open(pdf)
    found = []  # (page, title)
    for pno in range(len(doc)):
        for blk in doc[pno].get_text("dict").get("blocks", []):
            for line in blk.get("lines", []):
                txt = "".join(s["text"] for s in line.get("spans", [])).strip()
                if not txt:
                    continue
                size = max(s["size"] for s in line["spans"])
                if 17.0 <= size <= 20.0:
                    if re.match(r"第 \d+ 章", txt) or re.match(r"附录 [A-D]", txt) or txt == "目录":
                        found.append((pno + 1, txt))
    doc.close()
    return found

def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else nch.OUT_PDF
    verify = "--verify" in sys.argv
    hits = scan(pdf)
    # 按 fragment 顺序建立 id -> 标题匹配
    frags = []
    for f in nch.fragment_order():
        doc = open(os.path.join(nch.SRC, f), encoding="utf-8-sig").read()
        m = re.search(r'<h2 id="([^"]+)">([^<]+)</h2>', doc)
        if m:
            frags.append((m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()))
    pages = {}
    used = set()
    for fid, title in frags:
        tnorm = re.sub(r"\s+", "", title)
        for pno, txt in hits:
            if pno in used:
                continue
            t2 = re.sub(r"\s+", "", txt)
            # 标题过长在 PDF 中折行时，行文本是标题的前缀
            if t2 == tnorm or tnorm.startswith(t2):
                pages[fid] = pno
                used.add(pno)
                break
    missing = [fid for fid, _ in frags if fid not in pages]
    if missing:
        print("!! 未匹配到起始页:", missing)
        sys.exit(1)
    pfile = os.path.join(nch.ROOT, "_toc_pages.json")
    if verify:
        old = json.load(open(pfile, encoding="utf-8"))
        diff = {k: (old.get(k), v) for k, v in pages.items() if old.get(k) != v}
        if diff:
            print("!! 两遍打印页码漂移:", diff)
            sys.exit(1)
        print("页码稳定校验通过（%d 项一致）" % len(pages))
        return
    json.dump(pages, open(pfile, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("已写 %s（%d 项）：%s" % (pfile, len(pages), list(pages.items())[:5]))

if __name__ == "__main__":
    main()
