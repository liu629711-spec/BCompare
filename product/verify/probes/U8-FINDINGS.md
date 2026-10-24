# U8 — 编码/码页探测发现（7 轮，全部为 O 级实测）

> 探测日期：2026-10-14　Oracle：`D:\BCompare\BCompare\BComp.com` 5.0.3.30240（中文汉化安装，就地运行）
> 探针：`probes/u8_codepage_cascade.py`、`u8b_declaration_and_heuristic.py`、`u8c_declaration_parser_envelope.py`、
> `u8d_declaration_name_breadth.py`、`u8e_last_unknowns.py`、`u8f_name_fingerprints.py`、`u8g_fidelity_and_errors.py`
> 测量工具：`tools/u8_tables.py`、`tools/u8_ranges.py`
> 全部串行执行（单实例 + Job Object 进程树），未与 pytest 并行。

---

## 0. 最重要的结论：前提被推翻

**原计划「GBK 优先」是错的。** 动手前假设 BC 会自动探测 GBK —— 实测**不会**。

无 BOM 的 GBK 字节，BC 与产品**行为完全一致**：都按 **UTF-8 有损解码**（`B2 E2 CA D4` → `U+FFFD×4`），
两侧都写 `<error1>`/`<error2>`，判定一致。五个 GBK 用例（`gbk-collapse`、`gbk-same`、`gbk-vs-utf8`、
`gbk-overlap`、`gbk-error-line`）逐码点核对，**产品已经是对的**。

> 附带收益：先前担心的「假 same」风险（两个不同 GBK 串都塌成 4 个 U+FFFD → 误判 same）**不成立**。
> 实测 `B2 E2 CA D4` → `����`、`CA D4 B2 E2` → `�Բ�`（中间两个字节恰好构成合法 UTF-8 序列 `U+0532`），
> BC 判 `different`，产品同判 `different`。
>
> **这一条是"先测后写"的直接收益**：若按原计划实现"GBK 自动探测"，会引入一个 BC 没有的行为，
> 让所有既有 `enc-*` 锚点失去意义。

真正需要实现的是**另外两个机制**，都由实测确认：

| # | 机制 | 产品现状 | 证据 |
|---|---|---|---|
| **A** | `<?xml ... encoding="NAME"?>` 声明码页 | 完全不认（输出 `����` + 误报 `<error1>` + 判 `different`） | u8b/u8c/u8d/u8e/u8f/u8g |
| **B** | 无 BOM UTF-16 的 NUL 奇偶启发式 | 未实现（保留 NUL、切行不同） | u8/u8b |

---

## 1. 码页级联的**实测顺序**

```
1. UTF-16LE BOM (FF FE)          → UTF-16LE，跳 2 字节
2. UTF-16BE BOM (FE FF)          → UTF-16BE，跳 2 字节
3. UTF-8 BOM (EF BB BF)          → UTF-8，跳 3 字节
4. 字节 0 处为 "<?xml"           → 解析声明取码页（见 §3）；解析失败/无声明则落到 6
5. NUL 奇偶启发式（无 BOM 时）    → 判定 UTF-16LE/BE（见 §4）
6. 兜底                          → UTF-8 有损（U+FFFD）
```

**优先级实测**：
- `bom-beats-decl`（UTF-16LE BOM + 内含 GBK 声明）→ UTF-16 胜，声明被忽略（第 1 步先于第 4 步）。
- `decl-after-bom`（UTF-8 BOM + GBK 声明）→ **声明被忽略**，按 UTF-8 处理并报 `<error1>`。
  即 **BOM 存在时不再解析声明**。
- `decl-line2`（声明不在字节 0）→ 不解析，落 UTF-8 有损 + `<error1>`。
- `decl-no-xml`（只有 `encoding="GBK"`，无 `<?xml`）→ 不解析。

**没有 ANSI 回退、没有 GBK 自动探测。** 本机 ACP = **65001**（注册表实测），所以"回退到 ANSI"在本机
就等于"回退到 UTF-8"；本次探测**无法**排除"在 936 主机上存在别的行为"，此点记为待测项（见 §7）。

---

## 2. GBK 无声明时的行为（= 产品现状，已一致）

| 用例 | 左字节 | BC 判定 | 产品判定 |
|---|---|---|---|
| `gbk-collapse` | `B2E2CAD4` vs `CAD4B2E2` | different | different |
| `gbk-same` | `B2E2CAD4` vs 同 | same | same |
| `gbk-vs-utf8` | `B2E2CAD4` vs `E6B58BE8AF95` | different | different |
| `gbk-overlap` | `D6D0` vs `C8CB` | same | same |
| `gbk-error-line` | 第 3 行 `B2E2CAD4` vs `three` | same,same,different | same,same,different |

