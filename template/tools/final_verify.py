"""final_verify.py — 终验：页数 + 封面标题行数 + 书签数，并渲染封面 PNG"""
import io, sys, os, pymupdf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pymupdf.open(os.path.join(ROOT, "Linux外设总线通信协议深度详解.pdf"))
print("pages:", len(d))
pg = d[0]
title_lines = []
for b in pg.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        txt = "".join(s["text"] for s in l["spans"]).strip()
        if "深度详解" in txt or txt.startswith("Linux"):
            title_lines.append(txt)
print("title lines:", title_lines)
print("bookmarks:", len(d.get_toc()))
pix = pg.get_pixmap(dpi=110)
pix.save(os.path.join(ROOT, "_shots", "cover_final.png"))
print("cover_final.png saved")
d.close()
