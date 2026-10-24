# 12 — 维护/回归手册（合成语料收口后，2026-10-17；基线 2026-10-20 M112 刷新）

> 适用状态：M0–M5 + M5.5 十例产品改动 + M6 表格引擎（第十一例）+ M10/M11
> 注册表通道（第十二例）全部落地；gateb 带边界族 18 例已由 §30（双盒模型：
> 采集盒 1993 / 尾 NW 盒 2000）收口。
> 合成语料在案差异只剩文档化的 handler LIS 序取舍（15 例 AX/MF/GR，§25.4）。
> 本手册给出后续任何改动的最小复验配方与基线数字。

## 1. 基线快照（2026-10-20，M112 版本通道收尾轮实测；M11 期数字见括注）

| 电池 | 命令（均自 `D:\Rea`） | 基线 | 性质 |
|---|---|---|---|
| core 单测 | `cd product/core && cargo test --release` | **269** + doc 1（M7/M8 期增长，10-19 刷新） | 离线 |
| large_input | 同上（`tests/large_input.rs`） | 5/5，~7s | 性能护栏 |
| CLI 集成 | `cd product/cli && cargo test --release` | 141 + 206 + 118（M112 轮；M11 期为 195） | 离线 |
| m26 实语料 | `cd product/verify && python tools/m26_baseline.py` | 237 例 0 失配 | 离线重放 |
| fuzz | `python tools/m55_fuzz_replay.py` | 120/120 | 离线重放 |
| gateb 产品重放 | `cd extracted/_scratch/mode3 && python gateb_product_replay.py` | 167/182（失败 15 = 在案 LIS 序格，带边界 0） | 离线重放 |
| gateb 仿真器 | `python run_all.py` | 182/182（默认 WT=2000） | 离线 |
| **表格全帧重放 (M6.4+m67/m68)** | `cd extracted/_scratch/table && python replay_table_product.py` | **175 pass / 0 fail / 12 known-space / 2 skip**（帧+体全量；KNOWN 单元格列出、不冒充通过；空格候选=永久 KNOWN docs/13 §8，m68 残差收口 §9） | 离线重放 |
| **hex 产品重放 (M7)** | `cd extracted/_scratch/hex && python replay_hex_product.py` | **30 pass / 0 fail / 1 skip**（m70-m70g 全档 .out；唯一 skip = m70 H6 的 data-report-on-.bin 表格路细胞，非本通道） | 离线重放 |
| pic 单测 (M9) | `cd product/pic && cargo test` | **27**（DEFLATE/PNG/BMP 解码、像素比较、帧渲染，全离线 fixture） | 离线 |
| **pic 产品重放 (M9)** | `cd extracted/_scratch/pic && python replay_pic_product.py` | **130/130**（track A 金标准 36 逐字节折叠比对 + track B 归档 m83* 全部 .bcs 的退出码/是否写出重放 94） | 离线重放 |
| **reg 单测 (M10/M11)** | `cd product/reg && cargo test` | **27 解析 + 103 表格语料 + 9 帧**（103 = 85 中文 + 18 英文归档 .out 字节级；含 T1 逗号续行翻案、R19/I7 编码嗅探） | 离线 |
| ver 单测 (M112) | `cd product/ver && cargo test` | **18 格语料**（m112/m112b 归档表格字节级；U-ver-1 大小行按 docs/18 §8 折叠） | 离线 |
| harness pytest | `cd D:\Rea && python -m pytest product/verify/tests -q -p no:cacheprovider` | **160/160**（norm-6） | **含真实 Oracle 用例** |
| 官方门禁 | `cd product/verify && python -m harness.run_cli --install current --install reference --candidate reacmp --run-name <Mnn>-<tag>-NN` | **M112-gate-03：1056/1110**（anchor 636 + layout 93 + table 57 + hex 39 + pic 108 + reg 69 + **ver 50** + folder 2 + labels 31，current+reference 双安装；candidate 311+25=336）。54 个 fail = 17 reg sbs 几何（docs/17 §6）+ **19 ver sbs 几何（docs/18 §8，同形）** + **18 个 U-ver-1 大小行**（候选侧唯一结构外差异；docs/18 §8）。labels 佐证：31/31（norm-6 下旧折叠不受扰动） | Oracle 串行 |
| sync 集成测试 (M8) | `cd product/cli && cargo test --test script_exec` | **9/9**（逐格对应 m81*/m82* 实测：update 拷贝不删、mirror 删孤儿、空源清空、create-empty、visible 禁用 create-empty、无 load、半载 100、目标较新保留）；CLI 全量（M8 轮为 170，现 195） | 离线 |
| picture 集成测试 (M9) | `cd product/cli && cargo test --test script_exec` | **13/13**（逐格对应 m83*/O*/C* 实测：帧序、计数序、25/26、多余、错误行、选项惰性/改名、拒绝面 106/107、BOM shell、title）；CLI 全量 195 | 离线 |
| registry 集成测试 (M11) | `cd product/cli && cargo test --test script_exec` | **12/12**（逐格对应 m101 R*/N*/G* 实测：layout 拒绝面 106/107、四个选项 token、output-options 106、零文件 BOM shell 带 Mode、PNG 编码错误行无后缀、解析错误行 + 后缀存活、title、display 过滤）；CLI 全量 195 |
| version 集成测试 (M112) | `cd product/cli && cargo test --test script_exec` | **12/12**（逐格对应 m112 V*/W* 实测：layout 拒绝面 + 大小写折叠、四选项词汇、output-options 106、单/三文件 106、零文件 BOM shell 带 Mode、缺文件/目录 107、单文件形、title+diff 对）；CLI 全量 206 | 离线 |

