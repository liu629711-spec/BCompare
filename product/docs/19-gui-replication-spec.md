# 19 — GUI 复刻规格（功能 16 前置侦察，P1）

> **2026-10-22 路线变更（docs/20 定案）**："界面逐像素一致复刻"的目标已被
> **能力全继承、界面自设计**取代。本文全部实测成果（211 DFM 对照、四矩阵、
> 视图分派、灰态双层、chrome/骨架快照、§6.10/6.11 colors.json+filter-map）
> **归档为参考证据库**：行为语义与布局知识继续适用（docs/20 §2），像素级
> 对拍纪律不再作为验收判据（新判据见 docs/20 §4）。动 GUI 前仍先读本文——
> 它回答"BC 为什么这样设计"；docs/20 回答"我们怎么做自己的"。
>
> 目的：为"界面、UI、交互全部一致复刻"的核心目标建立**实测证据基础**，
> 划清"可对拍项 / 只能结构复刻项 / 必须活体测量项"三类，并给出活体窗口枚举
> 探针的执行方案。本文档**不是实现方案**；实现选型见 03，验收策略见 05。
>
> 纪律重申：所有结论来自 Oracle 二进制与双安装实测，不是截图目测。

## 1. 静态侦察成果（已完成，2026-10-20）

### 1.1 双安装 DFM 对照（本轮新增实锤）

工具 `tools/dfm-extract.py` 分别对两个安装的 `BCompare.exe` 解出全部 211 个
Delphi 设计期窗体流：

| 安装 | 路径 | 窗体数 | 控件对象 | 事件绑定 |
|---|---|---|---|---|
| reference（英文 5.2.6.32774） | `D:\bc-official\app\BCompare.exe` | 211 | 3,641 | 1,821 |
| current（中文重打包 5.2.1.32035） | `D:\BCompare\BCompare\BCompare.exe` | 211 | 3,642 | 1,819 |

结构 diff（按"清空字符串字面值后比较"）：
- **201/211 窗体逐字节相同** → 中文重打包**没有改动窗体结构**；本地化只发生在
  STRING 资源/运行时翻译层，与报告通道（norm-6 成对标签）同一结论。
- **10 个窗体有真实差异**（TABOUTDIALOG、TBCACTIONS、TDIROTHERFILTERITEMDIALOG、
  TEXPORTDIALOG、TFILEFORMATMANAGERDIALOG、THEXGOTODIALOG、THOMEVIEW、
  TPROGOPTIONSDIALOG、TREGVALDIALOG、TTABLEGOTODIALOG）。抽样核实为
  **版本构建漂移**而非汉化：如 `THEXGOTODIALOG` 差一行 `OnCreate = FormCreate`
  （5.2.1 有、5.2.6 删），`THOMEVIEW` 是布局项 Height/Top/Visible 调整。
  与既有在案事实一致（5.2.1 是 5.2.6 的旧构建汉化，见 docs/02）。

**规格含义**：GUI 规格以 **reference（5.2.6 英文）DFM 为唯一权威底本**；
current 的 10 处漂移按"旧版本行为"记录，不作为复刻目标（与 CLI 通道同政策——
金标准取英文安装，见 registry/version 通道先例）。

### 1.2 既有资产清单（`specs/ui/README.md` 为详版）

| 资产 | 位置 | 状态 |
|---|---|---|
| 211 DFM 解码（窗体树/几何/对齐/文字/事件名/图片索引） | `extracted/forms/*.dfm` + `forms-index.json` | ✅ 权威底本 |
| 中文版 DFM（对照用） | `extracted/_scratch/forms-zh/` | ✅ 本轮生成 |
| 动作目录（Caption/Hint/ShortCutStr/Category/Scope） | `T*ACTIONS.dfm`（14 个） | ✅ 完整 |
| 类骨架（VMT 直读 5,121 类，含视图/会话三元组） | `extracted/delphi-classes.json` | ✅ |
| 事件→代码链接（555/555 解析到地址，365 到单元） | `extracted/ui-event-map.json` | ✅ |
| 图标/位图/光标/PNG 资源（479 文件：74 icon、58 png、38 cursor、17 bmp、243 rcdata） | `extracted/resources/` | ✅ |
| STRING 资源 5,431 条（界面文案与格式化串） | `extracted/resources/strings.json` | ✅ |

## 2. 三类复刻面（本文核心结论）

### 2.1 可对拍项（静态即可判定一致性，可进自动门禁）

1. **窗体结构树**：控件类名、实例名、父子关系、TabOrder —— DFM 逐字节可比。
2. **控件几何**：设计期 Left/Top/Width/Height/Align/Anchors/Constraints —— 数值可比。
3. **文案**：Caption/Hint（含 `&` 加速键与 `|` 分隔结构）与 STRING 表 —— 字符串可比。
4. **动作语义**：14 个 `T*ACTIONS` 里每个动作的 Caption、Hint、`ShortCutStr`、
   Category、Scope、可见性条件（如 `DynVisible`）——这是**菜单/工具栏/快捷键的
   单一事实源**（见 §2.3）。
5. **事件绑定拓扑**：`OnClick = Handler` 名 → 处理单元（链接图已建）——交互语义
   的骨架可比。
6. **图标映射**：`Images = BcImages.MainImages` + `ImageIndex` + 图片资源字节 —— 可比。

这些全部**可以生成机器可读基线**（DFM→规范化 JSON→金标准），未来 GUI 实现的
结构层测试可以直接对拍，无需截图。

### 2.2 只能结构复刻项（不能逐字节对拍，需运行时观测）

| 项 | 原因 | 获取手段 |
|---|---|---|
| 主题渲染像素（亮/暗、125/150/200% DPI 位图合成） | `TBCIMAGES*` 12 变体已提取，但运行时合成结果非窗体定义 | 资源直接复用 + 活体截图像素对照（最后手段） |
| 运行时计算布局 | `FormResize` 等代码算出 | 事件名→反编译（语料已具备）+ 活体几何观测 |
| 动态创建控件 | 运行时 `Create` | 反编译 `FormCreate` |
| 自绘控件外观（`TUiVirtualListBox` 等） | VCL 自绘 | 逐类逆向（后端工作） |

### 2.3 必须活体测量项（DFM 给不出的关键结构 —— 本轮实锤的新边界）

**菜单/工具栏的完整层级不在任何 DFM 里。** 核验：211 个窗体中无设计期
`TMainMenu` 实例；类表存在 `TUiMainMenu`/`TUiMenuItem`/`TMenuPopulator`/
`TMenuUpdater`/`TBcExplorerMenu`，配合动作目录的 `Category`（Edit/Help/Mac/
MacWindow/Session/Tools…）字段 —— 证明 **BC 的菜单是运行时由 `TMenuPopulator`
按 Category/Scope 从 ActionList 生成的**。因此：

- 动作属性（快捷键、标题、提示）→ 静态可得（§2.1.4）；
- **菜单树的分组、顺序、分隔线、动态可见性规则** → 必须活体枚举；
- 同理：状态栏面板运行时文本、会话选项卡的动态构建、右键上下文菜单的触发条件。

## 3. 活体窗口枚举探针方案（P1 待执行，需确认后动手）

受控、只读、与 CLI 门禁同一进程纪律（严格串行 + Job Object 兜底 + 残留检查）：

1. **启动**：`D:\bc-official\app\BCompare.exe` 以默认 profile（临时
   `%APPDATA%` 重定向，避免污染用户配置）在 Job Object 内启动。
2. **枚举**：UI Automation 树遍历——
   - 主窗口菜单栏：每个顶级菜单展开→收集 MenuItem 文本/快捷键/启用态/分隔位置，收起；
   - 工具栏按钮（AutomationId + Name + ImageIndex 对照动作目录）；
   - 状态栏面板；Home 视图的会话列表结构；
   - 逐一打开各视图（Text/Hex/Table/Reg/Version/Folder）记录窗口类名与客户区结构。
3. **弹窗**：对 211 窗体中的高频对话框（会话选项、比较选项）以脚本路径触发并枚举控件树，与 DFM 基线对拍（这是 §2.1 的"活体验证"步骤）。
4. **收尾**：关闭 Job，`tasklist //FI "IMAGENAME eq BCompare.exe"` 残留必须为零。
5. **产物**：`extracted/live/` 下的 UIA 快照 JSON → 生成 `docs/19` 附录菜单基线。

风险与对策：中文安装与英文安装同机运行 → 串行且先英文后中文；弹窗触发可能写
profile → 重定向到临时目录并事后删除；UIA 展开菜单需前台焦点 → 固定屏幕区域、
避免用户交互时段执行。

### 3.1 探针实做结果（2026-10-20，已执行）

路线试错（全部实测记录，后续勿再浪费时间）：
1. **原生 HMENU 路线失败**：`GetMenu` 对每个窗口返回空——菜单栏是 VCL 自绘子窗
   `TUiMainMenu`，弹出菜单是独立顶层窗口 `TTBPopupWindow`（非 `#32768`）。
2. **UIA ExpandCollapse 失败**：菜单项的 `ExpandCollapseState = LeafNode (3)`，
   `Expand()` 无效；UIA 桥不实现展开。
3. **键盘事件失败**：`keybd_event` 的 Alt/F10/方向键序列在此环境下不可靠送达
   （`GetGUIThreadInfo.hwndMenuActive` 恒 0）。
4. **可用路线 = `click_input`（真实 SendInput 点击顶级项）→ 等待
   `TTBPopupWindow` → 对该窗口取 UIA 树 → RawViewWalker 遍历 `Menu` 子项**。
   子菜单嵌套经**悬停**（SetCursorPos）物化。安全纪律：只点顶级项开/关、只悬停，
   **从不调用（Invoke）任何命令项**。
5. **两个必须实现的护栏**（各修一轮才收敛）：
   - 弹窗**归属校验**：popup 矩形必须横向覆盖所点顶级项，否则是上一菜单的串位
     残留（曾导致 Session 抓到 File 内容）；
   - **确认式关闭**：关不掉则重复点击+ESC+`WM_CANCELMODE` 兜底，否则残留菜单把
     后续全部菜单引串（并导致进程关不掉、需 Job 兜底强杀）。

产物（严格串行、每轮一次启动、Job 兜底、残留归零核验）：

| 文件 | 内容 |
|---|---|
| `extracted/live/ref-5.2.6-uia/gui-home-en.json` | Home 视图 4 顶级菜单（Session 11/View 3/Tools 11/Help 9），全项含快捷键、AccessKey、启用态、分隔线 |
| `extracted/live/ref-5.2.6-uia/gui-text-session-en.json` | 文本会话 7 顶级菜单（Session 27/File 6/Edit 21/Search 20/View 24/Tools 11/Help 9） |
| `extracted/live/ref-5.2.6-uia/uia-snapshot.json` | Home 整树 UIA 快照（含 12 个 `THomeTaskBtn` 与 13 项会话树） |
| `extracted/live/cur-5.2.1-zh/gui-home.json` | 中文安装文本会话全 7 菜单（U-gui-3 活体文案） |

**对拍核验（活体 vs DFM 动作目录）**：Home 34 项 + 会话菜单逐项映射到
`T*ACTIONS.dfm` 的 `TUiAction`（352 动作总数）；快捷键以 `名称\tCtrl+…` 内嵌在
UIA name 中送达，与 DFM `ShortCutStr` **集合级全等（0 差异）**；AccessKey 与 DFM
Caption 的 `&` 位置一致。唯一名外项 = `About Beyond Compare`：其标题不在 DFM，
实锤取自 STRING 资源表 3954 index 504 的格式串 `About %s`（运行时填产品名，
`extracted/resources/strings.json`）——归入"运行时构建"类而非动作目录缺项。
**这实锤了 §2.3 的 TMenuPopulator 假说**：菜单内容确实 100% 来自动作目录
(Category 分组: Session/View/File/Edit/Search/Tools/Help)，活体基线可作产品权威。

**双语活体对照（U-gui-3 部分定案）**：EN↔ZH 文本会话 7 菜单的**结构逐位相等**
——顶级顺序、每个菜单项数（27/6/21/20/24/11/9）、View 菜单分隔线位置
`[3,6,8,13]` 全同；只有文案与 AccessKey 字母本地化（`Show All↔显示全部`，
`&Ruler↔标尺(R)`）。→ 中文界面 = 同一棵树 + 中文标签表；**标签表可直接从
`extracted/live/cur-5.2.1-zh/` 采集**（菜单文案）+ DFM/STRING 资源（对话框文案），
U-gui-3 的"外部补丁"疑点就此排除（本地化不改变结构，来源在资源层，定位细项仍开放）。

