$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = "Y:\Final yr project\Honours\gps-spoof-timesync\report\Honours_Final_Year_Mini_Project_Report.docx"
$doc = $word.Documents.Open($docPath, [Type]::Missing, $true)

$offset = 11
$captions = @()

foreach ($p in $doc.Paragraphs) {
    $text = $p.Range.Text.Trim()
    if ($text -match '^(Figure|Table)\s+[0-9]\.[0-9]') {
        $physPage = $p.Range.Information([Microsoft.Office.Interop.Word.WdInformation]::wdActiveEndPageNumber)
        $secPage = $physPage - $offset
        $captions += "$secPage : $text"
    }
}

$doc.Close()
$word.Quit()

Write-Output "=== CAPTIONS EXTRACTED FROM WORD ==="
$captions | ForEach-Object { Write-Output $_ }