门禁 1035 为**含 reference 佐证**的全量（reg/oracle 46 = 23 金标准 × 两安装；
金标准由**英文参考安装**生成——注册表 sbs 表格几何是 locale 参数的，
列下界=表头标签宽度，中文 名称/类型/数据 比英文 Name/Type/Data 窄，产品渲染
英文帧，故中文几何由 reacmp-reg 自己的 103 格语料锁定，docs/17 §6/§9）。
norm-5 起注册表标签（标题/两个 Mode 行/四条错误行模式/四个计数标签）入
ruleset；注册表金标准在 `verify/reg/`（append-only，23 判别细胞，
`tools/m111_add_reg_goldens.py` 生成；fixture 为探针字节逐字节复制、
最终树就地重跑）。

> 观测记录（2026-10-19）：CLI 全量在一次跨工作目录的 `cargo test --release`
> 中出现过 1 例瞬时失败（script_exec 195 中 194 过），同一条命令重跑
> 18 次全绿（含 6 次整包 141+195+118）、单测目标复跑 8 次全绿，未能复现
> 也未能定位到具体用例（输出未留下用例名）。记为**未定位瞬时**，不是回归：
> 门禁与整包复跑均绿。若再现，先用 `--nocapture` 抓用例名再归因。

## 2. 复验配方（改动 → 门禁的漏斗顺序）

1. **离线先跑**（秒级–分钟级，不碰 Oracle）：core/CLI cargo test、m26、fuzz、
   gateb 重放。任何一项背离基线 ⇒ 先归因，不进门禁。
2. **性能**：align/importance 相关改动必须 `cargo test --test large_input`
   （离线模型绿 ≠ 性能绿，纪律来源见记忆 [[rea-project-state]]）。
3. **仿真器先行**（模式 3 带引擎改动）：`simulate_mode3.py` + `run_all.py`
   对 182 存档夹具先行验证，绿了再动产品。开关 `SIM_W`/`SIM_WT`/`S_VARIANT`
   保留为探针用途；默认值即已验证行为。
4. **官方门禁**：串行、Job-Object 收束，跑完即 `tasklist | grep -i bcomp`
   验残留。锚点若背离，先做判别探针（新夹具、真 Oracle 小批量），
   再改产品——五步闭环（判别探针→实现→重放→锚点→门禁）。

