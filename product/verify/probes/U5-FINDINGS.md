# U5 — CLI / 脚本子集（M4）行为实测

> 探测日期：2026-10-14
> 探测脚本：`probes/u5_exit_codes.py`、`u5b_exit_codes_deep.py`、`u5c_script_state.py`、
> `u5d_expand_and_filter.py`、`u5e_criteria_order.py`、`u5f_text_report_root.py`、
> `u5g_dir_size_rules.py`、`u5h_cli_shapes.py`
> Oracle：`D:\BCompare\BCompare\BComp.com` 5.0.3.30240（就地、`/silent`、Job Object 容器）
>
> 证据分级：本文全部为 **O（已观察）**，除显式标注 D 的推论。

---

## 0. 本探测推翻了什么

`harness/oracle.py` 的注释曾记录"`folder-report` 没有 `load` 时退出码 106、报告 0 字节"。
**实测为 exit 0、155 字节有效报告**（`u5b` [1]）。该注释对应的是**早期配方错误时**的现象
（当时脚本形态不同），不是 `folder-report` 本身的性质。产品的退出码表以本文为准。

---

## 1. 退出码（M4.3 的权威表）

### 1.1 脚本错误三类（实测触发条件）

| 退出码 | 官方含义（help 表） | 实测触发条件 |
|---|---|---|
| 0 | Success | 脚本跑完并写出报告（无论文件是否不同） |
| 105 | Error loading script file | `@<path>` 指向**不存在的脚本文件** |
| 106 | Script syntax error | 未知命令名、缺必需参数、非法枚举值、`option <bogus>`、`expand "<不存在的路径>"`、`criteria <bogus-token>` |
| 107 | Script failed to load folders or files | `load` 的路径不存在、`load` 指向**文件**而非文件夹、`text-report` 的比较文件不存在、引号未闭合 |
| 104 | Trial period expired | 复制到别处运行（本工作区纪律：绝不复用） |

关键发现：**106 是"语法/命令层"错误，107 是"输入加载层"错误**。`criteria` 的非法 token 属于
106（不是 107），因为它不涉及路径。`expand "nope"` 也是 106。

### 1.2 `/qc` quick-compare 的 DOS error level（实测五级全部观察）

| 退出码 | 官方含义 | 实测输入 |
|---|---|---|
| 1 | Binary same | 字节完全相同（任何 `/qc` 变体） |
| 2 | Rules-based same | 仅**行尾差异**（`\n` vs `\r\n`） |
| 11 | Binary differences | 任意字节不同（crc / binary 模式） |
| 12 | Similar | `/qc`（rules）下**仅空白差异**或**仅大小写差异** |
| 13 | Rules-based differences | `/qc`（rules）下**注释内容不同**、真实内容差异 |
| 100 | Unknown error | `/qc` 的两个路径不存在 |

`/qc=crc` 与 `/qc=binary` **不区分** 2/12/13 —— 它们的非相同结果一律是 11。

### 1.3 裸命令行形态（M4.1）

| 形态 | 行为 |
|---|---|
| `/silent` 两文件 | **超时**（会开交互视图并等待） |
| `/silent` 两目录 | **超时** |
| `/silent` 三文件 | **超时** |
| `/silent` 无参数 | **exit 102**（"unable to wait" 类，实测值） |

含义：**BC 的裸命令行不是一个可自动化的比较入口**；M4 的验收通道是**脚本**（`@script` +
`text-report`/`folder-report`），与 M0 已经验证的配方一致。`reacmp` 的"两文件三参数"快捷形态
是**本产品的扩展**，不计入与 BC 的对拍（BC 无对应行为可对拍），文档必须显式标注。

---

## 2. 脚本语言（M4.2）

### 2.1 词法

| 特性 | 实测 |
|---|---|
| 续行 | 行尾 `&` 表示下一行续接（官方文档 + 我们的脚本均验证） |
| 注释 | `#` 起首为注释（官方 `sample_scripts.html` 全部使用） |
| 参数替换 | `%1` / `%2` / `%3` = 命令行第 1/2/3 个参数；`%date%` 等变量由脚本展开 |
| 引号 | 双引号包裹含空格参数；**未闭合引号 → exit 107**（不是 106） |
| `lt`/`rt` 别名 | 官方：任何命令中 `lt`= `left`、`rt`= `right` |

### 2.2 命令集（M4 范围内的实测行为）

