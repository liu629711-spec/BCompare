# 11 — M5 收尾清零验收（2026-10-14）

> M5 目标：修完 MVP 内的全部已知差异，让官方门禁归零，并用差分 fuzz 验证
> 修复的推广性。本文档记录实际达成与新增的开放项。

## 1. M5.1 —— `mixed-side-by-side` 与配对模型精化（完成）

官方 harness 唯一红项 `mixed-side-by-side` 的排查把两层规则都推进了一步：

* **side-by-side 槽位字形属块级、只画块首行**：same 块 `=`、纯左孤 `+-`、
  纯右孤 `-+`、含配对行 `<>`（即使首行本身是孤行），后续行一律空白槽位。
  推翻了"左格填满列才空白"的旧拟合猜测（`identical` 行 `y` 反驳）。
  证据：`probes/m51_sbs_marker.py`（`runs/m51-probe-*`，6 形态）。
* **closeness 相似度文本改为大小写敏感**（plain 用原始行，语法格式仍用
  重要文本，`Plan::closeness_text`）：`cs-check` 形态证明全零块必须 zip。
  锚定层保持大小写不敏感（case-swap-align 依赖），两层文本基准分离。
* **平局第三键 = 最小化已配对左行总长度**，等长回退最早：`tie-2v1`
  （`[bbbb,o1] v [X]` 配第二行）、`tie-len-2v1`、`tie-dup`、`tie-3v1` 等形态。
  键只取左侧，因为单调 count-max 匹配的右侧花费恒为前 k 行。
  证据：`probes/m51b_pairing_objective.py`（`runs/m51b-probe-20261014T163003Z`，
  10 形态）与 `runs/m51c-probe-manual`（3 形态）。目标次序仍是
  （相似度和, 配对数）在前（`score-vs-count` 形态）。

验证：探针复跑 16/16 与 BC 全同；`cargo test` 198+5+1 全绿（新增 5 个
M5.1b 回归测试）；`offline_check` 101/101+101/101+**31/31**（布局语料
首次全绿）；`m26_baseline` 133 例 0 分歧；`m26_model_grade` 更新后
226/234（8 处为在案 lab 分词近似，配对零失败）。
**官方 harness `M51-gate-serial-03`：429 = 429 过 + 0 失败 + 0 错误**
（M2 时代的 428+1 已知失败清零；labels 31 项本轮真实跑过）。

## 2. M5.2 —— statistics I/U 列模型（完成）

`probes/m52_statistics_columns.py`（`runs/m52-probe-20261014T165631Z/`，
6 形态含 /iu 变体）实测记账模型并实现：

* `IOriginal`/`UOriginal` 按重要性拆分**左侧行**（注释/空白行计入
  UOriginal，无论是否配成 similar 行；两者之和=左行总数）；
* 单侧不重要行 → `UDeleted`（左）/`UAdded`（右）；`UChanged` = similar；
* `options:ignore-unimportant` **不改变统计** → statistics 从未折叠组渲染
  （`Comparison::render`），`Comparison` 新增 `left_unimportant` 掩码
  （`Plan::unimportant_mask`）；
* plain 的 `// c` 是内容 → `IDeleted`（重要性按语法）。

探针复验 6/6 一致；statistics 五个 golden 不受影响；新增 4 个回归测试
（含 /iu 不变性）。注意：statistics 与 display 过滤的交互仍无观测。

## 3. M5.3 —— 21 个未实现格式（盘点完成，实现未开始）

`extracted/bcfileformats-spec.json` 有 25 个格式的完整元素表
（Keyword/Comment/… 的 Items 列表），产品已实现 4（PlainText/CPP/JS/
Python）。分词器是逐语法手写分支（`scan_line`），每个新格式需独立实现
扫描逻辑（BASH `#`、SQL `--`、VB `'`、HTML `<!-- -->` 等各有注释/字符串
规则）。**25 − 4 − PlainText 覆盖 ≈ 21 个待实现**，属多日工作流，M5 未
动它；这是 M5 之后最大的行为缺口（`.java` 大小写差异报 similar 而
BC 报 different 一类）。

## 4. M5.4 —— 差分 fuzz（完成，发现新分歧族）

`probes/m54_diff_fuzz.py`（种子 20261014，120 例随机小文件，fixtures 与
全部 BC XML 已存档 `runs/m54-fuzz-20261014T170917Z/`）：

* **85/120 配对一致**；35 例分歧连同 fixtures 全部存档。
* **f0083 直接证据**：BC 在 `[文本行, 空行] v [文本行2]` 中配**空行**、
  孤立文本行——尽管文本行与对方共享内部子序列（LCS 2）。即 **BC 的
  closeness 相似度不给内部公共子序列计分**，当前 LCS 度量在此类形态
  系统性偏置。
* 当日试改 common-prefix+suffix 度量：修复 interior-blind 形态（含
  f0083）但在 f0030/f0040/f0041（内部相似度真实起作用）上回退，
  全量 84/120 净负——**已回退到 LCS**（`line_similarity` 文档记录全程）。
* 其余分歧族的形态学指向（待证）：**锚定可能是两层**——先 raw 精确
  （f0019：BC 跳过 ci-equal 邻行去配 raw-equal 行），再 ci 精确
  （case-swap-align 的 similar 行）；以及重复行 run 的锚定选择
  （f0017：BC 锚第一个出现，产品锚了第二个）。
* 上述均已按纪律**记录不隐藏**：`runs/m54-replay-*/still-diverging.txt`
  保存逐例对照。fuzz 是 M5.5 的输入。

## 5. 门禁总表（收尾时点）

| 门禁 | 结果 |
|---|---|
| `cargo test`（core + 集成） | **198 + 5 + 1 全绿** |
| `offline_check.py` | 锚点 101/101 + XML 101/101 + 布局 **31/31** |
| `m26_baseline.py` | **133 例，0 配对分歧，0 状态分歧** |
| `m26_model_grade.py` | 226/234（8 处在案 lab 分词近似，配对零失败） |
| 官方 harness `M51-gate-serial-03` | **429 = 429 过 + 0 失败 + 0 错误** |
| `m52` / `m51` / `m51b` 活探针 | 6/6 + 6/6 + 10/10 与 BC 全同 |
| `m54` fuzz | 85/120（35 例分歧存档，M5.5 输入） |
| `pytest tests`（最终二进制） | **157 全绿** |
| 残留进程检查 | 无 BComp/BCompare 残留 |

## 6. M5.5 第一轮：伪代码挖掘（2026-10-14，进行中）

按 04 的纪律先挖证据再改实现。已解码的 BcAlign 链（`extracted/pseudocode/`）：

* `FUN_140de2f30`（977B）＝closeness 主函数：逐侧走字符——
  `FUN_14052a120`（SsClasses 空白表）字符**跳过**；`FUN_14052a160`
  （字符类别 ∈ {5..9, 13, 16}，经 `FUN_1400366f0` 分类）的连续 run 成
  token，其余字符自成单 token；token 用 **CRC32**（`FUN_1405efd70`：
  `table[(h^b)&0xFF]^(h>>8)`，初值 0xFFFFFFFF、终取反 `~`，逐字符 2 字节
  LE）对**原始字符**哈希（无折叠——2d00 是另一条折叠预处理路径，喂锚定）。
* 匹配器（`FUN_140de3e40`→`3c60`→`3420`，vtable 对象）在 token 序列上跑
  对齐；`FUN_140de3420` 揭示：两侧 token 数组**逐项相等时直取恒等 zip**
  （CompareMem 捷径——解释 al-replace-block），否则按 edit-script 记
  成本（跳过 + 长度，配对在 flag 下**计双倍**）并生成签名串。
* `FUN_140de2930`：以 token 配对为锚，做字符级精化并把结果投影回行。

离线评分（`tools/m55_model_lab.py`，对 290 条录制 + 120 条 fuzz，
`runs/m55-model-lab-*/`）：

| 模型 | recorded | fuzz |
|---|---|---|
| 现役（ci 锚 + LCS closeness） | **244**/290 | 84/120 |
| token-CRC/raw 锚 | 237/290 | 86/120 |
| token-CRC/ci 锚 | 240/290 | **87**/120 |

**无一占优**——缺失的环节是结构性的：BC 的匹配器跑在段级 token 序列上
再投影回行并做字符精化，不是"每对行打分"的逐对模型。f0083（token 序列
零重叠）已能被 token 模型解释，但 recorded 语料的回退说明投影/精化语义
尚未复现。产品二进制未改动（全部为 lab 脚本），门禁保持 M5.4 收尾状态。

## 7. 遗留与排序

1. **M5.5（继续，最高优先）**：解码 `FUN_140de3420` 的 vtable 对象（匹配
   器的 run/成本语义）与 `FUN_140de2930` 的投影规则，把 closeness 改成
   "段级 token 匹配 + 投影"结构；锚定层的 myers 平局拆分（f0017/f0019：
   BC 选后出现的等键匹配）对照 `FUN_140dc5d80` 逐行核对。
2. **M5.3**：21 个格式逐个实现（spec 数据齐备）。
3. 文件夹文本布局字节级（M4 的 2 个 KD）与 `ignore-unimportant` 借用 id
   的文本布局展示（07 遗留 4）。

## 8. M5.5 round-2：匹配器结构完全解码（2026-10-15）

持久化 Ghidra 项目（`tools/ghidra-persistent.py` batch + 新增
`tools/ghidra-scripts/DumpAsm.java` 汇编导出）完成解码。证据：
`extracted/pseudocode/140de{3370,3420,3a30,3b10,3b60,3b80,3ce0,3cf0,3d10,3d30}.c/.asm`
、`140dc6{7e0,820,860,8a0,8e0,920,970,9c0,d40,d50}.c`、`140dc5c60.c`、
`140e69f40.c`、`140525810.c`、`1400368f0.c`，以及 PE 直读（类表/常量）。

**类表**：`PTR_PTR_140de25c8 → 0x140de2690`（旧式 object 方法表，同表还有
三份拷贝：0x140de24b8、0x140e71148〔三种对齐模式类复用！〕、0x14100bbd0；
另有第二类 0x14104c960 含 38e0/3950/3ad0 簇）。槽位：

| slot | 函数 | 语义 |
|---|---|---|
| +0x00 | 140de3b10 | Init：`FUN_140dc5c60(PTR_LAB_140dc56f0,1,0)` 建 diff 状态 → obj+0x10 |
| +0x08 | 140de3b60 | Done：释放状态 |
| +0x10 | 140de3b80 | Align：**`FUN_140dc5d80(state, arr0, arr1, n0, n1)` —— 与行级对齐同一个 Myers 线性空间引擎**（断言 BcAlign.pas 0x1d9/473） |
| +0x18 | 140de3ce0 | 恒返 4：元素 4 字节（恒等捷径 memcmp 的是 4 字节元素数组） |
| +0x20 | 140de38d0 | **no-op（ret）**：3420 算的成本传进来后被丢弃（基类虚方法被覆盖为空） |
| +0x28 | 140de3cf0 | SectionCount → `140dc6d40` = 列表计数 |
| +0x30 | 140de3d10 | GetSection(i) → `140dc6d50`：从 state+0x80 列表拷 16 字节记录 |
| +0x38 | 140de3d30 | **map 写入器**：`assert writeCursor==pair.left`；`map[writeCursor+i] = pair.right>=0 ? pair.right+i : -1`，写 L 条（汇编证实只读 pair/L/游标/数组，第 5 参死参） |

**section 记录**（16B {kind, leftIdx, rightIdx, len}，run-length 合并后的
edit script）：kind-0=INSERT（6920，右独占）、kind-1=DELETE（69c0，左独
占）、kind-2=MATCH（6970，由相邻 delete/insert run 的首元素转化；单元素
DELETE/INSERT 被 match 吸收后直接 free〔68e0/68a0〕不入列表）。列表对左
侧完全铺平 ⇒ **skip-left 发射（token {1,1}，会写配对）实际不可达**。

**发射器** `FUN_140de3370(builder, token2B, count〔死参〕, p4〔死参〕, L, flag6)`：
token 两字节 = {左有效, 右有效}，无效侧记 -1，有效侧记 `cursor[k]` 并
`cursor[k]+=L`，随后一次 map 写入器调用写 L 条。3420 的发射表（汇编钉参）：

| 情形 | token | 效果 |
|---|---|---|
| 两侧皆空 | {0,0} L=0 | 无 |
| 左空 | {0,1} L=右数 | 右游标走完，不写 |
| 右空 | {1,0} L=左数 | 写 -1×L |
| **恒等捷径**（memcmp 相等，与 flag 无关） | {1,1} L=左数 | **map[i]=i 全配对** |
| kind-0 INSERT | {0,1} L=len | 右游标进 |
| kind-1 DELETE | {1,0} L=len | 写 -1×len |
| kind-2 MATCH，flag=0 | {1,1} L=len | **配对** |
| kind-2 MATCH，flag=1 | {1,0}+{0,1} 各 L=len | **拆半，不配对** |

**模式 A/B 的调用点（汇编实锤）**：顶层 `FUN_140de2f30` 传 flag=**1**
（Mode B），间隙细化 `FUN_140de2930` 递归调用传 flag=**0**（Mode A）。
结合"skip-left 不可达"：**顶层 token 阶段的产出只有两种——折叠后 token
序列逐字节相等 ⇒ 恒等全配对；否则 map 全 -1（token 级不产锚点）**。
真正的对齐全部由 2930 完成：无锚时整行成 gap，递归匹配器在**大写折叠字
符码**（fold = `CharUpperW`，1400368f0 实锤）上跑 Mode A Myers，锚点推进
器 `FUN_140de28e0`（map≥0 处跳进，右游标 = map+1）。即：

> **BC closeness = CharUpperW 折叠 → token CRC32 仅作"序列相同"快捷判定
> → 字符级 Myers（含空白字符，map 逐字符）→ 逐字符状态（1=精确等，
> 折叠等且大小写敏感开关开=2，否则=4；未映射按显著性 2/4）→ 压缩成
> {status,text} run（140e69f40，BcSession.pas）。**

`140e69f40` 即行内字符 diff（display 层），参数：p5=会话"全显著"反相、
p6=1、p7=1（该调用点硬编码）、p8=选项透传。`140de2d00` = 折叠预处理
（folded[i]=CharUpperW(ch)，sig[i]=p3?全真:(p4?ws 位图:假)）。

