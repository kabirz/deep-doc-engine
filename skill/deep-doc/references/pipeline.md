# 构建管线细节（pipeline）

主管线入口 `tools/build_all.py`，任一步非零退出即中止。参数：`--partial`（允许章不全）、`--min=N`（页数下限，默认 400）、`--skip-print`、`--skip-toc`。

## 十步顺序与各步职责

```
build_html.py [--partial]      1 全量 HTML（封面+目录+构建期高亮+侧边栏+wbr）
check_ids.py  [--partial]      2 结构总门禁
tag_check.py                  3 行内标签配平
svg_check.py                  4 SVG 禁令/画布/text-anchor
line_check.py                 5 SVG 线穿字/字重叠
cite_check.py                 6 源码引用文件+行号双核验（nch.KSRC=None 时自动跳过）
print_merged.py               7 分半打印合并 PDF
toc_pages.py → print_merged.py → toc_pages.py --verify
                              8 两遍法真实页码（提取→重印→零漂移断言）
sanitize_ghost.py             9 末页幽灵深色块白块覆盖
add_bookmarks.py [--partial] 10 PDF 书签（字号门控）
final_check.py --min=N       11 页数 + 打印缩放比 0.96~1.04
build_html.py [--partial]    12 再跑一次出交付版 HTML（目录已含真实页码）
```

## 关键实现要点

### nch.py（唯一事实源）
书名/副题/TOPBAR_TAGS/输出路径/NCH/NAPX/SPLIT（分半章号，默认 NCH//2）/MIN_LV2/PARTS 分篇/KSRC。`fragment_order()` 决定片段拼接顺序：`ch(\d+)_` 数字排序 + `apx_[a-d]`。

### build_html.py
- 片段按 h2 正则解析章号，断言连续无缺无重（partial/range 放宽）。
- Pygments Dracula 构建期高亮：`HtmlFormatter(nowrap=True, noclasses=True, style="dracula")`；sh 提示符 `$` 染 `#50fa7b`；注入 `.lang-tag` 语言角标。
- `--range=a:b --out=` 分段构建：仅起点=1 的段带封面/目录/侧边栏；附录归末段（range 终点 > NCH 时）。
- `wbr_code()` 先 stash 全部 `<pre>` 防误伤，再对行内 code 与 td/th 裸文本在 `_ / .` 与驼峰边界插 `<wbr>`。
- 输出 `utf-8-sig`（带 BOM）。

### 打印（print_pdf.ps1 + print_merged.py）
- Edge 探测两个固定路径（ProgramFiles 与 ProgramFiles(x86)），不查注册表。
- `--headless --disable-gpu --no-pdf-header-footer --disable-extensions --print-to-pdf=<file URI>`；PowerShell `Start-Process` 拉起 + 轮询输出文件（700ms×300s）+ `WaitForExit(180s)`。**必须经 PowerShell**：直接 subprocess 会挂到运行中的 Edge 实例静默失败。ps1 保持纯 ASCII。
- 分半：`--range=1:SPLIT` 与 `--range=SPLIT+1:99` 各打一份，PyMuPDF `insert_pdf` 合并、写元数据、`save(garbage=3, deflate=True)`。后半段为空（迷你书）时自动退化单次打印。

### 两遍法页码（toc_pages.py）
- 字号门控 17.0~20.0pt 抓「第 N 章/附录 A-D/目录」行；长标题折行按「行文本是标题前缀」匹配。
- `_toc_pages.json` → 下一轮 build_html 目录显示真实页码 → 重打印 → `--verify` 比对新旧 JSON，任何漂移 exit 1。

### 书签（add_bookmarks.py）
- 双字号门控：h2 18.75±1.0pt 一级、h3 14.25±0.85pt 二级（`N.M` 或「本章要点」）。
- 断言：章书签严格递增、无重复、NCH 章全、NAPX 附录全（partial 豁免）；`set_toc + saveIncr`，重开 `get_toc` 验证，二级 < MIN_LV2 视为失败。

## 故障排查表

| 症状 | 原因 | 修法 |
|---|---|---|
| final_check 缩放比 <0.96 | 存在超宽元素，Chromium 整本缩小 | 跑 `tools\_overflow_probe.py`（print 改 all + 680px 视口 dump scrollWidth）定位；宽表加 `table.wide`；pre 已有 pre-wrap+clip |
| 缩放比 >1.04 | 少见；字体栈回退异常 | 检查 CJK 字体是否在栈首 |
| 后半本整页宋体/衬线回退 | Chromium 长任务字体缓存耗尽 | 确认 CSS 字体栈 CJK 打头；确认走了分半打印（SPLIT 合理居中） |
| 末页深色残影块 | 分片打印残影 | sanitize_ghost 自动修；若未修到，检查其判定阈值（深色 RGB<0.22 且面积>30%宽/25%高、文字<200 字符） |
| toc_pages --verify 漂移 | 页码未收敛 | 再跑一轮 build_all；连续两轮漂移→查是否新增了改变分页的内容（大图/大表） |
| 书签缺章 | h2 折行/字号漂移出 18.75±1.0 门 | 检查该章 h2 是否过长折行、被缩小 |
| Edge 打印 0 字节 | 挂到运行中实例 | 确认走 print_pdf.ps1（Start-Process）；关掉正在运行的 Edge 进程组 |
| build_html 报双重编码乱码 | 片段被按错误编码读入重写 | check_ids 的特征串检测（Ã©/锟/\ufffd）；用 utf-8 重存；`strip_bom.py` 清 BOM |

## 维护工具（不在主管线内）

- `strip_bom.py`：剥片段 UTF-8 BOM（build_html 以 utf-8 读，BOM 会污染正文）。
- `fig_loc.py`：定位某章所有「图 N-K」行号（修图号错乱）。
- `render_samples.py`：抽页渲染 PNG 到 `_shots/`（视觉验收）。
- `final_verify.py`：封面/页数/书签抽查 + 封面 PNG。