**视图差异实锤**：Home 的 View 菜单只有 3 项（会话管理面板开关等），文本会话的
View 有 24 项——**同一 Category 的可见性随视图会话类型变化**，产品实现必须按
"当前视图 + 会话状态"驱动菜单可见性，不能只按 Category 静态排布（这正是 DFM
`DynVisible` 标志的运行时含义）。

### 3.2 全 12 视图活体菜单矩阵（2026-10-20，`extracted/live/menu-matrix.json`）

每视图一次启动采齐（严格串行、`--task` 走 Home 任务按钮开空会话、`active_view`
逐轮用 UIA 树里的 `T*View` 类坐实）：

| 视图 | active_view | 顶级菜单集 | 项数(去分隔线) |
|---|---|---|---|
| Home | THomeView | Session/View/Tools/Help | 8/3/9/7 = **27** |
| Text Compare | TTextCompareView | Session/File/Edit/Search/View/Tools/Help | 21/6/17/16/20/9/7 = **96** |
| Text Merge | TTextMergeView | 同上 7 集 | 19/3/17/21/28/9/7 = **104** |
| Hex Compare | THexCompareView | 同上 7 集 | 20/6/8/7/13/9/7 = **70** |
| Table Compare | TTableCompareView | 同上 7 集 | 20/6/18/11/14/9/7 = **85** |
| Picture Compare | TPixCompareView | **无 Search**（6 集） | 20/4/1/·/16/9/7 = **57** |
| Registry Compare | TRegCompareView | 7 集 | 21/2/9/5/12/9/7 = **65** |
| Version Compare | TVerCompareView | 7 集 | 20/2/2/5/10/9/7 = **55** |
| Folder Compare | TDirCompareView | **Actions 顶替 File**（7 集） | 23/·/9/5/22/[Actions 23]/9/7 = **98** |
| Folder Merge | TDirMergeView | 同 Folder | 21/9/5/19/[Actions 7]/9/7 = **77** |
| Folder Sync | TDirSyncView | 同 Folder | 18/6/5/6/[Actions 3]/9/7 = **54** |
| Media Compare | TMediaCompareView | 7 集 | 21/3/2/5/10/9/7 = **57** |

**四种顶级菜单形态**（`TMenuPopulator` 的 Category 投影随会话类型切换）：
1. Home：`Session|View|Tools|Help`
2. 常规比较/合并：`Session|File|Edit|Search|View|Tools|Help`
3. Picture：无 `Search`（图片无文本搜索）
4. 文件夹族：`File` → **`Actions`**（Copy/Delete/Rename/… 归入 Actions 类目）

**恒定项实锤**：`Tools`=9、`Help`=7 **全部 12 视图恒定**（与会话类型无关的全局命令）。
其余每个 Category 的**项数随视图翻转**（如 Session 18–23、View 6–28），产品菜单必须
按 `(view, session-type)` 双因子驱动，不能只按 Category。

### 3.3 工具栏/状态栏活体基线（`extracted/live/chrome-matrix.json`）

同一批快照的 UIA 整树已含工具栏/状态栏（**U-gui-4 就此收口，无需额外启动**）：
- **主工具栏**（每会话第一条 `TUiToolbar`）逐视图标签序列已采全，例：
  Text Compare=`Home|All|Diffs|Same|Context|Minor|Rules|Format|Copy|Next Section|…`（20 项）；
  Folder Merge 首栏 30 项含 `Same OK|Favor Left|Favor Right|Merge|To Output`（合并专属）；
  Picture=`Home|Tol|Range|Blend|Minor|…`（图片专属 容差/混合）；Folder Sync 仅 13 项（最简）。
  每窗格另有 3–4 项子工具栏（`TUiSpecComboBox`+按钮）。
- **状态栏面板**：Text Compare 主状态栏含 `Same | \tInsert | Load time: 0.35 seconds`，
  每窗格状态栏含行列位置 `1: 1` + 编码 `Default text`；文件夹视图状态栏 8–12 项（列多）。
- **Home 无工具栏/状态栏**（属实：主页界面无比较命令条）。

### 3.4 可见性/禁用谓词收口（U-gui-2，2026-10-20：活体数据路线，不反编译）

先记录死路（勿重试）：REA ephemeral Ghidra 会话里 BC 过程**无符号名**
（`search_procedures` regex `Populat|MenuUpdat|CanExecute` 返回空）；VMT −0x70
自动表指针定位成功（`TMenuPopulator@0x140417b48`、`TMenuUpdater@0x14041e2b0`），
但 ui-event-map 式"名串后 0x40 字节找代码指针"启发式在这两个类的方法表上
**只命中类名本身**（published 方法极少——逻辑在虚方法/普通方法里）。逐个反编译
`TMenuUpdater` 虚表是 P2 级的大工程，而 **P1 需要的是行为规格，活体数据已经给出**。

两条独立机制，活体分离如下：

**A. 可见性 = `TMenuPopulator` 的静态能力掩码**（`extracted/live/presence-matrix.json`）：
264 个 (菜单, 项) 对中 **238 项的"出现在哪些视图"是部分集**——每项一张精确的
视图存在性表（如 `Webpages` 仅 Text 双视图；`Rotate Clockwise` 仅 Picture；
`Conflict/Take Left/Center/Right…` 仅 Merge；`Next Difference Bytes/Cell/Item/Row`
= 各视图专属的差异导航动词）。**产品必须逐格复刻这张表**——这就是可见性谓词的全部
内容，已由行为实测穷举，无需读代码。存在度分布（12 视图）：**24 项全视图通用**
（New Session/New Tab/New Window/Open Session/Load·Save Workspace/Close Tab/Exit…），
7 项出现于全部 11 个会话视图（Save Session/Session Settings/Locked/Clear Session/
Swap Sides/Toolbar 等，Home 无），其余 233 项按
{比较族共享} > {Merge 族（Text/Folder Merge）} > {视图专属}（139 项只属于单一视图）
收窄。产品实现=先建"视图能力集"，每项登记其视图集（直接抄 presence-matrix）。
注意实测怪癖：Folder Compare 的 **Actions 菜单逐项重复了 Session 菜单**
（New Session…Exit 全列）——不是采集错误，是 BC 实况。

**B. 灰显 = `TMenuUpdater` 的内容态谓词**（`extracted/live/enabled-matrix.json`，
采集态=空/新载会话）：232 项恒可用；**25 项在所有出现的视图都灰**——谓词按
内容状态干净归组，正是产品置灰逻辑的规格：
- **无编辑历史**：Undo/Redo（可编辑视图：Text/Merge/Hex/Table/Reg）
- **无选区**：Sort…/Compare Selection to Clipboard/Copy Filename/Refresh Selection
- **无导航历史**：Back/Forward（Folder 系）
- **会话未载内容/新建**：Save File/Save…/Export All…/New Key/New Value/Rename/
  Exclude/Compare Contents/Ignored/Auto Sync/Clear Conflict Section, Next
- **媒体未播放/未载**：Play/Play Both
- **无差异光标**：Compare Metadata/Reset Difference Offset/Center Pane(部分)
另有 7 项跨视图**可用性翻转**（Copy/Cut/Paste/Delete 的编辑能力差、Isolate 仅
双视图合并、Copy to Right 不含 Reg）= 能力×状态混合，实现按 A 表先分视图，
再套 B 组状态谓词。

**结论**：U-gui-2 的"精确谓词"以**活体穷举**收口（比反编译更权威：直接是用户
可见行为）；`TMenuUpdater` 内部实现细节降级为 P2 兴趣项。产品验收 = 对
presence-matrix + enabled-matrix 逐格断言。

## 4. 对 P1（UI 测试基础设施）的直接输入

- 结构层测试**不需要截图**：用 §2.1 的六项对拍基线（DFM JSON 金标准 + 动作目录）
  即可验证"界面骨架一致"。
- **结构层对拍门禁已建（2026-10-20，`tools/ui-structure-check.py`，P1 骨架第一件）**：
  被测窗体描述与金标准**同构**（`{name, cls, props, children}`——即 ADR-7 数据驱动
  窗体的输出契约，任何框架导出这个形状即可进门禁）。三级比对：`structure`
  （类/实例名/父子层级+声明顺序/Caption·Hint·HelpKeyword）、`layout`（+几何布局键
  13 个）、`full`（全属性含事件绑定）。差异逐条带**路径**输出，退出码 0/1/2。
  已验证：自测 8/8（含"Left 在 structure 级必须无差异、layout 级必须抓到"的分级
  隔离用例）、TTEXTVIEW 双级往返 0 diff、变异必抓 rc=1。菜单/chrome/presence/enabled
  四矩阵的活体断言路线=`tools/live-gui-probe.py` 采产品同格式快照后对
  `extracted/live/*-matrix.json` 逐格比（探针 harness 本身已双向可用）。
- **WPF 端到端验收闭环已打通（2026-10-20，docs/03 定案 3B）**——见 §6。
- **结构基线已生成（2026-10-20，`tools/dfm-baseline.py`）**：文本 DFM 全语法面
  （scalar/quoted-string `''` 转义/ident/set `[..]`/inline-list `(..)`/collection
  `< item..end >`/binary `{N bytes}`）解析为规范化 JSON，**211/211 零错误**：
  - `extracted/guibaseline/forms-{en,zh}.json` —— 窗体树（对象计数 en 3,641 /
    zh 3,642，与 forms-index 逐位一致；事件绑定 1,821 逐条一致；确定性：EN 重跑
    sha256 相同；EN/ZH 对拍=201 同 + 与 §1.1 完全相同的 10 个漂移窗体）；
  - `extracted/guibaseline/actions-{en,zh}.json` —— 动作目录 381 项（caption/hint
    含 `|` 结构/shortcut（**96 项，纯 Windows 键位**，MacShortCutStr 不污染——
    §3.1 对拍用的旧正则曾误吞，基线已修）/category/scope/Visible·DynVisible·Checked
    （DynVisible 仅 2 项：ColListAction、WorkspaceLoadListAction））；
  - **13 个 Category**：Actions/DropDown/Edit/Favorites/File/Help/Mac/MacWindow/
    Search/Session/Toggles/Tools/View —— 即 `TMenuPopulator` 的分组事实源。
- 交互语义测试用 §2.1.5 的事件链接表逐条生成断言。
- 视觉层（§2.2）留到实现后期。**注意**：已提取的图标/位图/PNG 仅作**逆向参考与
  对拍基准**，不得直接打包进产品（docs/01 在案纪律：不复制 BC 资源）；产品图标
  资产须自绘并以提取件为像素级验收目标。
- §2.3 的活体基线是菜单/快捷键一致性的**唯一权威**，先于任何 GUI 实现代码产出。

## 5. 残差与开放项

- **U-gui-1**（已收窄，产品影响=零）：10 个版本漂移窗体与中文 Help 缺项的**机制已定位**：
  中文 5.2.1 安装自带的 DFM 动作目录**与英文逐词相同**（Category=Help 恰 7 项、
  caption 逐字一致，含 `Check for &Updates`/`&Enter Key...`/`&Contents` 等）——
  重打包没有删动作、也没改任何窗体。缺项发生在**运行时过滤**（老构建代码行为或
  补丁级修改；`Contents` 依赖 CHM 帮助文件、`Enter Key/Check for Updates` 涉及
  许可与更新——重打包有隐藏动机，但无证据分离两者）。产品复刻英文 5.2.6 的
  Help 语义（既有"英文安装为权威"政策），本残差不阻塞任何实现。
- **U-gui-2**：~~`TMenuPopulator` 的 Category→菜单位置映射规则未读~~
  **已收口（§3.4，活体穷举路线）**：可见性=presence-matrix（238 项逐视图存在表），
  灰显=enabled-matrix 六组内容态谓词（无编辑历史/无选区/无导航历史/未载内容/
  媒体未播/无差异光标）。`TMenuUpdater` 内部实现降级为 P2 兴趣项；反编译路线
  的死路记录在 §3.4 开头（无符号名+RTTI 启发式失配），勿重试。
- **U-gui-3**：**结构面已定案**（EN↔ZH 逐位同构，仅标签/AccessKey 本地化）；
  开放项收窄为"中文标签表来源在资源层的具体位置"（STRING 资源节 vs 代码内
  表），GUI 中文界面可先以 `extracted/live/cur-5.2.1-zh/` 实测文案为准。
- **U-gui-4（已收口）**：工具栏/状态栏基线在 §3.3（同一批快照整树已含，
  跨 12 视图汇总入 `chrome-matrix.json`，无需额外启动）。
- **U-gui-5（已收口 → §6.9 分派表）**：命令行打开 `.reg` 文件**不会进注册表视图**
  （实测落到 Text Compare / 甚至 Text Merge）；`/fv="Registry Compare"` 亦未被
  识别（官方 command_line_reference.html 记载该选项，实测被当成文件名 → 打开
  名为 `/fv=Registry Compare` 的文本视图）——**BC GUI 只按扩展名分派会话类型，
  文档的 /fv 对 5.2.6 实测无效**。可靠开视图方式=Home 任务按钮（`--task` 路线）。
  注册表/版本比较的真实触发是 HIVE 路径或新建空会话（`New Registry Compare`），
  非文件对。产品的视图分派规则须按此实测，勿照抄帮助文档。

