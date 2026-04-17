Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screenshotDir = "d:\Graduation_project\Test\screenshots"
if (-not (Test-Path $screenshotDir)) { New-Item -ItemType Directory -Path $screenshotDir -Force }

function Take-Screenshot {
    param([string]$Name)
    Start-Sleep -Milliseconds 500
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $screen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $path = Join-Path $screenshotDir "$Name.png"
    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    Write-Output "Screenshot saved: $path"
}

$pages = @(
    @{Name="01_index"; Url="http://localhost:8000/static/index.html"},
    @{Name="02_dashboard"; Url="http://localhost:8000/static/dashboard.html"},
    @{Name="03_knowledge"; Url="http://localhost:8000/static/knowledge.html"},
    @{Name="04_chat"; Url="http://localhost:8000/static/chat.html"},
    @{Name="05_api_docs"; Url="http://localhost:8000/docs"}
)

Start-Process "http://localhost:8000/static/index.html"
Start-Sleep -Seconds 3

foreach ($page in $pages) {
    Start-Process $page.Url
    Start-Sleep -Seconds 3
    Take-Screenshot -Name $page.Name
}

Write-Output "`nAll screenshots taken!"
