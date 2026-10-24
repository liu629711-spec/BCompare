param(
    [string]$Dir = "d:\Rea\extracted\rcdata"
)

# ---------- 1. 用观察推导 TPF0 编码：打印首个流的头部字节表 ----------
$head = [System.IO.File]::ReadAllBytes((Join-Path $Dir "TTEXTACTIONS.bin"))[0..95]
Write-Output "=== TTEXTACTIONS.bin 头 96 字节 ==="
for ($r = 0; $r -lt $head.Count; $r += 16) {
    $slice = $head[$r..([Math]::Min($r + 15, $head.Count - 1))]
    $hex = ($slice | ForEach-Object { "{0:X2}" -f $_ }) -join ' '
    $asc = -join ($slice | ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' } })
    "{0,4}  {1,-47}  {2}" -f $r, $hex, $asc
}

# ---------- 2. 解 zlib 块（78 DA） ----------
Write-Output ""
Write-Output "=== zlib 块解压 ==="
foreach ($name in @("RES_CODES", "PRESETSHAPES_XML", "PRESETTABLESTYLES_XML")) {
    $src = Join-Path $Dir "$name.bin"
    if (-not (Test-Path $src)) { Write-Output "$name 不存在"; continue }
    $bytes = [System.IO.File]::ReadAllBytes($src)
    $ms = New-Object System.IO.MemoryStream(, $bytes, 2, ($bytes.Length - 2))
    $defl = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
    $out = New-Object System.IO.MemoryStream
    $defl.CopyTo($out)
    $defl.Dispose(); $ms.Dispose()
    $plain = $out.ToArray()
    $dst = Join-Path $Dir "$name.out"
    [System.IO.File]::WriteAllBytes($dst, $plain)
    $preview = -join ($plain[0..([Math]::Min(120, $plain.Length - 1))] |
        ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } elseif ($_ -eq 10) { "`n" } else { '.' } })
    Write-Output ("{0,-24} {1,8} -> {2,8} bytes  头部: {3}" -f $name, $bytes.Length, $plain.Length, ($preview -replace "`n", '\n'))
}
