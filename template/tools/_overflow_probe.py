"""_overflow_probe.py — 找出在打印版式下超宽的元素（把 @media print 换成 all，680px 视口量宽）
用法：python _overflow_probe.py  ->  生成 _probe.html，再用 Edge --dump-dom 读取结果
"""
import os, re, sys, subprocess, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nch

PROBE = os.path.join(nch.ROOT, "_probe.html")
VIEW_W = 680  # A4 内容宽 ≈ 680px

def make_probe():
    doc = open(nch.OUT_HTML, encoding="utf-8-sig").read()
    doc = doc.replace("@media print", "@media all")
    script = """
<script>
(function(){
  function report(){
    var bad = [];
    var all = document.querySelectorAll('main *');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.closest('.topbar') || el.closest('.sidebar')) continue;
      if (el.closest('svg') || el.namespaceURI && el.namespaceURI.indexOf('svg') >= 0) continue;
      var r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      var over = Math.max(r.right - %d, el.scrollWidth - %d);
      if (over > 2) {
        var h = el.outerHTML || '';
        bad.push({t: el.tagName + '.' + (el.className || ''), w: Math.round(Math.max(r.width, el.scrollWidth)), s: h.replace(/\\s+/g, ' ').slice(0, 140)});
        if (bad.length >= 40) break;
      }
    }
    var out = document.createElement('pre');
    out.id = 'PROBE-RESULT';
    out.textContent = 'PROBE-BEGIN\\n' + (bad.length ? bad.map(function(b){return b.w + 'px  ' + b.t + '  ' + b.s;}).join('\\n') : 'NONE') + '\\nPROBE-END';
    document.body.appendChild(out);
  }
  if (document.readyState === 'complete') setTimeout(report, 400);
  else addEventListener('load', function(){ setTimeout(report, 400); });
})();
</script>
""" % (VIEW_W, VIEW_W)
    doc = doc.replace("</body>", script + "</body>")
    open(PROBE, "w", encoding="utf-8-sig").write(doc)

def main():
    make_probe()
    edge = None
    for c in [r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]:
        if os.path.exists(c):
            edge = c; break
    if not edge:
        print("未找到 Edge"); sys.exit(2)
    uri = "file:///" + PROBE.replace("\\", "/")
    r = subprocess.run([edge, "--headless", "--disable-gpu", "--dump-dom",
                        "--window-size=%d,900" % VIEW_W, "--virtual-time-budget=8000", uri],
                       capture_output=True, text=True, timeout=180)
    m = re.search(r"PROBE-BEGIN\n(.*?)\nPROBE-END", r.stdout, re.S)
    if not m:
        print("探针未输出（页面加载失败?）"); print(r.stdout[-500:]); sys.exit(2)
    body = m.group(1)
    if body.strip() == "NONE":
        print("overflow_probe: 无超宽元素，缩放应为 1.0")
        return
    print("发现超宽元素:")
    for line in body.splitlines()[:40]:
        print("  ", line)

if __name__ == "__main__":
    main()
