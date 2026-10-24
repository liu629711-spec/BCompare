# BCompare 差异算法逆向报告

生成时间：2026-10-12
目标：`D:\bc-official\app\BCompare.exe`
SHA-256：`4e44c526722d6420e89b372460c519e293c417723305b83ed0eff853db16ce5d`

---

## 一、本轮挖到的结论

**核心差异算法已定位并确认：BC 用的是 Myers 线性空间算法（middle-snake 双向搜索），与 GNU diff / Git 同源。**

逐层挖到的路径：

```
BcAlign.pas（对齐核心，薄封装）
  └─ FUN_140dc5d80 / FUN_140dc4500   ← 对齐引擎
       ├─ 剥离公共前缀 / 公共后缀
       └─ FUN_140dc60b0             ← Myers 核心搜索
            ├─ FUN_140dc6d80        ← 每轮 D 的进度回调（可取消）
            ├─ FUN_140dc6c40        ← 差异记录分派（删除/插入/替换）
            │    ├─ FUN_140dc6a00   ← 左独有行记录
            │    └─ FUN_140dc6b20   ← 右独有行记录
            └─ 递归（分治）         ← 线性空间的分治实现
```

---

## 二、Myers 算法的证据链

### 1. V 数组布局 = 教科书 Myers

`FUN_140dc5d80` 里分配了两个数组，大小 `(2*D_max+1)*4` 字节：

```c
local_20 = FUN_140009a00((*(int *)(param_1 + 0x78) * 2 + 1) * 4);
local_28 = FUN_140009a00((*(int *)(param_1 + 0x78) * 2 + 1) * 4);
*(longlong *)(param_1 + 0xa8) = local_20;   // 正向 V
*(longlong *)(param_1 + 0xa0) = local_28;   // 反向 V
// 基址前移，使对角线索引可为负
... - (0xffffff - *(int *)(param_1 + 0x78)) * 4;
```

对角线索引范围 `-D..+D`，数组长度 `2D+1`，这就是 Myers 的 V 数组。基址用 `0xffffff`（= 2^24-1）前移以允许负索引，是典型的手写实现技巧。

### 2. 双向搜索 + 奇偶 delta 重叠检测

`FUN_140dc60b0` 同时推进正向（偏移 `0xa8`）和反向（偏移 `0xa0`）两条搜索：

```c
uVar8 = (param_4 - param_2) - (param_5 - param_3);   // delta = 左右长度差
...
for (iVar10 = -iVar9; iVar10 < -(param_5 - param_3); iVar10 += 2) { }   // 前空隙
for (; iVar10 <= iVar6; iVar10 += 2) {                                   // 正向推进
    ...
    if (((uVar8 & 1) != 0) && ((int)(uVar8 - iVar9) < iVar10) &&
        (iVar10 < (int)(iVar9 + uVar8)) &&
        (V_back[iVar10] <= V_fwd[iVar10])) {        // ← 重叠判定
        ...
        cVar3 = FUN_140dc60b0(param_1, param_2, param_3, local_30, local_2c);  // 左半递归
        uVar4 = FUN_140dc60b0(param_1, iVar1, iVar2, param_4, param_5);        // 右半递归
        return uVar4;
    }
}
```

三个特征同时出现，只有 Myers 线性空间算法符合：
- **步长为 2 的对角线遍历**（`iVar10 += 2`）——因为对角线奇偶性固定
- **`delta & 1` 奇偶分支**——正向搜索只在 `delta` 为奇数时检测重叠，反向索引互补
- **重叠后立即二分递归**——这就是 O(ND) 空间优化成 O(N) 的"分治"关键

### 3. 公共前后缀裁剪

`FUN_140dc5d80` 在进入核心搜索前先剥离首尾：

```c
while (... (left[local_30] == right[local_34])) { local_30++; local_34++; }   // 公共前缀
while (... (left[local_38] == right[local_3c])) { local_38--; local_3c--; }   // 公共后缀
if ((local_38 < local_30) && (local_3c < local_34)) local_29 = 1;             // 完全相同，提前返回
```

这是所有高性能 diff 实现的标准预处理（BC、Git、GNU diff 都做）。

### 4. 差异段游程合并

`FUN_140dc6a00`（左）与 `FUN_140dc6b20`（右）不是简单输出单行，而是**判断能否并入已有差异段**：

```c
if (param_2 == *(int *)(lVar2 + 4)) {          // 与上一段相邻？
    if (上一段的末尾 == 当前行) {
        *(int *)(lVar2 + 0xc) += 1;            // 长度+1，并入
    } else {
        FUN_140dc6860(...); FUN_140dc6970(...); // 否则新开一段
    }
}
```

`+0xc` 是段长度计数器，`+4`/`+8` 是起始行号。这正是 BC 界面里"差异段"（diff section）的数据来源——也是它比裸 diff 更好用的原因。

`FUN_140dc6c40` 分派三种记录：
- `param_6 == 0` → 左独有行（删除）
- `param_6 == 1` → 右独有行（插入）
- `param_6 == 2` → 左右都记（替换）

