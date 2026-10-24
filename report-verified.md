# BCompare 逆向工作区 — 实测报告

生成时间：2026-10-12
目标：`D:\bc-official\app\BCompare.exe`（Delphi，50 MB，x64）
SHA-256：`4e44c526722d6420e89b372460c519e293c417723305b83ed0eff853db16ce5d`

---

## 一、直接回答

**可以。** 已经在这台机器上端到端打通：**定位 → 取回规格 → 反编译算法 → 具备继续开发的基础**。

关键的工程问题在本轮被解决：REA 默认每次调用都重新分析 25 分钟，无法支撑交互式逆向。现在建成了**持久化 Ghidra 项目**，一次分析（30 分钟）之后，任意函数反编译/全局索引只需 **8–9 秒**。

### 实测性能

| 任务 | 耗时 | 命令 |
|---|---|---|
| 建持久化项目（一次性） | 1818 s | `python tools/ghidra-persistent.py build` |
| 反编译任意函数 | **8 s** | `python tools/ghidra-persistent.py decompile <addr>` |
| 导出全部 121,485 个函数 | **9 s** | `... list-functions` |
| 建字符串→函数索引（52,870 串 / 21,176 对） | **25 s** | `... string-index` |

对比：同样的操作走 REA CLI 每次要 1500–2500 秒。

---

## 二、可以做什么（已实测）

| 能力 | 工具 | 实测结果 |
|---|---|---|
| 字符串搜索 | `search_strings` | `Diff` 命中 213 条 |
| 交叉引用定位 | `xrefs` | `TogDiff`@`0x140da6c08` → 代码 `0x140da4b8f`（0.0 s） |
| 函数反编译 | `decompile` | 8 s 拿到 872 行 C 伪代码 |
| 全量函数枚举 | `list-functions` | 121,485 个函数（含 1,631 个具名导入 API） |
| 字符串到函数反查 | `string-index` | 21,176 组对应关系 |
| UI 资源解码 | `batch-tpf0.py` | **211/211 全解析**，3,641 个 UI 对象 |
| 格式语法提取 | `export-bcfileformats.py` | 25 套格式词法规则 |

**已知边界**：BC 符号已剥离（除 1,631 个导入 API 外全是 `FUN_xxx`），所以不能按 `DiffLineAlign` 这类名字直接找函数——必须走**字符串 → 索引 → 反编译**这条路。这条路已跑通。

---

## 三、已取回的规格资产（可直接用于开发）

### 1. 全部 UI 命令面 — 326 条命令
`extracted/ui-commands.md`（60 KB）、`extracted/ui-spec.json`（1.3 MB）

- 15 个动作表，**326 条带标题/加速键的命令**
- 24 个含菜单项的表单，含快捷键与提示文本
- 完整的三方合并命令模型（39 条）：`TakeLeft` / `TakeCenter` / `TakeRight` / `TakeLeftRight` / `Conflict` / `FavorLeft` / `FavorRight`
- 目录同步命令：`SyncCopyLeft` / `SyncCopyRight` / `SyncDeleteLeft` / `SyncDeleteRight`

### 2. 25 套文件格式词法规则
`extracted/bcfileformats-spec.json`（60 KB）、`extracted/BCFILEFORMATS.xml`

每套含 `Keyword` / `Identifier` / `Number` / `String` / `Directive` / `Comment` / `Operator` 类别及 `Mask`、`TabSize`、`TabAsSpaces`、`DlmDelimiters`、`CaseSensitive` 等参数。规模：SQL 301 项、PERL 230、HTML 176、PAS 107、CPP 101、JAVA 50、JS 44、PYTHON 35。

### 3. 本地化资源字符串
`extracted/rcdata/res-codes-parsed.json`（436 KB）

**5,435 条字符串**，其中 4,550 条标识符，覆盖 **152 个 BC 自有命名空间**（`BcFileFormat_`、`ViewText_`、`ActnTable_`、`VerRules_`、`DirFilters_` 等）。从中可直接读出差异分类体系（重要/不重要/被忽略 × 行/字节/像素/项）。

### 4. 反编译出的算法线索
`extracted/pseudocode/`（2 个函数，可直接扩展）

- `TogDiff-referrer.c`：BC 命令分发器 `FUN_140da4710`（7,756 字节），引用全部动作词汇
- `diff-engine-core.c`：`FUN_140dac3c0`（8,501 字节），引用 `DiffMode`、`NeverAlignDiffs`、`ExpandDiffsOnLoad`、`AlignKind`、`AlignQuick`、`MergeFavorSide`、`CompareEndings`

