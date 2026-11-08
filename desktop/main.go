package main

import (
	"context"
	"embed"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"

	"guanxiang/desktop/internal/api"
	"guanxiang/desktop/internal/store"
	"guanxiang/desktop/legal"
)

//go:embed ui
var uiFiles embed.FS

const appVersion = "1.0.0"

func main() {
	var (
		dataDir   = flag.String("data-dir", "", "历史数据目录（默认为用户配置目录下的 GuanXiang）")
		port      = flag.Int("port", 8791, "本地服务端口；被占用时自动改用空闲端口")
		serveOnly = flag.Bool("serve", false, "仅启动本地服务（不打开窗口），用于调试与自动化验证")
		noWindow  = flag.Bool("no-window", false, "只打印访问地址，不启动浏览器窗口")
		width     = flag.Int("width", 1440, "窗口宽度")
		height    = flag.Int("height", 900, "窗口高度")
	)
	flag.Parse()

	dbPath := *dataDir
	if dbPath == "" {
		dbPath = store.DefaultPath()
	} else {
		// 转成绝对路径：数据目录、WebView2 缓存与日志不随启动时的工作目录漂移
		if abs, err := filepath.Abs(dbPath); err == nil {
			dbPath = abs
		}
		dbPath = filepath.Join(dbPath, "guanxiang.db")
	}

	logger, closeLog := newLogger(filepath.Dir(dbPath))
	defer closeLog()
	logger.Printf("启动 观象桌面版 v%s (%s/%s)", appVersion, runtime.GOOS, runtime.GOARCH)

	st, err := store.Open(dbPath)
	if err != nil {
		fatal(logger, err)
	}
	defer st.Close()

	ui, err := fs.Sub(uiFiles, "ui")
	if err != nil {
		fatal(logger, err)
	}

	server := api.New(st, ui, appVersion)
	server.SetThemeHandler(applyTitleBarTheme)
	server.SetNotices(legal.Notices()) // 第三方许可与数据来源（随包分发，见 legal/notices.md） // 界面切换深色时同步原生标题栏；无原生窗口时为空操作
	listener, err := listen(*port)
	if err != nil {
		fatal(logger, err)
	}
	url := fmt.Sprintf("http://127.0.0.1:%d/", listener.Addr().(*net.TCPAddr).Port)

	httpServer := &http.Server{Handler: server.Handler(), ReadHeaderTimeout: 10 * time.Second}
	go func() {
		if err := httpServer.Serve(listener); err != nil && err != http.ErrServerClosed {
			logger.Printf("本地服务退出: %v", err)
		}
	}()
	logger.Printf("本地服务已就绪: %s", url)
	logger.Printf("历史库: %s", st.Path())

	shutdown := func(code int) {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		_ = httpServer.Shutdown(ctx)
		_ = st.Close()
		os.Exit(code)
	}

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-signals
		logger.Printf("收到退出信号，正在关闭")
		shutdown(0)
	}()

	if *serveOnly || *noWindow {
		fmt.Printf("观象桌面版已启动: %s\n历史库: %s\n按 Ctrl+C 退出。\n", url, st.Path())
		<-server.Quit()
		shutdown(0)
		return
	}

	// 桌面窗口：优先原生 WebView2 窗口（标题栏/任务栏使用 EXE 内嵌的品牌图标），
	// 机器缺少 WebView2 运行时时再退回 Edge/Chrome 的应用模式。
	if openNativeWindow(url, filepath.Dir(dbPath), uint(*width), uint(*height)) {
		logger.Printf("原生窗口已关闭，退出进程")
		shutdown(0)
		return
	}
	logger.Printf("未检测到可用的 WebView2 运行时，回退浏览器应用窗口")

	launched, browser := openWindow(url, filepath.Dir(dbPath), *width, *height, logger)
	if !launched {
		logger.Printf("未找到可用的 Chromium 内核浏览器，改用默认浏览器打开")
		fallbackOpen(url, logger)
	}
	logger.Printf("窗口已启动: %s (%s)", url, browser)

	// 心跳守护：界面每 4 秒 ping 一次；窗口关闭后 30 秒内无心跳则退出进程。
	started := time.Now()
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-server.Quit():
			logger.Printf("界面请求退出")
			shutdown(0)
			return
		case <-ticker.C:
			last := server.Ping()
			if last.Before(started) {
				last = started
			}
			if time.Since(last) > 30*time.Second {
				logger.Printf("界面心跳停止 %.0fs，退出进程", time.Since(last).Seconds())
				shutdown(0)
				return
			}
		}
	}
}

