"""fig_seq_check.py — 校验每章 figcaption 图号章内连续（图 N-K，K 从 1 递增）"""
import re, os, sys, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
bad = 0
for fp in sorted(glob.glob(os.path.join(SRC, "ch*.html"))):
    doc = open(fp, encoding="utf-8-sig").read()
    ch = int(re.match(r"ch(\d+)_", os.path.basename(fp)).group(1))
    nums = [int(k) for k in re.findall(r"<figcaption>[^<]*图\s*%d-(\d+)" % ch, doc)]
    ok = nums == list(range(1, len(nums) + 1))
    print(os.path.basename(fp), nums, "OK" if ok else "BAD")
    bad += 0 if ok else 1
print("fig_seq_check: %d bad" % bad)
sys.exit(1 if bad else 0)
