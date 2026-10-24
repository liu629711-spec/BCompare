# 13 — M6 表格比较：通道定案（2026-10-17，M6.0）

> 功能矩阵 6「表格/CSV 比较」（U3 缺口）的开工情报轮。产品侧现状：
> `table-report`/`data-report` 按名拒绝（exit 106 诚实报未实现，args.rs:118）；
> core 无任何表格模块。本轮全部结论来自 8 单元真 Oracle 探针
> `probes/m60_table_probe.py` → 存档 `runs/m60-table-probe-20261017T155925Z`
> （串行、Job-Object、残留零；夹具 2×2 CSV，一处格内改 + 一处整行换）。

## 1. 通道实测表

| 单元 | 脚本 | 结果 | 含义 |
|---|---|---|---|
| T1 | `data-report layout:side-by-side "%1" "%2"` | **exit 0**，文本表报告 | **表格对拍主通道**。行级状态标记 `=`（同）/ `<>`（重要差异）；列按显示宽补格。 |
| T2 | `data-report layout:xml` | **exit 106，0 字节** | **表格引擎没有 XML 布局**——规格文档与 text 通道直觉在此分叉。 |
| T3 | `data-report layout:summary` | exit 0 | 记账行「1 个相同排 / 2 个重要差异排」——行级统计可作辅助校验。 |
| T4 | `data-report layout:interleaved` | exit 0 | 差异块用 `--------------` 分隔，右行带行号；与文本 interleaved 同族骨架。 |
| T5 | `text-report layout:xml`（.csv 输入） | exit 0，正常 XML | **`text-report` 无视 .csv 的表格关联**，永远按文本比较。既有门禁/锚点通道不受表格关联影响。 |
| T6 | `file-report layout:xml` | exit 106 | file-report 无 xml 布局（与帮助文档一致：仅 side-by-side/summary）。 |
| T7 | `load "<左文件>" "<右文件>"` + data-report | exit 107 | `load` 只收文件夹，不收文件；data-report 的定位参数形态（同 T1）才是文件对入口。 |
| T8 | `file-report layout:side-by-side` | exit 0，与 T1 逐字节同构（414B） | **`file-report` 按扩展名把 .csv 路由给表格引擎**（报告头「表格比较(B)」）——BC 内置关联 `*.csv → CSV 表格格式` 实锤。 |

## 2. 定案

1. **验收通道 = 表格 side-by-side（主）+ interleaved（辅，块结构）+ summary（记账）**，
   全部是**版式文本**，不是 XML。对拍方法沿用 layouts 套件的先例：
   *结构化解析后再逐行比对*（行状态 + 左右单元格序列），不做逐字节对
   （补格宽度依赖显示字体度量，非行为语义）。归一化规则要在 M6.1 用判别
   探针钉死（补格算法、`=`/`<>` 列位置、多行单元格换行进报告时的形态）。
2. **默认行为观察**（T1）：`banana,5` vs `cherry,2` 配成**一个 `<>` 行**而非
   删+加——默认行对齐有 closeness/配对行为，具体算法（Standard vs Myers、
   skew tolerance、closeness 开关默认值）是 **M6.1 第一探针批**的目标；
   不得按帮助文档（sessiontablerows.html，O 级）直接假定。
3. **CSV 内建格式**（D 级规格 + T8 行为证实）：分隔符 `,`、限定符 `"`。
   这是 RFC-4180 公开约定，产品按公开标准自研解析即可；合规红线不变——
   不复制 BC 格式表，只对齐可观察行为。
4. **范围切分**：M6 = CSV/TSV 文本表格（行模型 + 行对齐 + 三布局报告）。
   XLSX/XLS 依赖商业组件 FlexCel 的语义不可用同法验证，**单列后续里程碑**；
   HTML 表格、多工作表、列类型推断同样划出 M6。
