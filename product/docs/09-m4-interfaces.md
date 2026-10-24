# 09 — M4 接口冻结（脚本子集 + 统一入口）

> 冻结日期：2026-10-14
> 依据：`verify/probes/U5-FINDINGS.md`（13 轮 O 级实测）+ `help/scripting_reference.html`
> + `help/command_line_reference.html`（官方规格）
> 目的：**先冻结、再并行**。三路实现必须只依赖本文的接口签名与语义，不得各自发明。

---

## 0. 交付物与编排

M4 的验收：**给定脚本，本工具与 BC 产出同布局的等价报告**（`04-milestones.md` M4）。

三路并行、文件不重叠：

| 路 | 交付 | 拥有文件 | 依赖 |
|---|---|---|---|
| **A** | 脚本前端：词法 + 命令解析 + CLI 参数解析 | `product/cli/src/script/lex.rs`、`parse.rs`、`product/cli/src/args.rs`（修改） | 无（纯前端） |
| **B** | 执行器：状态机 + 报告生成 + 文件夹展开策略 | `product/cli/src/script/exec.rs`、`product/dir/src/expand.rs`（新增）、`product/dir/src/tree.rs` / `report.rs`（修改） | A 的 AST + 既有 core/dir 引擎 |
| **C** | 入口 + 退出码 + 门禁语料 | `product/cli/src/main.rs`、`product/cli/src/exit.rs`、`product/verify/tools/m4_*.py`、`product/verify/manifests/`（新增） | A、B 的公开签名 |

**冲突规则**：A 与 B 都不得改 `main.rs`；C 独占。B 独占 `dir` crate。`core` **三路都不得修改**（M1/M2 的门禁基线）。

---

## 1. 退出码（A/B/C 共用一张表）

实测（`u5`/`u5b`/`u5c`/`u5e`）：见 `U5-FINDINGS.md` §1。实现为 `product/cli/src/exit.rs`：

```rust
/// BC exit codes.  Every code here is OBSERVED (U5 probe series) or taken from
/// the help file's "Return codes" table where marked.
pub enum Exit {
    Success = 0,            // O: script ran; report written
    BinarySame = 1,         // O: /qc only
    RulesBasedSame = 2,     // O: /qc, line-ending-only difference
    BinaryDiff = 11,        // O: /qc crc/binary
    Similar = 12,           // O: /qc rules, unimportant-only difference
    RulesBasedDiff = 13,    // O: /qc rules, important difference
    Unknown = 100,          // O: /qc with missing files
    TrialExpired = 104,     // doc; never produced by us
    ScriptNotLoadable = 105,// O: @<missing script file>
    ScriptSyntax = 106,     // O: unknown command / missing arg / bad enum /
                            //    option <bogus> / expand <missing> / criteria <bogus>
    LoadFailed = 107,       // O: load <missing or file>, report inputs missing,
                            //    unclosed quote
}
```

**规则**：`text-report`/`folder-report` 成功写出报告一律 exit 0（无论状态序列）。只有 `/qc` 形态用 1/2/11/12/13。

---

## 2. 脚本 AST（A 产出，B/C 消费）

`product/cli/src/script/parse.rs`：

```rust
/// One script statement.  `line` is the 1-based source line for diagnostics.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    Load { left: String, right: Option<String>, line: usize },
    Criteria { spec: String, line: usize },
    Expand { paths: ExpandPaths, line: usize },
    Filter { masks: String, line: usize },
    Option { name: String, line: usize },
    Log { mode: LogMode, path: Option<String>, append: bool, line: usize },
    TextReport { spec: ReportSpec, line: usize },
    FolderReport { spec: ReportSpec, line: usize },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExpandPaths { All, Named(Vec<String>) }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LogMode { None, Normal, Verbose }

/// Parsed `text-report`/`folder-report` arguments, in any order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReportSpec {
    pub layout: String,             // REQUIRED; unknown name = syntax error 106
    pub options: Vec<String>,       // `options:` comma-separated
    pub title: Option<String>,
    pub output_to: Option<String>,  // printer/clipboard accepted-but-refused (see §5)
    pub output_options: Vec<String>,
    pub comparison: Vec<String>,    // bare args: up to two filenames
}

/// Parse result: commands or a syntax error carrying its line.
pub struct ScriptError { pub line: usize, pub message: String }

pub fn parse_script(text: &str) -> Result<Vec<Command>, ScriptError>;
```

