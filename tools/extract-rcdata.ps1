param(
    [string]$EvidencePath = "C:\Users\liuxinlong\.qoder\cache\projects\Rea-adec8f35\agent-tools\c6d98849\9b2be6a6.txt",
    [string]$OutDir = "d:\Rea\extracted\rcdata"
)

$ev = Get-Content $EvidencePath -Raw | ConvertFrom-Json
$exe = "D:\bc-official\app\BCompare.exe"

# 只接受与 Evidence 同一份文件：重新算哈希并比对 subject 摘要
$actual = (Get-FileHash -Algorithm SHA256 $exe).Hash.ToLower()
if ($actual -ne $ev.subject.digest.sha256) {
    throw "目标文件哈希与 Evidence 不一致：expected=$($ev.subject.digest.sha256) actual=$actual"
}
Write-Output "身份校验通过 sha256=$actual"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$rc = @($ev.normalized_result.resources | Where-Object {
    $_.type.kind -eq 'id' -and $_.type.id -eq 10 -and $_.name.kind -eq 'name'
})
Write-Output "待提取 RCDATA=$($rc.Count)"

$all = [System.IO.File]::ReadAllBytes($exe)
$sha = [System.Security.Cryptography.SHA256]::Create()
$manifest = foreach ($r in $rc) {
    $off = [int]$r.payload.location.offset
    $len = [int]$r.payload.location.bytes
    if ($off + $len -gt $all.Length) {
        Write-Warning "跳过越界项 $($r.name.name)"
        continue
    }
    $buf = New-Object byte[] $len
    [System.Buffer]::BlockCopy($all, $off, $buf, 0, $len)

    $got = [System.BitConverter]::ToString($sha.ComputeHash($buf)) -replace '-', ''
    if ($got.ToLower() -ne $r.payload.sha256.ToLower()) {
        Write-Warning "载荷哈希不匹配 $($r.name.name)"
        continue
    }

    $file = Join-Path $OutDir ("{0}.bin" -f $r.name.name)
    [System.IO.File]::WriteAllBytes($file, $buf)

    $n = [Math]::Min(15, $len - 1)
    $head = ($buf[0..$n] | ForEach-Object { "{0:X2}" -f $_ }) -join ' '
    $ascii = -join ($buf[0..$n] | ForEach-Object {
        if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' } })

    [pscustomobject]@{
        Name  = $r.name.name
        Bytes = $len
        Lang  = $r.language.id
        Head  = "$head | $ascii"
    }
}

$manifest | Sort-Object Bytes -Descending | Format-Table -AutoSize | Out-String -Width 200 | Write-Output
Write-Output "提取完成=$($manifest.Count) 个文件，输出目录=$OutDir"
