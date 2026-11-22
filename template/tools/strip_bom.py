"""strip_bom.py — 剥除 src/*.html 的 UTF-8 BOM"""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
n = 0
for f in glob.glob("*.html"):
    raw = open(f, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        open(f, "wb").write(raw[3:])
        n += 1
        print("stripped", f)
print("done", n)
