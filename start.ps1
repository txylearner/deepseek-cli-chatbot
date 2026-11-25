<#
.SYNOPSIS
    一键启动后端（8000）与前端（5173）。
.DESCRIPTION
    在仓库根目录执行： .\start.ps1
    脚本会依次启动 uvicorn 与 vite，等两者就绪后打开浏览器；按 Ctrl+C 停止两个服务。
    加 -NoBrowser 可以不自动开浏览器。
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$python = Join-Path $backendDir '.venv\Scripts\python.exe'
$vite = Join-Path $frontendDir 'node_modules\vite\bin\vite.js'

function Test-Listening([int]$port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

if (-not (Test-Path $python)) {
    throw '缺少 backend\.venv：先在 backend 目录执行 python -m venv .venv 和 pip install -e ".[dev]"'
}
if (-not (Test-Path $vite)) {
    throw '缺少前端依赖：先在 frontend 目录执行 npm install'
}
foreach ($port in 8000, 5173) {
    if (Test-Listening $port) {
        $tip = 'Get-NetTCPConnection -State Listen -LocalPort ' + $port + ' | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }'
        throw ("端口 $port 已被占用，先关掉旧进程再运行：" + $tip)
    }
}

Write-Host '启动后端（8000）...' -ForegroundColor Cyan
$backend = Start-Process -FilePath $python `
    -ArgumentList '-m', 'uvicorn', 'chatbot.app:app', '--host', '127.0.0.1', '--port', '8000' `
    -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
        if ($health.status -eq 'ok') { $ready = $true; break }
    } catch { }
}
if (-not $ready) {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    throw '后端启动失败：检查 backend\.env 里是否配置了 CHATBOT_API_KEY。'
}

Write-Host '启动前端（5173）...' -ForegroundColor Cyan
$frontend = Start-Process -FilePath 'node' `
    -ArgumentList $vite, '--port', '5173' `
    -WorkingDirectory $frontendDir -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Listening 5173) { $ready = $true; break }
}
if (-not $ready) {
    Stop-Process -Id $backend.Id, $frontend.Id -Force -ErrorAction SilentlyContinue
    throw '前端启动失败：先在 frontend 目录执行 npm install。'
}

if (-not $NoBrowser) { Start-Process 'http://localhost:5173/' | Out-Null }

Write-Host ''
Write-Host '  界面  http://localhost:5173/' -ForegroundColor Green
Write-Host '  接口  http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host '  按 Ctrl+C 停止两个服务' -ForegroundColor DarkGray
Write-Host ''

$script:stopped = $false
try {
    [Console]::add_CancelKeyPress({
        param($sender, $eventArgs)
        $eventArgs.Cancel = $true
        $script:stopped = $true
    })
} catch { }

try {
    while (-not $script:stopped -and -not $frontend.HasExited) {
        Start-Sleep -Milliseconds 800
    }
} finally {
    Write-Host '正在停止服务...' -ForegroundColor DarkGray
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    foreach ($port in 8000, 5173) {
        Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
    Write-Host '已停止。' -ForegroundColor DarkGray
}
