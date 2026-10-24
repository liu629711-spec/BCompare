param(
    [string]$Dir = "d:\Rea\extracted\rcdata",
    [string]$Sample = "",
    [switch]$Inventory
)

# ---------------------------------------------------------------------------
# BC 的 TPF0 方言 tokenizer（规则由 TTEXTACTIONS.bin 头部实测推导，见注释）
#   F1 <len> <name>       类名 / 对象名
#   <len 0x01..0xEF> <…>  长度前缀 ANSI 串（实例名、属性名、tag=06 的字符串值）
#   00                    结束标记
#   属性值前的 1 字节为值标签；实测 06 = 长度前缀 ANSI 串
# 未预期的标签不猜测：计入 unknown 并中止该对象的属性扫描，保证不产出假数据。
# ---------------------------------------------------------------------------

$script:pos = 0
$script:buf = $null
$script:unknownTags = @{}
$script:resyncs = 0

function Reset-Reader($bytes) {
    $script:buf = $bytes
    $script:pos = 0
}
function Eof { return $script:pos -ge $script:buf.Length }
function Peek { if (Eof) { return -1 } return $script:buf[$script:pos] }
function Take { $v = $script:buf[$script:pos]; $script:pos++; return $v }
function Take-Bytes($n) {
    if ($script:pos + $n -gt $script:buf.Length) { throw "越界读取 $n @ $script:pos" }
    $s = $script:buf[$script:pos..($script:pos + $n - 1)]
    $script:pos += $n
    return [System.Text.Encoding]::UTF8.GetString($s)
}
function Looks-Ident($s) { return $s -match '^[A-Za-z_][A-Za-z0-9_.]*$' }

# 读一个长度前缀串；返回 $null 表示此处不是串
function Try-ReadStr() {
    $start = $script:pos
    $len = Peek
    if ($len -lt 1 -or $len -gt 0xEF) { return $null }
    $script:pos++
    try {
        $s = Take-Bytes $len
    } catch { $script:pos = $start; return $null }
    if (-not (Looks-Ident $s)) { $script:pos = $start; return $null }
    return $s
}

function Read-ClassRef() {
    # 期望 F1 + len + 类名；非标识符一律视为误对齐，回滚并交回控制权
    if ((Peek) -ne 0xF1) { return $null }
    $start = $script:pos
    $script:pos++
    $len = Peek
    if ($len -lt 1 -or $len -gt 0xEF) { $script:pos = $start; return $null }
    $script:pos++
    $s = Take-Bytes $len
    if (-not (Looks-Ident $s) -or $s -notmatch '^T') {
        $script:pos = $start
        $script:resyncs++
        return $null
    }
    return $s
}

# 解析一个对象头（类名 + 实例名），随后读它的属性表
function Parse-Object($classes, $props, $objs) {
    $cls = Read-ClassRef
    if (-not $cls) { return }
    $classes[$cls] = 1 + $classes[$cls]
    $name = Try-ReadStr
    $rec = [pscustomobject]@{ Class = $cls; Name = $name; Props = [ordered]@{} }
    $objs.Add($rec)

    while (-not (Eof)) {
        $b = Peek
        if ($b -eq 0x00) { [void](Take); break }
        $pn = Try-ReadStr
        if (-not $pn) { [void](Take); continue }        # 非串字节：跳过并继续对齐
        $props[$pn] = 1 + $props[$pn]
        $tag = Take
        if ($tag -eq 0x06) {
            $len = Take
            if ($len -ge 1 -and $len -le 0xEF -and -not (Eof)) {
                $rec.Props[$pn] = Take-Bytes $len
            }
        }
        elseif ($tag -eq 0x0A) {       # 观测到的对象/集合引用（本版本仅记录标签）
            $rec.Props[$pn] = "<tag:0A>"
        }
        else {
            $script:unknownTags["0x{0:X2}" -f $tag] = 1 + $script:unknownTags["0x{0:X2}" -f $tag]
            $rec.Props[$pn] = "<tag:0x{0:X2}>" -f $tag
            break
        }
    }
}

