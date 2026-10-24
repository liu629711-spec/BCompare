# BCompare 逆向工程结果（v1）

## 数据层（已完成）

### 1. 资源文件提取
- **总 RCDATA**: 243 个块（全部已提取并 SHA256 校验通过）
- **TPF0 流**: 211 个 Delphi 序列化对象文件
- **zlib 解压**: 3 个压缩块 → RES_CODES(223KB), PRESETSHAPES_XML(561KB), PRESETTABLESTYLES_XML(537KB)

### 2. BC 组件类清单（按频次排序，前 25）
```
TUiPanel                  77
TUiAction                50
TUiLabel                 19
TUiActionList            14
TUiBtnPanel              14
TUiActionTree            14
TUiCheckBox               9
TUiWindowShape            9
TUiStatusBar              9
TUiActivePanelView        7
TUiBevel                  5
TUiButton                 5
TUiVirtualListBox         4
TUiActivePanel            4
TUiListBox                4
TUiOkBtn                  2
TUiTreeView               2
TUiRadioButton            2
TLogFrame                 2
TVerView                  1
TSccChooseProviderDialog  1
THomeView                 1
... (共 440 有效对象，另 1.37M 字节因对齐跳过)
```

### 3. 属性名清单（频次，前 10）
```
HelpType    80
Caption     68
Top         44
ClientHeight 40
Hint        39
TabOrder    33
Height      22
Width       15
Nodes       14
BorderStyle 13
```

### 4. TTextActions 命令表（样本）
从 `TTEXTACTIONS.bin` 解析出：
- **SelectAllAction** — Hint: "Select All|Selects all visible lines."
- **ExistsNextAction** — Hint: "Next Existing Line|Positions at next existing line..."
- **TogSameAction** — Caption: "&Toggle Same", Hint: "Shows or hides same lines."
- **TogLeftOrphanAction** — Caption: "Toggle Left Orphans", Hint: "...left orphan lines"
- **FileFormatAction**, **ImageIndex** (tag 0x07 未解码)
- Tree 结构包含嵌套节点（tag 0x01 二进制 blob）

---

## 格式层（已完成）

BCFILEFORMATS.xml 定义了 25 个内建文件格式的语法层：

### 文本格式类型示例
- **BASH / CPP / JAVA / HTML / XML / Python** 等共 19 种 `TTextFormat`
- **CSV / Excel** (`TTableFormat`)
- **图片 / 媒体** (`TPixFormat` / `TMediaFormat`)
- **EXE 版本信息** (`TVerFormat`)

每个格式的**差异判定规则**包括：
- **关键词清单**：每格式若干关键字（如 C++ 有 @autoreleasepool, @catch, @class, auto, bool 等）
- **正则 Token**：Identifier=`[_a-z]\w*`, Number=`\d+(\.\d+)?`、`0x[a-f\d]+`, String=`$?"` / `"\"`
- **终止条件**：StopText (行内终止符如 `'`, `"`, `*/`, `-->`, `\n`, `=end.*`)
- **分隔符**：DlmDelimiters (逗号 `,`), DlmQualifier (引号 `"`)
- **制表符处理**：TabAsSpaces=True, TabSize=4/2
- **大小写敏感**：CaseSensitive=False

这些规则直接告诉 Diff 引擎：**如何把一行文字切分成带类型（Keyword/Identifier/Number/String）的 token 序列**——这才是文本对齐的基础。

---

## 原生层（分析快照已就绪）

Ghidra 12.1.4 自动分析完成（用时 24 分钟）：
- **证据 ID**: `ev_fb02018089d3142fa2575028fa89c42abe62ea53da0fb959f4f60efb6ccf1c7b`
- **函数数**: 122,610
- **字符串**: 63,312
- **PE 段**: 13
- **快照**: `D:\Rea\extracted\bcompare.snapshot.json`（8.4KB）

快照可用于后续 MCP 调用（open_binary 时指定 `snapshot_path`），避免重复加载；但当前工具链对快照的查询存在超时限制，需要更直接的 CLI 方式提取具体函数伪代码。

---

## 下一步建议

1. **解码未知值标签**（tag 0x01/0x07/0x03...）→ 捕获 ImageIndex/Category/ShortCut 等属性
   - 方法：参考 Delphi VCL 的 ReadValue 协议实现多值类型支持
2. **全量动作树导出** → TUiActionTree 的 Nodes  blob（vtBinary）含菜单层次结构
3. **算法函数定位** → 通过 CLI `rea decompile --procedure <name>` 获取伪代码：
   - 搜索候选名：`DiffAlign`, `CompareLines`, `MergeThreeWay`, `Tokenize`, `FindBestAlignment`
   - 或从字符串引用反查：先找到包含 "diff" 字符串的地址，再用 xrefs 追溯

如需继续（尤其是算法层的 pseudo_code 抽取），请告知是否要我继续用 CLI 方式深挖 Ghidra 函数，或转向公开算法自建路线（此时已有完整词法规则，可立即启动原型开发）。

--- 

*报告生成时间：2026-10-12*
