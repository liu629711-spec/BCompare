# 00 — 当前状态审计（ReaCompare 架构审计）

> 审计日期：2026-10-13
> 审计范围：`D:\Rea` 工作区全部现有资产
> 审计性质：**只读**。未修改 `clone/`、`extracted/`、`verify/`、`ghidra-project/`、任何 `report-*.md`。
> 新增文件：`D:\Rea\product\docs\*`（本文档集）与 `D:\Rea\tools\_audit\*`（审计探针与输出）。
> 所有结论均标注证据来源；凡未实测者标注为「推断」或「未知」。

---

## 1. 一句话结论

工作区里**没有产品代码**。现有资产是三类不同性质的东西：

1. **一份高质量的可执行规格验证器**（`clone/`，Rust，~660 行）——它证明了文本比较的若干行为规格是充分的，但不是产品。
2. **一套已经跑通的 BCompare 黑盒 Oracle 工具链**（`tools/bc-*.py` + `verify/`）——这是本项目最有价值的资产，因为它把"像不像"变成了可度量的事。
3. **大量逆向资料**（`extracted/`、`specs/`、`report-*.md`）——信息量大，但**证据分级混乱**：绝大多数针对的是 5.2.6.32774，不是当前目标 5.2.1.32035。

---

## 2. 当前 BCompare 目标二进制（实测）

命令与输出（本次审计实测）：

```
$ powershell -NoProfile -Command "(Get-Item 'D:\BCompare\BCompare\BCompare.exe').VersionInfo | Format-List FileVersion,ProductVersion,CompanyName"
FileVersion    : 5.2.1.32035
ProductVersion : 5.2
CompanyName    : Scooter Software

File size : 50,680,536 bytes
LastWrite : 2026-03-25 15:26:25
```

SHA-256（分块读取以避开本环境的长十六进制渲染问题，见 §7）：

```
7b6033aa 8b2777f5 d009e4af 5fd2e0ff 4045c20d 7fe646ac 4ceb9acf b35ce762
```

**关键发现：当前安装是中文汉化版（repack），不是官方英文原版。** 证据：

| 证据 | 内容 |
|---|---|
| `BCompare.tr` | 439,296 字节，2026-03-20。官方英文安装**没有**此文件 |
| `423Down.url` | 指向第三方下载站的快捷方式（2018-08-08） |
| `!)添删右键菜单.bat` | 中文文件名的右键菜单安装脚本（2024-07-10） |
| 运行时输出 | 报告标题为「文本比较(T)」「已生成于：」「模式： 全部」而非 `Text Compare` / `Produced:` / `Mode:` |

**影响（重要）**：汉化版会把报告中的**标签文本**翻译成中文。因此：

- 用它做 Oracle 时，**不能直接对拍英文 golden 字节**；
- 但**比较逻辑本身完全一致**（见 §4 实测）。

对照安装（旧，reports 的目标）：

```
D:\bc-official\app\BCompare.exe  5.2.6.32774  50,565,160 bytes
SHA-256: 4e44c526 722d6420 e89b3724 60c519e2 93c41772 3305b83e d0eff853 db16ce5d
```

**BComp.com 在两个安装中逐字节相同**：

```
D:\BCompare\BCompare\BComp.com    125,592 bytes  d8d9d88a…e0359cc9
D:\bc-official\app\BComp.com      125,592 bytes  d8d9d88a…e0359cc9   ← 同一文件
```

这条事实很重要：**控制台 Oracle 引擎两者是同一个二进制**。

### 2.1 Oracle 必须在原安装目录内运行

实测：把 `BCompare.exe` + `BComp.com` 复制到别的目录后运行，触发授权校验失败：

```
Trial mode error — The trial information is missing or corrupt.
Version 5.2.1 (build 32035)          Error = 5
退出码 104
```

在原目录内运行则 `exit=0` 正常出报告。**结论：任何 Oracle 调用都必须使用真实安装路径，禁止复制可执行文件到工作区。**

---

## 3. 现有 clone 原型实测

`D:\Rea\clone`，crate 名 `bcx`，v0.1.0，6 个源文件：

