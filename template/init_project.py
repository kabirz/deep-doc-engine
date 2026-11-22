#!/usr/bin/env python3
"""init_project.py — 从 template 一键初始化新的文档工程。

用法：
    python init_project.py --dir ../my_doc --title "书名深度详解" \
        --subtitle "副题 · 基线" [--nch 12] [--napx 4] [--ksrc "C:\\path\\to\\src"]

做五件事：
  1. 复制 template/（tools + src + 四个规范文档）到目标目录
  2. 生成定制的 nch.py（书名/章数/篇结构占位/输出路径）
  3. 替换 00_head.html 封面占位符
  4. 生成可直接跑通构建链的示例章 ch01 + facts/ch01.md
  5. 打印下一步操作提示

依赖（打印提示，不自动安装）：pygments、pymupdf；PDF 需 Microsoft Edge。
"""
import argparse, os, re, shutil, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

NCH_TMPL = '''"""全书唯一的事实来源：书名、章数、篇结构、路径。所有工具 import 本文件。
新工程只需改这个文件 + src/00_head.html 的封面，其余工具零改动。
"""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

KSRC = {ksrc!r}    # 引用源码树（cite_check 校验基准）；非源码类书籍保持 None

BOOK_TITLE = {title!r}
BOOK_SUBTITLE = {subtitle!r}
TOPBAR_TAGS = ["{nch} 章 + {napx} 附录"]
META_TITLE = BOOK_TITLE + " · " + BOOK_SUBTITLE

OUT_HTML = os.path.join(ROOT, BOOK_TITLE + ".html")
OUT_PDF = os.path.join(ROOT, BOOK_TITLE + ".pdf")

NCH = {nch}
NAPX = {napx}
SPLIT = max(1, NCH // 2)      # 分半打印分割章号
MIN_LV2 = NCH * 4             # 节级书签数量下限

PARTS = [
    ("正文", 1, NCH),         # TODO: 按实际分篇改写，例 ("第一篇　基础", 1, 4),
]

def fragment_order():
    """src/ 下的片段顺序：ch01..chNN（按编号）+ 附录。"""
    frags = [f for f in os.listdir(SRC) if re.match(r"ch\\d+_.+\\.html$", f)]
    frags.sort(key=lambda f: int(re.match(r"ch(\\d+)_", f).group(1)))
    for a in "abcd"[:NAPX]:
        p = os.path.join(SRC, f"apx_{{a}}_*.html")
        import glob
        m = glob.glob(p)
        if m:
            frags.append(os.path.basename(m[0]))
    return frags

def part_of(chno):
    for title, a, b in PARTS:
        if a <= chno <= b:
            return title
    return "附录" if chno > NCH else ""

def is_apx(chno):
    return chno > NCH
'''

