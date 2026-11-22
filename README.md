# deep-doc-engine — 深度技术书籍文档引擎

一套从 20+ 本已交付技术书籍（合计 13000+ 页）中沉淀出来的**通用技术书籍生产线**：
分章 HTML 片段 → 单页 HTML（侧边栏导航 + Dracula 高亮）→ A4 PDF（真实页码目录 + 书签），
配十步构建管线与机器质量门禁。已在下列书籍工程中实战验证：

| 书 | 页数 | 章 | SVG 图 | 基线源码 |
|---|---|---|---|---|
| Linux 进程间通信深度详解 | 775 | 46+4 | 199 | Linux 7.1.1 |
| 外设总线通信协议深度详解（I2C/SPI/UART/CAN/USB/LIN） | 788 | 50+4 | 225 | Linux 7.1.1 |
| 伪文件系统深度详解 | 895 | 44+4 | 186 | Linux 7.1.1 |
| 线程深度详解 | 822 | 45+4 | — | Linux 7.1.1 + glibc/musl |
| 内核驱动工程师面试题集 | 507 | 50+4 | — | Linux 7.1.1 |
| 追踪/eBPF、同步机制、系统调用/模块、时钟、电源域、Regulator、pinctrl/GPIO、USB、PCI、ALSA、设备树、文件系统、中断、网络协议栈、V4L2… | 439~795 | 40~51+4 | 168~366 | Linux 7.1.1 |
| systemd 深度详解 | ~630 | 40+4 | 195 | systemd v261.4 |
| vLLM 深度详解 | 621 | 50+4 | 219 | vLLM v0.32.0 |
| Yocto 学习与开发深度详解 | 688 | 40+4 | 174 | Yocto 6.0 |
| AI Agent 面试题集 / 嵌入式面试题集 | — | 50+4 | — | LangChain/vLLM/STM32/FreeRTOS/Zephyr/Embassy |

## 一、总体方法论

```
PLAN.md（章节规划）
   │
   ├─ FACTS.md（全书共享事实基线：实测事实 + 版本铁律 + 待核实清单）
   │      └─ src/facts/chNN.md（每章实测事实，带源码行号证据）
   │
   ├─ AGENTS_STYLE.md（写作规范）  SVG_GUIDE.md（手绘图规范）
   │
   └─ src/chNN_短名.html（每章一个独立片段，不含 html/head/body）
          │
          ▼
   tools/build_all.py（十步管线，一键重建 HTML + PDF）
```

四条核心原则：

1. **单一事实源**：全书书名/章数/分篇/路径全部集中在 `tools/nch.py`，其余工具零定制。
2. **片段直写、构建期加工**：作者只写纯转义片段；高亮、目录、侧边栏、页码、书签全部构建期生成，HTML/PDF 视觉一致、无运行时 JS 依赖（侧边栏高亮除外，10 行 scrollspy）。
3. **机器门禁**：每章的结构、SVG 几何、源码引用、交叉引用全部由检查器断言，人只修检查器报出的问题。
4. **事实闭环**：正文引用的每个行号都会对着真实源码树核验；实测与教材不符的事实沉淀进 facts 文件，供后续章节复用。

## 二、HTML 生成方法

- **输入**：`src/00_head.html`（整册 `<style>` + 封面 div）+ `src/chNN_*.html` 章片段 + `src/apx_[a-d]_*.html` 附录。
- **组装**（`tools/build_html.py`）：
  - 按 `nch.fragment_order()` 拼接；断言章号连续无缺无重（`--partial` 增量放宽）；
  - **构建期 Pygments Dracula 高亮**：匹配 `<pre class="code" data-lang="c">…</pre>`，unescape → highlight(`nowrap=True, noclasses=True`) → re-escape；sh 块 `$` 提示符染绿；右上角注入 `.lang-tag` 语言角标；
  - 生成**左侧固定侧边栏**（296px，按篇分组、锚点跳转、scrollspy 高亮当前章）与**带页码目录**（页码优先取 `_toc_pages.json` 的真实 PDF 页码，无则回退章号占位）；
  - `wbr_code()`：行内 `<code>` 与单元格裸文本在 `_ / .` 边界和驼峰边界注入 `<wbr>`，使表格在 `word-break:normal` 下按语义折行；
  - 章标题 h2 自动补 `class="ch"`（附录 `ch apx`），打印分页依赖它；输出 `utf-8-sig` 带 BOM 保证浏览器编码探测。

