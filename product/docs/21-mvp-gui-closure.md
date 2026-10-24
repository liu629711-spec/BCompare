# 21 — MVP GUI 收口设计（2026-10-24 定稿，施工顺序即文末）

> 本文是 docs/20 方向下的**下一里程碑设计**：把 MVP 判据里还悬着的 GUI 件
> 收口。行为常量纪律不变（无实测出处=自设计并标注）；探针纪律不变
> （新行为=活体探针先行，Job Object 串行零残留）。

## 0. 状态盘点（MVP 判据对照，docs/20 §1）

| 判据 | 现状 | 缺口 |
|---|---|---|
| 功能 1/3/5 全链路（文本/目录/HEX） | 引擎字节级收口 + GUI 列表/双窗格全通 | 工具栏全是 2px 空壳（**用户第一眼可见的最大缺口**） |
| 功能 11 报告"能出" | 五通道 CLI/脚本全通 | **无 GUI 入口**（挂点已有：8 视图 Session 菜单的 `{View} Report...`） |
| 功能 13 脚本兼容 | CLI 全通 | — |
| 功能 15 配置 | 引擎四语法全通 | 无会话选项 GUI（Session Settings 对话框，结构锚点已探明） |
| 功能 2 合并 | 两档 + Merge to/Swap 收口 | Session Settings 的 OK→重合并行为环未测（在案） |
| 窗口化 | 打开即比 ✓、品牌/DPI/主题 ✓ | 见上 |

**结论：MVP 收口 = 四件 GUI 件 + 一件顺手接线。** 已按
[可见收益 × 探针风险] 排序如下。

## A. 状态栏计数接线（顺手件，最小）

- **现状**：Folder Compare 状态栏文本是 spec 静态串（recon 夹具录的
  `"4 file(s), 20 bytes"`/`"367 GB free on D:\"`，与真实引擎数据无关；
  与门禁夹具数字巧合相同）。
- **设计**：interact 模式的 LiveName 同款——attach/decorate 把 folder 状态栏
  的 2/4 号 Text 槽换成引擎计数（--dir3 已回 rows；每侧 count/bytes 在
  GUI 端聚合=引擎行求和，不重新分类状态），free 空间用 `DriveInfo`（表现
  自设计：BC 的 free 文案保留结构）。
- **UIA 不变性**：离线/无引擎路径仍是静态名 → 12 golden 不红；分派路径
  名字变真值，无门禁依赖旧串（folder 门禁只断言窗格像素）。
- **门禁**：并入 uia-folder-check 第三断言（状态栏计数 == 引擎行聚合，
  负向 `REACMP_FOLDER_SB_NEG=1` 注入错误计数被抓）。

## B. 工具栏自家渲染第一档（可见收益最大）

- **现状**：ChromeElement 全部渲染空白（只有过滤钮三兄弟画选中/未选底）。
  410 项 chrome 数据（ct/cls/name/Separator 分组）已就位。
- **设计（表现轴自设计，无逐钮探针需求）**：
  - **文字按钮第一档**：无边框、hover 浅灰底、按下微深、圆角 3px（Fluent
    家族）；宽度=文字+16px padding；高度=工具栏行高；Separator=1px 竖线
    分组。按钮文字=chrome name 原文（含 `...` 尾注的菜单型钮照画）。
  - **禁用态**：chrome 数据带 enabled（离线台账 845 断言过）→ 灰字。
  - 渲染全部发生在**既有 ChromeElement 控件内部** → UIA 名/类/序零变化 →
    离线 845/410/290、12 golden、dispatch 13 全部不红（golden 只看树）。
  - 暗色：文字/底色读 dark.json 的 ink/window_bg（D5 语义延续），theme
    门禁期望值不变（它不断言工具栏）。
  - **点击语义第二档**（本文不实现）：All/Diffs/Same 已接线；其余钮先
    无操作（按钮存在≠命令已实现——诚实呈现：无命令的钮**按下弹回**）。
- **门禁**：新 `uia-toolbar-check.py`——①Text Compare 视图按钮区非空
  （像素：按名字抽样按钮的 ink 覆盖率）；②UIA 树逐字节==golden（防树
  破坏）；③dark 主题按钮文字=dark.json ink；负向注入
  `REACMP_TB_NEG=1`（渲染禁用）→ 按钮区纯底色被抓。
- **显式自设计项**（记 docs）：按钮宽度/圆角/hover 色、无图标（矢量图标
  集=后续独立项，版权禁区必须自绘）。

## C. Session Settings 对话框（功能 15 GUI + 功能 2 收尾）

- **已有锚点**（§6.18）：TSessionDialog 599×602、四 tab（Specs/Format/
  Importance/Alignment）、Specs 帧=Left/Right/Center/Output 四路 + Copy/
  Swap 钮 + Merge to 单选行 + Description、OK/Cancel 底栏。
- **待探针（一次活体）**：**OK 行为环**——物理点击开对话框 → UIA 改 Specs
  的 Left 路径 → OK → 观察标题/内容/输出窗格/状态栏（BC 重比较吗？输出
  重置吗？标题跟谁走？）。同轮顺测 Cancel（无变化）。