// listen 优先使用指定端口，占用时退回系统分配的空闲端口。
func listen(port int) (net.Listener, error) {
	ln, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", port))
	if err == nil {
		return ln, nil
	}
	ln, err = net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, fmt.Errorf("无法监听本地端口: %w", err)
	}
	return ln, nil
}

// openWindow 以 --app 模式启动 Chromium 内核浏览器窗口。
func openWindow(url, dataDir string, width, height int, logger *log.Logger) (bool, string) {
	candidates := []struct{ path, name string }{
		{filepath.Join(os.Getenv("ProgramFiles(x86)"), `Microsoft\Edge\Application\msedge.exe`), "Edge"},
		{filepath.Join(os.Getenv("ProgramFiles"), `Microsoft\Edge\Application\msedge.exe`), "Edge"},
		{filepath.Join(os.Getenv("ProgramFiles"), `Google\Chrome\Application\chrome.exe`), "Chrome"},
		{filepath.Join(os.Getenv("ProgramFiles(x86)"), `Google\Chrome\Application\chrome.exe`), "Chrome"},
		{filepath.Join(os.Getenv("LOCALAPPDATA"), `Google\Chrome\Application\chrome.exe`), "Chrome"},
	}
	profile := filepath.Join(dataDir, "ui-profile")
	for _, candidate := range candidates {
		if candidate.path == "" {
			continue
		}
		if info, err := os.Stat(candidate.path); err != nil || info.IsDir() {
			continue
		}
		cmd := exec.Command(candidate.path,
			"--app="+url,
			fmt.Sprintf("--window-size=%d,%d", width, height),
			"--user-data-dir="+profile,
			"--no-first-run",
			"--no-default-browser-check",
			"--disable-features=Translate,MediaRouter",
			"--disable-session-crashed-bubble",
			"--disable-background-networking",
		)
		if err := cmd.Start(); err != nil {
			logger.Printf("启动 %s 失败: %v", candidate.name, err)
			continue
		}
		go func() { _ = cmd.Wait() }()
		return true, candidate.name
	}
	return false, ""
}

func fallbackOpen(url string, logger *log.Logger) {
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	} else {
		cmd = exec.Command("xdg-open", url)
	}
	if err := cmd.Start(); err != nil {
		logger.Printf("打开默认浏览器失败: %v；请手动访问 %s", err, url)
	}
}

// newLogger 把运行日志写到数据目录，便于无控制台的窗口模式排查。
func newLogger(dir string) (*log.Logger, func()) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return log.New(os.Stderr, "", log.LstdFlags), func() {}
	}
	path := filepath.Join(dir, "guanxiang.log")
	if info, err := os.Stat(path); err == nil && info.Size() > 1<<20 {
		_ = os.Remove(path)
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return log.New(os.Stderr, "", log.LstdFlags), func() {}
	}
	logger := log.New(file, "", log.LstdFlags)
	return logger, func() { file.Close() }
}

func fatal(logger *log.Logger, err error) {
	logger.Printf("致命错误: %v", err)
	fmt.Fprintln(os.Stderr, strings.TrimSpace("观象桌面版启动失败: "+err.Error()))
	os.Exit(1)
}
