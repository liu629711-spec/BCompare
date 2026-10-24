# 17 — M10/M11 注册表比较通道（registry-report）

功能 8（注册表比较）全程。全部结论来自 Oracle 实测
（`product/verify/probes/m101*.py`，共 14 批探针：m101 表面、m101b 模型、
m101c 几何、m101d 细节、m101e 孤儿键、m101f 盒几何（中英孪生）、m101g
逗号续行、m101i 标签、m101j 深层、m101k 几何二、m101m 折叠、m101n 解析；
每批串行、跑前/跑后残留检查 zero；m101f/m101i 各有中英孪生批次，
29+12 格同一 fixture 双语对照）。**所有帧/日期裁决只用整数计数与序数**：
本轮 Produced 日期 od 实测为斜杠形 `2026/10/19`（0x2f），显示层再次改写
成连字符。

产品实现：`product/reg/`（parse/values/collation/engine/report 五模块，
零外部依赖）+ `product/cli` 的 `do_registry_report` 执行器。

## 1. 动词与拒绝面（m101，`runs/m101-regsurface-*`）

| 脚本 | 退出 | 说明 |
|---|---|---|
| `registry-report layout:<l> [options:<o>] [title:<t>] output-to:"%3" "<L>" "<R>"` | **0** | 合法形态；layout 必填 |
| `layout:bogus`（R5）/ 无 layout（R6） | 106 | parse 面 |
| `layout:SUMMARY`（大写，R17） | **0** | 本动词实测大小写不敏感（m83o C4 同族） |
| `layout:side-by-side` / `layout:summary` | 0 | 仅此两个 layout（`Layout::NAMES`） |
| `options:display-all` / `display-matches` / `display-mismatches` / `ignore-unimportant`（R9/N2） | 0 | 四个实测接受；**display 三个对 summary 计数无实测影响**，ignore-unimportant 同样无影响（无"不重要"类别，见 §4） |
| `options:line-numbers`（bogus，N1） | 106 | |
| `output-options:<x>`（R10） | 106 | 同 hex Y10 / picture P7 |
| **零比较文件**（有 layout，R11） | **0** + BOM shell（99B 中文实测，G11） | shell 带 `模式：  全部` 行——**picture 的 shell 没有 Mode 行**，这是两通道 shell 的实测差别 |
| 一个比较文件（R12） | 106 | |
| 三个文件（R13） | 106 | |
| 缺左文件（R14）/ 缺右文件（R15） | **107 / 107** | 两侧都是输入加载类（同 picture，不同于 hex 的缺左 106） |
| 内容不是注册表文件（二进制/坏文本） | **0 + 错误行** | **不是命令失败**：二进制→`文件编码错误 (第 1 行)`，坏文本→`解析错误 (l： c)` 或 `不被支持的类型`（§5） |

`title:"<t>"` 替换帧首行（R16）。

## 2. 帧（m101c G 系列 + m101f 英文孪生）

```
[title | 注册表比较(R) / Registry Compare]
已产生： <斜杠日期> / Produced: <slash date>
<空行>
模式：  全部 / Mode:  All          ← 仅 side-by-side 有（92/92 实测）
左边文件： <L>:\\<basekey> / Left file: <L>:\\<basekey>
右边文件： <R>:\\<basekey> / Right file: <R>:\\<basekey>
[左边错误： … / Left error: …]
[右边错误： … / Right error: …]
[表格：表头 / 规则线 / 行 / 规则线]     ← 仅 side-by-side
[计数行……]                            ← 仅 summary（两 layout 的计数差别见 §4）
```

- **sbs 只到规则线为止，无任何计数行**（G*-sid 全批字节实证）。
- summary 无 Mode 行、无表格，只有帧 + 计数（G*-sum / C*-sum）。
- 文件行的 `:\\<basekey>` 后缀：冒号后是**双反斜杠**（R1 实测），
  `<basekey>` 是两侧公共的键路径前缀（大小写折叠）——一侧没有值键时
  取"列出的键"的公共前缀（G3/C10）；**文件解析出错时后缀仍然保留**
  （G3/C10：只要还有一行键存活）；编码错误的文件无后缀（R19/I7，§5）。
- 错误行在文件行之后、表格/计数之前（I5/I6 实证）。