**待办修正**（§7.1 的假设被推翻部分）：产品 closeness 的重写方向不是
"段级 token 匹配 + 投影"，而是"折叠 + 字符级 Myers + 逐字符状态"；
token 化只需保留恒等快捷路径。f0017/f0019 平局拆分对照仍未做。

## 9. M5.5 round-3：行配对相似度分数定位（2026-10-15）

**结论先行**：相似度分数不在 closeness 链（2f30/2930）内，而在三个
"对齐模式"类的 Mode1/Mode3 共享打分函数 `FUN_140e726b0`。调用链：
`140e71a10`（三模式分发）→ Mode1/Mode3 共享初始化 `140e72f50` →
行扫描 `140e738a0` → 遇到不确定区间按候选规模分级降级：精确哈希匹配
> `140e74660`（Needleman-Wunsch DP，逐格调用 `140e726b0` 打分）
> `140e73b40`（窗口近似兜底）。

**三模式分发** `FUN_140e71a10`（428B）：对 `param_1` 对象调用其
vtable[0]，返回值 `'\x01'`→Mode1(`140e718c0`)，`'\x02'`→Mode2
(`140e70f20`)，其他→Mode3(`140e71510`，默认分支)。三个策略类 vtable
核验（`FollowPointers.java`，`extracted/_scratch/mode-vtables.txt`）：
Mode1/Mode3 的 vtable[0] 都是 `140e72f50`（共享初始化，证实"共享方法"
说法），Mode2 的 vtable[0] 直接是 `140e71ea0`。

**Mode2（140e71ea0，721B）不计算相似度分数**：纯行哈希序列匹配——按
比较器 vtable[0x18] 动态探边界，逐行算 32 位哈希（`140e71d00`→
`FUN_1405efdc0(0xffffffff, ptr, len*2)`，CRC 风格），两侧哈希数组交给
`FUN_140de3c60` 做序列匹配，不产生数值打分。

**打分核心 `FUN_140e726b0`**（哈希不同、字符模式下的分支）：

```c
// 伪代码摘录，字符模式分支（param_1+0x58 == 真）：
local_1c = FUN_140e725f0(param_1, line0_trimmed, line1_trimmed); // common
if (*(char*)(param_1+0x58)=='\0') {
    iVar1 = local_1c*3 - len0 - len1;           // raw
    if (iVar1 < 1) {
        local_1c = clamp(iVar1*4 - 1, 下限 -0x28);
    } else {
        local_1c = (iVar1 * 25) / min(len0, len1);
    }
}
```

即：`common = Σ min(freq0[c], freq1[c])`（`FUN_140e725f0`，256 桶字符
频率表求交集，**忽略顺序，不是 LCS**）；`raw = common*3 - len0 - len1`；
`raw<=0` 时惨罚 `clamp(raw*4-1, 下限-40)`，否则归一化放大
`(raw*25)/min(len0,len1)`。哈希相等时走另一分支，只按"去空白后首尾
长度差"打分（`(w0+w1)*2`，长度不同再 -1）；非字符模式下哈希不等直接
给固定惨罚（-0x12 或 -5000）。

**`FUN_140e725f0`**（公共字符数）：

```c
short freq[256] = {0};
for (b in str1) freq[b]++;
count = 0;
for (b in str2) { freq[b]--; if (freq[b] >= 0) count++; }
return count;  // = Σ min(freq1[c], freq2[c])
```

**对先前 lab 结果的解释**：`tools/m55_model_lab.py` 里 token-CRC 与
LCS 变体均未压过 incumbent，现在有了结构性原因——真实度量既不是
token 匹配也不是保序 LCS，是**字符 multiset 交集**（直方图求交），
这是本质不同的相似度量，需要作为新的候选分数族补入 lab。

**本轮两处核验到的非结论**（如实记录，不编造）：
- 记忆草稿中出现的 `0x140e2690`（8 位）是转写时掉了一位 `d`，正确
  地址是 `0x140de25c8`（指针）→`0x140de2690`（vtable，9 位，§8 已有记录），
  **不是**新发现的歧义，是本轮子代理转述时的笔误，已核对澄清。
- `0x14104c960`：当前持久化 Ghidra 项目的函数表里**没有以此为入口的
  函数**，该地址落在一个 9 字节函数 `FUN_14104b9e0` 之后约 0xf80 字节
  的未分析区域。与已知 closeness matcher 类（`0x140de2690`）的关系
  **证据不足，无法判定**，未继续深挖（非本轮核心目标，且地址本身的
  有效性尚未确认）。

**工具链问题记录**（非产品代码，供归档，未修复）：
`tools/ghidra-scripts/BatchDecompile.java` 的 `resolve()` 方法用正则
`.*[g-zG-Z_].*` 判断输入是否为符号名，但字母 `x` 落在 `g-z` 区间内，
导致带 `0x` 前缀的地址批量输入会被误判为符号名查符号表，全部返回
`unresolved`。绕过方法：批量地址列表不写 `0x` 前缀，直接写纯十六进制
数字。单条 `decompile` 命令不受影响（内部直接 `replaceFirst`）。按
"只增不改"未修复脚本本身，仅记录。

**新增证据文件**：`extracted/pseudocode/140e71a10.c`、`140e72f50.c`、
`140e726b0.c`、`140e725f0.c`、`140e71ea0.c`、`140e74660.c`、
`140e74b60.c`、`140e738a0.c`、`140e74100.c` 等约 20 个反编译文件；
`extracted/_scratch/mode-vtables.txt`（三模式 vtable 跟踪）；
`extracted/m55-modeclass-addrs.txt`（地址列表）。

**剩余未知**：f0017/f0019 myers 平局拆分对照仍未做；`140e74b60`/
`140e74100` 的区间冲突消解细节、`140e74a70`/`140e75c50` 的空白行
加分表细节未完全展开（函数级证据已有，业务含义未深挖）。

## 10. M5.5-2c：字符频率交集公式接入离线 lab（2026-10-15）

把 §9 的 `common = Σmin(freq0[c],freq1[c])` / `raw = common*3-len0-len1`
归一化公式实现为 `tools/m55_model_lab.py` 的新变体 `freq/raw`、
`freq/ci`，用标准 Needleman-Wunsch（固定 gap=20，对角代价=该公式）
重接间隙配对，而不是套用其他变体共用的 "(score,count,-leftlen)
monotone-LCS" 框架——两者的"配对 vs 不配对"判定基础不同：monotone-LCS
框架下累加分数非负、配对永不吃亏；而该公式对不相关行给负分，必须用
真正的"对角代价 vs 两次 gap 代价"比较才能复现 BC 的 trade-off，否则
会把本该走 leftsimilar/rightsimilar 的空文本行强行拉去配对（已踩坑：
首次接线直接套用旧框架得 171/290+23/120；用真 N-W 后回升到
227/290+82/120）。

**结果**（290 录制 + 120 fuzz，`runs/m55-model-lab-20261015T014416Z/`）：

| 变体 | recorded | fuzz |
|---|---|---|
| incumbent（ci-anchor + LCS closeness） | 244/290 | 84/120 |
| tok/ci/weighted（token-CRC） | 240/290 | 87/120 |
| **freq/ci（字符频率交集归一化）** | **227/290** | **82/120** |
| freq/raw | 224/290 | 84/120 |

**结论**：字符频率交集公式接线正确后仍未压过 incumbent，两边 recorded
和 fuzz 分数都略低。说明 §9 解码的 `140e726b0` 公式本身**不是**驱动
录制语料/fuzz 分歧的主要变量——它只是 Mode1/Mode3 在候选规模过大时的
*降级*打分（§9 已记录：精确哈希锚定优先，DP 打分是兜底），录制语料和
fuzz 案例多是小文件，真实路径更可能走精确哈希锚定或 Mode2 序列匹配，
而不是触发这条降级 DP。按标准不继续调参凑数——如实记录这是一次有
负面证据价值的阴性结果，不代表公式解码有误，只代表它不是本阶段
离线模型该采用的主算法。离线模型若要进一步逼近 incumbent，下一步
应该是精确哈希锚定层级（`140e738a0`/`140e74b60`）的候选规模判据本身，
而不是继续在打分公式上调参。

产物：`product/verify/tools/m55_model_lab.py`（新增 `freq_score`/
`freq_common`/`freqscore_pair_gap`/`freqscore_rows`，§10 的两个变体）；
`product/verify/runs/m55-model-lab-20261015T014416Z/m55-model-lab.json`。
`cargo test`（`product/core`）复核仍为 198+5+1 全绿，未动产品代码。

## 11. M5.5-3：myers 平局拆分对照 + f0017/f0019 根因收窄（2026-10-15）

**平局操作符逐项核对（`140dc60b0.c` vs `product/core/src/myers.rs`）**：

- 前向：`k==-d || (k<d && Vf[k-1]<Vf[k+1]) → 取 Vf[k+1]`，否则
  `Vf[k-1]+1`（deletion 赢平局）——与 `myers.rs:201-207` 一致。
- 反向：BC 用绝对对角线 k 索引 `Vr[k]`；换算到 `myers.rs` 的反向空间
  `j=delta-k` 后条件逐项相同（`Vr[k-1]<Vr[k+1]` → 取 `Vr[k-1]`，否则
  `Vr[k+1]-1`）——镜像一致。
- 重叠窗口与奇偶分支：奇 delta 前向测 `Vr[k]<=Vf[k]`（窗口
  `delta-d<k<delta+d`），偶 delta 反向测（窗口 `-d<=k<=d`）——一致。
- 前缀/后缀修剪在包装器 `140dc5d80`——一致。0xffffff 对角线上限、
  `(D_max*2+1)*4` 双缓冲分配——一致。

**发现的真实结构差异**：BC 的 middle-snake **没有 1×N 基例**（
`140dc60b0` 直接进 D 循环）；产品 `emit_single_match`
（`myers.rs:510-531`）对单元素矩形取 `position()` 第一个匹配。手推
`[X] vs [u,X,X,v]`：BC 的 snake 在 d=2 命中重叠、回走后配**第二个**
X；产品基例配**第一个** X。这是代码级可证的行为分歧。

**但该分歧不解释 f0017 的 oracle 答案**：f0017 oracle 是左5 配右
**5**（第一个 Alpha，rtid=6 落单）——若 BC 行级走"配后位"的 snake，
答案应是右6。矛盾 ⇒ 结合 §9/§10：**BC 的行级对齐不走 Myers**，而是
`140e738a0` 哈希锚点前向贪心扫描（逐行哈希相等即锚定 ⇒ 重复项自然
配最早者）+ 唯一匹配/NW DP 降级；Myers 引擎（`140dc5d80`/`140dc60b0`）
只服务 closeness/字符层（§8 已证其被 2930/2f30 复用）。产品的
`align_plan` 用 Myers-on-AnchorKey：探针实测
`ia=[0,1,2,3,4] vs ib=[5,6,2,3,4,4,7]`（空行唯一 key 形状）给出
`(4,5)`——配**后**一个 Alpha，与 BC 的 `(4,4)` 相反；裸 id 形状
`[0,0,1,2,3] vs [0,0,1,2,3,3,4]` 给 `(4,4)` 与 BC 一致 ⇒ 分歧由
**空行唯一 key 改变对角线形状**触发，再经 middle-snake 平局方向落点
放大。

**f0019 另案**：oracle 与产品在 "alpha item" 配对上完全一致（左1↔右1、
左6 孤儿）——先前"BC 跳过 ci-equal 邻行配 raw-equal"的记录与本轮
XML 重读不符，实为**空行/注释行锚定分歧**（oracle：右3 `# tmp item
node` rightsimilar、左3/4 配右4/5；产品：左3 配右3 similar、右5
rightsimilar），属锚定层，与平局拆分无关。

**结论与处置**：观测尚不能判定 .txt 行对齐具体走三个 mode 中的哪个
（比较上下文对象的 vtable[0] 返回值语义未解码，是下一步探针目标），
按项目规则**不改 `myers.rs`**、不加个例硬编码。记录：平局操作符已
核实一致；f0017/f0019 根因收窄到**锚定层架构差异**（BC=哈希锚点贪心
扫描 vs 产品=Myers-on-keys），候补修复方向是按 `140e738a0` 重构锚定
层或在其上叠加唯一匹配，待 mode 判定证据后做单变量探针。

探针产物：临时 `examples/f0017_probe.rs` 已删除，`cargo test` 复核
198+5+1 全绿；无 Oracle 进程。

## 12. M5.5-4：mode 判定探针——TBcAlignKind 三模式定名 + Mode2 排除法（2026-10-15）

**枚举定名（RTTI 字符串，实锤）**：`BcAlignLines` 单元含枚举
`TBcAlignKind = (alignNone, alignPatience, alignQuick, alignSmart)`
（字符串于 `0x140e70172`，元素名 `0x140e70190..0x140e701b3`）。分发
`140e71a10` 按 `'\x01'/'\x02'/其他` 三选一，与枚举值 1/2/其余完全对上：

- `'\x01'` → 类表 `140e71988` = **TBcPatienceDiffAlign**（类名串
  `0x140e7199f`，Mode1）
- `'\x02'` → 类表 `140e70fe8` = **TBcQuickAlign**（类名串
  `0x140e71003`，Mode2）
- 其他（含 0 与 3）→ 类表 `140e715d8` = **TBcSmartAlign**（类名串
  `0x140e7128b`，Mode3）

三类的 vtable 槽[0]/[1] 与 §9 记录一致（Mode1/3 共享 `140e72f50` 入口，
Mode2 是独立 `140e71ea0`）。

**模式字节来源（调用链，实锤）**：`140e71a10` 共 6 个直接调用点
（E8 扫描：`14102a5a8/a9ff/b5d2/b87a`、`1417a3912/5350`），分两族：
TextMap 族上下文对象由 `FUN_14102c200(类表 141020fe8,…)` 构造
（vtable[0]=`14102c350`：`kind = *(*( *(ctx+0x10) + 0x60 ) + 0x88 ) + 0x38`；
`141029730`→`*(x+0x60)`，`141037600`→`140ef4fd0`→`*(x+0x88)`），
字段链 = map→session→对齐配置对象，`kind` 在配置对象 +0x38；
另一族 `FUN_1417a5570(类表 14179b398,…)` 构造（vtable[0]=`1417a5690`：
`kind = *( *(ctx+0x10) + 0xf8 )`）。kind 的**设置侧**（会话选项写入
+0x38/+0xf8）未能在本轮静态定位（两处疑似写入簇 `0x140afaca0` 与
`0x1419ede70` 分别为 XAdES CER/BER/PER/XER 与拷贝构造，已排除），
记为残留未知。

