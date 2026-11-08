//go:build windows

package main

import (
	"path/filepath"
	"unsafe"

	webview2 "github.com/jchv/go-webview2"
	"golang.org/x/sys/windows"
)

// iconResourceID 是编译进 EXE 的图标组 ID（由 desktop/rsrc_windows_amd64.syso 提供，
// 可用 `go-winres extract` 核对，当前为 #1）。
const iconResourceID uint = 1

// nativeView 保留原生窗口句柄，供界面切换深浅色时同步标题栏。
var nativeView webview2.WebView

// openNativeWindow 用 WebView2 打开原生窗口：标题栏、任务栏与 Alt-Tab 都使用本进程
// 与 EXE 内嵌的品牌图标，不再出现浏览器图标。窗口关闭后返回（调用方随即退出进程）。
// 返回 false 表示当前机器没有可用的 WebView2 运行时，调用方应回退到浏览器窗口。
func openNativeWindow(url, dataDir string, width, height uint) bool {
	scale := displayScale()
	w := webview2.NewWithOptions(webview2.WebViewOptions{
		Debug:     false,
		AutoFocus: true,
		DataPath:  filepath.Join(dataDir, "webview2"),
		WindowOptions: webview2.WindowOptions{
			Title:  "观象 · 本地命盘",
			Width:  uint(float64(width) * scale),
			Height: uint(float64(height) * scale),
			IconId: iconResourceID,
			Center: true,
		},
	})
	if w == nil {
		return false
	}
	defer w.Destroy()
	nativeView = w
	w.Navigate(url)
	w.Run()
	nativeView = nil
	return true
}

// displayScale 返回系统 DPI 缩放（1.0 = 100%）。原生窗口的尺寸以物理像素计，
// 需要按缩放换算，才能得到与浏览器窗口一致的视觉大小。
func displayScale() float64 {
	proc := windows.NewLazySystemDLL("user32.dll").NewProc("GetDpiForSystem")
	if err := proc.Find(); err == nil {
		if dpi, _, _ := proc.Call(); dpi >= 96 {
			return float64(dpi) / 96.0
		}
	}
	return 1
}

// applyTitleBarTheme 让 Windows 标题栏跟随界面深浅色（DWM 沉浸式暗色属性）。
func applyTitleBarTheme(mode string) {
	view := nativeView
	if view == nil {
		return
	}
	dark := int32(0)
	if mode == "dark" {
		dark = 1
	}
	view.Dispatch(func() {
		hwnd := windows.HWND(uintptr(view.Window()))
		dwm := windows.NewLazySystemDLL("dwmapi.dll").NewProc("DwmSetWindowAttribute")
		// 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 10 2004+)；19 为旧版编号
		if ret, _, _ := dwm.Call(uintptr(hwnd), 20, uintptr(unsafe.Pointer(&dark)), 4); ret != 0 {
			_, _, _ = dwm.Call(uintptr(hwnd), 19, uintptr(unsafe.Pointer(&dark)), 4)
		}
	})
}
