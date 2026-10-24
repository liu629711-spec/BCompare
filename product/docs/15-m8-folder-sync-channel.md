# M8 — 文件夹同步通道（`sync`）

功能矩阵 4 号（文件夹同步/复制，U8）。唯一**有副作用**的模块：所有结论都来自
`runs/m80*`、`runs/m81*`、`runs/m82*` 的实测（一次性 temp 树，Oracle 串行 +
Job-Object 包含，每格后残留进程检查 = 0）。

原则：不硬凑。每一条规则下面都标着它的实测格子；无法解释的单发差异如实记为
**在案残留未知**，不写进产品语义。

---

## 1. 语法面（measured）

```
sync [visible] [create-empty] (update|mirror):(left->right|right->left|all)
```

| 形态 | exit | 证据 |
|---|---|---|
| `sync update:left->right` / `sync mirror:right->left` | 0 | m81 A1/A2/A3/E3 |
| `sync update:all` | 0 | m81 A5、m81e E5 |
| `sync mirror:all` | **106** | m81 A4（公帮助明文：`all` 对 mirror 无效） |
| `sync visible mirror:…` | 0 | m81c C8、m82b X2 |
| `sync create-empty mirror:…` | 0 | m81f F3 |
| `sync visible create-empty update:…`（两旗标任意先后） | 0 | m81g G5、m81h H1a/H1b |
| `sync update:left->right visible`（旗标在 mode 之后） | **106** | m81f F2-1 |
| `sync update visible:…` / `sync visible:create-empty …` / `sync create-empty:yes …` | **106** | m81f F2-2/3/4 |
| `sync update:lr`（缩写） | **106** | m81g G7 |
| 裸 `sync` / `sync bad:lr` / `sync update` / `sync update:left` / 尾部多余位置参数 | **106** | m81b B8-1..6/8 |
| `load "<L>"` 半载后 sync | **100** | m81g G6 |
| 无 `load` 时 sync | **0**（静默无操作） | m81 A7、m80 S4/S5 |
| `sync` 出现在命令行（非脚本） | 106（`args.rs` 按名拒绝） | 09 §5 |

`visible` 与 `create-empty` 都在 **mode 之前**且相对顺序任意；mode 必须紧跟。

---

## 2. 语义模型

对偶分类复用 `reacmp_dir::compare_folders_filtered` 的既有 `Status`（它的
`timestamp:2sec` 容差正是实测边界：Δ2s 判 Same、Δ3s 判较新 —— E1/H4 vs D3/H4b）。

| Status | `update:DIR` | `mirror:DIR` | 证据 |
|---|---|---|---|
| `Same` | 不动 | 不动 | m81 A1 |
| `LeftNewer`/`RightNewer`（源侧较新） | **拷贝**（保留源 mtime） | **拷贝** | m81 A1、m81d D5、m82d N1 |
| 同上，但**目标侧**较新 | 不动 | **不动**（目标较新对不被覆盖） | m81d D2、m81f F6 |
| `Diff`（同时间戳但内容/尺寸不同） | 不动 | **拷贝**（源赢，不论谁大谁小） | m81c C6/C7、m81d D1/D6、m82d N3 |
| 源侧孤儿（文件/目录） | **拷贝**（递归） | **拷贝** | m81 A1/A5、m81b B4、m82d N2 |
| 目标侧孤儿（文件） | 保留 | **删除** | m81 S1/A2、m82b X1 |
| 目标侧孤儿（**非空目录**） | 保留 | **删除（整树）** | m81b B6、m81c C4 |
| 空源 + 非空目标 | 保留 | **目标清空** | m81c C4 |
| kind-conflict（一边目录一边文件） | 双方都不动 | **删目标项，源项不落地** | m81h H3/H3b、m82c K1/K2 |

### 旗标
- **`create-empty`**：只有它能让"子树无文件"的源孤儿目录落到目标
  （m81h H1c）；默认跳过（m81h H1d、m82b X5 的 `innerEmpty`）。