**Mode2 = Myers（本轮关键新证据，实锤）**：`TBcQuickAlign`（Mode2）
链 `140e71ea0` → `140de3c60` → `140de3420`（通用 matcher 驱动）→
matcher vtable+0x10 = `140de3b80` → **`FUN_140dc5d80`（Myers 包装器，
BcAlign.pas 断言 0x1d9）**。即 Mode2 就是"行哈希 id 序列上的 Myers"——
与产品的 `align_plan`（Myers-on-AnchorKey）同构。

**Mode2 排除法（f0017 行为证据 + Mode2 结构，推断=高置信）**：
§11 已证 oracle 在 f0017 配**最早**重复 Alpha，而 Myers-on-ids 形状
（产品探针 `[0,1,2,3,4] vs [5,6,2,3,4,4,7]` → `(4,5)` 配后位）给出
**后位**。Mode2 恰是 Myers-on-ids ⇒ 若 .txt 走 Mode2，BC 应给出与产品
一致的"后位"答案——与 oracle 相反 ⇒ **.txt 行对齐不走 Mode2** ⇒ 走
Mode1 或 Mode3，两者**共享同一主层**：`140e738a0` 前向贪心哈希锚点
扫描（重复项自然配最早）+ 唯一匹配 + `140e74660` NW DP（格分
`140e726b0`），仅超大区间兜底不同（Mode1=`140e75a70`，Mode3=
`140e73b40`）。§11 的锚定层假设由此获得证据支持。

**精确到 kind 值的判定（中等置信）**：分发 else 分支覆盖
alignNone(0) 与 alignSmart(3)；正常比较路径由上下文 vtable+0x48 断言
kind≠None（`140e71a10` 内 `BcAlignLines.pas:0xef/0xf0` 断言），故
其余路径 kind=alignSmart ⇒ **.txt 默认走 Mode3 TBcSmartAlign**。
Patience/Smart 之分只影响超大区间兜底，不影响锚点层与 NW DP——对
f0017 类小文件行为无差别。

**结论与下一步**：M5.5-3 悬置的"mode 判定"已闭环：产品锚定层修复
方向确认 = **按 `140e738a0` 重构行锚定（前向贪心哈希锚点 + 唯一匹配
+ NW 降级），Myers 保留给 closeness/字符层**。这是实现级改动，超出
本阶段（不动实现）的边界，留待下一阶段做单变量探针（先 `140e738a0`
候选规模判据 `140e74b60` 的阈值语义，再动产品）。本轮全程未改产品
代码、未跑 Oracle；`myers.rs`/`align.rs` 无改动。

探针产物（本轮 Ghidra 批量反编译，均存于
`D:\Rea\extracted\_scratch\`）：`callers71a10/`、`callsites71a10/`、
`factories/`、`modefns/`、`follow-context-classes.txt`、
`mode-vtables.txt`（前轮）、`kindwriters/`、`m2match/`、
`mode2/`、`mode2b/`。工具链备注：`getFunctionContaining` 接受调用点
地址，绕过 BatchDecompile 的 `0x` 前缀 bug 时可用"传调用点地址"替代
"传纯 hex 函数入口"。

## 13. M5.5-5：`140e74b60` 候选规模判据解码 + 三模式入口架构修正（2026-10-15）

目标：M5.5-4 指定的下一前置——解码 `140e74b60`（3728B，递归唯一锚定
核心）的两道规模门（`0x3e9`/5000）的精确语义。方法：全量 E8-rel32
调用扫描（自写 PE 解析，ImageBase 修正为 PE32+ OptionalHeader+24）
+ 模式对象 vtable 直接转储 + Ghidra 批量反编译（调用点地址技巧）。
全程未动产品代码、未跑 Oracle。

### 13.1 调用图实锤（vtable 转储 + E8 扫描）

- 共享 init `140e72f50` = **模式对象 vtable[0]**（Mode1/Mode3 的
  vtable 表首槽都是它），尾部调 greedyScan `140e738a0`；greedyScan
  尾部 `(**(code **)(*param_1 + 8))(...)` 调**模式对象 vtable[1]**。
- vtable 转储（`140e71988`/`140e70fe8`/`140e715d8`，表后紧跟类名短串
  "BcPatienceDiffAlign"/"TBcQuickAlign" 系）：
  - **Mode1 vtable[1] = `140e75a70`**（PatienceDiff 区间对齐入口）
  - **Mode3 vtable[1] = `140e73b40`**（SmartAlign 区间对齐入口）
- `140e74b60` 的全部 4 个 E8 调用点：2 个是自身递归（`140e755d4`/
  `140e75662`），2 个在 `140e75a70` 内（`140e75ac5`/`140e75c3b`）。
  ⇒ **Mode3（.txt 默认）从不进入 `140e74b60`**。
- **修正 §12**："Mode1=140e75a70、Mode3=140e73b40 为 oversized 兜底"
  的说法不准确——两者是各模式的 vtable[1] 区间对齐入口。方向恰好
  相反：Mode1 核心门失败时把段**委托给 `140e73b40`**（即
  PatienceDiff 的兜底 = SmartAlign 引擎），`140e73b40` 的唯一 E8
  调用点就是 `140e74b60` 内的 `140e75706`。

### 13.2 `140e74b60` 全语义（本任务主体）

递归唯一锚定 divide-and-conquer（入参：job, 左起, 右起, 左止, 右止）：

1. 公共前缀/后缀修剪：`140e72e80(side,idx)` 行哈希等值游走，
   `140e71e30` 发射匹配段；区间交叉则发纯增/删后返回。
2. 左侧建 哈希→行号 字典（`140526440` 系）：哈希已存在 → **毒化为
   -1**（`140528510`）并计数 `local_74 += 1`（即**重复出现次数**：
   Σ(每哈希出现数−1)，`-1` 不可哈希行不计）。右侧遍历取
   **唯一-唯一**配对（右侧重复则从两侧字典撤除并清候选）。
3. 对配对序列做 patience/LIS（严格递增，线性扫尾+插入点，回溯指针
   存 `local_50`）→ 锚点**逆序**递归切分区间（锚间空隙自递归
   `140e74b60`，锚本身逐行发射）。
4. **LIS 为空（零唯一配对）时的三层兜底**——两道门只在此评估：
   - `+0xac == 0`：对角线 1:1 填充 min(左,右)+1 行（仅当
     ctx-vtable+0x20 返回 0），余量发纯增/删。
   - `+0xac != 0`：门 A：`local_74 >= 0x3e9(1001)` → 委托
     `140e73b40`；门 B：**max(左段长, 右段长) > 5000** → 同上
     （注意 261-269 行取的是 max，与对角填充分支取 min 不同）；
     过门 → 在 job+0xa0 分配 (左+2)×(右+2) **方向字节阵**并调
     NW-DP `140e74660`（param_6=0 全回溯）。
5. `+0xac` 来源（`140e72f50` 解码）：`kind≠None` 且 ctx 槽
   +0x48（ctxA 读子对象 +0x40 字节）非 0 且 ctx 槽 +0x20（读
   +0x39 字节）为 0；kind==None 时强制 +0x98=1、+0xac=0。
   ctx 槽 +0x38（读子对象 **+0x3c int**）→ job+0x98 = SmartAlign
   **窗口宽（cache size）**。

### 13.3 SmartAlign 引擎（新解码）：窗口式增量 DP

- `140e73b40`（Mode3 vtable[1]）：死循环；单侧耗尽 → 另一侧按
  **200 行**分块发纯增/删（Mode1 的 `140e75a70` 同路径是 **2000 行**
  分块）；双侧健在 → `140e733b0`。
- `140e733b0`：窗口 = min(剩余, +0x98) 每侧；+0xa0 字节阵作
  **visited 位图**；`140e73040` 自左上逐行扩展 L 形边界：
  对角**等值哈希游程**（`140e72e80` 判等），游程权重
  （`140e74a70` 逐行权重求和）**>4999 → 抛异常**
  （`140052fe0(PTR_PTR_140e70a98,...)`），**>500 → 才记录**为锚点
  候选 {len, weight, left, right} 入 +0x90 列表（容量 0x80 步进）。
- `140e74100`（回溯/发射，1364B）：候选按位置排序（`140e73f30`）、
  **重叠消解**（对角重叠对：截短或置 len=-1 丢弃，`140e74080`），
  逐锚发射；**间隙与尾段用 NW-DP `140e74660` 填充**；外边界尾部
  （param_6=1）允许 partial-traceback——单侧耗尽即停并回写余量
  （`*param_4 -= 未耗尽数`），余量交还外层窗口循环。
- NW-DP `140e74660` 细节定案：滚动分数行 + job+0xa0 方向字节阵
  （1=删/2=增/3=配），**行代价 −0x14(−20)/行**，配对分 =
  `140e726b0`（字符交集相似度，§9 已解码）；回溯按方向段发射。

### 13.4 对产品重构方向的修正

- §12 的"按 `140e738a0` 重构行锚定"仍成立（greedyScan 为两模式
  共享），但**锚后引擎应按 SmartAlign 窗口 DP 建模（.txt 默认
  Mode3），而非 Mode1 的 LIS 核心**。产品 `align_plan`
  （Myers-on-AnchorKey）对应 Mode2，§12 已排除。
- f0017"最早重复配对"与两模式均相容：Mode1 毒化重复行（重复不参与
  锚定，落在 NW 层）；Mode3 从左上角先走到的对角游程即最早配对。
  Mode1/Mode3 行为级判别仍未做，也不阻塞重构（两者共享 greedyScan、
  NW-DP、发射助手，差异集中在锚后引擎与分块粒度）。
- 实现级改动仍超出本阶段边界；单变量探针设计现在有了精确判据：
  门 A=重复出现次数 1001、门 B=max 段长 5000、SmartAlign 游程
  权重 500/4999、窗口宽 = ctx+0x3c（运行时值待定位）。

### 13.5 制品与残留

- 新 scratch（保留）：`D:\Rea\extracted\_scratch\modeentry\`
  （`140e72230/722a0/72330/72e80/72f30/73040/733b0/73740(未解析)/
  738a0/73b40/74100/74b60→pseudocode/75a70/71e30.c` + `_index.tsv`）。
- 未探索：`140e736e8..140e738a0` gap 为 rbp 帧独立函数（2 处
  emitSegment + 2 处 getHashId + 2 处 boundsCheck），唯一调用点
  `0x141b3ac74`→`140e737c1`，Ghidra 未识别其入口。
- 残留未知不变：alignKind 字节的写入侧（§12 已记）；SmartAlign
  窗口宽（ctx+0x3c）的运行时取值与来源。
- 验证：`git -C D:/Rea/product/core status --short` 干净；无
  BComp/BCompare 残留进程。

## 14. M5.5-6：锚定层单变量探针——忠实 NW 平局次序是主导变量（2026-10-15）

目标：§13 指定的锚定层重构前置探针。方法：新离线工具
`product/verify/tools/m55_smartalign_probe.py`（本阶段新建，不动产品
代码、不跑 Oracle），在两轴独立切换锚定层与填充器，逐例对照既有
oracle 语料（290 recorded + 120 fuzz）。

### 14.1 两轴与忠实移植修正

- **锚轴**：`inc` = 现役 myers(ci keys)；`sa*` = §13 解码的
  `140e738a0` 贪心扫描模型（重要行相等即锚；双侧不重要相同时 flush
  pending 区间并锚；单侧不重要只推进该侧并记 pending；失配设
  pending，区间交 vtable[1]）。
- **填充轴**：`*0` = 现役 LCS 三元组；`*N` = 正向坐标 NW 端口；
  `*Nf` = **忠实 `FUN_140e74660` 移植**：DP 在**反向坐标**里填充
  （列 local_4c 取左行 hi−local_4c+1），平局次序 **diag > 跳左 >
  跳右**，再从 (n,m) 角回溯 ⇒ 平局偏好锚在区间**尾部**。这一忠实
  修正由 case-swap-align 判别：BC 配 B/b，正向前端口配 a/A。
- 窗口 DP 对角游程阶段按 §13.3 建模（权重 >500 记锚、≥5000 计数为
  不记录），实测 **1269 个游程 0 个达标** ⇒ 该阶段在本语料规模惰性，
  "saNf ≡ 本规模下的完整 SmartAlign 模型"是实测而非假设。

### 14.2 实测结果（`runs/m55-smartalign-probe-20261015T095342Z`）

| 变体 | recorded | fuzz |
|---|---|---|
| inc（现役） | 244/290 | 84/120 |
| **incNWf** | **245/290** | **91/120** |
| **saNf** | 241/290 | **94/120** |
| sa0 | 229/290 | 87/120 |
| incNW | 227/290 | 82/120 |
| saN | 214/290 | 83/120 |

**结论 1（主导变量）**：`nw_gap_faithful` 的正向/反向坐标差异是单变量
中的最大效应——仅换填充器（inc→incNWf）：recorded +1、fuzz **+7**
（84→91，损失 3 例、增益 10 例）；正向坐标端口（incNW/saN）反而
**劣于现役**（fuzz 82/83）⇒ §9/§10 的"负数结论"部分源于正向端口与
BC 平局语义相反。**此前所有 NW-DP 变体的负结果需按此重读**。

**结论 2（锚轴叠加）**：解码贪心扫描锚 + 忠实 NW（saNf）达
recorded 241/290、fuzz **94/120**（+10 净胜现役）。**动机用例 f0017
在 saNf 下通过**（inc/incNWf 仍失败：inc 配后位 Alpha、incNW 同；
saNf 的贪心扫描配前位）。fuzz 增益分布：plain +7、python +9、cpp +4；
损失 cpp 6 例（comment-* 4 例、f0000 等）。

**结论 3（格式维度未分叉）**：两模型的增益/损失在 plain/python/cpp
三格式上都出现 ⇒ 没有证据支持"不同扩展名走不同 mode"。cpp 损失集中在
注释锚定用例（comment-lead/middle、extra-comment-both、
mixed-comment-and-code），指向**不重要行（注释）在 SmartAlign 里参与
锚定的方式**与现役模型不同——这是下一个待挖点，不是 mode 差异。

### 14.3 对重构处置的修正

§13 的"按 SmartAlign 窗口 DP 建模"方向获得支持，但精确的优先修复
顺序应为：**① 先修填充器平局语义（反向坐标 + diag>left>right，产品
closeness/DP 层如有同构处一并核对）；② 再把行锚定层换成解码的贪心
扫描**。仅 ① 已 fuzz +7 且几乎零损失（recorded +1/−2），风险最低。
窗口 DP 游程阶段无本语料证据，不优先实现（保留判据）。

### 14.4 制品

- 探针：`product/verify/tools/m55_smartalign_probe.py`（新建，含
  六变体 + 忠实 NW 移植 + RUN_STATS 计数）。
- 运行记录：`runs/m55-smartalign-probe-20261015T095342Z/`（含首个
  三变体中间运行记录 `...T094848Z` 已保留）。
- 归因明细：`_scratch/m556/swap-analysis.txt`、`attribution.txt`、
  `format-attribution.txt`、`recorded-flips.txt`。
- 本阶段全程未动产品源码、未跑 Oracle；290+120 例全部为磁盘既有
  oracle 存档的重放。

## 15. M5.5-7：§14 归因更正 + 五点分解定案（2026-10-15，同日晚补记）

**§14 的"忠实 NW 平局次序是主导变量"被本节的轴分解推翻**（§14 结论按"只增不改"保留原文，此处更正）。原因：§14 的 `incNWf` 变体同时改了两件事（评分函数 LCS→freq **且** 产品文本选择→lab 折叠文本），观测到的 +7 被错误归因给几何轴。本节的干净分解（同一发射器、产品忠实文本选择、逐轴切换）给出：

### 15.1 五点分解（290 recorded + 120 fuzz，同一发射器）

| 配置 | 评分 | DP | 评分文本 | recorded | fuzz |
|---|---|---|---|---|---|
| A 基线 | LCS | 现役三元组 | 产品（plain 逐字 / syntax 重要） | 269/290 | 85/120 |
| B | LCS | 解码 NW（反向坐标+平局次序） | 产品 | 269/290 | **85/120（0 差异）** |
| C | 解码 `140e726b0` | 现役三元组 | strip（逐字去首尾空白） | 270/290 | 88/120 |
| D | 解码 | 现役三元组 | 产品 | 268/290 | 82/120 |
| E | 解码 | 解码 NW | 产品 | 269/290 | 95/120 |
| F | 解码 | 解码 NW | strip | **274/290** | **105/120** |

- **B≡A（零差异）**：DP 几何轴在 LCS 评分下完全惰性 ⇒ §14 的"平局次序主导"不成立。（§14 的 `incNWf` 与 `incFAI_L` 之差来自评分函数，不来自几何。）
- **评分函数是主变量之一**：C 单独换评分（+文本）得 recorded +3/−2、fuzz +7/−4。
- **评分文本选择是第二变量**：D（解码评分 + 产品文本）反而劣于 A（fuzz 82）⇒ 产品把 syntax 行换成"重要文本"（去注释）**损害**评分；C/E 的 strip 变体均更好。
- **F 同时超过 A**：recorded **274/290**（+5）、fuzz **105/120**（+20），损失各仅 1 例（f0092）。**这是本项目迄今对 oracle 语料的最佳模型**（历史最好为 inc 269/85 与 §14 的 lab 口径 244/94）。
- 两轴有交互：单独换评分（C/D）增益小，单独换几何（B）零增益，**合起来（F）才释放全部收益**——说明解码评分在现役三元组框架里被其 "count-max + 非负截断" 契约削弱。

### 15.2 `140e726b0` 全分支（本轮补解）

之前 model_lab 的 `freq_score` 只实现第三分支。完整解码（本次重读伪代码 + 网格搜索）：

1. **哈希 id 相等**（`140e72e80` 两侧相等）：取两侧文本，任一为空 → **−10**；否则 `(wL + wR) * 2`（文本长度不等再 −1）。w 为 `140e74a70` 权重（重要文本长度）。
2. 哈希不等且 **`job+0xac == 0`**：`+0x80` 清 → **−18**；置 → **−5000**（硬墙）。
3. 哈希不等、`+0xac != 0`：取文本 `140e723a0`（缓存版 `140e71cd0`→vtable+0x30(…,1)）；任一为空 → `v = −4*(lL+lR) − 1`，`v>−12` 抬到 **−11**，下夹 **−40**；否则 `140e725f0` 交集 `common`，`raw = 3*common − lL − lR`；`raw < 1` → `max(raw*4−1, −40)`；否则 `(raw*25)//min(lL,lR)`。

