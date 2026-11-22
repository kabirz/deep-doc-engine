# HTML 片段写法与主题（html-theme）

## 章节片段骨架

片段不含 `<html>/<head>/<body>`，直接从 `<h2>` 开始；**禁止 HTML 注释**（构建器剥离，历史吞章事故）。

```html
<h2 id="ch06">第 6 章 · 章标题（副题）</h2>
<p class="lead">导读段（2~4 句）</p>
<h3 id="ch06-01">6.1 节标题</h3>
<p>正文……行内 <code>api_name()</code>、<strong>强调</strong>、新术语 <em>首次出现</em>。</p>
<h4>更深小标题（不编号，无 id 要求）</h4>
<pre class="code" data-lang="c">/* 代码块：纯转义文本，&lt; &gt; &amp; 必须转义 */</pre>
<p class="src-ref">源码：fs/pipe.c @ L944</p>
<figure class="fig"><svg viewBox="0 0 760 310">…</svg>
<figcaption>图 6-1 · 说明</figcaption></figure>
<table><thead><tr><th>列</th></tr></thead><tbody><tr><td><code>field</code></td></tr></tbody></table>
<div class="tip">💡 <strong>提示：</strong>…</div>
<h3 id="ch06-99">本章要点</h3>
<ul><li>…</li></ul>
```

- id 规则：h2 `chNN`、h3 `chNN-KK`（要点节 `chNN-99`）；h3 编号「N.K 标题」。
- 要素底线（check_ids 断言）：h3≥6、图≥3、代码块≥5、表≥1、lead、facts 文件。经验篇幅：片段 450~680 行 = PDF 10~14 页。

## 代码块

- `<pre class="code" data-lang="c|sh|text|cpp|json">`；内容纯转义；构建器用 Pygments Dracula 重新高亮，作者禁手写 span。
- 单块 ≤55 行；用户态示例完整可编译；sh 提示符写 `$ `（构建器染绿）。
- 块级出处用 `<p class="src-ref">源码：path @ L行号</p>`（行号必须实测）。

## 引用与交叉引用

- 行内源码引用：`fs/pipe.c @ L730`（`@ L` 中间不能有空格变体）。libc 头/示例文件只写名不写行号。
- 章节互引：`第 9 章`、`见 9.2 节`；禁「上一章/下一章」。

## 表格

- 不加 class（构建器统一样式：深蓝表头 #1e3a8a 白字、斑马纹）；字段名一律 `<code>`。
- 超宽表（列多/标识符长）：`<table class="wide">`（fixed 布局 + 打印 7.5pt）。
- 构建器自动在标识符边界插 `<wbr>`，不要手写空格伪装断行。

## 主题速查

- 屏幕：浅灰底 `#eef0f4` + 白色圆角内容卡（960px）；固定侧边栏 296px（按篇分组、scrollspy 高亮）；sticky 毛玻璃 topbar。
- 章题 h2 渐变底 + 左色条：正章 `#4f6af0`、附录 `#8b5cf6`；h3 深蓝 `#1e3a8a` 下边线。
- 代码块 Dracula：底 `#282a36`、前景 `#f8f8f2`；注释 `#6272A4`、关键字 `#FF79C6`、类型 `#8BE9FD`、数字 `#FFB86C`、字符串 `#BD93F9`、函数 `#50FA7B`。
- 行内 code：底 `#f1f3f9`、玫红 `#b3305c`。提示框 `.tip`（绿）/`.warn`（红）/`.note`（蓝）。

## 打印 CSS 要点（00_head.html 的 @media print）

- `@page A4; margin: 13mm 14mm 16mm 14mm`；隐藏 sidebar/topbar、content 摊平。
- **防整本缩小三件套**：`body { overflow-wrap:anywhere }`；`pre { overflow-wrap:anywhere; white-space:pre-wrap; overflow:clip }`；表格特例 `break-word + word-break:normal`（恢复列最小内容宽，防窄列拦腰切断标识符）。
- 分页：`h2.ch { break-before:page }` 每章新页；`figure.fig/tr/th/td/.tip/.warn/.note { break-inside:avoid }`；`table { break-inside:auto }` 长表按行切；`thead { break-after:avoid }`；`orphans/widows:2`；封面缩字号（h1 30pt）。
- 字体栈 CJK 打头：`"Microsoft YaHei", "PingFang SC", sans-serif`（防 Chromium 长任务字体缓存退化）。

## 封面（00_head.html 尾部，每书手改区）

`.cover`：glyph 字母带 → `h1.ct` 书名 → `.cs` 副题 → `.cv` 胶囊标签 → `.cd` 简介（3~5 句）→ `.rule` 渐变条 → `.chips` 知识胶囊（打印 9.5pt，别太多防溢出）→ `.meta` 元信息。类名保持不变，构建器按 `<div class="cover">` 起始切分。
