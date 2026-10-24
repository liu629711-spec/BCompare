param(
    [string]$File = "d:\Rea\extracted\rcdata\TBCACTIONS.bin",
    [int]$MinLen = 4
)

$b = [System.IO.File]::ReadAllBytes($File)
Write-Output "文件=$($File) 字节=$($b.Length) 魔数=$([System.Text.Encoding]::ASCII.GetString($b,0,4))"

# TPF0 流里对象名以 0xF0/0xF1 + 1 字节长度 + ANSI 类名 的形式出现；
# 字符串值以 vtAnsiString(3)/vtString('S')/vtWideString/vtUnicodeString('U') 标签出现。
# 这里先做保守的可打印串抽取，用于确认结构层次。
$strings = New-Object System.Collections.Generic.List[string]
$i = 0
while ($i -lt $b.Length) {
    if ($b[$i] -ge 32 -and $b[$i] -le 126) {
        $start = $i
        while ($i -lt $b.Length -and $b[$i] -ge 32 -and $b[$i] -le 126) { $i++ }
        $s = [System.Text.Encoding]::ASCII.GetString($b, $start, $i - $start)
        if ($s.Length -ge $MinLen) { $strings.Add(("{0,7}: {1}" -f $start, $s)) }
    } else { $i++ }
}

Write-Output "抽取到字符串 $($strings.Count) 条，前 70 条："
$strings | Select-Object -First 70