文本网格（F 几何下）：strip 274/105 > nospace 274/103 ≈ verbatim 272/103 > close 268/94 ⇒ **评分文本 = 逐字去首尾空白**（保留注释与大小写），与产品 `closeness_text` 的"重要文本"约定不同。`job+0x58` 分支（裸 common vs 归一公式）与 `+0x80/+0xac` 的产生条件仍有残量未知，本次未再深挖。

### 15.3 待办与残留

- 产品迁移面（下一单变量）：① `line_similarity` 换 `140e726b0` 全分支评分；② `closeness_text` 的 syntax 分支改为 strip 逐字；③ 若仍不足再考虑把三元组 DP 换成解码 NW（B 显示几何独立零效应，但 F 的合效提示有交互——迁移时须逐轴验证，不得一次全换）。
- f0092 是 F 的唯一损失（recorded+fuzz 同例）：L `['delta','value value alpha','x node beta','beta']` vs R `['DELTA','Node']`，BC 配 (3,2)（"x node beta"↔"Node"），F 配 (4,2)（"beta"↔"Node"）——疑似 `+0x58`/大小写折叠路径，记为已知差异。
- 制品：`_scratch/m556/`（`five-way.txt`、`config_grid.py`、`strip-detail.txt`、`single-var-clean.txt`、`product-faithful-combos.txt`、`loss-inspection.txt`、`nw-diff.txt`）；新 scratch 反编译 `_scratch/scoretext/`（`140e723a0`、`140e71cd0`）。
- 本阶段未动产品源码、未跑 Oracle。

## 16. M5.5-8：产品迁移落地——closeness 层换解码模型（2026-10-15，首例产品改动）

按 §15 的 F 配置把产品 closeness 层一次性换成解码模型（三轴耦合，不能拆——§15 的 A1/A2 已证明文本与几何轴在旧评分下全部惰性，D 配置证明只换评分则回退）。改动全部在 `product/core/src/`，**无个例硬编码、无 Oracle 运行**。

### 16.1 改动面（三处）

1. **`align.rs::pair_similarity`（新）**：`FUN_140e726b0` 全三分支——哈希 key 相等 → `(wL+wR)*2`（文本空 −10、长度不等 −1）；单侧空 → `v=−4*(lL+lR)−1`（>−12 抬到 −11、下夹 −40）；否则字符交集公式 `raw=3*common−lL−lR`（`raw<1` → `max(raw*4−1,−40)`，否则 `(raw*25)//min`）。配套 `char_intersection`（`FUN_140e725f0` 的 256 桶直方图，非 LCS）。
2. **`align.rs::closeness_pairs`（重写）**：三元组 DP（score,count,min-left-len）+ 免费跳过 → 解码的 **Needleman-Wunsch**：反向坐标填充、`GAP_PENALTY=20`/行、平局次序 diag > skip-left > skip-right、从 (m,n) 角回溯（产物已按文档序升序）。`same_key` = 两侧 anchor key 相等且左侧非 `Unimportant`（blank/comment-only 走交集分支而非"同行改写"分支）。
3. **`importance.rs::Plan::score_text`（新）**：评分文本 = 逐字行去首尾空白（保留注释与大小写）。与 `closeness_text` 并存不互换——后者仍服务相似度判定/分类。

### 16.2 实测（改动后，全部离线）

| 指标 | 改动前 | 改动后 |
|---|---|---|
| core 测试 | 198/198 | **198/198** |
| m26_baseline 记录语料（133 例） | 0 mismatch | **0 mismatch** |
| 新增 `tools/m55_fuzz_replay.py`（120 例，产品 vs 存档 oracle XML） | 85/120 | **105/120** |
| `cli/tools/offline_check.py` | 101/101 + 31/31 | **101/101 + 31/31** |

**fuzz 105/120 与 §15 的 F 配置预测值精确一致**（Python 模型 105）⇒ 产品改动语义 = 实验室验证的配置，无实现漂移。记录语料 133 例全绿证明无回归。

### 16.3 迭代中修正的三个实现错误（记录备查）

1. 第一版把负分直接塞进旧三元组 DP：免费跳过使所有负分对不可选，33 例记录语料配对错位——§15 的 D/C 配置早已预警"负分在 count-max 框架里被语义吞噬"。
2. 反向 DP 的坐标：初版用 `ls[n-c]` 直接当 `lkey/lt` 下标（那是**文档行号**，而 `lkey/lt` 按**位置**索引），越界 panic；改用位置 `a=n-c, b=m-r`。
3. 回溯后多加了一次 `.reverse()`：反向填充从 (m,n) 角回溯的产物**本就是升序**，反转后顺序错乱（cs-check 形状暴露）。

### 16.4 残留与下一步

- fuzz 剩余 15 例失败（f0001/f0010/f0014/f0017/f0021/f0022/f0036/f0061/f0073/f0080/f0087/f0092/f0105/f0110/f0115）：f0017 仍配 (5,6) 而非 oracle 的 (5,5)+(orphan)——即重复行锚定差异（§11 的锚定层问题，产品锚定层仍是 myers-on-AnchorKey）；f0092 是本模型已知的路径未解例。**锚定层（§13 的 `140e738a0` 贪心扫描）是下一个迁移面**。
- 探针 `tools/m55_fuzz_replay.py` 为新增离线工具（产品 vs 已存档 oracle XML，不跑 Oracle）。
- 制品：`runs/m26-baseline-20261015T105833Z/`、`runs/m55-fuzz-replay-20261015T105836Z/`（改动前的同批基线 `...T105259Z` / `...T105303Z` 一并保留）；核心改动文件 `product/core/src/align.rs`、`product/core/src/importance.rs`。

### 16.5 官方门禁实测（Oracle 串行，Job Object 包裹）

`python -m harness.run_cli --candidate reacmp --run-name M55-alignment-migration-01`：

```
TOTAL 266  pass=265  fail=0  error=0  missing_output=0  timeout=0  unparseable=0  not_run=1
  anchor/candidate  101/101    anchor/oracle  101/101
  layout/candidate   31/31     layout/oracle   31/31
  folder/oracle       1/1      labels/oracle   0/1 (not_run: reference install unavailable)
```

唯一 not_run 是 `label-pairs-corrob`（需要 reference 安装做跨 locale 标签佐证，本机不可用），与本次改动无关，同 M51 基线状态。**改动前该门禁同样 265 pass；改动后 0 fail、0 error，无回归。** 门禁结束后 `tasklist` 无 BCompare/BComp.com 残留（Job Object 包裹生效）。收敛顺序：Oracle 全结束 → 无 pytest 并行（本次全程未跑 pytest，pytest 另在 core 侧 `cargo test`）。

### 16.6 收尾状态

- 死代码清理：`line_similarity`（被 `pair_similarity` 取代）与 `better_triple`（被 NW 逐格比较取代）删除，构建无新增 warning（`layouts.rs:458` 的 `left_lines` 未用是**改动前既有**）。
- core 测试：`cargo test --release` = 198 passed / 0 failed（另 5 + 1 doctest/integration 通过）。
- 全部四道离线验证 + 官方门禁 = 全绿；fuzz 是本轮唯一提升项（85→105）。

## 17. M5.5-9：锚定层迁移落地——解码贪心扫描替换 myers 锚（2026-10-15，第二例产品改动）

§16.4 指定的下一迁移面。离线选型用新工具 `product/verify/tools/m55_anchor_eval.py`（自包含，不依赖先前探针脚本；含解码扫描 + 区间 handler + NW 填充的干净移植），两模型同发射器对照；

### 17.1 候选模型（解码链）

- **锚层 `FUN_140e738a0` 贪心扫描**（faithful 极性）：
  - 双侧重要且 key 相等 → 无 pending 时立即配对；有 pending 时只延伸区间（不发射）；
  - 双侧重要且不等 → 开/延伸 pending 区间；
  - 单侧重要（另一侧不重要）→ **推进重要侧**并把区间起点钉在该行；
  - 双侧不重要 → 本模型（unimportant 行有 per-side 唯一 id）不等即结束扫描，余段整体成为一个区间。
- **区间处理 `FUN_140e74b60`**：公共 key 前/后缀修剪（直接成锚）→ 唯一-唯一 key 配对（任一侧重复即不锚）→ **patience LIS**（解码的槽覆盖规则：按**左序**迭代、tail 存右索引、回溯沿右索引链，即解码的 `local_50` 数组）→ 锚间空隙递归处理 → 无唯一配对时交 NW 填充。
- 保留 §16 已落地的 NW 填充与 `140e726b0` 评分、`score_text` 选择。

### 17.2 离线对照（`runs/m55-anchor-eval-20261015T113209Z`）

| 模型 | recorded | fuzz |
|---|---|---|
| A 现役（myers 锚 + NW） | 274/290 | 105/120 |
| **C 候选（扫描锚 + handler + NW）** | **279/290** | **115/120** |

翻转明细：记录语料 +6/−1（增益 f0022/f0036/f0061/f0080/f0087/f0110；唯一损失 f0040）；fuzz +11/−1（增益含 f0017 —— §11 的动机用例，损失同为 f0040）。

### 17.3 产品迁移

`align_plan`（`product/core/src/align.rs`）的 myers 锚替换为 `greedy_scan`；`groups_from_pairs` 的块填充路径改由 `interval_pairs`（→`interval_pairs_at`→`unique_key_pairs`/`lis_overwrite_left`/`interval_nw`）承担。取消语义保留：扫描前后与每个区间后检查 `cancel()` 并返回 `DiffError::Cancelled`。`myers.rs` 未改动（closeness/字符层仍用它，`map_ids`+`diff_matches_cancellable` 不再被 align 调用）。

### 17.4 验证（改动后）

| 项 | 结果 |
|---|---|
| core 测试 | **198/198**（含取消传播、文档序覆盖、golden 布局对照） |
| m26_baseline（133 例记录语料） | **0 pairing / 0 status mismatch** |
| fuzz 重放（120 例） | **115/120**（改前 105；与 Python 预测一致） |
| cli offline_check | **101/101 + 31/31** |
| 官方门禁（Oracle 串行） | **265 pass / 0 fail**（`runs/M55-anchor-migration-01`，唯一 not_run 同前） |

