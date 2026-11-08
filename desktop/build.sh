#!/usr/bin/env bash
# 观象桌面版 · 构建脚本（Windows 目标，可在 Git Bash / WSL / Linux 交叉构建）
# 用法：bash build.sh
set -euo pipefail
cd "$(dirname "$0")"

export CGO_ENABLED=0
mkdir -p build

# Windows 资源（图标 + 版本信息）：缺失或图标较新时重建，避免 EXE 沿用旧图标
if [ ! -f rsrc_windows_amd64.syso ] || [ ui/brand/icon.ico -nt rsrc_windows_amd64.syso ]; then
  echo "==> 生成 Windows 资源 (rsrc_windows_amd64.syso)"
  go run github.com/tc-hib/go-winres@latest simply --arch amd64 --out rsrc     --icon ui/brand/icon.ico --manifest gui     --product-name "观象桌面版" --file-description "观象 · 纯本地四柱排盘客户端"     --file-version 1.0.0.0 --product-version 1.0.0.0 --original-filename "观象.exe"     --copyright "本地离线使用，仅供文化研究与娱乐"
fi

echo "==> go vet"
go vet ./...
echo "==> go test"
go test ./...
echo "==> go build"
go build -trimpath -ldflags "-s -w -H windowsgui" -o "build/观象.exe" .

echo "==> 完成: build/观象.exe ($(du -h 'build/观象.exe' | cut -f1))"