## 3. 本会话教训（写死以免复发）

- **Oracle 串行纪律包括 pytest**：`test_oracle_live.py`/`test_process_tree.py`
  会真启 Oracle。与门禁并行跑会互相打架（本轮出现 3 例 exit 107 + 2 例
  树回收失败，串行重跑后全部通过、残留为零）。凡碰 Oracle 的电池一次只有一个。
- **禁止冻结清单计数**：锚点清单是 append-only 的（101→212）。四处硬编码
  `101`（test_runner、test_oracle_live ×2、run_cli 标签）已改为与
  `man_mod.load_anchors()` 动态一致。今后加锚点**不需要**改测试。
- **仿真器默认值 = 已验证模型**：WT 默认从 `str(W)` 更正为 `2000`（§30 双盒
  定案后遗留的默认值滞后）；`S_RAW` 证伪分支已删除并留注释。
- **显示层会改写分隔符**（M6.4 帧翻案）：od/grep/编辑器预览在同一轮里把
  斜杠显示成破折号、把破折号显示成斜杠，"dash 实测"结论由此而来并写进了
  M6.3。字节层裁决只用**整数计数与序数列表**（`b.count(bytes([0x2d]))`、
  `list(b[i:i+10])`），永远不读 repr 文本做定论。
- **验收面必须覆盖帧**：体层重放剥离了帧，帧里的 dash/slash 错误穿越了
  68/68 全部门；表格门禁（全帧比较）首跑即抓到体层从没有过的组合缺陷
  （summary 计数序）。任何"只比体层"的验收都是不完整的。

## 4. 免费真值资产清单

- `product/verify/runs/gateb-*`：182 夹具 + Oracle XML（137 旧 + 45 新，
  含 tailbox/tailreach 判别批）。
- `verify/golden/`、`verify/layouts/`、`verify/table/`（16 判别细胞，M6.4）、
  `runs/m54-fuzz-*`：m26/fuzz/表格重放真值。
- `runs/m60-*…m66b-*`：~150 份表格 Oracle 存档报告 = 表格引擎全帧免费回归集。
- 官方英文安装 `D:\bc-official\app`（5.2.6.32774）现在 harness 中
  `reference enabled=True`，可随时做 label 佐证与双版本回归。

## 5. 已知在案差异（非新缺陷，勿重复攻坚）

- 15 例 gateb 小区间 handler 格（AX/MF/GR）：`lis_overwrite_left` 左序 vs
  oracle 右序臂，实语料优先 ⇒ 保留左序（§25.4、记忆 [[reacompare-m5-mode3-router]]）。
- 尾 NW 盒 +7（2000 vs job+0x98=1993）的代码级来源未解，记为残差未知
  （§30.4）；行为层面已在 182 例上钉死。
- gateb 合成格与 gate 门禁的 2 例已知差异：见 `report.json` 的
  `known_differences`，逐条有出处。

## 6. GUI 门禁（2026-10-22 换代，docs/20 §4）

**新路线日常套件（改动 GUI 后必跑，零 Oracle 依赖）：**