- **`visible`**：脚本里对删除/拷贝本身**无效果**（m82b X2 仍删除），但会
  **使 `create-empty` 失效**（m81h H1a/H1b、m81g G5、m82c K4）。

### 其他
- 拷贝**保留源 mtime**（m81d D5、C2/C3：`age_h` 与源一致）。
- **不使用当前 selection**（公帮助明文；m80 S2/S3/S4 无 selection 时
  copy/delete/moveto 全部 exit 0 无操作）。
- **filter 会约束 sync**：不匹配的孤儿不被删除也不被拷贝（m81h H2b、
  m81f F4b）；匹配的照常删除（m82b X3）。产品实现里 sync 不施加 filter
  —— 这一点与 Oracle 有差异，见 §4。
- **criteria 被 sync 服从**：`criteria size` 下同尺寸不同内容判 Same、
  不拷贝（m81g G5/R5 复现），孤儿仍拷贝。
- **幂等**：连续两次 update 无额外效果（m81f F5）。
- 无 `expand all` 也照样递归（m81b B7）。

---

## 3. 实现落点

| 层 | 文件 | 内容 |
|---|---|---|
| AST | `cli/src/script/ast.rs` | `Command::Sync { visible, create_empty, mode, direction, line }` + `SyncMode` / `SyncDirection` |
| 解析 | `cli/src/script/parse.rs` | `parse_sync()`：两旗标（任意序、须在 mode 前）+ `mode:direction` 单 token；`mirror:all`、缩写、畸形全 106 |
| 执行 | `cli/src/script/exec.rs` | `do_sync()`：先比较建**计划**（`SyncAction`），再按序应用；`sync_node` 递归映射 Status；`apply_action` 走 `std::fs` |
| 日志回显 | `render_command` | `sync [flags] mode:direction` |
| 退出码 | `exit_code::NEEDS_INPUT = 100` | 半载 sync（m81g G6） |

副作用**先计划后应用**：拷贝在前、删除在后，任一失败即整脚本失败（107），
不会留下半应用的树。

ADR-3（只读内核）仍然成立：`reacmp_dir` 不写盘，写操作只在 CLI 执行器；
命令行层面 `sync` 依旧按名拒绝（106），只有脚本里的显式 `mirror` 才能触发删除。

---

## 4. 已知差异 / 在案残留未知

1. **filter 与 sync**：Oracle 的 filter 会约束 sync（H2b/F4b），产品不施加。
   未实现——`sync` 使用 `Filter::none()` 比较。记为已知差异（不是静默行为）。
2. **kind-conflict 的顺序原因未明**：H3 里"删目标 + 不拷源"是实测结果，但
   BC 内部判定顺序（先删后判类型？）无证据，产品按结果建模。
3. **单发未复现**：m81c C1-control（单对 L 较新 update 未拷贝）与 m81c C1
   （`criteria timestamp:2sec` + update = 105）在 m82 的三次重复中均未复现
   （R1a-c 全拷贝、R3/R4 全 exit 0）。按"不硬凑"原则，未写进产品语义，
   只在此存档。

---

## 5. 门禁 / 回归（M82-gate-01）

| 项 | 结果 |
|---|---|
| 门禁（anchor/layout/table/hex/folder） | **276/277**（labels 因 reference install 不可用 not_run，既有状态） |
| CLI `cargo test` | **170 passed**（其中 sync 集成测试 9/9） |
| core / dir / vfs | 269 / 全绿 / 全绿 |
| pytest | **158 passed** |
| table 重放 | 175 pass / 0 fail / 12 known-space / 2 skip |
| hex 重放 | 30 pass / 0 fail / 1 skip |
| Oracle 残留进程 | 0 |

sync 的 9 个集成测试直接对应实测格：A1/A5/E5（update 拷贝+不删）、
A2/B6/C4（mirror 删孤儿）、C4（空源清空）、F3/H1c/H1d/X5（create-empty）、
H1a/G5/K4（visible 禁用 create-empty）、A7（无 load）、G6（半载 100）、
D2/F6（目标较新保留）。
