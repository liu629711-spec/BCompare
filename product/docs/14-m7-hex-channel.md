# 14 — M7 hex 比较通道

功能 5（二进制/十六进制比较，U5）全程。全部结论来自 Oracle 实测
（`product/verify/probes/m70_*_probe.py` → `product/verify/runs/m70*`，
共 8 批探针 + 归档 ~40 份报告；每批串行、跑前/跑后残留检查 zero）。
**所有几何/间距裁决只用整数序数**（docs/12 §3 的教训：显示层对分隔符
不可信——本轮 m70 首读 zh 帧时 grep/od/编辑器再次互相矛盾）。
## 1. 动词与 CLI 面（m70，`runs/m70-hexsurface-*`）

| 脚本 | 退出 | 说明 |
|---|---|---|
| `hex-report layout:<l> output-to:"%3" "%1" "%2"` | **0** | 唯一合法形态 |
| `hex-report output-to:"%3" "%1" "%2"`（无 layout） | 106 | layout 必填（H1） |
| `file-report` / `binary-report` / `data-report` on .bin | 106 / 106 / 0 | 只有 `hex-report` 这个名字；data-report 在 .bin 上走表格路并写编码错误（H6，不属本通道） |
| `hex-report` 零比较文件（有 layout） | **107**（V2） | 与 data-report 同类的"无 path-only shell" |
| `hex-report` 一个比较文件 | **106**（O1） | data-report 会复用左文件，hex 拒绝 |
| 缺左文件 | **106**（O3/W5） | session-open 类 |
| 缺右文件（左文件正常） | **107**（O2） | 输入加载类 |
| 三个文件 | 106（W6） | parse 的 arity 检查 |
| `options:<x>` | **106**（Y9） | **不同于 data-report 的 105** |
| `output-options:<x>` | 106（Y10） | |
| `layout:bogus` | 106（Y8） | |
| `load:left … / load:right … / hex-report` 两段式 | 106（H7） | 本 build 不实现 hex 的 load 组合 |

`title:"<t>"` 替换帧首行（Y11/V3）。帧其余与表格路完全一致：
`Produced: <斜杠日期>`、空行、`Mode:  All`（summary 无此行）、
`Left/Right file:`；无 BOM、CRLF。英文孪生安装的帧标题为
`Hex Compare`（m70e，runs/m70e-hexreflabels），正常化器 norm-3 收
`16 进制比较(H) → Hex Compare`。

## 2. 行模型（m70b/m70c/m70d/m70f）

- **字节对齐 = 现有 Myers 字节 diff**（等值字节为 LCS 对）；间隙
  (gl×gr) 内先出 `min(gl,gr)` 个**配对变更槽**（两侧都有字节、
  标为非 matched），再出单侧孤儿槽，然后是对齐对。
- **行 = 8 个槽**；任槽不是"配对且 matched"⇒ 该行是 diff 行。
- **块 = 同性质行的极大连续段**（Y11 的收尾块把 4 个配对+4 个左孤儿
  合成一个 `<>` 块；Y5-many 每处变更独立成块）。块之间画横线
  （= 该报告**全局最大行宽**，Y4 证明：36 宽行所在的报告规则线仍是 70）。
- **标记列宽**：报告里只要有一个 diff 行，标记区宽 2；否则宽 1
  （Y1 ` = ` vs Y2 ` <> `）。标记文本只出现在**块首行**（Y5）。
- **列塌陷**：某侧在整个报告中都没有字节 ⇒ 该侧字段整体省略
  （Y13：空左文件 ⇒ ` <> 00 01…`）。
- **interleaved**：同行合并输出 `左偏移(8位十六进制大写) 右偏移 字段`；
  diff 块**两趟输出——先出该块所有含左字节的行、再出含右字节的行**
  （V3 抓到的产品缺陷，见 §4）。偏移为该侧行内首字节下标；某侧无字节
  时该偏移区填 8 空格（Z4/Z5）。偏移**恒 8 位**（Z7：600+1 字节仍
  `00000258`，不回绕不加宽）。
- **summary 计数序**：same → left orphan → right orphan → difference，
  零行省略（Y7/Z1-Z3/V1/V5 双侧安装实测）。配对变更槽算 **1 个差异字节**
  （V5 = 56/31/1/1；V1 = 60/18/2 的 18 个左孤儿正是 64-60-4-2 的
  拆分，钉死配对模型）。
- 空-空：无任何体行（Z6）。

## 3. 字段几何（8 字节槽/行，序数审计）

- 字段宽 33：hex 区 23（槽 0-6 各 `'XX '`，槽 7 两位）+ 2 空格 + 8 列
  ASCII（可打印字节原样，否则 `.`；无字节位置空格）。
- sbs 行 = `左字段(33) + ' ' + 标记区(w) + ' ' + 右字段(33)`，rstrip。
- 奇数长度尾行：槽 7 缺位填 2 空格（W1/Y11 行 `38 39 3A 3B`）。
- interleaved 规则线宽 = 全局最大行宽（51）。

## 4. 本轮抓到并修复的产品缺陷

1. **interleaved diff 块行序**（V3，重放 29/30 → 修）：产品原逐行
   L/R 交错；Oracle 是**块级两趟**（所有左行先、右行后）。
   修复 + 回归测试 `interleaved_diff_block_emits_left_then_right`
   （转录 m70d V1 夹具字节：L=seq(64)+seq(16)、R=FF+seq(59)+0x41）。
2. 帧/标签/计数模型在首轮重放即对（30/30 全帧逐字节）。

## 5. golden 与门禁

`verify/hex/`（append-only，13 判别细胞，`tools/m71_add_hex_goldens.py`
串行 Oracle 生成）：sbs 相等/插入/追加/删除/多块/600 字节/空侧/标题、
interleaved 插入/600/标题、summary 差异/四类。harness 第六套件
`hex`（oracle 双安装 + candidate 脚本对脚本，全帧逐行结构比较）；
norm-3 收 `16 进制比较(H)` 与四个 `…字节` 计数标签。

基线：`M71-gate-01` = **858/858**（819 + hex 26 oracle + 13 candidate）；
hex 产品重放（`extracted/_scratch/hex/replay_hex_product.py`，
覆盖 m70-m70g 全部 31 个 .out）= **30 pass / 0 fail / 1 skip**（唯一 skip
是 m70 的 H6：data-report-on-.bin 表格路细胞，非本通道）+ 1 个
exit-surface 判读；core **269**（+16 hex 单测）、CLI 141/161/118、
pytest **158**（ruleset 断言 norm-3）。

## 6. 残差

- `options:` 在 hex 上是 106 而在表格上是 105：已实测钉死（Y9 vs P6-P9），
  无残差，但**不要**把表格的 105 逻辑复制到 hex。
- hex 的 `load` 两段式（H7）106：未探其它 load 形态；产品不实现 hex load。
- 结构化偏移导航（PE/ELF 段映射，功能矩阵里的"可选结构定义"）未做，
  范围外（本轮只做字节级视图与报告）。
- XLSX/HTML/图片/媒体/注册表/版本报告仍未开始。
