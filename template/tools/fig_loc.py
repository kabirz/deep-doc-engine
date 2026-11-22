"""fig_loc.py — 定位某章文件中所有「图 N-K」出现处（行号+上下文）"""
import re, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
name, ch = sys.argv[1], int(sys.argv[2])
doc = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", name),
           encoding="utf-8-sig").read()
print("==" + name + "==")
for m in re.finditer(r"图\s*%d-(\d+)" % ch, doc):
    ln = doc.count("\n", 0, m.start()) + 1
    ctx = doc[max(0, m.start() - 46):m.end() + 34].replace("\n", " ")
    print("L%d: ...%s..." % (ln, ctx))