---

## 6. WPF 端到端验收闭环（2026-10-20 实测记录，ADR-8 定案 3B）

产品工程：`product/gui/WpfHost/`（`net8.0-windows`，SDK 8.0.422 就绪）。
**两层闭环都跑通，产品与 Oracle 共用同一套 harness 与同一份同构契约**：

### 6.1 结构层（离线，ε=0）

`reacmp-gui <descriptor> [--form N] --dump <out>`：渲染器把 descriptor 建成
WPF 树后 `--dump` 反向产出同构 JSON。五窗体验证（TABOUTDIALOG / TINFODIALOG /
TKEYUPGRADEDIALOG / TSNAPSHOTDIALOG / TQUICKCOMPAREDIALOG）**全部 0 差异**过
`tools/ui-structure-check.py --level full`，且 dump 过程**逐节点校验保真**
（模型节点必须在视觉树里带 Descriptor 标签、Canvas 几何必须与模型一致、
文字必须等于 Translate(Caption)）——任一不符 problems>0 且退出码 1。

负向验证：变异 descriptor（改 Left、改 Caption）→ dump 忠实携带变异、
结构门禁抓出 2 条 prop-value 差异（Golden Left=32 vs 82、Caption 定案值 vs
`__MUT__`）→ 证明链路不是"恒过"。

### 6.2 活体层（UIA，product self-check）

`tools/uia-selfcheck.py`：拉起 `reacmp-gui <descriptor> --show`，等
`HwndWrapper*` 窗口，**用与采集 Oracle 基线完全相同的 pywinauto UIA 路径**
遍历产品窗口，断言每个具名 descriptor 节点都在活体树里且文字一致。
TABOUTDIALOG：23/23 节点全命中（Window/Text/Edit/CheckBox/Button 语义级别
全部正确）。**PanelHost 定制 AutomationPeer 是必要条件**（见 6.3）。

### 6.3 第一个 WPF 坑（记录，防再犯）

WPF 布局容器（`Border`/`Canvas`/`ContentControl` 默认 peer）**不会进 UIA control view**
→ PanelView/BottomPanel/UnregisteredPanel 等 7 个容器节点在活体树里消失
（结构门禁却看不出任何问题——它测的是 descriptor 层面）。修复：`PanelHost`
（`ContentControl` 子类 + 自定义 `FrameworkElementAutomationPeer`，
`IsControlElementCore()=true`、ControlType=Pane、ClassName=Pane）。
**教训**：结构层与活体层必须都测——本例中 offline 绿、live 红，差异只在活体层可见。

### 6.4 下一步（P1 的主体）

1. 扩展渲染器类覆盖（TFILEREPORTDIALOG 等一节点壳 + TDIRSESSION*FRAME 会话页
   框架，对齐 docs/19 §3.2 视图矩阵的顺序做菜单系统）。
2. 把菜单轴接到数据源：`extracted/guibaseline/actions-*.json` + presence-matrix
   驱动菜单树（TUiMainMenu 等价物 = WPF Menu + MenuItem）。
3. 视图分派严格按 U-gui-5 实测（扩展名→会话类型），勿照抄帮助文档。
4. 引擎边界：CLI/报告引擎保持 Rust 既有进程边界（docs/03），GUI 经进程/F
   FFI 调用。

### 6.5 批量验收（2026-10-20 同日）：**211/211 全绿**

`tools/ui-batch-accept.py`：对全部 211 个金标准窗体逐个执行
render→dump→结构门禁，输出通过/失败分类。**`full` 级 211/211 通过**
（连跑两次稳定），`structure` 级同样 211/211；UIA 自检保持绿。
过程中修掉两个渲染器/校验问题（均记录防再犯）：

1. **DataModule 窗体的 Window MinHeight 陷阱**：`T*ACTIONS`/`T*IMAGES`
   （Height=291/320）被 WPF Window 的最小高度规则顶到 300 → fidelity 失败。
   修法：非 Dialog 根一律建离屏无边框窗口（`WindowStyle.None` + `Left/Top=-4000` +
   `MinHeight=1`），窗体自身尺寸由画布承载。
2. **根节点 Left/Top 不是契约数据**：BC DFM 的根 Left/Top 是屏幕/父坐标，
   校验器却拿窗口屏幕位置比 → 13 个 Frame 类全挂。修法：fidelity 校验只对
   画布内子节点的 Left/Top 生效，根节点跳过（Width/Height 仍校验）。

**覆盖含义**：211/211 证明的是**描述符契约零丢失**（渲染器完整承载每个
节点的类/名/全属性/子序/画布几何），不是视觉保真——后者按 §2.2 属实现期
逐步收敛项。下一里程碑=菜单系统（actions + presence-matrix 驱动）。

### 6.6 菜单系统（2026-10-21）：**离线台账 12/12 + 活体顶栏 12/12 全绿**

数据驱动菜单 = WPF `Menu`（`TUiMainMenu` 等价物），完全由 Oracle 实测数据
生成，无任何逐例硬编码。管道：

```
presence-matrix.json(262 行) + item_order + top_menus_per_view + view_forms
  + actions-{en}.json(515 复合键) + top_access          （全部 extracted/live、guibaseline）
        │ tools/…gen_spec → extracted/_scratch/menu-spec.json（per-view 字典）
        ▼
WpfHost --menu-spec spec.json --view NAME [--dump ledger.json] [--show]
  MenuBuilder.Build：presence 决定成员 → view_forms 决定动作来源窗体 →
  item_order 决定序 → ExpandFormat/NormalizeShortcut/InjectKey 决定文本
        ▼
门禁1（离线）：ledger vs presence-matrix 的 item_order —— 12/12 视图
  （Home 4 菜单 27 项 … Text Merge 7 菜单 104 项）全部序+标签一致
门禁2（活体）：tools/uia-menu-check.py 起产品窗口读真实 UIA 树，比
  顶栏标签序 + 每菜单 AccessKey —— 12/12 绿（含 Folder 系 Actions、Picture 无 Search）
```

**实测规则（全部有出处，进渲染器为常量+注释）**：
- **presence 权威，Category 不权威**：成员资格以活体 presence-matrix 为准
  （`Show All` Category=Favorites 但活在 View 菜单）；Category 只作动作来源。
- **每视图挂载窗体集不同**（`view_forms`）：Folder 系 =
  TBCACTIONS+TDIRBASEACTIONS+TDIRACTIONS+TSESSIONACTIONS，Text 系 =
  TBCACTIONS+TTEXT*+TSESSIONACTIONS；同名动作按窗体集过滤（OpenAction 在
  TBCACTIONS='&Open Session'、TFILEACTIONS='&Open File...'，复合键保变体）。
- **顶层菜单集是 per-view 的**（四变体：Home=4、标准=7、Picture=6 无 Search、
  Folder 系 File→Actions）——早期把 Text Compare 的 flat 数组写死进 spec，
  导致批量 8/12；改 `top_menus_per_view` 后 12/12。
- **顶菜单 AccessKey = 首子项 AccessKey**（`top_access`，实测随视图变：
  Search→t/c/n）。
- **快捷键序 = Ctrl+Alt+Shift**（活体 UIA 实测，非直觉的 Ctrl+Shift+Alt；
  DFM 是 Pascal 声明序 Shift+Ctrl+O 需重排）。`(?<!Mac)ShortCutStr` 防 Mac 键污染。
- **运行时格式符**：`About %s`→'About Beyond Compare'、`%0:s &Info`→'Text Compare
  Info'（`ExpandFormat`，正则 `%\d*:?s` 用视图名展开）。

**WPF 坑（均记录防再犯）**：
1. `InputGestureText` 不进 UIA Name → 必须 `new KeyBinding(cmd, key, mods)` 真注册
   （参数序是 command, key, modifiers）。
2. 默认 MenuItem peer 的 Name 带 `_` 标记、AccessKey 带 `Alt+` 前缀 → 自定义
   `BcMenuItemPeer.GetNameCore()` 剥 `&_` 并追加 `\t<gesture>`（对齐 Oracle 格式），
   `GetAccessKeyCore` 回单字母；`IsControlElementCore()=true` 首批漏写导致菜单项
   整体从控制视图消失。
3. WPF `Menu` 报 control_type=`Menu` 而非 `MenuBar`；OS 标题栏系统菜单报
   `MenuBar`（单孩子'系统'）——同一陷阱在 BC 探针出现过两次，选择器按子数≥2 择应用栏。
4. 活体子菜单展开需要真实前台（AttachThreadInput+Alt 助推在交互会话可用；
   后台服务进程被 OS 前台锁挡）→ checker 分两档：默认顶栏断言，`--expand` 走
   子菜单（需交互会话）。popup 打开后旧 UIA 引用失效 → 每次开/关后 `menu_state` 重读。

**灰态接线（同日追加）**：enabled-matrix 264 行并入 spec（`enabled` 块，标签剥
`	` 后与 presence 264/264 对齐）。实测语义（captured_state=空会话基线）：
`always-enabled`→在场即可用；`view-capability`→按视图列表**静态**置灰（等价
TMenuUpdater 能力掩码）；`state-dependent`→仅在捕获的空会话视图置灰、有内容即
翻转——台账重放同一基线故规则一致。渲染器 `IsEnabledIn()` 接线，ledger 加
`enabled` 字段。**离线门禁升级：845 项（12 视图逐项 标签+序+enabled）与 12 份
Oracle 快照对拍 0 违例**；灰态总数 56 = 矩阵 disabled 并集 56（零幻影零遗漏，
非恒过）；活体顶栏回归仍 12/12、零残留。

**残差**：子菜单逐项（标签+键+序）的活体 `--expand` 批量核验待在交互会话跑一次
（离线台账已覆盖同样内容，enabled 亦可在 expand 档下顺带核 UIA IsEnabled）；
`state-dependent` 谓词随**会话内容**翻转的活体复测（需加载真实差异/选区/历史）
未做；菜单图标尚未接渲染器——属 P1 后续。

### 6.7 工具栏/状态栏 chrome 接线（2026-10-21）：**离线 410 三元组 + 活体 12/12 全绿**

U-gui-4 的活体基线（`chrome-matrix.json`）直接进渲染管道，与菜单同一套纪律：
数据驱动、零逐例硬编码、双门禁。

- **数据**：`gen_spec2.py` 把每视图的 `toolbars`/`statusbars` 行（有序
  `(control_type, class, name)` 三元组）原样嵌入 `menu-spec.json` 的 `chrome` 块。
  全 12 视图共 410 项，Home 为空（属实：主页无命令条）。
- **渲染**：`ChromeHost.cs` 的 `ChromeElement`（Control 子类）+ `ChromePeer` 让
  UIA 身份完全由数据决定：`GetAutomationControlTypeCore/GetClassNameCore/GetNameCore`
  三属性逐字节还原 Oracle 观测（含 BC 的类名如 `TUiTreeButton`/`TUiSpecComboBox`）。
  行容器用 `PanelHost` 包裹（布局 peer 会被剪掉的同一坑）并以
  `AutomationId = chrome:{tb|sb}:{i}` 可寻址——活体校验按 id 定位行，不与
  DockPanel 的视觉顺序耦合（tb 全部 Dock=Top 顺序、sb 逆序 Dock=Bottom，与
  BC 的窗体几何一致）。
- **离线门禁**：产品 ledger（bundle 格式 `{view, items, toolbars, statusbars}`）
  逐三元组对拍 chrome-matrix = **410 项 0 违例**（菜单 845 项同步回归 0 违例）。
- **活体门禁**：`uia-menu-check.py --chrome` 起产品窗口读真实 UIA 树，按
  AutomationId 收集行、比 (ct,cls,name) 序列 = **12/12 视图全绿**。
  首跑抓到一处真实缺陷：`RadioButton`（Merge 视图 "Other:"）不在 ct→
  AutomationControlType 映射表里，落到 default 的 Custom → Oracle 报
  `('RadioButton','TUiRadioButton','Other:')` vs 产品 `('Custom',...)`。
  补映射后 12/12。这正是"活体层必须测"（§6.3 教训）的第 N 次验证：离线台账
  忠实重放 spec，而活体对拍才证明 WPF peer 真的把数据翻译成了 UIA 事实。
- **状态**：菜单（成员/序/标签/快捷键/AccessKey/格式展开/灰态）+ chrome（工具栏/
  状态栏结构）两轴的静态面全部收口。残差：Merge 视图 `TUiRadioButton` 的选择态、
  窗格子工具栏 `TUiSpecComboBox` 的内容项（快照里为空名）、chrome 按钮图标、
  状态栏运行时文本（Load time 等随会话变化，属动态面）。

