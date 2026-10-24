# SsLineList.pas 规格（第一遍）

> 逆向来源：Ghidra 反编译。原始源码 `C:\BCBuild\BCompare\Source\Ss\SsLineList.pas`。
> 125 个函数；本遍精读 5 个最大函数（3.3K/2.0K/1.4K/1.2K/1.2K 字节）+ 调用面。**未逐个读完**，标注 [?] 处待第二遍。

## 单元概览

TSsLineList = **分块(chunk)行存储容器**，文本比较器的内存行模型。三大特征：
1. 行数据分块存放（chunk 表 + 每 chunk 元数据），支持百万行级文件
2. **内置撤销栈集成**（编辑操作自动入栈）
3. **懒加载**：可挂接 TSsLineReader（SsLineParse 单元），行未读时从流拉取

## TSsLineList 对象布局（qword 槽位 → 偏移，二遍修正）

| 槽位 | 偏移 | 类型 | 含义 | 置信度 |
|---|---|---|---|---|
| [1] | +0x08 | Byte | 标志（读取中？） | 低 [?] |
| [2] | +0x10 | PPtr | 行记录指针表（动态数组，供快速按行号取） | 中 [?] |
| [3] | +0x18 | Int32 | 上表数量 | 中 |
| [4] | +0x20 | Int32 | **总字符数**（二遍修正：FUN_1406725b0 以字符增量调整它；FUN_140672a00 末行长度 = 总字符数 − 末行起始偏移） | 高 |
| [5] | +0x28 | Int64 | 与撤销栈顶比较的游标（编辑位置状态） | 中 [?] |
| [0xb] | +0x58 | Byte | Modified 标志 | 中 |
| [0xc] | +0x60 | Object | **撤销栈**（+0x10=深度；FUN_140129dc0=栈顶；FUN_140129b80=弹出） | 高 |
| [0xe] | +0x70 | Int32 | 读取器行游标状态（-1=无效） | 中 |
| [0x11] | +0x88 | Object | 关联 **TSsLineReader**（懒加载源） | 高 |
| [0x12] | +0x90 | Int32 | **行数**（元数据条目数；LocatePosition 二分上界） | 高 |
| [0x13] | +0x98 | PMeta | **行元数据数组**，每项 16 字节，见下 | 高 |

**行元数据记录（16B）**：
- `+0x00`：**union** —— 行已加载(flag=1)时 = **接口引用**（IInterface，FUN_140019af0 增减引用计数，FUN_14066c9e0 取出，断言行 0x1dd）；行未加载(flag=0)时 = **Int32 行字符长度**（FUN_14066cac0 取出，断言行 0x1e5）——**指针与长度原地复用**，未加载行只花 16 字节
- `+0x08`：Byte 加载标志
- `+0x0c`：Int32 **该行起始字符偏移**（全文件累计；LocatePosition 的二分键）

**虚方法**：vtable+0x10 = OnLineChanged(line*)；vtable+0x18 = EnsureLoaded；vtable+0x28 = SetText(text)。

## 位置模型（二遍已实读确认）

- `FUN_140672310(list, charPos) → (lineIdx, charIdx)`：**二分查找**起始偏移 ≤ charPos 的最后一行（对象 +0x90 行数为上界）；边界精确命中返回 (lineIdx, 0)，否则回退一行算 charIdx = charPos − 起始偏移
- `FUN_140672a00(list, lineIdx) → 行字符长度` = 下一行起始偏移 − 本行起始偏移（末行 = 总字符数 − 起始偏移）
- `FUN_1406725b0(list, fromLine, charDelta)`：**字符增量传播**——fromLine 起所有行的起始偏移 += charDelta，总字符数 += charDelta；断言总数不可为负（行 0x6ab=1707）。插入空行/删除字符共用此原语
- `FUN_14066e7d0(list, lineIdx, charIdx, count)`：**行拆分**——在 (lineIdx, charIdx) 处插入新元数据项（起始偏移 = 原偏移 + charIdx），把原行记录指针复制给新行（浅拷贝 + 接口增引），范围 count 行
- `FUN_14066e470(list, &lineIdx, &charIdx, absPos)`：**行合并/回退**——absPos<0 直接返回；断言行 0x348(840)：行已加载 或 (行长 + charIdx == absPos)；charIdx>0 时拆出新行；再处理"前一行未加载"时回退合并（把位置归并到前一行尾部，行 0x348 断言守门）
- `FUN_140673310(cursor, out, negate)`：**编辑事务位置记录** {delta = cursor[2]−cursor[0], start = cursor[0], simple = (delta≥1 && cursor[1]==1 && cursor[3]==0), negate 则 delta 取反}——上层编辑操作靠它传"净字符变化"
- `FUN_140672a90(list, lineIdx, idx)`：**取行文本**——已加载：从接口 chunk 的记录数组取（断言非空，行 0x70f=1807）；未加载：FUN_140673080 按绝对位置物化 [?]（该路径参数语义待第三遍）
- 撤销事务记录也走接口引用（FUN_14066c2d0，断言行 0x182=386：未提交标记 <0）

