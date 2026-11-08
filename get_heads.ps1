$ErrorActionPreference = "Stop"
# Lay so trang that cua bao cao FreshMart va ghi dump cho build_muc_luc.py.
# Buoc 1 (trc): cp "Bao_Cao_Mini_Project_FreshMart.docx" C:\Users\nguye\AppData\Local\Temp\rpt_toc.docx
# Buoc 2: powershell -NoProfile -ExecutionPolicy Bypass -File get_heads.ps1
$copy = "C:\Users\nguye\AppData\Local\Temp\rpt_toc.docx"
$out  = "C:\Users\nguye\AppData\Local\Temp\head_dump.txt"
if (-not (Test-Path $copy)) { throw "Chua co ban sao $copy" }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($copy, $false, $false)
$doc.Fields.Update() | Out-Null
$toc = $doc.TablesOfContents.Item(1)
$toc.Range.Fields.Item(1).Code.Text = ' TOC \o "1-3" \h \z \u '
$toc.Update()
$doc.Repaginate()
$lines = @()
foreach ($p in $toc.Range.Paragraphs) {
    $t = $p.Range.Text -replace "[`r`n`a`b]", ""
    $t = $t.Trim([char]0x20, [char]0x09, [char]0x0B)
    if ($t.Length -lt 2) { continue }
    $style = $p.Style.NameLocal
    $parts = $t -split "`t"
    $title = ($parts[0] -replace "^[.` ]+", "").Trim()
    $page = ""
    if ($parts.Count -gt 1) { $page = ($parts[-1] -replace "[^0-9]", "") }
    $lvl = 3
    if ($style -match "1") { $lvl = 1 } elseif ($style -match "2") { $lvl = 2 }
    $lines += ("{0}|{1}|{2}" -f $lvl, $page, $title)
}
$lines | Out-File -FilePath $out -Encoding UTF8
Write-Output ("entries: " + $lines.Count)
$doc.Close(0)
$word.Quit()
