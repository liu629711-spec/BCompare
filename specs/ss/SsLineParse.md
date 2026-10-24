# SsLineParse.pas 规格（第一遍）

> 逆向来源：Ghidra 反编译 + 二进制常量提取。BC 原始源码路径 `C:\BCBuild\BCompare\Source\Ss\SsLineParse.pas`。
> 24 个函数全部归类完毕。本单元 = **流式行读取器 + 行分割工具**，是整个文本比较引擎的输入层。

## 单元概览

职责：把任意编码的字节流/字符串切成"行内容 + 行尾类型"，并负责**字符编码自动检测**。
推断类清单：

| 推断原名 | 入口证据 | 职责 |
|---|---|---|
| TSsLineReader | 构造器 14051f290；读循环 14051f410；填充 14051fee0 | 从流读行，编码检测/转换 |
| TSsLine (record) | 14051f090 初始化、14051f250/14051f270 查询 | { Text: string; Eol: TSsLineEnding } |
| 行分割/拼接工具 | 14051f0b0、14051e860、14051efb0、14051ed40 | 字符串 ↔ 行集合 |

## 核心枚举：TSsLineEnding（行尾类型）

存于行记录 `+0x08`（1 字节）。**四值 + 零值在读取器与分割器两条代码路径中交叉验证一致**：

| 值 | 含义 | 备注 |
|---|---|---|
| 0 | 无（空行记录初始态） | IsEmpty 判定：text='' && eol=0（14051f270/14051f210） |
| 1 | CRLF (`\r\n`) | 消费 2 字符 |
| 2 | LF (`\n`) | 消费 1 字符 |
| 3 | CR (`\r`) | 消费 1 字符（经典 Mac） |
| 4 | CRCRLF (`\r\r\n`) | 消费 3 字符——**BC 显式兼容老式 CRCRLF 行尾**（该行为出现在两条独立路径：流式读取器 14051f690 与字符串分割器 14051f0b0） |
| 5 | 无行尾（EOF 截断） | 文件末行无换行符时 |

## TSsLineReader 对象布局（this 偏移 → 字段）

| 偏移 | 类型 | 含义 | 置信度 |
|---|---|---|---|
| +0x00 | VMT | 类指针 | 高 |
| +0x08 | Pointer | 输入字节缓冲区（首次填充时分配 0x10000=64KB） | 高 |
| +0x10 | Int32 | 缓冲区中剩余**元素**数（ANSI=字节，UTF-16=双字节） | 高 |
| +0x14 | Int32 | 单行最大字符数配置（0 = 无限；构造默认 0） | 高 |
| +0x18 | Int32 | 元素宽度：1=ANSI 单字节，2=UTF-16 | 高 |
| +0x1c | Int32 | **检测出的代码页**（-1 = 未定；公开 Getter：-1 时返回 0xfde9） | 高 |
| +0x20 | Byte | Ctrl+Z (0x1A) 视为 EOF 开关 | 高 |
| +0x21 | Byte | 错误标志（行超长 / 解码失败时置 1） | 高 |
| +0x22 | Byte | 单字节编码标志（GetCPInfo.MaxCharSize < 2 时置 1） | 高 |
| +0x23..+0x42 | Byte[32] | **DBCS 前导字节位图**（256 位，由 GetCPInfo.LeadByte 区间填充；扫描时前导字节跳过跟随字节） | 高（填充代码 14051fee0 直接可见） |
| +0x48 | PWideChar | 输出缓冲区（UTF-16，容量 = +0x14 或 0x10000 字符） | 高 |
| +0x50 | Int64 | 累计已读字节总数 | 高 |
| +0x58 | Int32 | 缓冲区内当前读取位置 | 高 |
| +0x60 | Object | 主源流（vtable+0x30 = Read(buffer, 0x10000)；vtable+0x18 = GetSize） | 高 |
| +0x68 | Int64 | 源流大小缓存 | 中 |
| +0x70 | Object | 副流（tee 目标：编码切换重读时回填用；EOF 时主副互换） | 中 |
| +0x78 | UInt32 | 当前生效读取代码页（构造默认 0xfde9） | 高 |
| +0x80/+0x88 | event | OnEncodingChanged（检测前后代码页不等时触发） | 中 |
| +0x90/+0x98 | event | OnEndOfStream（14051f3d0 触发） | 中 |
| +0xa0/+0xa8 | event | OnOverlongLine（读行循环中行超过上限时询问调用方） | 高 |
| +0xb0/+0xb8 | event | **OnBinaryDetected**（FUN_14051bb30 判缓冲为二进制内容时触发——阈值 2% 非法控制字符，见 SsCodePage.md；二遍修正，原误记为 BOM 事件） | 高 |