CH01 = '''<h2 id="ch01">第 1 章 · 示例章：管线自检</h2>
<p class="lead">本章是模板自带的示例章，用来验证构建链可用。开工时删除本章、按 PLAN.md 写正式章节即可。</p>

<h3 id="ch01-01">1.1 代码块写法</h3>
<p>代码块只写转义纯文本，构建器用 Pygments Dracula 在构建期高亮（作者禁手写 span）：</p>
<pre class="code" data-lang="c">#include &lt;stdio.h&gt;

int main(void)
{
    printf("hello, deep-doc\\n");
    return 0;
}</pre>
<p>shell 块的 <code>$</code> 提示符会被构建器染绿：</p>
<pre class="code" data-lang="sh">$ python tools/build_all.py --partial
全部完成 ✓</pre>

<h3 id="ch01-02">1.2 手绘 SVG 三则</h3>
<figure class="fig">
<svg viewBox="0 0 760 200" font-family="'Segoe UI','Microsoft YaHei',sans-serif">
  <defs><marker id="arrow-ch01-1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6b7280"/></marker></defs>
  <rect x="60" y="70" width="180" height="60" rx="8" fill="#eef2ff" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="150" y="105" font-size="13" fill="#1f2937" text-anchor="middle">src/ 章节片段</text>
  <line x1="245" y1="100" x2="335" y2="100" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow-ch01-1)"/>
  <rect x="340" y="70" width="180" height="60" rx="8" fill="#f0fdf4" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="430" y="98" font-size="13" fill="#1f2937" text-anchor="middle">build_all.py</text>
  <text x="430" y="118" font-size="11" fill="#6b7280" text-anchor="middle">HTML + 检查 + PDF</text>
  <line x1="525" y1="100" x2="615" y2="100" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow-ch01-1)"/>
  <rect x="620" y="70" width="100" height="60" rx="8" fill="#fef3c7" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="670" y="105" font-size="13" fill="#1f2937" text-anchor="middle">交付</text>
</svg>
<figcaption>图 1-1 · 构建管线一览</figcaption>
</figure>
<figure class="fig">
<svg viewBox="0 0 760 220" font-family="'Segoe UI','Microsoft YaHei',sans-serif">
  <rect x="80" y="30" width="600" height="44" rx="8" fill="#eef2ff" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="380" y="58" font-size="14" fill="#1e3a8a" text-anchor="middle" font-weight="700">封面与目录（00_head.html）</text>
  <rect x="80" y="86" width="600" height="44" rx="8" fill="#f0fdf4" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="380" y="114" font-size="14" fill="#1f2937" text-anchor="middle">章节片段 ch01..chNN + 附录</text>
  <rect x="80" y="142" width="600" height="44" rx="8" fill="#fef3c7" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="380" y="170" font-size="14" fill="#1f2937" text-anchor="middle">单页 HTML（侧边栏 + 构建期高亮）→ PDF</text>
</svg>
<figcaption>图 1-2 · 文档分层结构</figcaption>
</figure>
<figure class="fig">
<svg viewBox="0 0 760 240" font-family="'Segoe UI','Microsoft YaHei',sans-serif">
  <defs><marker id="arrow-ch01-2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6b7280"/></marker></defs>
  <rect x="100" y="20" width="140" height="40" rx="8" fill="#eef2ff" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="170" y="45" font-size="13" fill="#1f2937" text-anchor="middle">作者</text>
  <line x1="170" y1="60" x2="170" y2="200" stroke="#c9cfda" stroke-width="1.5" stroke-dasharray="6 4"/>
  <rect x="420" y="20" width="140" height="40" rx="8" fill="#eef2ff" stroke="#8a93a5" stroke-width="1.5"/>
  <text x="490" y="45" font-size="13" fill="#1f2937" text-anchor="middle">检查器</text>
  <line x1="490" y1="60" x2="490" y2="200" stroke="#c9cfda" stroke-width="1.5" stroke-dasharray="6 4"/>
  <line x1="180" y1="100" x2="480" y2="100" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow-ch01-2)"/>
  <text x="330" y="90" font-size="12" fill="#374151" text-anchor="middle">提交片段</text>
  <line x1="480" y1="150" x2="180" y2="150" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow-ch01-2)"/>
  <text x="330" y="140" font-size="12" fill="#374151" text-anchor="middle">报错清单</text>
</svg>
<figcaption>图 1-3 · 写作-检查往返时序</figcaption>
</figure>

<h3 id="ch01-03">1.3 表格写法</h3>
<table>
<thead><tr><th>阶段</th><th>工具</th><th>作用</th></tr></thead>
<tbody>
<tr><td><code>build_html</code></td><td>Pygments Dracula</td><td>片段拼接与构建期高亮</td></tr>
<tr><td><code>*_check</code></td><td>六项检查器</td><td>结构/标签/SVG 几何/引用/交叉引用</td></tr>
<tr><td><code>print_merged</code></td><td>Edge headless</td><td>分半打印合并出 PDF</td></tr>
</tbody>
</table>

<h3 id="ch01-04">1.4 提示框写法</h3>
<div class="tip">💡 <strong>提示：</strong>改完任何片段后重跑 <code>python tools\\build_all.py</code> 即可一键重建。</div>
<div class="warn">⚠️ <strong>注意：</strong>片段内禁止 HTML 注释，历史工程发生过注释吞章事故。</div>

<h3 id="ch01-05">1.5 更多语言块</h3>
<pre class="code" data-lang="text">纯文本块：无 lexer，原样输出（浅色环境用）。</pre>
<pre class="code" data-lang="json">{"book": "示例书", "nch": 2, "napx": 4}</pre>
<pre class="code" data-lang="c">/* 短块：转义演示 &lt;tag&gt; &amp; &amp;&amp; */</pre>

<h3 id="ch01-99">本章要点</h3>
<ul>
<li>示例章仅用于管线自检，开工时删除。</li>
<li>写作规范见 AGENTS_STYLE.md，图形规范见 SVG_GUIDE.md。</li>
<li>全书配置集中在 tools/nch.py。</li>
</ul>
'''

