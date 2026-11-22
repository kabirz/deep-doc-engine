"""print_merged.py — 分半打印 + pymupdf 合并（规避 Chromium 长任务字体缓存退化）
流程：build part1/part2 HTML -> Edge 打印两份 -> 合并 -> 落 OUT_PDF
用法：python print_merged.py [--verify]
"""
import io, sys, os, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import nch
import pymupdf

SPLIT = nch.SPLIT    # 1..SPLIT 为上半（分半打印规避 Chromium 长任务字体缓存退化）
PART1 = os.path.join(ROOT, "_part1.html")
PART2 = os.path.join(ROOT, "_part2.html")
P1 = os.path.join(ROOT, "_p1.pdf")
P2 = os.path.join(ROOT, "_p2.pdf")

def sh(args):
    r = subprocess.run(args, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(r.returncode)

def main():
    import re
    bh = os.path.join(HERE, "build_html.py")
    ps = os.path.join(HERE, "print_pdf.ps1")
    # 后半段（>SPLIT 的章 + 附录）为空时退化单次打印（迷你书），避免打出空白半本
    later = []
    for f in nch.fragment_order():
        m = re.match(r"ch(\d+)_", f)
        if (m and int(m.group(1)) > SPLIT) or not m:
            later.append(f)
    if later:
        sh([sys.executable, bh, "--range=1:%d" % SPLIT, "--out=" + PART1])
        sh([sys.executable, bh, "--range=%d:99" % (SPLIT + 1), "--out=" + PART2])
        sh(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps, "-InFile", PART1, "-OutFile", P1])
        sh(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps, "-InFile", PART2, "-OutFile", P2])
        parts = (P1, P2)
    else:
        sh([sys.executable, bh, "--out=" + PART1])
        sh(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps, "-InFile", PART1, "-OutFile", P1])
        parts = (P1,)
    out = pymupdf.open()
    for p in parts:
        src = pymupdf.open(p)
        out.insert_pdf(src)
        src.close()
    out.set_metadata({"title": nch.META_TITLE})
    if os.path.exists(nch.OUT_PDF):
        os.remove(nch.OUT_PDF)
    out.save(nch.OUT_PDF, garbage=3, deflate=True)
    print("合并完成: %s（%d 页）" % (nch.OUT_PDF, len(out)))
    out.close()

if __name__ == "__main__":
    main()