## 关键算法

### 1. 构造器 (14051f290) `Create(Stream, OwnsStream)`
+0x18 := 1（默认单字节）；+0x1c := -1（待检测）；+0x60 := Stream；+0x68 := Stream.GetSize()；**+0x78 := 0xfde9（先按 UTF-8 尝试）**。

### 2. 编码自动检测级联 (14051fee0, 首次填充时执行)——实现层见 SsCodePage.md
检测顺序（+0x1c = -1 时）：
1. 源流声明为 Unicode 属性（140010d70 接口/属性检查，具体属性 [?]）→ 直接 0xfde9
2. **UTF-8 BOM** (`EF BB BF`, SsCodePage.FUN_14051b0d0) → **65001**（注意：是 BOM 检测，非全文校验——二遍修正）
3. UTF-16LE BOM (`FF FE`) → **1200**；UTF-16BE BOM (`FE FF`) → **1201**
4. UTF-16 NUL 奇偶启发式 FUN_14051c100（阈值 0.6/0.02，见 SsCodePage.md）
5. ASCII→UTF-8 / UTF-8 序列校验 FUN_14051bc30；XML 声明解析 FUN_14051c310（`<?xml` 默认 UTF-8）
- **BOM 处理**：检测到 BOM → 跳过（+0x58 = 1 个 UTF-16 单元；UTF-8 时 = 3 字节）；内部枚举 -2/-3/-4 经 FUN_14051b160 规范化
- **UTF-16BE 特例**：整个缓冲区原地字节交换（FUN_14051cfe0），后续按 LE 处理
- 代码页为 Unicode 族（FUN_14051c780 = cp∈{1200,1201}）→ +0x18 置 2（按 UTF-16 读）
- ANSI + DBCS 代码页 → GetCPInfo 的 LeadByte 区间写入 +0x23 位图
- GetCPInfo 失败 → 回退 GetACP()

### 3. 读行核心 (14051f690) `ReadLineRaw(line, maxCharsLeft)`
按元素宽度三路：
- **UTF-8 路径**（+0x78=0xfde9）：`FUN_14051c510(lead)` = 前导字节序列长度；扫描序列时若遇 **LF/CR**（常量 0x24 掩码，位2=10、位5=13，已从二进制验证）→ 在换行处截断序列（畸形 UTF-8 按行尾切分）；不完整序列存 8 字节待续缓冲（local_38, +0x4c 计数）跨块携带；解码经 SsCodePage.FUN_14051b460，失败置 +0x21
- **ANSI 路径**（+0x18=1）：扫描至 CR/LF/CtrlZ；**DBCS 前导字节连跟随字节一起跳过**（+0x23 位图）；缓冲区尾部截断的前导字节回退并暂存到下次
- **UTF-16 路径**（+0x18=2）：扫描至 `\n`/`\r`/CtrlZ，按双字节搬运
行尾判定（公共尾部）：末字符 10→eolLF；13→再看下一个：10→CRLF、13→再下一个 10→**CRCRLF**（用 MarkPosition/RestorePosition = 1405202b0/1405203b0 回退试探）；缓冲耗尽且读满预算→eolNone(5)。
断言：`SsLineParse.pas` 行 0x30c（=780）"已读字符数 ≤ 预算"。

### 4. 公共读行循环 (14051f410) `ReadLine(out line)`
循环调用 ReadLineRaw 拼接，直到拿到带行尾的行或 EOF；行超长（≥0x7ffffffe）时触发 OnOverlongLine 事件，允许继续；断言行 0x248（=584）。**无限模式按 64KB 分块累进**（0x7fffffff-len 与 0x10000 取小）。

### 5. 字符串 → 行 (14051f0b0) `PopFirstLine(var text): (lineText, eol)`
停止符位图 DAT_14051f1ec = **仅 {LF, CR}**（二进制验证：byte[1]=0x24）；扫描到首个 CR/LF → 前缀为行内容，后缀判定行尾类型（含 CRCRLF 三连判定），从源串头部删除已消费部分。

### 6. 行 → 字符串（拼接方向）
- 14051efb0 `JoinLines(list)`: 行间以分隔符（SsClasses.FUN_140527250）连接，行尾按记录补齐
- 14051ed40 `EnsureEol(line)`: 行尾若非 CR/LF（位图 DAT_14051ef84 = {LF,CR}，二进制验证）则以对象 +0x18 的 EOL 字符补齐（+0x18 为该工具对象配置的默认行尾）；断言行 0x1a2/0x1a3
- 14051e860 `SplitQuotedLine`: 带引号续行意识的分割——+0x18 为引号字符，**成对引号 = 字面引号**（翻倍转义），停止谓词用 SsClasses.FUN_1405279a0；可选按预计算行宽数组（+0x20）切分；断言行 0x15c（=348）。[?] 具体用途（推断：多行字段值的解析）