- **设计**：自家 WPF 对话框（表现轴自设计），第一档只做 **Specs**：
  - 字段按当前视图：text/hex/folder=Left/Right(+Center/Output=merge)，
    Merge to 行仅 merge 视图；路径栏=可编辑 TextBox + 浏览钮（自家）。
  - **OK → 重跑对应引擎通道**（text=ReacmpEngine.Compare、merge=--merge3、
    hex=--hex3、folder=--dir3）→ 重建 View*State → 原窗口原地换数据
    （窗口不关——BC 行为待探针定，若 BC 关窗重开则照抄）。
  - Cancel/Esc → 弹窗丢弃，无副作用。Format/Importance/Alignment tabs =
    显式"后续"（引擎语义已在，UI 后置）。
  - 入口：Session 菜单 `Session Settings...`（台账已有）——菜单接线与
    Report 向导共用同一套"菜单命令→自家对话框"管线（见 C/D 共用件）。
- **门禁**：`uia-session-settings-check.py`——开对话框（UIA 断言字段框
  存在+预填当前路径）→ 改 Left → OK → 标题/窗格更新为新对；负向：
  Cancel 后标题不变；注入 `REACMP_SSET_NEG=1`（OK 不重跑）被抓。

## D. 报告向导第一档（功能 11 GUI，MVP 判据最后一件）

- **挂点（已核实）**：8 视图 Session 菜单各有 `{View} Report...`。
- **设计（自家向导，自设计标注；BC ReportDialog 结构可作布局参考）**：
  - 对话框字段：**layout**（按视图给合法集——text=XML/patch/summary…、
    hex=side-by-side/interleaved/summary、folder=…引擎已有的全集）、
    **options**（对应各通道 --opt 串）、**output 路径**（默认
    `<左文件名>.report.<ext>`）。
  - **执行 = 直接调自家 CLI 报告动词**（不另写渲染器）：text/folder 走
    既有脚本通道动词、hex=hex-report、其余同理——GUI 是 CLI 的薄壳，
    字节级契约零漂移。成功→状态栏/对话框提示 + 打开所在文件夹钮；
    失败→把 CLI 的退出码/错误原文透出（失败面=不猜结果，引擎纪律）。
  - 菜单命令→自家对话框管线：与 C 共用（数据驱动菜单的 Clicked 挂钩，
    按 (view, item) 分派到对话框工厂）。
- **门禁**：`uia-report-check.py`——菜单点开向导→选 layout→OK→输出文件
  存在且**逐字节==reacmp CLI 直跑同参数产物**（最强断言：GUI 零漂移）；
  负向：Cancel 不落盘；注入 `REACMP_REPORT_NEG=1`（写盘跳过）被抓。

## E. Folder 展开交互第二档（探针先行）

- **探针（一次活体）**：BC 展开语义——点 Expand 钮/双击目录行/点击 ►
  glyph 各自行为；展开后缩进/聚合/行序；收起还原。
- **实现**：--dir3 已回全 depth 行 → 视图维护 per-dir expanded 集，
  行=depth 0 + 已展开目录的直接子行（递归按展开集）；缩进=depth×14px
  （自设计）；►/▼ glyph 自绘。门禁正负向（展开→子行出现+缩进正确；
  负向注入展开无效）。

## 施工顺序与验收（每步全套回归 + 文档三件套）

1. ✅ **A 状态栏接线**（2026-10-24 收口）：LiveName 引擎聚合 + DriveInfo free；uia-folder-check 第三断言（4/24、4/26 + free 形状）+ 负向注入全绿。
2. **B 工具栏渲染第一档**（2026-10-24 实现+树级验证收口）：文字按钮面
   （39px 实测高+44px 行、1px 分隔、Fluent hover/pressed、dark.json
   toolbar 键、radio 底色照旧+文字叠加、无命令钮按下弹回）。
   uia-toolbar-check 三模脚本就位；**树级证明全绿（12 golden 逐字节、
   离线 845/410/290、负向树 386 节点一致）；活体像素三模因环境屏保锁定
   待补跑（见 docs/19 §6.21 收口状态）**。
3. **C 探针（OK 行为环）→ Session Settings 对话框**（1–2 天级）。
4. **D 报告向导第一档**（1 天级，与 C 共用菜单管线）→ MVP 判据全勾。
5. **E folder 展开探针→实现**（P1，MVP 后第一个）。
6. 里程碑尾：docs/20 §4-4 的"BC vs 我们"人工走查一次（探针基建出对照
   截图），结果记 docs/20 §7。

## 风险与纪律备忘

- B 的最大风险=像素门禁误伤：toolbar 渲染后 theme/interact 门的采样区
  若撞到按钮区需在门禁内显式排除（改动必须带门禁自身的负向验证）。
- C 的风险=OK 行为环未测前不得臆测"是否重比较/是否重置输出"——探针
  红灯则按实测实现，不按直觉。
- D 的断言强度=GUI 产物与 CLI 直跑逐字节相等（这是自家动词管线的免费
  红利，务必写进门禁，防止 GUI 私自加参数）。
- 所有新可见元素：无 peer 的 owner-draw 或显式豁免，UIA 前序纪律照旧。