| 文件 | 行数 | 职责 |
|---|---:|---|
| `src/main.rs` | 55 | CLI：`bcx <left> <right> [out.xml] [--opt=…] [--layout=…]` |
| `src/lines.rs` | 48 | 行切分 + 编码（UTF-16 BOM / UTF-8 BOM / UTF-8 lossy） |
| `src/align.rs` | 121 | LCS DP 对齐 + 孤儿块配对 + 三态状态 |
| `src/syntax.rs` | 44 | 极简"是否语法感知"判定 + 注释行判定 |
| `src/report.rs` | 70 | BC 兼容 XML 报告输出 |
| `src/layouts.rs` | 323 | 6 种文本报告布局 |
| **合计** | **661** | |

### 3.1 实测命令结果

```
$ cargo build
    Finished `dev` profile … (3 warnings: unused variable, dead_code)
    → 构建成功

$ cargo test
running 0 tests
test result: ok. 0 passed; 0 failed
    → 0 个测试（tests/ 是空目录）

$ python D:\Rea\tools\bcx-verify.py
45/45 status sequences match BC

$ python D:\Rea\tools\bcx-layout-verify.py
29/30 layouts byte-match BC
```

**必须纠正 README 的一处表述**：`clone/README.md` 写「已实现（45/45 通过）」，容易被读成 cargo 测试。实际上：

- `tests/` 目录**存在但为空**，`cargo test` 跑 **0 个测试**；
- 45/45 来自 `tools/bcx-verify.py`（Python 对拍脚本，比对的是 **status 序列**，不是字节）。

这不是造假——45/45 确实实测通过——但**表述会误导**，后续文档须区分「cargo 测试」与「Oracle 对拍」。

### 3.2 实际实现了什么（核对源码后）

已实现，且经 Oracle 对拍：

- **行切分/编码**：CRLF ≡ LF ≡ CR ≡ CRCRLF；缺尾换行等价；UTF-8/UTF-16LE/BE BOM 等价；无效 UTF-8 → U+FFFD；无 Latin-1 回退。
- **对齐**：LCS DP 最短编辑脚本；孤儿块按 min(a,b) 配对；重复行**前向优先**；**不做移动检测**。
- **重要性（极简版）**：全空白差异 → `similar`；注释行互比 → `similar`；`.txt` 大小写 → `similar`；语法感知文件大小写 → `different`。
- **XML 报告**：头、CRLF、制表符缩进、控制字符十进制字符引用、`ltid`/`rtid`。
- **6 种布局**：side-by-side / interleaved / patch / summary / statistics / over-under。

**未实现**（重要，避免高估）：

- 真正的**语法分词器**（`syntax.rs` 只判断注释行与扩展名，不是 `BcSyntaxElements` 的逐元素重要性）；
- **逐元素重要性规则**（`CaseSig` / `Weights` / 强制重要元素 Directive+Operator）；
- **三方合并**、`media-report`/`file-report`（版本引擎已收口：M112，`version-report` 见 docs/18；二进制/表格/图片/注册表引擎已做：M6/M7/M9/M11）；
- **VFS（FTP/SFTP/WebDAV/压缩包）**、**GUI**、**脚本引擎**、**会话持久化**。

一句话：**clone 覆盖的是「文本比较核心的 ~40%」，且是规格级而非产品级。**

---

## 4. 黄金数据来源：已定案（重要）

### 4.1 问题

`report-*.md` 与 `tools/bc-oracle.py` 都指向 `D:\bc-official\app\BComp.com`，即 **5.2.6.32774**。而项目规定当前目标是 5.2.1.32035。所以必须先回答：**45 个锚点 + 30 个布局的黄金数据，对当前版本是否有效？**

### 4.2 实测方法与结果

写了两个探针（`tools/_audit/probe-anchor-both.py`、`probe-provenance.py`），**让两个安装跑同一批输入**，并保持输入路径与 golden 一致（因为报告头会回显输入路径）：

| 指标 | 当前 5.2.1.32035 | 旧 5.2.6.32774 |
|---|---|---|
| 45 锚点：status 序列 == golden | **45/45** | **45/45** |
| 45 锚点：XML 字节等价（忽略 `created=`） | 41/45 | 45/45 |
| 30 布局：字节等价 | 5/30 | 30/30 |
| 30 布局：**去掉头部后**数据体等价 | **25/30** | 30/30 |

### 4.3 那 4 处 / 5 处差异是什么（逐个核对）

**XML 锚点的 4 处**——全部是**汉化字符串**，非行为差异：