5. **产品现状即诚实门禁**：未实现命令按名拒绝 exit 106（args.rs 测试
   `unimplemented_report_types_are_named_as_unimplemented` 在案），M6.1 起
   逐步换成真实实现，拒绝名单随之收缩。

## 3. 残差未知（记录，不硬凑）

- ~~`=`/`<>` 之外是否还有第三种行状态~~ **已收口（§4.6）：四标记全集 `=`/`<>`/`+-`/`-+`。**
- ~~单元格内换行（引号字段含 `\n`）在 side-by-side 报告里的排版形态~~ **已收口（§4.1：算一行，interleaved 行号单计）。**
- 列组间分隔是否依赖区域设置（`formattableregional.html` 存在但未动）。
- T1 报告头部的产生时间行需要归一化规则（layouts 套件已有同类先例可复用）。
- 分隔符检测是"众数投票"还是"逗号恒优先"未分辨；管道符/空白是否候选未探；
  interleaved 块边界的精确规则（P5 与 P2-1x2 两种读法）留给 M6.2 golden 逐字节钉。

## 4. M6.1 行对齐模型定案（四批探针：m61-rowalign / m61b-pairing / m61c-detect / m61d-residual）

存档 `runs/m61-rowalign-20261017T160350Z`（22 报告）、`runs/m61b-pairing-20261017T160932Z`（26 报告）、
`runs/m61c-detect-20261017T161300Z`（14 报告）、`runs/m61d-residual-20261017T161441Z`（8 报告）。
每批跑前残留检查=clean。**共 70 份 Oracle 报告 = 表格引擎的第一批免费回归真值。**

### 4.1 行模型
- **行 = CSV 解析行**，不是物理文本行：引号字段内的换行不拆行——T21 两侧
  `k,"x\ny",2` 行号各算 1（interleaved `1 1` 同排配对，`= ` 状态）。产品必须先做
  完整的带引号解析（RFC-4180 风格：`"` 限定、`""` 转义、字段内 `,`/换行合法）。

### 4.2 对齐 = 文本引擎同款内容对齐（不是行号对齐，也无键列特判）
- 纯插入/删除：孤儿带 `-+`/`+-`，其余按内容对齐（T10/T11）。
- 交换：`k1 k2 k3 k4` vs `k1 k2 k4 k3`（以及 2 行版 x/y 互换）⇒ **BC 选
  `k3+- / k4= / k3-+`**，即 LCS 平局偏向"匹配右序更前的行"（T12/T13/T19 一致）。
  与文本引擎的序偏好同源，产品 Myers 平局方向需对拍钉死。
- 重复行按位置序消费：3 个相同 `r,1` vs 2 个 ⇒ 前 2 个 `=`、第 3 个 `+-`（T14）。

### 4.3 差异块内配对 = 位置 zip，无相似度门槛
- 2×2 全零相似（`aaa,1/zz,9` vs `bbb,2/qq,8`）⇒ 两行都 `<>`，不出 4 孤儿（P1）。
- 1×2 ⇒ 首对 `<>` + 右余 `-+`；2×1 ⇒ 首对 `<>` + 左余 `+-`（P2）。
- 块内有完全相同行时 LCS 在块内继续锚定（P12：m,a,-+x,b,n ⇒ a 锚 b 不挪位）。
  ⇒ **行对齐 = Myers(LCS) 跑整文件；`<>` 只在块内按序 zip 产生**——与文本引擎
  「replace 块内配对」完全同构，M2.6 的 closeness 不参与（T15 `id,1000` vs
  `id,1001` 直接同位 `<>`，无相似配对概念差异）。

### 4.4 单元格相等 = trim 后原文比较
- `k,"a b",1` vs `k,a b,1` ⇒ `=`（引号解码后同，P3）。
- `n,1 ` vs `n,1`（尾空格）⇒ `=`（P4 行2）；`k,a  b,1` vs `k,a b,1`（内部双空格）
  ⇒ `<>`（P4 行1）。⇒ **只 trim 首尾空白，内部空白重要**；不做空白折叠归一。