### 5. 可取消设计

`FUN_140dc6d80` 每轮 D 迭代回调一次：

```c
if ((*(ulonglong *)(param_1 + 200) & 0xffffffffffff0000) != 0) {
    (**(code **)(param_1 + 200))(*(undefined8 *)(param_1 + 0xd0), param_1);
}
```

这解释了 BC 为什么能在比对超大文件时显示进度并允许取消。

---

## 三、意外收获：BC 的完整内部模块结构

这是本轮最有价值的发现，**比算法本身更有用**。

BC 的断言宏会嵌入源码路径，而这些字符串**原样编译进了发布版二进制**：

```
C:\BCBuild\BCompare\Source\Ss\SsPersistent.pas
```

我提取出 **271 条源码路径、190 个 BC 自有单元**，模块划分完整暴露：

| 模块 | 单元数 | 代表单元（名字即用途） |
|---|---|---|
| `Source\Bc\` | 62 | **BcAlign.pas**（对齐核心）、**BcAlignLines.pas**（行对齐）、BcFileFormat.pas、BcSyntaxElements.pas、BcSession.pas |
| `Source\Text\` | 15 | **TextMap.pas**（差异映射）、TextContent.pas、TextFormat.pas、TextREParser.pas、TextSession.pas |
| `Source\Ss\` | 15 | **SsLineList.pas**（行存储）、**SsLineParse.pas**（行解析）、SsXML.pas、SsCodePage.pas |
| `Source\Dir\` | 20 | DirSession.pas、DirFilters.pas、Op\OpSync.pas、Sync\ViewDirSync.pas |
| `Source\Ui\` | 21 | UiVirtualListBox.pas、UiMapTreeView.pas、UiSpeedBar.pas |
| `Source\Vfs\` | 17 | VfsFtpResourceImpl.pas、VfsOneDriveResourceImpl.pas、VfsWebDAVResourceImpl.pas |
| `Source\Table\` | 11 | TableMap.pas、TableDetect.pas、TableRules.pas |
| `Source\Pix\` `Hex\` `Reg\` `Ver\` `Media\` | 25 | PixMap.pas、HexMap.pas、RegMap.pas、VerRules.pas |

注意 **`*Map.pas` 的命名规律**：`TextMap` / `TableMap` / `PixMap` / `HexMap` / `RegMap` —— 每种内容类型都有对应的"差异映射"抽象，共享同一套对齐框架。这解释了一个架构级问题：**BC 为什么能在多种数据类型上做统一的差异展示**。

副产品：这条路径线索让函数定位从"猜函数名"（不可能，符号已剥离）变成"按模块查地址"，效率提升极大。

---

## 三之补：重要性判定（BC 最核心的差异化功能）

挖 Myers 的过程中顺带打通了重要性判定链路。

### 数据结构：每行一个"不重要"标志

`BcSyntaxElements.pas` 的 `FUN_140de5840` 维护一个**有序 int 数组**，存所有被标记为"不重要"的行索引：

```c
bVar1 = FUN_140de51f0(param_1, param_2, &local_2c);   // 该行当前是否不重要
bVar2 = FUN_140de5a40(param_1, param_2);              // 该行应有的目标状态
if ((bVar1 ^ bVar2) != param_3) {                     // XOR：需要翻转
    // 在 local_2c 处插入 / 删除（二分结果直接当作插入点）
    FUN_14000a390(...);                               // memmove 腾挪
    *(int *)(param_1[3] + local_2c * 4) = param_2;
    *(int *)(param_1 + 2) += 1;                       // 计数
}
```

查询是标准二分（`FUN_140de51f0`，`>>1` 折半维护边界），复杂度 O(log n)。数组长度记录在 `param_1[2]`，向量指针在 `param_1[3]`。

### 判定规则：两类语法元素强制重要

`FUN_140de5a40` 是目标状态判定器，规则极其简洁：

```c
if ((param_2 == 6) || (param_2 == 9)) {
    uVar2 = 0;      // 返回 0 = 不是"不重要" = 强制重要
} else {
    uVar2 = 1;      // 其余可判为不重要
}
```

`param_2` 是**语法元素类型索引**。把它与 `BCFILEFORMATS.xml` 里真实的元素顺序对齐后（CPP 为例）：

| 索引 | 元素 | 是否可判为不重要 |
|---|---|---|
| 0 | Keyword | 可 |
| 1 | Identifier | 可 |
| 2 | Number | 可 |
| 3–5 | String | 可 |
| **6** | **Directive**（`#include` 等） | **否 — 强制重要** |
| 7–8 | Comment | 可 |
| **9** | **Operator**（`{` `}` `(` `+` 等） | **否 — 强制重要** |

设计意图很清楚：**改一个预处理指令或一个运算符，语义影响太大，绝不允许被折叠成"不重要差异"**。其余元素（关键字、标识符、数字、字符串、注释）才允许按用户配置的 CaseSig / 权重规则判定。

