"""line_check.py — SVG 文字与线段相交/过近检查；overlap_check 功能合并：文字-文字重叠"""
import os, re, sys, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch
from svg_check import SVGSVG, ELEM_RE, elem_bbox, NUM

def segs_of(whole):
    segs = []
    for em in re.finditer(r"<(line|path|polyline)\b[^>]*>", whole):
        tag = em.group(0)
        if "display=\"none\"" in tag or "visibility=\"hidden\"" in tag:
            continue
        def g(a):
            r = re.search(r"\b" + a + r"=\"\s*" + NUM, tag)
            return float(r.group(1)) if r else None
        if em.group(1) == "line":
            x1, y1, x2, y2 = g("x1"), g("y1"), g("x2"), g("y2")
            if None not in (x1, y1, x2, y2):
                segs.append(((x1, y1), (x2, y2)))
        elif em.group(1) == "polyline":
            pts = re.findall(NUM + r"[,\s]+" + NUM, tag)
            p = [(float(a), float(b)) for a, b in pts]
            segs += list(zip(p, p[1:]))
        else:  # path
            d = g("d") if False else None
            dm = re.search(r"\bd=\"([^\"]+)\"", tag)
            if not dm:
                continue
            toks = re.findall(r"[MLHVQCSTAZ]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", dm.group(1))
            i = 0; cur = (0.0, 0.0); start = cur; cmd = None
            def take(k):
                nonlocal i
                v = []
                for _ in range(k):
                    if i < len(toks):
                        try: v.append(float(toks[i]))
                        except ValueError: v.append(0.0)
                    else: v.append(0.0)
                    i += 1
                return v
            def sample(p0, p1, p2, p3, n=10):
                out = []
                for k in range(1, n + 1):
                    t = k / n; mt = 1 - t
                    out.append((mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0],
                                mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]))
                return out
            prev_ctrl = None
            while i < len(toks):
                t = toks[i]
                if t.isalpha():
                    cmd = t; i += 1
                    if cmd == "Z":
                        segs.append((cur, start)); cur = start; continue
                try:
                    if cmd == "M":
                        x, y = take(2); cur = (x, y); start = cur
                    elif cmd == "L":
                        x, y = take(2); segs.append((cur, (x, y))); cur = (x, y)
                    elif cmd == "H":
                        x = take(1)[0]; segs.append((cur, (x, cur[1]))); cur = (x, cur[1])
                    elif cmd == "V":
                        y = take(1)[0]; segs.append((cur, (cur[0], y))); cur = (cur[0], y)
                    elif cmd in "CS":
                        if cmd == "C":
                            x1, y1, x2, y2, x, y = take(6)
                        else:
                            x1, y1 = (2*cur[0]-prev_ctrl[0], 2*cur[1]-prev_ctrl[1]) if prev_ctrl else cur
                            x2, y2, x, y = take(4)
                        pts = [cur] + sample(cur, (x1, y1), (x2, y2), (x, y))
                        segs += list(zip(pts, pts[1:])); prev_ctrl = (x2, y2); cur = (x, y)
                    elif cmd in "QT":
                        if cmd == "Q":
                            x1, y1, x, y = take(4)
                        else:
                            x1, y1 = (2*cur[0]-prev_ctrl[0], 2*cur[1]-prev_ctrl[1]) if prev_ctrl else cur
                            x, y = take(2)
                        pts = [cur]
                        for k in range(1, 11):
                            t0 = k / 10; mt = 1 - t0
                            pts.append((mt*mt*cur[0] + 2*mt*t0*x1 + t0*t0*x, mt*mt*cur[1] + 2*mt*t0*y1 + t0*t0*y))
                        segs += list(zip(pts, pts[1:])); prev_ctrl = (x1, y1); cur = (x, y)
                    elif cmd == "A":
                        v = take(7); x, y = v[5], v[6]
                        segs.append((cur, (x, y))); cur = (x, y)
                    else:
                        i += 1
                except Exception:
                    break
    return segs

def pt_in_bb(p, bb, pad=1.0):
    return bb[0]-pad <= p[0] <= bb[2]+pad and bb[1]-pad <= p[1] <= bb[3]+pad

def seg_bb_hit(s, bb):
    (x1, y1), (x2, y2) = s
    if pt_in_bb((x1, y1), bb) or pt_in_bb((x2, y2), bb):
        return True
    n = max(2, int(math.hypot(x2-x1, y2-y1) / 3))
    for k in range(n + 1):
        t = k / n
        if pt_in_bb((x1+(x2-x1)*t, y1+(y2-y1)*t), bb):
            return True
    return False

def seg_bb_dist(s, bb):
    if seg_bb_hit(s, bb):
        return 0.0
    (x1, y1), (x2, y2) = s
    n = max(2, int(math.hypot(x2-x1, y2-y1) / 4))
    best = 1e9
    for k in range(n + 1):
        t = k / n
        px, py = x1+(x2-x1)*t, y1+(y2-y1)*t
        dx = max(bb[0]-px, 0, px-bb[2]); dy = max(bb[1]-py, 0, py-bb[3])
        best = min(best, math.hypot(dx, dy))
    return best

def run():
    errs, warns = [], []
    frags = sorted(glob.glob(os.path.join(nch.SRC, "ch*.html"))) + \
            sorted(glob.glob(os.path.join(nch.SRC, "apx_*.html")))
    for fp in frags:
        doc = open(fp, encoding="utf-8-sig").read()
        fname = os.path.basename(fp)
        for si, sm in enumerate(SVGSVG.finditer(doc), 1):
            whole = sm.group(0)
            fig = "%s#svg%d" % (fname, si)
            segs = segs_of(whole)
            texts = []
            for em in ELEM_RE.finditer(whole):
                if em.group(1) != "text":
                    continue
                bb = elem_bbox(em)
                mm = re.search(r">([^<]*)</text>", em.group(0), re.S)
                label = re.sub(r"<[^>]+>", "", mm.group(1)).strip()[:16] if mm else "?"
                if bb and label:
                    texts.append((bb, label))
            for bb, label in texts:
                for s in segs:
                    d = seg_bb_dist(s, bb)
                    if d <= 1.0:
                        errs.append("%s: 线穿字「%s」 seg=(%.0f,%.0f)-(%.0f,%.0f)" % (
                            fig, label, s[0][0], s[0][1], s[1][0], s[1][1]))
                        break
                    elif d < 5.0:
                        warns.append("%s: 字贴线 %.1fpx「%s」" % (fig, d, label))
                        break
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    a, b = texts[i][0], texts[j][0]
                    ox = min(a[2], b[2]) - max(a[0], b[0])
                    oy = min(a[3], b[3]) - max(a[1], b[1])
                    if ox > 2 and oy > 2:
                        area = ox * oy
                        small = min((a[2]-a[0])*(a[3]-a[1]), (b[2]-b[0])*(b[3]-b[1]))
                        if area > 0.35 * small:
                            errs.append("%s: 字重叠「%s」「%s」" % (fig, texts[i][1], texts[j][1]))
    return errs, warns

if __name__ == "__main__":
    errs, warns = run()
    for e in errs[:120]: print("ERR", e)
    for w in warns[:60]: print("WARN", w)
    print("line_check: %d err, %d warn" % (len(errs), len(warns)))
    sys.exit(1 if errs else 0)