- 空单元格 `a,,c` vs `a,b,c` ⇒ `<>`（F1，三列标题 A B C 都在）。
- 列数不同 `a,1` vs `a,1,x` ⇒ 左缺列渲染空串 + `<>`（T18）。
- 空行参与比较：`h,1 / <空> / b,2` vs 同构右 ⇒ 空行 `=`（F4）。

### 4.5 分隔符模型（M6.2 batch-5/6 更正本节旧结论）
**两路模型，实测 runs/m62-delimiter-* / m62-autodetect-*：**
- `.csv` 命中 CSV 内建（mask `*.csv`）⇒ **分隔符固定逗号，不做检测**：
  tab、分号、管道全部留在单元格内（D2/D3/D4/D11/D12 均 1 列；D5 `a,b\tc\td`
  ⇒ 2 列 `["a","b\tc\td"]`）。旧说"分号不是候选/扩展名无关"**作废**。
- **其它扩展名**（.txt/.tsv/无扩展/.xyz/.TXT 大写同）⇒ **自动检测**，
  实测候选集含 **逗号、分号、管道、空格、tab**（S2 `a;b`→2 列、S3 管道→2 列、
  S4 空格→2 列；T17/E1 的 .csv 分号不切正是固定逗号的表现）。
  多候选并存时**逗号优先**（S1 逗号+tab ⇒ 2 列 `["a","b\\tc"]`，F2 同）。
  候选全集与优先序未完全钉死（残差，见 §3；产品 M6 只做 .csv 固定逗号路）。
- 引号单元免疫分隔符（E5）；ragged 合法且取最大列数（S5：行1 两列、行2 三列
  ⇒ 3 列）；行内首列宽随最长单元格（S8 `a  b`/`cd` ⇒ col-A 宽 2）。

### 4.6 四状态 + summary 记账
- 标记全集 = `=` / `<>` / `+-` / `-+`（§3 未知1 已收口）。
- summary 四类行标签：`N 个相同排`、`N 个重要差异排`（`<>` 对计数）、
  `N 个重要左边独有排`（`+-`）、`N 个重要右边独有排`（`-+`）（E1/E6/E7/F3）。
  空行算相同排（F4：2 相同+1 差异）。
- ~~计数序 same/diff/left/right~~ **本节旧稿的次序从未被实测钉死**（存档里
  没有多类别并存的细胞）；M6.4 表格门禁首跑抓到反例并实测定案
  **same → left → right → diff**，见 §7.3。

### 4.7 选项面实测：data-report 拒绝全部文本通道选项
- `options:display-mismatches / display-matches / line-numbers / ignore-unimportant`
  全部 **exit 105（脚本错误，报告 0 字节）**（P6–P9）——与帮助文档（O 级，
  声称可用）相反，实测为准。表格通道默认=全部行、无显示过滤。

### 4.8 interleaved 分块细节（引擎渲染层待定）
- `<>` 对的两行同块（P5）；`=` 行各自成块（T14）；1×2 的 `<>` 对与 `-+` 孤儿
  之间**有**分隔线（P2-1x2）——即"块边界=状态变化处 + 每对/每孤儿"两种读法未
  完全分辨（P5 与 P2 的配对形态差异：1×1 vs 1×2）。渲染逐字节钉死留 M6.2
  golden-replay 阶段，用这 70 份报告当回归集。

### 4.9 引擎范围定案（M6.2 动工输入）
1. `product/core/src/table.rs`：CSV 解析（限定符/转义/内嵌换行）→ 行模型 →
   复用文本 Myers 的行级对齐（键=解码单元格序）→ 块内 zip 出 `<>` →
   三渲染（side-by-side/interleaved/summary）。
2. CLI：`data-report`（含别名 `table-report`、file-report 的表格路由）从
   exit 106 拒绝名单毕业；`text-report` 不受影响（T5 实锤）。