FACTS_CH01 = '''# 第 1 章实测事实

- 示例条目：模板管线顺序为 build_html → 六项检查 → 分半打印 → 两遍法页码 → 书签 → 终检（出处：tools/build_all.py）。
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="新工程目录（相对或绝对路径）")
    ap.add_argument("--title", required=True, help="书名（也是输出 HTML/PDF 文件名）")
    ap.add_argument("--subtitle", default="", help="副标题")
    ap.add_argument("--nch", type=int, default=12)
    ap.add_argument("--napx", type=int, default=4, choices=[0, 1, 2, 3, 4])
    ap.add_argument("--ksrc", default=None, help="引用源码树根（不配则跳过 cite_check）")
    args = ap.parse_args()

    dst = os.path.abspath(args.dir)
    if os.path.exists(dst) and os.listdir(dst):
        print("!! 目标目录非空:", dst); sys.exit(1)
    os.makedirs(dst, exist_ok=True)

    # 1. 复制模板
    for item in ("tools", "src", "PLAN.md", "AGENTS_STYLE.md", "SVG_GUIDE.md", "FACTS.md"):
        s = os.path.join(HERE, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__", "_pycache_"))
        else:
            shutil.copy2(s, d)

    # 2. 生成定制 nch.py
    with open(os.path.join(dst, "tools", "nch.py"), "w", encoding="utf-8") as f:
        f.write(NCH_TMPL.format(ksrc=args.ksrc, title=args.title,
                                subtitle=args.subtitle or "副标题",
                                nch=args.nch, napx=args.napx))

    # 3. 替换封面占位符（glyph/chips/简介留手改）
    head_p = os.path.join(dst, "src", "00_head.html")
    head = open(head_p, encoding="utf-8").read()
    now = datetime.date.today()
    rep = {"{{BOOK_TITLE}}": args.title, "{{BOOK_SUBTITLE}}": args.subtitle or "副标题",
           "{{YEAR}}": str(now.year), "{{MONTH}}": str(now.month),
           "{{N_PARTS}}": "1", "{{NCH}}": str(args.nch), "{{NAPX}}": str(args.napx)}
    for k, v in rep.items():
        head = head.replace(k, v)
    open(head_p, "w", encoding="utf-8").write(head)

    # 4. 示例章 + facts
    os.makedirs(os.path.join(dst, "src", "facts"), exist_ok=True)
    open(os.path.join(dst, "src", "ch01_demo.html"), "w", encoding="utf-8").write(CH01)
    open(os.path.join(dst, "src", "facts", "ch01.md"), "w", encoding="utf-8").write(FACTS_CH01)

    # 5. 提示
    print("工程已创建:", dst)
    print("""
下一步：
  1. 编辑 src/00_head.html 封面（glyph/简介/chips/篇数）与 tools/nch.py 的 PARTS 分篇
  2. 写 PLAN.md 章节规划；按 AGENTS_STYLE.md 写 src/chNN_*.html
  3. 跑通自检：  python tools\\build_all.py --partial --min=2
  4. 全书完成后：python tools\\build_all.py
依赖：pygments、pymupdf（PDF 需 Microsoft Edge）""")


if __name__ == "__main__":
    main()
