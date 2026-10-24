# 07 — M2 重要性引擎：实现与验收（2026-10-14）

M2 把 `product/core/src/importance.rs` 从 M1 的行级近似换成了真正的逐元素引擎。
本文记录实现、证据链、验收结果与已知差异。前置阅读：`04-milestones.md` M2 节、
`probes/U1-FINDINGS.md`、`probes/U2-FINDINGS.md`（U1/U2/U2b/U3 四轮探测的 O 级行为表）。

## 实现范围（对应里程碑）

| 子任务 | 状态 | 内容 |
|---|---|---|
| M2.1 U1 定案 | ✅（上一会话） | 逐元素重要性 O 级行为表 |
| M2.2 分词器 | ✅ | 4 格式（PlainText/Cpp/Python/JavaScript）真分词器 + 跨行状态；25 格式 mask 表（`FORMAT_SPECS`）可加载 |
| M2.3 逐元素重要性 | ✅ | 重要元素逐字拼接比较；注释/空白不重要；Python Indent 重要 |
| M2.4 ignore-unimportant | ✅ | similar/leftsimilar/rightsimilar → same 折叠 + 借用 id 渲染 |
| M2.5 锚点 ≥80 | ✅ | **101 个锚点**（45 M1 + 56 M2），新锚点 100% 绿 |

## 代码落点

- `core/src/importance.rs` — 重写：`Grammar{PlainText,Cpp,Python,JavaScript}`（未知扩展名
  → PlainText，U2 foo-* 定案，替换 M1 的“未知=语法”假设）、`scan_line`（带 `Cont`
  跨行状态：块注释 / Python 三引号 / C++ `@""`）、`FORMAT_SPECS`（25 格式 mask，
  事实性文件关联）、`Plan`（每行 key + 重要拼接，一次性分词）。
- `core/src/align.rs` — `Status` 新增 `LeftSimilar`/`RightSimilar`；`Group.folded`
  标记；`pair_block` 双策略（位置配对 / 锚定配对，见 U2-FINDINGS §3）；`Plan` 驱动。
- `core/src/xml.rs` — 折叠行渲染：左借用 rtid（有内容）/ 右借用 ltid（自闭合无内容）。
- `core/src/layouts.rs` — summary 计数顺序（U3b 定案）与新计数行。
- `verify/harness/normalize.py` — `leftsimilar`/`rightsimilar` 入已知状态表；
  两个新 summary 计数标签（zh→en）。
- `verify/harness/manifests.py` — `LayoutCase.ext`（M2 的 .c 布局用例）。
- 新锚点由 `verify/tools/m2_add_golden_anchors.py` 生成（fixture + Oracle 报告 +
  manifest 追加，原条目不动，旧 manifest 快照存 runs/m2-anchors-*/）。

## 设计取舍：不复制 BC 的语法表

verdict/对齐只取决于（a）元素是否注释/空白、（b）重要元素的逐字文本（U1：
keyword/identifier/number/operator/directive 全部重要且按文本比较）。因此
**关键词表内容不影响可观察行为**——4 个格式的词法分类用公开语言知识实现
（ISO C++、Python、ECMA-262 关键词/运算符），BC 的内部格式表（`extracted/
bcfileformats-spec.json`）只作为元素类型与结构的参照，不逐字嵌入产品。这满足
“BCompare 只作行为参考，不复制其资源”的项目红线。

## 验收（全部串行）

| 关卡 | 结果 |
|---|---|
| `cargo test`（core 170 + large_input 5 + doctest 1 + cli 20） | **196 全绿** |
| `pytest tests`（157 项，含 live Oracle 101 锚点自对拍） | **157 全绿** |
| `offline_check.py`（无 Oracle） | 锚点 **101/101** 状态序列 + XML 归一化全同；布局 30/31 |
| 官方 harness `M2-gate-serial-01`（双安装 + 产品，串行） | **429 = 428 过 + 1 已知失败 + 0 错误**；anchor/candidate **101/101**，layout/candidate 30/31 |
| 残留进程检查 | 无 BComp/BCompare 残留 |

唯一失败 `mixed-side-by-side` 是 A-2 验收记录在案的候选已知差异（side-by-side
输出列对齐细节），与 M2 无关，未特例处理。

## 已知差异 / 后续工作