## 3. 解析器（m101b/m101g/m101n + `parse.rs` 27 测试）

- 头部：`Windows Registry Editor Version 5.00`（`REGEDIT4` 旧头实测亦接受，
  m101b）；无 BOM 且含 NUL 字节→**编码错误**（§5）；无 NUL 的垃圾→
  `不被支持的类型`（N4/N9）。
- **逗号续行永不拼接**（m101g T1 翻案）：`hex:68,65,6c,6c,6f,` + 缩进的
  `  2c,20,…` 保持 5 字节，缩进行是新语句→解析错误 (5:3)。本结论**推翻**
  了早期"续行拼接"假设，archived m101g fixture 字节为证。
- 重复值名→`删除/重复跳过` 行级备注（I6/N8），命令仍 0。
- 键行 `[路径]`、值行 `"name"=type:data`；`@`=默认值名
  （`(默认)`/`(Default)`，S3/J10）。
- 值类型：REG_SZ/REG_EXPAND_SZ/REG_DWORD(0x0000000A (10), J7)/
  REG_BINARY(`hex:` 逐字节 `XX `, S1/F13)/REG_MULTI_SZ(行尾 NUL 只在
  行末剥离, J3)/REG_NONE(空=占位符)/`hex(3)` 等裸十六进制类型码
  （S1 `hex(11)`→类型 `0x11`，N3）。
- 类型名显示：code 4→`REG_DWORD`（N3 h4）。

## 4. 计数（m101b/m101c/m101f，仅 summary）

计数类别按实测序输出：**same → left orphan → right orphan → difference**，
零值类别省略，**没有"不重要"类别**（I1/I2：注册表通道没有重要性概念）。
标签（norm-5 已收录，`verify/harness/normalize.py`）：

| 中文 | 英文 |
|---|---|
| `N 个相同项` | `N same item(s)` |
| `N 个重要的左边独有项` | `N important left orphan item(s)` |
| `N 个重要右边独有项` | `N important right orphan item(s)` |
| `N 个重要的差异项` | `N important difference item(s)` |

repack 的 的 不对称与 text/table 行族同构：左边独有带 的、右边独有不带、
差异项也带（三个都在 m101f 双安装实测）。

## 5. 错误行与编码嗅探（m101-regsurface/m101i I5/I6/I7/m101n）

`parse_reg` 先嗅原始字节：**无 BOM + 含 NUL → `RegError::Encoding{line:1}`**
→ `文件编码错误 (第 1 行)` / `File Encoding Error (Line 1)`（R19/I7，PNG
fixture 字节实证：PNG 含 NUL，ANSI 垃圾不含）。无 NUL 垃圾→头部检查失败
→ `不被支持的类型`（N4/N9）。**错误行不产生计数**（两 layout 都不计）。

其余错误文本（`SideError::text`，EN）：`Parsing Error (l: c)`、
`Deletes/Duplicates Skipped`。中文形态用全角冒号（`解析错误 (3： 38)`，
od 实证 0xff1a）——norm-5 的 `REG_TEXT_ERROR_PATTERNS` 按此匹配。

## 6. 侧边表格几何（m101c/m101d/m101e/m101f/m101g/m101j/m101k/m101m）

**几何是 locale 参数的**，这是本通道与前面所有通道的实测差别：

- 列下界 = **表头标签宽度**：中文 名称/类型/数据 = 2，英文 Name/Type/Data = 4
  （m101f 29 格双语同 fixture 对照实测；产品用 `Locale{ZH,EN}` 两个常量
  参数化，`engine.rs`）。
- 列序：`lt = floor_name + max(名称内容含盒前缀)`；
  `ld = lt + tw + 1`；`mcol = ld + dwL + 1`；`mlen = 0(仅表头)/1('=')/2(任一侧有 <> +- -+)`；
  `rn = mcol + mlen + 1`；`rt = rn + max(名称下界, 内容)`；
  `rd = rt + tw + 1`；规则线 = `rd + dwR`。
- 数据文本：二进制类（`hex:`/`hex(3)`/未知码）按字节渲染 `XX `——
  **每字节带一个尾部空格且计入宽度**（F13 64B→192、T1 5B→15、S1 实证）；
  空二进制/REG_NONE/坏串=占位符 `(零长度二进制值)`/`(zero-length binary value)`
  （I8：无额外空格，宽度=占位符字符数）；字符串按显示字符（NUL 计 1）；
  dword `0x{:08X} ({})`。