3. 验收 = 70 份探针报告结构化对拍（仿 layouts 先例：解析后逐行比，不逐字节；
   时间头行归一化沿用 layouts 规则）+ 新增锚点入 append-only 清单。
4. XLSX/HTML/多表/键列/列类型/选项面 维持划出。

## 5. M6.2 渲染模型定案（仿真器 56/56；探针批 m62b-width）

`_scratch/table/simulate_table.py` + `replay_table.py`：对 56 份 .csv 存档报告
（m60/m61a-d 55 份 + 新判别批 m62b-width 中并入者）体层逐行重放 **56/56 全绿**；
7 份非 .csv（自动检测路）诚实 skip。新探针 `probes/m62b_width_probe.py` →
`runs/m62b-width-20261017T174545Z`（12 报告，含镜像 ragged W7、不对称宽度 W1/W2）。

**定案规则（全部体层，报告帧头由重放剥离）**：
- **对齐平局方向**：LCS DP 在 `down ≥ right` 时先推进左轴 ⇒ "先孤左行、
  匹配锚在更早右行"（T12/T13 钉死；**difflib 的偏向相反，仿真器改用自写 DP**。
  Rust 用 myers.rs，移植时必须验证同方向——见残差）。
- **列数 n = 两侧最大列数**（全局）；每列宽度只由**该侧**行算（表头字母下限 1）；
  缺列渲染空单元格宽 1（T18 左也出 C 列；W7 镜像同）。无"跨侧撑宽"（W1/W2
  不对称宽度证伪了撑宽假设）。
- **单元格渲染** = trim→显示（引号内 `\n`→`NUL 0x00`，T21 原字节实测）；
  side-by-side：数字（`-?\d+(\.\d+)?`）右对齐、文本左对齐；
  interleaved：**全部左对齐含数字**（T19/T21/W1 实测）；空单元格照宽度补空格、
  整行只 rstrip 一次（F1/F4 尾空不 rstrip 到标记）。
- **side-by-side**：标记字段 `=`→`" =  "`（全同报告 `" = "`）、`<>`/`+-`/`-+`→
  `" X "`；左孤儿=左格+标记 rstrip；右孤儿=左格(ljust left_w)+标记+右格；
  表头=左块**不 rstrip** + 空白标记场(3/4) + 右块 rstrip；顶/底横线宽=最宽行。
- **interleaved**：共享列宽（两侧逐列取 max）；数字场宽度=各侧最大行号的位数，
  布局 `<lnum> <rnum> <cells>`；**`=` 行显示两个行号**（子代理修复的关键错）；
  `<>` 对共享一块（两行，各带各号）；每状态组一块；块间+尾横线。
- **summary**：计数序 same/diff/left/right、零省略；中英标签对在 m62-reflabels
  抓取（`N same row(s)` / `N 个相同排` 等；`的`不对称 repack 怪癖同文本通道）。

**残差（M6.2 新增）**：
- EOF 双换行计数：`a\n\n` 尾随空行 BC 算一行（W4 interleaved `5` 号孤儿行），
  仿真器 split_records 冻结在 RFC-4180 丢尾行为，未在 56 例内 ⇒ Rust 行切分
  需按 **lines.rs 同款语义**（BC 文本通道也按行计数）实测钉。
- myers.rs 的平局方向与仿真 DP 的等价性未在 Rust 层验证（移植第一测试项）。
- 全同多列报告的表头空白场宽 3 由标记规则推断、无直接存档。
- 自动检测候选全集/优先序（§4.5）划在产品路之外。

## 6. M6.3 产品落地（2026-10-18）

