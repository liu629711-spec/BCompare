---
name: reacompare-m4-state
description: M4 CLI/脚本子集完成状态 — 退出码表、脚本语义、/qc 判定模型、门禁结果与已知差异、并行派发的教训
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

M4（CLI 与脚本子集）于 2026-10-14 完成，**M0–M4 全部达成，MVP 完成**。
门禁 `product/verify/runs/M4-gate-serial-01`：53 用例 = 51 pass / 0 fail / 2 known_difference。
验收文档 `product/docs/10-m4-acceptance.md`，接口冻结 `product/docs/09-m4-interfaces.md`。

**代码落点**（`product/cli/`，一个二进制 `reacmp` 三种形态分派）：
`script/ast.rs`（冻结）· `script/lex.rs` · `script/parse.rs` · `script/exec.rs` ·
`exit.rs`（退出码表）· `args.rs`（三形态）· `main.rs`（入口 + `/qc` 判定）；
外加 `product/dir/src/expand.rs`（展开策略）与 `filter.rs`（掩码引擎）。

**退出码表（实测，不是文档抄录）**：0 成功 · 1/2/11/12/13 `/qc` 六级 · 100 `/qc` 输入不可读 ·
105 `@script` 文件读不到 · 106 语法/命令错（未知命令、缺必需参数、非法枚举、`option bogus`、
`expand` 不存在路径、`criteria bogus`）· 107 输入加载失败（`load` 不存在/是文件、报告文件不存在、
**未闭合引号**）。完整表与触发条件见 `verify/probes/U5-FINDINGS.md` §1。

**`/qc` 判定模型（U6 实测，易错）**：12 **当且仅当**每个分组都是
`same`/`similar`/`leftsimilar`/`rightsimilar`；出现 `different` 或 `leftorphan`/`rightorphan` 即 13。
`is_all_same()` 太严（会把"仅尾部空白"判成 13）；单侧行的判定**取决于扩展名/语法**
（`// note` 在 `.c` 是不重要的注释=12，在 `.txt` 是正文=13）。
实现为 `Comparison::differences_are_all_unimportant()`（`core/src/compare.rs`）。

**脚本语义要点**：`&` 续行在引号内同样生效（官方规则是行级的）；`#` 起首为注释；
`criteria` 整段尾巴原样交给 `dir::Criteria::parse`（不二次分词）；
`filter` 改变报告**行集合**、写入 `<filters>` 原文，且**不影响目录聚合 `<size>`**；
目录 `<size>` 仅当**整棵子树都展开**才显示聚合，否则自闭合 `<size/>`（`expand "A"` 时 A 仍是 `<size/>`）；
XML 元素顺序 `<ltpath>`→`<rtpath>`→`<ignoreunimportant/>`→`<filters>`；
criteria 只影响其**之后**的报告（`load` 之后发也生效）。

**U7 发现的真实 bug（已修）**：`<errorN>` 的 N 是**侧别编号**（`error1`=左、`error2`=右，
与 `filename1`/`filename2` 同构，两者同时出现时左在前）。产品原先两侧都写 `error1` ——
因为只观察到过左侧非法的锚点 `enc-latin1`，就外推了。M1 门禁没抓到的原因：候选锚点只比
status 序列，不比结构。修在 `core/src/xml.rs::error_element(side, line)`，
新增 4 个对拍用例（`enc-left/right/both-invalid`、`enc-second-line`）。
另记：**两侧都非法时 Oracle 判 `same`**（不同字节都被替换成 U+FFFD），与 BC 一致，非分歧。

**已知差异（2，记录不隐藏）**：`folder-summary-expand-all`、`folder-side-by-side-expand-all`
—— 文件夹**文本布局**本就不字节兼容（渲染器自己写明；M3 验收只用 XML）。这两个用例保留在语料里，
单独计入 `known_difference`，删除会掩盖缺口。修需把文件夹文本布局做到字节级。

**归一化器修正（U6b 普查）**：`normalize.py` 曾含 8 个**从未观察到**的猜测 token
（`leftnewer`/`rightnewer`/`leftolder`/`rightolder`/`orphan`/`conflict`/`*orphanimportant`）。
对全部归档报告普查后：`filecomp` 真实 token 是 `same`/`diff`/`ltonly`/`rtonly`/`ltnewer`/`rtnewer`；
`linecomp` 是 `same`/`similar`/`different`/`leftorphan`/`rightorphan`/`leftsimilar`/`rightsimilar`。
猜测项已删 —— 保留它们会让归一化器"接受从未见过的东西"。

**`--help` 的诚实清单**（不接受静默忽略）：裸两文件/两目录命令行（**实测 BC 会开视图挂起**，
退出码不可得，故无可对拍）、`load create:all`（**实测会创建目录**，破坏性）、
copy/move/delete/sync/rename/touch/attrib、select/snapshot/beep/compare、
printer/clipboard 与 html 输出选项、会话/压缩包/远程、stdin `-`。

**并行派发的教训**：三路子代理中，**A 路（词法/解析）未交付且终报被截断**，
`lex.rs`/`parse.rs` 仍是 stub —— 子代理的"完成"不能只看它的终报，必须核验磁盘 mtime 与测试。
B 路（执行器）与 C 路的部分交付（normalize 修复）可用。补救：主会话自己接管关键路径
（`args.rs`/`main.rs`/`/qc`），把未交付的解析器拆出重派，门禁语料与 runner 主会话自建。
派发子代理时把**完整内联规格**写进 prompt（含实测数据与陷阱）比指向文件更可靠。

**M4 之后选定的方向 A（编码/代码页）**：四轮探测（u8/u8b/u8c/u8d）**推翻了“BC 偏好 GBK”的前提**
——BC 不自动探测 legacy 编码，只认 XML 声明码页与无 BOM UTF-16 的 NUL 启发式。完整实测结论见
[[reacompare-encoding-codepage]]。

相关：[[reacompare-m2-state]] · [[reacompare-folder-criteria]] · [[reacompare-a1-harness-state]]
· [[reacompare-encoding-codepage]]
