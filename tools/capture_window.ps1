# AI POS Capture Service — PowerShell adapter (first Windows backend).
# Invoked only through tools/capture_service.py. Outputs one JSON result line.

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("List", "Capture", "Probe")]
    [string]$Action,

    [string]$Hwnd = "",
    [string]$OutputPath = "",
    [string]$ExcludeTitle = "",
    [string]$ResultPath = ""
)

$ErrorActionPreference = "Stop"
$ResultPrefix = "AI_POS_CAPTURE_RESULT="

function Write-CaptureResult([hashtable]$Data) {
    $json = ($Data | ConvertTo-Json -Compress -Depth 6)
    if (-not [string]::IsNullOrWhiteSpace($ResultPath)) {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($ResultPath, $json, $utf8)
        Write-Output ($ResultPrefix + "FILE")
    } else {
        Write-Output ($ResultPrefix + $json)
    }
}

Add-Type @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public class AiPosWin {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@

function Get-WindowTitle([IntPtr]$Handle) {
    $len = [AiPosWin]::GetWindowTextLength($Handle)
    if ($len -le 0) { return "" }
    $sb = New-Object System.Text.StringBuilder ($len + 1)
    [void][AiPosWin]::GetWindowText($Handle, $sb, $sb.Capacity)
    return $sb.ToString().Trim()
}

function Get-WindowProcessName([IntPtr]$Handle) {
    $procId = 0
    [void][AiPosWin]::GetWindowThreadProcessId($Handle, [ref]$procId)
    if ($procId -le 0) { return "" }
    try {
        $p = Get-Process -Id $procId -ErrorAction Stop
        return [string]$p.ProcessName
    } catch {
        return ""
    }
}

function Get-TopLevelWindows([string]$Exclude) {
    $list = New-Object System.Collections.Generic.List[object]
    $callback = [AiPosWin+EnumProc]{
        param([IntPtr]$hWnd, [IntPtr]$lParam)
        if (-not [AiPosWin]::IsWindowVisible($hWnd)) { return $true }
        $title = Get-WindowTitle $hWnd
        if ([string]::IsNullOrWhiteSpace($title)) { return $true }
        if ($Exclude -and $title.IndexOf($Exclude, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
        $proc = Get-WindowProcessName $hWnd
        $list.Add([pscustomobject]@{
            hwnd = ("{0}" -f [int64]$hWnd)
            title = $title
            process_name = $proc
            minimized = [bool][AiPosWin]::IsIconic($hWnd)
        }) | Out-Null
        return $true
    }
    [void][AiPosWin]::EnumWindows($callback, [IntPtr]::Zero)
    return $list
}

if ($Action -eq "List") {
    try {
        $windows = @(Get-TopLevelWindows -Exclude $ExcludeTitle)
        Write-CaptureResult @{
            ok = $true
            windows = @($windows | ForEach-Object {
                @{
                    hwnd = $_.hwnd
                    title = $_.title
                    process_name = $_.process_name
                    minimized = $_.minimized
                }
            })
        }
        exit 0
    } catch {
        Write-CaptureResult @{ ok = $false; message = "Не удалось получить список окон." }
        exit 1
    }
}

if ($Action -eq "Probe") {
    try {
        if ([string]::IsNullOrWhiteSpace($Hwnd)) {
            Write-CaptureResult @{ ok = $false; available = $false; message = "Не указано окно." }
            exit 1
        }
        $handle = [IntPtr]([int64]$Hwnd)
        if (-not [AiPosWin]::IsWindow($handle)) {
            Write-CaptureResult @{ ok = $true; available = $false; message = "Сохранённое окно больше недоступно." }
            exit 0
        }
        $title = Get-WindowTitle $handle
        $proc = Get-WindowProcessName $handle
        Write-CaptureResult @{
            ok = $true
            available = $true
            hwnd = ("{0}" -f [int64]$handle)
            title = $title
            process_name = $proc
            minimized = [bool][AiPosWin]::IsIconic($handle)
        }
        exit 0
    } catch {
        Write-CaptureResult @{ ok = $false; available = $false; message = "Не удалось проверить окно." }
        exit 1
    }
}

if ($Action -eq "Capture") {
    try {
        if ([string]::IsNullOrWhiteSpace($Hwnd) -or [string]::IsNullOrWhiteSpace($OutputPath)) {
            Write-CaptureResult @{ ok = $false; message = "Не указано окно или файл снимка." }
            exit 1
        }
        $handle = [IntPtr]([int64]$Hwnd)
        if (-not [AiPosWin]::IsWindow($handle)) {
            Write-CaptureResult @{
                ok = $false
                need_reselect = $true
                message = "Выбранное окно больше недоступно. Выберите окно снова."
            }
            exit 1
        }
        if ([AiPosWin]::IsIconic($handle)) {
            [void][AiPosWin]::ShowWindow($handle, 9) # SW_RESTORE
            Start-Sleep -Milliseconds 250
        }
        [void][AiPosWin]::SetForegroundWindow($handle)
        Start-Sleep -Milliseconds 200

        $rect = New-Object AiPosWin+RECT
        if (-not [AiPosWin]::GetWindowRect($handle, [ref]$rect)) {
            Write-CaptureResult @{ ok = $false; message = "Не удалось определить размер окна." }
            exit 1
        }
        $width = [Math]::Max(1, $rect.Right - $rect.Left)
        $height = [Math]::Max(1, $rect.Bottom - $rect.Top)
        if ($width -lt 40 -or $height -lt 40) {
            Write-CaptureResult @{ ok = $false; message = "Окно слишком маленькое для снимка. Разверните его и повторите." }
            exit 1
        }

        Add-Type -AssemblyName System.Drawing
        $bmp = New-Object System.Drawing.Bitmap $width, $height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size $width, $height))
        $g.Dispose()

        $dir = Split-Path -Parent $OutputPath
        if ($dir -and -not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
        $bmp.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()

        $info = Get-Item -LiteralPath $OutputPath
        $title = Get-WindowTitle $handle
        $proc = Get-WindowProcessName $handle
        Write-CaptureResult @{
            ok = $true
            hwnd = ("{0}" -f [int64]$handle)
            title = $title
            process_name = $proc
            width = $width
            height = $height
            bytes = [int64]$info.Length
            output_path = $OutputPath
        }
        exit 0
    } catch {
        Write-CaptureResult @{ ok = $false; message = "Не удалось сделать снимок окна. Повторите попытку." }
        exit 1
    }
}
