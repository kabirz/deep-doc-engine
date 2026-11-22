"""svg_check.py — 检查所有片段内嵌 SVG：禁令、id 唯一、出画布、text-anchor、禁词"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch

SVGSVG = re.compile(r"<svg[^>]*viewBox=\"0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)\"[^>]*>(.*?)</svg>", re.S)
ID_RE = re.compile(r"\bid=\"([^\"]+)\"")
TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
NUM = r"(-?\d+(?:\.\d+)?)"
ELEM_RE = re.compile(
    r"<(text|rect|circle|ellipse|line|polyline|polygon)\b[^>]*?(?:/>|>(?:(?!</?\1\b).)*?</\1>)", re.S)

def text_width(s, fs):
    w = 0.0
    for ch in s:
        w += fs * (1.0 if ord(ch) > 0x2E7F else 0.55)
    return w

def elem_bbox(m):
    tag = m.group(0)
    name = m.group(1)
    def g(attr):
        r = re.search(r"\b" + attr + r"=\"\s*" + NUM, tag)
        return float(r.group(1)) if r else None
    if name == "text":
        attrs = m.group(0)[:m.group(0).index(">")]
        content = re.sub(r"<[^>]+>", "", m.group(0)[m.group(0).index(">") + 1:m.group(0).rindex("</text>")])
        x, y = g("x"), g("y")
        if x is None or y is None: return None
        mf = re.search(r"font-size=\"(\d+(?:\.\d+)?)", attrs)
        fs = float(mf.group(1)) if mf else 12.0
        ma = re.search(r"text-anchor=\"(\w+)\"", attrs)
        anchor = ma.group(1) if ma else "middle"
        txt = content.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        w = text_width(txt, fs)
        if anchor == "start": x0, x1 = x - 1, x + w + 1
        elif anchor == "end": x0, x1 = x - w - 1, x + 1
        else: x0, x1 = x - w / 2 - 1, x + w / 2 + 1
        return (x0, y - fs * 0.78, x1, y + fs * 0.22)
    if name == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        if None in (x, y, w, h): return None
        return (x, y, x + w, y + h)
    if name == "circle":
        cx, cy, r = g("cx"), g("cy"), g("r")
        return None if None in (cx, cy, r) else (cx - r, cy - r, cx + r, cy + r)
    if name == "ellipse":
        cx, cy, rx, ry = g("cx"), g("cy"), g("rx"), g("ry")
        return None if None in (cx, cy, rx, ry) else (cx - rx, cy - ry, cx + rx, cy + ry)
    if name == "line":
        x1, y1, x2, y2 = g("x1"), g("y1"), g("x2"), g("y2")
        if None in (x1, y1, x2, y2): return None
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    if name in ("polyline", "polygon"):
        pts = re.findall(NUM + r"[,\s]+" + NUM, tag)
        if not pts: return None
        xs = [float(a) for a, b in pts]; ys = [float(b) for a, b in pts]
        return (min(xs), min(ys), max(xs), max(ys))
    return None

def check():
    errs, warns = [], []
    all_ids = {}
    frags = sorted(glob.glob(os.path.join(nch.SRC, "ch*.html"))) + \
            sorted(glob.glob(os.path.join(nch.SRC, "apx_*.html")))
    for fp in frags:
        doc = open(fp, encoding="utf-8-sig").read()
        fname = os.path.basename(fp)
        for si, sm in enumerate(SVGSVG.finditer(doc), 1):
            W, H, body = float(sm.group(1)), float(sm.group(2)), sm.group(3)
            whole = sm.group(0)
            fig = "%s#svg%d" % (fname, si)
            if "&nbsp;" in whole or "&#160;" in whole:
                errs.append("%s: 裸 &nbsp;" % fig)
            if "<!--" in whole:
                errs.append("%s: SVG 内注释" % fig)
            if re.search(r"<text[^>]*transform=\"[^\"]*rotate", whole):
                errs.append("%s: 旋转文字" % fig)
            for idm in ID_RE.finditer(whole):
                iid = idm.group(1)
                if iid in all_ids:
                    errs.append("%s: id 重复 %s（先见于 %s）" % (fig, iid, all_ids[iid]))
                else:
                    all_ids[iid] = fig
            for tm in TEXT_RE.finditer(whole):
                content = re.sub(r"<[^>]+>", "", tm.group(1))
                if re.search(r"第\s*\d+\s*章|附录\s*[A-D]", content):
                    errs.append("%s: 图内禁词「%s」" % (fig, content.strip()[:20]))
            for em in ELEM_RE.finditer(whole):
                bb = elem_bbox(em)
                if bb is None: continue
                x0, y0, x1, y1 = bb
                if x0 < -1 or y0 < -1 or x1 > W + 1 or y1 > H + 1:
                    txt = ""
                    if em.group(1) == "text":
                        mm = re.search(r">([^<]*)</text>", em.group(0), re.S)
                        if mm: txt = re.sub(r"<[^>]+>", "", mm.group(1))[:18]
                    errs.append("%s: %s 出画布 (%.0f,%.0f)-(%.0f,%.0f) 画布 %.0fx%.0f %s" % (
                        fig, em.group(1), x0, y0, x1, y1, W, H, txt))
                elif x0 < 8 or y0 < 8 or x1 > W - 8 or y1 > H - 8:
                    warns.append("%s: 元素贴边 (%.0f,%.0f)-(%.0f,%.0f)/%.0fx%.0f" % (
                        fig, x0, y0, x1, y1, W, H))
            for em in re.finditer(r"<text([^>]*)>", whole):
                if "text-anchor" not in em.group(1):
                    errs.append("%s: text 缺 text-anchor「%s」" % (fig, em.group(1)[:40]))
    return errs, warns

if __name__ == "__main__":
    errs, warns = check()
    for e in errs: print("ERR", e)
    for w in warns: print("WARN", w)
    print("svg_check: %d err, %d warn" % (len(errs), len(warns)))
    sys.exit(1 if errs else 0)
