# 前端 UI 规格 — Delphi DFM 窗体资源完整解码

> 证据来源:BCompare.exe 的 PE 资源目录(RT_RCDATA)。
> 生成工具:`tools/dfm-extract.py`。
> 产物:`extracted/forms/*.dfm`(211 个)+ `forms-index.json`。
> **结论:BC 的整个前端界面是结构化数据,不是"只能照截图重画"。**

## 1. 这个发现的意义

我最初判断"GUI 只能靠截图重画"。**这是错的**。Delphi 编译器把每个窗体(Form / Frame / Dialog)
的完整定义作为二进制 DFM 流写进 EXE 的 RCDATA 资源。解码它得到的是**与原始设计等价的
结构化描述**,包括:

| 内容 | 是否可得 | 说明 |
|---|---|---|
| 控件树(父子/嵌套) | ✅ 完整 | 精确到每个 Panel/Button/Label 的从属关系 |
| 几何(Left/Top/Width/Height) | ✅ 完整 | 设计期坐标,像素级 |
| 对齐/锚点(Align/Anchors/Constraints) | ✅ 完整 | 布局行为规则,不只是静态位置 |
| 文字(Caption/Text/Hint/HelpKeyword) | ✅ 完整 | 含 `&` 加速键、`|` 分隔的 Hint 结构 |
| 控件类名(TUiBtnPanel / TDirView …) | ✅ 完整 | 直接给出 VCL 类层次线索 |
| **事件处理函数名**(OnClick = JobCancelClick) | ✅ 完整 | 1,821 条绑定 → 与反编译的 Pascal 函数名对接 |
| 图片来源(Images = BcImages.MainImages, ImageIndex) | ✅ 完整 | 指向 TBCImages / PNG 资源 |
| 集合(StatusBar.Panels / 列定义 / 树列) | ✅ 完整 | 多值属性逐项还原 |
| Tab 顺序 / 焦点顺序 | ✅ 完整 | TabOrder 字段 |
| 字体 / 颜色 | ✅ 完整 | Color / Font.* 值 |
| 具体像素渲染结果 | ⚠️ 需主题引擎 | 由 VCL + 主题位图运行时合成,见 §5 |

## 2. 解码格式(二进制 DFM / `TPF0`)

从字节层反推并验证的完整文法:

```
DFM      := 'TPF0' Object
Object   := Prefix? ClassName ShortStr InstanceName ShortStr
            (PropName ShortStr Value)* ShortStr(空)
            Object* 0x00
Prefix   := 0x00  |  0xF<flags> [Value]      ; flags bit1 = ffChildPos,后跟位置值
Value    := 0x00 (vaNull,终止符)
          | 0x01 (vaList) Value* 0x00
          | 0x02 vaInt8 | 0x03 vaInt16 | 0x04 vaInt32 | 0x19 vaInt64
          | 0x05 vaExtended(10B) | 0x0F vaSingle(4B) | 0x15 vaDouble(8B)
          | 0x10 vaCurrency | 0x11 vaDate
          | 0x06 vaString  → ShortStr(字节长度)
          | 0x0c vaLString → int32 长度 + ANSI 字节
          | 0x14 vaUTF8Str → int32 长度 + UTF-8
          | 0x12 vaWString → int32 字符数 × 2 + UTF-16LE
          | 0x07 vaIdent → ShortStr
          | 0x08 vaFalse | 0x09 vaTrue | 0x0D vaNil
          | 0x0A vaBinary → int32 长度 + 原始字节(图片数据等)
          | 0x0B vaSet    → ShortStr* 0x00
          | 0x0E vaCollection → Item* 0x00
Collection := Item := 0x01 (PropName Value)* 0x00     ; 属性终止符兼作 item 终止符
ShortStr := len:u8 [转义:len&0xF0==0xF0 时低半字节 n = 后续 n 字节小端整数为真实长度] + 字节
```

**三个关键坑**(都是先失败后定位):
1. **ShortString 转义**:`f1 0c` 不是长度 241,而是"低半字节 1 = 后面 1 字节是真实长度 0x0c"。
   这是 Delphi `TReader.ReadStr` 的约定,出现在字符串 >255 或含特殊字节时。