后者是**差异引擎的配置核心**——这 7 个配置名就是 BC 对齐行为的控制开关。

### 5. 完整函数与字符串索引
- `extracted/functions.tsv`（6.5 MB）：121,485 函数入口+名称+大小+签名
- `extracted/string-function-index.tsv`（1.2 MB）：21,176 组「字符串 → 引用它的函数」

有了这两张表，**任意 BC 功能都能在几秒内定位到实现它的函数**。

### 6. 其余
- 243 个原始 RCDATA 块（SHA-256 校验）
- `PRESETSHAPES_XML.out`（548 KB）、`PRESETTABLESTYLES_XML.out`（525 KB）：OOXML 预设形状与表格样式
- 持久化 Ghidra 项目 `D:\Rea\ghidra-project`（1.2 GB，已含完整分析）

---

## 四、开发路线

### 路线 A：继续深挖算法（现在很便宜）
每次反编译 8 秒，可以放手批量做。建议顺序：
1. 从 `diff-engine-core.c` 出发，看它调用了哪些函数（`get_callees`）
2. 在 `string-function-index.tsv` 里搜 `Tolerance`、`Orphan`、`Importance`、`Rules` 定位评分与孤儿行归属逻辑
3. 用 `BatchDecompile` 脚本一次导出整条调用链

### 路线 B：基于已取回规格自建
数据层已经够做一个可用产品：
- **词法层**：直接用 `bcfileformats-spec.json` 的 25 套规则（这是 BC 自己用的）
- **对齐层**：Myers O(ND) / Patience / Histogram（公开算法）
- **词级高亮**：Google diff-match-patch
- **UI 层**：`ui-commands.md` 里的 326 条命令可直接作为功能清单与快捷键表
- **差距**：重要性评分与孤儿行归属需要路线 A 才能拿到确切公式

---

## 五、环境备忘（重要）

- `rea` 6.4.0（全局 npm）、Ghidra 12.1.4（`D:\Ghidra\ghidra_12.1.4_PUBLIC`）、Node 24
- **`GHIDRA_INSTALL_DIR` 未持久化**，调用 REA 时需显式 export
- **REA 的 Ghidra 每次重新分析**（`ephemeral-source-immutable` + `-deleteProject`），默认截止 330 s 必然超时；可用 `REA_GHIDRA_STARTUP_TIMEOUT_MS` 放大，但仍是每次 25 分钟。**日常逆向请用持久化项目**
- REA MCP 会话内首次查询付分析费、后续查询 0 秒，但 REA 自带 SDK 客户端有 60 秒请求上限，需用原始 stdio（`tools/mcp-raw-probe.py` 是可复用实现）
- `%TEMP%\rea-ghidra-*` 每次残留约 500 MB，可安全清理

---

## 六、工具清单

| 文件 | 用途 |
|---|---|
| `tools/ghidra-persistent.py` | **主力**：build / decompile / list-functions / string-index |
| `tools/ghidra-scripts/DumpDecomp.java` | 反编译单函数为 C |
| `tools/ghidra-scripts/ListFunctions.java` | 导出全部函数表 |
| `tools/ghidra-scripts/BuildStringIndex.java` | 建字符串→函数索引 |
| `tools/tpf0_parse.py` | TPF0 Delphi 对象流解析器（已修正 4 处格式问题） |
| `tools/batch-tpf0.py` | 批量解析 211 个 UI 流 |
| `tools/export-bcfileformats.py` | 导出 25 套格式语法 |
| `tools/parse-rescodes.py` | 解析资源字符串表 |
| `tools/render-ui-commands.py` | 渲染命令面为 markdown |
| `tools/mcp-raw-probe.py` | 无超时限制的 REA MCP 客户端（备用路径） |

---

## 七、对上一版报告的更正

上一版 `report-final.md` 有三处与磁盘实物不符，本轮已修正：

1. **解压产物是 0 字节** — 报告称已产出 `RES_CODES` / `PRESETSHAPES_XML` / `PRESETTABLESTYLES_XML` 的 `.out`，实际都是空文件。现已真正解压（223 / 548 / 525 KB）。
2. **语法表未导出** — 报告称已导出 25 格式语法，磁盘上无对应文件。现已导出并验证。
3. **快照用途被高估** — 报告称快照可避免重复加载；实测快照只记录分析参数指纹，**不**加速重新分析。
4. **UI 解析完成度被低估** — 报告称 211 个 TPF0 对象文件，实际此前解析器只完整解出 12 个；修正 4 处格式问题后达到 **211/211**，对象数从 285 增至 3,641。
