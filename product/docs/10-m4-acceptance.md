# 10 — M4 验收（CLI 与脚本子集）

> 完成日期：2026-10-14
> 门禁运行：`product/verify/runs/M4-gate-serial-01`（53 用例：51 pass / 0 fail / 2 known_difference）
> 前置：`09-m4-interfaces.md`（接口冻结）、`probes/U5-FINDINGS.md`（13 轮 + U6 两轮实测）

---

## 1. M4 验收标准与判定

`04-milestones.md` M4 的验收：**给定脚本，本工具与 BC 产出同布局的等价报告**。

| 任务 | 交付 | 验收方式 | 结果 |
|---|---|---|---|
| M4.1 CLI 参数解析 | 三种形态（三路径 / `@script` / `/qc`） | 门禁 15 个 `/qc` 用例 + `args.rs` 单测 | **达标** |
| M4.2 脚本解释器 | `load`/`criteria`/`expand`/`filter`/`text-report`/`folder-report`/`log`/`option` | 门禁 36 个脚本用例，退出码 + 归一化报告逐字节 | **达标** |
| M4.3 退出码语义 | 0/1/2/11/12/13/100/105/106/107 | 门禁覆盖 106×5、107×3、`/qc` 六级 | **达标** |
| M4.4 `/silent` | 接受并忽略（本工具从不交互、从不开窗） | 门禁全部脚本用例经 `/silent` 调用 | **达标** |

**判定：M4 完成。** 51/53 用例的退出码与归一化报告与 Oracle 完全一致，0 个失败。
2 个已知差异是**非 XML 的文件夹文本布局**（§4），XML 路径 100% 一致。

---

## 2. 术语位置（实现落在哪）