2. **对象前缀字节**:`f2 02 00` 出现在上次对象结束与下个子对象之间,不是字符串。
   高位半字节 F = 带标志,bit1(ffChildPos)后跟一个类型化整数。
3. **vaLString ≠ vaString**:前者 int32 长度前缀,后者单字节长度。混用会导致中段失步。

## 3. 窗体清单(211 个,分类)

完整机器可读清单:`extracted/forms/forms-index.json`(含每窗体的对象数、事件数、字节数)。

### 3.1 顶层视图(11 个视图类型的主体)
```
THOMEVIEW, TFOLDERVIEW??  → THOMEVIEW / TDIRVIEW / TFILEVIEW / TTEXTVIEW /
                             THEXVIEW / TTABLEVIEW / TREGVIEW / TVERVIEW /
                             TMEDIAVIEW / TPIXVIEW / TBCVIEW / TEMPTYVIEW
每个视图配套: T*ACTIONS(命令定义) + T*SESSION*FRAME(会话选项页)
```
> 对照 BC 官方 Goto 视图列表可确认 11 视图假说:**Home / Folder / Text / Hex /
> Table / Registry / Version / Media / Picture / BC(内容) / Empty**。

### 3.2 会话选项框架(Options 对话框的每一页 = 一个 Frame)
`TDIRSESSION*FRAME`(Comparison/Handling/Misc/NameFilter/OtherFilters/Specs)、
`TDIRSYNCSESSION*FRAME`、`TFILESESSION*FRAME`、`TLINESESSION*FRAME`、
`TTEXTGRAMMARITEMDIALOG`、`TFILEFORMAT*FRAME` 等 → 直接对应 BC 的
Tools→Options 树形结构。

### 3.3 对话框(操作类)
`TOPC*`(文件操作:Copy/Move/Delete/Rename/Touch/Attrib/NewFolder/Merge…)、
`TDIR*DIALOG`、`TFILE*DIALOG`、`THEX*DIALOG`、`TREG*DIALOG`、`TBCDIALOG`。

### 3.4 VFS / Profile 配置
`TVFS*FRAME`(FTP/SFTP/SVN/Dropbox profile 页)、`TPROFILE*`。

### 3.5 资源型窗体(非界面)
`TBCIMAGES*`(12 个:主/125%/150%/200%/Dark 变体)、`TABOUTDIALOG` 等。

## 4. 事件绑定 → 代码对接

1,821 条 `OnXxx = HandlerName` 直接给出**方法名**。结合 `function-attribution.json`
的单位归属,可以定位处理函数所在单元与地址,例如:

```
TDIRVIEW.dfm:  OnClick = JobCancelClick
   → 反编译语料中搜 JobCancelClick → 所属单元/地址 → 读实现
```

这是**前端到后端的完整链路地图**:每个按钮点下去调用哪个函数,可以逐条连起来。

## 5. 边界:DFM 不能给出的东西

| 缺失项 | 原因 | 替代手段 |
|---|---|---|
| 运行时主题渲染结果 | VCL + 主题位图合成,非窗体定义 | `TBCIMAGES*`/PNG 资源已可提取,可重建 |
| 运行时计算布局 | 依赖当前 DPI/字体,由代码在 `FormResize` 等里算 | 事件处理函数名已知 → 反编译读逻辑 |
| 动态创建的控件 | 运行时 `Create` 而非设计期 | 反编译 `FormCreate` 等 → 语料已具备 |
| 字符串本地化表 | 在 STRING 资源(340 条)与代码内常量 | 已可提取 |
| 菜单项的完整层级 | 部分菜单设计期在 DFM,部分运行时构建 | 两者结合 |

**结论**:静态界面骨架 100% 可得;动态部分靠"已知事件处理器名 → 反编译"打通。
剩下来的是**渲染引擎**(自绘控件如 `TUiVirtualListBox` 的绘制代码)需要逐类逆向——
这也是后端工作,不是"照抄截图"。

