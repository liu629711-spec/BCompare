---
name: reacompare-gui-wpf-p1-engine-wiring
description: GUI P1 引擎接线收口——reacmp 进程边界、活体取色 colors.json 全集、四门禁+负向验证；§6.11 radio 三钮；§6.12 D3 行进 UIA（WPF false-control 不可见实锤）+交互第一档+布局翻案；§6.18 Merge to/Swap+两真缺陷（content 根 StackPanel→DockPanel、near() uint8 回绕→int 强转）；§6.19 Hex 视图第一档（16 字节 2×8 组视图模型≠M7 报告 8 槽/--hex3）；§6.20 Folder 列视图第一档（全宽双画侧/--dir3/新视图接线两件套）——MVP 功能 1/3/11/13/15 GUI 关键路径全通
metadata:
  node_type: memory
  type: project
  originSessionId: session_48b07c16989dad3d0ca22d368bf6f4cb
---

2026-10-21 第十二例改动（承接 [[reacmpare-gui-wpf-p1]]）：引擎接线 + Text Compare 动态面收口，docs/19 §6.10。

**进程边界**：`EngineBridge.cs` = 一行 `text-report layout:xml` 脚本 + `reacmp @script` 子进程 + XML 解析（linecomp status/text ltid/rtid）。引擎失败面（105/106/107、缺 colors.json）GUI 统一收敛为**退出码 4=ENGINE-FAIL，绝不猜结果**。ledger `--dump` 新增 `content` 块（逐行 status/ltext/rtext/ltid/rtid）= 渲染数据可审计。

**活体取色实锤**（探针 `tools/live-text-color-probe.py`，三启动零残留；分析 `tools/textcolor-analyze.py` → `extracted/live/textcolor-en/colors.json` 每值带出处）：
- 语料先离线用自家引擎构造成五状态齐的一份 XML（单启动取齐全部色）；
- 行距 15px、首行 y=0、灰栏到 x=41 正文起点 42；**same 行=窗格底色（无着色带）**；similar 淡蓝 (238,238,255/右252)、different+孤儿内容侧淡红 (255,227,227 / 右252,230,230)、孤儿空档=底色+对角点阵（右 stripe191 周期8 相位(x+y)%8==7；左 stripe230 更密=在案未全建模）；墨色左黑/右(48,48,48)；
- **右窗格整体 -3 与焦点无关**（--click-pane 二次采集色不变=固定逐窗格常量，勿再翻案）；
- 词级 inline 标记（金/橙/蓝）=在案残差不入第一版。

**设计实锤**：BC TTextEditor 在 UIA **不暴露行内容**（两快照证实）→ 产品 `TextPaneView` 裸 FrameworkElement 自绘（默认 peer 被剪）→ 符合 Oracle 且不破 §6.8 290 前序。窗格树序 BC 实测=**右先**（editor#0 x=784），产品 attach 同序。

**四门禁**：textcontent-check（12 行逐字==独立直调引擎+文本锚定源行）、uia-text-content-check（活体 PrintWindow 10 tint+骨架24 未破；负向=REACMP_PRODUCT_COLORS 变异渲染抓红，非恒过证明）、**menu-offline-check.py（新收编：原散会话的 845/410/290 三轴离线重放成可跑脚本）**、dispatch-check（7 格路由+标题逐字、6 task-only **真实触发退出码 3** 经合成 .tonly 分支护栏=13/13）。

**回归全绿**：live 三档批量 12/12、211/211、零残留。WPF 坑：MeasureOverride 钳宽会致色带短于窗格（活体读底色）；Style 撞 FrameworkElement.Style→改名 Colors。

**动态面残差（下一步）**：MainBar 过滤钮选中态/display 联动、状态栏运行时文本（Load time、footer `1: 1`）、词级标记、详情窗格、滚动同步、Hex/Table/Picture 等其余视图内容通道、文件+目录混合格。

---

