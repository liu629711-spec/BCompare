param([string]$Dir = "d:\Rea\extracted\rcdata")

# ---------- 1. 关键窗口字节表：确认属性名 / 值 / 对象边界的编码 ----------
$b = [System.IO.File]::ReadAllBytes((Join-Path $Dir "TTEXTACTIONS.bin"))
Write-Output "=== TTEXTACTIONS.bin 字节 51..150（第一个 TUiAction 对象） ==="
for ($r = 51; $r -lt 151; $r += 16) {
    $hi = [Math]::Min($r + 15, 150)
    $slice = $b[$r..$hi]
    $hex = ($slice | ForEach-Object { "{0:X2}" -f $_ }) -join ' '
    $asc = -join ($slice | ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } elseif ($_ -eq 0) { '_' } else { '.' } })
    "{0,4}  {1,-47}  {2}" -f $r, $hex, $asc
}

# ---------- 2. 解压 zlib 块 ----------
Write-Output ""
Write-Output "=== zlib 解压 ==="
foreach ($name in @("RES_CODES", "PRESETSHAPES_XML", "PRESETTABLESTYLES_XML")) {
    $src = Join-Path $Dir "$name.bin"
    if (-not (Test-Path $src)) { Write-Output "$name 不存在"; continue }
    $bytes = [System.IO.File]::ReadAllBytes($src)

    $ms = New-Object System.IO.MemoryStream
    $ms.Write($bytes, 2, $bytes.Length - 2)   # 跳过 zlib 2 字节头
    $ms.Position = 0

    $out = New-Object System.IO.MemoryStream
    $defl = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
    $defl.CopyTo($out)
    $defl.Dispose(); $ms.Dispose()

    $plain = $out.ToArray()
    $dst = Join-Path $Dir "$name.out"
    [System.IO.File]::WriteAllBytes($dst, $plain)
    $txt = [System.Text.Encoding]::UTF8.GetString($plain[0..([Math]::Min(220, $plain.Length - 1))])
    $txt = ($txt -replace "`r", '' -replace "`n", '\n' -replace '[^\x20-\x7E]', '.')
    Write-Output ("{0,-24} {1,8} -> {2,8} bytes" -f $name, $bytes.Length, $plain.Length)
    Write-Output ("    {0}" -f $txt)
}
