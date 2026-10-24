# LiuCompare / D:\Rea — 项目长期记忆

## 产品方向（2026-10-22 用户批准，docs/20 为准）
- 产品名 **LiuCompare**；引擎二进制沿用 reacmp / reacmp-gui。
- **能力轴全量继承 BC**（16 项功能、12 视图、398 命令语义、快捷键肌肉记忆）；
  **表现轴自设计**（WPF 原生观感、高 DPI、亮/暗主题、矢量图标、配色色相语义保留）。
- 界面布局参考 BC 的五区格局：菜单/工具栏顶 + 左缘 overview 竖条 + 双窗格 + 底部详情条。
- 不复制 BC 代码/资源/图标/密钥；BC 仅作行为 Oracle。

## 硬约定
- **Oracle 只能串行调用**（BCompare 单实例）：任何 live probe/harness 不得并行。
- 每个行为常量必须有出处（实测 colors.json / ledger / DFM），无出处就自设计并在 docs 标注。
- 门禁纪律：新能力 = 探针 → 锚点 → 正负向门禁 → 全套回归；负向注入（REACMP_*_NEG）证明断言有牙齿。
- 结构门禁（290 骨架 / 12 golden）要求 UIA 前序逐字节不变；新增可见元素用「无 peer 的 owner-draw overlay」或显式豁免（class TextPane 先例）。
- 布局只改像素不动树序：Grid/镜像定位，子节点仍按 spec 前序添加。
- 出货产物 = WPF Release exe（LiuCompare.cmd 启动）；门禁多用 Debug exe。
- 活体门禁解释器：`C:/Python314/python.exe`（有 pywinauto 0.6.9 + keyboard；3.13 托管版没有）。

## 已收口（勿回退）
- 引擎：文本比较（字节级 golden）、目录五 criteria、HEX/表格/图片/注册表/版本通道、BC 兼容 CLI 脚本契约。
- GUI：12 视图骨架+chrome（845/410/290）、12 golden 回放、D3 无障碍、亮/暗主题、双窗格共享光标/视口、Ctrl+F 查找条、左缘 overview 缩略条（2026-10-23）、**文本合并通道两档**（--merge L R C [Out]：引擎 merge3+CLI --merge3+四窗格 GUI；输出=紧凑可编辑文档、初值 auto-merge、仅 Ctrl+S 落盘 LF/无BOM/无尾换行；docs/19 §6.15-6.17）、**Merge to 落盘目标+Swap Sides**（2026-10-24，docs/19 §6.18：单选=Ctrl+S 目标、标题跟随目标文件名、路径框显示当前目标、Swap 侧互换+重着色；Session Settings 对话框=显式在案后续，TSessionDialog 结构已探明）。
- GUI：…（追加 2026-10-24）**Hex Compare 双栏视图第一档**（docs/19 §6.19：--hex3 自家动词+HexPaneView 16 字节 2×8 组/逐字节红粉/hatch/共享青 caret；视图行模型≠M7 报告 8 槽是实测事实）。
- GUI：…（追加 2026-10-24）**Folder Compare 列视图第一档**（docs/19 §6.20：--dir3 自家动词+全宽双画侧列表/五状态文字色/斑马/光标跟随+BuildFolderRootArea；**新视图接线两件套=根布局分支+overlay MeasureOverride，缺一即空白窗**）。
- 门禁工具：menu-offline-check / dispatch-check / gui-self-check / uia-d3-check / uia-text-interact-check / uia-text-find-check / theme-dark-check / uia-overview-check / uia-text-merge-check / uia-text-merge-edit-check / uia-text-merge-to-check（三态）/ uia-hex-check（正负）/ uia-folder-check（正负）。
- docs/21 A 件 ✅（2026-10-24）：folder 状态栏 LiveName 引擎聚合+DriveInfo free；负向 REACMP_FOLDER_SB_NEG。

## 引擎/GUI 教训追加（2026-10-24 hex 档）
- 尾部间隙槽序=M7 模型：min(gl,gr) 配对变更槽在前、单侧孤儿在后（写测试预期先查 docs/14 §2）。
- 手写 JSON 布尔必须发 true/false（System.Text.Json GetBoolean 对 0/1 数字炸）。
- ChromeHost 双子容器布局：编辑器检测已扩展 THexEditor；"编辑器+工具栏"=工具栏 Auto 行 0 在上、编辑器 Star 行 1（树序编辑器在先，UIA 前序不变）。
- interact 门禁 wheel 步有偶发 footer 竞态（无重试），复跑确认。

## 布局与门禁教训（2026-10-24）
- **引擎态窗口 content 根必须是有界容器**（DockPanel LastChildFill）：StackPanel
  以无限高测量 → chrome 根 Grid Star 行退化内容高 → TextPaneView 期望高撑爆整窗、
  缩略条槽位/条本体错位（overview 门禁抓到）。UIA 前序不变的前提下改容器。
- 像素断言 near() 必须 int() 强转（numpy uint8 减法回绕 254-255→255）。
- content/filter 活体门禁用小 fixture（_tmp/c_L.txt/c_R.txt）；合并门禁族
  fixture=_tmp/merge-fix/（冲突族）。150 行 fixture 的 row59 在 864px 视口外。
- BC 侧触发经验：菜单/工具栏物理点击（click_input）唯一可靠，UIA invoke 对
  TUiBitBtn 可能无效；菜单弹层=TtbPopupWindow/TTBPopupWindow，对话框用自己
  hwnd 关闭（主窗包装器在模态期间 stale）。
- Git Bash kill 杀不掉 Windows 进程：残留 reacmp-gui 锁 exe 致 MSB3027，
  用 taskkill //F //IM reacmp-gui.exe。