- 行组装：绝对列 push，然后 `trim_end_matches([' ', '\u{0}'])`——行尾
  multi_sz 的 NUL **只在行末被剥**（J3/F13/S1：右行丢 `\0`，左行因后有
  填充而保留）。

**盒模型**（m101e/m101f/m101g/m101j，`engine.rs`）：

- level-0 项裸打；level≥1 项打祖先条（level≥1 祖先 '+'→'|'、'\'→' '）+
  自身连接符（非最后合并项 '+'、最后 '\'）+ 名称。
- 孤儿侧在自己的表头行上**什么都不打**；匹配的 '+' 祖先内某侧无内容时打
  续条 '|'（E2：`+Kx              |`、`|\a +- |`）。
- 匹配的值行用同一组连接符；`@`→`(默认)`/`(Default)`。

**排序**（S2/G8/E5/F8/F10/F11）：语言校序（CompareStringW
NORM_IGNORECASE + ASCII 数字串按数值），**先键后值**，每层各自排序。

## 7. display 过滤（m101i I4/I12，`report::filter_rows`）

| options | Mode 行 | sbs 表格 |
|---|---|---|
| display-all（默认） | `模式：  全部` | 全部行 |
| display-mismatches | `模式：  差异` | 丢掉 Same 行，`+-` 孤儿行保留 |
| display-matches | `模式：  相同` | 只留 Same 行，孤儿行与键头丢掉 |

几何在保留行上**重算**（I4 实测规则线 24 vs 未过滤 28）。summary 上三个
display 值对计数无实测差别（I1/I2/I3）。

## 8. 已知差异与残差未知（在案，不硬编码）

| 编号 | 内容 | 状态 |
|---|---|---|
| T6 | 右名称列宽 3 vs 模型 2（单格） | **残差未知 U-reg-1**：未解释，已从语料排除并在测试注释标注 |
| N6 | 归档 fixture 缺陷：引号数据内写了 CRLF 而报告显示 lone-CR 值 | fixture 缺陷，同旧 `\\r\\n` 字面量 bug 家族；已排除 |
| GIF/JPEG | 本通道不涉及（图片通道的事） | 不适用 |
| 双语几何 | 中文安装的 sbs 表格比英文窄（§6） | **设计后果**：金标准用英文安装生成（§9），中文几何由产品语料测试锁定 |

## 9. 验证基线（M111-gate-01）

- **产品**：`reacmp-reg` 27 解析测试 + 103 格归档表格语料
  （85 中文 + 18 英文，`tests/corpus_cases.rs` 字节级）+ 9 帧测试 +
  CLI 集成测试 12 例（拒绝面/帧/错误行/过滤器，`cli/tests/script_exec.rs`）
  → `cargo test` 全绿（CLI 195 + 141 + 118），clippy 零新增告警。
- **Oracle 侧**：`python tools/m111_add_reg_goldens.py` 从**参考（英文）
  安装**串行生成 23 个金标准到 `verify/reg/`（`r-sbs-equal` …
  `r-types-sid`；fixture 逐字节复制，manifest append-only）。
- **重放**：`python -m harness.run_cli --suite reg --candidate reacmp`
  → reg/candidate **23/23**（产品渲染英文帧，与英文金标准逐字节同构）。
- **门禁**：`python -m harness.run_cli --install current --install reference
  --candidate reacmp --run-name M111-gate-01` → **1018/1035**。17 个 fail
  全部是中文安装的 sbs 表格行（§6 的双语几何，**在案差异**，REPORT.md 的
  "Registry suite scope note" 有完整测量轨迹）；summary 6/23 双语折叠一致，
  即 norm-5 的计数/错误行标签对得到双语实证。
- **norm-5**：新增注册表标题、两个 Mode 行、四条错误行模式（解析/重复/
  编码，数据保留）与四个计数标签（§4）。未观测变体（如假设的
  `个重要的右边独有项`）按设计拒绝为 unparseable（test_normalize 实证）。
  旧有通道裁决在 norm-5 下不变（anchor 424 + layout 62 + table 38 +
  hex 26 + pic 72 + labels 31 + folder 2 全绿，与 norm-4 同数）。