### 6.8 内容视图骨架接线（2026-10-21）：**290 节点离线+活体双 12/12 全绿**

把每个视图快照的 `home_tree`（扁平深度前序表）重建为嵌套树，按**剪枝规则**（=测量
基准，全部有出处）提取内容骨架：剪掉 TUiMainDock 子树（菜单轴=§6.6）与 TitleBar
（OS/系统菜单）；只保留 BC 类名非空的节点（匿名叶子 Button/Separator/Text 已由
chrome 行/菜单台账覆盖，避免双重计账）；TUiToolbar/TUiStatusBar 容器消费预分配的第
i 条 chrome 行且不再下潜；TViewForm 窗口节点不比对（WPF 报 HwndWrapper，属已知身份差）。

- **数据**：`extracted/_scratch/skel.py`（提取器，含行消耗断言）→ spec `skeleton` 块，
  12 视图 290 节点。Text Compare 骨架含实测窗格几何：详情窗格(TTextDetailsEditor×2+
  滚动条) + 双 TUiPanel 列（每列 TTextEditor+子工具栏+窗格状态栏）+ TUiThumbnail。
- **渲染**：ChromeHost 的 `ChromeContainer`（容器也带自定义 peer，三元组全数据驱动）；
  行宿主复用 `chrome:{sec}:{i}` AutomationId（骨架内嵌行与 chrome 台账同一物理元素，
  **零重复渲染**——旧 §6.7 的顶层独立行被骨架取代）。
- **双门禁**：离线台账 skeleton 段逐前序三元组对拍 = **290/290**（同时菜单 845 +
  chrome 410 回归 0 违例）；活体 `--skeleton` 档读真实 UIA 树（跳过规则：菜单/标题栏、
  chrome 宿主不下潜）= **12/12**。
- **又抓到一例真实缺陷**：Picture/Media 的 `TUiTrackBar` 在 Oracle 报 ct=Slider，
  产品落 default=Custom → 补 Slider/Spinner/ProgressBar 映射后 12/12。至此
  ct→AutomationControlType 覆盖两份快照的全部词汇
  （Pane/Edit/Button/Tree/ToolBar/StatusBar/ScrollBar/Slider/ComboBox +
  chrome 项的 Separator/MenuItem/Text/RadioButton/Custom/MenuBar）。
- **教训固化**：Python 默认参数可变对象跨调用共享（`ti=[0]`）会污染行消耗计数——
  行配对断言（assert used==total）把这类状态 bug 变成显式失败，不是静默错位。

**残差**：骨架节点几何（rect 已采但未作契约——VCL 尺寸随窗口变化，属实现期收敛）；
TViewForm 窗口身份别名；窗格内文本内容（编辑区文字/行号）属动态面。

### 6.9 视图分派接线（2026-10-21）：**7/7 实测格重放 + 活体标题 2/2 逐字匹配**

回答"源码不是有了吗，逆向不出来吗"的一次完整取证实验——结论：**行为真相仍以最
小实测为准，RE 只贡献静态线索**：

- **RE 可行性实证**（Ghidra 会话，BCompare.exe sha 4e44c5…）：
  1. `Picture Compare` 字符串→xref→32 字节注册壳（伪码可读）；
  2. 但类型注册经**函数指针表**，`FUN_141197940` 静态调用者=空——调用图碎；
  3. 注册 API `FUN_1400144c0` 的调用者 **1300+**（输出截断）——接收者过度通用，
     穷举甄别成本远超探针；
  4. 逐函数反编译一次 30 分钟超时——纯 RE 定案不现实。
  有价值的静态副产品：掩码串 `*.htm;*.html;*.xml;*.jpg;*.gif;*.png`@0x140ef0870
  （Picture 家族候选）——**只记录为 hint**（未行为实测，不入分派格）。
  早前 campaign 的 190 单元名表（ViewFile/BcFileFormat/TextSession…）与本次
  `MediaContent.pas` 命中印证分派代码在 `BcFileFormat/ViewFile` 一带。
- **实测取证**：整张分派表需要的唯一缺口格=**未知扩展名兜底**（负格大多已被
  12 份快照+U-gui-5 覆盖）。合并探针一次启动落定：`.zqq` 文件对 →
  **Text Compare**（view-fallback-zqq 快照，残留 0）。产品侧 dispatch 门禁 7/7
  全格重放（.txt/.bin/.csv/.png/目录对/.reg→Text/兜底）+ task-only 六视图无
  文件路由 + 标题规则 `{L} <--> {R} - {View} - Beyond Compare` 实测吻合；
  `--show` 活体互证产品窗口标题逐字匹配 Oracle 2/2。
- **产品实现**：`product/gui/WpfHost/Dispatch.cs`（spec `dispatch` 块驱动，
  每格带 `evidence` 字段——分派表本身即文档）；`reacmp-gui --menu-spec spec
  --dispatch L R [--show]` 为 GUI 入口：解析视图→渲染该视图菜单/chrome/骨架。
  `--dispatch` 命中 task-only 视图时退出码 3（无路由拒路，非猜测）。

**残差**：`.htm/.xml/.jpg` 等 hint 格待行为实测补正（若做 Picture 家族扩展）；
文件夹 vs 文件对混合输入的落点未测（实测均为双侧同类）；分派进视图后窗格内容
渲染仍属引擎接线之后。

### 6.10 引擎接线 + Text Compare 动态面（2026-10-21）：**双门禁全绿，负向验证可红**

分派后的视图拿到**真实比较结果**并动态渲染窗格——P1 引擎接线第一块，Text
Compare 一条线贯通：dispatch → reacmp 进程边界 → XML 差异 → 窗格着色。

- **进程边界（ADR-7/8 坐实）**：`EngineBridge.cs` 的 `ReacmpEngine` 构造一行
  `text-report layout:xml output-to:… "<L>" "<R>"` 脚本，`reacmp @script`
  子进程执行，解析 `linecomp status / text ltid rtid`。退出码契约沿用 CLI 实测
  表（0 出报告；105/106/107 拒绝面），GUI 侧统一收敛为**退出码 4
  （ENGINE-FAIL）——引擎没给出的结果 GUI 绝不猜测**。缺 colors.json 同码 4。
- **活体颜色取证（本轮新增探针，串行三启动，均零残留）**：
  `tools/live-text-color-probe.py` 用 Job Object 起参考版 5.2.6，`PrintWindow
  (PW_RENDERFULLCONTENT)` 采整窗 PNG + 按 UIA rect 裁两窗格；语料
  `tools/textcolor/content-left|right.txt` 先离线用**自家引擎**构造成一份
  XML 含全部五状态（same/similar/different/leftorphan/rightorphan 各至少一
  行），使单启动取齐全部色。`tools/textcolor-analyze.py` 离线把 PNG 固化为
  `extracted/live/textcolor-en/colors.json`（每个值带出处）。**实测定案**：
  行距 15px、首行 y=0、行号灰栏到 x=41（正文起点 42）；**same 行=窗格底色
  （无着色带）**；similar 淡蓝 (238,238,255/252)、different 与孤儿内容侧淡红
  (255,227,227/252,230,230)、孤儿空档侧=底色+对角点阵斜纹（右 191、x 周期 8、
  相位 (x+y)%8==7；左 230 更密，在案未全建模）；墨色左 (0,0,0)/右 (48,48,48)。
  **右窗格整体 -3 的色调差经 `--click-pane` 二次采集证明与焦点无关**（点击
  右窗格后色值不变）——固定逐窗格常量，非活动态规则。词级 inline 标记
  （金 251,222,112 边栏标记、橙 212,113,37、similar 词蓝）记为残差不入第一版。
- **窗格内容不进 UIA（活体两快照实锤驱动设计）**：BC 的 TTextEditor 在 UIA 树
  里**不暴露行内容**（子节点只有滚动条/状态栏），产品内容层 `TextPaneView` 用
  裸 `FrameworkElement`（默认 peer 从控制视图被剪）自绘——既符合 Oracle 观测，
  又不破坏 §6.8 的 290 节点前序对拍。窗格树序挂接照抄实测：BC 快照
  editor#0=屏幕右（rect x=784）、editor#1=左（x=86），产品 attach 同序。
- **台账即文档**：`--dispatch --dump` 的 ledger 新增 `content` 块（逐行
  status/ltext/rtext/ltid/rtid），渲染数据可离线审计。
- **四道门禁（本轮新增三道 + 一道重放）**：
  1. `tools/textcontent-check.py`（离线）：产品台账逐行逐字 == **独立直调引擎**
     的 XML（status+双文本+双 tid），外加文本锚定（每文本 == 源文件第 ltid 行）
     ——12 行 0 违例；
  2. `tools/uia-text-content-check.py`（活体）：起产品 `--dispatch --show`，
     UIA 定位两 TTextEditor rect → `PrintWindow` 像素按 grid 行死心取色，逐状态
     两侧 == colors.json（同色必须等于底色=无着色带规则），且骨架前序 24 节点
     未被内容层破坏——**10 tint + 24 节点全绿**；负向验证：产品用变异色渲染
     （REACMP_PRODUCT_COLORS）时门禁如期抓红（want=(255,227,227)
     got=(200,0,0)×2），证明链路非恒过；
  3. `tools/menu-offline-check.py`（离线重放，**收编原散在会话里的 845/410/290
     三轴对拍**为可重跑脚本）：12 视图逐项 labels+序+enabled、chrome 三元组、
     skeleton 前序 vs 四矩阵/spec——**totals 845/410/290，0 违例**；
  4. `tools/dispatch-check.py`（离线）：7 实测格路由+标题逐字，6 task-only 拒路
     **真实触发退出码 3**（合成 `.tonly` cell 进临时 spec 走同一代码分支——
     分支护栏非 Oracle 格）——13/13 绿。
- **回归**：活体 menu/chrome/skeleton 三档批量 12/12×2 全绿、211/211 结构门禁
  全绿、BCompare/reacmp-gui 残留 0。产品 dispatch 截图留档
  `extracted/live/textcolor-product/dispatch.png`。
- **WPF 坑（本轮新增，防再犯）**：`MeasureOverride` 把宽度钳到常数会让色带短
  于窗格，活体取色读到底色——内容层必须全宽伸展；`TextPaneView.Style` 与
  `FrameworkElement.Style` 撞名（CS0108），改 `Colors`。

**残差（动态面后续）**：MainBar 过滤钮（All/Diffs/Same/Context/Minor 的选中态
与 display 联动）、状态栏运行时文本（`Load time`、窗格 footer `1: 1`）随会话
翻转、词级 inline 标记色、详情窗格（word-level diff）、滚动同步、Merge 三栏
与其余视图（Hex/Table/Picture 等）的内容通道、文件+目录混合输入格（沿 §6.9）。

### 6.11 过滤钮 radio 三钮接线（2026-10-21）：**All/Diffs/Same 实锤单选，离线+活体双门禁全绿**

§6.10 残差第一条收口。MainBar 的 display 过滤钮接入引擎三路径过滤通道。

- **取证实锤（探针 `tools/live-text-filter-probe.py` / `probe4.py`，参考版 5.2.6
  串行三启动，零残留；数据 `extracted/live/textfilter2-en` + `textfilter4-en`）**：
  1. **选中态完全不进 UIA**：六个钮每步的 Toggle/legacy pressed 全 `None`——
     选中只能像素读。BC 的钮选中=整钮底染淡蓝 (194,220,245)，未选=工具栏灰
     (240,240,240)（单色列 x=153/212/271 在 step0/click-All/Diffs/Same 间
     蓝块精确移动，逐拍裁定）。
  2. **All/Diffs/Same 是互斥 radio**（任何时刻恰好一个蓝）；**初始选中=All**
     （step0-initial）。Context/Minor 的可加性（叠加 or 入组）**未裁定**——
     探针里其矩形含图标色干扰；在案残差，本块不接（绝不猜）。
  3. **tooltip 即模式语义**（鼠标停在钮上 UIA Text 实测全文）：
     All="Shows same, left orphan, right orphan and difference lines."、
     Diffs="Shows left orphan, right orphan and difference lines."、
     Same="Shows same lines."、Context="Shows lines surrounding difference."、
     Minor="Treats unimportant differences as same."——映射到 CLI 已实测的
     display 选项词汇（`button_to_option` 存 `filter-map.json`）。
  4. **钮尺寸 59×39**（probe4 UIA rect 实测）进 filter-map 供产品同尺寸渲染。
  5. **footer `N: C` = 源文件行号:列号**（probe2 点第 4 行得 `4: 10`）——在案
     待接（本块未动 footer）。
