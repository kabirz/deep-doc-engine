"""sanitize_ghost.py — 修复 Chromium 大文档分片残影：末页幽灵深色代码背景，用白矩形覆盖"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch
import pymupdf

def is_dark(c):
    return c and c[0] < 0.22 and c[1] < 0.22 and c[2] < 0.22

def main():
    pdf = nch.OUT_PDF
    doc = pymupdf.open(pdf)
    n = len(doc)
    fixed = 0
    for pno in range(max(0, n - 3), n):
        page = doc[pno]
        ptext = page.get_text().strip()
        rects = page.get_drawings()
        pr = page.rect
        cover = []
        for dr in rects:
            if dr.get("fill") and is_dark(dr["fill"]):
                r = dr["rect"]
                if r.width > pr.width * 0.3 and r.height > pr.height * 0.25:
                    cover.append(r)
        if cover and len(ptext) < 200:
            for r in cover:
                page.draw_rect(r, color=None, fill=(1, 1, 1), overlay=True)
                fixed += 1
            print("第 %d 页: 覆盖 %d 个幽灵深色块（页面文字 %d 字符）" % (pno + 1, len(cover), len(ptext)))
    if fixed:
        doc.saveIncr()
        print("已保存修复 (%d 处)" % fixed)
    else:
        print("末 3 页无幽灵背景，无需修复")
    doc.close()

if __name__ == "__main__":
    main()
