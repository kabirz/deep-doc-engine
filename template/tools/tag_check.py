"""tag_check.py — 行内格式标签平衡检查（strong/em/code/b/i/u/sub/sup/kbd/span）
未闭合的行内标签会跨片段污染后续章节样式（历史教训：ch19/ch34 未闭合 <code>
导致数章正文被染成玫红等宽）。构建链必跑。
"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
TAG = re.compile(r"</?(strong|em|code|b|i|u|sub|sup|kbd|span)\b[^>]*>")

def run():
    errs = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".html"):
            continue
        doc = open(os.path.join(SRC, f), encoding="utf-8-sig").read()
        doc2 = re.sub(r"<pre\b.*?</pre>", "", doc, flags=re.S)  # pre 内是代码正文
        stack = []
        for m in TAG.finditer(doc2):
            name = m.group(1)
            if m.group(0).startswith("</"):
                if stack and stack[-1] == name:
                    stack.pop()
                elif name in [s for s in stack]:
                    while stack and stack[-1] != name:
                        errs.append("%s: 交错闭合 </%s>，先弹未闭合 <%s>" % (f, name, stack[-1]))
                        stack.pop()
                    if stack:
                        stack.pop()
                else:
                    errs.append("%s: 多余闭合 </%s> 上下文: …%s…" % (
                        f, name, doc2[max(0, m.start()-60):m.start()].replace("\n", " ")[-50:]))
            else:
                stack.append(name)
        for name in stack:
            errs.append("%s: 未闭合 <%s>" % (f, name))
    return errs

if __name__ == "__main__":
    errs = run()
    for e in errs[:60]:
        print("ERR", e)
    print("tag_check: %d err" % len(errs))
    sys.exit(1 if errs else 0)