| 命令 | 实测语义 |
|---|---|
| `load "<L>" "<R>"` | 加载两个**文件夹**；路径不存在或指向文件 → 107 |
| `load create:all "<L>" "<R>"` | **会创建**缺失的目录（实测 `new-L`/`new-R` 被创建）——**破坏性**，M4 不实现（见 §5） |
| `load <default>` | 接受；报告形状与空 `load` 相同（`<ltpath/>` `<rtpath/>`） |
| `expand all` | 递归展开整棵树 |
| `expand "<path>"` | 展开单个相对路径；`A\B` 与 `A/B` **都接受**；尾随 `\` 也可（`expand "A\"`）；指向文件不报错也不展开；路径不存在 → 106 |
| `expand` 累积 | `expand "A"` 然后 `expand "A\B"` = 两者都展开 |
| `filter "<masks>"` | **改变报告的行集合**（不只是视图），并在报告写入 `<filters>原文</filters>` |
| `criteria <spec>` | 与文件夹侧 M3/U4 完全一致；**`load` 之后发也可以**（实测 crit-after-load 与 crit-before-load 同结果）；但**报告命令之后发的 criteria 不影响已写的报告**（crit-after-report 第二次报告仍是默认判据） |
| `option stop-on-error` / `confirm:yes-to-all` / `confirm:no-to-all` | 接受，无输出影响 |
| `option <bogus>` | 106 |
| `log [none\|normal\|verbose] ["<path>"]` | 写出日志文件；实测含命令回显 + 中文提示 + 耗时行；编码为 UTF-8；默认 `Log.txt` |
| `text-report layout:<l> output-to:"<path>" ["<L>" "<R>"]` | 有 `%1 %2` 参数时比较这两个文件；**无参数且此前 `load` 的是文件夹 → 写出空报告（只有 ltpath/rtpath），exit 0** |
| `folder-report layout:<l> output-to:"<path>"` | 报告**当前已加载的**文件夹；无 `load` 时 exit 0 + 155B 空报告（不会 106） |

### 2.3 报告命令的收尾必须分两类（u5f 实测）

| 场景 | 报告形状 | exit |
|---|---|---|
| `text-report ... "%1" "%2"` | `<bcreport><ltpath/><rtpath/><filecomparison>...` | 0 |
| `text-report ...`（无参数，无 load） | `<bcreport><ltpath/><rtpath/></bcreport>`（122B） | 0 |
| `text-report ...`（无参数，已 `load <folders>`） | `<bcreport><ltpath>L</ltpath><rtpath>R</rtpath></bcreport>`（272B） | 0 |
| `text-report ...`（无参数，已 `load <files>`） | — | **107**（load 文件本身就不允许） |
| `folder-report ...`（无 load） | `<bcreport><foldercomp><ltpath/><rtpath/></foldercomp></bcreport>`（155B） | 0 |
| `folder-report ...`（已 load） | 正常文件夹报告 | 0 |

---

## 3. `filter` 语义（u5c/u5d/u5g/u5h）

| 规则 | 实测 |
|---|---|
| 作用范围 | **报告行集合**（文件行被剔除），文件夹行按规则保留或移除 |
| `<filters>` 元素 | 只要发过 `filter`，报告里写入**原文**（含 `-` 与尾随 `\`），位置在 `<rtpath>` 之后 |
| 大小写 | **不敏感**：`filter "*.TXT"` 命中 `a.txt` 与 `c.TXT` |
| `?` 通配 | 支持：`filter "d?.bin"` 命中 `d1.bin` |
| 分号列表 | 支持，可混合包含与排除：`"*.txt;*.TXT;-b.log"` |
| 排除掩码 | 前缀 `-`；`-*.txt` 去掉所有 `.txt` |
| 文件夹掩码 | 尾随 `\`（XML 里显示为 `sub\\`）；`filter "sub\"` **只保留**该文件夹及其内容 |
| 排除文件夹 | `filter "-A\"` **整棵移除** `A`（含子目录），即使 `expand all` 也不展开它（与官方文档一致） |
| 通配全不命中 | 文件夹行**仍在**且带聚合 size（`A=10`），文件行全被剔除（u5g s7） |
| 与 `expand` 顺序无关 | `filter` 在 `expand` 前或后，结果相同（s7/s8） |

**注意**：文件夹行的 `<size>` 聚合**忽略 filter**（子文件被过滤掉后目录仍显示全量聚合值）——
这是 B 路必须以字节级复现的行为。

---

## 4. `expand` 与目录 `<size>` 形状（u5g 实测，纠正了 dir 引擎的现有假设）

