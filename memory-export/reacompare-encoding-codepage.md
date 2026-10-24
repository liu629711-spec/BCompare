---
name: reacompare-encoding-codepage
description: U8 编码/码页里程碑（已完成）——BC 不自动探测 GBK、只认 XML 声明码页、无 BOM UTF-16 NUL 启发式、完整名称表、实现与验收状态
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

2026-10-14 对"编码/代码页（原建议 A：GBK 优先）"做了 **8 轮** Oracle 实测并完成实现。
证据台账：`product/verify/probes/U8-FINDINGS.md`；回归护栏：`product/verify/tools/u8_verify.py`（44/44 + 1 已知差异）。
探针：`u8_codepage_cascade` · `u8b_declaration_and_heuristic` · `u8c_declaration_parser_envelope` ·
`u8d_declaration_name_breadth` · `u8e_last_unknowns` · `u8f_name_fingerprints` · `u8g_fidelity_and_errors` ·
`u8h_alignment_tiebreak`。本地测量：`tools/u8_tables.py` · `u8_ranges.py` · `u8_sizes.py`。

**前提被推翻**：BC **不**自动探测 BOM-less GBK。无声明时按 **UTF-8 lossy** 解码，产品**本来就逐字节一致**
（U8 五个 GBK 用例）。若实现"自动探测"就会引入 BC 没有的行为。首轮 U8 把真一致误报 DIFF 是因为比了
error 元素**原文**（汉化写 `文件编码错误 (第 N 行)`）——比较必须走 normalizer。

**真实缺口只有两个（O 级），均已实现**：
1. **XML 声明码页**：`<?xml ... encoding="NAME"` 在 byte 0 时用该码页解码整个文件。
2. **无 BOM UTF-16 的 NUL 奇偶启发式**：`len>=4` 且偶数（**修订**规格的"len>3"：len=4 实测触发，
   len=2 不触发）；`odd>0.6 && even<0.02`→LE，镜像→BE。

**级联顺序（实测）**：UTF-16LE BOM → UTF-16BE BOM → UTF-8 BOM（**其存在会抑制声明解析**）→
byte 0 处 `<?xml` 声明 → NUL 启发式 → UTF-8 lossy。声明**权威高于内容**（正文是合法 UTF-8 也按声明解）。

**名称表（u8f 指纹法全表，非抽样）三个反直觉事实**：
1. **数字名不解**：`cp936`/`CP936`/`936`/`windows-936`/`ms936`/`x-gbk`/`gbk-2312` 全失败；
   可用的是 `GBK`/`gbk`/`GB2312`/`gb2312`/`GB_2312-80`/`csGB2312`/`csgb2312`/`chinese`（+`GB18030`）。
2. **ASCII 族落到 cp1252**：`US-ASCII`/`ascii`/`ASCII`/`ANSI_X3.4-1968`/`iso-ir-6`/`ISO-8859-1`/
   `ISO8859-1`/`latin1`/`cp1252` 全部 → **1252**（指纹 `€""é\x81\x8d\xa0²` 与 cp1252 逐字节同）。
   `ISO-8859-15` → **28591**（不是 28605）。
3. **Unicode 族被拒**：`utf-16`/`UTF-16`/`utf-16le`/`utf-16be`/`ucs-2`/`UTF-32` → 不采纳。
   另有 932/950/949/1361/1250–1258/874/28592/28595/28597/437/850/866 各页的真实名。
   `utf-8`/`UTF-8`/`utf8`/`CP65001` 解析成功且为**无操作**。

**声明语法**：`encoding` 属性名必须**全小写**；值必须带引号（单双均可）；必须 `?>` 闭合；
`=` 两侧**不得有空格**；名称本身大小写**不**敏感（`GbK` 可）；`version` 可省；后随属性可以。
只在 byte 0 生效。

**解码与上报分离**：BC 用**宽松**转换决定显示（`0xFF`→`U+F8F5`，**非** U+FFFD），
用**严格**校验决定是否报错；行号取**首个**非法行（声明占第 1 行）。二者可同时发生。
**保真度 23/23**：BC 解码与 `MultiByteToWideChar` 逐字节一致，故实现**直接调用同一 OS API**
（比转录 ~140KB 生成表更准；`tools/u8_sizes.py` 测过体积）。

**踩过的坑（都实测）**：
- 探针写死期望值会自造假阴性（u8d/u8e 两次把"落在我没预期的页"误标"未解析"）——必须用**指纹法**。
- BC 让**前导字节吞掉后续换行**（`81 0A`→`?` 且合并下一行），切行必须在**字节层**做。
- 声明为 UTF-8 时**不能**走字节级码页扫描器（会把合法多字节 UTF-8 误报错误；这是实现中实际抓到的 bug）。
- `u8h` 发现 1-vs-2 尾部平局差异，**纯文本无码页下同样复现**（8 形态中 6 一致）→ 属既有对齐平局，
  归入 M2.6（已记入 `07-m2-importance.md`），并非 U8 引入。

**host 依赖（关键）**：本机 **ACP=65001**、OEMCP 也 65001，故 BC 的"ANSI 回退=GetACP()"在本机等于 UTF-8，
**legacy-ANSI 行为在本机不可达**；936 机器上结论可能不同。

**交付**：`product/core/src/codepage.rs`（新模块）+ `lines.rs`（`Encoding::CodePage`、级联扩展）+
`compare.rs::decode_side`。**验收**：core 186 / vfs 35 / dir 133 / cli 410 全绿；
锚点 101/101、layout 31/31、folder 1/1、offline 101/101+101/101+30/31（既有 `mixed-side-by-side`）、
m4_gate 55/57（2 既有已知差异）、pytest 157、u8_verify 44/44+1KD。**无回退**。

相关：[[reacompare-m4-state]] · [[reacompare-a1-harness-state]] · [[reacompare-m2-state]] · [[reacompare-folder-criteria]]