```
enc-latin1              <error1>文件编码错误 (第 1 行)</error1>   vs  <error1>File Encoding Error (Line 1)</error1>
opt-display-context     <mode>差异, 带上下文</mode>              vs  <mode>Differences, With Context</mode>
opt-display-matches     <mode>相同</mode>                        vs  <mode>Same</mode>
opt-display-mismatches  <mode>差异</mode>                        vs  <mode>Differences</mode>
```

**布局的 5 处**——同样是标签，且只出现在 summary 布局：

```
2 个相同行   vs   2 same line(s)
```

### 4.4 结论

> **两个版本的比较引擎在本语料上行为等价。差异 100% 来自汉化。**
> 45 锚点的 status 序列对**当前版本同样成立**；布局数据的**数据体**对当前版本也成立。

**但证据归属必须改写**：现有 `verify/golden/README.md` 说「生成：BCompare 5.2.6」，这是**事实**（就是 5.2.6 生成的），但**未说明它对 5.2.1 的适用性**。审计后应补充这条实测结论（本次已记录于 `02-version-and-evidence.md`，不改动原文件）。

### 4.5 附带发现：报告头会换行，取决于路径长度

追查过程中发现：报告头 `Left file: …  Right file: …` 在路径较长时会**折成两行**。实测与 `COLUMNS` 环境变量无关，与**路径字符串长度**有关。任何对拍工具必须固定输入路径或归一化头部，否则会误判为差异。

---

## 5. 现有逆向资料盘点（含证据分级问题）

### 5.1 `report-*.md`（6 份）

| 文件 | 目标声明 | 证据分级问题 |
|---|---|---|
| `report-algorithm.md` | `bc-official` + 明写 SHA-256 `4e44c526…` | ✅ 标注清晰，但属 **5.2.6** |
| `report-verified.md` | `bc-official` + 明写 SHA-256 `4e44c526…` | ✅ 同上 |
| `report-rules-and-merge.md` | `bc-official` | ⚠️ **未写 SHA-256** |
| `report-clone-roadmap.md` | 明写「Beyond Compare 5.2.6（Pro）」 | ✅ 版本标注清晰 |
| `report-bcompare-summary.md` | 未写版本/路径 | ⚠️ 来源不明 |
| `report-final.md` | 命令行含 `bc-official` | ⚠️ 未写 SHA-256 |

**没有任何报告针对 5.2.1.32035。** 也没有发现任何 5.0 时代证据（`grep "5\.0"` 无命中）——审计前的假设「哪些报告是旧版 5.0」**不成立**：实际是 **5.2.6 vs 5.2.1** 的差异，而非 5.0。

### 5.2 算法结论的可信度分级

`report-algorithm.md` 声称「BC 用 Myers 线性空间算法」。审计认为该结论**证据强度高**，因为它是**结构性**的（V 数组 `2D+1`、对角线步长 2、`delta` 奇偶分支、重叠后二分递归、前后缀裁剪），伪代码已存于 `extracted/pseudocode/`。

但需明确标注：

| 主张 | 分级 | 理由 |
|---|---|---|
| Myers 线性空间 + 前后缀裁剪 + 段合并 | **已观察**（结构证据） | 伪代码特征唯一匹配 |
| 重要性由语法元素索引 6/9（Directive/Operator）强制重要 | **推断** | 依赖「元素索引 → 类型」的映射假设，非直接观测 |
| `CaseSig`/`Weights` 70 字段 schema | **已观察**（字符串/结构） | 但**默认值**由黑盒实测得出（见下） |
| 「空白默认不敏感、大小写默认敏感」 | **已观察**（黑盒实测） | 45 锚点里 `ws-*` / `case-*` 直接验证 |
| 383 条命令、11 种视图、25 套格式 | **已观察**（资源/字符串） | 但**未逐条验证可用性** |

**关键提示**：`report-clone-roadmap.md` 自己记录了一次**自我修正**——「我此前以为 `StrCaseInsig`/`StrWSInsig` 默认都关闭，实测表明空白默认已不敏感、大小写默认敏感」。这说明**逆向推断必须用黑盒对拍复核**，该纪律应延续。

### 5.3 `specs/`（单元规格）

已完成的规格单元：