- **core/table.rs**（新模块，第十一例产品改动）：固定逗号 RFC-4180 解析
  （引号/`""` 转义/引号内换行）、`align_rows`（复用 myers.rs 锚点 + 间隙
  位置 zip；平局方向由 myers 既有实现给出，经 68 例存档验证与 Oracle 一致）、
  三渲染器 + 帧（`Table Compare`/dash 时间戳/两行文件路径/无 BOM；
  `title:` 顶替首行，X4 实测）。`stamp.rs` 加 `dashed()`（表格通道实测
  `yyyy-mm-dd`，文本通道斜杠不变）。
  **【M6.4 更正：帧日期 dash 是误读，表格与文本通道同为斜杠；`dashed()`
  已删除，见 §7.1。体层 68/68 重放剥离帧，所以错误穿越了 M6.3 的全部门。】**
- **CLI**：`data-report`/`table-report` 从 106 拒绝名单毕业 → 新
  `Command::TableReport`；实测错误面全套：任何 `options:` → **105**
  (P6-P9)、`output-options:` → **106** (X8)、`layout:xml` → **106** (T2)、
  零文件 → **107** (X5)、缺文件 → **107** (X7)、三文件 → **106** (X6)。
  exit_code 表新增 105（含表格参数类复用的实测说明）。--help 同步。
- **验收**：产品二进制重放 68 份 .csv 存档报告体层 **68/68**
  （`replay_table_product.py`，中文计数行经实测标签对映射）；核心 245 单测
  （+24 表格）、CLI 161（+10 表面）；文本通道零回归（m26 0 / fuzz 120 /
  gateb 167/182 基线不变）；**官方门禁 `M63-table-01` = 762/762**，零残留。
- **产品重放抓到仿真器漏项**：W3-2digit 的编号字段**右对齐到该侧最大行号
  位数**（` 1  1 a1  1`、`   13 x   13`）。仿真器的夹具从未有 ≥10 行 ⇒
  存档 56 例对"宽度"的覆盖不足；已同时补进仿真器文档、Rust 实现与单测。
  教训入册：**产品二进制重放是更强的门**，仿真器绿 ≠ 产品绿。
- **残差更新**：W4 尾随空行语义（BC 把 EOF 前空行算行；Rust 解析器实测
  与之一致，`split_records` 不预剥尾换行）；≥3 位行号未探（W3 只到 13）；
  26+ 列字母表续法未探（>26 列渲染 `#` 并记残差）；自动检测路（非 .csv）
  仍未实装（§4.5 规则在手，产品路划出 M6.3）。

## 7. M6.4 收尾轮（2026-10-18）：帧更正、宽度残差、自动检测、表格门禁

四个子任务（c 宽度补探 → b 自动检测 → a golden+门禁）连跑，外加轮首一
个字节普查推翻了 M6.3 的帧结论。**全部结论来自实测探针/门禁，无一条来
自帮助文档。**

### 7.1 帧日期 dash→slash 更正（display 层误读，字节普查翻案）
- M6.3 记录"表格通道实测 `yyyy-mm-dd`"。M6.4 轮首用序数级普查全部
  114 份表格存档报告（中文 current + 英文 reference 双安装）：**0 例
  dash、114 例 slash**（`2026/10/18`，与文本通道完全相同）。当初的
  "dash 实测"是把报告里其他连字符误读进日期行（od/grep 的显示层
  转义与渲染互相矛盾，最终裁决只用整数字节计数与序数列表）。
- 产品当时在 `render_report` 调 `stamp.dashed()`，帧行输出 dash——
  **真实缺陷**。体层重放剥离帧，68/68 与单测都没拦住；只有把帧纳入
  比较面才能。修复：`render_report` 直接用 `{stamp}`（斜杠），
  `stamp.rs` 删除 `dashed()`；帧单测转录改为斜杠。
- 教训入册：**验收面必须覆盖帧**。以后表格细胞一律全帧比较
  （`Produced:` 行折叠为 TIME、路径行保留逐字节）。
- 修复后经整数字节复核：产品帧分隔符 47(`/`)，与 Oracle 47(`/`) 一致。