`gbk-overlap` 值得留意：`D6 D0` 与 `C8 CB` **都是合法 UTF-8**（U+0590 / U+0232），
解码后是两个不同字符，但 BC 把**两侧都**报 `<error1>`+`<error2>` 后判 **`same`**。
产品同样如此 —— **此处 BC 的 `same` 与「乱码相同」无关，只是字节序列解码后恰好相同**。

---

## 3. 声明码页（机制 A）—— 完整实测规则

### 3.1 名称表（u8f 指纹法全表实测）

**这是完整表，不是抽样**：每个候选名跑一次 Oracle，用「每行一个判别字节」的指纹体与
OS（`MultiByteToWideChar`）逐码页比对得出，不依赖任何预期值。

**解析到 cp936（GBK）的名称**：
`GBK`、`gbk`、`GB2312`、`gb2312`、`GB_2312-80`、`csGB2312`、`csgb2312`、`chinese`、`Chinese`

**解析到 cp54936（GB18030）**：`GB18030`、`gb18030`

**其他实测解析成功的页**（名称 → cp）：

| 页 | cp | 接受的名 |
|---|---|---|
| Shift_JIS | 932 | `Shift_JIS`、`shift_jis`、`sjis`、`SJIS`、`cp932`、`x-sjis`、`ms_kanji` |
| Big5 | 950 | `Big5`、`big5`、`big-5`、`cp950`、`cn-big5`、`csbig5` |
| 韩文 | 949 | `cp949`、`ks_c_5601-1987`、`euc-kr`、`EUC-KR`、`ksc5601` |
| Johab | 1361 | `johab` |
| Western | 1252 | `windows-1252`、`cp1252`、`ISO-8859-1`、`ISO8859-1`、`iso-8859-1`、`latin1`、**`US-ASCII`**、**`ascii`**、**`ASCII`**、**`ANSI_X3.4-1968`**、**`iso-ir-6`** |
| 其他 125x | 1250/1251/1253/1254/1255/1256/1257/1258 | `windows-125N` |
| 泰文 | 874 | `windows-874` |
| 拉丁 | 28591 | `L1`、`ISO-8859-15`（注：`ISO-8859-15` 实测落在 28591，**不是** 28605） |
| ISO | 28592/28595/28597 | `ISO-8859-2`、`ISO-8859-5`、`ISO-8859-7` |
| OEM | 437/850/866 | `IBM437`/`cp437`、`IBM850`、`cp866` |

**实测解析失败（落 UTF-8 有损）的名**：
`cp936`、`CP936`、`936`、`windows-936`、`ms936`、`x-gbk`、`gbk-2312`、`GBK-2312`、`gb_2312`、
`gb231280`、`932`、`windows-31j`、`Japanese`、`949`、`950`、`1252`、`latin-1`、`646`、
`utf-16`、`UTF-16`、`utf-16le`、`utf-16be`、`ucs-2`、`UCS-2`、`utf-32`、
`x-nonexistent-page`、空串、空白串。

> **两个反直觉但已实测的事实**（务必不要"想当然"）：
> 1. **数字名不解** —— `936`/`cp936`/`windows-936` 全部失败，**只有 `GBK` 这类字母名可用**。
> 2. **`US-ASCII`/`ascii`/`iso-ir-6` 解析到 cp1252**，不是 7 位 ASCII。实测指纹
>    `€“”é\x81\x8d\xa0²` 与 cp1252 逐字节相同（含 `0x81`/`0x8D` 直通）。
>    这解释了 `SsCodePage.md` 记录的「0x4e9f(20191) 按 ANSI 族处理」——**在本机即 cp1252 行为**。
> 3. **`utf-8`/`UTF-8`/`utf8`/`UTF8`/`CP65001` 解析成功**，且为无操作（就是 UTF-8）。
> 4. **Unicode 族被拒**：`utf-16`/`ucs-2`/`utf-32` 均解析失败 → 落 UTF-8 有损 + `<error1>`。

### 3.2 声明语法（u8c/u8e 实测）