- **引擎通道实测（本轮关键发现）**：@script `text-report options:` 通道**接受
  选项名但不过滤**（`exec.rs` 用 `ReportOptions::default()`，实测 12 行无
  `<mode>`）；三路径 `reacmp L R out --opt=<display-*>` 通道**真过滤**并写
  `<mode>`（语料 12/7/5/12/12 行 = all/mismatches/matches/context/ignore）。
  GUI 因此切到三路径通道复用过滤语义——**窗格绝不自己实现过滤谓词**。
- **实现**：`ReacmpEngine.Compare(L,R,opt)` 三路径形式 + 解析 `<mode>`；
  `FilterMap`（filter-map.json 驱动，radio 成员/颜色/尺寸全加载零硬编码）；
  `ChromeElement` 加 `Selected/Clicked/OnRender`（选中底色=实测值，UIA 不暴露
  选中态——照抄 BC 观测）；MenuMode：`--display NAME` 选初始钮（未知名=拒，
  退出码 4）；radio 点击→引擎重取（失败=保留现图+报 ENGINE-FAIL，不造假）→
  窗格/按钮 InvalidateVisual 刷新。**坑（本轮）**：BuildSkelNode 递归分支漏传
  decorate → 钮 2×2 无色（活体首跑抓到）；dispatch 窗口 800×480 容不下 12 行
  过滤网格（row11 采样落窗外黑像素）→ dispatch 时窗扩到 1200×820（尺寸属实现
  期收敛项，非契约）。
- **双门禁**：
  - 离线 `textcontent-check.py` 加 display 档：产品台账（--display Diffs/Same）
    逐行逐字+`<mode>` == 独立直调引擎三路径过滤（7 行 mode=Differences、
    5 行 mode=Same），文本锚定源行——三钮全绿；
  - 活体 `uia-text-filter-check.py`：起产品 `--dispatch --display B --show`，
    UIA 读三钮 rect（59×39）取色断言选中钮=蓝/其余=灰，并按引擎过滤网格逐行
    双侧取窗格 tint（24/14/10 tint 采样）——All/Diffs/Same **3/3 全绿**；
  - 回归：离线三轴 845/410/290 0 违例、dispatch 13/13、§6.10 内容 tint 门禁
    10+骨架 24 全绿、活体批量 12/12（含 chrome+skeleton 复跑）。

**残差**：Context/Minor 语义（可加 or radio 组）未裁定待专探针；footer `N: C`
跟随光标联动、状态栏运行时文本（Load time 等）、MainBar 钮图标、其余视图内容
通道、滚动同步（沿 §6.10）。

### 6.12 D3 无障碍 provider 落地 + 详情/滚动活体探针（2026-10-22，第四步）

**A. D3 provider（docs/20 §5 D3 的决定=不藏，本轮落地并活体验证）**：
- **关键实测发现（WPF↔UIA 桥语义）**：初版按标准 UIA 设想做
  IsControlElement=**false** 的内容视图专属行 peer → pywinauto（raw/control
  遍历）与 `content_only=True` 遍历**都看不到节点**——WPF 桥对
  IsControlElement=false 的 peer 根本不暴露给树遍历。据此**翻案**：行 peer
  走 IsControlElement=true + IsContentElement=true，结构门禁改在共享遍历器
  `uia_menu_check_lib.live_skeleton_preorder` 里按 **class `TextPane` 显式
  豁免**子树（行=数据非布局骨架；豁免规则单点定义，本地副本退役）。
- **实现**：`EngineBridge.TextPaneView` 加 `PaneContentPeer`（Group,
  class=TextPane, children 缓存=同 DiffResult 同 peer，刷新自动重建）+
  每行一个 `RowPeer`（Text，name=`{行号} {状态}: {文本}`，孤儿空侧=`(empty)`；
  ItemStatus=状态；HelpText=行号+状态；AutomationId=`d3row:{k}`；矩形=
  行带屏幕 rect）。默认 ON，`REACMP_D3=0` 退 opt-out（供门禁负向用）。
- **活体门禁 `tools/uia-d3-check.py`**：A 半=控制视图骨架 24 节点与 spec
  逐字节不变（行零泄漏）；B 半=TextPane 子树可达 **2×12=24 行**，逐行 name
  与引擎台账（--dump）逐字==。正向绿；**负向**：REACMP_D3=0 → 24 行消失、
  骨架仍绿、门禁退 1 正确抓红（"骨架不变+内容缺失"两半都断言=链路非恒过）。
- 回归全套绿：211 / 845+410+290 / 13 / 12+7+5 / golden 12/12 / tint 10+24 /
  filter 3/3 / dark 正负。

**B. BC 详情区/选中/滚动活体探针（textlayout-en 12 行对 + textscroll-en/-3/-4
149 行大语料；Job Object 串行、残留 0 已验）**：
- **详情区几何（step0 UIA+PNG 实测）**：两窗格下方是 **两条横贯详情编辑器**
  `TTextDetailsEditor`：上条 h=15（y808 屏rel）、下条 h=32（y824）+ 其下
  横向滚动条；宽度=双窗格合宽（1386px 单条）。**overview 缩略图在左缘竖条**
  （`TUiThumbnail` x=34 w≈52 全高，DFM InThumbnail alLeft 一致；docs/20 §3
  "底部行距缩略图"表述与此实测不符——布局以实测为准，docs/20 需按 §6.12 修正）。
- **点击行联动（实测）**：点左窗格 row2(different) 后，UIA 变化仅=两窗格
  footer `N: C` 从 `3: 1`→`5: 3` 同步跳变（初始 3:1=**光标默认停在首个
  different 行**，§6.13 新实锤；证实 §6.11 残差的 footer 光标
  联动语义：双 footer 同步、行:列**）；详情两条像素带都改变（darkcounts
  前后不同=内容更新）、两主窗格各 ~2950px 改变但**逐行底色 census 不变**——
  BC 当前行高亮不是整行铺底色（词级 mark/边框形态，在案残差=不建模）；
  详情条带的文字内容 BC 不进 UIA（Text 节点仅 footer 两处 `N: C`）。
- **滚动通道（实测负向+未决）**：pywinauto wheel、keybd VK_NEXT、UIA
  down-line 钮点按、轨道页区点按**均未触发滚动**（三次独立探针三阶段树
  逐字节相同；唯一 30px 变化=光标闪烁 y[186..200]x[115,116]）。footer
  `40: 1` 全程不动。结论候选：BC 编辑器需先获焦（点击行只改光标行不改
  焦点？）/探针消息路由与真实输入差异——**开放项 U-layout-1**，不臆测。
  深行点击（y=550）也未产生位移（dy best=0）=选中不自动滚动到视野外内容。
- **产品第一档（本轮实现+活体门禁 `tools/uia-text-interact-check.py` 全绿，
  负向注入被抓）**：共享 `DiffViewState`（选中行 index + 列 + 视口 TopRow，
  Changed 事件广播）；点窗格行=选行→**双 footer 同步**更新为
  `{本侧 ltid/rtid}: {列}`（列=自家渲染器字形宽度换算——Consolas 11px 实测
  advance≈6.6px，非拟合 BC；BC 探针给出行号 5 而引擎说 3=在案差异
  **U-layout-2**，产品显示真源行号，不吸收 BC 偏移）；详情两条=选中行
  文本+状态/行号读数（**内容=自家设计**：BC 条带文字不可从 UIA/像素解码，
  几何 h32+h15、位于窗格下方=实测；peer=null 保持骨架）；选中不铺整行底色
  （实测 BC 逐行 census 不变）；滚轮=共享视口同步滚动（3 行/格=Windows
  默认度量；BC 精确值 U-layout-1 未测到——同步语义本身=BC 实测 footer
  联动+行为规格）。
- **本轮布局翻案（活体门禁抓到的潜伏缺陷）**：attach 前双窗格实际是**竖排
  叠放**（band 为 2px 小残段时无人采样故未暴露）。修正=引擎模式按实测
  空间模型布局（docs/20 §3 布局参考）：两 TTextEditor 子树→Grid 左右分栏
  且 **列取镜像**（BC 实测 tree-first 窗格在屏幕 RIGHT x=784——UIA 序与
  视觉序分离，与 band 树序/视觉序同族现象）；编辑区子树与详情子树混排→
  竖排、详情在**下**（DFM DetailsPanel alBottom+实测 y808/824）。UIA 前序
  不变（Grid 只改空间位置）——24 节点骨架/TTextEditor rect 门禁继续绿。
- **真实输入需前台**：mouse.click/scroll 在未激活窗口上只会触发激活不会
  送达按下事件（首跑全静默失败）；门禁加 `win.set_focus()` 后正常——与
  菜单探针的前台锁同族限制，自动化脚本一律先激活。
- **负向验证**：`REACMP_INTERACT_NEG=1`（仅测试注入，模拟"右 footer 未绑
  共享状态"接线故障）→ 门禁抓到 2 处 footer 违例退红=断言有牙齿。
- **门禁断言集**（正向全绿）：初始 footer=`{grid[0].ltid}: 1` 双侧；点击
  row2→双侧 footer 同值且行号∈{ltid,rtid}；两详情带像素改变；点击后各
  状态行 tint 不变（众数采样规则同 §6.10）；滚轮 -2 格→双侧可见首行
  渲染 grid[6] 的本侧 tint（同步视口=同 view 不同本侧色，跨窗格直接比
  像素会误判 orphan 行——此断言写法教训已内置）；footer 不随滚动变（光标
  是索引非视口位置）；全程骨架 24 节点不变。


### 6.13 Find 通道活体探针（2026-10-22，第五步侦察；textfind-en，Job Object 串行、残留 0）

探针 `tools/live-text-find-probe.py`：step0 → Ctrl+F → 键入 `totally` →
Enter → Enter → Esc，逐拍存 tree-*.json + window-*.png。**实测行为规格**：

- **形态=内嵌查找条，非独立对话框**：Ctrl+F 在主窗格区顶部插入
  `TTextFindFrame`（实测 rect x=34 y=128 **宽=内容区全宽 1440**、高 37；
  静态 DFM `TFILEFINDFRAME` 的 750×82 是含 Replace/Sides/高级钮的**展开态**，
  默认收起态只有基础钮）。Escape 移除该 frame（closed 态 frame 节点=0，
  footer 保留最后值）。
- **基础控件集（find-open 新增节点实测 rect）**：`TUiComboBox`
  Find-what x=75 w=655 h=25（内含 Edit x=78 w=632 + Windows 下拉按钮
  报本地化名 '打开'=**宿主 OS 中文 locale 产物，非 BC 文本**，勿当 BC 契约）；
  `TUiButton Prev` x=905 w=46 h=30；`TUiButton Next` x=951 w=48 h=30。
  **展开态按钮（RegExp/Case/WholeWords/Wrap/Replace/Sides/Advanced）在默认
  收起条里不存在**——本轮第一档只做基础条（收起态=实测默认）。
- **Ctrl+F 快捷键**：台账实锤 `TFILEACTIONS.FindAction` caption `&Find...`
  shortcut `Ctrl+F` hint "Find|Finds search string."；`FindNext` F3、
  `FindPrevious` Shift+F3、`Find in Files` Shift+Ctrl+F（TTEXTACTIONS）。
- **光标默认态**：fresh 打开比较视图 footer=`3: 1`（**双窗格同值**，再次证实
  共享光标；3=第一个 different 行 ltid）——BC 打开即把光标停在**首个差异**，
  非行 1。这是 §6.11 之外的新语义实锤。
- **键入即实时标记（typed 态像素 diff）**：在右侧正文 y≈198–210（grid row2，
  rtid=3 `TOTALLY differing words here` 的 `TOTALLY` 处）出现新着色带，
  **footer 不变（3:1）**→键入只画匹配带，**不移动光标**。
- **Enter=Find Next（next 态）**：footer 仍 `3: 1`（当前首个匹配就在 row2，
  光标落到它），详情带出现内容（footer/details y782–796 变）。第二次 Enter
  （again 态）：footer **双侧同步跳 `3: 8`**（列=8=`TOTALLY` 词宽后位置）→
  **第二个匹配在别处？** 语料里 case-insensitive `totally` 只命中左右各 1 次
  （L 行3 / R 行3）。实测 again 的左窗格大变化 x[60,683] y[124,776] 含
  (255,227,227)/(255,227,162) 底色与 (219,127,50) 橙色——**wrap 到左窗格**
  把当前匹配画在左侧并滚动/重绘。结论：**Find Next 在全集内循环，跨双窗格
  推进共享光标**（footer 双侧同步跳变再次实锤共享模型）。
