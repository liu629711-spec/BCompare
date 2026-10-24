# Dir（目录比较）模块规格索引（侦察完成，第一遍未开始）

> 项目：Beyond Compare 全产品复刻。本目录为 Dir（目录/文件夹比较）模块规格。
> 日期：2026-10-13。上游：S 地基 14 单元（`../ss/`）、Text 9 单元（`../text/`）已完成。
> 数据源：`D:\Rea\extracted\function-attribution.json`（121485 函数中 28126 已归属，271 单元）、
> `D:\Rea\extracted\pseudocode\*.c`、`D:\Rea\extracted\string-function-index.tsv`。

## 0. 模块边界（重要发现）

Dir 战役范围 **大于** 单元名含 `Dir` 的集合。依据 `string-function-index.tsv` 中的
assertion 源路径 `C:\BCBuild\BCompare\Source\Dir\...`，模块实际由两个源码子目录构成：

- `Source\Dir\`：18 个含 `Dir` 的单元 + `Op\` 子目录
- `Source\Dir\Sync\ViewDirSync.pas`（注意：在 Sync 子目录下，非 Dir 根）
- `Source\Dir\Op\`：`OpBase.pas`、`OpCopy.pas`、`OpMoveBoth.pas`、`OpSync.pas`、
  `DlgOpCompareResults.pas` —— **文件复制/移动/同步操作引擎**，与目录比较强耦合
  （OpBase/OpCopy/OpMoveBoth/OpSync 分别调用 DirTree 24/9/9/23 个目标函数）

**规模**：Dir 命名 18 单元 = 1629 函数 / 308261 B；`Op\` 5 单元 = 387 函数 / 64465 B。
**模块合计 2016 函数 / 372726 B**（占已归属函数 28126 的 7.2%）。

## 1. 单元地图

### 1.1 核心单元（本轮已出清单）

| 单元 | 函数数 | 总字节 | 角色一句话 | 证据 |
|---|---|---|---|---|
| **DirTree.pas** | 303 | 76994 | **目录比较引擎核心**：树节点存储 + 后台构建/内容搜索 Job | `TDirBuildFolderJob`(140f509a0)、`TDirTreeContentSearchJob`(140f569f0)；依赖 SsMapTree(193 目标)/SsPersistent(25)/BcJobs(54)；被 DirSession(21)/ViewDir(64)/ViewDirBase(66)/DirFilters(25)/DlgDirReport(20) 引用 |
| **ViewDirBase.pas** | 269 | 49180 | 目录视图**基类**：树控件、右键菜单、打开方式、路径栏 | 调用 DirTree(66 目标)、UiComCtrls(30)；字符串 `OpenWith`(141b26af0)、`ftps`/`sftp`(141b2c620)；被 ViewDir 引用(110 目标) |
| **ViewDir.pas** | 282 | 40072 | **文件夹比较视图**（左/右双栏目录会话的实际视图） | 调用 ViewDirBase(110 目标)、DirTree(64)；字符串 `CompareTo`/`AlignWith`(141b4ee20)、`SessionDirMerge{Specs,NameFilter,OtherFilters,Misc,Handling,Comparison}`(141b55f20..141b563e0)；最大函数 7703 B(141b51a00) |
| **DirFilters.pas** | 191 | 25352 | 名称过滤器 + 文件夹合并（Folder Merge）规则，`.bcss` 设置持久化 | 字符串 `NameFilter`(140f6acc0)、`Folder Merge`(140f5bd00)、`.bcss`/`%s_%d.bcss`(140f6af90)；调用 DirTree(25 目标)、BcJobs(23) |
| **DlgDirScript.pas** | 61 | 20714 | 文件夹比较**脚本/DSL 解析器**（criteria/load/filter/expand/copyto 指令） | 37 个 DSL 关键字：`attrib:`/`cutoff:`/`size:`/`unixtype:`/`exclude-protected`/`follow-symlinks`(1417cd0a0,1417cbb20)、`create:`/`append:`/`Log.txt`(1417ceda0,1417cf880)、`lt->rt`/`left->right`(1417cb4b0)、`confirm:`/`stop-on-error`(1417d01f0) |
| **DlgDirReport.pas** | 88 | 20131 | 目录比较**报告生成**（HTML 表格 + `bcreport` XML + `foldercomp` 脚本） | 调用 BcReport(89 目标)；状态名 `DirDiff`/`DirNewer`/`DirOlder`/`DirOrphan`/`DirSame`/`DirHollow`/`DirFiltered`/`DirUnknown`(140fccbf0)、`DirItem*`(140fcec20)、HTML CSS(140fcee70)、`foldercomp`+`ltpath`/`rtpath`/`mode`/`ignoreunimportant`/`filters`/`advfilters` XML 写出(140fd2340)、`bcreport`(140fd25e0) |
| **ViewDirSync.pas** | 105 | 15295 | **文件夹同步视图**（Sync 子目录，基于目录树的三方同步） | 字符串 `Folder Sync`(141b5b910)、`SYNC_RUN`(141b64fa0)、`Swap`；调用 ViewDirBase(20 目标)、DirTree(8)、OpBase(5) |
| **DirSession.pas** | 83 | 9569 | 目录**会话对象**（比较规格 Specs、多基准、只读标志），持久化载体 | 字符串 `Specs`/`MultiBaseSpecs`/`NoEdit`(140f5a270)；对 SsPersistent 调用 39 个目标函数（会话序列化），调用 DirTree(21)；被 FrameDirSessionComparison(10)、ViewDir(15)、DirTree(24) 引用 |

### 1.2 次级单元（未出清单）

| 单元 | 函数数 | 总字节 | 角色 | 证据 |
|---|---|---|---|---|
| DlgDirAlignWithItem.pas | 68 | 13384 | 「与某项对齐」对话框（选左/右基准项） | `DirHandlingDropDownBtn`(141b061f0)、`ActionsMenu`(141b06260)、`Action(s)`(141b01d70)；⚠ 88% 为 edge-nearest，归属可靠性最低 |
| DirColors.pas | 13 | 8945 | 目录视图颜色/字体偏好 | `FontStr`(140f3b540,140f3b6e0)；单函数 6763 B 占该单元 76% |
| FrameDirSessionComparison.pas | 64 | 8620 | 会话比较信息面板（Frame） | `%s (%s)`(141b15520)；调用 DirSession(10 目标) |
| DlgDirOtherFilterItem.pas | 17 | 5947 | 「其他过滤器」编辑项对话框 `[?]`（零字符串） | 调用 DirFilters(11 目标) |
| DirTreeView.pas | 19 | 4278 | 目录树视图控件（Unix 权限串/时间戳列格式） | `drwxrwxrwx`/`1234567`/`00.00.00.00`(140fc6de0, 权限列格式串)；调用 DirTree(10 目标) |
| DlgDirLegend.pas | 12 | 2762 | 图例对话框 `[?]`（零字符串） | 调用 ViewDirBase(1 目标) |
| DlgDirFind.pas | 12 | 2525 | 目录内查找对话框 `[?]`（零字符串） | 被 ViewDirBase 引用(3) |
| DirSessionState.pas | 23 | 1762 | 会话状态（持有正则 `(.*)`） | 被 DirTree(2)/DirTreeView(3)/DirFilters(1) 引用 |
| FrameDirOpProgress.pas | 11 | 1396 | 文件操作进度 Frame `[?]`（零字符串，据调用关系推断） | 调用 DlgDirOpErrors(1 目标) |
| DlgDirOpErrors.pas | 8 | 1335 | 操作错误列表对话框 | `TDirOpProgressFrame`(141b0efa0) |

### 1.3 `Source\Dir\Op\` 子目录（文件操作引擎，本轮未出清单）

| 单元 | 函数数 | 总字节 | 角色 | 证据 |
|---|---|---|---|---|
| OpBase.pas | 133 | 21587 | 操作框架基类（任务/进度/错误汇总，`*.xml` 报告） | assertion 路径 `Source\Dir\Op\OpBase.pas`；调用 DirTree(24 目标)、BcJobs(18)；被 OpCopy 引用(33)/OpSync(41) |
| OpSync.pas | 121 | 18549 | 同步操作执行器 | assertion 路径 `Source\Dir\Op\OpSync.pas`；调用 OpBase(41 目标)、DirTree(23) |
| OpMoveBoth.pas | 71 | 13425 | 双向移动（自动合并） | `TOpAutoMergeJob`(141b3dba0)；调用 OpBase(21 目标) |
| OpCopy.pas | 61 | 10575 | 复制操作 | assertion 路径 `Source\Dir\Op\OpCopy.pas`；调用 OpBase(33 目标) |
| DlgOpCompareResults.pas | 1 | 329 | 比较结果对话框（几乎未归属） | assertion 路径存在，仅 1 函数 |

## 2. 已确认的调用链（跨单元）

> **计数口径**：下文 `A→B = n` 指「A 中**引用了 B 的函数个数**（去重后的目标函数数）」，
> 非调用点总数。原始调用点计数更高（例：ViewDir→ViewDirBase 原始 249 次 / 去重 110 个目标函数；
> DirTree→SsMapTree 原始 301 次 / 去重 193 个）。所有数字由伪代码中 `FUN_<addr>` 文本
> 引用 + `function-attribution.json` 的 unit 归属交叉计算得出。

```
                    ┌──────────────┐
                    │ DirTree.pas  │  ← 引擎核心（树存储 + Build/Search Job）
                    │ 303 fn 77KB  │
                    └──────┬───────┘
       ┌───────────────┬───┴────┬──────────────┬─────────────┐
       │66             │64      │25            │21           │20