| 形式 | 结果 |
|---|---|
| `<?xml version="1.0" encoding="GBK"?>` | ✅ 接受 |
| `<?xml encoding="GBK"?>`（无 version） | ✅ 接受 |
| `<?xml version="1.0" encoding='GBK'?>`（单引号） | ✅ 接受 |
| `<?xml version="1.0" encoding="GbK"?>`（混合大小写） | ✅ 接受（名称大小写不敏感） |
| `<?xml version="1.0" encoding="GBK" standalone="yes"?>`（后随属性） | ✅ 接受 |
| `<?xml version="1.0" ENCODING="GBK"?>`（属性名大写） | ❌ 拒绝 |
| `<?xml version="1.0"   encoding = "GBK"  ?>`（空格宽松） | ❌ 拒绝 |
| `<?xml version="1.0" encoding=GBK?>`（无引号） | ❌ 拒绝 |
| `<?xml version="1.0" encoding="GBK"`（无 `?>`） | ❌ 拒绝 |
| `<?xml version="1.0"?>`（无 encoding） | ❌ 无声明 → UTF-8 |

**规则归纳**：必须 `<?xml` 起始、属性名 `encoding` **全小写**、值**必须带引号**（单双均可）、
必须存在 `?>` 闭合。名称本身大小写不敏感。

### 3.3 声明优先于内容合法性（u8b 实测）

`decl-gbk-valid-utf8`：声明 `GBK`，但正文字节恰好是**合法 UTF-8**（`E6B58BE8AF95`）。
BC **仍按 GBK 解码**（`E6B5` → U+5A34、`8BE8` → U+5B2D、`AF95` → U+762F），
判 `different`，**不报 `<error1>`**。

→ **声明的权威性高于内容**，不做「先验证 UTF-8 再决定」的回退。产品当前判 `same`（未解码），**这是缺陷**。

### 3.4 声明页下的解码：宽松 + 错误上报（u8g 实测）

关键规则：**BC 用"宽松"模式解码，同时独立上报错误**。两者可同时发生。

| 输入（声明 GBK） | 解码结果 | `<errorN>` |
|---|---|---|
| `B2E2CAD4`（合法） | `测试` | 无 |
| `FF`（非法） | `U+F8F5` | `<error1>` + `<error2>` |
| `81 0A`（前导字节后紧跟换行） | `?` **且换行被吞** | 第 3 行 |
| `81 7F`（前导 + 非法跟随） | `?` | 有 |
| `81` 在 EOF | （该行无内容） | **无** |
| 合法 CJK 文件 | 正确 | **无** |

- `FF` 的宽松产物是 **U+F8F5**（Private Use Area），来自 `MultiByteToWideChar` 宽松模式，
  **不是** U+FFFD。这一点已用 OS API 逐值核对（`tools/u8_tables.py`）。
- 错误行号是**首个含非法序列的行**：`err-line-3`（非法在第 4 行）→ `第 4 行`；
  `err-line-1`（非法在第 2 行）→ `第 2 行`。
- 多个非法行只报**首个**（`err-two-bad`：第 2、4 行均非法 → 报第 2 行）。
- 元素文本为**本地化**形式：`文件编码错误 (第 N 行)`（汉化安装）。
  归一化器已有该标签对（`normalize.py` 第 50-54 行），无需改动。

### 3.5 各页解码保真度（u8g 实测）

**23/23 页与 `MultiByteToWideChar` 逐字节一致**：
cp936、54936、932、950、949、1361、1250–1258、874、28591、28592、28595、28597、437、850、866。

→ **可以放心由 OS 表生成静态表**：BC 用的就是同一张表。
生成器：`tools/u8_tables.py`（几何/分组）、`tools/u8_ranges.py`（范围压缩）。
GB18030 四字节区段已实测有效（`81 30 84 36` → U+00A5），即**需要真 GB18030 表，而非仅 GBK 双字节表**。

---

## 4. 无 BOM UTF-16 的 NUL 奇偶启发式（机制 B）

### 4.1 实测行为

| 用例 | 左字节 | BC 文本 | BC 判定 |
|---|---|---|---|
| `utf16le-nobom` | `61 00 62 00 0A 00` | **`ab`**（单行） | different, **rightorphan** |
| `utf16le-dense` | `61 00 62 00 63 00 0A 00` | **`abc`** | different, rightorphan, rightorphan |
| `utf16be-nobom` | `00 61 00 62 00 0A` | **`ab`** | different, rightorphan |
| `utf16le-short` | `61 00 0A 00`（len 4） | **`a`** → 判 **`same`** | same |
| `utf16le-ascii-mix` | `61 62 00 63 64 00 0A 00` | `ab&#0;cd&#0;`（未触发） | different |
| `utf16le-cjk` | `中文` 的 UTF-16LE（几乎无 NUL） | UTF-8 有损 + `<error1>`（未触发） | — |
| `nul-len2` | `00 61`（len 2） | `&#0;a`（未触发） | same |
| `nul-even-also` | `61 00 00 00 62 00 00 00` | 未触发 | different |

