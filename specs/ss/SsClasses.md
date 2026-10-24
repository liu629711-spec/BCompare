# SsClasses.pas 规格（二遍完成版）

> 逆向来源：Ghidra 反编译语料 `extracted/pseudocode/`（本单元 266 函数全部登记：60 个非平凡精读 + ~206 个小函数分类）。
> 原始源码 `C:\BCBuild\BCompare\Source\Ss\SsClasses.pas`（断言内嵌路径确认）。
> 单元身份：Ss 地基根单元——字符集、区间属性图、缓冲流、泛型容器、流序列化、排序。
> 日期：2026-10-13。

## 1. 对象总览（六大家族）

| 家族 | 身份证据 | 核心成员 |
|---|---|---|
| TSsCharSet | TypeInfo `TSsCharSet`（tkRecord, elSize=0x18）@140521c70 | 位图+字符表记录、四个全局默认集 |
| 区间属性图 | 基类 ctor 14052b7c0 | 带值区间图 / 二级映射 |
| TSsBufferedStream | ctor 140526850 + Read/Write/Seek/Flush 全套 | 1024B 缓冲的流包装 |
| 泛型容器 | TypeInfo TArray\<System.Integer\>/TSsBytes；TMethod 16B 记录 | int 数组代数、事件表、双向链表、MRU、线程队列 |
| 流序列化 | 读/写配对（u8/u16-escape 长度前缀） | 字符串与定宽数值 |
| 排序/杂项 | Hoare 快排抽象+整型特化 | CharToDigit、右对齐拷贝、哈希 |

**误归属澄清**：140f56xxx/140f58xxx（11 个函数，inventory 标 boundary-guess/edge-nearest）实为 **TDirSession 邻接单元**的泛型实例化（140f571b8 TypeInfo 名为 `:TDirSession.:1`）；140dc3a90 属 diff 引擎邻区（ti @140dbfa00）。它们是同一泛型的其他实例，语义一并记录在对应小节。

## 2. TSsCharSet（字符集，24 字节 record）

```
TSsCharSet = record          // TypeInfo@140521c70, size 24
  chars : TWideCharDynArray; // +0x00 排序 ushort 数组（TWideCharDynArray ti@1405208b0）
  bitmap: array[0..15] of Byte; // +0x08 ASCII 0..127 每字符 1 位（128 bit = 16 字节）
end;
```

- **成员判定** `FUN_1405279a0(cs, ch)`：ch<0x80 → 位图 O(1)；ch≥0x80 → `FUN_1405271e0`（chars 二分查找，返回命中=1/插入点 idx）。
- **插入** `FUN_140527070(cs, ch)`：二分得插入点 → SetLength(n+1) → 尾段 memmove → 写入；若 ch<0x80 同步置位图位。
- **位图重建** `FUN_140527120(cs)`：清 +8/+0x10 两个 qword，遍历 chars 置位（chars→bitmap 单向同步）。
- **集合代数**（全部要求输入排序；位图分别 OR / AND / **AND-NOT**，AND-NOT 由 RTL `FUN_14000f9c0(dst,src,n)` 完成 = 逐字节 `dst &= ~src`）：
  - 并集 `FUN_1405275c0`、交集 `FUN_140527ab0`、差集 `FUN_140527d40`（out.bitmap = a.bitmap AND NOT b.bitmap）
- **IsSubset** `FUN_1405279f0(a,b)`：len(a)>len(b) 短路假；逐元素 advance 扫 b；任一失配即假。
- **比较/相等** `FUN_140527740`（首个差异 code-unit 的无符号差，相等比长度）、`FUN_1405277c0`（长度相等+逐位相等）。
- **构建器**：
  - `FUN_140527830(out, ch)` 单字符集：chars=[ch]；ch<0x80 时位图由 RTL `FUN_14000f790(&local, ch&0xff, 0x10)` 构造 [?]（伪代码形似 FillChar，须按"置位第 ch 位"理解——见谜团 1）。
  - `FUN_140527430(out, ranges, n)` **区间表→集**：`TSsIntegerRangeDynArray`（ti@140520e30，元素 8B {i32 first; i32 count}）逐区间展开，末尾 RebuildBitmap。
  - `FUN_1405278d0(out, bitmapPtr)` **16 字节位图→集**：与全零常量（14052798c）比较，非零才展开 128 位；顺带拷贝源前 16 字节为位图。
  - `FUN_140527510(out, intArr)` Int32 数组截断为 WideChar 集 + 重建位图。
