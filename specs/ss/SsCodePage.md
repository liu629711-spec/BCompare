# SsCodePage.pas 规格（第一遍）

> 逆向来源：Ghidra 反编译 + PE 常量提取 + 持久化工程补拉 10 个未入册助手。
> 原始源码 `C:\BCBuild\BCompare\Source\Ss\SsCodePage.pas`。62 个函数，本遍精读 21 个（含全部编码判定/转换核心）。**14KB 巨型函数 14050fc80 尚未读**，见未解之谜。

## 单元概览

BC 的字符编码基础设施：BOM 检测、启发式编码判定、二进制内容判定、UTF-8/UTF-16 解码与码页表。
SsLineParse 的全部编码决策都委托到本单元。

## 关键常量（全部二进制验证）

| 常量 | 值 | 用途 |
|---|---|---|
| BOM 字节序列 | UTF-16LE `FF FE`；UTF-16BE `FE FF`；UTF-8 `EF BB BF` | FUN_14051b0d0 精确比对 |
| BOM 内部枚举 | -2=LE, -3=BE, -4=UTF-8 | FUN_14051b090 写 / FUN_14051b160 规范化为 1200/1201/65001 |
| **二进制判定阈值** | **0.02**（double） | 非法控制字符占比 > 2% → 二进制文件 |
| 合法控制字符掩码 | 0x24 @ 位9,10,12,13 → **\t \n \f \r** | 二进制判定与 UTF-8 序列扫描共用逻辑 |
| UTF-16 判定阈值 | **0.6 / 0.02**（double×2） | NUL 奇偶位密度 |
| 0xFE/0xFF | UTF-8 回扫硬非法 | DAT_14051c0e8 = 0xC0（位14,15） |
| XML 声明前缀 | `<?xml` | FUN_14051c310 |
| 紧凑存储枚举 | **0=ANSI(GetACP), 1=OEM(GetOEMCP), 0xfde9=65001 UTF-8**；0x4e9f 按 ANSI 处理 | FUN_14051c920 编码 / FUN_14051ca50 解码 |

## 核心函数

### 编码判定级联（SsLineParse.FUN_14051fee0 首块调用的实现层）

1. **BOM 检测** `FUN_14051b0d0(buf,len,cp)`：仅前 2/3 字节精确比对，返回是否有 BOM
2. **UTF-16 NUL 奇偶启发式** `FUN_14051c100(buf,len,out)`（len 为偶数且 >3 才做）：
   统计偶/奇下标 NUL 字节占比 `ratio = count*2/len`；
   - odd > 0.6 且 even < 0.02 → **1200 UTF-16LE**（ASCII 低字节）
   - even > 0.6 且 odd < 0.02 → **1201 UTF-16BE**
   - 其余 → 放弃判定（返回 false）
3. **ASCII → UTF-8** `FUN_14051bc30(buf,len,out)`：全部字节 < 0x80 → 判 **65001 UTF-8**；有高位字节则进入 UTF-8 序列反向校验（0xFE/0xFF 硬非法；每步按 FUN_14051c510 前导长度跳序列）
4. **XML 声明解析** `FUN_14051c310(buf,len,out)`：前缀 `<?xml` → 默认 0xfde9；再扫首个 `>`，在其中找 `encoding="..."`，取引号内名字经 FUN_14051c580 查码页，**拒绝 Unicode 族码页**（FUN_14051c780 = cp∈{1200,1201}）后采纳
5. **二进制内容判定** `FUN_14051bb30(buf,len)`：有 UTF-16 BOM → 非二进制；否则**反向**扫描，字符 < 0x20 且 ∉ {\t\n\f\r}（掩码 0x24，含 NUL 特判与一次性 Ctrl+Z 豁免）计数，`count/len > 0.02` → 二进制

### UTF-8 前导字节长度表 `FUN_14051c510(ch)`

| 首字节范围 | 序列长 |
|---|---|
| 0xC0–0xDF | 2 |
| 0xE0–0xEF | 3 |
| 0xF0–0xF7 | 4 |
| 0xF8–0xFB | 5 |
| 0xFC–0xFD | 6 |
| 其余 | 1 |

**支持到 6 字节序列**（RFC 2279 时代方案，非现代 RFC 3629 的 4 字节上限）——复刻时保持一致。

### 转换

- `FUN_14051b460(buf)`（309B，UTF-8 → UTF-16 解码，SsLineParse 读行路径调用）— 已登记，细节归入后续遍 [?]
- `FUN_14051cfe0(buf,n)`：UTF-16 缓冲区原地逐字字节交换（BE→LE 归一）
- 码页归一：`FUN_14051c920`（真码页 → 紧凑存储枚举）+ `FUN_14051ca50`（反向）；**设置持久化用紧凑枚举**——这是选项文件兼容性的关键事实

## 可测试行为锚点

1. `FF FE` 开头 → UTF-16LE + 跳 2 字节；`FE FF` → BE + 跳 2 字节；`EF BB BF` → UTF-8 + 跳 3 字节
2. 无 BOM 的 ASCII → UTF-8；无 BOM 且 NUL 全在奇下标（>60%）→ UTF-16LE
3. `<?xml` 开头无 encoding → UTF-8；`encoding="windows-1252"` → 1252；`encoding="utf-16"`（Unicode 族）→ 不采纳该声明
4. 含 2.1% NUL 的 ANSI 文本 → 判二进制；含 1.9% → 不判
5. \f（换页符）不算二进制特征
6. 0xFC 前导 → 6 字节序列（超长 UTF-8 兼容）
7. UTF-16BE 文件读入后内部按 LE 处理（字节交换）

## 码页注册表（巨型函数 14050fc80 已定性）

14,446 字节 = **单元初始化**，逐条注册 Windows 码页元数据。注册器 `FUN_14050fae0(ctx, codepage, flag, description, aliases[], aliasCount)`：
- 全局注册数组 `DAT_141fe1ec0`，每项 **40 字节**：`{Int32 aliasCount; Pointer aliasNames[]; Int32 flag; Byte flag2; UnicodeString description}`
- ctx 对象 +0x24c = 已注册条数；断言行 0x13e(318) 容量守卫
- 别名即 IANA/IANA 风格名："US-ASCII"/"ANSI_X3.4-1968"/"iso-ir-6"…（ASCII 一个码页 10 个体名）、"utf8"/"CP65001"、"UTF-32LE"/"UTF-32"
- **0x4e9f(20191) = IANA "US-ASCII (7-bit)"**——上一遍之谜解开，故按 ANSI 族处理
- 覆盖范围：从 37100 系、Mac 系、ISCII 系到 12000/12001(UCS-4)、65000(UTF-7)、65001(UTF-8)、65005/65006(UTF-32) 全量
- flag（byte，1/0）语义 [?]：Unicode 族全 1，Mac 10082=1，台湾系/IA5=0——推测"默认显示在编码选择器"或"BC 内建转换支持"
- 这张表 = BC 编码选择器 UI 的数据源 + `encoding="名字"` 解析的查找表（FUN_14051c580）

## 未解之谜

- [?] flag/flag2 的确切语义（两值分发，待上层 UI 引用回填）
- [?] 140519ff0（1,931B）/ 14051ab10（1,181B）：可能是 MultiByteToWideChar 封装/表驱动转换（待读）
- [?] FUN_14051b460 UTF-8 解码对 malformed 序列的精确处置（替换符？跳过？——读行层已见"遇 LF/CR 截断"）
