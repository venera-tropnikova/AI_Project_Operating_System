# Optional: create Desktop shortcut AI POS -> start_ai_pos_silent.vbs
# Технические файлы держим в ASCII-именах: русское название живёт в самом ярлыке.
# Optional branding ICO; warns if missing and uses default icon.
$ErrorActionPreference = "Stop"

function Write-User([string]$Text) {
    Write-Host $Text
}

try {
    $root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
    $vbs = Join-Path $root "start_ai_pos_silent.vbs"
    $ico = Join-Path $root "assets\branding\ai-pos-icon-v1.ico"

    if (-not (Test-Path -LiteralPath $vbs)) {
        Write-User "Не найден файл запуска AI POS в корне папки."
        Write-User "Откройте папку AI POS и запустите start_ai_pos.cmd."
        exit 1
    }

    $desktop = [Environment]::GetFolderPath("Desktop")
    $lnkPath = Join-Path $desktop "AI POS.lnk"
    $wscript = Join-Path $env:SystemRoot "System32\wscript.exe"

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($lnkPath)
    $shortcut.TargetPath = $wscript
    $shortcut.Arguments = '"' + $vbs + '"'
    $shortcut.WorkingDirectory = $root
    $shortcut.WindowStyle = 7
    $shortcut.Description = "AI Project Operating System"

    $iconMissing = $false
    if (Test-Path -LiteralPath $ico) {
        $shortcut.IconLocation = "$ico,0"
    } else {
        $iconMissing = $true
    }

    $shortcut.Save()

    Write-User "Ярлык AI POS создан на рабочем столе."
    if ($iconMissing) {
        Write-User ""
        Write-User "Предупреждение: фирменная иконка не найдена."
        Write-User "Будет использована стандартная иконка."
    }
    Write-User ""
    Write-User "После переноса папки AI POS запустите создание ярлыка снова."
    Write-User ""
    try { Read-Host "Нажмите Enter, чтобы закрыть" | Out-Null } catch { }
    exit 0
}
catch {
    Write-User "Не удалось создать ярлык."
    Write-User ($_.Exception.Message)
    Write-User ""
    try { Read-Host "Нажмите Enter, чтобы закрыть" | Out-Null } catch { }
    exit 1
}