| 场景 | 目录行 `<size>` |
|---|---|
| 未展开（或整棵子树未全展开） | `<size/>`（自闭合） |
| **该目录的整棵子树都已展开** | 聚合数字（该目录下全部文件字节之和，按侧分别计算） |

实测证据（树：`A/B/f.txt(6)`、`A/g.txt(4)`、`C/i.txt(3)`、`h.txt(5)`）：

| 脚本 | 观察 |
|---|---|
| 不 expand | `A=<size/>`, `C=<size/>` |
| `expand all` | `A=10`, `B=6`, `C=3` |
| `expand "A"` | `A=<size/>`, `B=<size/>`，但 `g.txt` 出现（**部分展开 → 目录仍空 size**） |
| `expand "A\B"` | `A=10`, `B=6`（**整棵 A 被展开 → A 聚合**） |
| `expand "A"` + `expand "C"` | `A=<size/>`（B 未展开）, `C=3` |
| `expand all` + `filter "*.nomatch"` | `A=10`, `B=6`, `C=3`，无文件行 |

**规则（O）**：目录 `<size>` = 该目录子树**全部展开**时的文件字节聚合；否则 `<size/>`。
`filter` 只影响行集合，不影响聚合值。

> 现有 `dir` 引擎**总是递归**并总是渲染聚合 size，这在"未 expand"的脚本报告里会产生
> **字节级差异**。B 路必须给 `compare_folders` 增加"展开集合"输入（见接口冻结文档 §3）。

---

## 5. 明确不实现（文档必须标注）

| 能力 | 理由 |
|---|---|
| `load create:all` | **会创建目录**（实测）。M4 是只读工具；实现它等于引入破坏性行为，须独立安全评审（与 MVP 排除"文件复制/同步"同理） |
| `copy`/`copyto`/`move`/`moveto`/`delete`/`rename`/`sync`/`touch`/`attrib` | 破坏性，MVP 明确排除 |
| `snapshot` | 需要 `.bcss` 格式（未探测） |
| `select` | M4 的报告命令不使用选择（`folder-report` 报告全部已加载项）；无验收手段前不实现 |
| `beep` | 无输出意义 |
| `printer`/`clipboard` 输出目标 | 需要 GUI/OS 会话；`output-to:` 只实现文件路径 |
| `output-options: html-*` | HTML 输出未对拍 |
| `/qc` | 实测需直接进程调用（非脚本），且它的比较语义与报告路径不同；M4 范围外（列为已知差异） |
| 裸命令行两文件/两目录比较 | BC 实测**超时**（开视图等待），无可对拍行为 |

---

## 6. 与工作区既有记录的差异（须修正）

1. `harness/oracle.py` 的 `EXIT_MEANINGS` 注释（105 "script error" / 106 "script command error"
   / 107 "file not found"）是**约略描述**；官方表与实测一致的是：
   105 脚本文件读取失败、106 语法错误、107 输入加载失败。文档已按实测更新。
2. "`folder-report` 无 `load` → 106" 已被 u5b 推翻（实为 exit 0 + 155B）。
3. `dir` 引擎"总是递归 + 总是显示聚合 size"在脚本报告里需要区分"展开状态"（§4）。

---

## 附录 U6 —— `/qc` 对「单侧不重要行」的判定（M4 门禁暴露后补测）

M4 门禁（serial-01 首轮）暴露产品 `/qc` 把「仅尾部空白」判成 13，而 Oracle 是 12。
根因是判定过严：产品用"字面 `same`"，而 Oracle 用"**全部差异都不重要**"。
但 `similar` 之外还有三种状态可能出现在不重要一侧，边界必须实测而不是推断，
因此补测 `probes/u6_qc_orphans.py`（12 个单元格，含 4 个自校验对照）：

| 输入 | 报告状态序列（Oracle） | `/qc` |
|---|---|---|
| 完全相同 | `same` | **1** |
| 仅尾部空白 | `similar` | **12** |
| 单侧注释行（左/右） | `leftsimilar`/`rightsimilar` + `same` | **12** |
| 单侧空行 | `same`,`leftsimilar`,`same` | **12** |
| **单侧代码行** | `leftorphan`/`rightorphan` + `same` | **13** |
| 行内内容变更 | `different` | **13** |
| 注释文本变更 | `similar`（报告路径）但 `/qc` | **13** |
| 不重要 + 重要混合 | `leftsimilar`,`same`,`rightorphan` | **13** |