1. **多不重要行的 Myers 平局 —— 已定位并修复（M2.6，2026-10-14）**。
   文件里多条注释行挨着替换块时，BC 会选与旧实现不同但等价的匹配集
   （U2-FINDINGS §3 的 all-kinds 例）；U8 又发现同一形状的第二个可复现
   形态（1-vs-2 尾部平局）。

   **根因不是“不重要行零代价的加权 diff”**。重新核对证据后确定是两层：

   * **锚定层**：旧实现让“无重要内容”的行（注释/空白）共享同一个对齐键，
     于是 Myers 会把注释与注释相互锚定，可能排在更好的整体脚本之前。
     BC 不这样做——它把这类行交给相似度配对。产品现改为：有重要内容的行
     按重要文本锚定，无重要内容的行取“独一无二”的键、永不参与锚定
     （`align::AnchorKey`）。
   * **块内配对层**：旧实现用“位置配对 / 锚定配对”二选一。BC 的发射层
     （`FUN_140dc6c40` case 2）把 1×1 未匹配格直接记为**成对行**，因此
     `different` 行是算法选出的配对；其帮助文档写明默认对齐是 Standard 并
     提供 “Use closeness matching ... based on their similarity”。产品现改为
     按相似度做单调匹配，目标为（相似度总和，配对数）字典序最大、平局取最早
     （`align::closeness_pairs`）。相似度全零时它退化为位置配对，
     `al-replace-block` 的「三行 different」因此保持不变。

   实现为有界策略：块超过 25 万格或预计工作量超过 3200 万字符时回退位置
   配对，`myers` 的线性空间保证不被破坏（`large_input.rs` 仍全绿）。

   **验证**（全部串行）：
   * 离线：产品对磁盘上 **127** 条已记录 BC 观测重放，配对与状态序列
     **127/127 全同**（修复前 5 处配对分歧：`all-kinds-c`、`all-kinds-txt`、
     `comment-lead-c`、`comment-middle-c`、`tail-1v2-txt`）。
   * 活 Oracle：`probes/m26_weighted_diff.py` 六个用例 **6/6 SAME**，
     BComp 5.0.3.30240 / 应用 5.2.1.32035，退出码全 0，Job Object
     containment（`runs/m26-weighted-probe-20261014T150040Z/`）。
   * `cargo test` **189 全绿**（新增 7 个回归测试钉住上述形态）。
   * `pytest tests` **157 全绿**（含 live Oracle 101 锚点自对拍）。
   * `offline_check.py` 锚点 **101/101** + XML **101/101**，布局 30/31。
   * 官方 harness `M2-gate-serial-02`：**429 = 428 过 + 1 已知失败 + 0 错误**，
     与修复前基线逐项相同；唯一失败仍是 `mixed-side-by-side`（A-2 在案的
     列对齐差异，与 M2 无关）。
   * U8 代码页回归护栏重跑 **45/45 全过、0 已知差异**：唯一已知差异
     `tail-tiebreak-1v2` 随本修复通过并转为护栏用例
     （`runs/u8-verify-20261014T153156Z/`，`10-m4-acceptance.md` §7 已补记）。
   * 残留进程检查：无 BComp/BCompare 残留。

   复现配对拟合的离线脚本：`tools/m26_model_grade.py`（模型对 205 条记录的
   配对拟合 205/205）、`tools/m26_baseline.py`（产品重放对比）。

   **M5.1 精化（2026-10-14，同日）**：官方门禁唯一红项 `mixed-side-by-side`
   的排查把配对模型又推进了一层，两处修正均有活 Oracle 判别证据
   （`probes/m51_sbs_marker.py`、`probes/m51b_pairing_objective.py`，
   `runs/m51-probe-*`、`runs/m51b-probe-20261014T163003Z`、
   `runs/m51c-probe-manual`；探针共 16 形态 + 3 补充形态全数复现）：

   * **closeness 相似度文本改为大小写敏感**（plain 用原始行，语法格式仍用
     重要文本，`Plan::closeness_text`）：`cs-check` 形态（`[bbbb,xx] v [X,Y]`）
     显示 BC 把全零块 zip 成两对——小写化文本会给 `xx/X` 记 1 分而选
     “孤行+单配对”，与 BC 不符。锚定层保持大小写不敏感
     （case-swap-align 依赖它），两层文本基准自此分离。
   * **平局第三键 = 最小化已配对左行总长度**，等长回退最早：2v1 全零块
     `[bbbb,o1] v [X]` BC 配第二行 `o1`（`tie-2v1`）、`[abcdefgh,ab] v [X]`
     配 `ab`（`tie-len-2v1`），而 `[dup,dup]`、`[p,q,r]` 等长形态配最早
     （`tie-dup`、`tie-3v1`）。键只取左侧是因为单调 count-max 匹配的
     右侧花费恒为前 k 行、从不构成选择。目标次序仍是（相似度和, 配对数）
     在前——`score-vs-count` 形态证明 3 分单配对胜过 0 分双配对。
   * **side-by-side 槽位字形属块级、只画块首行**（same=`=`、纯左孤=`+-`、
     纯右孤=`-+`、含配对行=`<>`），修正了此前“左格填满列才空白”的
     拟合猜测（`identical` 的行 `y` 反驳它）。`mixed-side-by-side`
     随之转绿，布局语料 **31/31**（`verify/layouts/README.md` 已补记）。

   M5.1 验证：`cargo test` **194+5+1 全绿**（新增 5 个 M5.1b 回归测试，
   1 个旧已知差异测试改为钉金标准）；`offline_check` **101/101+101/101+
   31/31**；`m26_baseline` 磁盘重放 **133 例 0 配对分歧 0 状态分歧**；
   `m26_model_grade` 更新后 **226/234**（8 处均为 M2.6 在案的四类 lab
   分词近似，配对无一失败）；两个探针复跑 **16/16 与 BC 全同**；官方
   harness `M51-gate-serial-*` 见运行报告（`mixed-side-by-side` 红项清零）。
