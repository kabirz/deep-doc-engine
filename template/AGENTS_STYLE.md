# 章节片段写作规范（每章作者必读）

每章产出**一个独立 HTML 片段**，写入 `src/chNN_短名.html`（如 `ch06_pipe.html`）。附录写 `apx_a_api.html` 等。片段不含 `<html>/<head>/<body>`，直接从 `<h2>` 开始。

## 结构

```html
<h2 id="ch06">第 6 章 · 章标题（副题）</h2>
<p class="lead">本章导读段落……（2~4 句）</p>
<h3 id="ch06-01">6.1 节标题</h3>
<p>……</p>
<h4>更深的小标题（无 id 要求）</h4>
…
<h3 id="ch06-99">本章要点</h3>
<ul><li>……</li></ul>
```

- 章号一律两位数字：`ch01`…`chNN`；h3 的 id 形如 `chNN-KK`（KK 两位顺序号，要点节用 `chNN-99`）。
- h3 编号写成「N.1 标题」格式（含章号前缀），h4 不编号。「本章要点」h3 的 id 用 `chNN-99`，标题不带编号。
- **禁止 HTML 注释 `<!-- -->`**（构建器会剥离，且历史工程出现过注释吞章事故）。

## 代码块

```html
<pre class="code" data-lang="c">int main(void) {
    return 0;   /* &lt; &gt; &amp; 必须转义 */
}</pre>
```

- `data-lang` 取值：`c`、`sh`、`text`（偶尔 `cpp`/`json`）。
- 内容必须 HTML 转义 `&` → `&amp;`、`<` → `&lt;`、`>` → `&gt;`。构建器会用 Pygments（Dracula 配色）在构建期重新高亮。
- shell 块的提示符写 `$ `（构建器会给提示符着色）。代码块内不要出现中文标点；注释可用中文但保持简短。
- 代码块不要超长：单块 ≤ 55 行；更长的代码拆成多块配讲解。
- 用户态示例必须完整可编译（含 #include、错误检查）。
- 引用真实源码时，在块后用 `<p class="src-ref">源码：path/to/file.c @ L84</p>` 标注出处（**行号必须亲自 Read/Grep 核实**，禁止抄规划文件里的行号）。

## 图（SVG）

- 每张图包在 `<figure class="fig">` 里，图必须有 `<figcaption>`（`图 6-3 · 说明文字`，编号=章-序号，**章内连续**）。
- 手绘 SVG 规范见 `SVG_GUIDE.md`（必须逐条遵守，构建器会机器检查）。

## 表格

```html
<table>
<thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead>
<tbody><tr><td><code>ring_size</code></td><td><code>unsigned int</code></td><td>说明文字</td></tr></tbody>
</table>
```

- 字段/函数名一律 `<code>` 包裹。表格不加 class，构建器统一样式（超宽表加 `class="wide"`）。
- 长标识符构建器会自动插断行点；不要在 `<code>` 里手写空格伪装。

## 提示框

```html
<div class="tip">💡 <strong>提示：</strong>……</div>
<div class="warn">⚠️ <strong>注意：</strong>……</div>
<div class="note">📌 <strong>说明：</strong>……</div>
```

## 行内约定

- 强调用 `<strong>`；新术语首次出现用 `<em>`；API/文件/类型用 `<code>`。
- 引用源码行内格式：`fs/pipe.c @ L730`（cite_check 校验文件存在且行号不越界；`@ L` 中间不能有空格变体）。
- **不属于引用源码树的头文件/示例文件**（libc 头、自己写的示例）**不写 `@ L行号`**，只写名字。
- 章节交叉引用：`第 9 章`、`见 9.2 节`。**不要**写"上一章/下一章"。
- 不确定的内容**必须读源码/原始资料核实**，禁止编造；尤其禁止编造：行号、默认数值、函数签名、tracepoint 名称、命令输出。实测到与常识/教材不符的事实写入 `src/facts/chNN.md`（标题：`# 第 N 章实测事实`，条目列表，每条含证据行号）。
- **FACTS.md 里标注「待核实」的条目由对应章作者核实后写进自己的 facts 文件**。

## 版本与历史表述

- 描述行为时以选定基线现状为准；历史演进（"从 X 版本开始…"）只允许引用 FACTS.md「已知引入版本」段中的条目。**其余一律不写版本归属**（历史工程曾因臆测引入版本被批量判错）。

## 篇幅

目标每章 PDF 10~14 页。经验值：片段 450~680 行 HTML（含 3~5 张 SVG、6~10 个代码块、2~4 张表）。写完自查：节数 ≥6、图 ≥3、代码块 ≥5、表 ≥1、最后 h3 是「本章要点」。

## 术语与文风

- 中文技术文档语气，专业但不生硬；英文术语首次出现给中文译名。
- 示例代码注释可中文；示例完整可编译。
- 与官方文档/教材冲突时以实测为准，并在 facts 里记录。

## 自检与交付清单（每章作者必须执行）

1. 写完 `src/chNN_*.html` 与 `src/facts/chNN.md`。
2. 在工程目录下运行（base 环境）：`python tools\check_ids.py --partial`、`tools\svg_check.py`、`tools\line_check.py`、`tools\cite_check.py`。输出里**只修自己章文件名**的错误（其他章未写会报缺章 ERR，忽略）。
3. svg_check/line_check 对自己章报 0 错误、cite_check 不报自己章的 ERR 后才算完成。
4. 交付信息里报告：片段行数、图数、代码块数、facts 条数、四项检查结果。
