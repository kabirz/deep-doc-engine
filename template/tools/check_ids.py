"""check_ids.py — 片段结构检查：id 唯一、章号、每章要素（节数/图/代码块/表/要点/lead）、注释"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch

H2_RE = re.compile(r"<h2 id=\"([^\"]+)\">(.*?)</h2>", re.S)
H3_RE = re.compile(r"<h3 id=\"([^\"]+)\">(.*?)</h3>", re.S)
TAG = re.compile(r"<[^>]+>")

def run(allow_partial=False):
    errs, warns = [], []
    frags = sorted(glob.glob(os.path.join(nch.SRC, "ch*.html"))) + \
            sorted(glob.glob(os.path.join(nch.SRC, "apx_*.html")))
    all_ids = {}
    seen = []
    for fp in frags:
        fname = os.path.basename(fp)
        doc = open(fp, encoding="utf-8-sig", errors="replace").read()
        if "<!--" in doc:
            errs.append("%s: 含 HTML 注释" % fname)
        # 双重编码乱码特征（UTF-8 被按 Latin-1/GBK 再编码）
        for bad in ("Ã©", "Ã¨", "ä¸", "æ", "锟", "\ufffd", "å"):
            if bad in doc:
                errs.append("%s: 疑似双重编码乱码（含 %r）" % (fname, bad))
                break
        if not doc.lstrip().startswith("<h2"):
            errs.append("%s: 片段未以 <h2 开头" % fname)
        for idm in re.finditer(r"\bid=\"([^\"]+)\"", doc):
            iid = idm.group(1)
            if iid in all_ids:
                errs.append("%s: id 重复 %s（先见于 %s）" % (fname, iid, all_ids[iid]))
            else:
                all_ids[iid] = fname
        h2 = H2_RE.search(doc)
        if not h2:
            errs.append("%s: 无 h2" % fname)
            continue
        t = TAG.sub("", h2.group(2))
        mc = re.match(r"第 (\d+) 章(?: · )?\s*(.*)", t)
        if mc:
            ch = int(mc.group(1))
            seen.append(ch)
            if ch > nch.NCH:
                errs.append("%s: 章号 %d 超出 NCH=%d" % (fname, ch, nch.NCH))
            h3s = H3_RE.findall(doc)
            if len(h3s) < 6:
                errs.append("%s: h3 只有 %d 个（要求 ≥6）" % (fname, len(h3s)))
            figs = len(re.findall(r"<figure class=\"fig\"", doc))
            if figs < 3:
                errs.append("%s: 图只有 %d 张（要求 ≥3）" % (fname, figs))
            pres = len(re.findall(r"<pre class=\"(?:code|shell)\"", doc))
            if pres < 5:
                errs.append("%s: 代码块只有 %d 个（要求 ≥5）" % (fname, pres))
            tabs = len(re.findall(r"<table>", doc))
            if tabs < 1:
                errs.append("%s: 无表格" % fname)
            if '<p class="lead">' not in doc:
                errs.append("%s: 缺 lead 导读" % fname)
            if h3s:
                last_id, last_t = h3s[-1][0], TAG.sub("", h3s[-1][1])
                if "本章要点" not in last_t:
                    warns.append("%s: 最后 h3 不是本章要点（是「%s」）" % (fname, last_t[:20]))
            # h3 编号连续
            exp = 1
            for hid, ht in h3s:
                mt = TAG.sub("", ht)
                mm = re.match(r"(\d+)\.(\d+)", mt)
                if mm:
                    a, b = int(mm.group(1)), int(mm.group(2))
                    if a != ch:
                        errs.append("%s: h3 编号章前缀 %d != 章号 %d「%s」" % (fname, a, ch, mt[:18]))
                    if b != exp:
                        errs.append("%s: h3 编号不连续，期望 .%02d 实际 .%02d「%s」" % (fname, exp, b, mt[:18]))
                        exp = b
                    exp += 1
            if not os.path.exists(os.path.join(nch.SRC, "facts", "ch%02d.md" % ch)):
                warns.append("%s: 缺 facts/ch%02d.md" % (fname, ch))
        else:
            ma = re.match(r"附录 ([A-D])(?: · )?\s*(.*)", t)
            if not ma:
                errs.append("%s: h2 标题格式不符「%s」" % (fname, t[:24]))
            else:
                idx = "ABCD".index(ma.group(1))
                expect_id = "apx-" + ma.group(1).lower()
                if h2.group(1) != expect_id:
                    errs.append("%s: 附录 id 应为 %s" % (fname, expect_id))
                h3s = H3_RE.findall(doc)
                if len(h3s) < 4:
                    warns.append("%s: 附录 h3 只有 %d 个" % (fname, len(h3s)))
        # pre 内破碎标记
        for pm in re.finditer(r"<pre class=\"(?:code|shell)\"[^>]*>(.*?)</pre>", doc, re.S):
            if re.search(r"</?(p|div|h[1-6]|table)\b", pm.group(1)):
                errs.append("%s: pre 内出现块级标签（转义遗漏?）" % fname)
    if not allow_partial:
        missing = sorted(set(range(1, nch.NCH + 1)) - set(seen))
        if missing:
            errs.append("缺章: %s" % missing)
        if len(seen) != len(set(seen)):
            errs.append("章号重复: %s" % sorted({x for x in seen if seen.count(x) > 1}))
    n_apx = len([f for f in frags if os.path.basename(f).startswith("apx_")])
    if n_apx != nch.NAPX and not allow_partial:
        errs.append("附录数量 %d != %d" % (n_apx, nch.NAPX))
    return errs, warns

if __name__ == "__main__":
    ap = "--partial" in sys.argv
    errs, warns = run(allow_partial=ap)
    for e in errs[:80]: print("ERR", e)
    for w in warns[:40]: print("WARN", w)
    print("check_ids: %d err, %d warn%s" % (len(errs), len(warns), "（partial）" if ap else ""))
    sys.exit(1 if errs else 0)
