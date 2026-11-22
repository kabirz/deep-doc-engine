"""cite_check.py — 校验片段里引用的源码文件与行号：文件在 nch.KSRC 树中存在、行号不越界"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch

CITE = re.compile(r"([\w\-./\\]+\.(?:cmake|md|py|sh|txt|json|yml|yaml|glsl|c|h|m|rst))(?:\s*@\s*L?(\d+))?(?![a-zA-Z])")
# libc 头文件路径前缀：属于 glibc/musl，不在内核树中，不校验
LIBC_PREFIX = ("sys/", "bits/", "arpa/", "net/", "netinet/", "gnu/")
VIRTUAL = {
    "main.c": "泛指用户自己的程序文件",
    "producer.c": "示例程序文件", "consumer.c": "示例程序文件",
    "server.c": "示例程序文件", "client.c": "示例程序文件",
    "worker.c": "示例程序文件", "demo.c": "示例程序文件",
    "stdio.h": "libc 头文件", "stdlib.h": "libc 头文件",
    "string.h": "libc 头文件", "stdint.h": "libc 头文件", "stdbool.h": "libc 头文件",
    "unistd.h": "libc 头文件", "fcntl.h": "libc 头文件", "errno.h": "libc 头文件",
    "limits.h": "libc 头文件", "signal.h": "libc 头文件", "pthread.h": "libc 头文件",
    "semaphore.h": "libc 头文件", "mqueue.h": "libc 头文件", "time.h": "libc 头文件",
    "poll.h": "libc 头文件", "dirent.h": "libc 头文件", "ctype.h": "libc 头文件",
    "stdlib.h": "libc 头文件", "inttypes.h": "libc 头文件", "locale.h": "libc 头文件",
    "Makefile": "内核构建文件（同名文件太多，不校验）",
    "Kconfig": "内核配置文件（同名文件太多，不校验）",
    "Kbuild": "内核构建文件（同名文件太多，不校验）",
    "defconfig": "架构默认配置（同名文件太多，不校验）",
    "log.h": "示例程序文件",
}
PRE_SPLIT = re.compile(r"<pre\b.*?</pre>", re.S)
LINECNT = {}

# 只遍历与本书相关的子树，加速索引构建（在 nch.py 里配 INDEX_SUBS；不配则走全树）
INDEX_SUBS = getattr(nch, "INDEX_SUBS", None)

def build_index():
    idx = {}
    roots = [os.path.join(nch.KSRC, sub) for sub in INDEX_SUBS] if INDEX_SUBS else [nch.KSRC]
    for d in roots:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for f in files:
                idx.setdefault(f, []).append(os.path.join(root, f))
    for f in os.listdir(nch.KSRC):
        if os.path.isfile(os.path.join(nch.KSRC, f)):
            idx.setdefault(f, []).append(os.path.join(nch.KSRC, f))
    return idx

def nlines(path):
    if path not in LINECNT:
        try:
            with open(path, "rb") as fh:
                LINECNT[path] = fh.read().count(b"\n") + 1
        except OSError:
            LINECNT[path] = -1
    return LINECNT[path]

def run():
    if not nch.KSRC:
        print("cite_check: nch.KSRC 未配置（非源码类书籍），跳过引用校验")
        return [], []
    idx = build_index()
    errs, warns = [], []
    frags = sorted(glob.glob(os.path.join(nch.SRC, "ch*.html"))) + \
            sorted(glob.glob(os.path.join(nch.SRC, "apx_*.html")))
    for fp in frags:
        doc = open(fp, encoding="utf-8-sig").read()
        fname = os.path.basename(fp)
        # 代码块外的正文才检查引用
        parts = PRE_SPLIT.split(doc)
        for pi, seg in enumerate(parts):
            if pi % 2 == 1:
                continue
            for m in CITE.finditer(seg):
                name, ln = m.group(1), m.group(2)
                if name.startswith(("http", "www.")):
                    continue
                norm = name.replace("\\", "/")
                if norm.startswith(LIBC_PREFIX):
                    continue    # libc 头文件，不在内核树
                base = os.path.basename(name)
                if base in VIRTUAL:
                    continue
                hits = idx.get(base)
                if not hits:
                    errs.append("%s: 引用文件不存在 %s" % (fname, name))
                    continue
                if len(hits) > 1:
                    norm = name.replace("\\", "/")
                    parts = [p for p in norm.split("/") if p]
                    # 按引用路径的后缀深度择优：与引用路径尾部匹配分量最多者胜。
                    # 解决 include/linux/X.h 与 include/uapi/linux/X.h 同名误配
                    def depth(h):
                        hp = os.path.normpath(h).replace("\\", "/").split("/")
                        n = 0
                        while n < len(parts) and n < len(hp) and hp[-1 - n] == parts[-1 - n]:
                            n += 1
                        return n
                    best = max(depth(h) for h in hits)
                    cand = [h for h in hits if depth(h) == best]
                    hits = cand
                    hits.sort(key=len)  # 仍多个：取离根最近的
                path = hits[0]
                if ln:
                    n = nlines(path)
                    if n < 0:
                        warns.append("%s: 无法读行数 %s" % (fname, path))
                    elif int(ln) > n:
                        errs.append("%s: 行号越界 %s @ L%s（文件仅 %d 行）" % (fname, name, ln, n))
    return errs, warns

if __name__ == "__main__":
    errs, warns = run()
    for e in errs[:100]: print("ERR", e)
    for w in warns[:40]: print("WARN", w)
    print("cite_check: %d err, %d warn" % (len(errs), len(warns)))
    sys.exit(1 if errs else 0)
