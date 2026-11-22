"""add_bookmarks.py — 用 pymupdf 给 PDF 建书签（封面/目录/章 h2/节 h3，字号门控）"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch
import pymupdf

H2_SIZE, H2_TOL = 18.75, 1.0     # 设计字号 25px = 18.75pt
H3_SIZE, H3_TOL = 14.25, 0.85    # 19px = 14.25pt

def scan(pdf):
    doc = pymupdf.open(pdf)
    found = []   # (page_idx, level, title, y)
    for pno in range(len(doc)):
        page = doc[pno]
        d = page.get_text("dict")
        for blk in d.get("blocks", []):
            for line in blk.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                txt = "".join(s["text"] for s in spans).strip()
                if not txt:
                    continue
                size = max(s["size"] for s in spans)
                y = line["bbox"][1]
                if H2_SIZE - H2_TOL <= size <= H2_SIZE + H2_TOL:
                    mc = re.match(r"第 (\d+) 章", txt)
                    ma = re.match(r"附录 ([A-D])", txt)
                    if mc:
                        found.append((pno, 1, int(mc.group(1)), txt, y))
                    elif ma:
                        found.append((pno, 1, nch.NCH + "ABCD".index(ma.group(1)) + 1, txt, y))
                    elif txt.strip() == "目录":
                        found.append((pno, 0, 0, "目录", y))
                elif H3_SIZE - H3_TOL <= size <= H3_SIZE + H3_TOL:
                    if re.match(r"^\d+\.\d+", txt) or "本章要点" in txt:
                        found.append((pno, 2, 0, txt, y))
    doc.close()
    return found

def main():
    partial = "--partial" in sys.argv
    pdf = nch.OUT_PDF
    found = scan(pdf)
    chs = [f for f in found if f[2] and f[2] <= nch.NCH]
    apxs = [f for f in found if f[2] > nch.NCH]
    chnums = [c[2] for c in chs]
    if not partial:
        if chnums != sorted(chnums) or len(set(chnums)) != len(chnums):
            print("!! 章级书签顺序异常:", chnums); sys.exit(1)
        if len(chnums) != nch.NCH:
            missing = sorted(set(range(1, nch.NCH + 1)) - set(chnums))
            print("!! 缺章书签: %s（找到 %d 章）" % (missing, len(chnums))); sys.exit(1)
        if len(apxs) != nch.NAPX:
            print("!! 缺附录书签: 找到 %d / %d" % (len(apxs), nch.NAPX)); sys.exit(1)
    toc = [[1, "封面", 1]]
    for pno, lvl, num, title, y in sorted(found, key=lambda f: (f[0], f[4])):
        if lvl == 0 and title == "目录":
            toc.append([1, "目录", pno + 1])
        elif lvl == 1:
            toc.append([1, title, pno + 1])
        else:
            if toc and toc[-1][0] == 1:
                toc.append([2, title, pno + 1])
            else:
                toc.append([2, title, pno + 1])
    doc = pymupdf.open(pdf)
    doc.set_toc(toc)
    doc.saveIncr()
    doc.close()
    # 验证：用 get_toc 而不是日志
    doc = pymupdf.open(pdf)
    got = doc.get_toc()
    lv1 = [t for t in got if t[0] == 1]
    lv2 = [t for t in got if t[0] == 2]
    print("书签完成: 总 %d（%d 章/附录级 + %d 节级）" % (len(got), len(lv1), len(lv2)))
    print("前 6 条:", [(t[0], t[1][:22], t[2]) for t in got[:6]])
    if len(lv2) < nch.MIN_LV2 and not partial:
        print("!! 节级书签过少（%d < %d），检查 h3 字号门控" % (len(lv2), nch.MIN_LV2)); sys.exit(1)

if __name__ == "__main__":
    main()
