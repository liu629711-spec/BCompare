# SsBcd.pas 规格（第一遍·架构级）

> 逆向来源：语料精读 + 剪贴板格式串全表（91 函数；巨头 6 个）。地址段 14052cxxx–140530xxx。日期 2026-10-13。
> 单元身份：**Bcd = Binary/Character Data 层**——十六进制视图的数据模型 + 与外部十六进制编辑器的剪贴板互操作。

## 1. 剪贴板格式兼容层（14052ebf0，3248B，栈帧含 3976B 缓冲）

BC 的十六进制视图能**粘贴来自 15 种以上十六进制编辑器的二进制数据**，格式串全表（实测）：

| 外部工具格式 | 其他 |
|---|---|
| `010 Editor Binary Data` | `CF_TEXT` / `CF_UNICODETEXT` |
| `AviHex DataSize` / `AviHex RawData` | `BinaryData` |
| `CygnusBinary` | `CMBINARY` |
| `HEdit binary data` | `FileContents` |
| `Hex Workshop Binary Data` | `FileGroupDescriptor` / `FileGroupDescriptorW` |
| `Hexprobe HEX-Data` | `JGsoft Editor Data` |
| `MFCX` | `RLE32HexBinary` |
| `RegEdit_HexData` | `Rich Text Format` |
| `Size Information` | `System.String` |
| `WinHex Data` | `application/madedit-hexdata` |

- `AviHex DataSize`/`Size Information` = 数据长度伴随格式；`FileGroupDescriptor` = 文件拖放；`Rich Text Format`/`CF_TEXT` = 文本回退。
- 语义：按格式优先级依次尝试（二进制格式优先，文本格式按十六进制文本解析）→ 构建 Bcd 数据对象。

## 2. 其他函数

- 1405301a0（824B）：`RegEdit_HexData` 专用解析（注册表编辑器十六进制格式：`hex:...` 行式）。
- 1405305d0（926B）：测试/校验串（`aaaaaaaa`/`bbbbbbbb`/...——疑为十六进制解析的自检表）。
- 14052d7b0/14052ca90/14052e510：数据模型操作 [二遍]。

## 3. 与 SsClasses 的接口

SsBcd 消费 SsClasses 的字符集/区间设施（1410034d0 字符类节点调用链回溯至此域）——十六进制字符判定（0-9a-fA-F）走**全局空字符集占位 + 静态表**混合路径。

## 4. 可测试锚点

1. 剪贴板格式优先级顺序（二进制格式 → 文本回退）。
2. RegEdit_HexData 行式解析（`hex:` 前缀、换行分块）。
3. 十六进制文本解析容错（空白/大小写）。

## 5. 未解之谜

1. [?] 14052ebf0 的格式探测顺序（列表内优先级）。
2. [?] Bcd 数据对象的内部表示（byte 数组 + 行/列布局？）。
3. [?] 六个巨头函数的分工（数据模型 vs 剪贴板 vs 视图协作）。