- **补集** `FUN_140527c60(out, cs)`：chars = 0..0xFFFF 中不在 cs 的全部（0x10000−n 个）；位图 = 0xFF×16 常量（140527d0c）AND-NOT cs.bitmap = **ASCII 补位图**。chars 与位图基准不一致（chars 含全部 BMP、位图只反 ASCII）——按实现记录。
- **大小写闭包** `FUN_140527320(cs)`：复制 chars，对每个 c 若 `FUN_1405257f0(c)`（大写）/`FUN_140525810(c)`（小写）≠ c 则 Insert——**集合扩展为大小写不敏感**。

### 全局默认字符集（懒初始化 + 全局锁）

单元 `initialization`（FUN_14052adc0）把 4 个全局槽清零（源 = 16 零字节 @14052af4c，即空集）：

| 槽 | 懒构建 | 内容（PE 直读证实） | getter |
|---|---|---|---|
| DAT_141fe1f08 | FUN_140528010（表@141d0ea9c，**count=0**） | **恒空集** | — |
| DAT_141fe1f20 | FUN_140528040（表@141d0eaac ×34） | **Unicode 数字**：0-9 + 34 个 Nd 块（0660/06F0/07C0/0966/09E6/0A66…ABF0，每块 10 字符） | FUN_140528040 |
| DAT_141fe1f38 | FUN_140528070（位图@1405281b0） | **行内空白 {TAB(09), FF(0C), SPACE(20)}**（LF/CR 不算行内空白） | FUN_140528070 |
| DAT_141fe1f50 | FUN_1405281c0（表@141d0ec1c ×37） | **默认标识符** `[0-9A-Za-z_]` + Unicode 数字 | FUN_1405281c0 |

- 通用懒构建 `FUN_140527ef0(out, slot, ranges, count)`：slot 空 → 全局锁（DAT_141fe1f00，vtable+0=Enter/+8=Leave）内 double-checked 构建；`FUN_140527fe0` = Leave。
- 消费方（SsLineParse 域）：141002d30/141002f50/141006a40 直接调 FromBitmap/字符集构建。
- 静态快查表（与 #3 同内容，性能双轨）：`FUN_14052a120(ch)` = ch<0x100 时查表@14052a13c（{09,0C,20}）。
- `FUN_14052a0f0(x)` = "非 X 且非空白 → 1" 组合分类器（X = FUN_14052a160：byte∈5..9 ∨ '\r' ∨ '\x10' [?]）。

## 3. 区间属性图家族

- **基类构造** `FUN_14052b7c0`：+0x28 = TQueue\<Pointer\> TypeInfo（PTR_140524de0，`TQueue<System.Pointer>.arrayOf`）；+0x30 = self；+0x38/+0x40 = 默认值/相等回调 `FUN_14052bf50`/`FUN_14052bf70`（= 一遍规格的 vtable+0/+8 虚值协议的默认实现）。
- **取值** `FUN_14052b1a0(map, pos)`：`FUN_14052bcc0` 定位 → 未命中返回 vtable+0 默认值；命中返回 12B 记录的值。
- **从枚举器填充** `FUN_14052b890`（枚举器协议：vtable+0 GetEnumerator / +8 MoveNext / +0 GetCurrent）与 `FUN_14052b9e0`（列表协议：+0x20 Get(out)、+0x20 MoveNext、+0x30 Current），逐项 `FUN_14052bb30` 添加。
- **带容量变体** `FUN_140526440`：基类在 14026fxxx（跨单元）；SetCapacity 0x100 → +0x20 = cap−1、+0x28 = cap×12 —— 12B 记录、2 的幂掩码结构 [?]。
- **二级映射**（桶→值列表）：`FUN_140526560` AddOrSet——vtable+8 Find(key,&桶,&值idx)，未命中 vtable+0x10 插入，命中直接写桶内 16B 记录的值槽；`FUN_140528480` 取值同路径。
- **锁+数据 owner 模板** {+8 锁对象（vtable+0 Enter/+8 Leave），+0x10 数据}：线程队列（Push 140528f80 / TryPop 140528e90，空时 out=0 返回假）与 {锁+区间图}（ctor 140528d70，+0x10 = 新建基类区间图）两个实例。
- 子类 ctor `FUN_14052b6a0`：+8 = 关联对象、+0x10 = −1（无效索引初值）。

