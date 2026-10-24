# SsXML.pas 规格（第一遍·架构级）

> 逆向来源：语料头部精读 + 字符串索引反查 + PE 常量解析（272 函数；≥250B 的 40 个中已定性 8 个核心，其余登记待二遍）。
> 地址段 1405dexxx–1405edxxx。日期 2026-10-13。
> 单元身份：**BC 自研 XML 引擎**（无 PCRE/无外部 XML 库）——词法表、解析器、写出器、转义、节点树。

## 1. 已定性的核心引擎

### 1.1 XML NameChar 全表判定 — `FUN_1405e2e70(ch: WideChar) → bool`（3423B）
纯区间测试树实现 XML 1.0 Name/NameChar 产生式（实测常量：0x388–0x38A、0x38C、0x38E–0x3A1、0x3A3–0x3CE、0x3D0–0x3D6、0x3DA、0x3DC、0x3E2–0x3F3 = 希腊段等）。**词法层唯一入口**；二遍需导出完整区间表并与 XML 规范对拍。

### 1.2 XML 转义器 — `FUN_1405ea3b0(out, str, quoteChar)`（506B）
`&`→`&amp;`（DAT_1405ea608）、`<`→`&lt;`（DAT_1405ea61c）；quoteChar=0x22 时 `"`→`&quot;`、0x27 时 `'`→`&apos;`（实体名 quot/apos 由 FUN_140014550 装载，结尾包装 DAT_1405ea660）。逐字符原地插入式改写。
- **被 SsPersistent 树序列化器 140684e20 调用**（0x22 引号包属性值）——跨单元链证实。

### 1.3 节点深度相等 — `FUN_1405e4ce0(a, b) → bool`（341B）
协议：vtable+0x40 名（Pos 比对）、+0x58 值、+0x50 子 i、FUN_1405e5c60 节点类型、FUN_1405e5dc0 子数；类型→名→值→子数→逐子递归。
- **被 SsPersistent SameValues 14067eb70 用于区段比较** → 区段类 14067e258 实现同一节点协议（+0x40/+0x50/+0x58/+0x68），**配置树与 XML 树同构**——本单元是 SsPersistent 的语义底座。

### 1.4 XML 解析器 — `FUN_1405e8210`（1701B）
字符串证据：`xml:space`、`preserve`、`default`、`CDATA[`、`OCTYPE`（DOCTYPE）。处理 xml:space 继承、CDATA 段、DOCTYPE。（驱动/入口与 DOM 构建在二遍展开。）

### 1.5 XML 写出器 — `FUN_1405e9140(self, arr, int, bool)`（1766B）
字符串证据：`<![CDATA[`、`xml:space`、`preserve`、`default`。按 xml:space 决定是否 CDATA 包裹。**text-report layout:xml 的输出路径在此**（oracle 对拍的直接对象，二遍优先精读）。
- **已证实消费链（2026-10-13）**：SsPersistent 140685170 写出 `<?xml version="1.0" encoding="UTF-8"?>` + `<!-- Produced by %s from Scooter Software -->` 头部后经 140684e20 序列化配置树——**BC 的配置文件即 XML**；加载侧对应本单元解析器 1405e8210。

### 1.6 转义/字符引用引擎 — `FUN_1405eacf0(self)`（4007B）
高频单字符常量：`'`、`]`、`#`、` +` → CDATA 结束（`]]>`）处理 + `&#...;` 字符引用生成/逆转。全单元最大函数。

### 1.7 变量占位替换 — `FUN_1405ec820`（1698B）
常量 `$`、`#` → $name/#n 形态替换。与 SsPersistent 140680670 的特殊变量解析（"Dummy" 占位）呼应，二遍确认协议。

### 1.8 回调驱动器 — `FUN_140df7b0`（2577B，实为 1405df7b0）
(self, handler{fn,ctx})：拷贝 5-uint 参数块（140001320，含 "string" RTTI 痕迹 = array-of-const）、vtable+0x18 取规模——疑为 SAX 式逐节点分发器 [?]。

## 1.9 Oracle 校准：报告 XML 的确切字节行为（2026-10-13，verify/golden）

- **声明行**：`<?xml version="1.0" encoding="utf-8"?>`（**小写 utf-8**，与配置文件头 `UTF-8` 大小写不同——两处各自的常量）；全文 **CRLF** 行尾；缩进 = 制表符（每层 1 个 	）。
- **控制字符 → 十进制字符引用**：0x01→`&#1;`、0x07→`&#7;`、0x1A→`&#26;`（与 1405eacf0 的 `#` 常量链一致）；**emoji/中文原样 UTF-8 直出**（不转义）。
- **结构**：`<bcreport created>` → `<ltpath/>`/`<rtpath/>` → `<filecomparison created>` → `<filename1>`/`<filename2>` → `<linecomp status>` → `<text ltid rtid>`（same 时 ltid/rtid 同元素；similar/different/orphan 分两元素）。
- **created 时间格式**：`yyyy/mm/dd hh:nn:ss`（SsRegistry 日期引擎的另一消费点，与配置用的 `yyyy-mm-dd hh:nn:ss` 不同格式串）。

## 2. 中层（≥250B，二遍清单）

1405ed5d0(826) 1405e71e0(716) 1405e9e90(639) 1405e6f40(623) 1405e8af0(494) 1405e9c00(476) 1405ea940(450) 1405e6b30(385) 1405eda20(372) 1405ec090(358) 1405e55a0(329) 1405ec320(324) 1405e6830(321) 1405ed0c0(311) 1405e6370(303) 1405ecf50(301) 1405e7810(280) 1405e52c0(275) 1405ed270(269) 1405e6dc0(265) 1405e7600(260) 1405ec490(259) 1405ebce0(256) 1405df640(256) 1405de040(255) 1405ddf40(255) 1405e01d0(254) 1405ec700(253) 1405e4ec0(248) …（全量见 inventory/SsXML.tsv，272 项）

## 3. 可测试锚点（本遍可立）

1. EscapeXML：`&`/`<` 必转；按 quote 参数转 `"` 或 `'`；其余原样。
2. NameChar：XML 1.0 名字字符集（ASCII 段 + 希腊段实测吻合）；非名字字符拒绝。
3. 节点相等：类型/名/值/子数全同才等；子节点递归。
4. 写出器：含 `xml:space="preserve"` 的文本走 CDATA 包裹（`<![CDATA[` 前缀实测存在）。
5. 区段（SsPersistent）与 XML 节点协议同构 → 配置树可按节点协议遍历。

## 4. 未解之谜

1. [?] DOM 节点对象布局与解析器入口（1405e8210 的驱动者；1405df7b0 的 handler 协议）。
2. [?] 1405eacf0 的调用面（属性写出 or 独立工具）。
3. [?] 1405ec820 变量替换的语法（$name/#n 的确切形式）与消费方。
4. [?] text-report layout:xml 输出是否直接由 1405e9140 生成（待 oracle 抓取对照）。
5. [?] 中层 30+ 函数的角色（二遍按 size 降序精读）。
