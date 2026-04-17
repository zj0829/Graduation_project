Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screenshotDir = "d:\Graduation_project\Test\screenshots"

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

Take-Screenshot -Name "06_docker_desktop"
Start-Sleep -Seconds 1
Take-Screenshot -Name "07_terminal_mcp"
Start-Sleep -Seconds 1
Take-Screenshot -Name "08_terminal_backend"
Start-Sleep -Seconds 1
Take-Screenshot -Name "09_dashboard_audit"
Start-Sleep -Seconds 1
Take-Screenshot -Name "10_knowledge_owasp"

Write-Output "Additional screenshots taken!"
