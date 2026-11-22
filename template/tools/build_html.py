"""build_html.py — 拼接片段 -> 单页 HTML（侧边栏 + 目录 + Dracula 构建期高亮）"""
import os, re, sys, html, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch
from pygments import highlight as pyg_highlight
from pygments.util import ClassNotFound
from pygments.lexers import CLexer, CppLexer, BashLexer, JsonLexer, MarkdownLexer, CMakeLexer
from pygments.formatters import HtmlFormatter

FMT = HtmlFormatter(nowrap=True, noclasses=True, style="dracula")
LEXERS = {"c": CLexer, "cpp": CppLexer, "glsl": CppLexer, "sh": BashLexer,
          "bash": BashLexer, "json": JsonLexer, "md": MarkdownLexer, "markdown": MarkdownLexer,
          "cmake": CMakeLexer}

H2_RE = re.compile(r'<h2 id="([^"]+)">(.*?)</h2>', re.S)
H3_RE = re.compile(r'<h3 id="([^"]+)">(.*?)</h3>', re.S)
PRE_RE = re.compile(r'<pre class="(code|shell)"(?:\s+data-lang="(\w+)")?>(.*?)</pre>', re.S)
TAG_RE = re.compile(r"<[^>]+>")

def strip_tags(s):
    return TAG_RE.sub("", s).strip()

def hl_one(kind, lang, body):
    """body: 已转义的代码文本 -> 高亮后的转义 HTML"""
    raw = html.unescape(body).strip("\n")
    if lang == "sh" or lang is None and kind == "shell":
        lang = "sh"
    lex = None
    if lang and lang in LEXERS:
        lex = LEXERS[lang]()
    if lex is None:
        try:
            lex = LEXERS.get("c", CLexer)() if lang == "text" else None
        except ClassNotFound:
            lex = None
    if lang in ("text", None) and lex is None:
        out = html.escape(raw)
    else:
        out = pyg_highlight(raw, lex, FMT).strip("\n")
    if lang == "sh":
        out = re.sub(r"^(\s*)(\$)( )", r'\1<span style="color:#50fa7b;font-weight:700">$3</span>', out, flags=re.M)
    tag = (lang or "sh").upper()
    return '<span class="lang-tag">%s</span>%s' % (tag, out)

def highlight_all(doc):
    def rep(m):
        kind, lang, body = m.group(1), m.group(2), m.group(3)
        return '<pre class="%s" data-lang="%s">%s</pre>' % (kind, lang or "sh", hl_one(kind, lang, body))
    return PRE_RE.sub(rep, doc)

def parse_head():
    src = open(os.path.join(nch.SRC, "00_head.html"), encoding="utf-8").read()
    style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    cover = src[src.index('<div class="cover">'):]
    return style, cover

def collect():
    frags = []
    for f in nch.fragment_order():
        frags.append((f, open(os.path.join(nch.SRC, f), encoding="utf-8").read()))
    return frags

def toc_entry_labels():
    """[(kind, num, id, title_html, part)]"""
    out = []
    for f, doc in collect():
        h2 = H2_RE.search(doc)
        if not h2:
            print("无 h2:", f); continue
        fid, ftitle = h2.group(1), h2.group(2)
        m = re.match(r"第 (\d+) 章(?: · | ·)?\s*(.*)", strip_tags(ftitle))
        if m:
            num, title = int(m.group(1)), m.group(2)
            out.append(("ch", num, fid, title, nch.part_of(num)))
        else:
            m2 = re.match(r"附录 ([A-D])(?: · | ·)?\s*(.*)", strip_tags(ftitle))
            if m2:
                num = nch.NCH + "ABCD".index(m2.group(1)) + 1
                out.append(("apx", num, fid, m2.group(2), "附录"))
            else:
                out.append(("front", 0, fid, strip_tags(ftitle), "目录"))
    return out

def build_sidebar(entries):
    import html as _h
    buf = ['<div class="sidebar"><div class="sb-head"><div class="t">%s</div>'
           '<div class="s">%s</div></div><nav class="sb-nav">' % (nch.BOOK_TITLE, nch.BOOK_SUBTITLE)]
    cur_part = None
    for kind, num, fid, title, part in entries:
        if part != cur_part and part:
            cur_part = part
            buf.append('<div class="sb-part">%s</div>' % part)
        label = ("第 %d 章 · %s" % (num, title)) if kind == "ch" else (
            "附录 %s · %s" % ("ABCD"[num - nch.NCH - 1], title) if kind == "apx" else "目录")
        cls = "ch apx" if kind == "apx" else "ch"
        buf.append('<a class="%s" href="#%s">%s</a>' % (cls, fid, label))
    buf.append("</nav></div>")
    return "\n".join(buf)

