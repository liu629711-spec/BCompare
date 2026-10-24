---
name: reacmpare-gui-wpf-p1
description: GUI 实现开工（P1）：WPF 选型定案+渲染器骨架；双闭环（结构 211/211 + UIA 自检）；菜单/chrome/内容骨架/视图分派四线收口（845/410/290/7格全 0 违例+活体 12/12）；RE 不可行实证；下一步=引擎接线/窗格内容
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

2026-10-20：功能 16 GUI 从"侦察"进入"实现开工"（用户批准 docs/03 3B = Rust 核心 + .NET WPF）。

**为什么 WPF（判据，勿翻案）**：①验收命脉是 UIA（四份 Oracle 活体基线全由 pywinauto UIA 采集），WPF 是 UIA 一等公民、测产品与测 Oracle 同一 harness；BC 的 VCL UIA 桥三轮试错教训（ExpandCollapse 不实现）——egui/Slint 的 AccessKit 桥不敢赌；②BC 是原生 Win32 观感，WPF 系统主题/原生弹出/高 DPI 天然接近；③.NET SDK 8.0.422 + WindowsDesktop runtime 本机就绪。

**工程与验收（docs/19 §6 为详版）**：`product/gui/WpfHost/`（net8.0-windows）。
- descriptor（与 guibaseline 同构 `{name,cls,props,children}`）→ WPF 树 → `--dump` 反向同构 JSON；dump 过程逐节点保真校验（视觉树存在性/几何/文字），违例退出码 1。
- **结构层**：5 窗体（ABOUT/INFO/KEYUPGRADE/SNAPSHOT/QUICKCOMPARE）过 `ui-structure-check.py --level full` 全 0 diff；变异（Left/Caption）被门禁抓 2 条（非恒过）。
- **活体层**：`tools/uia-selfcheck.py` 拉起 `--show` 窗口、同 Oracle 路径断言：23/23 具名节点命中、文本一致。
- **WPF 坑（重要）**：布局容器默认 peer 不进 UIA control view → 7 个容器节点活体消失而结构层全绿。解法 `PanelHost`（ContentControl + 自定义 peer：IsControlElementCore=true、ControlType=Pane）。教训：结构层与活体层必须都测。

**批量验收（同日收口）**：`tools/ui-batch-accept.py` 对全 211 窗体 render→dump→门禁，**full 级 211/211 两次稳定全绿**、structure 级 211/211、UIA 自检仍绿。两个坑（防再犯）：①非 Dialog 根（T*ACTIONS/T*IMAGES）必须建离屏无边框窗口（WindowStyle.None+MinHeight=1+Left/Top=-4000），否则 WPF MinHeight 把 291/320 顶到 300；②DFM 根 Left/Top 是屏幕坐标非契约，fidelity 校验只对画布内子节点做。211/211=描述符契约零丢失，**不等于**视觉保真（§2.2 实现期收敛项）。

**菜单系统（2026-10-21 收口，docs/19 §6.6）**：数据驱动 WPF Menu = TUiMainMenu 等价物，spec 全部来自 Oracle 实测（presence-matrix 262 行 + item_order + top_menus_per_view + view_forms + 515 复合键 actions + top_access → `extracted/_scratch/menu-spec.json`；生成器 `gen_spec2.py`）。`reacmp-gui --menu-spec … --view NAME --dump ledger` 产台账；`tools/uia-menu-check.py` 活体读产品 UIA 树对拍。**双门禁 12/12 视图全绿**（离线：Home 4菜单27项…Text Merge 7菜单104项，序+标签一致；活体：顶栏标签序+每菜单 AccessKey，Picture 6 菜单无 Search、Folder 系 File→Actions 全对）。实测规则（勿翻案）：①presence 权威 Category 不权威（Show All 活在 View）；②每视图挂载窗体集不同（Folder=TDIRBASE+TDIR…）；③顶层菜单集是 per-view 的——spec 曾硬编码 Text 的 flat 数组致批量 8/12，改 per-view 字典后 12/12；④顶菜单 AccessKey=首子项 AccessKey；⑤快捷键序 Ctrl+Alt+Shift（活体实测，非 Ctrl+Shift+Alt；`(?<!Mac)ShortCutStr`）；⑥运行时格式符 ExpandFormat（About %s、%0:s &Info）。WPF 坑（防再犯）：InputGestureText 不进 UIA Name→真 KeyBinding(command,key,mods)；BcMenuItemPeer.GetNameCore 剥 `&_` 追 `\t<gesture>`、IsControlElementCore=true 漏写=菜单整体消失；WPF Menu 报 'Menu' 而系统标题栏报 'MenuBar'（子数≥2 择应用栏）；子菜单 --expand 需交互前台（后台服务被 OS 前台锁挡）→ checker 两档；popup 后旧 UIA 引用失效→每开关重读。残差：图标、state-dependent 随会话内容翻转的活体复测。
**菜单灰态接线（2026-10-21 同日追加）**：enabled-matrix 264 行并入 spec（标签剥 `\t` 与 presence 264/264 对齐）。实测语义（captured_state=空会话基线）：always-enabled=在场即可用；view-capability=静态置灰（TMenuUpdater 能力掩码）；state-dependent=仅捕获的空会话视图置灰（重放同一基线故规则一致）。渲染器 `IsEnabledIn`+台账 `enabled` 字段；门禁升级=845 项（标签+序+enabled）逐项对拍 12 份 Oracle 快照 0 违例；灰态总数 56=矩阵 disabled 并集 56（非恒过）；活体顶栏回归 12/12、零残留。