function Parse-Stream($bytes) {
    $classes = @{}; $props = @{}
    $script:unknownTags = @{}
    $script:resyncs = 0
    $objs = New-Object System.Collections.Generic.List[object]
    Reset-Reader $bytes
    if ([System.Text.Encoding]::ASCII.GetString($bytes[0..3]) -ne 'TPF0') { return $null }
    $script:pos = 4
    $guard = 0
    while (-not (Eof) -and ($guard++ -lt 200000)) {
        $b = Peek
        if ($b -eq 0x00) { [void](Take); continue }
        if ($b -eq 0xF1) { Parse-Object $classes $props $objs; continue }
        [void](Take)   # 结构间隙字节
    }
    return [pscustomobject]@{ Classes = $classes; Props = $props; Objects = $objs; Unknown = $script:unknownTags; Resyncs = $script:resyncs; Consumed = $script:pos; Size = $bytes.Length }
}

if ($Sample -ne "") {
    $r = Parse-Stream ([System.IO.File]::ReadAllBytes((Join-Path $Dir $Sample)))
    Write-Output "=== 样本 $Sample ==="
    Write-Output ("解析对象数={0}  消费字节={1}/{2}" -f $r.Objects.Count, $r.Consumed, $r.Size)
    Write-Output "类名: " + (($r.Classes.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { "$($_.Key)x$($_.Value)" }) -join ' ')
    Write-Output "属性: " + (($r.Props.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { "$($_.Key)x$($_.Value)" }) -join ' ')
    if ($r.Unknown.Count) {
        $u = ($r.Unknown.GetEnumerator() | ForEach-Object { "{0}x{1}" -f $_.Key, $_.Value }) -join ' '
        Write-Output "未识别值标签: $u"
    }
    Write-Output "=== 前 18 个对象 ==="
    $r.Objects | Select-Object -First 18 | ForEach-Object {
        $kv = ($_.Props.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join '; '
        "[{0}] {1} :: {2}" -f $_.Class, $_.Name, $kv
    }
    return
}

if ($Inventory) {
    $allClasses = @{}; $allProps = @{}; $fileCount = 0; $objTotal = 0; $resyncTotal = 0
    $tagTotals = @{}
    Get-ChildItem $Dir -Filter *.bin | ForEach-Object {
        $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
        if ($bytes.Length -lt 5) { return }
        if ([System.Text.Encoding]::ASCII.GetString($bytes[0..3]) -ne 'TPF0') { return }
        $fileCount++
        $r = Parse-Stream $bytes
        $objTotal += $r.Objects.Count
        $resyncTotal += $r.Resyncs
        foreach ($k in $r.Unknown.Keys) { $tagTotals[$k] = $r.Unknown[$k] + $tagTotals[$k] }
        foreach ($k in $r.Classes.Keys) { $allClasses[$k] = $r.Classes[$k] + $allClasses[$k] }
        foreach ($k in $r.Props.Keys) { $allProps[$k] = $r.Props[$k] + $allProps[$k] }
    }
    Write-Output "=== TPF0 流文件数=$fileCount，解析对象总数=$objTotal，重同步次数=$resyncTotal ==="
    if ($tagTotals.Count) {
        Write-Output "尚未解码的值标签（计数）: "
        $tagTotals.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { "    {0} x{1}" -f $_.Key, $_.Value }
    }
    Write-Output ""
    Write-Output "=== BC 使用的类（按出现次数，前 45） ==="
    $allClasses.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 45 | ForEach-Object { "{0,-34} {1}" -f $_.Key, $_.Value }
    Write-Output ""
    Write-Output "=== 属性名（按出现次数，前 30） ==="
    $allProps.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 30 | ForEach-Object { "{0,-28} {1}" -f $_.Key, $_.Value }
}
