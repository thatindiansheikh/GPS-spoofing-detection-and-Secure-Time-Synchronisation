$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = "Y:\Final yr project\Honours\gps-spoof-timesync\report\Honours_Final_Year_Mini_Project_Report.docx"
$doc = $word.Documents.Open($docPath, [Type]::Missing, $true)

$headings = @()

foreach ($p in $doc.Paragraphs) {
    $text = $p.Range.Text.Trim()
    if ($text -match '^(CHAPTER [0-9]|[0-9]+\.[0-9]+|LIST OF|ABSTRACT|ACKNOWLEDGEMENT|TABLE OF CONTENTS|BONAFIDE|REFERENCES)') {
        $page = $p.Range.Information([Microsoft.Office.Interop.Word.WdInformation]::wdActiveEndPageNumber)
        $headings += "$page : $text"
    }
}

$doc.Close()
$word.Quit()

$headings | Out-File "Y:\Final yr project\Honours\gps-spoof-timesync\scripts\actual_pages.txt" -Encoding utf8
Write-Output "Extracted $($headings.Count) headings and their page numbers!"
