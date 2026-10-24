---
name: reacompare-gui-recon
description: GUI 侦察收口（docs/19）：双安装 211 DFM 对照、活体全 12 视图菜单+chrome 基线（四形态/双因子可见性）、DFM 结构金标准、U-gui-1..5
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

功能 16（GUI）侦察于 2026-10-20 完成（静态+活体），成文 `product/docs/19-gui-replication-spec.md`。

**静态实锤**：双安装 DFM 对照 **201/211 逐字节相同**；10 处差异全是版本构建漂移（THEXGOTODIALOG 差 OnCreate 等），中文重打包不改窗体结构。规格以英文 reference 5.2.6 为权威底本。

**活体枚举路线（试错后定案，勿再走弯路）**：GetMenu 恒空（菜单是 VCL 自绘 TUiMainMenu，弹出是独立顶层窗口 TTBPopupWindow，非 #32768）；UIA ExpandCollapseState=LeafNode，Expand() 无效；keybd_event Alt/F10 不可靠送达。**可用路线 = pywinauto UIA + `click_input` 顶级项 → 等 TTBPopupWindow → 该窗口 UIA 树 RawViewWalker 遍历 → 子菜单靠 SetCursorPos 悬停物化**。必须护栏：①弹窗归属校验（popup 矩形横向覆盖顶级项，防上一菜单串位）②确认式关闭（重点+ESC+WM_CANCELMODE，防残留菜单引串后续全部）。只点顶级开关、从不调用命令项。

**三份基线（`extracted/live/`）**：英文 Home（Session11/View3/Tools11/Help9）、英文文本会话（27/6/21/20/24/11/9）、中文文本会话。EN↔ZH 结构逐位一致（View 分隔线位置 [3,6,8,13] 全同），仅标签/AccessKey 本地化 → **U-gui-3 结构面定案**：中文界面=同树+中文标签表。活体 vs DFM `T*ACTIONS`（352 动作）**快捷键集合级 0 差异**；About Beyond Compare 标题取 STRING 资源表 3954 idx 504 `About %s`。Home View 3 项 vs 文本会话 View 24 项 → 菜单可见性随视图/会话状态翻转（DynVisible 运行时含义，精确谓词留反编译 U-gui-2）。

**探针脚本**：`tools/live_probe_job.py`（Job/launch/共享 helper，launch 支持 args）、`tools/live-gui-probe.py`（聚合：一次启动采全部顶级菜单+整树快照，可带会话文件参数）。纪律=严格串行+profile 隔离到 outdir+关后 tasklist 残留归零。

**残差**：U-gui-1（5.2.1 中文 Help 仅 3 项 vs 英文 9 项——版本漂移 vs 重打包裁剪未区分；复刻以英文 5.2.6 为准）、U-gui-2（可见性精确谓词=反编译 `TMenuUpdater`，内容来源已定案）、U-gui-3（中文标签表在资源层的具体位置；结构面已定案）、U-gui-4 **已收口**（chrome 基线入 chrome-matrix.json）、U-gui-5（视图分派实测规则≠帮助文档）。

**活体全 12 视图基线（方向 A 收口，同日）**：`extracted/live/menu-matrix.json`
（每视图一次启动，`--task` 走 Home 任务按钮开空会话，`active_view` 由 UIA 树
`T*View` 类坐实）+ `chrome-matrix.json`（工具栏/状态栏从同批整树提取，零额外启动）。
**四种顶级菜单形态**：Home=`Session/View/Tools/Help`；常规=+`File/Edit/Search`；
Picture 无 Search；文件夹族 `File`→`Actions`。**Tools=9、Help=7 全 12 视图恒定**，
其余 Category 项数随视图翻转（Session 18–23、View 6–28）→ 产品菜单=
(view, session-type) 双因子驱动。**U-gui-5 视图分派实测**：命令行开 `.reg` 落文本
视图、`/fv="Registry Compare"` 官方文档记载但 5.2.6 实测无效（被当文件名）——
分派只按扩展名/新建会话，勿照抄帮助。探针坑：Git Bash 传参 outdir 必须正斜杠；
`--task` 值曾被误当会话文件（已修参数解析）。

**结构基线已生成（同日，`tools/dfm-baseline.py`→`extracted/guibaseline/`）**：
文本 DFM 全语法面（scalar/`''`转义/ident/set/inline-list/collection `<>`/binary
`{N bytes}`）→ 规范化 JSON，211/211 零错误、确定性重跑 sha256 相同。
forms-{en,zh}.json（对象计数 3641/3642 与 forms-index 逐位一致、事件 1821 一致、
EN/ZH=201 同+10 漂移）；actions-{en,zh}.json **381 动作**（96 项 ShortCutStr 纯
Windows 键位——旧对拍正则曾把 MacShortCutStr 误当 ShortCutStr，已修；13 个
Category：Actions/DropDown/Edit/Favorites/File/Help/Mac/MacWindow/Search/Session/
Toggles/Tools/View；DynVisible 仅 2 项=ColList/WorkspaceLoadList）。

**U-gui-2 收口（活体穷举路线，同日）**：反编译路线已探明为死路（REA ephemeral
Ghidra 无符号名；VMT−0x70 自动表指针可得但 RTTI 名串启发式只命中类名），改用
行为数据穷举：**presence-matrix.json**（可见性=TMenuPopulator 静态能力掩码，
238 项逐视图存在表；24 项全 12 视图通用=Session 基础 8+Tools 9+Help 7，与
§3.2 恒定项自洽；139 项单一视图专属；实测怪癖：Folder Compare 的 Actions 菜单
逐项重复 Session 菜单）+ **enabled-matrix.json**（灰显=TMenuUpdater 六组内容态
谓词：无编辑历史/无选区/无导航历史/未载内容/媒体未播/无差异光标；采集态=空会话，
232 恒可用+25 全灰+7 跨视图翻转）。产品验收=两矩阵逐格断言；Updater 内部留 P2。

**B 起步：结构层对拍门禁已建（同日）**：`tools/ui-structure-check.py`——被测窗体
输出与金标准同构 `{name,cls,props,children}`（=ADR-7 契约，框架无关），三级
比对 structure(类/名/层级顺序/Caption·Hint·HelpKeyword)/layout(+13 几何键)/
full(全属性)，差异带路径、退出码 0/1/2；自测 8/8（含 Left 分级隔离用例）、
TTEXTVIEW 双级往返 0 diff、变异 rc=1。`--emit-sample` 出模板。ADR-7→契约成形、
ADR-8 前提（无验收手段）已消除（选型仍待用户定）；docs/04 P1 前置标达成。
U-gui-1 离线收口：中文安装 DFM 动作目录与英文逐词相同（Help 7 项 caption 全同）
→ 重打包未删动作，Help 缺项纯属 5.2.1 运行时过滤，产品复刻英文 5.2.6 语义零阻塞。

相关：[[reacompare-m112-version-channel]]、[[rea-project-state]]