### 7.2 宽度补探 m64/m64c2：三个残差收口 + 一个渲染新规则
存档 `runs/m64-residual-*`（10 报告）、`runs/m64c2-letters-*`（2 报告）。
- **≥3 位行号**：W3 规则外推成立——interleaved 编号场宽=该侧最大行号
  位数，`lw_=3`（102 行），空号场=3 空格。无新代码。
- **>26 列字母**：实测 **A..Z 后为 `AA`,`AB`,`AC`**（Excel 式 bijective
  base-26），不是续 ASCII。且**字母自身的字符数就是该列宽度下限**
  （C2-29narrow：全部 1 字符单元格，第 27+ 列仍渲染宽 2）。
  `column_letter()` 实装，`side_widths` 下限由 1 改为字母长度；
  `#` 占位残差删除。两个形状（宽 2/3 与窄字母撑宽）转录进单测。
- **EOF 空行**：m64 E1/E2/E3 证实 BC 把 EOF 前的空行计为真实行
  （E1 右侧 `a,1\nb,2\n\n` → 第 3 行 `-+` 孤儿；E2 双尾行 → 两个孤儿；
  E3 双侧 → `=` 行）。Rust `split_records` 行为实测一致（只丢
  "最后一个换行之后的空段"），**0 代码改动**，重放全绿。
- **规则线宽度 = rstrip 前的行宽**（m65b SP5 发现）：单元格尾随空格
  参与行宽，横线按未 rstrip 的最宽行拉长；100 例存档两种算法同结果
  （delimiter 路尾列从不拖尾空白），rawline 细胞把它们分开——
  sbs 改为 raw 行算宽、输出再 rstrip。

### 7.3 表格 golden 树 + 门禁首跑抓到 summary 计数序错误
- 新树 `verify/table/`（append-only 清单，16 判别细胞：帧/标记/平局/
  zip/重复/引号内换行/ragged/数字对齐 2 位场/EOF 幻影/AA 字母撑宽/
  检测 tab/优先序/rawline/title）+ 门禁第五套件 `table`
  （oracle 16 + oracle×reference 16 + candidate 16），逐行结构比较
  沿用 layouts 先例；norm-2 收表格标题/计数标签对。
- **首跑即抓到帧剥离放过的缺陷**：summary 计数序。t-summary-mixed
  （同具 diff 与 right-orphan，存档从未有过的组合）显示 Oracle 序为
  same → right → diff；m66/m66b 四态并现探针钉死完整序
  **same → left → right → diff**。旧 §4.6 的 "same/diff/left/right"
  是未测推断，已划线更正。`summary_body` 修序 + O4-all 转录单测。
- 门禁：`M64-gate-01` = **810/810**（762 + table 32/32/16），零残留。

### 7.4 自动检测路实装（batch-7 m65 + m65b/m65c）
- 存档 `runs/m65-autodetect-*`（15 报告）、`runs/m65b-spacerules-*`
  （10 报告）、`runs/m65c-spacemodel-*`（6 报告）。
- **定案**（十格两两矩阵，无一例外）：非 `.csv` ⇒ 对**两侧联合**扫描
  （PF1/PF2：单边有候选即生效于双方），优先链
  **逗号 > tab > 分号 > 管道**；候选必须在**引号外**至少出现一次
  （Q1/SP4：逗号只在 `"…"` 内不算）；`.csv`（双侧任一命中，大小写
  不敏感）钉死逗号（CS1）；**全无候选 ⇒ rawline**（整行一个单元格、
  保留引号字节、去前导空白 SP10、尾随空格是数据 W1/SP5、逐字节相等
  SP9）。
- **空格候选 = 已记录残差，不实装**：S4/SP1/SP6-SP9 的接受条件互相
  矛盾（S4 切、SP1 同形不切、SP6 只切一侧、SP9 表头宽 3、SP7 双空格
  撑宽……没有任何单一规则能同时成立；m65c 六格补探后仍矛盾）。
  产品在这些细胞落 rawline，`replay_table_product.py` 列 5 个
  **KNOWN(space residual)**——既不冒充通过也不算失败，等后续轮次定案。