### 17.5 残留

- fuzz 剩余 5 例失败（f0021/f0040/f0073/f0092/f0115，见 `runs/m55-fuzz-replay-20261015T113629Z`）；f0040 是本次唯一损失，其 oracle 期望右端两个空行 `rightsimilar` 而模型把它们并入区间（疑似不重要行的区间划分差异）；f0092 为已知的 `+0x58`/大小写路径未解例。
- 制品：`tools/m55_anchor_eval.py`（新）、`runs/m55-anchor-eval-20261015T113209Z/`、`runs/m55-fuzz-replay-20261015T113629Z/`、`runs/M55-anchor-migration-01/`；源改动 `product/core/src/align.rs`。
- 全程未跑 pytest、Oracle 期间无其他使用者、结束后无 BCompare 残留。

## 18. M5.5-10：剩余 5 例收口——扫描旗标极性定案 + 后缀修剪 gate（2026-10-15，第三例产品改动）

§17.5 列的 5 例（f0021/f0040/f0073/f0092/f0115）归因与修复。方法沿用：先用 `_scratch/m556/` 下的可控变体（`residual5.py`、`polarity.py`、`faithful.py`）在 290 recorded + 120 fuzz 上选型，再落地产品。

### 18.1 两条独立根因

1. **后缀修剪歧义**（修好 f0021/f0073/f0115，§17 已诊断）：`140e74b60` 尾部 trim 在 key 于区间内**重复**时不确定——扫描层已用"最早重复优先"，此处却提交给最后一次出现。改为**遇重复 key 停止 trim**，交 NW 处理尾段。
2. **扫描旗标极性**（修好 f0040）：`FUN_140e72f30` 的返回语义此前读作"该行不重要"，实测应为**"该行携带重要内容"**。极性正确后：
   - 单侧重要 → 推进**不重要**侧（只跳过无内容的一侧）；
   - 双侧重要且 id 不等 → **停止扫描**（解码的 `break`），余段整体成区间；
   - 双侧不重要 → 同样停止（unique-id 下等价于解码的"id 不等"分支）。
   反读（TRUE=不重要）在语料上是 279/290 + 115/120，本极性为 **281/290 + 119/120**（判别用例：f0040 的 `['','']` 头段与 `orphan-ws-line` 家族必须同时成立——见 18.3）。

### 18.2 新增对照实验（`faithful.py`，A/B/C/D）

变体轴：外部谓词（ctx vtable+0x28：ctxB 恒 `return 0`，ctxA 为 `140682190`→字节表查询，具体值未定）是否令扫描 `break`；以及"双侧不重要"分支是否按解码设 pending。

| 变体 | recorded | fuzz |
|---|---|---|
| **A 无谓词、无双不重要 pending** | **281/290** | **119/120** |
| B 无谓词、加双不重要 pending | 281/290 | 119/120 |
| C/D 谓词 break | 280/290 | 118/120 |

A 与 B 在语料上等价，C/D 掉 f0040 ⇒ **不加谓词 break**（谓词值未定，不引入无法证实的规则）；A 采纳（无 pending 分支，且顺带修掉一处 flush 越界：pending 单侧为空时 `j-1` 下溢产生伪区间，已加 `l0 < i && r0 < j` 守卫）。

### 18.3 边界判别（两个形状必须同时成立）

```
['   ','int x;'] vs ['int x;']        -> leftsimilar + same      （不配对）
['', 'x']       vs ['yy alpha data alpha','x'] -> different 1:1 + same （配对）
```
两者形状相同、结果相反（`orphan-ws-line` vs `f0015`），A/B/C/D 全变体均通过 ⇒ 该判别的承接者是区间 handler（唯一层/NW），不是扫描谓词。

### 18.4 产品落地与实测

改动均在 `product/core/src/align.rs`：`greedy_scan` 极性反转 + flush 守卫；`interval_pairs_at` 后缀 trim 加重复 key gate。取消语义不变。

| 项 | 改动前（§17） | 改动后 |
|---|---|---|
| core 测试 | 198/198 | **198/198** |
| 记录语料（133） | 0 mismatch | **0 mismatch** |
| fuzz 重放（120） | 115 | **119**（唯一失败 f0092） |
| cli offline_check | 101/101+31/31 | **101/101+31/31** |
| 官方门禁 | 265 pass/0 fail | **265 pass/0 fail**（`runs/M55-residual-fix-01`） |

累计（本章程起点 → 现在）：fuzz **85/120 → 119/120**；记录语料始终 0 mismatch。

### 18.5 残留

- **f0092（唯一剩余 fuzz 失败）**：区间 `L['value value alpha','x node beta','beta'] × R['Node']`，BC 配 `L2 'x node beta'`（重要文本 `xnodebeta` 与 `Node` 的字符交集 common=3），产品/模型配 `L3 'beta'`（common=1）。判别点在**配对评分函数对"长度惩罚"的处理**：BC 选择 common 更高但更长的行，说明该分支的 `raw`/归一化公式在此未按当前实现生效。精确机制未定（涉及 `job+0x58`/`+0x80`/`+0xac` 三旗标的运行时取值），**保留为已知差异，不做个例硬编码**。
- 未探索项不变：alignKind 写入侧、SmartAlign 窗口宽运行时值、`140e736e8..140e738a0` gap 函数；本轮新增未定项：ctxA 谓词 `140682190` 的字节表语义（不影响已采纳的最优配置）。
- 制品：`_scratch/m556/{residual5.py, polarity.py, faithful.py}`、`runs/M55-residual-fix-01/`、`runs/m55-fuzz-replay-20261015T120820Z/`（119/120）。
- 全程未跑 pytest、Oracle 串行、结束后无 BCompare 残留。

## 19. M5.5-11：评分文本轴定案 + 剩余 2 例的边界刻画（2026-10-15，纯离线，无产品改动）

§18.5 留了两个待解：f0092（唯一 fuzz 失败）与 nospace 文本轴是否更优。本轮在最终结构
（P1 扫描 + 后缀 gate + handler + NW）下把文本轴与扫描轴扫完，结论如下。

### 19.1 文本轴：`strip` 仍是正确选择（fold 假设证伪）

| 评分文本 | recorded | fuzz |
|---|---|---|
| **strip（现役：逐字裁空白）** | **281/290** | **119/120** |
| nospace（去全部空白，注释保留） | 282/290 | 118/120 |
| elem_concat（逐元素拼接，注释保留） | 282/290 | 118/120 |
| fold_all（去空白 + 全小写） | 279/290 | 112/120 |
| fold_code（代码小写、注释保留） | 279/290 | 112/120 |
| elem_code_only（只取代码元素） | 277/290 | 109/120 |

- **大小写折叠假设被证伪**：fold_all/fold_code 各掉 7 例 ⇒ 评分文本**保留大小写**（与
  §15 的 E/F 结论一致）。
- nospace/elem_concat 用 f0092 换 f0059+f0062（净 −1）⇒ **不采纳**，strip 保持现役。
- f0092 的机制已精确到区间级：`L['value value alpha','x node beta','beta'] × R['Node']`
  NW 在 strip 下选 `(3,1)`（'beta' 分 −21 > 'x node beta' −25），nospace 下选 `(2,1)`
  （−17 < −21）。**判别在 `140e726b0` 的分支选择（`job+0x58/+0x80/+0xac` 运行时旗标），
  不在评分文本**——三旗标需运行时观测，静态解码已到边界。

### 19.2 扫描轴：break 语义保持（keepgoing 证伪）

`faithful.py` 的 A 变体在 f0059/f0062 零锚（双侧重要且不等 → break）。试"设 pending 并继续
推进"（keepgoing）：

| 扫描 | 文本 | recorded | fuzz |
|---|---|---|---|
| A（break，现役） | strip | **281/290** | **119/120** |
| keepgoing | strip | 280/290 | 118/120 |
| keepgoing | nospace | 281/290 | 117/120 |

keepgoing 修 f0059/f0062 但掉 f0040 ⇒ **保留 break**。f0059/f0062 的真实根因升级为：
它们需要"扫描在重复 key 上配对"的能力（`tmp gamma`×3 之类），即 **`140e738a0` 的
`140e722a0` 边界助手在重复行上的推进语义**（该助手此前只解出"越界钳制"半边），
记为下一个未解点，不再硬凑。

### 19.3 产物与状态

- 新 scratch：`_scratch/m556/score-text-summary.txt`、`f0059-trace.txt`（两例的 scan/handler
  逐步插桩，证明"扫描零锚"）。
- 产品未改动（本轮全部为离线判别）；fuzz 仍 119/120，官方门禁仍 265/0。
- **剩余 2 例（f0092 + f0059/f0062 族）的共同前置**：需运行时观测三个旗标
  （`job+0x58/+0x80/+0xac`）或补解 `140e722a0` 的重复行语义——两者都超出静态解码与
  本阶段边界，明确保留为已知差异。

## 20. M5.5-12：`140e722a0` 补解（阴性结论）+ 扫描三轴全网格定案（2026-10-15，纯离线，无产品改动）

§19.2 定的下一步：补解边界助手 `140e722a0`，看 f0059/f0062（扫描零锚）能否靠"重复行配对"修好。结论是**阴性**，但过程排除了两条错误路径并把扫描语义完全定案。

### 20.1 `140e722a0` → `140e72af0` 补解结果

- `140e722a0`（132B）：纯越界钳制——`idx > max` 或 `loaded_len < idx` 时把上限压到 `min(idx, loaded_len)`；不越界但未建到该行时调 `140e72af0` 惰性建段，建完若仍不可用继续钳制。
- `140e72af0`（824B）：**逐行建表器**——按行推进 ctx vtable 取文本（+0x18/+0x40/+0x60 槽）、算哈希（`1405efdc0` 存 job+0x60 侧数组）、存旗标（job+0x70 侧字节）与权重（job+0xb0 侧，`140e75c50` 复合）。**不含任何配对/重复处理逻辑**。
- ⇒ "扫描在重复 key 上配对"的假设**不成立于这两个函数**。f0059/f0062 的零锚另有其因（见 20.3）。

### 20.2 重读 `140e738a0` 主循环：LAB_140e739cc 嵌套段

此前（§17/§18）把该段简化掉了。真实结构是三层：`F_left==0` 时先查 `F_right`，为 0 才进入
`LAB_140e739cc`；该段**再查一次 `F_left`**，为 0 时调外部谓词（ctx vtable+0x28，ctxB 恒
`return 0`、ctxA 为 `140682190` 字节表查询），非 0 → `break`，为 0 → pin pending 并推进左。

### 20.3 三轴全网格（break / both-insig pending / predicate）

| 配置 | recorded | fuzz |
|---|---|---|
| **A break+break+no-pred（产品现役）** | **281/290** | **119/120** |
| A2 break+bi-pending+no-pred | 281/290 | 119/120 |
| E keep+bi-pending+pred-break（字面翻译） | 279/290 | 112/120 |
| F keep+break+no-pred | 276/290 | 111/120 |

- **字面翻译（E）比产品现役（A）差 7 例** ⇒ BC 的真实行为在"双侧重要且 key 不等"时是
  **break**（伪代码的 pin+continue 分支未被走，或该分支的条件在 BC 侧另有门控）。
- A 与 A2 等价（双不重要 pending 分支在 unique-id 模型下不可达）⇒ 该轴保持未建模，无信息损失。
- **f0059/f0062 重新定性**：它们的扫描零锚不是"缺重复行配对"，而是"全文没有一处双侧重要
  且 key 相等"⇒ 按 A 的 break 语义整个文件落进一个区间，之后由 handler 的唯一层/NW 决定
  （oracle 在该区间配 4 对，产品配 0 对）。这不再是扫描层问题，而是 **handler 在"全重复
  key"区间上的唯一层判据**（`140e74b60` 的 `local_74 ≥ 0x3e9` 门与字典毒化在半数重复时
  的行为），记为下一个未解点。

### 20.4 状态

- 产品未改动（A 已是现役实现）；fuzz 119/120、记录语料 0 mismatch、官方门禁 265/0 不变。
- 制品：`_scratch/m556/pred-exact.txt`（字面扫描两读法，均劣于 A）、`_scratch/modeentry/140e72af0.c`。
- **剩余 2 例（f0092 + f0059/f0062）都需要下一层信息**：f0092 需运行时旗标
  `job+0x58/+0x80/+0xac`；f0059/f0062 需 `140e74b60` 唯一层在全重复区间的精确判据。
  两者都超出静态解码的当前边界，明确保留为已知差异，不做个例硬编码。

## 21. M5.5-13：SmartAlign 窗口引擎完全解码 + 惰性实证 + large_input 二次回归修复（2026-10-15 晚，第四例产品改动=纯性能）

§20 收尾后本轮做三件事：把 Mode3 引擎（`140e73b40` 族）解码补完并**实测它对现役
模型是否构成行为差异**；用同一测量**更正 §19/§20 的残留归因**；cargo 全量跑时
捕获并修复 M5.5-9 锚定迁移埋下的两处 O(n²)。

### 21.1 补解码（新制品 `_scratch/smartalign/`）

- `14102c470`（ctxA vtable+0x38）：窗口宽 = 对齐配置对象 `+0x3c`（int）——§13.5 留的
  "窗口宽来源"闭环；`140e72ea0`：运行时把 job+0x98 **上取整到 2 的幂（≤4096）**并分配
  两个 -1 哨兵数组；比较器 `140e73e80`（weight 降→r 升→l 升）/ `140e73cc0`（r 升→l 升）；
  `140e74080`：截断后按 140e74a70 权重重算，**<500 则 len 归零**；`140e74100` 全结构
  （截断→weight 快排→对"更晚"候选消重叠（包含→掐头、部分→丢弃）→(r,l) 终排→逐锚
  NW 间隙→尾部 param_6=1 部分回溯）。
- 工具链：REA MCP 的 Ghidra provider 在 50 MB BCompare 上每次调用**重新导入+重分析**
  （单次 `procedure_pseudo_code` 30 分钟超时），批量反编译仍走 `tools/ghidra-persistent.py`
  （持久工程，秒级）；REA 会话打开 `rea-snapshot`（digest 匹配 5.2.6 参考件）确认身份后即关。

### 21.2 惰性实证：窗口引擎在本语料上与 NW 兜底**零行为差异**

新离线模型 `_scratch/m556/model_s.py`（全保真：L 形遍历、visited 位图、对角等值游程、
重叠消解、逐锚 NW），同一 faithful 管线下测（`faithful_win.py`）：

