param([string]$Path = "d:\Rea\extracted\rcdata\BCFILEFORMATS.bin")

$xml = [xml](Get-Content $Path -Raw -Encoding UTF8)
$root = $xml.DocumentElement
Write-Output "根元素: <$($root.Name)>  子节点数=$($root.ChildNodes.Count)"
Write-Output ""
Write-Output "=== 直接子元素类型分布 ==="
$root.ChildNodes | Group-Object NodeType | ForEach-Object { "{0,-14} {1}" -f $_.Name, $_.Count }
Write-Output ""
Write-Output "=== 元素名 -> 出现次数 / 属性名集合 ==="
$all = $root.SelectNodes("//*")
$all | Group-Object Name | Sort-Object Count -Descending | ForEach-Object {
    $attrs = @()
    foreach ($nd in $_.Group) {
        foreach ($a in $nd.Attributes) { $attrs += $a.Name }
    }
    $uniq = ($attrs | Sort-Object -Unique) -join ','
    "{0,-22} x{1,-5} attrs: {2}" -f $_.Name, $_.Count, $uniq
}
Write-Output ""
Write-Output "=== 第一个格式条目的完整内容（样本） ==="
$first = $all | Where-Object { $_.Name -ne $root.Name -and $_.ParentNode.Name -eq $root.Name } | Select-Object -First 1
if ($first) { $first.OuterXml }