**§6.11 过滤钮 radio 接线（同日追加，残差第一格收口）**：
- **通道实锤（关键）**：@script `text-report options:` 通道**接受选项名但不过滤**（exec.rs `ReportOptions::default()`，实测 12 行无 mode 元素）；三路径 `reacmp L R out --opt=<display-*>` **真过滤+写 `<mode>`**（语料行数 all=12/mismatches=7/matches=5/context=12/ignore=12）。GUI 已切三路径通道（`Compare(L,R,opt)`），**窗格绝不重实现过滤谓词**。
- **radio 三钮实锤**（探针 live-text-filter-probe/probe4，textfilter2/4-en，零残留；映射+色+尺寸 59×39 全存 `extracted/live/textfilter2-en/filter-map.json`）：All/Diffs/Same 互斥单选（初始=All），选中=整钮淡蓝 (194,220,245)/未选灰 (240,240,240)（单色列逐拍裁定）；**选中态完全不进 UIA**（Toggle/legacy 全 None）；tooltip 文本即模式语义（"Shows same, left orphan…"=All 等）；**Context/Minor 可加性未裁定=在案残差，本块不接**。footer `N: C`=源行号:列号（点第4行得 4: 10）=待接。
- **实现**：ChromeElement 加 Selected/Clicked/OnRender（像素色=实测、UIA 不暴露选中照抄 BC）；--display NAME 初始钮（未知名退 4）；点击→引擎重取（失败保留现图）→刷新。双门禁：textcontent-check display 档（台账 7/5 行+mode==直调引擎三路径）、新活体 `uia-text-filter-check.py`（三钮 rect 取色+过滤网格逐行 24/14/10 tint）3/3 绿；回归 845/410/290、dispatch 13/13、§6.10 内容档、活体 12/12 全绿。
- **两坑（活体首跑抓到，再证"活体必须测"）**：BuildSkelNode 递归分支漏传 decorate→钮 2×2 无色；800×480 窗口容不下 12 行（row11 采到窗外黑）→dispatch 窗扩 1200×820（尺寸=实现期收敛非契约）。

---

**§6.12 第四步 D3+交互第一档（2026-10-22，详情/滚动/选中/footer 全落地）**：
- **D3 provider 实锤（关键 WPF 平台事实）**：初版 IsControlElement=false 的行 peer **在 UIA 里根本不可见**（WPF 桥对 false-control peer 不暴露给任何树遍历=探针实锤）→翻案：行=控制元素，结构门禁在 `uia_menu_check_lib.live_skeleton_preorder` **按 class `TextPane` 单点豁免**子树（本地副本退役）。行 name=`{行号} {状态}: {文本}`（空侧 `(empty)`）。门禁 uia-d3-check：骨架 24 不变+双窗格 24 行逐行==引擎台账；负向 REACMP_D3=0 行消失被抓。**§6.10 的"裸自绘不进 UIA"已被自家决策 D3 推翻，勿再照旧论**。
- **BC 布局实测翻案（探针 textlayout/textscroll-en 系列，Job Object 串行零残留）**：详情=**双条在窗格下方**（h32+h15，横贯全宽）；overview=**左缘竖条**非底部（docs/20 §3 已修正）；点击行→**双 footer 同步变文本**（共享光标），各状态行底色 census **不变**（选中不铺底=实测，词级 mark 残差照旧）；BC 行号探针给 5 而引擎给 3=**U-layout-2 在案差异**，产品显示真源不吸收；**滚动通道全灭**（wheel/keybd/UIA 钮/轨道点均无位移=U-layout-1 开放项，不臆测）。
- **实现**：共享 `DiffViewState`（行/列/TopRow+Changed 事件）→点行=选行、双 footer chrome `LiveName` 同步 `{本侧 ltid/rtid}: {列}`（列=自家字形宽度换算，非拟合）、滚轮=**共享视口**双窗格同步（3 行/格=Windows 默认）+footer 不动；详情双条=选中行文本+状态读数（内容自家设计、peer=null）。**布局翻案修复**：attach 模式竖排叠放是潜伏缺陷→引擎模式 Grid：两 TTextEditor 子树左右分栏且**列取镜像**（tree-first=屏幕右 x=784 实测；UIA 序≠视觉序与 band 同族）、editor+details 混排竖排详情在下（DFM alBottom+实测 y808/824）；UIA 前序不变。
- **真实输入必须前台激活**：未 set_focus 的窗口 mouse.click 只触发激活不送达按下（首跑全静默）；门禁脚本先 set_focus。
- **门禁 uia-text-interact-check**（正负向全绿；共享视口断言=双窗格可见首行渲染同一 grid 行的**本侧** tint——直接比窗格像素会误判 orphan 行）；负向注入 REACMP_INTERACT_NEG=1 右 footer 失联被抓 2 违例。**全套 13 门禁复跑全绿**（211/845+410+290/13/12+7+5/12golden/tint/filter/dark/D3/interact）。docs/19 §6.12、docs/20 §5-D3+§6-3、docs/12 §6 已记。**未完**：查找 Ctrl+F 通道、左缘 overview 缩略条、U-layout-1/2。

