# 01 — Device bootstrap (换设备开发引导)

> 本仓库是**公开**仓库，故意不含以下三类大件（版权/体积）。换设备后按本文件
> 步骤即可 100% 恢复开发环境。

## 1. 克隆与构建

```bat
git clone https://github.com/liu629711-spec/BCompare.git D:\Rea
cd D:\Rea
:: Rust 引擎
cd product\core && cargo build --release && cargo test --release
cd ..\cli && cargo test --release
:: WPF GUI（出货面）
cd ..\gui\WpfHost && dotnet build -c Release && dotnet build -c Debug
:: 冒烟：双击 LiuCompare.cmd 或 LiuCompare.cmd fileA fileB
```

## 2. 活体门禁的 Python 环境（解释器有硬性要求）

- **必须** `C:/Python314/python.exe`（3.13 托管版没有 pywinauto/keyboard）：
  `pip install pywinauto keyboard numpy`
- 离线门禁任意 python3 + 标准库即可。
- BC Oracle 探针（tools/live-*.py）另需 `pefile`。

## 3. 未提交的第三方字节 → 重建/就位（版权红线，永不入库）

清单= `verify/FIXTURE-MANIFEST.json`（路径+sha256，共 62 项），恢复脚本:

```bat
python tools/fetch_fixtures.py            :: 从本机参考安装拷贝并逐文件校验
python tools/fetch_fixtures.py --verify  :: 只校验在位性
:: 安装不在默认位置时：
python tools/fetch_fixtures.py --source BCompare-official="E:\path\BCompare.exe"
```

覆盖：`verify/ver/v-*.exe`、`product/ver/tests/fixtures/V*` 里的 BCompare.exe
50MB 拷贝、BComp.com 拷贝/等长补丁变体（`v-w*`/`W*`，补丁夹具由
`product/verify/probes/m112b_ver_fields_probe.py` 逻辑可再生，但该探针**跑一次
就会打开 BC 实例**——纯引擎开发不需要它，重放 harness 全量重跑时才需）、
cmd/notepad 系统拷贝。

同样未入库、按需就位：
- `tools/ghidra/ghidra_11.2.1.zip` → https://github.com/NationalSecurityAgency/ghidra/releases
- `help/`（BC 随附帮助，仅供本地 RE 查阅，勿再分发）
- `extracted/resources`、`extracted/rcdata`（安装内二进制资源原样抽取）
- `extracted/pseudocode`（Ghidra 反编译 .c 树，衍生代码；重新导出=
  对本地安装跑 tools/ghidra-scripts）
- `ghidra-project/`、`product/verify/runs/`（会话工程/历史归档，可再生但
  归档重放需要本地保留）
- `BCompare.exe`/`BComp.com` 参考安装本身不在仓库里：harness 在
  `D:\BCompare\BCompare` 与 `D:\bc-official\app` 发现它
  （product/verify/harness/installs.py）；活体门禁需要 English 5.2.6 安装
  （中文安装几何/locale 漂移=在案差异，docs/17/18）。

## 4. 全套门禁基线（2026-10-24，push 前实测）

| 门禁 | 期望 |
|---|---|
| tools/menu-offline-check.py | 845/410/290 全绿 |
| tools/dispatch-check.py | 13 绿 |
| C:/Python314/python.exe tools/gui-self-check.py spec | 12 golden 逐字节 |
| cargo test core | 278+5+1 过 |
| cargo test cli | 146+206+118 过 |
| 活体 uia-*（含新 uia-toolbar-check 三模） | 需活体桌面（OpenInputDesktop=Default）+BCompare 单实例串行 |

## 5. 阅读顺序（开工前）

1. `.workbuddy/memory/MEMORY.md` + 最近一日日志（当日状态快照）
2. `product/docs/20-product-direction.md`（方向权威）
3. `product/docs/21-mvp-gui-closure.md`（当前里程碑施工顺序）
4. `product/docs/19-gui-replication-spec.md` §6.x（实测行为规格）
5. `product/docs/12-maintenance-regression.md`（门禁台账）