## 已精读的编辑操作

| 入口 | 大小 | 推断语义 | 关键证据 |
|---|---|---|---|
| 14066f0b0 | 3348B | **InsertLines(pos, lines)**：在 (行,列) 定位点拆行、插入行集合、处理行尾归属（新行吃旧行行尾：`HasEol` 标志分支） | 断言 0x3f1(1009)；`+0x98` 元数据 ±计数操作 |
| 140670060 | 2036B | **DeleteRange(pos, eolMode)**：删除定位点起的行内容；`param_4<0` = 连行尾一起删 | 断言 0x48c(1164)/0x4c4(1220)；vtable+0x10 通知 |
| 14066de20 | 1416B | **InsertText(pos, lines[])**：文本集合插入，尾部行与后文拼接（取尾行 EOL 融合） | 断言 0x2e5(741) |
| 1406718e0 | 1240B | **GotoLine/EnsureLineLoaded(idx)**：行越界时经 reader MarkPosition 拉取；撤销栈深 0x100(=256) 时弹栈并触发重置（`param_1[5] == 栈顶` 比对） | reader +0x88 交互直接可见 |
| 140670930 | 1217B | **SetChar/Overtype(pos, ch, flag)**：列位置改字符；`param_3<0` 走覆盖分支 | 断言 0x4ed(1261)/0x50e(1294)/0x4f0(1264) |
| 14066d640 | 688B | **GetLines(from, to) → 行集合**：区间抽取，`0x7fffffff` = 到文件尾 | 断言 0x29a(666)：位置必须有效 |

撤销事务模式：编辑前 `FUN_140673310(定位记录, 0/1)` 初始化事务；编辑后统一入栈（FUN_14066c2d0/FUN_14066c7f0 = 事务记录构造/提交）。

## 原始源码行号锚（Assertion failure 提取）

0x29a(666), 0x2e5(741), 0x3f1(1009), 0x48c(1164), 0x4c4(1220), 0x4ed(1261), 0x4f0(1264), 0x50e(1294) —— 可用于将来对照（若拿到泄漏/文档版源码可校准语义名）。

## Oracle 校准：对齐行为实测（2026-10-13，verify/golden）

| 模式 | 输入 → status 序列 |
|---|---|
| 纯插入 | `a c` → `a b c` = same, rightorphan, same |
| 纯删除 | `a b c` → `a c` = same, leftorphan, same |
| 块替换 | 3 行换 3 行 = same, different×3, same |
| 单行下移 | `a b c d`→`a c d b` = same, leftorphan, same×2, rightorphan |
| **块交换** | `ab cd`→`cd ab` = **leftorphan×2, same×2, rightorphan×2** |
| 重复行 | `x x x`→`x x` = same, same, leftorphan（从前对齐） |
| 空 vs 内容 | = rightorphan；双空 = 无 linecomp |

**关键语义**：BC 的 Myers 最短编辑脚本**不做移动/交换检测**——块交换按"左删右插"对齐（交换任意大小块时均为 orphan 对）。克隆实现必须复现此非直觉行为（不可自作聪明做 move detection）。重复行从前对齐（贪心最短脚本的自然结果）。

## 可测试行为锚点

1. 插入行吃掉原定位行的行尾：InsertLines 在行中间 → 原行内容成为首行（无行尾），新插入行居中，尾行继承原行尾
2. 删除到行尾 vs 删除含行尾的两种模式（param_4 符号区分）
3. 撤销栈深度上限 256 的截断行为
4. 懒加载：GotoLine 未加载行时从 reader 拉取且流位置可恢复

## 未解之谜

- [?] chunk 元数据 16 字节记录的精确字段语义（+0x08 标志与 +0x0c 计数的准确含义）
- [+] 需第二遍：剩余 ~40 个 ≥100B 函数、全部 76 个 <100B 函数；FUN_140673310/140672310 的定位算法（线性 or 二分）
- [?] vtable+0x10 通知的订阅方（推测：文本视图缓存失效）

## 与 SsLineParse 的接口

reader(+0x88) 提供：读行(14051f410)、流位置 Mark/Restore(1405202b0)、检测代码页(140520280)。
行记录结构直接复用 SsLineParse 的 TSsLine（{text; eol:1B}），EOL 枚举同一套（1=CRLF,2=LF,3=CR,4=CRCRLF,5=EOF）。