**§6.18 Merge to/Swap 收口 + 布局根缺陷修复（2026-10-24）**：
- **Merge to 实测（4 轮 7 次串行探针零残留，merge-to-findings.json）**：单选
  Left/Right/Other:=Ctrl+S 落盘目标（4 文件切 Left 直接写 left.txt、OUT 哨兵
  原样无对话框；3 文件 Other 弹 BC 自家 `Save File on File System As - Output
  Side`、Esc 后切 Left 直写=§6.17 缺口关闭）；**窗口标题跟随目标文件名**
  （3 文件 Other 无路径回退 center）；Other: 旁路径框显示**当前**目标路径
  （§6.15 的 selected_tint 实为路径框激活底色，单选点=accent (0,95,184)）；
  Swap Sides=L/R 互换+色带换侧、C 不动、输出内容不变着色翻转（BC 工具栏
  Swap 的 UIA invoke 无效=物理点击才行，在案）；Session Settings 对话框结构
  探明（TSessionDialog/四 tab/Specs 帧几何）但**改文件重合并行为环未测→
  对话框实现=显式在案后续**。
- **实现**：MergeState.MergeTo/DestPath/DestTitle/SetMergeTo/SwapSides；路径框
  不设显式 UIA 名（路径文本即名）；标题 Changed 直写；工具栏加 Swap。新门禁
  uia-text-merge-to-check 三态（positive/mergeto/swap）全绿。
- **两个回归抓到的真缺陷（已修， 勿回退）**：①MenuMode 引擎态 `content` 根
  StackPanel 无界测量→Grid Star 行退化→缩略条槽位 2301 vs 条 729 错位
  （overview 门禁抓到）→**content 改 DockPanel LastChildFill**（UIA 前序不变）；
  ②uia-overview-check near() 的 numpy uint8 回绕（254-255→255）→int() 强转
  +色带带内多点采样（容忍选中行橙线）。content/filter 门禁须小 fixture
  （c_L/c_R），150 行 fixture row59 在视口外=在案。
- 全套回归绿：core277/cli465/离线 845+410+290/13/12golden/d3/interact/find/
  overview/dark/content/filter/merge 两档/merge-to 三态；Debug+Release 0 error。
  **下一步候选**：Session Settings 对话框（锚点已存）或 docs/20 矩阵的
  功能 5 HEX 双栏窗格（引擎 M7 已收口、纯表现层）。
- **BC 探针/harness 环境事实（复用勿再踩）**：BC 菜单弹层=TTBPopupWindow
  （非 #32768）；模态对话框开着时主窗 UIA 包装器 stale（ElementNotEnabled）——
  关对话框必须用对话框自己的 hwnd/按钮；pywinauto 无 Desktop.top_level()
  （枚举窗用 top_windows(pid)+handle 包装）；BC 工具栏钮 UIA invoke 可能无效，
  物理点击唯一可靠。本机：Git Bash `kill` 杀不掉 Windows 进程，残留
  reacmp-gui 锁 exe 致 dotnet build MSB3027——用 `taskkill //F //IM reacmp-gui.exe`。

**§6.19 Hex Compare 视图第一档（2026-10-24，功能 5 GUI 层）**：
- **实测（2 次串行活体零残留，hexview-findings.json）**：视图行模型=**16 字节
  2×8 组+16 字符 ASCII**（≠M7 报告 8 槽！行距 17.5px）；变更/孤儿字节=红字
  (255,0,0)+粉带(255,227,227) 逐字节着色（同行红黑混排）；缺槽=对角 hatch
  (230,230,230)；caret=青块(0,255,255) 在 ASCII 格、双窗格共享；窗格内容不进
  UIA；hex 状态栏无段计数；每侧独立路径栏+信息行；THexEditor 左
  [60,154,694,677]/右[758,154,690,677]、树序右先。