- **标记配色（again 态实测色，从 diff 众数取）**：当前匹配词底
  **(255,227,162)**（淡黄，区别于 diff 淡红 (255,227,227)）；橙
  **(219,127,50)**=当前匹配**边界/下划线**像素；(57,127,195)/(182,227,227)=
  选中区相关像素。→ **自家第一档采用**：普通匹配=淡黄底，当前匹配=橙底边
  强调（色号即实测值；语义=黄=hit、橙=当前，与 BC 家族一致）。
- **坑（本轮）**：pywinauto 无 `type_keys`，用 `keyboard.send_keys`（全局投递
  到前台窗，故探针必先 set_focus，§6.12 教训复用）；`TUiSpeedButton` UIA 名
  全空（同过滤钮：BC speed-button 不暴露可测身份，展开态钮语义只能靠 DFM
  hint，不做活体断言）。

### 6.14 Overview 缩略条第一档落地（2026-10-23；TUiThumbnail）

**实测参考几何（textlayout-en step0，窗相对坐标）**：`TUiThumbnail [8,102,52,729]`
—— 左缘 52px 宽全高竖条，位于窗格区左侧（窗格区 `TUiPanel [60,102,1388,729]`，
工具栏 `TUiDock [8,58,1440,44]` 在上、窗口状态栏 `TUiStatusBar [8,831,1440,25]`
在下）。UIA 前序里 TUiThumbnail 是根区最后一个子节点（视觉左、树序后——与
"tree-first 窗格在屏幕右侧"同族现象，docs/19 §6.12）。

**能力继承（docs/20 能力轴）**：整文件差异分布图 + 共享视口窗口 + 点击跳转
（点缩略条=移动共享光标，双 footer 同步——沿用 §6.12 共享光标模型）。
**表现自设计（docs/20 表现轴 P5）**：每行一条状态色带，色相=实测 status tint
（different 红 (255,227,227)、similar 蓝 (238,238,255)、orphan 取有文侧 tint）；
视口框=1px 灰框；当前选中行=2px 橙线（复用实测 accent (219,127,50)）。

**实现（product/gui/WpfHost）**：
- `EngineBridge.OverviewStripView`：owner-drawn FrameworkElement，**无 peer**
  （骨架门禁零影响）；`MeasureOverride` 返回实测槽宽 52 / 高度 729（无限高时）。
- `DiffViewState.VisibleRows`：窗格 OnRender 每次刷新（ActualHeight/pitch），
  缩略条据此画视口框；`OverviewClick` = 选行 + 视口必要时居中。
- `ChromeHost.BuildRootArea`：引擎模式下根区 4 子节点（TUiDock/StatusBar/
  TUiPanel/TUiThumbnail）改为 3 行×2 列 Grid —— **子节点按 spec 前序添加**
  （UIA 前序不变），Grid 只改空间位置；TUiThumbnail 叶子由 attach 挂
  `OverviewStripView` 并包 `ChromeContainer`（triple 不变）。
- 无引擎/离线模式（attach==null）走原 StackPanel 路径，离线 ledger 不变。

**门禁 `tools/uia-overview-check.py`（正负向均实测通过）**：
1. 几何：槽宽 40–60、高 ≥60% 窗高、左偏移 ≤120、与窗格顶对齐 ±40；
2. 色带：用 `--dump` 的引擎 ledger 逐行校验缩略条像素=该状态 tint（容差 26）；
3. 跳转：物理点击最后一个双侧有文的非 same 行 → **双 footer** = `{ltid}: 1` /
   `{rtid}: 1`（首击可能只激活窗口，门禁内重试一次）。
负向 `REACMP_OVERVIEW_NEG=1`（只注入点击失效）→ 门禁抓红，已实测。

**回归**：845+410+290 离线 / 13 分派 / 12 视图 golden / D3 / 交互 / 查找
（含负向）/ 暗色 全绿；Release 出货产物重建 0 error。

### 6.15 Text Merge 通道活体探针（2026-10-23；textmerge-en + textmerge-conf-en）

探针 `tools/live-text-merge-probe.py`（Job Object 串行、残留 0、参考 5.2.6）。
命令行形式=官方帮助实锤：`BCompare.exe <Left> <Right> <Center>` 开合并视图
（4 文件带 output pane）。**BC 脚本无 merge 命令**（SCRIPTING 命令全集核对），
合并 Oracle 只能 UIA+像素，字节级 golden 不适用（在案限制）。

**空间模型实测（窗相对 rect）**：
- 工具栏 `TUiDock [8,58,1440,44]`；**三源窗格横排在上**：
  `[8,154,479,226] / [491,154,474,226] / [969,154,479,226]`（L/C(base)/R）；
  中间一行 **Merge to: 单选组**（Left/Right/Other:，选中底 (194,220,245)，默认 Other）；
  **输出窗格在下**（全宽 `[60,491,1388,340]`）；底部窗口状态栏。
- **无左缘 overview 缩略条**（TUiThumbnail 不在合并树）——与文本比较的空间差异。
- 三源窗格**只读**（footer "Editing disabled"）；输出窗格可编辑（无该字样）。
- 窗格 footer 各有一个 `1: 1`（**各自独立**，非双栏共享模型）。

**按钮组（UIA 名实测）**：Take 区 `Conflict / Left / Center / Right` +
`Next Conflict / Prev Conflict`；工具栏另有 `Same OK / Favor Left / Favor Right /
Swap / Rules / Context / Minor`。take_buttons_uia 六键=我们 GUI 的行为规格。

**状态语义（两场景实测对照）**：
- 自动合并（L 改行2、R 改行5，互不冲突）：左源改动行带 (218,252,252) 青、
  右源 (246,230,252) 紫；输出=两侧改动**都已并入**，对应行带
  took-left (213,255,255) / took-right (248,227,255)；
  状态栏 `N difference section(s)`、无 # 前缀。
- 冲突（L/R 同行双改）：输出行带 **(255,227,227) 红**（与文本比较 different
  同色系），内容=**保持 base 原文直到 Take 解决**；状态栏出现
  `# 1 conflict section(s)`（# 前缀=未解决冲突计数）。
- 色相语义沿用自家规则（docs/20 P5）：青/蓝=左源、紫/粉=右源、红=冲突、
  base 白；具体色号已录 `extracted/live/textmerge-en/merge-palette.json`。

**残差**：行距按文本比较的 15px 假定（同源 face），未单独测合并视图的 sub-toolbar 高
（编辑器顶+~28px 处才有正文）；gutter 冲突标记形态=像素可见但 UIA 不可名（在案
speed-button 同族）。

### 6.16 Text Merge 视图第一档落地（2026-10-23；D4）

**引擎（product/core merge.rs）**：`merge3(base,left,right)` = 两侧分别对 base
做已复刻的 Myers 对齐（`map_ids`+`diff_matches`，report-algorithm.md 实锤核），
取**三方公共锚点**（base 行同时在两个匹配集里），锚点链合并成 equal 带，
带间隙按 (l_changed, r_changed) 分类 take-left / take-right / conflict；
双侧改写内容相同 → 自动并（官方 3-way 概念页语义）；不同 → conflict。
`output_source`：equal=center、take=改动侧、**conflict 未解决=center**
（§6.15 实测红带内是 base 原文）。7 个 cargo 锚点（含探针两夹具的逐字对拍）。

**CLI（product/cli）**：`reacmp --merge3 <L> <R> <C> <out>` 输出
`reacmp-merge3/1` JSON（lines 三侧全文 + sections + counts）。**自家动词**：
BC 脚本命令全集（scripting_reference.html 实核）无 merge，help 明确标注非
BC 兼容，位次却沿用 BC GUI 命令行 `L R C`（command_line_reference.html），
迁移肌肉记忆零成本。计数实测与 BC 状态栏一致（干净=2 difference section(s)、
冲突=1）。手写 JSON（无 serde 依赖，小 schema 自家消费）。

**GUI（product/gui/WpfHost MergeMode.cs）**：入口 `reacmp-gui --menu-spec … --merge
<Left> <Right> <Center> [--dump json] [--show]`。布局按 §6.15 实测空间模型：
Take 工具带（六按钮 UIA 名逐字：Conflict/Left/Center/Right/Next Conflict/Prev
Conflict）→ 三源窗格横排（左/中(base)/右，owner-draw，"Editing disabled" 实测
footer 渲染）→ `Merge to:` 单选行（Left/Right/Other: 实测三件+默认 Other）→
输出窗格全宽在下 → 底部状态行（`# N conflict section(s)` / `N difference
section(s)`，计数**全部来自引擎**，GUI 零再分类）。色带=merge-palette.json
实测色号（left 青 (218,252,252)、right 紫 (246,230,252)、took-left
(213,255,255)、took-right (248,227,255)、conflict 红 (255,227,227)、void
(240,240,240)）。共享光标/视口沿用 §6.12 模型；`Take`/`StepConflict`/点击/滚轮
全走 `Changed` 广播。窗格带 **MergePane/MergeOutput 定位 peer**（本窗不属于
12 golden 视图，暴露 rect 安全且 D3 对齐）。标题=实测结构 `{center} - Text
Merge - LiuCompare`（D1 品牌换轴）。

**门禁 `tools/uia-text-merge-check.py`（正负向全绿）**：① 几何（三源横排
left<center<right、output 在下方）+ Take 组六名齐备；② 冲突夹具状态行含
`# N conflict section(s)`；③ 初始共享光标停在首个 conflict 带（实测 fresh
view 定位规则），Invoke `Left` → 状态 # 计数消失 **且** 输出带红→took-left
青（SolidColorBrush 无 AA，色号精确，容差 8）。负向 `REACMP_MERGE_NEG=1`
（Take 接受但不改 resolution）→ 门禁抓红，断言有牙齿。

**本轮修的产品缺陷（门禁抓到的真问题）**：状态 TextBlock 初版用 WPF Binding
绑非 INotifyPropertyChanged 的视图状态 → Take 后色带变而状态文本冻结；改
`Changed` 事件直写。教训：**绑定源必须可通知，否则用事件直写**（并入既有
"每常量有出处"纪律的表现层配套）。

**回归**：845+410+290 离线 / 13 分派 / 12 视图 golden 12/12 / D3 / 交互 /
查找 / overview / 暗色 / 合并正负向——全套复跑全绿；Debug+Release 0 error。

### 6.17 Text Merge 编辑/落盘语义探针 + 第二档落地（2026-10-23；textmerge-edit-en）

**探针 `tools/live-text-merge-edit-probe.py`**（Job Object 串行、残留 0；4 文件
命令行 `BCompare.exe L R C OUT`，OUT 预置哨兵 PRESETPANE_*）。回答 GUI 设计
必须的三个未实测分叉：

- **Q1 输出窗格初值 = AUTO-MERGE，不是 OUT 磁盘内容**：preset OUT（2 行
  PRESETPANE_*）全程未显示也未保留——Ctrl+S 后文件 = base 8 行（单冲突段
  未解决 → 输出取 center 'line two'）+ 键入的 ZZEDITMARKER7。
  **第 4 文件仅作保存目标**。此形态逐字交叉验证了引擎 merge3 的
  output_source 物化规则（equal/take→该侧，未解决 conflict→center）。
- **Q2 保存 = 仅显式 Ctrl+S**：打开未碰文件、键入未写文件、Ctrl+S 直写无
  对话框（目标已命名；post_ctrls_windows 仅见 TApplication 包装窗）。
- **可编辑窗格规则**：恰好一个 TTextEditor footer 无 'Editing disabled' =
  输出窗格（UIA 树序第一个，屏幕却在最下——树序≠视觉序，§6.12 同族）；
  三源全 disabled；标题 4 文件形态 = `{out} - Text Merge - <brand>`。
- 字节形态实测：LF 连接、无强制尾换行（'...eight\nZZEDITMARKER7' 原样）。
- 证据：extracted/live/textmerge-edit-en/merge-edit-findings.json + 三张
  tree/window 快照。帮助锚点：viewtextmerge.html「non-editable source panes
  + editable output pane」、commandstextmerge.html「Save File = saves the
  modified file from the picked pane」。

**第二档落地（MergeMode.cs 重构）**：输出窗格从 tier-1 的 band 对齐视图改为
**紧凑可编辑文档**（实测 Q1：初值=auto-merge，DocBounds 记录每段在 doc 中的
[start,end)）；行内编辑 = TextComposition Enter/Backspace/方向键（caret 自绘
1px 竖线，表现自设计已标注）；**Take 语义修正** = 用该侧 run 替换 section 的
doc 块（保留其他段的手工编辑，后段边界自动平移）；Next/Prev Conflict 同时
把该段的 doc 块滚进输出视口。`--merge` 接受可选第 4 参 = 保存目标（实测 Q2
规则：仅显式 Ctrl+S 落盘；3 文件形态 Ctrl+S 走 SaveFileDialog，此路未探针
覆盖=在案标注）。落盘字节 = UTF-8 无 BOM、LF、无尾换行（实测逐字）。状态行
加 `[modified]` 标记（表现自设计：BC 的 modified 状态不在实测状态栏单元内）。