## 4. TSsBufferedStream（1024 字节缓冲流）

```
+0x08   byte buf[0x400]      读写共用缓冲
+0x408  i32 bufPos           缓冲内游标
+0x40c  i32 bufLen           有效数据高位水位
+0x410  byte mode            1 = 写缓冲挂起（脏）
+0x411  byte ownsStream      析构时是否 Free 底层流
+0x418  stream               底层流对象
+0x420  i64 pos              逻辑位置
+0x428  i64 size             大小水印（GetSize 报告值）
```

- **构造** `FUN_140526850`：+0x428 = 底层流 vtable+0x18（GetSize）；子类 ctor `FUN_1405281f0`（基初始化在 FUN_140135930，140135xxx = 流基单元）。
- **Read** `FUN_1405269b0(buf, count)`：若 mode=1（写脏）→ 先冲刷（WriteBuffer + pos+=bufLen + 重置）；缓冲空时 pos+=bufLen、底层 vtable+0x30 Read(buf,0x400) 回填，0 即 EOF；Move 拷出 min(count, bufLen−bufPos)。
- **Write** `FUN_140526bc0(buf, count)`：若 mode=0 → 切写模式（pos+=bufPos、Seek、清零）；填满 0x400 即 `FUN_140526cd0` 冲刷；bufPos>bufLen 时抬 bufLen，pos+bufPos>size 时抬 size。
- **Seek** `FUN_140526ae0(pos, origin)`：origin 1=当前位置（+pos+bufPos）、2=自尾（size−pos）、否则绝对；夹取 [0,size]；目标在缓冲窗口内**只移 bufPos（零 I/O）**，否则冲刷+真 Seek+清缓冲。
- **Flush** `FUN_140526cd0`：WriteBuffer(buf, bufLen)；pos+=bufLen；清零计数。
- **SetSize** `FUN_140526d30`：底层 Seek(v)；pos=size=v。
- **析构** `FUN_140526930`：写脏则冲刷；ownsStream 则 Free 底层流。
- 底层流 vtable 槽位（跨单元约定）：+0x18 GetSize、+0x30 Read；helper：FUN_1401326e0=Seek/SetPos、FUN_140133fa0=ReadBuffer、FUN_1401346a0=WriteBuffer。
- Read/Write/Seek 无直接调用者（虚分派使用）。

## 5. 泛型容器家族

### 5.1 有序 int 数组代数（TArray\<System.Integer\>，ti@140006b80）
- 并集 `FUN_1405285e0`：双指针归并，**跨数组相等折叠一次、各自内部重复保留**（多重集并）。
- 差集 `FUN_1405287c0`：a − b（advance 扫 b）。
- 连接 `FUN_140526d90`（TSsBytes ti@140521ba8 = 泛型 Concat：nil 处理 + SetLength(a+b) + 两次 Move）。
- 插入 `FUN_140529b20(&arr, idx, v)`、删除 `FUN_140529a00(&arr, idx)`、**排序去重前插** `FUN_140528550`（find→Insert，即有序 AddIfAbsent）、Pop `FUN_140529ac0`。
- 对象形态 int 列表 {+8 count, +0x10 arr}：AddInt `FUN_140528970`。
- 排序：抽象快排 `FUN_14052a1a0`（ctx：+0x20 Swap 方法对、+0x30 Compare 方法对、+0x80 用户上下文；Hoare 分区、pivot=mid、较大半尾循环消除）；入口 `FUN_14052a320(lo,hi,cmp,swp)`；整型特化 `FUN_140529ba0`（升序、直接比较字段 +0x30 的数组）、包装 `FUN_140529c90`。
- 容量增长 `FUN_14052a190(count, minCap)` = **max(2×count, minCap)**。