| 模型 | recorded | fuzz |
|---|---|---|
| faithful A（现役语义，空 LIS→NW） | 281/290 | 119/120 |
| A + 窗口引擎替换空-LIS 兜底 | **281/290** | **119/120** |

机制（`cand_stats.py`/`faithful_win2.py`）：候选须游程权重 **>500** 才记录；
- key 长权重：0/334 窗口有候选；
- **真 `140e75c50` 复合权重**（重要行 2·len+50）：仅 2/668（f0094 一处，且已过）。
合成阈值演示（`win_fire.py`）：20 字符行需 ≥10 行连续等值对角线才过 500 门。
⇒ §12"Patience/Smart 之分只影响超大区间兜底、对锚点层与 NW 无差别"在**语料尺寸**上
由推断升级为**实测**：Mode3 引擎不迁移——产品空-LIS 走 NW 与 BC 在这些输入上逐例同解。

### 21.3 空-LIS 的另一分支（`+0xac==0` 对角 1:1 填充）证伪

`140e74b60` 243-260 行的对角填充分支（D 模型：min(n,m)+1 行按位置配对）实测
（`diag_fill.py`）：**248/290 + 82/120**（现值 N=281/119）⇒ D 不是这条路径，
`+0xac==0` 在 .txt 默认配置不成立（与 §13.4 门条件一致）。

### 21.4 归因更正（带日期，§19/§20 原文不改）

§20.3 说"f0059/f0062 落进一个区间后 handler 唯一层判据未解（oracle 配 4 对、产品配 0）"
——本轮 faithful 管线与产品 fuzz 双双实测：**f0059/f0062 自 M5.5-10 起已通过**。
§20 的读例来自 residual5 时代的旧插桩（§18 迁移前）。**当前唯一残留 = f0092**
（需 `job+0x58/+0x80/+0xac` 运行时旗标观测），已知差异清单据此收窄为一例。

### 21.5 large_input 二次回归：根因、修复、验证（第四例产品改动，纯性能）

`cargo test` 全量首跑抓到 `two_hundred_thousand_lines_complete_in_linear_space`
**151s > 120s 预算**（M5.5-9 锚定迁移引入，当时只跑过 198 单测+小夹具门禁）。两处都是
**我们的转写**而非解码结构：

1. `lis_overwrite_left` 线性找槽从头重扫（BC 的 patience 是增量维护）：
   tails 单调 ⇒ `partition_point` 与线性扫描**逐位等价**（3000 组随机序列验证
   `lis_equiv.py`），改二分 O(k log k)。
2. `interval_pairs_at` 每个锚点 `filter().collect()` 复制剩余区间（O(k²) 拷贝）：
   ls/rs 升序且锚点升序 ⇒ 空隙恒为**连续切片**，改按索引切分，语义不变。

**验证（全绿，行为零变化）**：该测试 **151s → 1.12s**；large_input 5/5；core 单测
198/198；记录语料 **133/133（0 mismatch）**；产品 fuzz **119/120（仍仅 f0092）**；
offline_check 101/101+31/31；官方门禁 `M55-perf-linearfix-01` **265 pass / 0 fail**
（not_run=labels 佐证，与改动无关）；结束后无 BComp/Java 残留进程。

### 21.6 已知限制（记录，不硬凑）

- 全不相交的大区间：BC 靠门 B（max>5000 委托窗口引擎）把方向阵限宽在 W×W；
  产品 `interval_nw` 仍整阵分配（20k×20k 实测可行 ~90s、~3.6GB，100k×20k 级会 OOM）。
  窗口宽 W 的**运行时值**（配置 +0x3c）未知、窗口化 NW 与整段 NW 在超大输入上的输出
  差异无 BC 大夹具可判 ⇒ 不凭猜实现，列为需要一次**大文件 Oracle 探测**的开放项。
- REA 的 `observe_native_calls` 仅支持 Mach-O（本目标是 PE），f0092 的运行时旗标观测
  仍需另寻 Windows 侧手段或大夹具判别探针。

制品：`_scratch/smartalign/`（新反编译 8 份+batch 索引）、`_scratch/m556/`
（model_s.py、faithful_win.py、faithful_win2.py、cand_stats.py、win_fire.py、
diag_fill.py、mixed_eval.py、mixed2_eval.py、flip_s_vs_a.py、lis_equiv.py）；
产品改动仅 `align.rs` 两处性能修复。

## 22. M5.5-14：f0092 判别探针定案 —— NW 打分文本对 plain 去行内空白（第五例产品改动，2026-10-16 凌晨）

### 22.1 离线单变量排除（全负）

四个"文本层"假设逐一在全语料网格上测（`_scratch/f0092/`）：
ci 字符交集 279/290+114/120；小写 score_text 279+114；词元直方图四变体
259–263；半权重折中 281+117（修 f0092 破 f0050/f0062/f0073）。基线
（区分大小写、原样 strip 文本）281+119 保持最优——**任何全局大小写折叠都是
净亏**，与 m51b "打分逐字节" 的旧探针一致。唯一例外 f0092 必须另寻判据。

### 22.2 判别探针 `probes/f0092_score_axis.py`（串行 Oracle，6 夹具）

夹具设计让候选模型给出**互异预测**，一次 Oracle 全部裁决：
- P1（f0092 原样）：BC 配 L3↔R2。
- P2 `NODEx/beta/alpha` vs `node/x`：BC 孤儿 L1，配 (beta,node)(alpha,x) →
  **区分大小写交集**（ci 会给 (NODEx,node)）。
- P5 `NODE X BETA/BETA` vs `Node`：BC 配 L2↔R1 → 再次排除折叠。
- P4 `x node beta/beta` vs `Node`：**BC 配 L1↔R1**——但区分大小写下
  'beta' vs 'Node' 是 -21 而 'x node beta' 11 字符是 -25，只有当打分文本
  **去掉行内空白**（9 字符, raw −4 → −17）才配 L1。
- P7（f0057 形状 .txt 化）：BC 孤儿 L1 → 排除对 plain 的折叠。

### 22.3 定案规则（可推广、非个例）

**`140e726b0` 的异 key 打分文本：plain 格式去除全部空白、保留大小写；语法格式
保持原样 strip 行。** 手算复核 P1–P7 七例全对（`extracted/_scratch/f0092/`
predict.py/space_axis.py）；全语料重放：
- 记录语料 288/296（探针的 6 例 oracle 被 collect 吸收）：f0092 与 P2/P4/P5/P7
  全部转对，且语法夹具无一回归——仅余原有 8 例**语法分词**已知差异
  （py-indent/js-regex-ws/triple-quote/string-internal-ws 及其 m2- 副本）。
- fuzz **120/120**（f0092 清零）。
- plain-only 门控是关键：T1 不加门控会破 f0059/f0062（语法内空白有语义）。

### 22.4 产品改动（第五例）与连带修复

`importance.rs`：`Plan::nw_score_text`（plain 去空白 / 语法原样）。
`align.rs::interval_nw` 改用它。`closeness_pairs`（M5.1b 旧层）不动。
验证：core 198/198、large_input 5/5、CLI 141+151+118、m26 **133/133**、
产品 fuzz **120/120**、m4_gate 55/57（2 既有 KD）、官方门禁
**`M5514-f0092-nwtext-01` 265/0**；无残留进程。

### 22.5 连带发现：CLI shell 测试的时钟依赖缺陷（测试修复，非产品）

凌晨 1 点首触发的 5 例 script_exec 失败与对齐无关：BC 的 log/created 实测为
`2026/10/16 1:52:09`（**斜杠日期、小时不补零**；`runs/log-hour-pad-probe/`，
od 字节级证实——注意本环境显示层会把斜杠日期渲染成短横，字节计数为准）。
产品行为与 BC 一致；断言 `len==155/122/272`、`as_bytes()[13]==':'` 把
19 字符/两位小时的戳写死了。改为 fold_time 后的时钟无关长度与结构化的
`timestamped()` 校验。**教训：任何时间戳断言必须对不补零单位数小时成立。**

制品：`probes/f0092_score_axis.py`（探针）、`runs/f0092-score-axis-*`、
`runs/log-hour-pad-probe/`、`_scratch/f0092/`（7 个离线模型脚本）。

## 23. M5.5-15：门 B 窗口引擎 Oracle 探测 —— W≈1993 实测、惰性范围收窄、移植阻塞（2026-10-16 凌晨）

### 23.1 探针一 `probes/gateb_window_probe.py`（串行，7 夹具，阈值两侧 + dup 门）

门 B 条件（重读 `callsite_140e75706.c` 255-306 行）：区间内**左侧重复 key 计数
local_74 ≥ 1001** 或 **max(n,m) > 5000** ⇒ 委托窗口引擎 `140e73b40`；否则整阵 NW
`140e74660`。夹具覆盖两个门的两侧（尺寸门 4999/5001/12000 全不相交；重复门
dup k=1000/1001 与 k=2500/2501 且尺寸≤5000）：**全部 oracle/产品行逐例 SAME**
（含指纹：全不相交→对角 1:1 全配；旋转 dup→全配 ltid=rtid+1）。⇒ 窗口引擎在
"平凡形状"上与产品整段 NW **行为等价**；§21.6 的担忧只在"区间内有远离对角的
共享块"形状上兑现（下节）。计时：S3 12000×12000 oracle 1.90s / 产品 2.31s（O(n²)
阵在 12k 仍可跑；100k 级仍不可行）。

### 23.2 探针二 `probes/gateb_width_probe.py` + 二分（8+3+4+5+3 次，窗口外共享块不配对）

夹具：区间 10100×10100（max>5000 强制窗口），两侧共享一个 K 行块，块在右移
offset 距离（扫描在 (0,0) 断 ⇒ 单区间）。观测（共享块配对数）：

| 夹具 | off≤1992 | off≥1993 | 判据 |
|---|---|---|---|
| K=100 (S1..S99, len~3) | 配 100 | **0** | 边界在 1992/1993 之间（1989-1992 配、1993-1999 不配） |
| K=50 | 1990 配 50 | 1993/1994 0 | 与 K=100 同边界 |
| K=200 | 1990 **配 200** | 2050 0 | 游程越过 1992（至 2189）仍全配 ⇒ **起点在窗内即可，游程不受窗宽截断** |
| K=2 off=1992 | 0 | — | 2×~50 权重 <500 门 ⇒ 不是纯位置窗 |
| 负偏移（共享块在左侧远） | 1990 配 100；1993 0 | | 两轴对称 ⇒ 每窗扫描 [l0,l0+W-1]×[r0,r0+W-1] 方窗，W-1=1992 |
| K=1 BIG（300 字符行，权重≈650>500） | **0**（off=1000/1992） | | **与 `500<iVar10` 候选门矛盾——见 23.4** |

⇒ **窗口宽实测 W=1993**（方窗，行列各自 ≤ l0/r0+1992；`140e72ea0` 的"上取整 2
幂"读法与实测不符，待重解）。产品整段 NW 在 off>1992 时仍配对共享块 ⇒ 这是
**真实的行为差异**（新证据），非仅性能差异：BC 的大区间只看得见起点距当前窗
≤1992 行/列的共享游程。

### 23.3 决策：移植阻塞，记录为已知差异（不硬凑）

要忠实移植需要同时解释三个实测异常，当前解码都做不到：
1. **len=1 高权重候选不发射**（BIG 行 650>500 却 0 配）——发射路径还有未知过滤
   （怀疑在 `140e74100` 或 `140e72330` 的游程消费记账里）；
2. **K=200 游程越窗仍全配** vs **off=1993 起点不扫描**——窗宽截断作用于"起点
   访问"而非"游程延伸"，`140e733b0` 里 `*param_4` 就地钳制的语义与此冲突，需重解；
3. **>4999 中止**：K=100（~5400 权重）配对成功 ⇒ `4999<iVar10` 的异常并非终止
   扫描，"abort" 读法错误。
产品现状：语料内（fuzz 120/120、记录 288/296、S1–S7）**与 BC 无行为差**；差异
仅出现在"≥1 万行区间内、距窗起点 >1992 行且 ≥~10 行连续等值"的形状。按纪律：
**不改 Myers、不实现未定案的窗口引擎**，此形状记为已知差异（第 3 例），大文件
内存上限维持 §21.6 记录。

### 23.4 制品

`probes/gateb_window_probe.py`、`probes/gateb_width_probe.py`、
`runs/gateb-window-20261015T181927Z`（S1–S7 含 oracle/产品 XML）、
`runs/gateb-width-20261015T182136Z` 与 `gateb-width2..8-*`（边界二分 + K 依赖 +
BIG/负偏移判别，全部 oracle XML 留存，未来移植的免费回归真值）。

## 24. M5.5-16：双子代理轮——StopEOL 未闭合串（第六例产品改动）+ 门 B 三疑点静态全解（2026-10-16 上午）

### 24.1 更正（带日期，§23 原文不改）

§23.1 把门 B 尺寸谓词写成 `max(n,m) > 5000`——重读 `callsite_140e75706.c:263-270`
为 **`5000 < min(左剩余, 右剩余)`**（取两侧较小者）。gateb 探针全为方阵，两读法
同解，观测结论（W=1993、两侧 SAME）不受影响。

### 24.2 实现代理：未闭合字符串 = StopEOL 单元素（可推广规则，非个例）

`importance.rs::scan_line` 三分支（Py/JS/C++）：未闭合 `'`/`"` 起一个吞到行尾的
Str 元素、**不**设跨行状态。规格依据 `bcfileformats-spec.json` 各格式 String 元素
`StopEOL:"True"`（三引号元素无此属性→仍走 Cont::MultiStr 跨行，未动）。修复同族
缺口：未闭合串内的空格/`#`/`/*` 不再泄漏为空白/注释/块注释起点（u2
`string-unterminated` 类比）。新增 3 单测；core 201、CLI 141+151+118、m26 0 失配、
fuzz 120/120、**主会话核验：8 例"语法分词 KD"对测产品二进制逐行已全等**——
旧 KD 清单出自离线简化模型不建模 Indent（m26_model_grade.facts 把缩进 split 掉），
产品二进制此前即通过，子代理如实指出。官方门禁 `M5516-py-stopeol-01` **265/0**。
**未知（子代理声明，保留）**：未闭合串跨行吞并行为无 Oracle 案例可判，按规格
StopEOL=True 取"行尾止"。

### 24.3 分析代理：门 B 反常①②已解（`_scratch/gateb/ANALYSIS.md`，O 级汇编证据）