- Rust：`TableFormat{Delimited(char)|RawLine}`、`detect_format`、
  `candidate_present`（镜像 split 的引号边界规则）、
  `split_records_delim`（旧 `split_records` 保持 csv 别名）；
  `trims` 贯穿 display/宽度/对齐键（rawline 逐字节、delimited trim）。
  6 个新单测（扩展名钉死/优先链/联合检测/限定符屏蔽/rawline 空白/
  rawline 相等）。
- 全帧重放升级：体层→**帧+体全量**（114→162 细胞，含 exit-surface
  细胞复用 .bcs 原行）；**157 pass / 0 fail / 5 known-space / 2 skip**。

### 7.5 基线更新（本轮后）
core **253**（+2 字母/宽 +6 自动检测，含 summary 序转录）；CLI
141/161/118 不变；large_input 5/5@6.95s；harness pytest **158**
（+1 ruleset bump 改写 + 表格标签折叠例）；m26 0 / fuzz 120 / gateb
167/182 / 表格全帧重放 157+0；官方门禁 **810**（含 table 套件）。

### 7.6 残差（更新）
- ~~≥3 位行号~~ ~~26+ 列字母~~ ~~W4 尾空行~~ ~~自动检测候选集/优先序~~
  **四项本轮收口**。
- **空格候选接受条件**（§7.4）：六探针批后仍内部矛盾，待专用轮。
  → m67 攻坚轮已跑（§8）：矛盾定位于 BC 自身渲染（H5 核心格），空格候选
  维持不实装，转永久 KNOWN。
- `.csv` 大小写混合扩展名对（一侧 .csv 一侧 .txt）未探。
- interleaved 的 rawline 形态未探（本轮 sbs 细胞足够，interleaved
  rawline 若将来实测不符，按 KNOWN 处理）。

## 8. m67 攻坚轮：空格候选矛盾定案（2026-10-18）

探针 `probes/m67_space_attack_probe.py` → `runs/m67-spaceattack-20261018T054039Z`
（8 对 × sbs+interleaved 双布局 = 16 报告，串行 Oracle，跑前/跑后残留 zero）。
方法升级：sbs 列补空格会毁掉单元格字节，**以 interleaved 的逐字节单元格列表
为判定读数**（H1-H8 全部双布局归档）。

新增判别（全部与产品现行为一致）：

- **单行文件永不空格切分**（H1 `a b`、H2 `a  b` 自身相同 ⇒ interleaved 单列
  `A`，rawline）。接受条件与行数无关的"每行候选"说法不成立。
- **逗号 > 空格优先**（H6 `a b,c`/`a,b c` ⇒ 两侧都按逗号切，interleaved
  单元格 `a b`|`c`，空格留在单元格内）。空格候选若将来实装必须排在逗号链
  之后——与现链 comma > tab > semi > pipe 的相对位无关紧要（空格不在链内）。
- **无一空格行的文件 ⇒ rawline**（H7，SP3 的 interleaved 直读复核）。
- **对齐单空格 = 切分且单元格保留空格**（H8 = S4 形，interleaved 单元格
  `a  b` 双空格、表头两列 `A  B`；产品 rawline 在此仅补白形态与帧不符 ⇒
  KNOWN）。H4 同理：两侧行 1 原始字节本就不同（`a b` vs `a  b`），`<>` 可
  由"保留 run 的切分"模型解释，不构成矛盾证据。

矛盾定域（Oracle 输出自身矛盾，非我们的模型缺项）：

