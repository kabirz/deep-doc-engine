"""xref_check.py — 章节交叉引用检查：「第 N 章」越界、「N.M 节」目标存在"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch

H2_RE = re.compile(r"<h2 id=\"([^\"]+)\">(.*?)</h2>", re.S)
H3_RE = re.compile(r"<h3 id=\"([^\"]+)\">(.*?)</h3>", re.S)
TAG = re.compile(r"<[^>]+>")

def run(partial=False):
    frags = sorted(glob.glob(os.path.join(nch.SRC, "ch*.html"))) + \
            sorted(glob.glob(os.path.join(nch.SRC, "apx_*.html")))
    chap_secs = {}   # 章号 -> set(节号 int.int)
    chap_nums = []
    for fp in frags:
        doc = open(fp, encoding="utf-8-sig").read()
        h2 = H2_RE.search(doc)
        if not h2:
            continue
        t = TAG.sub("", h2.group(2))
        m = re.match(r"第 (\d+) 章", t)
        if not m:
            continue
        ch = int(m.group(1))
        chap_nums.append(ch)
        secs = set()
        for h3 in H3_RE.finditer(doc):
            ht = TAG.sub("", h3.group(2))
            ms = re.match(r"(\d+)\.(\d+)", ht)
            if ms and int(ms.group(1)) == ch:
                secs.add((int(ms.group(1)), int(ms.group(2))))
        chap_secs[ch] = secs

    errs, warns, stat = [], [], {"xref_ch": 0, "xref_sec": 0}
    for fp in frags:
        doc = open(fp, encoding="utf-8-sig").read()
        fname = os.path.basename(fp)
        body = H2_RE.sub(" ", H3_RE.sub(" ", doc))
        for m in re.finditer(r"第\s*(\d+)\s*章", body):
            n = int(m.group(1))
            stat["xref_ch"] += 1
            if n not in chap_nums:
                msg = "%s: 引用第 %d 章，但该书不存在" % (fname, n)
                (warns if partial else errs).append(msg)
        for m in re.finditer(r"(\d+)\.(\d+)\s*节", body):
            a, b = int(m.group(1)), int(m.group(2))
            stat["xref_sec"] += 1
            if a not in chap_secs or (a, b) not in chap_secs[a]:
                msg = "%s: 引用 %d.%d 节，但目标节不存在" % (fname, a, b)
                (warns if partial else errs).append(msg)
    return errs, warns, stat

if __name__ == "__main__":
    partial = "--partial" in sys.argv
    errs, warns, stat = run(partial)
    for e in errs[:100]: print("ERR", e)
    for w in warns[:60]: print("WARN", w)
    print("xref_check: %d err, %d warn （章引用 %d，节引用 %d）%s" % (
        len(errs), len(warns), stat["xref_ch"], stat["xref_sec"], "（partial）" if partial else ""))
    sys.exit(1 if errs else 0)