2. **21 个未实现格式**：mask 表已登记（.java/.sql/...），行为回退 PlainText——
   对 `.java` 大小写差异会报 similar 而 BC 报 different。按格式逐个实现即可消除。
   *更正（2026-10-16，M5.3-1）*：**JAVA 已实现**（`Grammar::Java`；判别探针
   `probes/m53_java_grammar.py`、20 个金标锚点 `m53-java-*`，docs/11 §26），
   `.java` 大小写差异已报 different，本条剩余面收窄为 **18 个格式**。
   *再更正（2026-10-16，M5.3-2）*：**XML/HTML/SQL 已实现**（判别探针
   `probes/m53b_xml_html_sql.py` + `m53c_case_model.py`，35 个金标锚点
   `m53b-*`，docs/11 §27——含逐格式大小写策略：XML/HTML 串外折叠、
   SQL 关键字/标识符折叠、HTML 实体表大小写敏感匹配 + 类别配对），
   剩余面收窄为 **15 个格式**。
   *三更正（2026-10-16，M5.3-3）*：**PAS/VB/REG/COBOL/DFM 已实现**（判别
   探针 `probes/m53e_batch3.py`，35 个金标锚点 `m53e-*`，docs/11 §28——
   COBOL 列制 LineNum 不重要、VB `rem ` 未锚定注释、REG 行首锚定注释、
   PAS 指令重要、DFM 无注释）。25 条目中 12 个文本语法已实现；剩余面 =
   **BASH + PERL（文本语法）** + 10 个专用比较器（CSV/EXE/MEDIA/MSEXCEL/
   MSWORD/OPENOFFICE/PDF/PIX/RTF/SORT，划出文本语法范围，docs/11 §28.4）。
   *四更正＝M5.3 收口（2026-10-17，docs/11 §29）**：**PERL 已实现**
   （`Grammar::Perl`：全逐字比较——CaseSensitive=False 只改切分不改语义、
   POD 行锚定块跨行、StopText 无 StopEOL 跨行串、q(...)/s|tr/.../.../
   按规格完整匹配、除法形 `//` 真实）；**BASH 实测为纯文本行为**
   （`.sh` 行首 `#` 差异 different、串内大小写折叠——plain 重放 15/15
   全等，产品维持 PlainText 即正确实现，4 个 `m53p-bash-*` 锚点钉死）。
   21 个金标锚点，manifest 191→212；门禁 `M53-perl-bash-01` 487/0。
   **13 个文本语法全部落地；本已知差异条目关闭**——剩余 11 条目均为
   非文本语法（表格/二进制/文档比较器），属独立里程碑范围。
3. **statistics 布局的 I/U 列模型 —— 已定案并实现（M5.2，2026-10-14）**。
   `probes/m52_statistics_columns.py`（`runs/m52-probe-20261014T165631Z/`，
   6 形态含 /iu 变体）实测出完整记账模型：
   * `IOriginal`/`UOriginal` 把**左侧行按重要性分**（注释/空白行计入
     UOriginal，无论它是否配成 similar 行；两者之和=左行总数）；
   * 单侧不重要行进 `UDeleted`（左）/`UAdded`（右）——M2 期假设证实；
   * `options:ignore-unimportant` **不改变统计**（iu 变体逐字节相同），
     因此 statistics 从**未折叠**的组渲染（`Comparison::render`）；
   * plain 的 `// c` 是内容 → `IDeleted`（重要性按语法）。
   产品实现：`Comparison` 增加 `left_unimportant` 掩码
   （`Plan::unimportant_mask`），`statistics()` 按上述模型记账；新增 4 个
   回归测试（含 /iu 不变性）。探针复验 **6/6 一致**；statistics 五个
   golden 布局不受影响（全重要 plain fixture），`offline_check` 仍
   101/101+101/101+31/31。注意：statistics 与 display 过滤的交互仍无
   观测（语料无 statistics+display 组合），按整册比较记账处理。
4. `ignore-unimportant` 下折叠行的**借用 id** 在文本布局（side-by-side 等）中的
   展示未观察（布局语料无注释文件）；XML 布局已逐字节验证。

## 复现命令

```bash
cd D:\Rea\product\verify
python probes/u2_element_edges.py          # U2（串行 Oracle）
python probes/u2b_orphan_semantics.py      # U2b
python probes/u3_leftsimilar_options.py    # U3
python probes/u3b_summary_order.py         # U3b
python tools/m2_add_golden_anchors.py      # 语料（已执行过，重跑会拒绝重复键）
cd ..\cli && python tools/offline_check.py # 无 Oracle 对拍
cd ..\verify && python -m pytest tests -q -p no:cacheprovider
python -m harness.run_cli --install current --install reference --candidate reacmp --run-name M2-gate-serial-01
```
