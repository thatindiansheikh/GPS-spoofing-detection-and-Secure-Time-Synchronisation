$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = "Y:\Final yr project\Honours\gps-spoof-timesync\report\Honours_Final_Year_Mini_Project_Report.docx"
$doc = $word.Documents.Open($docPath, [Type]::Missing, $true)

for ($i = 1; $i -le 13; $i++) {
    $range = $doc.GoTo([Microsoft.Office.Interop.Word.WdGoToItem]::wdGoToPage, [Microsoft.Office.Interop.Word.WdGoToDirection]::wdGoToAbsolute, $i)
    $text = $range.Paragraphs[1].Range.Text.Trim()
    Write-Output "Physical Page $i first line: $text"
}

$doc.Close()
$word.Quit()
