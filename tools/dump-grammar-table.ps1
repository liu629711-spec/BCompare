param([string]$Path = "d:\Rea\extracted\rcdata\BCFILEFORMATS.bin")

# 导出 25 个内建格式的语法表：关键字清单规模 + 正则 token + 终止/分隔/制表符设置
$xml = [xml](Get-Content $Path -Raw -Encoding UTF8)

foreach ($fmt in $xml.DocumentElement.ChildNodes) {
    $idv = if ($fmt.Attributes['Value']) { $fmt.Attributes['Value'].Value } else { '(无名)' }
    $maskNode = @($fmt.SelectNodes(".//Mask")) | Select-Object -First 1
    $mask = if ($maskNode) { $maskNode.Attributes['Value'].Value } else { '' }

    $listItems  = @($fmt.SelectNodes(".//_0/Items/*")) + @($fmt.SelectNodes(".//Items/*"))
    $kwNodes    = @($fmt.SelectNodes(".//_0")) | Where-Object { $_.SelectSingleNode("ElementStr") -and $_.SelectSingleNode("ElementStr").Attributes['Value'].Value -eq 'Keyword' }
    $kwCount = 0
    if ($kwNodes.Count) { $kwCount = @($kwNodes[0].SelectNodes(".//Items/*")).Count }

    $tokens = @($fmt.SelectNodes("//*")) | Where-Object {
        $_.Name -match '^_\d+$' -and $_.SelectSingleNode("Text")
    } | ForEach-Object {
        $e = $_.SelectSingleNode("ElementStr").Attributes['Value'].Value
        $t = $_.SelectSingleNode("Text").Attributes['Value'].Value
        $re = if ($_.SelectSingleNode("IsRegExp")) { $_.SelectSingleNode("IsRegExp").Attributes['Value'].Value } else { '' }
        "$e=$t$(if ($re -eq 'True') {' [re]'} else {' [lit]'})"
    }

    $stops = @($fmt.SelectNodes("//*")) | Where-Object { $_.Name -in @('StopText', 'StopEOL', 'StopCol', 'Escape', 'DlmDelimiters', 'DlmQualifier', 'TabAsSpaces', 'TabSize', 'CaseSensitive') } | ForEach-Object {
        "$($_.Name)=$($_.Attributes['Value'].Value)"
    }

    Write-Output ("### {0}  <{1}>  Mask={2}" -f $idv, $fmt.Name, $mask)
    Write-Output ("    关键字 {0} 个；正则/字面 token {1} 个" -f $kwCount, $tokens.Count)
    if ($tokens.Count) { Write-Output ("    token: " + (($tokens | Select-Object -First 6) -join ' | ')) }
    if ($stops.Count) { Write-Output ("    规则: " + (($stops | Select-Object -Unique) -join '  ')) }
    Write-Output ""
}