### 主题（浅灰底 + 白卡片 + Dracula）

- 屏幕：`body { background:#eef0f4 }`，正文白色圆角卡片（max-width 960px、双层阴影），sticky 毛玻璃 topbar；章题 h2 渐变底 + 左侧色条（正章蓝 `#4f6af0`、附录紫 `#8b5cf6`）。
- 代码块：Dracula 深底 `#282a36`、前景 `#f8f8f2`、圆角 10px；token 配色：注释 `#6272A4`、关键字/预处理 `#FF79C6`、类型 `#8BE9FD`、数字 `#FFB86C`、字符串 `#BD93F9`、函数/属性 `#50FA7B`。
- 表格：深蓝表头 `#1e3a8a` 白字、斑马纹、无 class（构建器统一样式）；超宽表加 `class="wide"`（fixed 布局 + 打印 7.5pt）。
- 提示框三件套 `.tip/.warn/.note`（绿/红/蓝左边条）。

## 三、PDF 生成方法（Edge headless + PyMuPDF）

打印链专门对付 **Chromium 打印引擎的四个坑**：

1. **整本等比缩小**：任一元素超出版心宽，整本被缩小（实测曾到 0.59~0.765）。修法：全局 `overflow-wrap:anywhere`、`pre` 用 `pre-wrap + overflow:clip` 禁横向滚动、宽表 `table.wide`；终检用 **h2 实测字号 / 18.75pt 设计值 ∈ [0.96, 1.04]** 间接测出缩放比，超标跑 `_overflow_probe.py`（`@media print` 换 `all` + 680px 视口 dump 每个元素的 `scrollWidth`）定位元凶。
2. **长任务字体缓存退化**：数百页后半本整页宋体回退。修法：CSS 字体栈 **CJK 字体打头**（`"Microsoft YaHei"`）+ **分半打印合并**（`--range` 分两段各打一份 PDF，PyMuPDF `insert_pdf` 合并）。
3. **分片残影**：末页遗留幽灵深色代码背景块。修法：`sanitize_ghost.py` 扫末 3 页深色大矩形，白块覆盖 `saveIncr()`。
4. **拉起方式**：Edge 直接 subprocess 会挂到运行中实例静默失败；必须 PowerShell `Start-Process -Wait` 拉起（`print_pdf.ps1`，纯 ASCII，`--headless --no-pdf-header-footer --print-to-pdf=`）。

**目录真实页码·两遍法**：首遍打印 → `toc_pages.py` 按字号门控（17.0~20.0pt）提取各章起始页写 `_toc_pages.json` → 重建 HTML（目录用真实页码）重打印 → `--verify` 断言两遍页码零漂移。

**PDF 书签**：`add_bookmarks.py` 双字号门控（h2 18.75±1.0pt 一级、h3 14.25±0.85pt 二级），章号严格递增断言，`set_toc + saveIncr`，重开验证。

**打印 CSS 要点**：`@page A4 13/14/16/14mm`；隐藏侧边栏/topbar；`h2.ch { break-before:page }` 每章新起页；`figure.fig/tr/td/.tip/.warn/.note { break-inside:avoid }` 但 `table { break-inside:auto }`（长表按行切）；`thead { break-after:avoid }`；`orphans/widows: 2`；`a { color:inherit }`。

## 四、图解：手绘 SVG 规范

统一画布 `viewBox="0 0 760 H"`（H=240~560，不写 width），`<figure class="fig">` + `<figcaption>图 N-K · 说明</figcaption>`（章内图号连续，`fig_seq_check` 断言）。浅色纸面配色（打印友好）：箱体白底/淡彩填充（蓝 `#eef2ff` 绿 `#f0fdf4` 黄 `#fef3c7` 红 `#fee2e2` 紫 `#f3e8ff`）+ 描边 `#8a93a5`，标题带 `#4f6af0`，强调 `#e4572e`，箭头统一 marker（id 全书唯一 `arrow-chNN-M`），代码示意块用 Dracula 底。

八条硬禁令（`svg_check`/`line_check` 机器检查，全部来自历史事故）：

1. 禁裸 `&nbsp;`（XML 解析硬错误）；2. 禁 `transform="rotate"` 文字（打印截断 + 检查器误报）；3. SVG 内禁 HTML 注释；4. marker/渐变 id 全书唯一（`arrow-章号-序号`）；5. 图内文字禁「第 N 章/附录 X」（书签扫描器误判）；6. 每个 text 必须显式 `text-anchor`（缺省值陷阱：估宽方向全错）；7. 全部元素 + 文字包围盒在画布内留 ≥8px（文字宽按 CJK `fs×1.0`/西文 `fs×0.55` 估算）；8. 字号标题 15~16/正文 12~13/注 11，中文标签 ≤14 字。