- **H5**（左 `a b`/`c d ␠`、右 `a b`/`c X`）：两侧行 1 **原始字节逐字节相同**
  （fixtures 审计：[97,32,98,10] == [97,32,98,10]），BC 表头是 split 形
  （两列 `A   B`）而第一行渲染 `<>`。任何"逐行切分、按位置比较单元格"的
  模型都会让行 1 得 `=`；行 2 的差异（尾随空格）不应回溯改变行 1 的切分。
  SP6/SP9 的"相同行 `<>`"与它同族（sbs 补白使其不可直读，H5 以
  interleaved 首次把它钉成可读矛盾）。

⇒ H5 + H8/H4（切分且保留 run）+ H3/SP1（错位拒切）+ H1/H2（单行拒切）无法
由同一接受/比较规则同时满足。这是 m62/m65/m65b/m65c 六批之后第七批独立探针
再次命中同一矛盾族，判定**空格候选为 BC 自身渲染不一致的永久记录差异**，
产品维持 rawline 回退。KNOWN 表从 5 细胞扩至 8 tag（+H4/H5/H8，11 份报告；
H4/H8 属"Oracle 切分、产品 rawline"的形态差，H5 属 Oracle 自矛盾），重放
基线 **167 pass / 0 fail / 11 known / 2 skip**（总 178）。

### 8.1 本轮后残差（最终）
- 空格候选：定案为永久 KNOWN（矛盾在 Oracle 输出侧，非缺探针）。
- ~~`.csv` 混合扩展名对、interleaved rawline~~ **m68 已收口（§9）**。

## 9. m68 残差收口轮：混合扩展名 pin + interleaved rawline（2026-10-18）

探针 `probes/m68_mixed_ext_interleaved_probe.py` →
`runs/m68-mixedext-20261018T062627Z`（8 对 = 5 MX + 3 IR，11 报告；
全部序数审计读数；跑前/跑后残留 zero）。

**§8.1 两残差定案（产品行为无需改动，全部实测一致）**：

- **`.csv` pin 对混合扩展名对成立**：MX6（L `.txt`/R `.csv`，内容 `a;b`
  无逗号）与 MX1（`a;b ` 尾空格）⇒ 表头**单列**、行 `a;b = a;b`（trim
  掉尾空格）—— `.csv` 一侧把**双侧**钉死固定逗号（候选规则 (i)；(ii)/(iii)
  会让联合扫描在两侧都检出分号切成两列）。MX4（L `a,b` .txt / R `c;d`
  .csv，序数审计：左两列 `a`|`b`、右单列 `c;d`）与 pin 一致但**不判别**
  （联合逗号同结果）；判别格是"无逗号 + 混合扩展名"（MX1/MX6）。
- **大写扩展名同样命中**：MX2/MX3（`.CSV`/`.TXT`）⇒ 逗号 pin 生效
  （单列 `a;b <> c d`），产品 `eq_ignore_ascii_case` 实测正确。
- **interleaved rawline 与 sbs 同模型**：IR1 去前导空白（`ab`）、逐字节
  相等；IR3 数字 rawline 在 interleaved 左对齐（T19/T21 规则对 rawline
  同样成立）。产品 `trims` 贯穿两种版式，重放全过。
- **IR2**（两侧相同 `a b `/`c d `，interleaved）：Oracle 表头两列 =
  空格切分（H8/SP8 同族）⇒ 入 KNOWN 表（(m68-mixedext, IR2)）。

**golden 收编** `tools/m68_add_table_goldens.py` → 3 格追加进
`verify/table/`（append-only，16→19）：`t-mixed-csvp`（MX6 pin 判别）、
`t-int-rawline`（IR1）、`t-int-num`（IR3）。`TableCase`/manifest 新增
可选 `ext_right`（混合扩展名对专用；缺省同 `ext`，推导约定不变）。

**门禁**：`M68-gate-01` = **819/819**（810 + 3 格 × (oracle 双安装 +
candidate)）；`M68-table-01` table 套件 57/57。空格家族至此**全部**
KNOWN 化（9 tag/12 报告，重放 175 pass/0 fail/12 known/2 skip，总 187），
无任何在案残差要求实装。
