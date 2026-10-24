# 报告布局黄金数据（30 例）

> 生成：2026-10-13，`python tools/bc-layout-capture.py`。
> 5 个代表性输入对 × 6 种布局（side-by-side/interleaved/patch/summary/statistics/over-under）。

## 实测格式规则（全部经字节级验证）

| 布局 | 规则 |
|---|---|
| **共同头** | `Text Compare\r\n` / `Produced: yyyy/mm/dd h:nn:ss\r\n` / 空行 / `Mode:  All\r\n` / `Left file: ...     Right file: ...\r\n`（summary/statistics 无 Mode 行） |
| **side-by-side** | 左列 pad 到最长左内容宽；`=`（same，后 2 空格，全 same 报告时 1 空格）/ `<>`（different，后 1 空格）/ `+-`（左孤儿）/ `-+`（右孤儿）；**同块连续 same 行只首行显示标记**；分隔线 = 全报告最长行宽的 `-` |
| **interleaved** | `ln rn 内容`（same）；非 same 块**先列全部左行再列全部右行**（另一列留空）；分隔线宽 = 全报告最长行 |
| **patch** | `diff -r L R`；`a,b c,d` 全范围（单行折叠）；`d` 右侧 = 块前右行数；`a` 左侧 = 块前左行数；`---` 仅 c 形式；`<`/`>` 前缀 |
| **summary** | 计数行（same / unimportant difference / important left|right orphan / important difference）+ 空行 + `N difference section(s)`；0 段时省略尾部 |
| **statistics** | CSV：`SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error` |
| **over-under** | **字节级等同 interleaved**（官方已废弃） |

## 验证结果（bcx 对拍）

| 布局 | 通过 |
|---|---|
| statistics | 5/5 |
| summary | 5/5 |
| interleaved | 5/5 |
| over-under | 5/5 |
| patch | 5/5 |
| side-by-side | 4/5 |
| **合计** | **29/30** |

**patch 行号规则（2026-10-13 探针网格实测，BC 用游标位置而非标准 diff 行号）**：
- `c` 形式：`左起[,左止]c右起[,右止]`（真实行号，单行折叠）
- `a` 形式：`锚a右起[,右止]`，锚 = 块前已对齐左行数（**≤1 时钳为 0**）
- `d` 形式：`左起[,左止]d锚`，锚 = 块前已对齐右行数（**≤1 时钳为 0，否则减 1**）

已知限制（1 例）：
1. `mixed-side-by-side`：配对行左内容填满整列时 BC 省略标记字形（`real diff 1    real diff 9`）——精确触发条件未建模（孤儿行同宽度不省略）。

**2026-10-14 已解决（M5.1）**：上面的"填满整列"假设被推翻——`identical-side-by-side` 的行 `y` 同样填满 1 字符列却被空白，而首行 `x` 有 `=`。真实规则是**槽位字形属于整个块、只画在块首行**（same 块 `=`、纯左孤 `+-`、纯右孤 `-+`、含配对行 `<>`），后续行一律空白槽位；证据为 `product/verify/probes/m51_sbs_marker.py`（`runs/m51-probe-*`）与 `runs/m51b-probe-*`。产品已实现，布局语料 31/31 全绿（`product/cli/tools/offline_check.py`）。同一探针还定案了块内配对的平局规则（最小化已配对左行长度，见 `product/core/src/align.rs` 模块注释）。

## 复现

```bash
python D:\Rea\tools\bc-layout-capture.py    # 重捕
python D:\Rea\tools\bcx-layout-verify.py    # 对拍
```
