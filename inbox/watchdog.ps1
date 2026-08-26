# 3rdBrain Inbox watchdog: keep exactly one collector running.
# Schedule this script at logon and every few minutes. It needs no admin access.

$ErrorActionPreference = "Stop"
$inboxDir = $PSScriptRoot
$botPath = Join-Path $inboxDir "bot.py"
$logPath = Join-Path $inboxDir "bot.log"
$configPath = Join-Path $inboxDir "config.json"
$lockPort = 47921

function Write-WatchdogLog([string]$Message) {
    $line = "{0} watchdog: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
}

if (Test-Path -LiteralPath $configPath) {
    try {
        $config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
        if ($null -ne $config.lock_port) {
            $configuredPort = [int]$config.lock_port
            if ($configuredPort -lt 1 -or $configuredPort -gt 65535) {
                throw "lock_port must be between 1 and 65535"
            }
            $lockPort = $configuredPort
        }
    }
    catch {
        Write-WatchdogLog "invalid config.json or lock_port; refusing launch: $($_.Exception.Message)"
        exit 1
    }
}

try {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $lockPort)
}
catch {
    Write-WatchdogLog "could not inspect lock port $lockPort; refusing launch: $($_.Exception.Message)"
    exit 1
}

if ($listeners.Count -gt 0) {
    foreach ($processId in ($listeners.OwningProcess | Sort-Object -Unique)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
        $isPythonBot = $process.Name -like "python*.exe" -and
            $process.CommandLine -match '(?i)(^|[\\/"\s])bot\.py(["\s]|$)'
        if (-not $isPythonBot) {
            Write-WatchdogLog "port $lockPort belongs to another process; refusing launch"
            exit 1
        }
    }
    exit 0
}

$pythonw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($null -eq $pythonw) {
    Write-WatchdogLog "pythonw.exe was not found on PATH; refusing launch"
    exit 1
}

Start-Process -FilePath $pythonw.Source -ArgumentList "`"$botPath`"" `
    -WorkingDirectory $inboxDir -WindowStyle Hidden
Write-WatchdogLog "relaunched collector on lock port $lockPort"