def build_toc(entries):
    buf = ['<h2 id="toc-h">目录</h2>']
    cur_part = None
    for kind, num, fid, title, part in entries:
        if part != cur_part and part:
            cur_part = part
            buf.append('<div class="toc-part">%s</div>' % part)
        if kind == "ch":
            label = "第 %d 章 · %s" % (num, title)
            buf.append('<div class="toc-line"><a href="#%s">%s</a><span class="dots"></span><span class="n">%d</span></div>' % (fid, label, num))
        elif kind == "apx":
            label = "附录 %s · %s" % ("ABCD"[num - nch.NCH - 1], title)
            buf.append('<div class="toc-line"><a href="#%s">%s</a><span class="dots"></span><span class="n">A</span></div>' % (fid, label))
    # 二级目录：章内 h3
    return "\n".join(buf)

def build_toc2(entries_by_file):
    """带 h3 的完整目录；若 _toc_pages.json 存在则用真实 PDF 页码"""
    import json
    pages = {}
    pfile = os.path.join(nch.ROOT, "_toc_pages.json")
    if os.path.exists(pfile):
        pages = json.load(open(pfile, encoding="utf-8"))
    buf = ['<h2 id="toc-h">目录</h2>']
    cur_part = None
    for f, doc in collect():
        h2 = H2_RE.search(doc)
        if not h2:
            continue
        fid, ftitle = h2.group(1), strip_tags(h2.group(2))
        m = re.match(r"第 (\d+) 章(?: · )?\s*(.*)", ftitle)
        kind = "ch"
        if not m:
            m = re.match(r"附录 ([A-D])(?: · )?\s*(.*)", ftitle)
            kind = "apx"
            if not m:
                kind = "front"; label, num = ftitle, 0
            else:
                num = nch.NCH + "ABCD".index(m.group(1)) + 1
                label = "附录 %s · %s" % (m.group(1), m.group(2))
        else:
            num = int(m.group(1)); label = "第 %d 章 · %s" % (num, m.group(2))
        part = "目录" if kind == "front" else (nch.part_of(num) if kind == "ch" else "附录")
        if part != cur_part and part:
            cur_part = part
            buf.append('<div class="toc-part">%s</div>' % part)
        if kind != "front":
            shown = pages.get(fid, num)
            buf.append('<div class="toc-line"><a href="#%s">%s</a><span class="dots"></span><span class="n">%s</span></div>' % (fid, label, shown))
        for hm in H3_RE.finditer(doc):
            hid, htitle = hm.group(1), strip_tags(hm.group(2))
            buf.append('<div class="toc-line lv3"><a href="#%s">%s</a></div>' % (hid, htitle))
    return "\n".join(buf)

def wbr_code(doc):
    """行内 <code>（非 pre 内）插入零宽断点：_ / . - 与驼峰边界后。
    使表格在 word-break:normal 下仍能按语义边界折行（段最小宽度大幅下降）。"""
    codes = []
    def stash(m):
        codes.append(m.group(0))
        return "\x00CODE%d\x00" % (len(codes) - 1)
    doc = re.sub(r"<pre\b.*?</pre>", stash, doc, flags=re.S)          # 保护代码块

    def wbr_text(seg):
        seg = re.sub(r"([_/.])", r"\1<wbr>", seg)
        seg = re.sub(r"([a-z0-9])([A-Z])", r"\1<wbr>\2", seg)
        return seg

    def wbr_cell(m):
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        parts = re.split(r"(<[^>]+>)", body)
        for i in range(len(parts)):
            if parts[i] and not parts[i].startswith("<"):
                parts[i] = wbr_text(parts[i])
        return open_tag + "".join(parts) + close_tag

    def wbr_one(m):
        return m.group(1) + wbr_text(m.group(2)) + m.group(3)
    doc = re.sub(r"(<code>)(.*?)(</code>)", wbr_one, doc, flags=re.S)  # 行内 code
    doc = re.sub(r"(<t[dh]>)(.*?)(</t[dh]>)", wbr_cell, doc, flags=re.S)  # 单元格裸文本
    def unstash(m):
        return codes[int(m.group(1))]
    doc = re.sub(r"\x00CODE(\d+)\x00", unstash, doc)
    return doc

