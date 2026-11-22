"""build_all.py — 一键重建：HTML -> 五项检查 -> PDF -> 幽灵修复 -> 书签 -> 终检
用法：C:\\Users\\jxwaz\\venv\\base\\Scripts\\python.exe build_all.py [--partial] [--skip-print]
"""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

def run(args, check=True):
    print("\n=== %s ===" % " ".join(os.path.basename(a) for a in args[1:]))
    t0 = time.time()
    r = subprocess.run([PY] + args, cwd=ROOT)
    dt = time.time() - t0
    print("--- %.1fs exit=%d" % (dt, r.returncode))
    if check and r.returncode != 0:
        print("!! 步骤失败，中止（修复后重跑）")
        sys.exit(r.returncode)
    return r

def main():
    partial = "--partial" in sys.argv
    min_pages = 400
    for a in sys.argv:
        if a.startswith("--min="):
            min_pages = int(a.split("=")[1])
    run([os.path.join(HERE, "build_html.py")] + (["--partial"] if partial else []))
    run([os.path.join(HERE, "check_ids.py")] + (["--partial"] if partial else []))
    run([os.path.join(HERE, "tag_check.py")])
    run([os.path.join(HERE, "svg_check.py")])
    run([os.path.join(HERE, "line_check.py")])
    run([os.path.join(HERE, "cite_check.py")])
    run([os.path.join(HERE, "xref_check.py")] + (["--partial"] if partial else []))
    if "--skip-print" not in sys.argv:
        # 分半打印 + 合并（规避 Chromium 长任务字体缓存退化/分片残影）
        run([os.path.join(HERE, "print_merged.py")])
        if "--skip-toc" not in sys.argv:
            # 页码两遍法：提取真实页码 -> 重建 -> 重打印 -> 校验稳定
            run([os.path.join(HERE, "toc_pages.py"), nch_path_out_pdf()])
            run([os.path.join(HERE, "print_merged.py")])
            run([os.path.join(HERE, "toc_pages.py"), nch_path_out_pdf(), "--verify"])
        run([os.path.join(HERE, "sanitize_ghost.py")])
        run([os.path.join(HERE, "add_bookmarks.py")] + (["--partial"] if partial else []))
        run([os.path.join(HERE, "final_check.py"), "--min=%d" % min_pages])
    run([os.path.join(HERE, "build_html.py")] + (["--partial"] if partial else []))  # 交付版完整 HTML
    print("\n全部完成 ✓")

def nch_path_out_html():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nch", os.path.join(HERE, "nch.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.OUT_HTML

def nch_path_out_pdf():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nch", os.path.join(HERE, "nch.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.OUT_PDF

if __name__ == "__main__":
    main()
