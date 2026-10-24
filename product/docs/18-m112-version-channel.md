# 18 — M112 版本比较通道（version-report）

状态：**通道收口**。动词/拒绝面、帧、PE 版本资源解析器、字段模型、双布局、
侧边表格几何、display 过滤、零文件 shell 全部按双 Oracle 实测落定；
产品侧 `reacmp-ver`（零依赖 hermetic crate）+ CLI 接线 + 25 个英文金标准 +
norm-6 + 语料测试全绿。残差未知 **U-ver-1**（数据字段）、**U-ver-2**（打包
阈值的精确归属）、**U-ver-3**（EN 缺侧值槽 +1）在案。

侦察：`probes/m112_ver_surface_probe.py`（V1–V25，25 格）+
`probes/m112b_ver_fields_probe.py`（W1–W12，16 格，真实 PE 原地补丁版
本块）；几何求解 `probes/_fit/m112_vergeom*.py`；语料生成器
`probes/_fit/m112_gen_corpus.rs.py`；金标准 `tools/m112_add_ver_goldens.py`。

## 1. 动词与拒绝面（m112 V9–V19/V21/V25）

唯一拼写 `version-report`（无别名）。比较文件数：**0 = 退出 0 写 BOM
shell**（V21，含 `模式：` 行——同注册表 R11，异于图片 P8）；**1 = 106**
（V19）；**2 = 正常**；**3+ = 106**（V13b）。缺文件：任一侧 = **107**
（V9/V10）；目录参数 = 107（V25）。layout：缺失 = 106（V12）、非法 =
106（V11）、**大小写折叠**（V13 `layout:SUMMARY` 正常渲染——异于 hex
的 H 系大小写敏感）。options: 词汇 = `display-all` / `display-mismatches`
/ `display-matches` / `ignore-unimportant`（V14–V16 接受；前两者对字节无
效，与图片 O2/O3 同），**词表外 = 106**（V17）。`output-options:` =
106（V18，同 hex Y10 / 图片 P7）。

## 2. 帧（m112 V1–V8/V21/V22 + `verify/ver` 英文金标准）

行序：标题 / `已产生： <slash date>` / 空行 / [`模式：  <mode>` 仅 sbs] /
[独立 `正在忽略不重要` 行 **仅 summary**] / 文件行 / [表格] / [计数行 仅
summary]。要点：

- **ignore-unimportant 双形**：sbs 把它折进 Mode 行
  （`模式：  全部, 正在忽略不重要`，m112b W11）；summary 无 Mode 行，打
  **独立** `正在忽略不重要` 行（`v-opt-ignore-unimp` 金标准 3–4 行）。
  与图片通道（永远独立一行）不同。
- **文件行打包**：左右路径相同时单行 `文件： <path>`（V8）。不同时，
  两行**打包**为一行（`左边文件： <L>␠␠␠␠␠右边文件： <R>`，5 空格
  = `core::stamp::HEADER_GAP`）当合并长度 ≤ **109**；否则分两行。实测：
  打包 83（hex ZH）、87（pic ZH）、98（`v-sbs-equal` EN）、108
  （`v-sbs-plain-both` EN）；分行 178（m112 V1 ZH）、173（reg EN）、
  110（`v-sbs-plain-vs-pe` EN）。**阈值 109 由 108/110 双侧夹出**；
  一般情形是否恰为 109 属 U-ver-2。
- title: 替换第一行（V22）。
- 零文件 shell：BOM + 标题 + Produced + 空行 + `模式：  全部` +
  `基点文件夹： `（79 字节，V21）。

## 3. 解析器（`parse.rs`）

PE 头（COFF+Optional，PE32/PE32+ 双形）→ 节表 → 资源目录（RT_VERSION
= type 16 → name → language → DATA）→ `VS_VERSION_INFO` 解码：

- `CheckSum` 在 Optional 头 **0x40**，PE32/PE32+ 同址（m112b W8 实证：
  PE32 BComp 拷贝 0x0002D28D；此前 0x3c 的猜测读到 0x400）。
- `wValueLength` 计 **UTF-16 码元**，字节数 ×2（m112b W1：
  "Scooter Software" v_len=16 = 16 字符/32 字节）。
- **PE 头与版本资源两级独立**：资源目录不可达（截断文件）时仍返回
  PE 头字段（m112b W8 左侧：只渲染 代码/数据 + PE 头信息 两组，
  固定/翻译/变化 组该侧全空）。`locate_version_resource` 任一步失败即
  降级为 header-only。
- 时间戳：Oracle 宿主本地时区 UTC+8（m112 V1：2026-03-20 18:52:34 UTC
  渲染 `2026/3/21 2:52:34`），分/秒补零、时不补零（`8:06:14`）。
  `LOCAL_ZONE_SECS = 8*3600` 显式传入，crate 保持 hermetic。

## 4. 字段模型（`engine.rs` build_fields）

五组固定序：**代码/数据**（`\数据 <n> 字节`）、**PE 头信息**
（操作系统/处理器/创建日期/标志/链接器版本/图像库/[图像版本 非零才打]/
校验/用户界面/\DLL 旗帜）、**固定**（文件版本/产品版本/操作系统（常量
`Windows NT, Windows 32-bit`）/\文件类型）、**翻译**（\语言）、**变化**
（+语言 + StringFileInfo 键）。

- **标志（COFF characteristics）按机器而非按位渲染端序对**：I386 一律
  打 `小端序`（32位字长 前）+ `大端序`（后），AMD64 一律不打（m112b W8：
  0x818e 两个端序位都没有仍打两者）。位序实测：可执行 → 行号 → 本地
  符号 → [小端序] → 32位字长 → [大端序] → 地址空间>2GB → …。