**结论**：
- 启发式**确实实现**了（`61 00 62 00 0A 00` → 解出 `ab`，而非保留 NUL）。
- **len 4 也触发**（`61 00 0A 00` → `a`），说明 `SsCodePage.md` 记的「len 为偶数且 >3」需要修正为
  **`len >= 4` 且偶数**（len=2 不触发）。
- 阈值行为与规格一致：奇位 NUL 占比高 → UTF-16LE；NUL 落在两种奇偶上 → 不触发，保持 UTF-8 有损。
- 判 `rightorphan` 是**因为左文件被解成 1 行、右文件 2 行**，与编码判定本身无关，属预期。

### 4.2 与规格的对照

`specs/ss/SsCodePage.md`：`odd > 0.6 且 even < 0.02 → 1200 (LE)`；`even > 0.6 且 odd < 0.02 → 1201 (BE)`。
本次实测**与该阈值模型一致**（无反例），并补出 `len>=4` 的边界。

---

## 5. 对产品的影响清单

| 项 | 现状 | 应然（实测） | 处理 |
|---|---|---|---|
| 无声明 GBK 字节 | UTF-8 有损 | **同左** | ✅ 已是正确，**不动** |
| `encoding="GBK"` 声明 | 忽略 | 按 cp936 宽松解码 | 🔧 需实现 |
| 声明语法（单引号/无 version/后随属性/大小写） | 忽略 | 接受 | 🔧 需实现 |
| 声明名大小写 | 忽略 | 不敏感 | 🔧 需实现 |
| 数字名（`936`/`cp936`） | — | **拒绝** | 🔧 需实现（且不可"顺手支持"） |
| `US-ASCII` 家族 | — | → **cp1252** | 🔧 需实现 |
| Unicode 族（`utf-16`/`ucs-2`） | — | 拒绝 | 🔧 需实现 |
| 声明优先于内容 | 先验证 UTF-8 → 判 same | **声明权威** | 🔧 需实现（真缺陷） |
| 宽松解码产物 | U+FFFD | 页内宽松值（如 U+F8F5） | 🔧 需实现 |
| 错误上报 | 已在（U7 修复过侧别） | 首行号、宽松与上报共存 | 🔧 调整 |
| NUL 奇偶启发式 | 无 | len>=4 偶数即试 | 🔧 需实现 |
| 码页表 | 无 | 23 页与 OS 逐字节一致 | 🔧 需生成 |

---

## 6. 仍需注意的坑（实测踩到过）

1. **探针的期望值本身就是 bug 源**：u8d/u8e 两次把"解析成功但落在我没预期的页"标成"未解析"。
   凡比对都要**指纹法**（与候选表逐一比对），不要写死期望。
2. **BC 会吞掉前导字节后的换行**（`81 0A` → `?` 且合并到下一行）：切行必须在**字节层**做，
   不能让解码结果里的 `\n` 参与切行 —— 否则行数不同、判定跟着错。
3. **本地化元素文本**：`文件编码错误 (第 N 行)`。比对必须走 normalizer，否则全是假 DIFF。
4. **`ISO-8859-15` 落到 28591**（不是 28605）—— 又一个"想当然会错"的点。
5. **`GBK-2312`/`gbk-2312`/`gb_2312` 全不解**，只有 `GBK`/`gb2312`/`GB_2312-80`/`csGB2312` 可用。

---

## 7. 未解 / 待测项（诚实记录）

1. **936 主机上的行为未测**：本机 ACP=65001，"ANSI 回退"路径无法触发。
   若目标环境 ACP=936，无声明 GBK 文件可能走 ANSI 分支（不在本次结论范围内）。
2. **`flag2` 语义**（`SsCodePage.md` 未解之谜）与本表关系未查。
3. **`ISO-8859-15` → 28591 是否 BC 有意**（还是表里写错）未定；实测就是 28591，按实测实现。
4. **声明长度上限**未测（如 `<?xml` 后超长内容）；实现按"扫描首个 `>`"取，与规格一致。
5. **cp20191（US-ASCII 数字页）**在本机落到 cp1252 行为，与其在 936 主机上的行为关系未测。
