"""全书唯一的事实来源：书名、章数、篇结构、路径。所有工具 import 本文件。
新工程只需改这个文件 + src/00_head.html 的封面，其余工具零改动。
"""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

# ── 引用源码树（cite_check 校验基准）；非源码类书籍设为 None 即跳过引用校验 ──
KSRC = None    # 例：r"C:\Users\me\Documents\code\linux-7.1.1"

# ── 书籍元信息（build_html 侧边栏/topbar/title、print_merged PDF 元数据共用）──
BOOK_TITLE = "示例书名深度详解"
BOOK_SUBTITLE = "副标题 · 基于某源码基线"
TOPBAR_TAGS = ["12 章 + 4 附录", "主题词一", "主题词二"]   # topbar 尾部小字，可空列表
META_TITLE = BOOK_TITLE + " · " + BOOK_SUBTITLE            # PDF 元数据 title

OUT_HTML = os.path.join(ROOT, BOOK_TITLE + ".html")
OUT_PDF = os.path.join(ROOT, BOOK_TITLE + ".pdf")

NCH = 12    # 正文章数（与 PLAN.md 一致；check_ids 断言 ch01..chNN 全在）
NAPX = 4    # 附录数 apx_a..apx_d
SPLIT = 6   # 分半打印分割章号（1..SPLIT 为上半；规避 Chromium 长任务字体退化）
MIN_LV2 = NCH * 4   # 节级书签数量下限（add_bookmarks 终检）

PARTS = [
    ("第一篇　基础", 1, 4),
    ("第二篇　核心", 5, 8),
    ("第三篇　进阶", 9, 12),
]

def fragment_order():
    """src/ 下的片段顺序：ch01..chNN（按编号）+ 附录。"""
    frags = [f for f in os.listdir(SRC) if re.match(r"ch\d+_.+\.html$", f)]
    frags.sort(key=lambda f: int(re.match(r"ch(\d+)_", f).group(1)))
    for a in "abcd"[:NAPX]:
        p = os.path.join(SRC, f"apx_{a}_*.html")
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
