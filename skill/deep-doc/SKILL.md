---
name: deep-doc
description: 用 deep-doc-engine 生产线撰写深度技术书籍/长篇技术文档（分章 HTML 片段 → 单页 HTML 侧边栏导航 + Dracula 高亮 → A4 PDF 真实页码目录 + 书签 + 机器质量门禁）。当用户要写书、写系统性的深度技术文档、要 HTML+PDF 双格式交付、提到"像之前那些 linux_xx_doc 一样的文档工程"或要为某源码库/某技术主题写"N 章+附录"的详解时使用本技能——即使只说"帮我写个 XX 深度详解"也要触发。
---

# deep-doc — 深度技术书籍生产线

本技能驱动一条已在 20+ 本已交付书籍（合计 13000+ 页）上验证的文档生产线。
**先读完本文件再动手**；细节按需读 `references/`（相对本 SKILL.md 所在目录）。

## 引擎获取

引擎模板位于（按序探测，取第一个存在的）：

1. `C:\Users\jxwaz\Documents\code\deep-doc-engine\template`
2. `git clone https://github.com/kabirz/deep-doc-engine` 后取其 `template/`

Python 用 `C:\Users\jxwaz\venv\base\Scripts\python.exe`（需 pygments、pymupdf；PDF 需 Microsoft Edge）。

## 工作流总览

```
1 初始化工程 → 2 规划 PLAN/FACTS → 3 逐章写作+自检 → 4 全书构建 → 5 交付验收
```

### 第 1 步：初始化工程

```bat
cd <引擎>\template
python init_project.py --dir <新工程目录> --title "书名深度详解" --subtitle "副题 · 基线 vX.Y" ^
     --nch <章数> --napx 4 [--ksrc "C:\path\to\源码树"]
```

- `--ksrc` 指向引用源码树（cite_check 会核验正文每个 `文件 @ L行号`）；非源码书省略。
- 初始化后必改两处：`src/00_head.html` 封面（glyph/简介/chips）、`tools/nch.py` 的 `PARTS` 分篇。
- 立刻跑 `python tools\build_all.py --partial --skip-print` 确认示例章全绿，再删示例章开写。

### 第 2 步：规划

- `PLAN.md`：分篇分章，每章列覆盖点与配图；章数写入 `tools/nch.py`（唯一事实源）。
- `FACTS.md`：基线声明 + **版本铁律**（只写基线现状，禁臆测"新增于某版本"；版本归属只允许引用文内"已知引入版本"白名单）+ 共享实测事实。
- 需要深度引用源码的书：先通读关键路径，把行号级事实写进 FACTS，标注【待核实】条目分给各章。

### 第 3 步：逐章写作

- 每章一个 `src/chNN_短名.html` 片段 + `src/facts/chNN.md` 实测事实。
- **写作前读 `references/html-theme.md`（片段骨架与格式约定）与 `references/svg-guide.md`（手绘 SVG 八禁令）**——检查器会逐条机器断言，违者构建失败。
- 引用源码行号必须亲自 Read/Grep 核实，禁止抄第二手资料；实测与教材不符的写进 facts。
- 并行多代理写章时：按章文件分组互斥，每章作者只修自己章的报错。
- 每章写完自检四件套（工程目录下）：

```bat
python tools\check_ids.py --partial
python tools\svg_check.py
python tools\line_check.py
python tools\cite_check.py
```

### 第 4 步：全书构建

```bat
python tools\build_all.py            :: 一键：HTML → 六检查 → PDF → 两遍法页码 → 书签 → 终检
python tools\build_all.py --partial --min=2    :: 未写全时增量验证
```

管线细节与故障排查读 `references/pipeline.md`。常见失败：
- 缩放比 <0.96（整本被超宽元素缩小）→ 跑 `tools\_overflow_probe.py` 定位，宽表加 `class="wide"`；
- 页码校验漂移 → 再跑一遍 build_all（两遍法偶需三轮收敛，连续两轮漂移才是真问题）。

### 第 5 步：交付验收

- `final_check`（页数 + 缩放比）与 `add_bookmarks`（书签数）必须 PASS；
- 渲染样张抽查（`render_samples.py` 抽页存 `_shots/`）——封面、任一 SVG 章、宽表页、末页（查幽灵背景）；
- 交付物 = `<书名>.html` + `<书名>.pdf`（工程根目录），附页数/图数/书签数统计。

## 何时读哪份参考

| 文件 | 何时读 |
|---|---|
| `references/html-theme.md` | 写片段前；调样式/排版问题 |
| `references/svg-guide.md` | 画每张 SVG 前后（含自查清单） |
| `references/pipeline.md` | 构建失败、打印异常、页码/书签问题 |
| `references/quality.md` | 检查器报错含义；多代理分派；扩展检查器选配 |

## 红线（历史事故换来的，违反必返工）

1. 片段内禁止 HTML 注释（构建器剥离，曾吞章）。
2. 版本归属必须有据（FACTS 白名单），否则只写现状。
3. SVG 逐条过八禁令（`references/svg-guide.md`），尤其 text-anchor 必须显式、marker id 带章前缀。
4. 行内标签必须配平（未闭合 `<code>` 曾污染后续数章样式）。
5. 正文引用行号必须实测（cite_check 对着真实源码树核验，编造必被抓）。