**门禁 `tools/uia-text-merge-edit-check.py`（正负向全绿）**：
① 打开不写目标（哨兵保留）；② 键入不写（显式保存规则）；③ Ctrl+S 直写且
内容=auto-merge+marker、无 PRESETPANE 泄漏、LF、无尾换行、无 BOM；
④ 负向 `REACMP_MERGE_SAVE_NEG=1`（保存静默失效注入）→ 抓红实测。
门禁首轮跑红暴露的是**门禁自身**的全局键投递缺陷（§6.14 同族教训），改
click_input + win.type_keys 后稳定——产品侧一次通过。

**回归**：core 276 / cli 141+206+118 / 离线 845+410+290 / 分派 13 / 12 golden
/ overview / D3 / 交互 / 查找 / 暗色 / merge 第一档正负向 / merge 编辑档正向
+负向——全绿；Debug+Release 0 error。

### 6.18 Merge to 落盘目标 + Swap Sides 探针与落地（2026-10-24；textmerge-to-en）

**探针 `tools/live-text-merge-to-probe{,2,3,4}.py`**（4 轮共 7 次串行活体，
Job Object+CREATE_SUSPENDED+临时 profile，全部残留 0；fixture 家族与 §6.15 同：
L 改 line2、R 改 line5、C=base8、OUT 预置哨兵）。合并到的权威语义 =
help/sessiontextmergespecs.html「Merge to defines the destination file of the
merge results」，视图级行为全部实测（merge-to-findings.json）：

- **Merge to 行结构（4/3 文件同构）**：`Merge to:` 标签 + 单选
  `Left [84,467,41,22] / Right [135,467,50,22] / Other: [195,467,56,22]`（默认
  Other:）+ **路径框**（TUiSpecComboBox，3 文件形态 [277,492,1118,25]）。
  §6.15 记录的 selected_tint(194,220,245) 实为**路径框激活底色**而非单选点；
  选中单选点 = accent 蓝 (0,95,184)。
- **路径框显示"当前"合并目标路径**：切到 Left 后字段内容即刻改写为 left 文件
  完整路径（非仅 Other 槽位）；字段按侧的可编辑性未测（在案）。
- **标题跟随合并目标**：`out.txt - Text Merge` →(点 Left)→ `left.txt - Text
  Merge`（切 Right 同理）；3 文件形态 Other 无路径时回退 `base.txt`（center）。
  切换不改状态栏段计数、不改输出窗格与源窗格像素（仅 Load time 单元常规重渲）。
- **Ctrl+S 落盘 = 单选所指向**：A/B 轮 4 文件切 Left/Right 后直接写
  left.txt/right.txt（内容=合并输出），OUT 哨兵原样、对侧与 base 不动、无对话框；
  C2 轮 3 文件默认 Other+Ctrl+S 弹 BC 自己的 `#32770 Save File on File System
  As - Output Side`（Esc 取消零落盘），**Esc 后切 Left+Ctrl+S 直接写盘无对话框**
  ——§6.17 的"3 文件保存路径未探针覆盖"在案缺口就此关闭。
- **Swap Sides（Session>Swap Sides / 合并工具栏 Swap 钮）**：UIA invoke 无效
  （在案），物理 click_input 实锤：L/R 窗格内容互换且色带换侧（原左青变右紫），
  center 零像素变化，输出窗格内容不变、着色归属翻转（took-left (213,255,255) ↔
  took-right (248,227,255)）；区域像素差 L=12564/R=12570/C=0/OUT=38544（L≠R
  逐像素相等是因色带与 gutter 同步换侧）。
- **Session Settings 对话框（结构）**：物理点击 Session 菜单弹层 = **TTBPopupWindow**
  （19 项全录，含快捷键 Save Session Ctrl+Shift+S / Clear Session Ctrl+Shift+C /
  Reload Files F5 等）；`Session Settings...` → **TSessionDialog "Session
  Settings - Text Merge"** 599×602，四 tab（Specs/Format/Importance/Alignment），
  Specs 帧 = TTextMergeSessionSpecsFrame（left combo y257 / Copy+Swap 钮 y289 /
  right y339 / center y421 / Merge to 单选行 y476 / output y504 / description
  y565，OK+Cancel 底栏）——与 TFILESESSIONSPECSFRAME.dfm 对应。**改文件→OK→
  重合并的行为环未测**：对话框实现列为显式在案后续（结构锚点已存档）。

**产品落地（MergeMode.cs）**：MergeState 增 `MergeTo`(left/right/other，默认
other) + `OtherPath`；`DestPath()/DestTitle()` 按实测规则；单选 Checked →
SetMergeTo（测试注入 `REACMP_MERGETO_NEG=1` 拒绝迁移）；路径框 TextBlock 实时
显示 DestPath()（**不设显式 AutomationProperties.Name——路径文本即 UIA 名**，
门禁按完整路径断言）；标题经 Changed 事件直写跟随（§6.16 绑定教训同款）；
Ctrl+S 改写 `state.DestPath()`（null → SaveFileDialog 既有路径）；工具栏追加
**Swap 按钮**（BC 合并工具栏同有 Swap；位次为表现自设计）；`SwapSides()` 交换
Model.Left/Right+路径+section 两侧区间与 take 方向，重建 band rows/输出文档
（侧手工编辑回到 auto-merge：新鲜视图实测；Dirty 复位=表现自设计，在案），
注入 `REACMP_SWAP_NEG=1` 拒绝交换。

**门禁 `tools/uia-text-merge-to-check.py`（positive/mergeto/swap 三态全绿）**：
①初始标题=OUT+路径框=OUT 路径+三单选齐备；②Invoke Left → 标题与路径框切到
left；③Ctrl+S → left.txt=合并输出、OUT 哨兵原样、R/C 不动；④回 Other: →
Ctrl+S → OUT=合并输出；⑤Invoke Swap → 左窗格青带移到 R-fixture 行、输出带
(213,255,255)→(248,227,255)。负向 mergeto（标题/路径框不动）与 swap（带不换位）
均被抓红。

**门禁顺手修的两个真缺陷（回归抓红→修复→全绿）**：
1. **产品：引擎态窗口内容根是垂直 StackPanel**（查找条接入时引入）——StackPanel
   以无限高测量子树，chrome 根 Grid 的 Star 行退化为内容高，TextPaneView 期望高
   （行数×15=2301）把整窗撑爆，缩略条槽位被拉伸到 2301 而条本体停在 729 回退值，
   点击映射错位（uia-overview-check 跳转断言抓到：点 row41 落 130:1）。
   修复 = content 改 **DockPanel（LastChildFill）**，前序子元素显式 Dock=Top
   （查找条在 0 位）；UIA 前序不变，12 golden 复验全绿。
2. **门禁：uia-overview-check 的 near() 缺 int() 强转**——numpy uint8 减法回绕
   （254-255→255），抗锯齿混合像素永久误判；补强转（uia-text-merge-check 同款）
   并把色带采样改为**带内多点候选**（带首/中心/带尾各±1px）以容忍选中行橙线
   （§6.14 设计表现）盖住带中心。

**fixture 规范化**：合并门禁族 fixture 固化在 `_tmp/merge-fix/`（base8 + 双侧
同改 line2=冲突族）；content/filter 活体门禁须用小 fixture（`_tmp/c_L.txt /
c_R.txt`）——150 行 fixture 的首孤儿行在 864px 窗口视口外（row 59），属门禁-
fixture 适配在案项（非产品缺陷，两布局下同样采不到）。

**回归（全绿）**：core 277+5+1 / cli 141+206+118 / 离线 845+410+290 / 分派 13 /
12 golden / d3 正负 / 交互正负 / 查找正负 / **overview 正负（缺陷修复后）** /
暗色正负 / content / filter All-Diffs-Same / merge 一档正负 / merge 二档正负 /
merge-to 三态；Debug+Release 0 error；无残留进程。

### 6.19 Hex Compare 视图第一档落地（2026-10-24；hexview-en，功能 5 GUI 层）

**探针 `tools/live-hex-view-probe.py`**（2 次串行活体、零残留；A-small 差异
夹具 52/50 字节 + B-600 golden 对）。THEXVIEW.dfm 只命名 LeftPanel/RightPanel，
窗格内部=运行时自绘控件，全部实测（hexview-findings.json）：

- **空间模型**：THexCompareView [8,58,1440,798]；全宽工具栏一行
  （Home/Sessions/All/Diffs/Same/Rules/Format/Copy/Next Diff/Prev Diff/Swap/
  Reload）；**每侧独立路径栏 + 文件信息行**（`{时间} {N} bytes Everything
  Else`）；**THexEditor 左 [60,154,694,677] / 右 [758,154,690,677]**；
  TUiThumbnail [8,102,52,729]（同文本视图槽位）；树序=右先（与文本视图镜像
  同族）。窗格内容**不进 UIA**（仅状态栏 `\tInsert`/`Load time`）；hex 视图
  状态栏**无段计数**（实测两轮）。
- **行模型（视图层，≠ M7 报告的 8 槽）**：**每行 16 字节、2×8 组**
  （hex 区组距 16px、字节距 ~21.1px）+ **16 字符 ASCII 区**（字符距
  ~7.1px，同 2×8 组）；行距 ~17.5px；offset 列 8 位十六进制、灰墨
  (105,105,105)、**每侧自己的字节下标**。
- **色板（逐字节着色）**：正常字节/ASCII=黑墨；**变更/孤儿字节=红字
  (255,0,0) + 粉带 (255,227,227)**（hex 槽位与 ASCII 字符都着，同一行内
  红黑混排）；**缺槽=对角 hatch (230,230,230)**（尾部分行：L 4 字节+hatch、
  R 2 字节+hatch——与文本视图"点阵=空侧"同语义）；**caret=青色块
  (0,255,255)** 落在当前字节的 ASCII 格（实测两窗格都在 row0 char0=共享
  光标初始位）。

**引擎通道**：core 增 `align_slots()`/`slot_counts()`（平面槽流+字节值，
与 align_bytes 逐行交叉验证测试）；CLI 增 **`--hex3 <L> <R> <out>`——
LiuCompare 自家动词**（help 明示非 BC 兼容；@script 形态优先=merge3 先例；
`--opt/--layout` 拒绝；JSON=`reacmp-hex3/1`：sizes+counts+槽三元组
`[l,r,matched]`）。GUI 不再分类。

**GUI（HexMode.cs 新文件 + MenuMode/ChromeHost 挂钩）**：`--dispatch` .bin →
Hex Compare 分派（既有 7 格之一）接引擎；attach 在 THexEditor 槽位挂
`HexPaneView`（owner-draw、无 UIA peer——骨架树不变、窗格内容不出树，D3
hex 行暴露=在案后续）；HexViewState 共享光标/视口（点击 hex/ASCII 单元格
定位槽、方向键 ±1/±16、滚轮共享 3 行/格、初始=首个变更字节）；色板严格读
hexview-findings.json（每常量有出处）；行列度量自自家字形（表现轴自设计，
结构/色彩=实测契约）。ChromeHost：编辑器检测扩展 THexEditor（双编辑器并排
+镜像沿用）；新增"编辑器+工具栏"上下排布分支（实测路径栏在编辑器上方；
树序编辑器在先→Grid 行序翻转，UIA 前序不变）。

**门禁 `tools/uia-hex-check.py`（正负向全绿）**：①双 THexEditor 并排+顶对齐
（tree-first=右）；②左窗格粉带/红字/hatch/青 caret 计数、右窗格粉带；
③点击左窗格 hex 单元格 → 双窗格青 caret 同步移动到点击行（共享光标）；
负向 `REACMP_HEX_NEG=1`（点击接受但光标冻结）→ 抓红实测。

**回归**：core 278+5+1（+1 hex 交叉验证锚点）/ cli 144+206+118（+3 hex3
契约测试）/ 离线 845+410+290 / 分派 13 / 12 golden / d3/interact/find/
overview/dark 正负 / content / filter 三钮 / merge 两档+merge-to 三态 /
hex 正负——全绿；Debug+Release 0 error；零残留进程。interact 首轮一次
footer 偶发竞态（wheel 步瞬时值），复跑 3× 稳定绿=在案观察。

**在案后续**：TUiThumbnail 的 hex 缩略条渲染（槽位在树中、绘制为空）；
每侧文件信息行文本（bytes 数来自 --hex3 sizes）；D3 的 hex 行内容暴露；
Next Diff/Prev Diff 工具钮接线；BC 每侧路径栏的完整按钮组。

### 6.20 Folder Compare 列视图第一档落地（2026-10-24；folderview-en，功能 3 GUI 层）