### 5.2 多播事件表（泛型，TMethod 16B 记录 {code, data}）
- 断言：code 高 48 位非零（非小整数/非空），原始行 **SsClasses.pas 0xad2(2770)**×2、**0xde0(3552)**。
- Add：`FUN_140529040`（本单元实例）、`FUN_140dc3a90`（diff 邻区实例）、`FUN_140f56cb0`（Dir 邻区实例）——同一泛型三编译。
- Remove（按方法恒等线性查找 + 左移）：`FUN_1405291d0`/`FUN_140f56e50`。
- Notify(a,b)：`FUN_140f56de0`/`FUN_140529170` 遍历调 `code(data, a, b)`，**插入序**。
- 相等 `FUN_14052a6a0`：code+data 双 qword 全等。
- {+0 Count; +8 ?; +0x10 记录数组}。

### 5.3 双向链表（owner {+8 count, +0x10 first, +0x18 last}，node 含 prev/next/data@+0x10）
AddFirst 140528cd0、AddLast(node) 140528af0 / AddLast(data) 140528a20、unlink 140528d20/140528ba0、RemoveFirst 140528c90 / RemoveLast 140528cb0、Clear 140528b20（FreeMem 逐节点）、**Merge** 140528bf0（dst 尾接 src 链、count 相加、src 清空；IsEmpty 140528be0）、遍历复制 140528ac0。

### 5.4 MRU 列表（抽象 vtable 协议）
槽位：+0x18 Get(out,i)、+0x28 Count、+0x98 Delete(i)、+0xb0 IndexOf、+0xC8 Insert(0,item)、+0xF8 Move(i,0)。
- `FUN_140529800(self, item, cur)`：IndexOf→有则 Move(i,0)/无则 Insert(0,item)；**裁剪到 ≤9**（上限常量 DAT_141d0e618=9）；然后 Get(0)≠cur 则 Put(0,cur)。
- `FUN_1405298c0(self)`：先裁剪，再从尾向头 IndexOf≠i 即删——**重复项保留最旧下标最小者**（配合 MoveToFront = 最近使用置顶）。

### 5.5 线程安全队列 {+8 lock, +0x10 deque}
Push `FUN_140087760(deque+8, &v)`、TryPop `FUN_140087810(deque+8, 5, 0, &out)`（mode 5 = 弹出语义 [?]；count 在 deque+0x20）。锁协议与全局锁同款。

## 6. 流序列化（读/写配对）

字符串长度字段 = `*(u32*)(str-4)`（x64 字符串头 Int64 长度的低 32 位）[确切 string 类型 ?]。

| 格式 | 写 | 读 |
|---|---|---|
| u8 长度（≤255，断言 **SsClasses.pas 0x120b(4619)**） | 14052ab00 | 14052a460 |
| u16 位15逃逸（≥0x8000 → 0x8000\|low15 再写 high15，30 位） | 14052ac80 | 14052a540 |
| 仅内容 | 14052a9a0（带长）/ 14052aa60 | — |
| UTF-8 变体（0xfde9=CP_UTF8 转码后走上表） | 14052ac10(u8) / 14052ad10(u16esc) / 14052a9e0 | — |
| Byte | 14052a960 / 14052a980 | — |
| Word16 | 14052ada0 | — |
| Int32 | 14052ad80 / 14052aaa0 | — |
| Int64 | 14052aae0 / 14052aac0 | — |

读侧包装（返回 string）：14052a5e0（u16esc）、14052a4d0（u8）。

## 7. 杂项机制