## TRIVIAL 函数汇总

| 入口 | 语义 |
|---|---|
| 140520280 | GetDetectedCodePage：+0x1c，-1→0xfde9 |
| 14051f090 / 14051f230 | TSsLine.Initialize(text, eol) |
| 14051f250 | 行记录"物理行数"贡献：len + (有内容或有行尾 ? 1 : 0) |
| 14051f270 / 14051f210 | IsEmpty |
| 14051f630 | PeekNextChar（ANSI/UTF16 双宽，缓冲耗尽返回 0） |
| 14051f380 | Destroy（释放双缓冲） |
| 14051f3d0 | EndOfStream 收尾：有副流则主副互换，触发 OnEndOfStream |
| 14051eed0/14051f070/14051ec90/14051fe20 | 外部结构中行记录/字符串字段的 finalize 钩子（偏移 0x50/0x40/0x38/0x30/0x68——提示存在持有行集合的容器类，归属 [?]） |
| 14051f370 | 单元 finalization |

## Oracle 校准（2026-10-13，verify/golden 45 锚点）

- **行尾等价**：CRLF ≡ LF ≡ CR ≡ CRCRLF 全部 same（le-* 四例）；缺尾换行 ≡ 有尾换行。
- **BOM 等价**：UTF-8/UTF-16LE/UTF-16BE BOM 均与无 BOM 等价。
- **Ctrl-Z 默认非 EOF**：`abcdef` vs `abc` = different（+0x20 开关**默认关**；.txt 下 0x1A 是普通字符，报告中输出为 `&#26;`）。
- **无 Latin-1 回退**：`café`（无效 UTF-8）→ `caf�`（U+FFFD），且与 UTF-8 的 `café` 判 different——.txt 路径**不做 ANSI 回退解码**（修正旧"ANSI 回退"理解：回退仅在显式 ANSI 代码页路径）。
- **含 NUL 按文本比较**（enc-nul-binary 正常产出 status）。

## 可测试行为锚点

1. **CRCRLF 兼容**：输入 "a\r\r\nb\r\n" → 行1="a" eol=CRCRLF(4)，行2="b" eol=CRLF
2. **编码检测序**：合法 UTF-8 内容 + 无 BOM → 识别为 65001； UTF-16LE BOM → 1200 并跳过 2 字节；UTF-8 BOM → 跳过 3 字节
3. **UTF-16BE 原地字节交换**后正常读行
4. **畸形 UTF-8 断行**：前导字节后紧跟 \n → 在 \n 处断行而非解码失败
5. **DBCS 前导字节**：Shift-JIS 内容中 0x81-0x9F 前导字节 + 0x5C（反斜杠）不误判为换行/分隔
6. **EOF 无行尾**：末行 eol=5
7. **Ctrl+Z 开关**：+0x20 置位时 0x1A 终止行
8. **成对引号转义**：SplitQuotedLine 中 `""` = 字面 `"`

## 未解之谜

- [?] 140010d70 检查的流属性具体是什么（PTR_14050f580 指向接口表，非字符串）
- [?] FUN_14051f630 的 this 传递路径（Ghidra 参数绑定异常，语义=窥视下一字符已明确）
- [?] 1405203b0 (RestorePosition) 未入函数清单（约 30B），语义由调用点反推，可从持久化 Ghidra 工程按需反编译
- [?] 14051ed40 中 FUN_1404ffc50 五参格式化调用的第 5 参（DAT_14051efa4 指向 0xCC 填充——Ghidra 渲染伪引用，实为寄存器传参）
- [?] OnBomDetected / OnEncodingChanged 事件的消费方（谁挂了这些事件——待上层单元分析时回填）
- [?] SplitQuotedLine 的实际调用场景（多行字符串字段？脚本比较？）

## Rust 实现要点（行为契约）

- `LineEnding { None0, Crlf, Lf, Cr, CrCrlf, Eof }` 与 BC 值序一致
- 编码检测按上述级联顺序实现，BOM 跳过量一致（UTF-8:3 / UTF-16:2）
- DBCS 前导字节位图按 GetCPInfo 语义构建
- 读行以 64KB 块流水推进，支持不完整多字节序列跨块续读