┌──────┴──────┐ ┌──────┴────┐ ┌─┴─────────┐ ┌──┴────────┐ ┌──┴──────────┐
│ViewDirBase  │ │ViewDir    │ │DirFilters │ │DirSession │ │DlgDirReport │
│269 fn 49KB  │ │282 fn 40KB│ │191 fn 25KB│ │83 fn 9.5KB│ │88 fn 20KB   │
└──────┬──────┘ └───────────┘ └───────────┘ └───────────┘ └──────┬──────┘
       │110 ↑                                    ↑39 SsPersistent │89
       └───── ViewDir（视图派生）                  （会话持久化）    └→ BcReport.pas
              ↑20                                                      （HTML/XML 报告引擎）
       ViewDirSync（Sync 子目录）─5→ OpBase ─33→ OpCopy
                                            ─41→ OpSync
                                            ─21→ OpMoveBoth
```

**要点**
1. **DirTree 是唯一引擎核心**：所有其他 Dir 单元都直接调用它；它自身只依赖 S 地基
   （SsMapTree 193 目标函数、SsPersistent 25 目标）与 BcJobs（54 目标，后台任务）。
2. **视图层两级派生**：`ViewDirBase`（基类）← `ViewDir`（文件夹比较）与
   `ViewDirSync`（同步）。ViewDir 对 ViewDirBase 引用 110 个目标函数（原始 249 个调用点），是最强耦合边。
3. **无外部单元直接调用 ViewDir/ViewDirBase**：对 BcViews/BcSession/BcStartup/ViewSession/
   UiMainControl 全量扫描，调用点数为 **0**。说明视图经 Delphi 类工厂/RTTI 或虚表
   注册后由框架动态创建 —— 静态调用图在此处断开，需靠字符串/虚表补链。
4. **报告链路复用 Text 战役的 BcReport.pas**：DlgDirReport 调 BcReport 89 个目标函数
   （HTML 引擎），自身只负责目录专有的状态名与 XML schema。
5. **引擎 API 表面是小型访问器**：DirTree 中被跨单元引用最多的是
   `140f4d7b0`(195 B, 48 callers)、`140f4dbc0`(83 B, 30 callers)、`140f4ef50`(91 B, 24 callers)、
   `140f4f5c0`(14 B, 21 callers)、`140f4f950`(105 B, 11 callers)；而最大的函数
   （140f43890 3720 B、140f51d40 2879 B）**全库仅本单元内 2 处引用** —— 是私有实现。


## 2b. 状态枚举全文（2026-10-13 REA 实证，`FUN_140fccbf0`）

Dir 比较结果枚举（数值来自 REA 反编译，**语料 grep 无法获得**）：

| 值 | 名称 | 语义 |
|---|---|---|
| 0x0C | **DirHollow** | 空洞项（两侧都存在但内容为空/占位目录） |
| 0x114 | DirDiff | 内容不同 |
| 0x116 | DirDiffNewer | 不同 + 左侧较新 |
| 0x118 | DirDiffOlder | 不同 + 左侧较旧 |
| 0x11A | DirDiffOrphan | 不同 + 一侧缺失 |
| 0x11C | DirFiltered | 被名称/其他过滤器排除 |
| 0x12C | DirNewer | 左侧较新（时间戳） |
| 0x12E | DirNewerOlder | 新↔旧组合 |
| 0x130 | DirNewerOrphan | 左新 + 右缺失 |
| 0x132 | DirOlder | 左侧较旧 |
| 0x134 | DirOrphan | 一侧缺失 |
| 0x136 | DirOrphanOlder | 缺失 + 左旧 |
| 0x13C | **DirSame** | 相同 |
| 0x13E | DirUnknown | 未知（未比较/错误） |

**关键机制**：
- `status − expandedFlag`：`Expanded` 标志使值 +1（`local_20 - local_34`，local_34∈{0,1}）——展开态是状态的**加一修饰**，非独立枚举。
- **后缀修饰**：`Link`（符号链接）、`Error`（访问错误）、`Expanded`（已展开）依次拼接（`FUN_140016090` 追加到状态串）。
- 断言：非枚举值 → `DlgDirReport.pas` 行 **0x31e(798)**。
- 报告文本用 `<DIR>` 占位目录名（`FUN_140f09460`）。


## 2c. 静态断裂点定位（2026-10-13 REA 实证）

侦察阶段发现"视图创建链静态断裂"（语料扫描 0 调用点）。REA 的 `xrefs` 直接给出了答案：

| 目标 | 调用点（REA） | 结论 |
|---|---|---|
| `TDirTreeContentSearchJob` 构造器 `0x140f569f0` | **0 个代码调用 + 1 个数据引用 `0x1421cf0d8`**（.rdata 虚表/注册表） | **经虚表登记创建**——工厂模式，非直接 call |
| `TDirBuildFolderJob` 构造器 `0x140f509a0` | **6 个调用点**：140f41a70 / 140f46be0 / 140f470f0 / 140f4a450 / 140f51990 / 140f54ff0 | 直接构造（构建/刷新路径）——全部在 DirTree 地址段内 → **DirTree 自身驱动 Job** |

**因此视图创建链的正确解释**：视图层（ViewDir/ViewDirBase）不直接构造 Job；Job 经 .rdata 虚表（0x1421cf0d8 所在表）被**类工厂按需实例化**，或者由 DirTree 内部（6 个调用点）在构建/刷新时创建。复刻时的对应实现：Job 类需注册到类工厂表，而非在视图里 new。

**方法论记录**：`procedure_callers` 给"直接 call"，`xrefs` 给"全部引用（含数据）"——**数据引用是定位虚表/工厂链的唯一静态途径**，语料 grep 无法覆盖。

## 3. 第一遍工作清单

按 size 降序的每单元前 10 个函数（完整清单见 `inventory/*.tsv`）。

> 置信度说明（来自 attribution）：`anchor` = 由源路径字符串直接锚定（最可信）；
> `interior-same-unit` = 落在同单元锚点之间（可信）；`edge-nearest` = 由相邻单元边界推断；
> `boundary-guess` = 边界猜测（最弱）。**Dir 命名单元整体以 interior/anchor 为主，但
> DlgDirScript(61/61 edge-nearest)、DlgDirAlignWithItem(60/68 edge-nearest)、
> DirColors(12/13 edge-nearest) 三个单元归属可靠性低，其地址清单需谨慎使用。**

### 3.1 DirTree.pas（303 fn / 76994 B）— 引擎核心，**优先**
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 140f43890 | 3720 | interior-same-unit |
| 2 | 140f51d40 | 2879 | interior-same-unit |
| 3 | 140f42500 | 2098 | interior-same-unit |
| 4 | 140f54680 | 1967 | interior-same-unit |
| 5 | 140f4a450 | 1963 | interior-same-unit |
| 6 | 140f470f0 | 1909 | interior-same-unit |
| 7 | 140f55470 | 1760 | interior-same-unit |
| 8 | 140f4bf50 | 1742 | interior-same-unit |
| 9 | 140f44780 | 1731 | interior-same-unit |
| 10 | 140f4b8b0 | 1654 | interior-same-unit |

补充：API 表面优先读 `140f4d7b0`(195 B, 48 callers)、`140f4dbc0`(83 B, 30 callers)、
`140f4ef50`(91 B, 24 callers)、`140f4f5c0`(14 B, 21 callers)；Job 类 `140f509a0`(753 B,
`TDirBuildFolderJob`)、`140f569f0`(410 B, `TDirTreeContentSearchJob`)。

### 3.2 ViewDirBase.pas（269 fn / 49180 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 141b28dc0 | 4253 | interior-same-unit |
| 2 | 141b26da0 | 2185 | anchor |
| 3 | 141b2e320 | 1484 | edge-nearest |
| 4 | 141b2bc10 | 1462 | interior-same-unit |
| 5 | 141b2f0d0 | 1366 | anchor |
| 6 | 141b25340 | 1088 | edge-nearest |
| 7 | 141b30230 | 980 | edge-nearest |
| 8 | 141b2e920 | 973 | anchor |
| 9 | 141b24070 | 921 | edge-nearest |
| 10 | 141b25b60 | 909 | edge-nearest |

补充：`141b26af0`(368 B, `OpenWith`)、`141b2c620`(490 B, `ftps`/`sftp`)；
热访问器 `141b2f720`(8 B)、`141b2fb80`(8 B, `*(this+0x550)`)、`141b2ac70`(380 B)。

### 3.3 ViewDir.pas（282 fn / 40072 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 141b51a00 | 7703 | interior-same-unit |
| 2 | 141b4ee20 | 1976 | anchor |
| 3 | 141b53f90 | 1457 | interior-same-unit |
| 4 | 141b53880 | 1172 | interior-same-unit |
| 5 | 141b4fc40 | 1119 | interior-same-unit |
| 6 | 141b4d690 | 1030 | anchor |
| 7 | 141b55670 | 915 | edge-nearest |
| 8 | 141b57270 | 729 | edge-nearest |
| 9 | 141b503a0 | 691 | interior-same-unit |
| 10 | 141b4bb50 | 671 | edge-nearest |

补充：`141b51a00` 在函数体内经访问器 `141b55aa0`(`*(this+0x598)`) 取字段 **124 次**，
是本单元最热的字段访问点；`SessionDirMerge*` 六个会话项
141b55f20/141b56010/141b56100/141b561f0/141b562e0/141b563e0（各 112 B）
与已完成的 Text 战役 `SessionTextMerge{Specs,Formats,Importance,Alignment}` 同构
——**证实两个模块共用同一套「会话项」框架**。

### 3.4 DirFilters.pas（191 fn / 25352 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 140f699f0 | 3276 | edge-nearest |
| 2 | 140f6b9c0 | 1888 | edge-nearest |
| 3 | 140f692c0 | 1379 | edge-nearest |
| 4 | 140f66f60 | 1278 | interior-same-unit |
| 5 | 140f664a0 | 1260 | interior-same-unit |
| 6 | 140f6c8b0 | 1177 | edge-nearest |
| 7 | 140f6af90 | 958 | edge-nearest |
| 8 | 140f68010 | 908 | anchor |
| 9 | 140f6dd50 | 647 | edge-nearest |
| 10 | 140f66050 | 549 | anchor |

补充：`140f6af90` 持有 `.bcss` 文件名与 `yyyy-mm-dd`（设置持久化）；
`140f6acc0`(77 B) `NameFilter`；`140f5bd00`(32 B, boundary-guess) `Folder Merge`。
跨单元 API 表面：`140f6ab70`(49 B, 5 callers)、`140f68fd0`(73 B, 4)、`140f691d0`(66 B, 4)。

### 3.5 DirSession.pas（83 fn / 9569 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 140f5a270 | 732 | interior-same-unit |
| 2 | 140f593e0 | 725 | anchor |
| 3 | 140f59960 | 670 | interior-same-unit |
| 4 | 140f5a7f0 | 603 | interior-same-unit |
| 5 | 140f591a0 | 495 | boundary-guess |
| 6 | 140f5a080 | 411 | interior-same-unit |
| 7 | 140f597c0 | 372 | interior-same-unit |
| 8 | 140f5ad10 | 299 | interior-same-unit |
| 9 | 140f59da0 | 265 | interior-same-unit |
| 10 | 140f5b6e0 | 258 | interior-same-unit |

补充：`140f5a270`(732 B) 持有 `Specs`/`MultiBaseSpecs`/`NoEdit` 三个属性名，
是**会话序列化入口**（对 SsPersistent 39 次调用）。另有 `140f5b570`(124 B)、
`140f5b910`(150 B)、`140f5ba70`(150 B) 三个 anchor 确认的源路径函数。

### 3.6 DlgDirScript.pas（61 fn / 20714 B）— ⚠ 全部 edge-nearest
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 1417cd0a0 | 3718 | edge-nearest |
| 2 | 1417cbb20 | 2896 | edge-nearest |
| 3 | 1417ceda0 | 2387 | edge-nearest |
| 4 | 1417ce630 | 1327 | edge-nearest |
| 5 | 1417cad10 | 1267 | edge-nearest |
| 6 | 1417cf880 | 1229 | edge-nearest |
| 7 | 1417ce150 | 1134 | edge-nearest |
| 8 | 1417cb740 | 756 | edge-nearest |
| 9 | 1417ca9b0 | 705 | edge-nearest |
| 10 | 1417cc9e0 | 700 | edge-nearest |

补充：DSL 关键字分布 —— `1417cd0a0`(criteria: cutoff/attrib/unixtype/protected)、
`1417cbb20`(load: version/timestamp/ignoredst/timezone/permissions/follow-symlinks)、
`1417ceda0`(expand: `<default>`/create:)、`1417cf880`(append:/Log.txt)、
`1417cb4b0`(copyto: lt->rt / left->right / rt->lt)、`1417d01f0`(confirm:/stop-on-error)。

### 3.7 DlgDirReport.pas（88 fn / 20131 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 140fcd4e0 | 2006 | interior-same-unit |
| 2 | 140fd0290 | 1955 | anchor |
| 3 | 140fd1140 | 1781 | edge-nearest |
| 4 | 140fccbf0 | 1233 | anchor |
| 5 | 140fcfe00 | 1133 | interior-same-unit |
| 6 | 140fcf7b0 | 987 | interior-same-unit |
| 7 | 140fcddc0 | 759 | interior-same-unit |
| 8 | 140fd1e90 | 673 | edge-nearest |
| 9 | 140fcee70 | 636 | interior-same-unit |
| 10 | 140fd0d00 | 632 | edge-nearest |

补充：`140fccbf0`(1233 B) 是**状态名映射表**（`DirDiff`/`DirDiffNewer`/`DirDiffOlder`/
`DirDiffOrphan`/`DirFiltered`/`DirHollow`/`DirNewer`/`DirNewerOlder`/`DirNewerOrphan`/
`DirOlder`/`DirOrphan`/`DirOrphanOlder`/`DirSame`/`DirUnknown`/`Expanded`）——
**这是目录比较结果分类的权威枚举，第一遍必读**。`140fcec20`(207 B) `DirItem*`
（报告项类型）；`140fd2340`(`foldercomp` XML: ltpath/rtpath/mode/ignoreunimportant/
filters/advfilters)；`140fd25e0`(39 B) `bcreport`；`140fd0290`(1955 B) 报告文件落盘
（`BcFiles/`、时间戳格式）。

### 3.8 ViewDirSync.pas（105 fn / 15295 B）
| # | 地址 | size | conf |
|---|---|---|---|
| 1 | 141b63e00 | 1953 | interior-same-unit |
| 2 | 141b5e090 | 1266 | edge-nearest |
| 3 | 141b647b0 | 1077 | edge-nearest |
| 4 | 141b634a0 | 990 | interior-same-unit |
| 5 | 141b627c0 | 829 | edge-nearest |
| 6 | 141b63a50 | 802 | interior-same-unit |
| 7 | 141b5de60 | 528 | edge-nearest |
| 8 | 141b65080 | 441 | edge-nearest |
| 9 | 141b632d0 | 427 | interior-same-unit |
| 10 | 141b5cc00 | 380 | edge-nearest |

补充：`141b63e00` 调用 `141b28dc0`(ViewDirBase 最大函数)、`141b2ac70`、
`141b5ae70`、`141b65330/141b65350` —— 同步视图复用基类渲染路径。

### 3.9 `Op\` 子目录（若纳入战役，建议作为独立子战役）
- **OpBase.pas**：140fd8e00(1288)、140fd95a0(846)、140fd5390(776)、140fda7c0(762)、
  140fdbb10(716)、140fdb130(689)、140fd8740(642)、140fd5100(602)、140fdcba0(601)、
  140fd3f40(595)；`*.xml` 在 140fd41c0(282)。
- **OpCopy.pas**：140fe7b20(1653)、140fe73d0(1485)、140fe88f0(1292)、140fe8320(818)、
  140fe70d0(690)、140fe8ff0(290)、140fe4fe0(269,anchor)、140fe6ec0(266)、
  140fe94e0(226)、140fe6cd0(220)。
- **OpMoveBoth.pas**：141b3f150(1267)、141b3dec0(1238)、141b3c730(936)、
  141b3d810(832)、141b3fac0(775)、141b407b0(633)、141b3dba0(606,`TOpAutoMergeJob`)、
  141b3d5b0(523)、141b3ccb0(416)、141b3d430(379)。
- **OpSync.pas**：140ff43c0(1599)、140fef950(1019)、140ff3860(792,anchor)、
  140ff3de0(711)、140ff3060(706)、140ff6310(675)、140ff3350(633)、140ff1160(614)、
  140ff0cc0(589)、140ff0f30(502)。

## 4. 建议的第一遍顺序（理由）

1. **DirTree.pas** — 引擎核心，全部其他单元的上游；先拿下树节点结构与
   Build/Search Job 生命周期，后续单元才有语义地基。
2. **DlgDirReport.pas 的 `140fccbf0`（状态名枚举）** — 单函数即可确定目录比较的
   **结果分类空间**（Diff/Newer/Older/Orphan/Same/Filtered/Hollow/Unknown），
   是理解所有其他单元判断逻辑的词汇表。**性价比最高，建议紧随 DirTree**。
3. **ViewDirBase.pas → ViewDir.pas** — 视图层，双栏目录会话的交互与渲染；
   ViewDir 依赖 ViewDirBase（110 个目标函数），顺序不可颠倒。
4. **DirSession.pas** — 会话对象与持久化（`Specs`/`MultiBaseSpecs`/`NoEdit`），
   与已完成的 SsPersistent 直接对接，可快速闭环。
5. **DirFilters.pas** — 名称过滤 + Folder Merge 规则；含 `.bcss` 设置格式，
   与 BcProfile/BcGeneralPrefs 交界。
6. **ViewDirSync.pas** — 同步视图，依赖 3 的成果。
7. **DlgDirScript.pas** — 脚本 DSL；**归属置信度全为 edge-nearest，建议先花时间
   用字符串锚点校正地址归属，再正式解析**（37 个关键字是清晰的规格骨架）。
8. （可选，独立子战役）**`Op\` 四个单元** — 文件操作引擎；与 Dir 强耦合
   （OpBase/OpSync/OpCopy/OpMoveBoth 共引用 DirTree 65 个目标函数），但语义上属于
   「操作执行」而非「比较」，可在目录比较规格稳定后单独立项。

## 5. 已知缺口与风险

- **视图创建链静态断裂**：无任何外部单元直接调用 ViewDir/ViewDirBase（扫描
  BcViews/BcSession/BcStartup/ViewSession/UiMainControl 均为 0 调用点）。视图经
  类工厂/虚表注册创建，需用虚表 dump（`align-vtables.txt` 目前为空）或字符串补链。
- **`DlgDirScript.pas` 地址归属不可靠**（61/61 edge-nearest）：整单元地址需校正。
- **`DlgDirAlignWithItem.pas` 归属不可靠**（60/68 edge-nearest）。
- **`DirColors.pas`**：单函数 6763 B 占 76%，且 12/13 为 edge-nearest。
- **`DlgOpCompareResults.pas`** 仅归属 1 函数（329 B），几乎未覆盖。
- **无 Win32 API 名可用于证据**：反编译语料中调用全部呈现为 `FUN_<addr>`，IAT 桩
  （如 `FindFirstFileW` @1400288b0）**未在伪代码中出现**。文件系统枚举等系统调用
  只能通过 `functions.tsv` 的名字表 + 跨引用间接推断 `[?]`。
- **`DlgDirFind.pas`/`DlgDirLegend.pas`/`DlgDirOtherFilterItem.pas`/`FrameDirOpProgress.pas`
  零自有字符串常量**，角色判定仅依据调用关系与 DFM/控件命名 `[?]`。
  （`FrameDirSessionComparison.pas` 仅 `%s (%s)`、`DirSessionState.pas` 仅 `(.*)`、
  `DirColors.pas` 仅 `FontStr`，证据同样稀薄。）
- `[?]` `140f43890`(DirTree 最大函数) 与 `140f51d40` 的具体语义未定：全库仅本单元
  2 个文件引用它们，从结构看是遍历/构建循环，需读完整函数体确认。

## 6. 证据索引

| 结论 | 证据 |
|---|---|
| 模块源路径 | `string-function-index.tsv` 中 `C:\BCBuild\BCompare\Source\Dir\{,...}\*.pas` |
| DirTree 为引擎核心 | DirTree 引用 SsMapTree 193 / SsPersistent 25 / BcJobs 54 个目标函数；被 5 个 Dir 单元引用（66/64/25/21/20 个目标函数） |
| DirTree Job 类名 | `TDirBuildFolderJob`@140f509a0、`TDirTreeContentSearchJob`@140f569f0 |
| 结果分类枚举 | 140fccbf0 的 15 个 `Dir*` 字符串 |
| 视图两级派生 | ViewDir→ViewDirBase 110 个目标函数；ViewDirSync→ViewDirBase 20 个目标函数 |
| 视图无静态外部调用者 | 对 BcViews/BcSession/BcStartup/ViewSession/UiMainControl 全量扫描，引用 0 |
| Op 属于 Dir 模块 | assertion 路径 `Source\Dir\Op\OpBase.pas` 等 5 个 |
| 报告复用 BcReport | DlgDirReport→BcReport 89 个目标函数；DlgDirReport 自有字符串仅目录专有项 |
| DSL 关键字集 | DlgDirScript 37 个去重字符串（见 §3.6） |

清单文件：`inventory/*.tsv`（`entry`/`size`/`confidence`，按 size 降序，CRLF，
与 `../ss/inventory/SsLineList.tsv` 格式一致）。