- **流复制+进度** `FUN_14052a720(dst, src, callbacks{fn,ctx})`：GetSize → 64KB（0x10000）ReadBuffer/WriteBuffer 循环；每块后回调 `(ctx, done, total, &cancel)`，cancel 置位 → 构造消息（LAB_140525790 [文本?]）抛异常。消费方：1405091d0、140e10d50。
- **按分隔符拆分入列表** `FUN_1405293e0(list, text, delim)`：BeginUpdate(vtable 槽 14012e3c0 协议) → Clear(+0x90) → Pos 循环（FUN_140016660 查找 / FUN_1400163a0 子串）→ Add(+0x78) → EndUpdate。多字符分隔符；1 基索引。
- **注释截断 Add** `FUN_140529270(self, name, x)`：标志 +0x48 开时取注释字符（+0x30 的 WideChar）→ Pos → 截断后走 vtable+0x70；否则基 Add（FUN_140131ee0）。
- **大小写可覆盖查找** `FUN_140529350(self, name)`→idx：标志 +0x48 关 → 基查找 FUN_1401318e0；开 → 再入保护（+0x78 置位）下走 vtable+0x140 比较，未中返回 −1。
- **逐行装载** `FUN_140529620(self, src)`：BeginUpdate/Clear → reader（SsText 域，类 ref PTR_14051d938，行记录 `TSsLine` ti@14051d648 size 0x10）ReadLine 循环 Add；reader+0x21 错误标志 → 抛异常类（VMT @1405209c0，名称 [?]）→ EndUpdate。
- **字符→数字** `FUN_140529f30(ch)`：ch<0x100 且表@140529f7c 置位（表 = 精确 0-9），断言 **SsClasses.pas 0x1079(4217)**，返回 ch−0x30。
- **右对齐尾拷贝** `FUN_140526f70(src, dst, count)`：Move(src → dst+max(0,count−srcLen), min(count,srcLen))——"取源的最后 count 字节写入 dst 尾部"（140527000 的底层）。
- **哈希** `FUN_1405265d0(self, x)`：`((x ^ x>>4) * 0x27d4eb2d) ^ (x>>15) & *(u32*)(self+0x20)`（桶掩码 = 容量−1）。
- **加锁单例赋值** `FUN_14052a090(slot, obj)`：锁内置换，重复者 Free。
- **字符串交换** `FUN_14052a8e0(a,b)`（temp 交换）；指针交换 14052a0c0；双 int 记录比较 140528310。
- **锁内数据队列/列表杂项**：14052bb30（入队包装）等。

## 8. TRIVIAL 登记（代表样本；全量见 inventory）

- 空体/纯返回：1405267f0, 14052af60, 14052b990, 14052b5b0, 1405283f0, 140529000, 140528c60, 1405285b0, 140528160, 140527400, 14052b640, 1405263b0, 140528920, 1405299c0, 140529730, 140529560, 140526600, 14052bc00, 14052bb00, 14052bae0, 14052ad60, 14052bf50, 140f58ea0, 14052afb0, 14052a650, 14052a3e0, 14052a3b0, 14052a380, 14052a430, 14052a400, 140528750, 14052b780（读 +8/+0x18 嵌套长度）, 14052bc80, 1405275a0（dynarr 长度）, 1405275b0, 1405262e0（首元素）, 14052a670, 14052bbb0/bb80/bb50, 1405299e0
- 析构样板（BeforeDestruction+FreeInstance）：1405289d0, 140528e40, 14052b5f0, 140526930(见 §4)
- WriteBuffer 定宽：14052a960/980(1B) 14052ada0(2B) 14052ad80/aaa0(4B) 14052aae0/aac0(8B)
- 比较运算六件套（返回布尔）：140528330(==0) 140528350(>0) 140528370(≥0) 140528390(<0) 1405283b0(≤0) 1405283d0(≠0)
- 链表包装：140528c90(RemoveFirst) 140528cb0(RemoveLast) 140528b70(条件 unlink)
- 其他：140528480（二级映射取值）、14052ad10/ac10/a9e0（UTF-8 写）、14052a5e0/4d0（读串包装）、140526d30（SetSize）、140528f50、140529780（按值删除 [?]）、1405295a0（工厂+虚添加 [?]）、140526510（键变换设置 [?]）、140526e80（位置插入 [?]）、140529a70（逆序遍历 [?]）、14052a6d0（位标志置/清）、140529f10/a0d0/93c0/…（未逐一定性的 <60B 尾部，见 inventory）

## 8.5 Oracle 校准：重要性判定实测（2026-10-13，verify/golden）

| 输入对 | .txt 结果 | .c 结果 |
|---|---|---|
| 大小写（标识符/字符串） | **similar** | **different** |
| 空白（前导/尾随/内嵌、tab↔空格） | similar | similar |
| 数字/操作符/指令/关键字改动 | different（无语法→全文重要） | different |
| **注释内容改动** | — | **similar**（注释非重要元素） |

