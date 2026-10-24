# 01 — Device bootstrap (换设备开发引导)

> 本仓库是**公开**仓库，故意不含以下三类大件（版权/体积）。换设备后按本文件
> 步骤即可 100% 恢复开发环境。2026-10-24 按首次真实换机跑改写过：新设备是
> 空盘，§1 是一次性从零准备清单，不是"已就位后的验证清单"。

## 1. 全新设备一次性准备 + 克隆构建

```bat
:: (a) 先装工具链：Git、Rust(rustup + MSVC 链)、.NET 8 SDK、VS Build Tools(C++)
:: (b) Python 3.14 装到固定路径 C:\Python314（安装包选 Custom installation
::     location 指到 C:\Python314；若已装到 %LOCALAPPDATA%\Programs\Python\
::     Python314，把整个 Python314 目录复制到 C:\Python314 即可，不要保留
::     两份）。活体门禁的纪律路径= C:/Python314/python.exe，全设备统一，
::     不要每台记一个不同路径（3.13 托管版没有 pywinauto/keyboard）。
    C:\Python314\python.exe -m pip install pywinauto keyboard numpy pefile
:: (c) Beyond Compare **5.2.6 English** 装到 D:\BCompare\BCompare（正版许可）。
::     必须英文原版（中文 repack=在案陷阱，docs/2/17/18 的 locale 差异），
::     harness 按该路径发现安装（product/verify/harness/installs.py）。
::     注意：夹具按 5.2.6.32774 的字节 sha256 钉死——装别的版本 fetch 会拒。
git clone https://github.com/liu629711-spec/BCompare.git D:\Rea
cd D:\Rea
:: (d) 恢复未入库的第三方夹具（逐文件 sha256 校验，需 (c) 已就位）
    C:\Python314\python.exe tools\fetch_fixtures.py
::     安装不在默认位置时：
::     ... fetch_fixtures.py --source BCompare-5.2.6="E:\path\BCompare.exe"
:: (e) Rust 引擎
cd product\core    && cargo build --release && cargo test --release
cd ..\cli          && cargo test --release
:: (f) WPF GUI（出货面）
cd ..\gui\WpfHost  && dotnet build -c Release && dotnet build -c Debug
:: 冒烟：双击 LiuCompare.cmd，或 LiuCompare.cmd fileA fileB
```

## 1b. ZCode 持久记忆（已随仓库入库，克隆即得）

ZCode 记忆文件本体在用户目录下（不在 git 仓库里），换设备拷不了——所以
2026-10-24 已把它们**导出进仓库**：`memory-export/`（28 个 .md，经密钥扫描
干净）。`.workbuddy/memory/` 每日日志同样在仓库里。

新设备就位命令（克隆后跑一次即可，幂等）：

```bat
C:\Python314\python.exe tools\install_memory.py
:: 目标位置自动解析：C:\Users\<user>\.zcode\cli\memories\projects\rea-<key>\memory\
:: （本仓库若放 D:\Rea，key 与旧设备一致；脚本找不到现有键目录时按工作区
::   路径哈希新建同名规则目录并打印落点）
```

跑完**重启该设备的 ZCode 会话**记忆才会自动加载。跳过的后果：不影响开工
（docs 19/20/21 + .workbuddy 日志 + 本节是权威事实源），但跨会话纪律/在案
教训要重新积累。旧设备上的原始记忆目录不用带走——仓库里就是最新导出。

## 2. 活体门禁的 Python 环境（解释器有硬性要求）

- **必须** `C:/Python314/python.exe`（路径纪律见 §1(b)）：
  `pip install pywinauto keyboard numpy`
- 离线门禁任意 python3 + 标准库即可。
- BC Oracle 探针（tools/live-*.py）另需 `pefile`。

## 3. 未提交的第三方字节 → 重建/就位（版权红线，永不入库）

清单= `verify/FIXTURE-MANIFEST.json`（路径+sha256，共 82 项），恢复脚本
`tools/fetch_fixtures.py`（§1(d)）。覆盖：`verify/ver/v-*.exe`、
`product/ver/tests/fixtures/V*` 里的 BCompare.exe 50MB 拷贝、BComp.com
等长补丁变体、cmd/notepad 系统拷贝。

**补丁变体（`v-w*`/`W*` 共 20 个）不是纯拷贝**：它们是探针把 BComp.com 的
VS_VERSION_INFO 字符串原位改写的产物（`product/verify/probes/
m112b_ver_fields_probe.py` 的 build()，会开一次 BC 实例）。两条恢复路：
① 最省事=旧设备上用私有移动盘整目录带 `verify/ver/` +
`product/ver/tests/fixtures/` 过去（含全部 .txt 金标准）；② 新机跑 m112b
探针再生（顺序/命名一致，hash 自动对上）。纯引擎开发**不需要**这些夹具，
只有重放 harness 全量重跑时才需要。

同样未入库、按需就位：
- `tools/ghidra/ghidra_11.2.1.zip` → https://github.com/NationalSecurityAgency/ghidra/releases
- `help/`（BC 随附帮助，仅供本地 RE 查阅，勿再分发）
- `extracted/resources`、`extracted/rcdata`（安装内二进制资源原样抽取）
- `extracted/pseudocode`（Ghidra 反编译 .c 树，衍生代码；重新导出=对本地
  安装跑 tools/ghidra-scripts）
- `ghidra-project/`(1.2G)、`product/verify/runs/`(550M 历史归档)：会话状态/
  考古用，RE 继续深挖或全量重放才从旧盘迁移；日常开发不需要
- 第二套 BC 安装（官方版，`D:\bc-official\app`）仅重放 harness 的官方对照
  用到，缺了不挡门禁

## 4. 全套门禁基线（2026-10-24，push 前本机实测）

| 门禁 | 期望 |
|---|---|
| tools/menu-offline-check.py | 845/410/290 全绿 |
| tools/dispatch-check.py | 13 绿 |
| C:/Python314/python.exe tools/gui-self-check.py product/gui/spec/menu-spec.json | 12 golden 逐字节 |
| cargo test core | 278+5+1 过 |
| cargo test cli | 146+206+118 过 |
| 活体 uia-*（含 uia-toolbar-check 三模） | 需活体桌面（OpenInputDesktop=Default，屏保锁定则像素全白）+ BCompare 单实例串行 |

活体桌面判定一行命令：
`C:/Python314/python.exe -c "import ctypes;h=ctypes.windll.user32.OpenInputDesktop(0,False,1);b=ctypes.create_unicode_buffer(256);n=ctypes.c_ulong();ctypes.windll.user32.GetUserObjectInformationW(h,2,b,256,ctypes.byref(n));print(b.value)"`

## 5. 阅读顺序（开工前）

1. `.workbuddy/memory/MEMORY.md` + 最近一日日志（当日状态快照）
2. `product/docs/20-product-direction.md`（方向权威）
3. `product/docs/21-mvp-gui-closure.md`（当前里程碑施工顺序）
4. `product/docs/19-gui-replication-spec.md` §6.x（实测行为规格）
5. `product/docs/12-maintenance-regression.md`（门禁台账）
