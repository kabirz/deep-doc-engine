# SVG 手绘图规范（必须逐条遵守，构建器 svg_check / line_check 机器检查）

统一画布：`viewBox="0 0 760 H"`（H 按内容 240~560，**width 属性不写**，只写 viewBox），放入：

```html
<figure class="fig">
<svg viewBox="0 0 760 320" font-family="'Segoe UI','Microsoft YaHei',sans-serif">
  …
</svg>
<figcaption>图 6-1 · 管道环形缓冲区与 head/tail 指针</figcaption>
</figure>
```

## 硬性禁令（历史工程血泪）

1. **禁止裸 `&nbsp;`**（XML 解析硬错误）；要空格直接用普通空格。
2. **禁止 `transform="rotate(...)"` 文字**（检查器会误报出画布且打印易截断）；竖排标签改为水平文字放在空白区。
3. **禁止 HTML 注释**包裹 SVG；SVG 内也不写 `<!-- -->`。
4. **marker id 全书唯一**：`<marker id="arrow-ch06-1">` 用 `arrow-章号-序号` 前缀；渐变 id 同理 `grad-ch06-1`。
5. **SVG 内文字不得出现「第 N 章」「附录 X」**字样（书签扫描器会误判）；用「本节」「后文」替代。
6. 文字**必须**有明确 `text-anchor`（start/middle/end），不要依赖默认值（line_check 的缺省陷阱）。
7. 所有元素坐标必须在画布内：留 ≥8px 边距；文字包围盒按 `fs*0.75` 估宽、`fs` 估高自查。
8. 字号：标题 15~16、正文 12~13、注 11；**图内中文字符串尽量短**（≤14 字），长句放 figcaption。

## 线与文字的几何关系（line_check 规则）

- 文字与直线/箭头**不得相交**。标签放在线段端点延长线之外，或与线错开 ≥12px。
- end 锚文字的包围盒按 `(x-w+2, y-0.75fs, x-2, y+0.05fs)` 计算，w=字符数×fs×0.55（英文）/×1.0（中文）。
- 折线拐点、箭头尖端都算"线"的一部分。
- 两行文字之间垂直间距 ≥ fs+6，避免被判粘连重叠。
- 时序图生命线穿字的最稳修法：生命线在文字框区断开成短段。

## 配色（浅色纸面风格，打印友好）

```
底色/卡片   #ffffff  描边 #8a93a5（箱体）#c9cfda（细线）
标题带      #4f6af0 / 深蓝 #1e3a8a   强调   #e4572e（橙红）
填充淡彩    #eef2ff（蓝） #f0fdf4（绿） #fef3c7（黄） #fee2e2（红） #f3e8ff（紫）
文字       #1f2937 主  #6b7280 次
代码/终端   #282a36（Dracula 底）文字 #f8f8f2
```

- 箱体：`<rect rx="8" fill="#eef2ff" stroke="#8a93a5" stroke-width="1.5"/>`
- 箭头统一 `marker`：`<marker id="arrow-ch06-1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6b7280"/></marker>`
- 连线 `stroke="#6b7280" stroke-width="1.5"`；强调线 `#4f6af0`、警示 `#e4572e`。
- 虚线：`stroke-dasharray="6 4"`。

## 常用图形模板

- **流程图**：矩形节点 + 箭头 + 判断菱形（`<path>` 菱形）。
- **结构图**：外壳 rect + 内部标题栏 rect + 分隔线 + 文字列表。
- **时序图**：顶部角色框 + 生命虚线 + 横向箭头消息（文字在线上方 14px）。
- **状态机**：圆角矩形状态 + 弧线转移（弧线贴文字下方走，文字放弧外空白）。
- **对比图**：左右两栏各一个卡片，中间中缝线。
- **内核数据结构图**：外壳 + 标题栏（结构体名用 Consolas）+ 字段行；指针字段用带箭头连线指向目标框。
- **代码示意**：深底 rect（#282a36）+ `<text font-family="Consolas,monospace" fill="#f8f8f2">`，逐行 text y 步进 18~20。

## 自查清单（写完每张图）

- [ ] viewBox 内所有坐标 + 文字包围盒都在 0..760 / 0..H 内
- [ ] 无 rotate / 无 &nbsp; / 无注释 / marker·渐变 id 带章前缀
- [ ] 每个文字有 text-anchor，与任何线段距离 ≥12px
- [ ] 中文标签 ≤14 字；图号连续；figcaption 有