- **引擎**：core align_slots/slot_counts（平面槽流，交叉验证测试）；CLI
  `--hex3 L R out`（自家动词，@script 优先=merge3 先例）；JSON 布尔必须发
  true/false（0/1 数字会被 GetBoolean 炸）。**尾间隙槽序=M7：min(gl,gr)
  配对变更在前**（写测试预期先查 docs/14 §2）。
- **GUI**：HexMode.cs（HexPaneView owner-draw 无 peer+HexViewState 共享光标/
  视口+HexPalette 严格读实测 JSON）；MenuMode hex 引擎块+THexEditor attach
  （tree-first=右镜像）；ChromeHost 编辑器检测扩展 THexEditor+编辑器/工具栏
  上下分支（工具栏 Auto 行 0 在上，UIA 前序不变）。
- **门禁 uia-hex-check 正负向全绿**（几何+逐字节 tint+点击双窗格 caret 同步；
  REACMP_HEX_NEG 抓红）。全套回归绿：core278/cli144+206+118/离线 845+410+290/
  13/12golden/各活体门禁；Release 0 error。**在案**：hex 缩略条渲染、信息行
  文本、D3 hex 行暴露、Next/Prev Diff 钮。interact 门禁 wheel 步有偶发竞态
  （复跑 3× 稳定）。

**§6.20 Folder Compare 列视图第一档（2026-10-24，功能 3=MVP 关键路径收口）**：
- **实测（3 次串行活体零残留，folderview-findings.json）**：**一个全宽列表
  画两侧**（TDirTreeView），每侧 Name|Size|Modified+中央细缝；行带对齐
  （孤儿单侧渲染）；状态=**文字色**（same 黑/diff 红(255,0,0)/孤儿紫
  (106,0,213)/newer 灰(128,128,128)+新侧时间戳红）；斑马=奇数数据行
  (248,250,249)；**光标=浅蓝(168,205,241) 跟随点击**（C-selcheck 实锤）；
  Size=字节、**目录行=子树聚合（收起也预计算）**；时间戳不补零；目录在前。
- **引擎**：CLI `--dir3 L R out`（自家动词；JSON=reacmp-dir3/1 带 depth/
  status token/每侧 size+time）；ExpandPolicy::All 算聚合、**视图默认渲染
  depth 0**（=BC 默认收起带聚合），后续扩展层级无需重排通道。
- **GUI**：FolderMode.cs（FolderListView 全宽双画侧无 peer+FolderViewState
  单光标+FolderPalette 严格读实测 JSON）；ChromeHost 新增
  **BuildFolderRootArea**（folder 根树序日志在列表前、视觉在底）；编辑器
  检测扩展 TDirTreeView。**新视图接线两件套教训：根布局分支（folder 根第
  4 子≠TUiThumbnail 不走 BuildRootArea→整窗空白）+overlay 的
  MeasureOverride（缺→塌零）**——两处都被 smoke 截图抓到。
- **门禁 uia-folder-check 正负向全绿**（全宽+光标蓝首行+斑马/红/紫/灰+
  点击跟随；REACMP_FOLDER_NEG 抓红）。全套回归绿：core278/cli146+206+118/
  离线 845+410+290/13/12golden/全部活体门禁；Release 0 error。**MVP 功能
  1/3/11/13/15 GUI 关键路径全通**。在案：展开交互/双击子会话/TLogFrame
  内容/状态栏计数接线/中央比对列语义。

