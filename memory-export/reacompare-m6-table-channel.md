---
name: reacompare-m6-table-channel
description: M6 表格比较全程收口：通道/行模型/三渲染 + M6.3 引擎落地 + M6.4 收尾（帧 dash→slash 翻案、AA/AB 字母、EOF 收口、自动检测三路实装、verify/table golden + 门禁 table 套件）+ m67 空格攻坚定案（永久 KNOWN）+ m68 残差收口（混合扩展名 pin/interleaved rawline），门禁 819/819、重放 175/0/12known
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

2026-10-17/18 M6 全程（docs/13 `product/docs/13-m6-table-channel.md` §1–§8）。探针 `probes/m60_table / m61_* / m62_* / m62b_width / m63_cli_surface / m64_residual / m65_autodetect / m65b_space_rules / m65c_space_model / m66_summaryorder / m66b_summaryorder / m67_space_attack` → 对应 `runs/m6*-*`（**~166 份 Oracle 报告 = 全帧免费回归真值**；每批跑前残留检查）。

**通道**：`data-report`（别名 `table-report`）无 XML 布局（106，T2）；三版式 side-by-side/interleaved/summary；**任何 `options:` → 105**（P6-P9）、`output-options:` → 106（X8）、零文件 107、三文件 106、缺文件 107、`title:` 顶替首帧行（X4）。`text-report` 无视 .csv 关联（T5）。**帧 = 斜杠日期**（M6.3 记的 "dash 实测"是显示层误读，M6.4 字节普查 114/114 slash 翻案；`stamp.rs::dashed()` 已删。教训：**验收面必须覆盖帧**，字节裁决只用整数计数/序数列表，永远不读 repr 文本）。

**行模型**：行=CSV 记录（引号内 `\n` 一行、显示 0x00）；EOF 前空行=真实行（m64 E1-E3 收口，Rust split_records 行为实测一致）；对齐=内容 LCS+间隙位置 zip（无 closeness）；四标记 `=`/`<>`/`+-`/`-+`；summary 计数序 **same→left→right→diff**（旧 §4.6 "same/diff/left/right" 是未测推断——表格门禁首跑抓到反例，m66b 四态并现钉死；文档划线更正）。列：列数=两侧最大；宽度该侧 + **字母本身撑下限**（AA/AB=2，m64c2）；列字母 A..Z→**AA,AB,AC**（Excel 式，非 ASCII 续行；`#` 占位残差删除）；sbs 数字右对齐、interleaved 全左对齐、行号场 rjust 到该侧最大行号位数；**规则线宽=rstrip 前的行宽**（SP5）。

**三态格式（§7.4，M6.4 实装）**：`.csv`（任一文件命中，大小写不敏感）⇒ 固定逗号；其它 ⇒ **联合检测**（PF1/PF2：单边候选生效双方），优先链 **逗号>tab>分号>管道**（十格两两矩阵无一例外），限定符屏蔽（Q1/SP4）；无候选 ⇒ **rawline**（整行一单元格、去前导空白 SP10、尾随空格是数据 W1/SP5、逐字节相等 SP9）。

**空格切分 = 永久 KNOWN，定案于 m67 攻坚轮（§8，2026-10-18）**：`probes/m67_space_attack_probe.py` → `runs/m67-spaceattack-20261018T054039Z`（8 对 × sbs+interleaved = 16 报告；**方法关键：sbs 补白毁掉单元格字节，判定读数必须用 interleaved 的逐字节单元格列表**）。新增一致判别：单行文件永不空格切（H1/H2 自身相同⇒rawline）；逗号>空格（H6 ⇒两侧都按逗号切，产品重放 PASS）；无一空格行的文件⇒rawline（H7）；对齐单空格=切且单元格保留 run（H8=S4 形⇒KNOWN）。**矛盾钉在 Oracle 自身渲染**：H5（两侧首行原始字节逐字节相同 [97,32,98,10]，BC 表头 split 形却行 1 `<>`；行 2 差异不应回溯改变行 1 切分）与 H8/H4（切且保留 run）、H3/SP1（错位拒切）、H1/H2（单行拒切）无法由同一接受/比较规则同时满足——七批独立探针（m62/m65/m65b/m65c/m67）反复命中同一矛盾族。产品维持 rawline 回退。KNOWN 表 5 tag→8 tag（+H4/H5/H8=11 报告），重放基线 **167 pass/0 fail/11 known-space/2 skip**（总 178）。H4 教训：判"相同行 `<>`"矛盾前必须整数审计原始行字节——H4 两侧行 1 本就不同（`a b`≠`a  b`），不构成矛盾；真矛盾只有 H5。

**门禁（§7.3）**：`verify/table/` append-only 16 判别细胞（`tools/m64_add_table_goldens.py` 串行 Oracle 生成；空格残差细胞刻意排除）+ harness 第五套件 `table`（oracle 双安装 + candidate 脚本对脚本、全帧逐行结构比较；norm-2 收表格标题/计数标签对）。数字：全门禁 `M64-gate-01`/`M67-gate-01` = **810/810**（762+table 32oracle+16candidate）；全帧重放 `replay_table_product.py`（升级版：帧+体全量 + .bcs 原行重放 + exit-surface 细胞）= m67 后 **167 pass/0 fail/11 known-space/2 skip**（总 178；KNOWN 表 keyed by (run-prefix, tag)）；core 253（+8 M6.4：字母/宽/summary 序/检测/rawline 6+2；m67 无产品代码改动，仅 help 文案指向 §8）、CLI 141/161/118、pytest 158（ruleset bump 测试改写 + 表格标签折叠例）。

**教训（入册）**：产品重放是比仿真器更强的门（W3）；**帧剥离的重放放过帧错误**（dash/slash）；**未测推断写进文档要划线更正而非静默改**；门禁首跑即抓到体层重放从未见过的组合缺陷（diff+orph 并现）——"golden 树+全帧+多类别组合"的价值证明；display 层（od/grep/编辑器）对分隔符不可信，字节序数才可。

**How to apply:** 表格改动按 [[reacompare-maintenance-state]] 漏斗：先 `replay_table_product.py`（全帧）→ core/CLI → 门禁 `--suite table`（`--install current --install reference --candidate reacmp`）。空格候选**已定案永久 KNOWN（§8），勿再开攻坚**——七批探针证实矛盾在 Oracle 渲染侧；若未来 BC 升级改变行为，先整数审计原始字节再判"相同行 `<>`"（H4 教训：`a b`≠`a  b`，别把形似当相同）。**m68 残差收口（§9）**：`.csv` pin 对混合扩展名成立（MX6/MX1：一侧 .csv ⇒ 双侧固定逗号，含大写 .CSV；判别格=无逗号+混合扩展名；MX4 只与 pin 一致、不判别）；interleaved rawline 与 sbs 同模型（IR1 去前导空白、IR3 数字左对齐）；IR2（空格切分形）入 KNOWN。golden 树 16→19（+t-mixed-csvp/t-int-rawline/t-int-num，`tools/m68_add_table_goldens.py`；TableCase 新增可选 `ext_right`，manifest 缺省同 ext）。基线：门禁 **M68-gate-01=819/819**（table 38oracle+19candidate）、重放 **175/0/12known/2skip**（总 187）、core 253、CLI 141/161/118、pytest 158。表格通道在案残差全部清零；下一缺口=功能矩阵 5 二进制/十六进制（U5）或 4 文件夹同步（U8）。
