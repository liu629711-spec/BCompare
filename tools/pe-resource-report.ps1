param(
    [string]$EvidencePath = "C:\Users\liuxinlong\.qoder\cache\projects\Rea-adec8f35\agent-tools\c6d98849\9b2be6a6.txt"
)

$n = (Get-Content $EvidencePath -Raw | ConvertFrom-Json).normalized_result

Write-Output "=== 资源类型分布（kind + 名称/ID） ==="
$n.resources | ForEach-Object {
    if ($_.type.kind -eq 'name') { "NAME:$($_.type.name)" }
    else { "ID:$($_.type.id)" }
} | Group-Object | Sort-Object Count -Descending | ForEach-Object {
    "{0,-20} {1}" -f $_.Name, $_.Count
}

Write-Output ""
Write-Output "=== 命名资源示例（每类前 12 个名字） ==="
$n.resources | Where-Object { $_.type.kind -eq 'name' } | ForEach-Object {
    [pscustomobject]@{
        type   = $_.type.name
        name   = $_.name.name
        nameId = $_.name.id
        lang   = $_.language
        bytes  = $_.payload.bytes
    }
} | Group-Object type | ForEach-Object {
    "--- $($_.Name) ($($_.Count) 项) ---"
    $_.Group | Select-Object -First 12 | ForEach-Object {
        "    {0}  lang={1}  bytes={2}" -f $_.name, $_.lang, $_.bytes
    }
}

Write-Output ""
Write-Output "=== payload 总字节按类型汇总 ==="
$n.resources | Where-Object { $_.type.kind -eq 'name' } | Group-Object { $_.type.name } | ForEach-Object {
    $sum = ($_.Group | Measure-Object -Property bytes -Sum).Sum
    "{0,-20} {1,10} bytes" -f $_.Name, $sum
} | Sort-Object