**探针 `tools/live-folder-view-probe.py` + C-selcheck 追问**（3 次串行活体、
零残留；夹具=L/R 目录五状态全家桶 + sub/ 子目录）。TDirTreeView 行为
运行时自绘，全部实测（folderview-findings.json）：

- **空间模型**：**一个全宽列表控件**（TDirTreeView [8,172,1440,555]）内部
  同时画两侧——每侧 Name|Size|Modified 三列，中央细缝（~690-737，默认无
  墨）；**行带对齐**（两侧同步滚动，孤儿行单侧渲染另一侧空白）；行距
  ~20.5px；目录在前。工具栏两行（All/Diffs/Same/Structure/Minor/Rules/
  Copy/Expand/Collapse/Select/Files/Refresh/Swap/Stop + Filters 行）；每侧
  独立路径栏；状态栏每侧 `{N} file(s), {N} bytes` + `{N} GB free on D:\`。
- **色板（状态=文字色）**：same=黑；diff=**红 (255,0,0)**；孤儿=**紫
  (106,0,213)**（左右同色）；newer=**灰 (128,128,128)** 且**新侧时间戳红**；
  斑马纹=**奇数数据行 (248,250,249)**；**光标=浅蓝 (168,205,241) 跟随点击**
  （C-selcheck 实锤：点击 a.txt 后蓝底从 sub 行跟到 a.txt；初始=第一行）。
- **字段语义**：Size=字节计数（a=6/b=7:8/c=9/d=10），**目录行=子树聚合**
  （sub=2=s.txt 字节，收起状态也预计算）；时间戳格式
  `2026/10/24 2:19:13`（斜杠日期、月/日/时不补零）。

**引擎通道**：CLI 增 **`--dir3 <L> <R> <out>`——自家动词**（同 merge3/hex3
地位；@script 优先先例；--opt/--layout 拒绝；+2 契约测试，cli 146 绿）。
JSON=`reacmp-dir3/1`：引擎可见行序（hidden 跳过）带 depth/name/rel/dir/
status 五态 token/每侧 size（字节）/每侧 time（unix millis）。目录聚合
计算=ExpandPolicy::All；**视图默认渲染 depth 0**（=BC 实测默认：目录收起
带聚合），后续扩展层级无需重排通道。

**GUI（FolderMode.cs 新文件 + MenuMode/ChromeHost 挂钩）**：attach 在
TDirTreeView 槽位挂 `FolderListView`（owner-draw 全宽双画侧、无 UIA peer，
骨架树不变）；FolderViewState 单光标（点击/↑↓/翻页/滚轮，初始=首行）；
色板严格读 folderview-findings.json；列度量自自家字形（表现轴自设计，
结构=实测契约）；时间戳按实测格式渲染（本地墙钟）。ChromeHost 新增
**BuildFolderRootArea**：folder 根 [TUiDock, StatusBar, TLogFrame, TUiPanel]
的实测空间模型=工具栏顶/列表 Star/日志底/状态栏底——树序（日志在列表前）
≠视觉序（同镜像规则族），Grid.Row 只动像素；编辑器检测扩展 TDirTreeView
（"列表+工具栏"上下分支复用）。本轮修两处接线缺陷：FolderListView 缺
MeasureOverride、folder 根缺布局分支（均 smoke 抓到）。

**门禁 `tools/uia-folder-check.py`（正负向全绿）**：①全宽 TDirTreeView；
②光标蓝在首行+斑马/红/紫×2/灰计数；③点击 b.txt 行 → 光标蓝移到该行；
负向 `REACMP_FOLDER_NEG=1`（点击接受光标冻结）→ 抓红实测。

**回归（全绿）**：core 278+5+1 / cli 146+206+118 / 离线 845+410+290 /
分派 13 / 12 golden / d3、interact、find、overview、dark、content、filter、
merge 两档、merge-to 三态、hex、folder 正负向全部复跑绿；Debug+Release
0 error；零残留进程。

**状态栏计数接线（docs/21 A，2026-10-24 当日收口）**：folder 状态栏
`{N} file(s), {N} bytes` 双侧换成引擎聚合 LiveName（interact 模式同款；
语义=**可见行**的文件数+字节和——BC 实测同语义：sub 收起时 s.txt 不计）；
free 槽=DriveInfo 活值（`{N} GB free on {drive}` 文形保留=表现自设计）；
无引擎路径保持静态串（12 golden 不红）。门禁 uia-folder-check 增第三断言
（双侧计数==夹具聚合 4/24、4/26 + free 形状）+ 负向
`REACMP_FOLDER_SB_NEG=1` 注入 999 被抓（教训：门禁 env 曾漏带新注入变量）。

**在案后续**：目录展开/收起交互（JSON 已带 depth）；双击行开子会话；
TLogFrame 内容渲染；状态栏计数的 LiveName 接线（chrome 文本已实测同构）；
文件夹行图标；中央比对标记列语义（默认无墨=未测）。

### 6.21 工具栏文字按钮第一档落地（2026-10-24；docs/21 B，功能 1/3/5 共用 chrome 面）

**现状翻案**：ChromeElement 全部渲染空白（只有 radio 三钮画实测选中/未选
底色），410 项 chrome 数据（ct/cls/name/Separator 分组）闲置——用户第一眼
可见的最大缺口。

**带出处的几何常量**（extracted/live/textlayout-en/tree-step0.json 实测）：
工具栏行 TUiDock 高 **44**；按钮 UIA 高 **39**（y=86 于工具栏 y=84 → 上边距
2、下边距 3）；分隔条实测宽 **6**（我们不抄，见自设计）。

**表现自设计项（无逐钮探针需求，docs/21 B 定案）**：
- **文字按钮**（非图标）：BC 工具栏面是纯图标（实测 59×39 图标钮），无文字
  面可测 → 文字面全自设计。字体 Segoe UI 13；宽度=字形串+16px padding；
  圆角 3px；hover 浅灰 (245,245,245)、按下微深 (231,231,231)；亮色文字
  (32,31,30)、分隔线 (217,217,217)（Fluent 家族）。分隔条=**1px 竖线**
  （docs/21 B 定案，不抄 BC 的 6px）。无名字的钮/Pane/ComboBox 路径条
  保持空壳（图标集=后续独立项，版权禁区必须自绘）。
- **禁用态不渲染**：chrome 捕获（chrome-matrix）每项只有 ct/cls/name，无
  enabled 轴（845 enabled 轴是菜单项的）→ 第一档全部按可用渲染，禁用态
  待有数据源再收。
- **radio 三钮**（All/Diffs/Same）：实测 59×39 整块底色照旧（filter-map.json
  sel/unsel），文字叠画其上——filter/theme 门禁的 mode-color 采样不受字
  形污染（已核对其采样为 most-common）。
- **暗色**：dark.json 新增 `toolbar` 键（text 226/hover 43/pressed 53/
  divider 64，色相中性灰阶沿用 gutter 家族，对比度注释在文件里）；
  light.json 不设键=亮色保持上述默认（叠加式主题纪律）。
- **点击语义第二档**（本文不实现）：无命令的钮按下弹回（按钮存在≠命令
  已存在——诚实呈现）。渲染全部发生在既有 ChromeElement 内部 → UIA
  名/类/序零变化。

**门禁 `uia-toolbar-check.py`（pos/neg/dark 三模）**：①13 个命名钮全在 +
39px/44 行实测几何；②按钮区字形墨水覆盖（亮=暗字、dark=dark.json
toolbar.text ±25）；③**树不变**：负向注入 `REACMP_TB_NEG=1`（面禁画、
尺寸布局不变）→ 全树 preorder (ct,cls,name) 与正向逐字节一致（386 节点
实测一致）+ 按钮区墨水归零被抓。

**✅ 收口状态（2026-10-25 桌面恢复，补跑完成）**：实现+树级验证全绿（离线
845/410/290、dispatch 13、**12 golden 逐字节**、core 278+5+1、cli 146+206+118、
Debug+Release 0 error、零残留）。屏保锁定原因存档：输入桌面=Screen-saver 时
PrintWindow 对 WPF DirectX 面返回空白、鼠标注入被拒（OpenInputDesktop 判定
命令见 BOOTSTRAP §4）。桌面恢复=Default 后补跑：
`tools/uia-toolbar-check.py` 三模 positive/negative/dark **全绿**；全套活体
门禁串行复跑（d3 / interact 正负 / overview 正负 / find 正负 / content /
filter All+Diffs+Same / theme-dark 正负 / merge 一档正负 / merge-edit 二档
正负 / merge-to 三态 positive+mergeto+swap / hex 正负 / folder 正负）
**全绿、零残留**（merge-check 首次 "window not found"=窗口显示偶发时序竞态，
复跑即稳——同 §interact 在案偶发类，非缺陷）。

**像素判据修正三处（补跑首红暴露的门禁自身不鲁棒；产品渲染零缺陷，
截图目检 13 钮文字面全画出）**：
1. "绝对亮度带 max(r,g,b)<140" → **"距声明墨色 (32,31,30) Chebyshev≤128"**：
   选中态 radio 蓝底把整段抗锯齿像素抬出亮度带（"All"两字母仅剩 13 核心
   像素<15 误报），而蓝底距墨色恒>128 不混入；hover(245)/pressed(231)/白底
   距墨色 199–223 同样排除。负向注入=面不画 → 计数 0 判据不变（牙齿实测）。
2. dark 模式色识别加**核心半径 48**：选中蓝底距 light 墨 93 落在 128 带内、
   会毒化 top 色众数（dark 首跑 Rules/Same top=(133,186,215)≠(226,226,226)）。
3. dark 色判定从逐通道 ±25 改**亮度均值 ±28**：ClearType 子像素渲染在笔画
   边缘产生固有彩边（绿偏 (204,219,193)），是渲染器属性而非产品填色；三通道
   彩边在亮度上抵消，luma 均值仍命中 (226,226,226)。


**在案后续**：图标集自绘（版权禁区）；无命令钮的第二档命令接线；禁用态
数据源；hover/按压的活体像素验证并入上述补跑。

### 6.22 Session Settings OK 行为环探针（2026-10-25；session-settings-en R5）

探针 `tools/live-session-settings-probe.py`（Job Object 串行、三场景
ok-yes/ok-no/cancel 各一次、零残留）。证据 `session-settings-findings.json`。

**开框环**（结构锚点承 §6.18 R4）：Session 菜单物理点击开 TSessionDialog；
首击偶发被吞（前台过渡），探针改"重试直到弹层含目标项"（同工具栏弹层家族）。
Specs 帧=4 个 TUiSpecComboBox（顶序 Left/Right/Center/Output），
**ValuePattern 可读初值**（BC 自家 combo 不暴露路径 name，但读得到值）。

**写入/提交环**：`set_edit_text` 写可见字段（UIA Edit 读回可能滞后，像素差
证写入）；**TAB 提交**后 combo 值读回新路径=进模型；TAB 会使旧包装器失效
（COM 'no subscribers'，重取再操作——对话框包装器复用 §6.18 stale 教训）。

**OK 环（本轮核心答案，全部实测）**：
1. **OK 对 TUiOkBtn 用 uia invoke 有效**（与工具栏 TUiSpeedButton 的
   invoke-无效家族不同——别外推）。
2. OK 先弹 **TFileConfirmSaveDialog "Save merge output?"（Yes/No/Cancel，
   模态）**——条件=当前输出文档≠磁盘目标（探针从未手工编辑仍弹=BC 以
   "目标文件内容与合并结果不同"判脏，不是仅看用户编辑）；Cancel 关设置框
   **不弹**此框（实测）。
3. **Yes** = 先把 **改路径前（旧 spec）的合并文档**写入目标
   （out=LEFT-ONE-ORIGINAL…=旧 take-left 结果，非 left2），**再**应用新
   spec；**No** = 跳过写入、直接应用；两者之后 **原地重比较**：主窗
   TViewForm **句柄不变**（main-replaced=false）、左窗格像素 diff=611
   （L→left2 生效）、标题仍 `{out} - Text Merge`（**不**随新 Left 走）。
4. 模态未处理时 TSessionDialog 仍"可见"——此前所有"OK 没反应"的误读
   全是这层叠加（四路输入全被确认框吞掉），**方法论教训：对话框环要按
   模态栈逐层处理，窗口存在≠可交互**。
5. **Cancel 环**：直接关设置框、零副作用（无重比较 diff=0、目标文件未动、
   spec 编辑丢弃）——实测。

**未实测=在案**：确认框答 Cancel 的行为（探针未覆盖）；自家 GUI 对确认框
Cancel 定义为"放弃本次 OK、留在设置框"（表现自设计，已标注）。非 merge
视图（text/hex/folder）无"输出文档脏"概念，BC 是否弹同类确认未测——
自家第一档按语义只在 merge 视图弹。