| 组件 | 文件 | 说明 |
|---|---|---|
| 脚本 AST | `product/cli/src/script/ast.rs` | 冻结接口（先冻结再并行） |
| 词法（续行/注释/引号） | `product/cli/src/script/lex.rs` | `&` 续行、`#` 注释、**未闭合引号 = 107** |
| 命令解析 | `product/cli/src/script/parse.rs` | 9 个命令；不实现者**具名拒绝** 106 |
| 执行器 | `product/cli/src/script/exec.rs` | 状态机 + 报告生成 |
| 退出码表 | `product/cli/src/exit.rs` | 每个码标注 O（已观察）/ 文档 |
| 参数解析 | `product/cli/src/args.rs` | 三形态分派 + `--help` 诚实清单 |
| 入口 | `product/cli/src/main.rs` | `/qc` 的规则判定 |
| 展开策略 | `product/dir/src/expand.rs` | `None`/`All`/`Only`，决定 `<size>` 形状 |
| 掩码引擎 | `product/dir/src/filter.rs` | 大小写不敏感、`?`、`;`、`-`、尾随 `\` |
| 门禁 | `product/verify/tools/m4_gate.py` | 53 用例，逐条带实测来源 |

---

## 3. 与 Oracle 的等价性（实测支撑）

| 维度 | 证据 |
|---|---|
| XML 报告逐字节 | 归一化后 `oracle == product`，覆盖 text 6 布局、folder 3 布局中的 XML、壳报告、filter、criteria |
| 退出码 | 106/107/105 三类错误的触发条件全部实测（见 `U5-FINDINGS.md` §1.1） |
| `<size>` 形状 | 目录整棵子树展开才算聚合，否则 `<size/>`（u5g 六种展开形态） |
| 元素顺序 | `<ltpath>`→`<rtpath>`→`<ignoreunimportant/>`→`<filters>`（u5i 五例交叉验证） |
| `filter` 语义 | 改变报告行集合而非仅视图；目录聚合值**不受 filter 影响**（u5g s7） |
| criteria 时序 | `load` 之后改 criteria 生效；**报告之后改不影响已写报告**（u5e） |
| `/qc` 六级 | u5b/u5k/u6 共 26 个单元格 |

---

## 4. 已知差异与未支持项（显式记录，不隐藏）

### 4.1 已知差异（2）

| 用例 | 差异 | 原因 |
|---|---|---|
| `folder-summary-expand-all` | 首行 `文件夹比较(F)` vs `Folder Compare Summary` | 文件夹**文本布局**本就不字节兼容；渲染器在自己的输出里写明，M3 验收只用 XML |
| `folder-side-by-side-expand-all` | 同上 | 同上 |

这两个用例**保留在语料中**并单独计入 `known_difference`——既不算 pass 也不算 fail，
删除它们会掩盖缺口。修正它们需要把文件夹文本布局做到字节级，属独立工作。

### 4.2 未支持（`--help` 中具名拒绝）

GUI/交互视图；裸两文件/两目录/三文件命令行（**实测 BC 会开视图并挂起，退出码不可得**，
故无可对拍行为）；三方合并；表格/十六进制/图片/媒体/注册表/版本/按类型报告；
文件操作（`copy`/`copyto`/`move`/`moveto`/`delete`/`rename`/`sync`/`touch`/`attrib`）；
`load create:all`（**实测会创建目录**，破坏性，须独立安全评审）；`select`/`snapshot`/`beep`/`compare`；
printer/clipboard 输出；HTML 输出选项；会话持久化/压缩包/远程；标准输入 `-`。

### 4.3 与既有记录的修正

1. `harness/oracle.py` 曾记「`folder-report` 无 `load` → 106」，**实测 exit 0 + 155B 有效报告**（u5b）。
2. `normalize.py` 的状态集合含 8 个**从未观察到**的猜测 token，真实拼写是 `ltnewer`/`rtnewer`（U6b 普查）。
3. `dir` 引擎原先**总是递归**且总显示聚合 `<size>`；M4 增加展开策略后，
   `expand "A"` 这种部分展开的目录现在正确显示 `<size/>`（u5g）。
4. 文件夹文本布局的标签（`过滤：` 行）与 Oracle 逐字节一致，但整体排版不一致（§4.1）。

---

## 5. 回归（M4 未破坏既有基线）

| 门禁 | 结果 |
|---|---|
| `cargo test` core / vfs / dir / cli | **177 / 35 / 133 / 410** 全绿 |
| M1+M2 锚点 + 文件夹 | **203/203** |
| 文本布局 | **31/31** |
| 文件夹夹具自检 | **79/79** |
| 文件夹 Oracle 逐字节 | PASS |
| `pytest` | **157 passed** |
| `offline_check` | 锚点 101/101、XML 101/101、布局 30/31（既有 `mixed-side-by-side`） |

---

## 6. MVP 完成度

`04-milestones.md` §7 的七条判定：

1. `cargo test` 有真实测试且全绿 —— **是**（755 个测试）。
2. 文本锚点 ≥80 且 status 对拍 100% —— **是**（101 锚点，101/101；已知差异显式列出）。
3. 文本布局 ≥29/30 字节级一致 —— **是**（30/31，1 个既有已知差异）。
4. 文件夹夹具 ≥40 且 XML 对拍一致 —— **是**（79 例；另有逐字节 PASS）。
5. CLI 脚本子集可跑通且与 BC 等价 —— **是**（51/53 + 2 已知差异）。
6. 未支持功能在 `--help` 与文档中显式标注 —— **是**。
7. 无假功能（无硬编码/占位返回）—— **是**；所有未实现路径**具名拒绝**，不产占位报告。

**M0–M4 全部完成，MVP 达成。**

---

## 7. 后续里程碑 U8（编码/码页）已完成

M4 之后按"规格就绪度"推进的第一项是编码/码页。开工前提是"BC 偏好 GBK"，
**实测推翻了它**：BC 不自动探测任何传统编码，无声明时按 UTF-8 有损解码（产品本来就一致）。
真正需要实现的是两个机制，现均已完成：

| 机制 | 内容 | 证据 |
|---|---|---|
| XML 声明码页 | `<?xml … encoding="NAME"?>` 选择码页解码整个文件 | `probes/u8b`…`u8g` |
| 无 BOM UTF-16 | NUL 奇偶启发式（`len>=4` 且偶数，阈值 0.6/0.02） | `probes/u8`、`u8b` |

关键实测事实（详见 `probes/U8-FINDINGS.md`）：数字名 `cp936`/`936` **不解析**而 `GBK` 可以；
`US-ASCII`/`iso-ir-6` 族落 **cp1252**；Unicode 族被拒绝；解码用**宽松**转换、上报用**严格**校验，
两者可同时发生；BC 的解码与 `MultiByteToWideChar` 在 **23/23** 页逐字节一致。

**U8 验收**：

| 门禁 | 结果 |
|---|---|
| `tools/u8_verify.py`（新建护栏，44 例） | **44/44** + 1 已知差异（`tail-tiebreak-1v2`） |
| `cargo test` core | **186**（新增 9 个 codepage 测试） |
| 锚点 / 布局 / 文件夹 / pytest / offline_check / m4_gate | 101/101 · 31/31 · 1/1 · 157 · 101/101+101/101+30/31 · 55/57（2 既有 KD） |

`tail-tiebreak-1v2` 已归因：`probes/u8h` 在**纯文本、无码页**下复现了同一平局
（8 形态 6 一致），故与编码层无关，属既有对齐平局，记入 `07-m2-importance.md` 的 M2.6 条目。

**2026-10-14 收尾**：M2.6 对齐修复（锚定层 `AnchorKey` + 块内 closeness 配对，
见 `07-m2-importance.md` 已知差异 1）使 `tail-tiebreak-1v2` 与 BC 逐字节一致。
U8 护栏重跑 **45/45 全过、0 已知差异**
（`runs/u8-verify-20261014T153156Z/`），该用例已从 `KNOWN_DIFFERENCES`
移入 `CASES` 作为回归护栏（原归因记录保留在脚本注释与本文档中）。


---

## 8. 五 criteria 收尾 U9/U10 已完成

`08-folder-criteria.md` §已知差异 1 与 4 两项未收尾工作已实测完成。

### U9 —— `version` 的扩展名门控（**发现并修复真实缺陷**）

文档怀疑"BC 只对 `.exe`/`.dll` 等生效"——**实测属实**。BC 只对这 8 个扩展名读版本资源：
`.exe` `.dll` `.ocx` `.scr` `.sys` `.drv` `.vxd` `.386`；其余一律 `same`，
**即使文件是真的 PE**（`.cpl` 是真 PE 被忽略、`.txt` 携带真 PE 字节被忽略）。
`.vxd`/`.386` 是反直觉成员（老式驱动格式），而 `.cpl`/`.efi`/`.ax` 等虽像可执行却被排除。

修复前 24 个扩展名中 **16 个与 BC 不一致**。修正在 `vfs/src/pe.rs::version_applies_to`，
并同步了参考模型（`dir/tools/make_cases.py`）与夹具（`versioned` 树新增 `masked.*`/`included.*` 行）。

### U10 —— 文件夹 `ignore-unimportant` 的范围

10 个 `iu-*` 用例逐字节通过，实测规则：目录行**从不携带 status**（结构行不受影响）；
单侧文件行**仍报 `ltonly`/`rtonly`**（无法折叠）；修饰符**独立出现 ≡ 什么都不比较**，
加 `rules-based` 才折叠，**token 顺序无关**。产品**本来就正确**，本轮只补护栏。

### 验收

| 门禁 | 结果 |
|---|---|
| `tools/u9_folder_gate.py`（新建，18 例 U9+U10） | **18/18 逐字节一致** |
| `dir/tools/compare_fixtures.py` | **79/79**（observed 25/25、predicted 54/54） |
| `cargo test` core / vfs / dir / cli | 186 / **39**（+4 掩码测试）/ 133 / 410 |
| 锚点 / 布局 / 文件夹 Oracle / offline_check | 101/101 · 31/31 · PASS · 101/101+101/101+30/31 |
| `u8_verify` / `m4_gate` / `pytest` | 44/44+1KD · 55/57（2 既有 KD）· 157 |

### 一个探针陷阱（记下来避免重犯）

**`criteria` 必须写在 `load` 之前**才能对该报告生效。我首轮把顺序写反，导致 BC 对
全部 24 个扩展名（含 `.exe`/`.dll`）都返回 `same`，看起来像"BC 完全不比较版本"——
与既有 `serial-07` 门禁中 `left_higher.dll` 真报 `ltnewer` 的事实矛盾。
**结论与既有证据矛盾时先怀疑探针**；若照首轮结果行动，会把本来正确的 `.dll` 行为改坏。