几何规则（`line_check`）：文字与线/箭头不相交、错开 ≥12px；两行文字间距 ≥ fs+6；时序图生命线在文字框区断开成短段。常用模板：流程图、结构图（外壳+标题栏+字段行，结构体名 Consolas）、时序图、状态机、对比图、内核数据结构图（指针字段带箭头连线）、深底代码示意。

## 五、质量门禁链

```
build_html → check_ids → tag_check → svg_check → line_check → cite_check → xref_check
    → print_merged → toc_pages 两遍法 → sanitize_ghost → add_bookmarks → final_check
    → build_html（交付版 HTML）
```

| 检查器 | 断言内容 |
|---|---|
| `check_ids` | id 唯一、片段以 h2 开头、无 HTML 注释、无双重编码乱码、章号配额、每章要素底线（h3≥6 图≥3 代码块≥5 表≥1 lead）、pre 内无块级标签（转义遗漏） |
| `tag_check` | 行内标签（strong/em/code…）开闭配平——历史事故：未闭合 `<code>` 把玫红等宽样式污染后续数章 |
| `svg_check` | 上述八禁令 + 出画布 + text-anchor 显式 |
| `line_check` | 线穿字/字贴线/字重叠（把 line/polyline/path 全折算线段，含贝塞尔采样） |
| `cite_check` | 正文源码引用「文件存在 + 行号不越界」双核验（对照 `nch.KSRC` 源码树；同名文件按路径尾部分量深度择优） |
| `xref_check` | 「第 N 章 / N.M 节」交叉引用目标存在 |
| `fig_seq_check` | 图号章内从 1 严格递增 |
| `final_check` | 页数下限 + 打印缩放比 0.96~1.04 |

扩展检查器（按书选配，见 `skill/deep-doc/references/quality.md`）：`hist_check`（无依据版本说法）、`demo_check`（示例代码真实 WSL gcc 编译）、`blank_scan`（半空页）、`colon_check`（页尾悬空冒号）、`box_check`（SVG 绘制顺序遮挡关系）等。

## 六、多代理写作协作（FACTS 闭环）

- `FACTS.md`（主对话维护）：基线声明 + 版本铁律（**只写基线现状，禁臆测"新增于某版本"**——非 git 树无法证明版本归属，历史工程曾批量翻车）+ 已知引入版本白名单。
- `src/facts/chNN.md`（每章作者维护）：实测事实 + 证据行号；与教材不符的必须记录。
- 每章作者写完片段必须跑四项自检（check_ids/svg_check/line_check/cite_check 的 `--partial`），只修自己章的报错。
- 并行写作时按章文件分组互斥；凭证错误波次先查落盘再重派。

## 七、快速开始

```bat
:: 初始化新工程（工具链零改动，只生成定制 nch.py + 替换封面占位符 + 示例章）
python template\init_project.py --dir ..\my_doc --title "书名深度详解" --subtitle "副题" --nch 12

:: 写章节（src/chNN_*.html，见 template\AGENTS_STYLE.md 与 SVG_GUIDE.md）

:: 增量自检（章未写全）
python tools\build_all.py --partial --skip-print

:: 一键重建全书（HTML + 六项检查 + PDF + 两遍法页码 + 书签 + 终检）
python tools\build_all.py
```

依赖：Python（pygments、pymupdf）+ Microsoft Edge（PDF 打印）。Windows 优先（Edge 探测、PowerShell 拉起），其余平台需替换打印环节。

## 仓库结构

```
├── README.md                  # 本文档（方法论总结）
├── template/                  # 通用工程脚手架（init_project.py + tools/ + 规范模板）
│   ├── init_project.py        # 一键初始化新工程
│   ├── tools/                 # 21 个构建与检查脚本（nch.py 单点定制）
│   ├── src/00_head.html       # 主题模板（CSS + 封面占位符）
│   └── PLAN.md / AGENTS_STYLE.md / SVG_GUIDE.md / FACTS.md
├── skill/deep-doc/            # ZCode/Claude skill（AI 写书工作流）
│   ├── SKILL.md
│   └── references/            # pipeline / html-theme / svg / quality 细节
└── docs/                      # 方法论专题文章
```

## License

MIT