def main():
    allow_partial = "--partial" in sys.argv
    rng = None
    out_path = None
    for a in sys.argv[1:]:
        if a.startswith("--range="):
            a_, b_ = a.split("=", 1)[1].split(":")
            rng = (int(a_), int(b_))
        elif a.startswith("--out="):
            out_path = a.split("=", 1)[1]
    style, cover = parse_head()
    frags = collect()
    if rng is not None:
        keep = []
        for f, doc in frags:
            h2 = H2_RE.search(doc)
            t = strip_tags(h2.group(2))
            mc = re.match(r"第 (\d+) 章", t)
            if mc:
                ch = int(mc.group(1))
                if rng[0] <= ch <= rng[1]:
                    keep.append((f, doc))
            elif rng[1] > nch.NCH:      # 附录归入末段
                keep.append((f, doc))
        frags = keep
    # 校验章号连续（range 模式下只校验范围段）
    nums = []
    for f, doc in frags:
        m = H2_RE.search(doc)
        if not m:
            print("!! 片段缺 h2:", f); sys.exit(1)
        t = strip_tags(m.group(2))
        mm = re.match(r"第 (\d+) 章", t)
        if mm:
            nums.append(int(mm.group(1)))
    expect = list(range(rng[0], rng[1] + 1)) if rng else list(range(1, nch.NCH + 1))
    expect = [x for x in expect if x <= nch.NCH]
    if nums != expect:
        missing = sorted(set(expect) - set(nums))
        dup = sorted({x for x in nums if nums.count(x) > 1})
        msg = "!! 章号不连续/缺失: 缺%s 重复%s 现有%d章" % (missing, dup, len(nums))
        if allow_partial or rng:
            print(msg + "（range/partial，允许继续）")
        else:
            print(msg)
            sys.exit(1)
    body_parts = [highlight_all(doc) for _, doc in frags]
    head_mode = (rng is None) or (rng[0] == 1)
    toc2 = build_toc2(frags) if head_mode else ""
    if head_mode:
        body = '\n<!--TOC-->\n<div class="toc-page">\n%s\n</div>\n<!--BODY-->\n%s' % (toc2, "\n".join(body_parts))
    else:
        body = "\n".join(body_parts)
    # 章标题补 class：ch（正章）/ ch apx（附录），打印分页与样式依赖它
    body = re.sub(r'<h2 id="(ch\d+)"', r'<h2 class="ch" id="\1"', body)
    body = wbr_code(body)
    body = re.sub(r'<h2 id="(apx-[a-d])"', r'<h2 class="ch apx" id="\1"', body)
    body = body.replace("<h2 ", '<h2 ', 1)
    sidebar_html = build_sidebar(toc_entry_labels()) if head_mode else ""
    cover_html = cover if head_mode else ""
    full = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
%s
</style>
</head>
<body>
%s
<div class="wrap">
<div class="topbar"><b>%s</b><span>%s</span>%s</div>
<main class="content">
%s
%s
</main>
</div>
<script>
/* 侧边栏当前章高亮 */
(function(){
  var hs=[].slice.call(document.querySelectorAll('main h2'));
  var nav=[].slice.call(document.querySelectorAll('.sb-nav a'));
  function cur(){
    var y=window.scrollY+90, best=null;
    hs.forEach(function(h){ if(h.offsetTop<=y) best=h; });
    nav.forEach(function(a){ a.classList.toggle('cur', best&&a.getAttribute('href')==='#'+best.id); });
  }
  addEventListener('scroll', cur, {passive:true}); cur();
})();
</script>
</body>
</html>""" % (nch.META_TITLE, nch.BOOK_TITLE, nch.BOOK_SUBTITLE,
              "".join('<span>·</span><span>%s</span>' % t for t in nch.TOPBAR_TAGS),
              style, sidebar_html, cover_html, body)
    full = full.replace("<main class=\"content\">\n%s\n</main>", "")  # noop 防御
    out = full
    target = out_path or nch.OUT_HTML
    open(target, "w", encoding="utf-8-sig").write(out)
    n_fig = len(re.findall(r"<figure class=\"fig\"", out))
    n_pre = len(re.findall(r"<pre class=\"(?:code|shell)\"", out))
    n_tab = len(re.findall(r"<table>", out))
    n_h3 = len(re.findall(r"<h3 ", out))
    print("HTML 完成: %s  (%.2f MB, 章%d, h3=%d, 图=%d, 代码块=%d, 表=%d)" % (
        target, len(out.encode('utf-8'))/1048576, len(nums), n_h3, n_fig, n_pre, n_tab))

if __name__ == "__main__":
    main()