**结论**：重要性由**文件格式语法**决定（.c 走 BCFILEFORMATS 元素表：注释 similar、标识符/字符串/数字/操作符/指令 different）；.txt 无语法 → 仅空白/大小写不重要。空白不重要是**跨语法共性**（实测 .txt 与 .c 一致）。

## 9. 可测试行为锚点

1. 默认空白集 = {TAB, FF, SPACE}：LF/CR/CRCRLF 不是行内空白（分词/重要性判定依赖）。
2. 默认标识符集 = [0-9A-Za-z_] ∪ Unicode Nd；数字集 = Unicode Nd（34 块）。
3. CharToDigit：仅 0-9 通过断言，返回 ch−0x30；非数字 → Assertion failure（行 4217）。
4. IsInlineWhitespace 静态表与全局 #3 位图完全一致（{09,0C,20}）。
5. 字符集插入：ASCII 字符同步置位图；≥0x80 只进 chars。补集位图 = 0xFF AND NOT 原位图。
6. 差集位图 = a AND NOT b（逐字节 AND-NOT）；并/交对应 OR/AND。
7. IsSubset：长度短路 + 线性归并扫描。
8. 缓冲流：读→写切换先冲刷；窗口内 Seek 零 I/O；soFromEnd 基于大小水印；Write 抬高 size 水位。
9. 字符串序列化往返：u8（≤255，越界断言行 4619）；u16 位15逃逸 = 30 位长度；UTF-8 写入走 0xfde9 转码。
10. MRU：容量 9；命中移顶；去重保最旧（IndexOf≠i 即删）。
11. 事件表 Notify 按插入序；Remove 按 {code,data} 恒等。
12. 容量增长 = max(2n, min)；哈希 = ((x^(x>>4))·0x27d4eb2d)^(x>>15) & mask。
13. 流复制块 64KB；取消回调置位即抛。
14. 快排：pivot=mid、Hoare 分区、不稳定（相等元素次序可变）。
15. 拆分：多字符分隔符、Pos 逐段、1 基；空文本产出单空段路径 [?]。
16. 泛型并集语义：跨数组相等折叠、组内重复保留（多重集并）。

## 10. 未解之谜

1. ~~单字符集构建 140527830 的位图初始化~~ **已解决（2026-10-13，REA 汇编+helper 反编译）**：RTL `FUN_14000f790(dst, index, size)` = **SetBit**——清零 size 字节后 `dst[index>>3] = 1<<(index&7)`（越界/负数只清零）。故 140527830 = 置第 ch 位，语义确定。
2. ~~全局 #1（恒空字符集）的消费者~~ **已解决（2026-10-13，REA procedure_callers）**：唯一调用方 = `FUN_1410034d0`（SsLineParse 域的 BCFILEFORMATS 字符分类节点：处理 `(`/`.`/`[` 分支）：`.` 分支在无字符集对象（+0xc0 空）时取空集作为"无附加字符"占位传入。空集 = 解析器占位符。
3. [?] 分类器 FUN_14052a160（byte∈5..9 ∨ CR ∨ 0x10）与 14052a0f0 组合的具体属性名（控制字符类?）。
4. [?] 注释截断 Add（140529270）的消费方；+0x30 注释字符、+0x48 开关的设置者。
5. [?] 大小写可覆盖查找类（140529350）的身份与 +0x140 比较器。
6. [?] 二级映射（140526560/140528480/140526440 家族）的键值类型与消费方（哈希索引? 目录缓存?）。
7. [?] 线程队列 deque 布局与 FUN_140087760/087810（pop mode 5）语义。
8. [?] 字符串序列化的确切类型（WideString/UTF8String/AnsiString；长度字段 −4/−8 的 x64 头解释）。
9. [?] 补集 140527c60 的 chars（全 BMP）与位图（仅 ASCII 反转）双轨是否有消费方依赖差异。
10. [?] TSsLine 记录（ti@14051d648）布局 → SsText/SsLine 读取单元规格。
11. [?] 异常类 VMT @1405209c0 与取消消息 LAB_140525790 的文本。
12. [?] 14052a720 进度回调的调用约定确认（fn(ctx, done, total, &cancel)）。
13. [?] 泛型事件表三实例各自挂接的事件源（本单元实例的注册方）。