**chrome 接线（2026-10-21 同日追加，docs/19 §6.7）**：chrome-matrix 12 视图工具栏/状态栏原样嵌入 spec `chrome` 块（410 项 (ct,cls,name) 三元组，Home 空属实）。`ChromeHost.cs` ChromeElement/ChromePeer 三属性全由数据决定（含 TUiTreeButton/TUiSpecComboBox 类名还原）；行=PanelHost 包裹+AutomationId `chrome:{tb|sb}:{i}`（活体按 id 定位、不耦合 DockPanel 序；tb 全 Dock=Top、sb 逆序 Bottom）。台账改 bundle {view,items,toolbars,statusbars}。离线 410 项 0 违例；活体 `uia-menu-check --chrome` **首跑抓到真实缺陷**：RadioButton 不在 ct→AutomationControlType 映射落 default Custom，Oracle ('RadioButton','TUiRadioButton','Other:') vs 产品 ('Custom',...)——补映射后 12/12。教训（§6.3 再验证）：离线台账只证明 spec→ledger 忠实，活体对拍才证明 WPF peer 真把数据翻成 UIA 事实。残差：RadioButton 选择态、子工具栏 combo 内容项、chrome 图标、状态栏运行时文本（动态面）。

**内容视图骨架接线（2026-10-21，docs/19 §6.8）**：home_tree 扁平深度前序表重建嵌套树→剪枝规则=测量基准（剪 TUiMainDock 子树=菜单轴、TitleBar=OS；只留 cls 非空节点；TUiToolbar/TUiStatusBar 容器按预分配消费第 i 条 chrome 行且不下潜；TViewForm 窗口节点不比=已知身份别名 WPF 报 HwndWrapper）。`extracted/_scratch/skel.py`（行消耗断言防静默错位；教训：Python 默认参数 `ti=[0]` 跨调用共享污染计数）→ spec `skeleton` 块 12 视图 290 节点。ChromeContainer（容器同样三元组全数据）；行宿主复用 `chrome:{sec}:{i}` AutomationId→骨架内嵌行与 chrome 台账同一物理元素零重复渲染（§6.7 顶层独立行被骨架取代）。活体 --skeleton 档（跳过规则同剪枝）再抓一例：TUiTrackBar Oracle 报 Slider、产品落 Custom→补 Slider/Spinner/ProgressBar 映射；至此 ct 映射覆盖两份快照全部词汇。双门禁：离线 skeleton 290 + menu 845 + chrome 410 全 0 违例；活体 topbar+chrome+skeleton 12/12、零残留。残差：骨架几何（rect 已采未作契约）、窗格文本动态面。

**视图分派收口（2026-10-21，docs/19 §6.9）**：用户问"有源码了为何不逆向"→ 完整 RE 可行性实验：①字符串→xref→注册壳伪码可读；②但类型注册走函数指针表→静态调用者=空（调用图碎）；③注册 API 调用者 1300+（过度通用的字符串赋值例程）→穷举甄别成本爆炸；④一次逐函数反编译 30min 超时→纯 RE 定案不现实。副产品：Picture 掩码串 *.htm;*.html;*.xml;*.jpg;*.gif;*.png @0x140ef0870 记录为 hint（未行为实测不入格）。实测缺口只剩兜底格：合并探针一次启动 .zqq→Text Compare（view-fallback-zqq 快照，残留 0）。`Dispatch.cs`+spec `dispatch` 块（每格带 evidence 字段）；`--dispatch L R` 入口：7/7 格重放全过（.txt/.bin/.csv/.png/dirs/.reg→Text/fallback）+task-only 六视图无文件路由（拒路退出码 3）+标题规则 `{L} <--> {R} - {View} - Beyond Compare`；活体互证产品窗口标题逐字匹配 Oracle 2/2。三轴全量回归 12/12、零残留。残差：hint 格待实测补正、混合输入（文件+目录）未测。

**下一步（P1 主体）**：引擎边界走进程/FFI（CLI 调用）→ 窗格内容动态渲染（差异着色/行号）。菜单/chrome/内容骨架/视图分派四轴静态面已全收口。

相关：[[reacompare-gui-recon]]、[[reacompare-m112-version-channel]]