- `specs/ss/`：14 个 Ss 单元（`SsLineParse`、`SsLineList`、`SsXML`、`SsClasses`、`SsPersistent`、`SsRegistry`…）
- `specs/text/`：10 个 Text 单元（`TextMap`、`TextContent`、`TextREParser`、`TextOutput`…）
- `specs/dir/`：8 个 Dir 单元 + `Op\`（`DirTree`、`ViewDir`、`DirFilters`、`DlgDirReport`、`ViewDirSync`…）
- `specs/ui/`：UI 规格 README（DFM 解码总论）

**资产质量**：`specs/dir/README.md` 的模块边界分析（由断言路径 `C:\BCBuild\BCompare\Source\Dir\...` 反推）质量很高，且**明确标注了每个单元的置信度**（例如 `DlgDirAlignWithItem.pas` 标注「88% 为 edge-nearest，归属可靠性最低」）。这种自我标注应作为后续规范。

### 5.4 `extracted/`（原始证据）

| 资产 | 规模 | 用途 |
|---|---|---|
| `bcfileformats-spec.json` | 19 种文本格式语法规则 | 词法/重要性规则的直接来源 |
| `ui-spec.json` | 表单结构 | GUI 复刻的结构化输入 |
| `ui-event-map.json` | 事件处理器映射 | 命令与函数对接 |
| `source-modules.json` | 271 条源码路径 + 190 模块 | 模块划分（**逆向效率的关键**） |
| `delphi-classes.json` | 5,121 个类 | 类层次线索 |
| `pseudocode/*.c` | 263 个函数伪代码 | 算法细节 |
| `function-attribution.json` | 121,485 函数（28,126 已归属） | 函数定位 |
| `forms/*.dfm` | 212 个 DFM 窗体 | GUI 结构化定义 |

**重大发现（应继续利用）**：BC 的断言宏把**源码路径原样编译进发布版**，因此模块结构（`Source\Bc\`、`Source\Text\`、`Source\Ss\`、`Source\Dir\`、`Source\Vfs\`…）完全暴露。这把「猜函数」变成「按模块查地址」。

### 5.5 `help/`（官方文档，231 个 HTML）

由官方 CHM 解出。**这是唯一"干净的"规格来源**，且本次审计证明了它的实用价值：§6 的文件夹 Oracle 配方就是靠它修好的。

---

## 6. 审计期间发现并修复的一个真实缺陷

**问题**：`verify/dir/` 的文件夹比较 Oracle **完全失败**：

```json
// verify/dir/reports/manifest.json（审计前）
"folder-report": { "exit": 106, "bytes": 0, "seconds": 0.58 },
"xml":           { "exit": 106, "bytes": 0, "seconds": 0.59 }
```

**根因**（查 `help/scripting_reference.html` 的 FOLDER-REPORT 条目）：`folder-report` 报告的是**当前已 load 的基准文件夹**，必须先 `load`；而原脚本用了 `folder-report … "%1" "%2"`（把 `text-report` 的用法套用到 `folder-report`）。

**修复并实测**（`tools/_audit/probe-dir-oracle.py`）：

| 脚本形式 | 退出码 | 字节 |
|---|---|---|
| `load "%1" "%2"` + `folder-report layout:xml output-to:"%3"` | 0 | 1724 |
| 同上 + `expand all` | **0** | **2026** |
| `folder-report … "%1" "%2"`（原脚本） | 106 | 0 |

**顺带实测出文件夹比较的判据模型**（`probe-dir-criteria.py`）。夹具中 `diff.txt` 内容为 `aaaa` vs `bbbb`，但默认报告判为 `same`：

| criteria | `diff.txt` | `samesize.bin` |
|---|---|---|
| 默认（无条件） | **same** | same |
| `criteria size` | same | same |
| `criteria timestamp` | same | same |
| `criteria CRC` | **diff** | diff |
| `criteria binary` | **diff** | diff |
| `criteria rules-based` | **diff** | diff |
| `criteria content` / `binary-content` | exit 106（非法命令） | — |

> **结论：BC 文件夹比较默认是「时间戳 + 大小」，不是内容比较。** 这是产品设计中必须先定的默认语义，且此前工作区**没有记录**。

---

## 7. 环境与工具链

```
rustc / cargo  1.95.0
dotnet         8.0.422
node           v24.15.0
python         3.14.4
cmake          4.4.0
qmake          （未安装）
```

**一个必须记录的环境陷阱**：本环境的工具输出会把**长十六进制串渲染成全零占位**。实测：

```
$ python -c "import hashlib; print(hashlib.sha256(b'abc').hexdigest())"
0000000000000000000000000000000000000000000000000000000000000000   ← 显示被替换
```

而同一条哈希以**分块形式**打印则正常（`ba7816bf 8f01cfea …`，且与已知正确值一致）。审计初期因此一度误判「哈希工具损坏」，实际是显示层问题。

**操作要求**：后续任何证据采集，**不得**直接抄录 `sha256sum` / `Get-FileHash` 的单行输出作为哈希证据，必须用分块或独立工具交叉确认。本文档 §2 的哈希已按此规则处理。

---

## 8. 资产清单总表

| 路径 | 性质 | 状态 | 对本项目的价值 |
|---|---|---|---|
| `clone/`（Rust, 661 行） | 规格验证器 | 45/45 status、29/30 layout 实测通过 | **高**：算法与布局的可执行规格 |
| `tools/bc-*.py` | Oracle 工具链 | 部分可用（`bc-oracle.py` 路径写死为 5.2.6） | **最高**：把"像不像"变可度量 |
| `verify/golden/`（45 锚点） | 黄金数据 | 对当前版本**同样成立**（§4） | **最高** |
| `verify/layouts/`（30 布局） | 黄金数据 | 数据体成立，标签受汉化影响 | **高** |
| `verify/dir/` | 文件夹 Oracle | **审计前失败**，配方已修复 | **高**（修复后） |
| `specs/ss|text|dir|ui/` | 单元规格 | 质量高，含置信度标注 | **高** |
| `extracted/` | 逆向原始证据 | 体量大，未逐条核验 | **中**：需按需取用 |
| `help/`（231 HTML） | 官方文档 | 与版本一致 | **最高**：干净规格 |
| `report-*.md`（6 份） | 二手结论 | **全部指向 5.2.6，且分级混乱** | **中**：结论可用，须核对 |
| `ghidra-project/` | 持久化分析库 | 1.2 GB，秒级查询 | **中高**：按需深挖 |

---

## 9. 结论：本项目实际起点

| 维度 | 真实状态 |
|---|---|
| 产品代码 | **0 行** |
| 可执行规格 | 文本比较核心的 ~40%，经 Oracle 验证 |
| 验证基础设施 | **已建成**（Oracle + 锚点 + 对拍脚本） |
| 证据基础 | 文本比较扎实；文件夹/表格/图片/二进制/合并/VFS/GUI **基本空白** |
| 当前目标版本证据 | **缺失**——所有深度逆向针对 5.2.6，须按 §4 结论重新归属 |
| 最大风险 | 不是算法，而是**范围**：11 种视图、9 个引擎、17 个 VFS 单元、211 个窗体 |

**最重要的正面结论**：本项目**已经解决了最难的一步——可验证性**。有了 Oracle，任何功能都能用「黑盒对拍」定义完成，这让后续工作可以并行派发、客观验收。这比任何单点逆向成果都更有价值。

---

## 10. 本文档的证据可复现性

本文档所有实测结论，可通过以下命令复现（均在 `D:\Rea` 下）：

```bash
# 目标二进制版本与哈希
powershell -NoProfile -Command "(Get-Item 'D:\BCompare\BCompare\BCompare.exe').VersionInfo | Format-List FileVersion"

# clone 构建与对拍
cd clone && cargo build && cd ..
python tools/bcx-verify.py           # → 45/45 status
python tools/bcx-layout-verify.py    # → 29/30 layout

# 版本等价性（本次审计新增）
python tools/_audit/probe-anchor-both.py     # → 两版本 status 均 45/45
python tools/_audit/probe-provenance.py      # → stale 30/30, current 5/30（汉化标签）
python tools/_audit/probe-body-only.py       # → 去头后 25/30

# 文件夹 Oracle 配方（本次审计修复）
python tools/_audit/probe-dir-oracle.py      # → load+expand 形式 exit=0
python tools/_audit/probe-dir-criteria.py    # → 默认 size+timestamp，非内容
```

`tools/_audit/` 为本次审计新增，与既有 `tools/` 脚本**互不干扰**：审计探针只读既有资产，输出仅写入 `tools/_audit/`。
