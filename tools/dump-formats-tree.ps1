param(
    [string]$Path = "d:\Rea\extracted\rcdata\BCFILEFORMATS.bin",
    [int]$Depth = 4,
    [int]$Tree = 0
)

$xml = [xml](Get-Content $Path -Raw -Encoding UTF8)
$root = $xml.DocumentElement

function Show-Node($nd, $indent, $level) {
    $v = ''
    if ($nd.Attributes['Value']) { $v = ' = ' + $nd.Attributes['Value'].Value }
    $txt = if ($nd.InnerText -and -not $nd.Attributes['Value'] -and $nd.ChildNodes.Count -eq 0) { ' : ' + $nd.InnerText.Trim() } else { '' }
    Write-Output ("{0}<{1}>{2}{3}" -f $indent, $nd.Name, $v, $txt)
    if ($level -ge $Depth) { return }
    foreach ($c in $nd.ChildNodes) {
        if ($c.NodeType -eq 'Element') { Show-Node $c ($indent + '  ') ($level + 1) }
    }
}

Write-Output "=== 顶层 25 个内建文件格式 ==="
$i = 0
foreach ($fmt in $root.ChildNodes) {
    $i++
    $desc = $fmt.SelectSingleNode("Description")
    $mask = $fmt.SelectSingleNode(".//Mask")
    $nameAttr = if ($fmt.Attributes['Value']) { $fmt.Attributes['Value'].Value } else { '' }
    "{0,2}. <{1}>{2}  Mask={3}" -f $i, $fmt.Name, $nameAttr, ($mask.Attributes['Value'] -join '')
}

if ($Tree -gt 0) {
    Write-Output ""
    Write-Output "=== 第 $Tree 个条目的完整结构树（深度 $Depth） ==="
    Show-Node $root.ChildNodes[$Tree - 1] '' 0
}