**模型（O）**：`/qc` = 12 **当且仅当每个分组都是**
`same` / `similar` / `leftsimilar` / `rightsimilar`；出现 `different` 或 `leftorphan`/`rightorphan`
即为 13。实现为 `Comparison::differences_are_all_unimportant()`（`core/src/compare.rs`），
由 8 个实测单元格的单测锁定。

**注意两处陷阱**：
1. `is_all_same()`（只认字面 `same`）**过严** —— 会把"仅尾部空白"判成 13。
2. 单侧行的判定**取决于语法**：`// note` 在 `.c` 下是注释（不重要，12），
   在 `.txt` 下是正文（`leftorphan`，13）。同一段字节因**扩展名**不同而退出码不同，
   所以 `m4_gate.py` 的 `qc-indent` 等用例必须带正确扩展名。

**另一处语料错误（门禁纠正）**：`qc-rules-indent-only` 初稿期望 12（"空白都不重要"的推广），
实测 `/qc` = **13** —— Python 前导缩进是**重要**元素（`07-m2-importance.md`）。
探针是权威，期望已改为 13。

## 附录 U6b —— 归一化器状态 token 的普查修正

`harness/normalize.py` 的两张状态集合里含**从未被观察到的猜测成员**。对全部归档报告
（M0…M4 的 `runs/**/*.out|*.xml`）做普查后修正：

| 集合 | 实测 token 与计数 |
|---|---|
| `filecomp/@status` | `diff` 687、`ltnewer` 61、`ltonly` 1213、`rtnewer` 396、`rtonly` 561、`same` 3067 |
| `linecomp/@status` | `different` 1720、`leftorphan` 307、`leftsimilar` 178、`rightorphan` 264、`rightsimilar` 22、`same` 3143、`similar` 893 |

删除了此前列出的 `leftnewer`/`rightnewer`/`leftolder`/`rightolder`/`orphan`/`conflict`/
`leftorphanimportant`/`rightorphanimportant` —— 它们**一次都没出现过**，真实拼写是 `lt`/`rt`
（与 `ltonly`/`rtonly` 一致）。保留猜测项会让归一化器"接受从未见过的东西"，
而 M4 门禁正是在一个真实报告的 `rtnewer` 上被拒，才暴露了这一点。

## 附录 U7 —— `<errorN>` 的侧别编号（M4 之后发现的真实产品 bug）

对 `enc-latin1`（左文件有非法 UTF-8 字节）只观察到**一个**元素，产品据此把两侧都写成
`<error1>`。`probes/u7_encoding_error_elements.py` 实测三种状态后确认这是错的：

| 输入 | Oracle 元素 | 产品（修复前） |
|---|---|---|
| 仅左侧非法 | `<error1>` | `<error1>` ✓ |
| **仅右侧非法** | **`<error2>`** | `<error1>` ✗ |
| 两侧都非法 | `<error1>` 然后 `<error2>` | 两个 `<error1>` ✗ |
| 非法字节在第 2 行 | `<error1>…(Line 2)</error1>` | 行号正确 ✓ |

**结论（O）**：`errorN` 的 **N 是侧别编号**，与 `filename1`/`filename2` 同构；
`error1` = 左文件，`error2` = 右文件；两者同时出现时左侧在前。行号是 DATA（会随规范化保留）。

修复：`core/src/xml.rs` 的 `error_element(side, line)` 现在按侧取标签名，
调用点分别传 `Side::Left`/`Side::Right`；单测锁定四种组合（含"仅右侧必须不写 error1"）。
**这是 M1 遗留的推断错误**，M1 门禁没抓到的原因是：候选锚点只比 status 序列，
结构差异不参与判定；`enc-latin1` 又恰好只覆盖左侧。

**实测可用的对照**：中文安装写 `文件编码错误 (第 N 行)`，英文写 `File Encoding Error (Line N)`；
`harness/normalize.py` 已覆盖这组标签对且**保留行号**（`xml:label-pair:error1-line-number-preserved`），
所以该元素在 harness 下是可对拍的。语义上值得记录：**两侧都非法时 Oracle 判 `same`**
（u7 `both-invalid`：`caf\xe9` vs `caf\xe8` 都被替换成同一个 U+FFFD，因此匹配）——
这正是"有损解码会把不同字节看成相同"的坑，但它与 BC 的行为一致，不是分歧。

**新锚点**：`m4_gate.py` 的 `enc-left-invalid` / `enc-right-invalid` / `enc-both-invalid` /
`enc-second-line`（4 例，全部与 Oracle 归一化后逐字节一致）。
