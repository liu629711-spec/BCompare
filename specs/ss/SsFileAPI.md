# SsFileAPI.pas 规格（第一遍·架构级）

> 逆向来源：语料精读（135 函数；巨头 4 个 + 中层 20+ 已定性）。地址段 140507xxx–14050cxxx。日期 2026-10-13。
> 单元身份：**BC 文件系统 API 层**——Win32 文件/进程/Shell 封装，SsPersistent 原子保存的底层。

## 1. 核心函数

### 1.1 进程执行 — `FUN_14050c830(cmdline, workdir, ..., bool, ...)`（2264B）
CreateProcess 完整封装：`_STARTUPINFOW`/`_SECURITY_ATTRIBUTES`/双 `_OVERLAPPED` + 双 1024B 缓冲（stdout/stderr 管道）；完成端口式异步读取。用于外部工具调用（diff 助手、命令行比较）。

### 1.2 文件读入 — `FUN_14050b120(...)`（1337B）
打开+读取（64B 栈缓冲段、HANDLE local_28、wchar 路径缓冲）→ 疑为**BOM 感知的文本读入** [二遍确认编码逻辑，与 SsLineParse 级联呼应]。

### 1.3 URL 下载 — `FUN_140509fb0(out, url, bool)`（1295B）
`pszUrl` + `WCHAR[261]`（MAX_PATH）→ WinINet/URLDownloadToFileW 族。

### 1.4 Shell 文件操作 — `FUN_140508ca0(..., SHFILEOPSTRUCTW*)`（1183B）
`SHFileOperationW` 封装（复制/删除/移动目录树，进度 UI 可控）。

### 1.5 原子替换 — `FUN_140509bb0(target, source, backup) → bool`（248B）
**ReplaceFileW(replaced=target, replacement=source, backup, flags=2 REPLACEFILE_WRITE_THROUGH, nil, nil)**；失败保留 GetLastError。**SsPersistent 1406852f0 的 .tmp→目标 换名即此函数**——.bak 由 ReplaceFileW 原子生成。路径经 FUN_140509d50 规整到 0x104（260）缓冲。

### 1.6 其他已定性
- 140509ac0 = **MoveFileW** 封装（长度是 0x104 缓冲，移动失败语义）。
- 1405097a0 = 文件删除（DeleteFile 族，注释中 SetLastError 保护）。
- 140507cd0/140507f80 = 文件打开/时间戳（FILETIME + FIND_DATA）；14050bd60 = 路径合法化；14050ab60 = 路径规范化（FUN_1404ff440 → 无扩展名保持）；1405092a0 = 目录遍历（16KB 栈缓冲 + 通配）。
- 14050c3a0 = **版本字符串组装**（app 对象 FUN_1403f5fb0 + FUN_14050c320 + IntToStr → "%s"，格式串 @14050c448）——SsPersistent XML 头注释 "%s" 的来源。
- 140507690 = FileExists；140509d50 = 路径→260 缓冲；140503a30 等属 SsRegistry 域（见下）。

## 2. 可测试锚点

1. 原子保存链：.tmp 写入 → ReplaceFileW(写到目标, 备份=.bak, WRITE_THROUGH)（SsPersistent 集成锚点）。
2. MoveFileW/DeleteFile 失败时 SetLastError 透传。
3. 版本串格式（"%s" @14050c448）→ XML 头 `Produced by <version> from Scooter Software`。

## 3. 未解之谜

1. [?] 14050b120 读取器的编码级联细节（是否复用 SsLineParse 检测）。
2. [?] 1405092a0 遍历的排序/过滤规则。
3. [?] 中层函数（≥300B）逐个角色：14050ba20/140509e30/140509610/140508330/1405084b0/1405087c0/1405081d0/140507750/14050af20/14050a5d0/14050a780/14050b8b0/14050c580/14050adf0 等（全量见 inventory/SsFileAPI.tsv）。