- 反常②（>4999 不终止）**已解**：汇编 `140e73147 CMP EDI,0x1388`，raise 路径
  （Delphi 0x0EEDFADE）**无 break/return，fall-through 回循环体**，且 140e73040
  无 SEH 帧 ⇒ 软断言/上报，扫描继续。K=100（权重 5580）正常记录候选并发射。
- 反常①（K=1 长行不配）**部分解**：`140e75c50` 真实读法=**非空白行 len+30**
  （2*len+50 属空白行——§21.2 的"真权重"读法需修正），K=1·300 字符=330<500
  候选门排除；provider vtbl+0x60 的 len 语义未反编译（未知子项）。发射路径
  无专门 len≥2 门（O）。
- W=1993 澄清：`140e733b0` 窗宽来自 **job+0x98**（provider vtbl+0x38 getter），
  140e72ea0 的幂上取整只写 hash 表字段 +0x38/0x48/0x50，**不回写 0x98**——
  1993 非 2 幂无矛盾；常量注入点在本族之外（未知）。移植只需可配置整数默认 1993。
- 重放器 `replay_window_engine.py` 对 13/13 边界用例命中真实 oracle XML。
- **移植前必须解决的张力**（§7.4）：140e74b60 锚点 LIS 理论上与 off 无关地抢先
  配对远处唯一块，但 oracle 显示 off≥1993 不配 ⇒ 存在未定位的"锚点不抢先"外层
  门（疑 job+0xac/0x58 组合）。gateb-width2..8 的 oracle XML 是现成回归真值。

制品：`_scratch/pytok/`、`_scratch/gateb/{ANALYSIS.md,replay_window_engine.py,
pseudocode/,asm/}`；产品改动 `importance.rs` 三处（同文件族 StopEOL 规则）。

## 25. M5.5-17：mode3 带引擎移植 + 双引擎路由器（2026-10-16，第七例产品改动）

**背景**：§23/TODO 遗留"band 引擎移植阻塞"（三疑点）。本会话先复核磁盘实况：
`align.rs` 已被前置会话改为**纯 band**（`mode3_pairs`，2026-10-16 17:39），
`pre-mode3-backup/` 存有改动前源码；离线模拟器 `_scratch/mode3/simulate_mode3.py`
当时 102/137（gateb 存档 oracle），产品二进制门禁用 `gateb_product_replay.py`
重放得 **102/137**，core 单测 **5 红**、m26 **5 配对失配**、fuzz 119/120 —— 即
纯 band 移植把实语料打红，但把大体量门 B 用例转绿。

### 25.1 架构定调：CLI 是**双引擎 + 路由器**，不是纯 band

对 42 个 `gateb-mode*` 存档 cell 逐格核对形状签名（ANCHOR = 存在 `similar`
行/非位置配对；WINDOW = 头部右孤 + 位置 `different`）：

| 侧数 (L,R) | 形状 | 侧数 (L,R) | 形状 |
|---|---|---|---|
| (2,2) | WINDOW | (12,15) | WINDOW |
| (4,15) (15,4) | ANCHOR | (13,13) | WINDOW |
| (5..8,15) | ANCHOR | (22,12) | ANCHOR |
| (12,12) | ANCHOR | (12,22) | WINDOW |

⇒ 规则**按侧**且不对称：`L > 8 且 R > 12` 走 band（`140e73b40`），否则走
handler（`140e74b60` 锚点 LIS 链）。**42/42 零误分类**；§23.4/§24.3 的"锚点
不抢先外层门"张力由此消解——不需要额外门，两个引擎各管一段。
（`min(L,R) < 3` 的 2×2 格由 band 的 NW 反走产生 oracle 形状。）

### 25.2 离线模拟器（`_scratch/mode3/simulate_mode3.py`）

两处修复把模拟器从 102 提到 **119/137**：
1. **same-key 分数用权重族**（`FUN_140e74a70` → `job+0xb0`，即 `len+30` 族），
   不是文本长度——单字符行同键分数由 4 变 124，正是小区间形状的判据；
2. **补 `similar` 状态**（raw 相等→`same`，折叠 key 相等→`similar`），
   此前模拟器只发 `same`/`different`。
新增 `handler_rows`（`140e74b60` 忠实模型：前缀/后缀裁剪 + 唯一-唯一配对 +
patience LIS + 递归 + 头侧 NW）与路由器；`ENGINE=band|handler` 可强制单引擎
（band-only 114、handler-only 32、router 119）。

### 25.3 产品落地（第七例改动，`align.rs`）

- `interval_pairs` 恢复为**路由**：`L>8 && R>12` → `mode3_pairs`，否则
  `interval_handler_pairs_at`（从 `pre-mode3-backup` 恢复的既有实现）。
- 保留 band 引擎全部解码细节（W=1993、候选门 500、200 行孤儿块、param_6=1
  尾抑制）。

**验证（全绿）**：core **201/201**（5 红清零）、CLI 141+151+118、fuzz
**120/120**、m26 **133/133（0 配对失配）**、offline_check 101/101+101/101+31/31、
`large_input` 5/5、官方门禁 `M5525-mode3-router-01` **265 pass / 0 fail**
（唯一 not_run 为 reference 安装不可用的 labels 佐证）。无残留进程。

### 25.4 已知差异（记录，不硬凑）

- **gateb 合成语料 104/137**：剩下 33 例 = 带边界族 **18** 例
  （`W-off*` 12 + `K50/K200-off*` 3 + `neg-off*` 3）与小区间格 **15** 例
  （`AX-2x13`/`MF-pad*`/`GR-*x13` 等）。根因单点：小区间路径里
  `lis_overwrite_left`（**左序迭代**，实语料验证：m26 133 + fuzz 120）与
  oracle 的**右序**臂在交叉平局上相反。右序实测：fuzz 116/120、m26 4 失配
  （+13 合成格）⇒ **实语料优先，保留左序**。该取舍已由 A-F 六配置矩阵隔离
  （权重版 same-key 与 LIS 序两变量独立：权重版对实语料零效应）。
- 小区间格剩余差异同源于此，不是新机制。
- 带边界族 18 例（`W-off1990` 等）为 `140e74660` 的 `stop_at_edge` 裁剪
  与真 oracle 的次生差，仍在案。**（§30 已收口：尾 NW 盒 = cursor+1999，
  第十例产品改动，18 例全消。）**

制品：`_scratch/mode3/{simulate_mode3.py,gateb_product_replay.py,sim_replay_fuzz.py,
align.rs.{final-20261016,validated,mode3port},reacmp-anchor.exe}`；
存档真值 `runs/gateb-*`（137 例 oracle XML）为免费回归。

## 26. M5.3-1：JAVA 语法格式落地（2026-10-16，第八例产品改动）

M5.3（语法格式覆盖扩展）开工。Java 是盘点后的第一优先候选（M2 起在案的
`.java` 大小写误报 similar 已知差异）。

### 26.1 判别探针（Oracle 真值先行，实现之前）

`probes/m53_java_grammar.py`：16 对夹具、每对隔离一条语法规则，串行 Oracle
采真值（runs `m53-java-20261016T174435Z`）。**16 条规则全部按规格预测命中**
（唯一"miss"是预测表没算字节相同行= same，Oracle 反而更符合语法）。定案规则：

- 重要元素逐字比较（大小写保留）：identifier/keyword **大小写-only 改动 =
  different**；注释/空白不重要（`similar`），跨行 `/* */` 体不重要。
- Java **无 Indent 元素**（不同于 Python）：行首缩进差异 = `similar`。
- 两种引号 `'`/`"` 均为 String：Escape=92（`\` 转义）、**StopEOL**——未闭合
  串吞到行尾，串内 `//`/`/*` 是重要串内容，且**不设跨行状态**（下一行重新
  分词；`str-vs-block` 实测无泄漏）。
- realistic 16 行类文件行级真值归档（注释行 similar、大小写行 different）。

安装身份澄清（无异常）：`harness.installs` 的 **current** =
`D:\BCompare\BCompare`（引擎 5.2.1.32035 汉化版，BComp.com 自身 PE 版本号
5.0.3.30240 只是启动器文件版本），`D:\bc-official\app` 是 reference 英文版
——与历次门禁同源。

### 26.2 产品落地（`importance.rs`，第八例改动）

`Grammar::Java` 变体 + 路由（`IMPLEMENTED` 增 `("JAVA", Grammar::Java)`，
mask `.jav/.java`）；`scan_line` 分支：`//`/`/*` 与 Cpp/JS 共享；双引号分支
= JS 同形（escape + StopEOL）；无预处理器指令、无 verbatim 串、无 regex、
`$` 按规格不进 `\w`（信息性分类，verdict 只取决于注释/空白，与既有认识
一致）；`scan_number` 对 Java 关闭 `0x` 十六进制（规格无数制元素，信息性）；
`JAVA_KEYWORDS`/操作符表为公开语言事实（不改变 verdict）。

### 26.3 验证

- core **206** 全绿（+5 Java 用例：大小写、注释/空白、跨行块注释、串内容、
  StopEOL 无泄漏）；探针夹具离线重放 **16/16 全等**（含 realistic 行级）。
- CLI 141+151+118、m26 **133/133（0 失配）**、fuzz **120/120**、
  offline_check **101/101+101/101+31/31**、large_input **5/5**。
- **20 个 Java 金标锚点**入库（`tools/m53_add_java_anchors.py`，
  unit `M5JavaGrammar`，manifest 101→121；runs `m53-anchors-20261016T175259Z`）。
- 官方门禁 `M53-java-grammar-01`：**306 总数 305 pass / 0 fail**
  （anchor 121×2、layout 31×2、folder 1 全绿；唯一 not_run 仍是 reference
  安装不可用的 labels 佐证，与改动无关）。结束后无 BCompare 残留进程。

### 26.4 M5.3 剩余面

18 个格式待逐语法开工（HTML/XML/SQL/Perl/Bash/Pascal/VB/PowerShell…）。
流程已定型：判别探针采真值 → 实现语法 → 探针夹具离线重放 → 金标锚点入库
→ 官方门禁。多行/容器类格式（HTML/XML 标签跨行、PowerShell here-string）
预计需要新的 `Cont` 状态形态，是下一批的主要工作量。

## 27. M5.3-2：XML / HTML / SQL 语法格式落地（2026-10-16，第九例产品改动）

M5.3 第二批：三个最常用文本格式。判别面比 Java 深一层——**大小写策略是逐格
式的实测规则**，不是全局假设。

### 27.1 三轮判别探针（Oracle 真值先行）

- `probes/m53b_xml_html_sql.py`（20 例，runs `m53b-xml-html-sql-20261016T180351Z`）：
  规则面。14/20 预测命中；6 个 miss 全是模型修正信息。
- `probes/m53c_case_model.py`（14 例，runs `m53c-case-model-20261016T180715Z`）：
  大小写模型。13/14 命中，唯一反例（HTML 实体）引出第三轮。
- m53d 迷你探针（6 例，runs `m53d-edge-*`）：实体表匹配语义、SQL `n` 前缀、
  单引号串。

### 27.2 实测定案（全部有活 Oracle 证据）

- **XML/HTML 大小写策略（TXMLFormat 结构化比较器行为的行级模型）**：字符串
  内容之外的**一切大小写差异不重要**（标签名/属性名/文本/裸文本全 similar，
  `<?xml` vs `<?XML` 也 similar）；**字符串内容逐字**（属性值大小写
  different）。`<!--`→`-->` 注释跨行且**未闭合时状态持续到下一行**；串
  StopEOL 且**无 Escape 属性**（`\` 不转义，`"x\"` 在第二引号闭合）。
- **HTML 实体**：261 个命名实体（W3C HTML4 公开数据，BC 表含 9 处重复）按
  **大小写敏感**匹配——`&copy;` 在表内=Keyword 逐字比较；`&COPY;` 不在表内
  =未声明文本折叠。**类别配对语义**：列表内实体 vs 折叠后同字节的其他文本
  = different（m53d），纯"拼接+折叠"模型在此翻车。
- **SQL**：Keyword/Identifier 元素 CaseSensitive=False ⇒ 大小写折叠
  （`SELECT`/`select`、`t1`/`T1` 均 similar）；String 是**完整匹配正则**
  （无 StopEOL）：未闭合引号**不吞行尾**，后面的 `--` 仍是真注释（similar，
  与 Java 行为相反）；已闭合串吸收 `--` 为内容（different）；`''` 双写、
  `\'` 转义在串内；**`n`/`N` 前缀属串 token 逐字比较**（different）。

### 27.3 产品落地（`importance.rs`，第九例改动）

`Grammar::{Xml,Html,Sql}` + 路由；`scan_line` 新分支（`<!--` 注释、StopEOL
无转义串、HTML 实体 `match_html_entity`、SQL `scan_sql_string` 完整匹配）；
`span_folds` 逐 span 大小写策略；`LineFacts.profile`（每行 span 类别序列
`S/K/O`）+ `Plan::verdict` 类别配对检查——只对 Xml/Html/Sql 启用，C-like
格式零行为变化。`HTML_ENTITIES`（261 项，公开数据）为唯一行为性数据表。

### 27.4 验证

- core **213** 全绿（+7 XML/HTML/SQL 用例）；三批探针夹具离线重放
  **50/50 全等**（m53 16 + m53b 20 + m53c 14，含 4 个 realistic 行级真值）。
- CLI 141+151+118、m26 **133/133（0 失配）**、fuzz **120/120**、
  offline_check **121/121+121/121+31/31**、large_input **5/5**。
- **35 个金标锚点**入库（`tools/m53b_add_anchors.py`，unit `M5XmlHtmlSql`，
  manifest 121→**156**；runs `m53b-anchors-20261016T182326Z`）。
- 官方门禁 `M53-xml-html-sql-01`：**376 总数 375 pass / 0 fail**
  （anchor 156×2、layout 31×2、folder 1 全绿；唯一 not_run 仍为 labels 佐证）。
  结束后无 BCompare 残留进程。

### 27.5 M5.3 剩余面

**15 个格式**待开工：PERL/BASH（正则元素、POD 块、`$'`/`$"` 前缀）、
PAS/VB/COBOL/REG/CSV/DFM、二进制/文档类（EXE/MEDIA/MSEXCEL/MSWORD/
OPENOFFICE/PDF/PIX/RTF/SORT——多为专用比较器，超出文本语法范围）。
流程定型五步闭环不变。