**A 必须实现的语法**（实测）：

| 规则 | 出处 |
|---|---|
| 行尾 `&` 续接下一行；续接后为一条命令 | 官方 `sample_scripts.html` + 本工作区全部脚本 |
| `#` 起首的行是注释；`&` 续接的行同样可含 `#` | 官方样例 |
| `%1`/`%2`/`%3` 在**执行期**替换为 CLI 参数 1/2/3 | `U5-FINDINGS` §2.1 |
| 双引号参数；**引号未闭合 = 107（不是 106）** | u5 实测 |
| 参数名 `lt`≡`left`、`rt`≡`right` | 官方 |
| 未知命令名 = 106；`load`/`criteria`/`expand`/`filter`/`option`/`log`/`text-report`/`folder-report` 之外一律 106 | u5 实测 |
| 注释行为 0 字节？→ 不产生命令 | 需 A 自行验证 |

**A 不做**：不解析 `criteria` 的规格串（交给既有 `reacmp_dir::Criteria::parse`）、不解析 `filter` 掩码、不触碰文件系统。

CLI 参数解析（`args.rs`，A 修改）新增形态：

```
reacmp /silent @<script> [<arg1> [<arg2> [<arg3>]]]
reacmp @<script> [<arg1> ...]                (same, /silent optional)
reacmp /qc[=<size|crc|binary>] <left> <right>
reacmp <left> <right> <output> [--opt=...] [--layout=...]   (existing M1 form)
reacmp --help | --version
```

---

## 3. 执行器（B 产出）

`product/cli/src/script/exec.rs`：

```rust
pub struct ScriptContext {
    pub loaded: Option<(String, Option<String>)>,  // last `load`
    pub criteria: reacmp_dir::Criteria,
    pub filter: Option<String>,
    pub log: Option<LogSink>,
}

/// Run a parsed script.  Returns the exit code (§1) and writes every report.
pub fn run_script(cmds: &[Command], argv: &[String]) -> i32;
```

### 3.1 状态机语义（全部实测）

| 命令 | 行为 |
|---|---|
| `load "<L>" "<R>"` | 两个**目录**。不存在/是文件 → **107**，脚本终止。设置 `loaded`。 |
| `load <default>` | 接受，`loaded = None`，后续报告写空壳（155B/122B 形状）。 |
| `criteria <spec>` | 委托 `reacmp_dir::Criteria::parse`。**解析失败 → 106**（实测 `criteria bogus-token`）。可在 `load` 前后任意位置；**只影响其后**的报告。 |
| `expand all` | 展开整棵树。 |
| `expand "<p>"` | 展开一个相对路径；`A\B`、`A/B`、`A\` 均可；路径不存在 → **106**；指向文件 → 无害（不展开、不报错）。多次 `expand` **累积**。 |
| `filter "<masks>"` | 存入上下文；报告里写入 `<filters>原文</filters>`。**改变报告行集合**。 |
| `option stop-on-error` / `confirm:*` | 接受，无输出影响。**其它值 → 106**。 |
| `log <mode> ["<path>"]` | 写日志；`append:` 前缀表示追加。 |
| `text-report ...` | 有 `comparison` 参数 → 比较那两个文件（core 引擎）；无参数 → 用 `loaded` 的 ltpath/rtpath 写空壳报告。 |
| `folder-report ...` | 报告当前 `loaded` 的文件夹；无 `load` → exit 0 + 155B 空壳（`<ltpath/>` `<rtpath/>`）。 |

### 3.2 报告元素顺序（字节级，u5i 实测）

XML 报告头，**严格此序**：

```
<foldercomp>
    <ltpath>…</ltpath>
    <rtpath>…</rtpath>
    <ignoreunimportant/>     <- 仅当 criteria 含 ignore-unimportant
    <filters>原文</filters>   <- 仅当发过 filter
    …rows…