- **DLL 旗帜**：0x4000 = 控制流防护（不是 0x400——V6 notepad 0xc160
  实证纠错）。
- **变化排序**（m112 V1/V5/W3 双层）：**有本地化标签的键**按英文键字典
  序在前（Comments < CompanyName < FileDescription < … < ProductName），
  其余键在后、彼此字典序（CompileDate < Subversion Revision，虽 "C" < "F"
  会在单层排序时插队）。
- **空值键整行不渲染**：两侧皆空（V1/V5 的 DevBranch）无此行。
- **连接符按侧独立**：每组**该侧最后一个有值的行**打 `\`，其余 `+`
  （m112 V5：右侧行止于 产品版本 → 右列 `\产品版本` 而左列仍是
  `+产品版本`）。为此 `Field` 带 `name`/`rname` 双名字。
- **单侧行的 `|`**：**已知键**在缺侧的名字列打 `|`（m112b W3 右
  Comments 补丁为空 → `|`；m112 V24 DLL 缺 LegalTrademarks 仍 `|`）；
  **未知键**（`其它 (...)`）仅当该侧真有此键才打 `|`，否则整半空
  （m112 V5 CompileDate/Subversion 右半空）。侧整体缺资源（非仅缺键）
  也整半空（W8 左侧）。
- marker：`=` 同、`<>` 异、`+-` 左有右无、`-+` 右有左无。

## 5. 计数（仅 summary；`count()`）

`<n> 个相同项` + `<n> 个重要的差异项`（EN `same item(s)` /
`important difference item(s)`，norm-5 已收录，m112 V2/V4 双语实证）。
diff 计数含全部单侧行。

## 6. 侧边表格几何（m112/m112b + `verify/ver` 金标准；`report::Geometry`）

**全表列位是字符索引**（非显示列）：同一表格所有行在相同字符位对齐。
四段恒等式在每个归档格成立：
`ld = LN+1`；`mcol = ld + LV + (2 或 3)`；`rn = mcol + widest + 1`；
`rd = rn + RN + 1`；`rule = rd + RV`。其中 LV/RN/RV 是**可见**最大值
（含组行），widest ∈ {1,2} 按 `'='`/`'<'>'`。两个 +2/+3 由标记宽决定：
只 `=` 时值+3，有 `<>`/`+-`/`-+` 时值+4。

- **缺侧（any_left = false）例外**：值槽 = dispw(值标签) + (ZH 0 / EN 1)
  ——EN 的 +1 是 **U-ver-3**（V7 ZH 3+2=5 vs V7 EN 5+5+1=11，两个实测点
  无法统一）；rn = mcol + 3。
- **空表（V8）**：`ld = chars(名称)+1`，值槽 = chars(值标签)+2，
  `rn = ld+值槽`，`rd = rn+chars(名称)+1`，`rule = rd + chars(值标签)`
  （ZH 10，EN 22——**非**固定 10）。
- 打包规则、ignore 折叠见 §2。

## 7. display 过滤（V14–V16 / W11）

`display-mismatches` / `display-matches` 过滤行（组行保留），sbs 的
Mode 行换 `模式：  差异` / `模式：  相同`；计数不变。字节级效果仅出现在
有差异的表格上（V2/V4 的 summary 计数不受 display 影响——实测无差）。

## 8. 已知差异与残差未知（在案，不硬编码）

| 残差 | 内容 | 状态 |
|---|---|---|
| **U-ver-1** | `数据/Data` 大小字段的推导：非文件大小；SizeOfImage、节和（raw/virt）、FileAlignment 取整、证书表、调试目录、尾零、首节偏移全部被 41 格否决；delta−blob 残差 504/516/520 无常数 | **开放**。金标准保留 Oracle 数值原文；norm-6 对该行做"仅大小不同"折叠，行名/标记/列位仍须逐字节同 |
| **U-ver-2** | 文件行打包阈值的精确归属：本语料双侧夹出 ≤108 打包 / ≥110 分行（109 为本实现取值）；更一般语料是否仍为 109 | 开放（窄） |
| **U-ver-3** | 缺侧值槽 EN = dispw+1 而 ZH = dispw 的一列不对称 | 开放（窄） |

另有在案差异：**oracle 套件的 19 个 sbs 格**是中文安装对英文金标准的
几何差（§6 的 locale 参数化，docs/17 §6 同形）——REPORT.md 的
"Version suite scope note" 记录，绝不折掉。

## 9. 验证基线（M112）

- **产品侧**：`reacmp-ver` 语料 18/18（归档表格字节级，U-ver-1 行按 §8
  折叠）+ `cli/tests/script_exec.rs` M112 块 12 例（拒绝面/帧/单文件形/
  打包）→ `cargo test` 全绿（CLI 206 + 141 + 118），clippy 零新增。
- **Oracle 侧**：`python tools/m112_add_ver_goldens.py` 从**参考（英文）
  安装**串行生成 25 个金标准到 `verify/ver/`（fixture 逐字节复制，
  manifest append-only，`authored_by` 记录英文依据）。
- **重放**：`python -m harness.run_cli --suite ver --candidate reacmp`
  → 37 非 PASS = **18 个 U-ver-1 大小行 + 19 个 oracle 几何格**（§8）；
  **0 个结构差异**。
- **norm-6**：`版本比较(V)` 标题、ver 表头（`名称/值` → `Name/Value`
  原地替换）、21 条前缀规则（文件行/组行/值行，路径与数值为数据保留）、
  W11 的折叠 Mode 行。未观测变体按设计拒绝为 unparseable。