## 28. M5.3-3：PAS / VB / REG / COBOL / DFM 语法格式落地（2026-10-16，第十例产品改动）

M5.3 第三批：五个 TTextFormat。判别探针 `probes/m53e_batch3.py`（31 例，
runs `m53e-batch3-20261016T183026Z`，**31/31 预测全中**）+ m53f 边界 4 例
（runs `m53f-edge-*`）。

### 28.1 实测定案

- **PAS**：`{$...}` 编译器指令是**重要**元素（`{$X+}` vs `{$Y+}` =
  different，与 `{ }` 注释的元素顺序区分）；`{ }` 与 `(* *)` 注释跨行且
  未闭合持续（m53f）；字符串是**完整匹配正则**（`'..'` 含 `''` 双写、
  `#65` 字符字面量、**无反斜杠转义**）——未闭合 `'` 落回普通分词，后面的
  `//` 仍是真注释（SQL 族行为）。关键字/标识符大小写折叠。
- **VB**：`'` 与 **`rem `（未锚定，行中出现也算）** 注释到行尾；字符串是
  正则且带 **EOL 锚定回退**（`"([^"]|"")*$`）——未闭合 `"` **吞到行尾**
  （与 SQL/PAS 相反），`""` 双写在串内，可选 `c` 后缀。大小写折叠。
- **REG**：注释**仅行首锚定**（`^\s*;`）——行中 `;` 是普通重要文本
  （`x = 1 ; note` = different）；串 Escape=92 + StopEOL；`dword`/`hex`
  关键字**大小写敏感**（m53f different）⇒ REG 全逐字比较。
- **COBOL（列制）**：**列 1-6 与列 73-80 的 LineNum 元素不重要**（新增
  `Kind::LineNum`）；列 7 `*` 使整行其余部分成注释（`^.{6}\*`），列 7 之外
  的 `*` 是操作符（m53f）；`"` 串 Escape=92 + StopEOL。
- **DFM**：`#65` 与 `'..'` 完整匹配串；**无注释元素**（`{ note }` vs
  `{ other }` = different）。

### 28.2 产品落地（`importance.rs`，第十例改动）

`Grammar::{Pas,Vb,Reg,Cobol,Dfm}` + 路由；`Kind::LineNum`（重要文本与
profile 均排除）；`scan_pascal_string`/`scan_vb_string`（后者含 EOL 回退与
`c` 后缀）；`span_folds` 扩展（Reg 全逐字；Pas/Vb/Dfm/Cobol 折叠非串
span）；verdict 类别配对扩展到新折叠格式。PAS 未闭合 `{$` 指令按 EOL 有界
实现——其持久性在 verdict 层不可观测（指令与代码都是重要类），已记录。

### 28.3 验证

- core **219** 全绿（+6）；m53e+m53f 夹具离线重放 **35/35 全等**（含
  pas/vb realistic 行级）。
- CLI 141+151+118、m26 **133/133（0 失配）**、fuzz **120/120**、
  offline_check **156/156+156/156+31/31**、large_input **5/5**。
- **35 个金标锚点**入库（`tools/m53e_add_anchors.py`，unit
  `M5PasVbRegCobolDfm`，manifest 156→**191**；runs
  `m53e-anchors-20261016T184054Z`）。
- 官方门禁 `M53-pas-vb-reg-cobol-dfm-01`：**446 总数 445 pass / 0 fail**，
  结束后无 BCompare 残留进程。

### 28.4 M5.3 收口盘点

25 个格式条目中 **12 个文本语法已实现**（CPP/PYTHON/JS/JAVA/XML/HTML/SQL/
PAS/VB/REG/COBOL/DFM）。剩余 12 条目：**文本语法仅剩 BASH 与 PERL**
（正则元素、POD 块、`$'`/`$"` 前缀——需要新的匹配机制）；其余 **10 个是
专用比较器，划出文本语法范围**（CSV=TTableFormat 列结构、EXE/MEDIA/PIX=
二进制、MSEXCEL/MSWORD/OPENOFFICE/PDF/RTF=文档比较器、SORT=无扩展名掩码），
若将来要做属于独立里程碑（表格/文档结构比较），不属文本语法。

## 29. M5.3-4：PERL 语法落地 + BASH 实测为纯文本（2026-10-17，第十一例产品改动，文本语法收口）

M5.3 最后一批：**13 个文本语法全部实现**（含本例 PERL）。BASH 以实测结论
定案为**纯文本行为**（零改动）。判别探针七轮串行：m53g（32 例，runs
`m53g-bash-perl-20261017T075649Z`）→ m53h/i/j/k/l/m（边界 27 例，runs
`m53*-20261017T08*`）。

### 29.1 BASH = 纯文本（实锤，非差异）

m53g-m53j 五连测：`.sh` 的大小写不敏感、**行首 `#` 差异 = different**
（`# alpha` vs `# beta` 在 BC 的 .sh 里也是重要文本，对照 `.pl` 同形
similar）、串内大小写/空白全折叠——与 plain（`.foo` 控制组、当前产品回退）
**逐案例全等**；当前 plain 二进制直接重放 m53g 的 15 个 BASH 夹具
**15/15 全等**。结论：BC 对 .sh 的行为就是纯文本（其 BASH 语法在 CLI 文本
比较路径上不生效），产品维持 `Grammar::PlainText` 路由即为正确实现，并用
4 个 `m53p-bash-*` 锚点把该行为钉成规格（防止未来误加语法）。

### 29.2 PERL 实测定案

- **一切逐字比较**：`CaseSensitive=False` 只改变 token 切分、不改变
  比较——`$Name`/`$name`、`@Items`/`@items`、裸词 `Name`/`name`、
  `0x1F`/`0x1f` 全 different（m53e/m53g/m53i/m53m）。唯一折叠策略的例外；
  其余折叠格式（SQL/PAS/VB/DFM/COBOL）的机制相同，只是恰好没有跨类碰撞。
- **POD 块行锚定**：`=pod`/`=head\d`/`=item`→`=cut`、`=over`→`=back`、
  `=begin`→`=end`；开/停行都是整行注释；**停标记必须行首**——`x =cut y`
  不关闭块（m53g `perl-pod-mid-cut`：第三行 similar=仍在块内）；停行的
  尾部属于注释（m53k `=cut Z1` vs `=cut Z2` = similar）；未闭合持续到
  文件尾。
- **`"`/`'` 串 = StopText 无 StopEOL：跨行**且吸收 `#`（m53g
  `perl-dquote-multi-hash`），闭合引号可在续行列 0（m53k
  `str-closed-next-line`），Escape=92。
- **quote-like 按规格顺序完整匹配**：`q(...)`/`qq(...)`/`s(...)`（`[^)]+`
  内容，无嵌套）；`(s|tr)/.../.../` 两段吸收 `#`；**无 `#` 定界形式**——
  `s#a#b#c#d#` 的第一个 `#` 就是注释（m53l similar）；除法形 `/[^/]*/`
  **是真实元素**：`a / b / c` 配对 `/ b /`（m53g different）、`/a # b/`
  吸收注释符。
- `#` 注释（含行首，shebang 无特例——m53h）。

### 29.3 产品落地（`importance.rs`，第十一例改动）

`Grammar::Perl` + 路由（`IMPLEMENTED` 增 PERL）；`Cont::StrQuote(char)`
（跨行串续行，闭引号可在列 0）与 `Cont::Pod(&str)`（停标记行首判定、
停行整行归注释）；`pod_start`、`scan_bracketed`、`scan_slash_form`、
`scan_slash_regex` 按规格语义；`span_folds` 对 Perl 全逐字；
`matches_keyword`/`operators` 补分支；`.sh` 留在 PlainText（实锤行为）。

### 29.4 验证

- core **223** 全绿（+4 PERL 测试函数，覆盖 m53g/m53k/m53l/m53m 全部
  关键规则）；**m53 系列十二轮探针夹具离线重放 144/144 全等**
  （java 16 + xml/html/sql 34 + batch3 35 + m53f 4 + bash/perl 32 +
  27 边界）。
- CLI 141+151+118、m26 **133/133（0 失配）**、fuzz **120/120**、
  offline_check 191+191+31、large_input **5/5**。
- **21 个金标锚点**入库（`tools/m53p_add_anchors.py`，unit
  `M5PerlGrammar`/BASH 组，manifest 191→**212**；runs
  `m53p-anchors-20261017T085346Z`）。
- 官方门禁 `M53-perl-bash-01`：**488 总数 487 pass / 0 fail**（anchor
  212×2 全绿；唯一 not_run 仍是 labels 佐证）。无 BCompare 残留。

### 29.5 M5.3 文本语法收口

13 个文本语法全部落地并金标钉死：CPP、PYTHON、JS、JAVA、XML、HTML、SQL、
PAS、VB、REG、COBOL、DFM、PERL（+BASH 实测=plain）。剩余 11 个格式条目
全部是**非文本语法**（CSV=TTableFormat 列结构、EXE/MEDIA/PIX 二进制、
MSEXCEL/MSWORD/OPENOFFICE/PDF/RTF 文档比较器、SORT 无掩码），属独立
引擎/里程碑，不在文本语法范围（§28.4 定案）。M5.3 完成。

## 30. M5.5-30：带边界 18 例攻坚——尾 NW 盒 2000 定案（2026-10-17，第十例产品改动）

§25.4 在案差异的带边界族 18 例（`W-off*` 12 + `K50/K200-off*` 3 + `neg-off*` 3，
即 `gateb-*` 存档 137 例中产品 104/137 的缺口）本轮收口。

### 30.1 定位过程（离线模拟器 = 零成本试验台）

1. 产品重放与模拟器逐例复现同一 18 例（模拟器 119/137，产品 104/137 的差
   15 例 = 在案 handler LIS 序小区间格）——模拟器是忠实试验台。
2. 分数变体扫描排除公式分支：`formula` 119 vs pen40/forbid/sub18 的 63/16/63。
3. `W-off1990` 角部格级对照：oracle 隐含路径在**我们的 S 矩阵**下总分
   -6995 > 模拟 DP 路径 -7032 ⇒ 分歧不在平局/方向表（NW_TIE 试验 117/137
   回归证伪），而在**尾段 NW 的盒几何**。
4. 双盒参数实验：采集盒 W=1993 不动、尾 NW 盒 WT 独立扫描——
   **WT=2000 ⇒ 带-only 132/137（18 例全消）**；WT=1993/1994-1996/2001-2003/
   4000/5000/∞ 全部 114-118；**WT=2000 + 路由器 ⇒ 137/137 全过**。
   （全局 W=2000 仅 121 且破坏 off 1992/1993 收集边界夹具——尾盒与采集盒
   必须是两个量。）

### 30.2 判别探针（Oracle 真值先行，串行）

- `probes/gateb_tailbox_probe.py`（runs `gateb-tailbox-20261017T132135Z`）：
  K=2 纯 DP 起点扫 off∈1990..2005 + K=100 块起点扫 1980..1993，29 例。
  K=2 块因与头部共享键走位置配对，判别力不足（诚实记录）。
- `probes/gateb_tailreach_probe.py`（runs `gateb-tailreach-20261017T132903Z`）：
  **TB1-k20-off1990**（K=20 权重 640>500 走 run 收集，使 iter2 游标落在
  **新位置** (20,2010)）——单盒 1993 模型逐行 DIFF、**双盒 2000 模型 MATCH**，
  独立于 137 例存档钉死 2000；TB2（盒被表尾钳制）与 TB3（双块 2000 间距）
  两模型一致（无回归信息量，如实记录）。
- `probes/gateb-tailbox2`（runs `gateb-tailbox2-20261017T132957Z`，12 例内联）：
  两模型全 MATCH——确认 2000 不在这些形状上引入新差异。

### 30.3 产品落地（`align.rs`，第十例改动）

`MODE3_TAIL_WINDOW = 2000`（新常量，doc 注释记录测量证据与"未解码"性质）：
`runs.is_empty()` 的尾 NW 分支改用独立尾盒 `[cl..cl+1999] × [cr..cr+1999]`
（各自钳到表尾），回溯裁剪回写 `cl = tail_l + 1 - rem_l`。采集盒、候选门、
重叠消解、路由、handler 臂一概不动。

### 30.4 验证与在案残留

- core 223、CLI 141+151+118、**m26 0 失配、fuzz 120/120**、large_input 5/5
  （1.06s，尾盒 +7 无性能代价）。
- 产品重放 `gateb-product-replay-20261017T135118Z`：**167/182**（137 存档 +
  45 新探针夹具）——**带边界族 18 例 = 0**、45 例新夹具全过、
  剩 15 例 = 在案 handler LIS 序小区间格（AX/MF/GR，§25.4 记录，非新机制）。
- 官方门禁 `M5530-tailbox-01`：**488 总数 487 pass / 0 fail**（anchor 212×2
  全绿；唯一 not_run = reference 不可用的 labels 佐证）；无 BCompare 残留。
- **残留未知（记录，不硬凑）**：+7 的代码级来源未定位——`140e733b0` 的
  `*param_4/*param_5` 盒界与 `140e74100` 尾段 `local_50/local_44` 在反编译里
  同源（应同为 cursor+1992），BC 真值却是 1999。候选解释（游标前进量回写、
  窗口格阵分配取整、param_6 分支差异）均未证实。行为已由 182 例夹具钉死，
  来源问题不阻塞；后续若做三/四路对比（更大语料）再攻。

## 31. 维护收口（2026-10-17，合成语料宣告关闭）

- 全电池复验：core 223 / CLI 141+151+118 / m26 237 例 0 失配 / fuzz 120/120 /
  仿真器 182/182 / 产品重放 167/182（失败恰为 §25.4 在案 15 例）。
- 官方门禁 `M5531-maintenance-02`（中/英双安装 + 产品候选）：**762/762**，
  labels 佐证 31/31 —— §30 那例 not_run（reference 不可用）收口：英文安装
  5.2.6.32774 现于 harness `enabled=True`。无 BCompare 残留。
- 修复四处**冻结清单计数**（101→212 过时钉死：test_runner、test_oracle_live
  ×2、run_cli 标签），改为与 `load_anchors()` 动态一致；harness pytest
  157/157。教训入册：`product/docs/12-maintenance-regression.md`。
- 本轮曾把 pytest（含真 Oracle 用例）与门禁并发跑，出现 3 例 exit 107 假阴性；
  串行重跑全部通过。**Oracle 串行纪律覆盖一切会真启 BComp.com 的电池。**