</foldercomp>
```

文本布局（summary/side-by-side）同样带过滤行（u5i：`过滤：  *.txt`）。

### 3.3 目录 `<size>` 与展开（u5g/u5j 实测，**dir 引擎必须新增能力**）

**规则**：目录行 `<size>` = 该目录**整棵子树全部展开**时的文件字节聚合；否则 `<size/>`（自闭合）。

| 脚本 | `A` 的 size（树 `A/B/f=6`、`A/g=4`） |
|---|---|
| 不 expand | `<size/>` |
| `expand all` | `10` |
| `expand "A"` | `<size/>`（B 未展开） |
| `expand "A\B"` | `10`（整棵 A 已展开） |

**目录行永不携带 `status` 属性**（u5j：展开/未展开一律 `<foldercomp>`，无 `status=`）。
**filter 不影响目录聚合值**（u5g s7：子文件全被过滤，`A=10` 仍在）。

B 需要给 `dir` 增加展开策略输入。建议签名（B 可微调，但**必须**让 C 的调用点可编译）：

```rust
// product/dir/src/expand.rs (new)
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExpandPolicy {
    /// Nothing expanded: every directory row is `<size/>`, no children rows.
    None,
    /// Everything expanded (the M3 behaviour, and `expand all`).
    All,
    /// Only the listed relative paths (and therefore all their ancestors on the
    /// path to each named dir) are expanded.
    Only(Vec<String>),
}

impl ExpandPolicy {
    /// True when this directory's whole subtree is expanded, i.e. the row shows
    /// an aggregate `<size>` (U5g).
    pub fn fully_expanded(&self, relative: &str) -> bool;
}
```

`CompareOptions` 增加 `expand: ExpandPolicy`（默认 `All`，保持 M3 门禁 429/429 不变）。

### 3.4 filter 掩码（B 实现，实测规则）

| 规则 | 实测 |
|---|---|
| 大小写不敏感 | `*.TXT` 命中 `a.txt` |
| `?` 单字符通配 | `d?.bin` 命中 `d1.bin` |
| `;` 分隔多掩码 | 混合包含/排除 |
| `-` 前缀 = 排除 | `-*.txt` 去掉所有 `.txt` |
| 尾随 `\` = 文件夹掩码 | `sub\` 只保留该文件夹；`-A\` **整棵移除** |
| 全不命中 | 文件夹行保留，文件行全删 |

---

## 4. 统一入口（C 产出）

BC 的裸命令行（两文件/两目录/三文件）**实测超时**（会开视图等待），无可对拍行为。
因此 `reacmp` 的统一入口按**本产品语义**定义，并在 `--help` 显式标注这是扩展：

```
reacmp <left> <right> <output> [--opt=] [--layout=]   # M1 form, unchanged
reacmp @<script> [args...]                            # M4: script mode
reacmp /qc[=kind] <left> <right>                      # M4: quick compare
reacmp --help | --version
```

**分派规则**（C 实现）：

1. 任何位置出现 `--help`/`-h`/`/?` → help（既有语义，保留）。
2. 首个非开关参数以 `@` 开头 → 脚本模式。
3. 首个开关是 `/qc` → 快速比较模式。
4. 否则 → 既有 M1 三参数模式。

**`/silent`**：脚本模式接受并忽略（我们本来就是非交互的）。裸 `/silent` 两文件/两目录形态**不实现**（BC 超时，无对拍），`--help` 必须标注。

---

## 5. 明确不实现（C 在 `--help` 与文档中标注）

`load create:all`（实测会创建目录，破坏性）、`copy`/`move`/`delete`/`sync`/`rename`/`touch`/`attrib`、
`snapshot`、`select`、`beep`、`output-to:printer|clipboard`、`output-options:html-*`、
裸命令行两文件/两目录比较、`/qc` 之外的全部开关。

**每个都必须以命名错误的形式拒绝，不得静默忽略、不得产出占位报告。**

---

## 6. 验收（C 负责建，主会话负责跑）

1. **脚本对拍**：新增脚本语料（≥20 例），Oracle 与产品各跑一遍，归一化后比较
   XML 结构 + 状态序列 + `<filters>` 行；文本布局比较归一化文本。
2. **退出码测试**：§1 表中每个 O 级码至少一例（含 `/qc` 五级）。
3. **回归**：既有 101 文本锚点 + 31 布局 + 79 文件夹用例 + cargo/pytest 全绿。
4. **门禁纪律**：Oracle 串行（单实例 + Job Object），绝不与 pytest 并行。

产出：`product/verify/runs/M4-gate-serial-01/REPORT.md`。