## 6. 待办扩展

- [ ] 提取 ICON(74)/BITMAP(17)/GRP_ICON(16)/PNG(58)/CURSOR(38) 资源 → 图标主题重建
- [ ] 提取 STRING(340)资源 → 界面文本/本地化
- [ ] `TBCIMAGES` 系列(12 个,最大 2.5MB)含 Photoshop 级主题位图 → 直接可用
- [ ] 事件处理器名 → attribution 单元映射表(自动生成)
- [ ] 自绘控件绘制逻辑清单(`TUi*` 类 → 反编译)

## 7. 类骨架清单（PE VMT 直读，2026-10-13 补充）

**工具**：`tools/delphi-classes.py` → `extracted/delphi-classes.json`（**5,121 个类**，含 VMT 地址与类名）。
Delphi x64 VMT 布局（实证 vs `TSsPersistentParent @ 0x14067bee8`）：
**`vmtClassName` 在 VMT−0x50**，指向 ShortString（首字节=长度，随后 ASCII）。
（早期误按 −0x88 读取会得到乱码；−0x50 才是正确偏移。）

### 7.1 视图家族（11 个，每个 = View / CompareView / ViewState 三元组）

| 家族 | View VMT | CompareView VMT | ViewState VMT | 对应 DFM |
|---|---|---|---|---|
| Dir（文件夹比较） | `0x141b42e88` | `0x141b479c0` | — | TDIRVIEW / TDIRSESSION*FRAME |
| DirMerge | `0x141b48420` | — | — | TDIRSESSION* |
| DirSync | `0x141b5f1a0` | — | — | TDIRSYNCVIEW |
| Text | `0x141b881b8` | — | — | TTEXTVIEW |
| File（文件信息） | `0x14181b838` | — | `0x14181b368` | TFILEVIEW |
| Hex | `0x141bbdf90` | `0x141bc0798` | `0x141bbd1d0` | THEXVIEW |
| Table | `0x141c1af70` | `0x141c1f6e8` | — | TTABLEVIEW |
| Registry | `0x141bf3a60` | `0x141bf6658` | `0x141bf2648` | TREGVIEW |
| Version | `0x141c39688` | — | — | TVERVIEW |
| Media | `0x141bce658` | `0x141bd07d0` | `0x141bcd4c8` | TMEDIAVIEW |
| Picture | `0x141bdef20` | `0x141be24b8` | `0x141bde380` | TPIXVIEW |

另有：`TEmptyView` `0x140fb0508`、`THomeView` `0x141830190`、`TBcView` `0x140faca70`、
`TSessionView` `0x141813970`、`TDirTreeView` `0x140fc3778`、`TDirBaseView` `0x141b1ef20`。
基类：`TView` `0x140eda538`、`TViewForm` `0x140edbf20`、`TViewCommands` `0x140e6d498`。

### 7.2 会话类层次（Dir 模块）

| 类 | VMT | 说明 |
|---|---|---|
| `TDirBaseSession` | `0x140e4dae8` | 基类（BcSession 族） |
| `TDirSession` | `0x140f57290` | 通用目录会话（488 B 实例） |
| `TDirCompareSession` | `0x140f58330` | "Folder Compare" |
| `TDirMergeSession` | `0x140f588b8` | "Folder Merge"（3-way） |
| `TDirSessionState` | `0x140f33698` | 状态对象（152 B，持 `+0x8A` 比较模式） |
| `TDirCompareSessionState` | `0x140f34300` | 两方状态 |
| `TDirMergeSessionState` | `0x140f34568` | 三方状态 |
| `TBcState` | `0x140dc0380` | 全局应用状态（对应 BCState.xml） |

### 7.3 第三方组件确认（类名前缀 → 厂商）

