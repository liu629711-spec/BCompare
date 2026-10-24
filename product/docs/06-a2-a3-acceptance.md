# 06 — A-2 / A-3 交付与验收记录（2026-10-13）

> 本文是 A-2（M1 文本核心）、A-3（M3 只读文件夹比较）与 A-4/U1 探测的正式验收存档。
> 运行产物在 `product/verify/runs/`，全部为串行实测；旧资产（`verify/`、`clone/`、
> `report-*.md` 等）未被修改。

## 1. 验收命令与结果总表

| 验收 | 命令 | 结果 |
|---|---|---|
| A-1 单元/集成测试 | `python -m pytest product/verify/tests -q -p no:cacheprovider` | **157 passed** |
| A-2 cargo 测试 | `cargo test`（core + cli） | **191 passed**（core 171 + cli 20） |
| A-2 离线对拍（不调 Oracle） | `python product/cli/tools/offline_check.py` | 45/45 锚点，45/45 归一化 XML，29/30 布局 |
| A-2 官方 harness | `python -m harness.run_cli --install current --install reference --candidate reacmp --run-name A2-gate-serial-01` | **257 项 256 过**；candidate 45/45 锚点 + 29/30 布局 |
| A-3 cargo 测试 | `cargo test`（vfs + dir） | **107 passed**（第二轮后 78+29） |
| A-3 自检 | `python product/dir/tools/compare_fixtures.py` | **75/75**（observed 16/16） |
| A-3 串行 Oracle 门禁 | `python tools/_audit/a3-folder-gate.py A3-folder-gate-serial-04` | **75 = 66 过 + 9 已知分歧 + 0 失败；49/49 XML 与活体 BC 逐字节一致** |
| U1 探测 | `python product/verify/probes/u1_element_importance.py` | 结论见 §3 |

首轮门禁（`A3-folder-gate-serial-01`）的 21 项发现全部在第二轮闭环；过程
记录在 `A3-folder-gate-serial-01/REPORT.md`（发现 F1–F8）与
`A3-folder-gate-serial-04/REPORT.md`（终态）。

## 2. 产品状态（重要：区分产品与旧原型）

`reacmp`（`product/cli/target/release/reacmp.exe`）是**产品**（harness 中
`is_product=True`），不再与旧原型 `bcx.exe` 的数字混用。文本核心当前能力：

- 行切分/编码、Myers 线性空间对齐（含重复行前向优先）、XML + 6 种文本布局
- 45 锚点 status 全对拍；XML 归一化后 45/45 逐字节（`created=` 除外）
- `mixed-side-by-side` 是唯一已知布局差异（有案可查，未做特例硬编码）

文件夹引擎（`product/dir` + `product/vfs`）当前能力见
`product/dir/README.md` 与 `docs/EVIDENCE.md`（含 §9 第二轮附录）。

## 3. U1 定案（M2.1 完成）

活体 Oracle 两模式探测（9 个 token 类别 × 默认/ignore-unimportant）：
**除注释行与空白差异外，一切单类差异都判 `different` 且不被
`ignore-unimportant` 折叠**（指令/运算符/标识符/数字/字符串/关键字/大小写
全部重要；注释与空白 → `similar` → 折叠为 `same`）。"元素索引 6/9 强制重要"
的内部映射永远不可由 CLI 观察（永久 I 级），M2 实现以行为表为准。
完整表：`product/verify/probes/U1-FINDINGS.md`。

## 4. 已知分歧（显式列出，非失败）

1. `mixed-side-by-side`：候选行填满左栏时 BC 省略差异标记（触发条件未建模）。
2. BC **接受** `criteria version / owner / group / permissions /
   ignore-unimportant`（exit 0），引擎按"未探测即拒绝"——实现已被门禁产物解锁，
   列入 M2/M4 后续。
3. BC 文本版文件夹布局（side-by-side/summary）样本已归档，字节兼容未建模
   （引擎输出自带 `NOT byte-compatible` 声明）。

## 5. 基础设施变更（本轮）

- `tools/_audit/a3-folder-gate.py`：串行门禁驱动（行级比较 + cli_flag 映射 + 已知分歧分类）。
- `product/cli/tools/offline_check.py`：A-2 离线对拍（不调 BCompare）。
- `product/verify/probes/`：A-4 落位（U1 探针 + 结论）。
- `product/verify/harness/candidate.py`：`reacmp` 从"声明但缺席"转为"已建成"；
  两个前提失效的测试按原意图改写（`test_runner.py`，改动有注释说明）。
- `make_cases.py` 校验器新增 check 4：夹具清单重建时逐例核对门禁产物，
  防止期望漂移。`A3-folder-gate-serial-04/` 是承重证据目录，不可删除。

## 6. 下一步

- **M2 重要性引擎**（B-1，已无阻塞）：U1 已定案，按 `U1-FINDINGS.md` 行为表 +
  `extracted/bcfileformats-spec.json` 的 4 种格式规则实现分词器与逐元素重要性。
- 五个已解锁 criteria（version/owner/group/permissions/ignore-unimportant）
  的实现（自带夹具与对拍）。
- `mixed-side-by-side` 触发条件建模（可选）。（**2026-10-14 已完成，M5.1**：
  真实规则是块首行才画槽位字形，见 `07-m2-importance.md` M5.1 精化与
  `verify/layouts/README.md` 补记。）
- M4 CLI/脚本子集（B-2）在 M2 之后。