| 门禁 | 命令 | 判据 | 现状基线 |
|---|---|---|---|
| 结构 211 | `python tools/ui-batch-accept.py --min 211` | 渲染→dump→结构门禁 full 级 211/211 | 211/211 |
| 离线三轴重放 | `python tools/menu-offline-check.py` | 台账 vs 四矩阵/spec：菜单+序+enabled、chrome 三元组、骨架前序 | 845/410/290 0 违例 |
| 分派 | `python tools/dispatch-check.py` | 7 实测格路由+标题（品牌位=LiuCompare，D1）+6 task-only 拒路 exit 3 | 13/13 |
| 内容台账 | `python tools/textcontent-check.py <spec> L R [All|Diffs|Same]` | 产品 ledger == 直调引擎逐行逐字+文本锚定+mode | 12/7/5 绿 |
| **活体自家 golden** | `python tools/gui-self-check.py <spec> [--view V]` | 产品 UIA 树（tops/labels/accessKey/chrome/skeleton/标题）== `extracted/golden-gui/<View>.json`；缺文件=红 | 12/12 绿 |
| 活体内容 tint | `python tools/uia-text-content-check.py <spec> L R` | PrintWindow 逐状态行取色 == colors.json 实测值+骨架未破 | 10+24 绿 |
| 活体过滤钮 | `python tools/uia-text-filter-check.py <spec> L R All|Diffs|Same` | radio 选中/未选像素+过滤行集（三路径通道） | 3/3 绿 |
| **活体暗色主题** | `python tools/theme-dark-check.py`；负向=`... negative`（须红才过） | 产品 `--theme dark` 渲染，PrintWindow 逐状态 tint+gutter+radio == `product/gui/themes/dark.json` 声明值（自家设计基线；几何不主题化=仍读实测 colors.json）；负向=变异色板注入产品须被抓=可红证明 | 正向 10 tint+gutter+radio 绿；负向 2 违例被抓 |
| **活体 D3 无障碍** | `python tools/uia-d3-check.py <spec> L R` | 控制视图骨架 24 节点不变（TextPane 子树豁免单点定义于 uia_menu_check_lib）+ 内容视图双窗格 2×N 行 Text 节点逐行 name==引擎台账；负向=`REACMP_D3=0`（行消失须被抓） | 正向 24+24 绿；负向退 1 被抓 |
| **活体交互第一档** | `python tools/uia-text-interact-check.py <spec> L R [negative]` | footer 初始=grid[0].ltid:1 双侧；点击 row2→双 footer 同值+详情双条像素变化+各状态 tint 不变（选中不铺底色=实测）；滚轮→双窗格可见首行渲染同 grid 行本侧 tint（共享视口）+footer 不动；全程骨架 24；负向=`REACMP_INTERACT_NEG=1` 注入右 footer 失联须被抓 | 正向全绿；负向 2 违例被抓 |
| 活体查找通道 | `python tools/uia-text-find-check.py <spec> L R [negative]` | Ctrl+F 条开合+键入实时黄标不移动光标+Next 跳共享光标（橙 accent 仅落持有匹配窗格）+Esc 关条保光标；负向=注入 Next 不步进须被抓 | 正向全绿；负向被抓（2026-10-23） |
| 活体 overview 条 | `python tools/uia-overview-check.py <spec> L R [negative]` | 几何（左 52px 列/顶对齐）+逐状态色带（带内多点采样，容忍选中行橙线=near() 必须 int() 强转防 uint8 回绕）+点击跳转双 footer 同步；负向=`REACMP_OVERVIEW_NEG=1` 条绘制但点击失联须被抓 | 正向全绿；负向被抓（2026-10-24 修复 StackPanel 无界测量后复绿） |
| 活体合并第一档 | `python tools/uia-text-merge-check.py L R C [negative]` | 三源横排+输出在下+Take 六钮 UIA 名逐字+`# N conflict section(s)` 状态行+Take Left 解析红→青；负向=`REACMP_MERGE_NEG=1` Take 不生效须被抓（fixture=_tmp/merge-fix/ 冲突族） | 正向全绿；负向被抓（2026-10-23） |
| 活体合并编辑档 | `python tools/uia-text-merge-edit-check.py <spec> L R C [negative]` | 打开/键入不落盘+Ctrl+S 直写 auto-merge+marker、LF/无 BOM/无尾换行、无 PRESETPANE 泄漏；负向=`REACMP_MERGE_SAVE_NEG=1` 静默失效须被抓 | 正向全绿；负向被抓（2026-10-23） |
| 活体 Folder Compare | `python tools/uia-folder-check.py [negative]` | 全宽 TDirTreeView+光标蓝(168,205,241)首行+斑马(248,250,249)+红/紫/灰状态文字色（folderview-findings.json 实测）+点击光标跟随+状态栏计数==引擎聚合（4/24、4/26+free 形状）；负向=`REACMP_FOLDER_NEG=1`（光标冻结）与 `REACMP_FOLDER_SB_NEG=1`（计数注入 999）均须被抓 | 正负向全绿（2026-10-24，含状态栏接线） |
| 活体 Hex Compare | `python tools/uia-hex-check.py [negative]` | 双 THexEditor 并排（tree-first=右）+逐字节粉带/红字/hatch（hexview-findings.json 实测值）+双窗格共享青 caret 点击同步；负向=`REACMP_HEX_NEG=1` 光标冻结须被抓 | 正负向全绿（2026-10-24） |
| 活体合并 Merge to/Swap | `python tools/uia-text-merge-to-check.py [positive\|mergeto\|swap]` | 标题+路径框跟随 Merge to 单选（OUT→left，docs/19 §6.18 实测）；Ctrl+S 写所指向（left 文件→OUT，哨兵原样、对侧不动）；Swap 交换侧带+输出着色翻转 (213,255,255)→(248,227,255)；负向=`REACMP_MERGETO_NEG=1`/`REACMP_SWAP_NEG=1` 须被抓 | 三态全绿（2026-10-24） |
| 活体工具栏文字钮 | `python tools/uia-toolbar-check.py L R [positive\|negative\|dark]` | 13 命名钮全在+39px/44 行实测几何+按钮区字形墨水（dark 模式==dark.json toolbar.text ±25）+全树 preorder 与正向逐字节一致；负向=`REACMP_TB_NEG=1`（面禁画、布局不变）墨水归零+树不变须被抓 | **树级已绿（12 golden 逐字节+负向树 386 节点一致）；像素三模待补跑**（2026-10-24 环境屏保锁定，docs/19 §6.21 收口状态） |

