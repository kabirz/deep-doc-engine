# 质量门禁与协作（quality)

## 构建链内检查器（顺序即 build_all 调用序）

| 检查器 | 断言 | 报错含义速查 |
|---|---|---|
| `check_ids` | id 唯一、片段以 h2 开头、无注释、无双重编码乱码（Ã©/锟/\ufffd）、章号配额、要素底线（h3≥6 图≥3 代码块≥5 表≥1 lead）、pre 内无块级标签 | 「pre 内块级标签」= 代码没转义；「缺章」在 --partial 下忽略 |
| `tag_check` | strong/em/code/b/i/u/sub/sup/kbd/span 开闭配平（栈式匹配，剥 pre） | 未闭合 `<code>` 会把玫红等宽样式污染后续数章——必须修 |
| `svg_check` | 八禁令 + 出画布（>1px 容差 ERR、贴边 <8px WARN）+ text-anchor 显式 | 见 svg-guide.md；文字宽按 CJK fs×1.0 / 西文 fs×0.55 估算 |
| `line_check` | 线穿字（距离≤1.0 ERR）/字贴线（<5.0 WARN）/字重叠（面积>小框 35% ERR）；line/polyline/path 全解析（贝塞尔采样） | 时序图生命线穿字：生命线在文字框区断开成短段 |
| `cite_check` | 文件存在 + 行号不越界（对照 nch.KSRC，按文件名索引）；同名文件按引用路径尾部分量深度择优；libc 头/示例文件白名单豁免 | KSRC=None 自动跳过；Makefile/Kconfig 同名太多豁免 |
| `xref_check` | 「第 N 章」N 存在、「N.M 节」目标存在（剥标题自身） | partial 下降级 WARN |
| `fig_seq_check` | figcaption「图 N-K」章内 K 从 1 严格递增 | 跨章复制图忘改号最常见 |
| `final_check` | 页数下限 + 打印缩放比 0.96~1.04（h2 实测字号/18.75pt） | FAIL→跑 _overflow_probe.py 找超宽元素 |

## 扩展检查器（按书选配，不在默认链）

- `hist_check`：搜无依据版本说法（「X 新增」「旧内核」「5.x」等）——版本归属只允许 FACTS 白名单。**凡写源码史的书都该配**。
- `demo_check`：抽出完整用户态示例，WSL gcc `-std=gnu11 -D_GNU_SOURCE -pthread` 编译（不运行）；内核模块跳过。
- `blank_scan`：非章首页上半部就结束 = 大图/大表被 `break-inside:avoid` 整页推走（半空页）。
- `colon_check`：页尾最后一行以「：」结尾 = 引导句与图表被分页拆开。
- `box_check`：SVG 绘制顺序遮挡模拟（后画垫片可遮线；时序图竖直虚线在填充之下属常态不报）。
- `attr_check`：line/rect/text 属性完整性（缺 x1/y1 等）。
- `inline_check`/`wbr_long_ids`：未闭合 span 吞版面；超长标识符断行。

## 历史踩坑速查（每条都是真实事故）

1. 未闭合行内标签跨章污染数章样式（tag_check 根治）。
2. Chromium 打印遇超宽元素整本等比缩小（曾 0.59~0.765）→ 防缩放三件套 + final_check 缩放比门 + _overflow_probe。
3. 数百页长任务后半本字体缓存退化回退宋体 → CJK 字体栈打头 + 分半打印。
4. 分半打印末页幽灵深色残影 → sanitize_ghost 白块覆盖。
5. text-anchor 缺省陷阱：估宽器假设与 SVG 规范缺省（start）不一致 → 强制显式。
6. 臆测「新增于某版本」批量翻车（非 git 树无法证明）→ FACTS 版本铁律 + hist_check。
7. 同名头文件误配（include/linux/X.h vs include/uapi/linux/X.h）→ 路径尾部深度择优。
8. SVG 裸 &nbsp; XML 硬错误、旋转文字打印截断、marker id 撞名、图内出现「第 N 章」骗过书签扫描器。
9. 注释吞章（构建器剥离 HTML 注释时连章吞掉）→ 全线禁注释。
10. BOM/双重编码乱码混入正文 → strip_bom + check_ids 特征串检测。
11. 表格相邻单元格不换行粘出 `CLONE_VM0x100` 假符号（cite_check 也会误报）。

## FACTS 闭环（多代理防编造机制）

- `FACTS.md`（主对话/牵头人维护）：基线声明、版本铁律、共享事实、待核实清单、已知引入版本白名单。各章作者**不回写**。
- `src/facts/chNN.md`（章作者维护）：实测事实 + 证据行号；「与教材不符」必须记录；FACTS 的待核实条目由对应章作者核实后落入本章 facts。
- cite_check 对着真实源码树执法 → 「人记录、机器核验」双保险。

## 多代理分派建议

- 每代理 1~N 章，按 `src/chNN_*.html` 文件分组互斥（不共写文件就不冲突）。
- 每章交付前必须过四件套自检（check_ids --partial / svg_check / line_check / cite_check），只修自己章的报错。
- 检查器是全书级的（svg_check 扫所有片段）：自己章 0 错后才交付，别被他章报错带偏。
- 限额/限流波次：先查落盘（哪些章已写完）再重派缺失的；已落盘未达标的只派修复任务。