**docs/21 MVP GUI 收口设计定稿（2026-10-24）**：设计输入核实——folder
状态栏文本=spec 静态串（与门禁夹具数字巧合）；报告 GUI 挂点=8 视图
Session 菜单的 `{View} Report...`（845 台账已核）。五件设计+施工顺序：
A 状态栏 LiveName 接线 → B 工具栏文字按钮第一档（渲染在既有 ChromeElement
内=UIA 零变化/golden 不红；点击语义=第二档诚实呈现"无命令弹回"）→
C Session Settings 对话框（**探针 OK 行为环先行**，自家对话框 OK=重跑对应
引擎通道）→ D 报告向导（薄壳调 CLI 报告动词，**门禁=GUI 产物==CLI 直跑
逐字节**）→ E folder 展开。尾部 docs/20 §4-4 人工走查。施工从 A 开始。

**docs/21 A 件 ✅（2026-10-24 当日收口）**：folder 状态栏 Items[1]/[5]
=LiveName 引擎聚合（**可见行**文件数+字节和——BC 实测语义：收起目录不计；
SideTotals 在 FolderViewState）；[3]/[7]=DriveInfo free 活值（文形保留=
表现自设计）；无引擎路径静态串不动（12 golden 不红）。uia-folder-check
第三断言（4/24、4/26+free 形状正则）+ 负向 REACMP_FOLDER_SB_NEG 注入 999
被抓。**教训：门禁加新注入变量时 env 行必须同步补**（漏带=负向假失败）；
heredoc 写反斜杠正则用 chr(92) 构造。下一步=docs/21 B（工具栏文字按钮
第一档）。

**docs/21 B 件（2026-10-24，实现+树级验证收口；像素三模待桌面恢复）**：
- **工具栏文字按钮第一档落地**：ChromeElement 面渲染（Segoe UI 13、
  宽=字形+16px、**39px 高+2/3 边距=实测 44 行**（textlayout tree-step0）、
  3px 圆角、hover (245,245,245)/按下 (231,231,231)、亮字 (32,31,30)、
  **分隔条 1px**（docs/21 B 定案，不抄 BC 实测 6px））；渲染全在既有
  元素内部 → UIA 零变化（12 golden 逐字节=铁证）；radio 三钮实测底色
  照旧+文字叠加（strip/theme 门禁 most-common 采样不受字形污染，已核）；
  无名字钮/路径条保持空壳（图标集=后续独立项）；无命令钮按下弹回。
  **禁用态不做：chrome-matrix 每项只有 ct/cls/name，无 enabled 轴
  （845 enabled 轴是菜单项的）——docs/21 B 草案"chrome 数据带 enabled"
  与实情不符，已改记 docs/19 §6.21**。
- dark：dark.json 新增 `toolbar` 键（text 226/hover 43/pressed 53/
  divider 64，中性灰阶=gutter 家族+WCAG 注释）；Theme.cs 解析四色；
  `ChromeElement.Current` 静态挂接（MenuMode --theme 时设置）。
- 新门禁 **uia-toolbar-check（positive/negative/dark 三模）**：13 命名钮
  全在+39/44 几何+墨水断言（dark==dark.json toolbar.text ±25）+**树不变
  铁证（负向 REACMP_TB_NEG=1 面禁画布局不变 → preorder 386 节点与正向
  逐字节一致）**。
- **环境事故根因（重要复用勿再踩）**：活体探针全白+鼠标注入被拒
  （"no active desktop"）→ **根因=输入桌面是 Screen-saver（机器屏保
  锁定）**：WPF DirectX 面不经 DWM 到 PrintWindow（全白）、pywinauto
  鼠标拒动，**但 UIA 树/窗口几何完全正常**。判定法：
  `OpenInputDesktop` 名≠"Default"=像素门禁不可跑、树级门禁照常。
  排查中用过的 stderr 诊断/无条件红块/`false &&` 二分开关全部已清理
  （误编译错误源：Python `!r` 写进 C# 内插字符串）。
- 回归（可跑面全绿）：offline 845/410/290、dispatch 13、12 golden、
  core 278+5+1、cli 146+206+118、Debug+Release 0 error、零残留；
  toolbar-check 负向树一致绿；dark 模式对空白像素 exit 1=拒收垃圾实锤。
  **补跑清单（桌面恢复后）**：toolbar 三模+全套活体门禁串行 → 回填
  docs/12 工具栏行。下一步=docs/21 C（Session Settings，探针 OK 行为环
  先行——同样需要活体桌面，先补跑再开 C）。