**活体门禁-fixture 适配在案**：`uia-text-content-check` / `uia-text-filter-check`
须用小 fixture（`_tmp/c_L.txt`/`_tmp/c_R.txt`）——150 行 fixture（layout-left/
right）的首孤儿行在 864px 窗口视口外（row 59），门禁采样为 None 属 fixture
适配问题而非产品缺陷（任意布局下同样采不到）。

**golden 纪律**：改 UI 必然红——修 bug 就重录 `--record`（逐视图或全量）；
re-base 与改动**同提交**并在提交信息里写明原因；禁止"顺手录一次消红"。
golden 是**产品自己**的活体观测（非 spec 复述），故仍能抓 spec→WPF→UIA
翻译损耗（RadioButton/Slider 历史教训的捕获面不变）。

**Oracle 系检查器（uia-menu-check.py、uia-text-*.py 对 Oracle 的部分、
live-*probes.py、extracted/live/**、extracted/guibaseline/**）**：退役为
低频对标工具与参考证据库（docs/20 §4-4 走查时启用；探针纪律不变=
`live_probe_job.py` Job Object+串行+残留 0）。**不得**再把"与 Oracle 逐字节
一致"当作 GUI 验收判据；语义层例外——行为规格（分派表、radio 互斥、
灰态双层、footer 语义）已转入上方自家门禁。

**colors.json / filter-map.json** 仍被内容/过滤活体门禁用作**期望值**：
它们是 BC 实测色/像素语义，我们当前选择沿用其色相（docs/20 §3 P5）；
若主题改色（D5 暗色），重录这两档期望=自家基线化（走 --record 同款纪律），
不要手改 JSON 数字。

**启动路径-DPI 实锤（2026-10-22）**：`dotnet reacmp-gui.dll`（托管 host）= SYSTEM
感知，`reacmp-gui.exe`（apphost，内嵌 PerMonitorV2 清单）= PER_MONITOR（GetProcessDpiAwareness
实测）。自家活体门禁 `gui-self-check.py` 已改用 **exe 出货路径**（golden 亦按此重录；
在 96-DPI 测试台两条路径的控制视图逐字节一致，已互 diff 证明）。其它仍走
`dotnet dll` 的活体门禁在本测试台等价（DPI=100%），换缩放显示器验证时一并切换。