| 前缀 | 类数 | 厂商 / 用途 |
|---|---|---|
| `TEl*` (TElXML/TElBu/TElPG/TElSS…) | 172+68+62+28 | **SecureBlackbox**（XML 安全 / 加密 / PGP / SSH / TLS） |
| `TXlsx*` / `TEscher*` / `TChart*` | 121+35 | **FlexCel**（Excel / 图形记录） |
| `TId*` (TIdFTP…) | 76+ | **Indy 10**（FTP/网络） |
| `TChar*` | 87 | 字符 token 层（可能是 Abbrevia 或自有） |
| `TCust*` | 90 | VCL 自定义基类 |
| `TPlCP*` | 37 | 代码页表 |

> **对克隆的意义**：这些是**付费/开源第三方库**，我们的实现只需在行为上等价
> （FTP/SFTP 用 Rust 原生库；Excel 解析用我们自己的实现或开源替代），
> 不必也不应复刻其内部类结构。

## 8. UI → 代码链接图（自动生成，2026-10-13）

**工具**：`tools/ui-event-map.py` → `extracted/ui-event-map.json`。

**方法**：DFM 里的 `OnXxx = HandlerName` 给事件处理器名；Delphi 把 published 方法名作为
ShortString 存在类 RTTI 表里，**紧跟其后就是该方法码指针**。扫描"长度字节+名字"的
ShortString，在其后 0x40 字节内找落于 `.text` 的指针，即得方法地址；再经
`function-attribution.json` 映射到单元。

**结果**：555 个不同处理器，**555/555 全部解析到代码地址**，其中 **365 个**名到具体单元。

### 8.1 处理器分布（按单元，Top 30）

| 单元 | 处理器数 |
|---|---|
| `DlgProgOptions.pas` | 66 |
| `ViewHome.pas` | 50 |
| `ViewPix.pas` | 22 |
| `ViewText.pas` | 19 |
| `ActnGeneral.pas` | 19 |
| `FrameDirSessionComparison.pas` | 17 |
| `DlgTextWeightItem.pas` | 17 |
| `DlgImport.pas` | 15 |
| `DlgProfileManager.pas` | 14 |
| `FrameFileFormat.pas` | 10 |
| `FrameTableSessionColumns.pas` | 10 |
| `ViewDirBase.pas` | 9 |
| `DlgReport.pas` | 8 |
| `FrameTextSessionImportance.pas` | 8 |
| `DlgFileFormatManager.pas` | 7 |
| `FrameFileFind.pas` | 7 |
| `OpSync.pas` | 6 |
| `DlgProfileFileOpen.pas` | 5 |
| `VfsZipForgeResourceImpl.pas` | 4 |
| `DlgProfileBrowse.pas` | 4 |
| `DlgExport.pas` | 3 |
| `HTTPGet.pas` | 3 |
| `FrameHexFind.pas` | 3 |
| `ViewTable.pas` | 3 |
| `OpBase.pas` | 3 |
| `DlgRegBrowse.pas` | 3 |
| `ViewDirSync.pas` | 3 |
| `ViewSession.pas` | 2 |
| `DlgTableSort.pas` | 2 |
| `BcStartup.pas` | 2 |

### 8.2 用法示例

```
DlgProgOptions.pas   66 个  ← Options 对话框是最大的单窗体逻辑
ViewHome.pas         50 个  ← 主页视图
ViewText.pas         19 个  ← 文本视图交互
FrameDirSessionComparison.pas 17 个 ← 目录会话"比较"选项页
ViewDirBase.pas       9 个  ← 目录视图基类交互
OpSync.pas            6 个  ← 同步操作
VfsZipForgeResourceImpl.pas 4 个 ← ZIP 虚拟文件系统
```

例：`AlignWithsCloneClick → 0x141b192a0 → FrameDirSessionComparison.pas`
（"对齐方式"列表的克隆按钮）。这条链路让每个控件的每个事件都能直达反编译源码。

### 8.3 剩余 190 个未映射的原因与后续

190 个处理器指向的地址**不在 BC 自研函数的 19,014 个归属表里**——它们多为
RTL/VCL 内部方法或编译时内联，属正常。要补全可用 `tools/ghidra-persistent.py decompile <addr>`
逐个取（或 REA）——但这批本来就是 VCL 标准行为，对克隆无信息量。
