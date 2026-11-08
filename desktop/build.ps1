# 观象桌面版 · Windows 构建脚本
# 用法：powershell -ExecutionPolicy Bypass -File build.ps1
# 产物：build\观象.exe（单文件，内嵌界面与知识数据，无需安装运行时）

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    $env:CGO_ENABLED = "0"
    $out = Join-Path $PSScriptRoot "build\观象.exe"
    New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null

    # Windows 资源（图标 + 版本信息）：图标比资源新时必须重建，避免 EXE 沿用旧图标。
    $syso = Join-Path $PSScriptRoot "rsrc_windows_amd64.syso"
    $icon = Join-Path $PSScriptRoot "ui\brand\icon.ico"
    if ((-not (Test-Path $syso)) -or ((Get-Item $icon).LastWriteTimeUtc -gt (Get-Item $syso).LastWriteTimeUtc)) {
        Write-Host "==> 生成 Windows 资源 (rsrc_windows_amd64.syso)" -ForegroundColor Cyan
        go run github.com/tc-hib/go-winres@latest simply --arch amd64 --out rsrc `
            --icon ui/brand/icon.ico --manifest gui `
            --product-name "观象桌面版" --file-description "观象 · 纯本地四柱排盘客户端" `
            --file-version 1.0.0.0 --product-version 1.0.0.0 --original-filename "观象.exe" `
            --copyright "本地离线使用，仅供文化研究与娱乐"
        if ($LASTEXITCODE -ne 0) { throw "生成 Windows 资源失败" }
    }

    Write-Host "==> go vet" -ForegroundColor Cyan
    go vet ./...
    if ($LASTEXITCODE -ne 0) { throw "go vet 失败" }

    Write-Host "==> go test" -ForegroundColor Cyan
    go test ./...
    if ($LASTEXITCODE -ne 0) { throw "go test 失败" }

    Write-Host "==> go build" -ForegroundColor Cyan
    go build -trimpath -ldflags "-s -w -H windowsgui" -o $out .
    if ($LASTEXITCODE -ne 0) { throw "go build 失败" }

    $size = [math]::Round((Get-Item $out).Length / 1MB, 1)
    Write-Host "==> 完成: $out ($size MB)" -ForegroundColor Green
}
finally {
    Pop-Location
}