这解释了 BC界面里那个经典行为：把"忽略大小写差异""忽略空白差异"打开后，`int x` 与 `Int X` 被标为不重要，但 `#include` 变动和运算符变动永远高亮。

### 规则来源：用户可配置的部分

`FUN_140da9ad0`（已反编译）解析语法规则 XML，暴露出完整的可配置 schema（70 个字段），其中与重要性直接相关的：

```
CaseSensitive  IdentifierCaseSig  KeywordCaseSig  NumberCaseSig   StringCaseSig
CommentCaseSig DirectiveCaseSig   OperatorCaseSig LabelCaseSig    LineNumCaseSig
IndentCaseSig  EnvironVarCaseSig  CustomElementCaseSigs          Weights
```

`*CaseSig` = 大小写重要性（0=忽略 / 1=区分），`Weights` = 各元素类型的权重表。用户可在 BC 的"重要性"标签页里改这些值——它们最终就落在上面那套有序数组的增删逻辑里。

### 复刻要点

重要性判定不依赖 Myers，是独立的预处理/后处理层：
1. 按文件格式的语法规则对每行分词
2. 对差异行做逐元素比对（大小写、空白、权重）
3. 全部差异元素都"允许不重要"且命中用户规则 → 该行进入不重要集合
4. 渲染与统计时按该集合分级显示（重要/不重要/被忽略三级，与 `RES_CODES` 里的统计文案一致）


---

## 四、可复刻的算法规格

基于伪代码，BC 文本对齐的最小复刻路线：

1. **行哈希**（`left[i]` / `right[j]` 是 `int`，说明先做了行→哈希的归约），配合 `TextFormat.pas` 的词法规则决定"何种差异算重要"
2. **公共前后缀裁剪**（几行代码，收益极大）
3. **Myers O(ND) 双向搜索**：V 数组 `2D+1`，对角线步长 2，`delta` 奇偶分支检测重叠
4. **重叠后递归分治**（把空间从 O(ND) 降到 O(N)）
5. **差异段游程合并**：相邻差异行合并为一个可折叠段

第 1 步的哈希归约 + 第 5 步的段合并，是 BC 相比裸 Myers 的工程增量。

---

## 五、下一步可挖方向

至此数据层与算法层的关键路径都已打通。继续深挖的选项：

| 方向 | 目标函数 | 价值 |
|---|---|---|
| **重要性判定**（为什么某些差异被标为"不重要"） | `TextFormat.pas` / `BcSyntaxElements.pas` 关联函数 | 复刻 BC 的差异分级能力，这是它最核心的差异化功能 |
| **对齐规则引擎**（`AlignWith`、自定义对齐） | `FUN_140db7710`（已反编译，解析 Align/Keys/Custom XML） | 复刻手工对齐与规则对齐 |
| **词法解析器** | `SsLineParse.pas`（5 个函数）、`TextREParser.pas`（2 个） | 复刻分词与正则 |
| **三方合并** | `BcAlignLines.pas` 的策略类（vtable 分派） | 复刻合并语义 |

---

## 六、本轮产出的文件

| 文件 | 说明 |
|---|---|
| `extracted/source-modules.json` | **271 条源码路径 + 190 个模块 + 路径→函数映射** |
| `extracted/pseudocode/*.c` | **263 个函数的伪代码**（累计，0 失败） |
| `extracted/pseudocode/140dc60b0.c` | Myers 核心搜索（1,832 字节） |
| `extracted/pseudocode/140dc5d80.c` | 对齐引擎（V 数组分配 + 前后缀裁剪） |
| `extracted/pseudocode/140dc6a00.c` `140dc6b20.c` | 差异段游程合并器 |
| `extracted/pseudocode/140dc6c40.c` | 差异记录分派（删除/插入/替换） |
| `extracted/pseudocode/140db7710.c` | 用户对齐规则 XML 解析器 |
| `extracted/pseudocode/140da9ad0.c` | 语法规则解析器（70 个字段 schema） |
| `tools/extract-source-modules.py` | 从断言路径提取模块结构 |
| `tools/map-algorithm-functions.py` | 按模块名把算法单元映射到函数地址 |
| `tools/ghidra-scripts/BatchDecompile.java` | 批量反编译（一次 JVM 跑完整个波次） |
| `extracted/wave1..7-addresses.txt` | 各波次的目标清单（可复用、可扩展） |

---

## 七、工具链现状

```bash
# 单函数（8 秒）
python tools/ghidra-persistent.py decompile 0x140dc60b0

# 批量（一次 JVM，百级函数约 5 分钟）
python tools/ghidra-persistent.py batch wave.txt --out-dir extracted/pseudocode

# 字符串 → 函数
python tools/ghidra-persistent.py string-index

# 源码模块结构
python tools/extract-source-modules.py
python tools/map-algorithm-functions.py
```

持久化项目 `D:\Rea\ghidra-project`（1.2 GB）已包含完整分析，所有查询秒级响应，无需再付 25 分钟重分析成本。
