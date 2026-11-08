package api

import (
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"mime"
	"net/http"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"guanxiang/desktop/internal/bazi"
	"guanxiang/desktop/internal/store"
)

// 本地 HTTP 接口：只监听 127.0.0.1，无账号、无外网请求。

type Server struct {
	store        *store.Store
	ui           fs.FS
	version      string
	lastPing     atomic.Int64
	quit         chan struct{}
	themeHandler func(string)
	notices      []byte
}

func New(st *store.Store, ui fs.FS, version string) *Server {
	// 让 Web App Manifest 与 .ico 以正确 MIME 提供，Chromium 才会用作品牌图标。
	_ = mime.AddExtensionType(".webmanifest", "application/manifest+json")
	_ = mime.AddExtensionType(".ico", "image/x-icon")
	s := &Server{store: st, ui: ui, version: version, quit: make(chan struct{})}
	s.lastPing.Store(time.Now().UnixNano())
	return s
}

// Quit 在窗口关闭（心跳停止）或用户主动退出时被关闭。
func (s *Server) Quit() <-chan struct{} { return s.quit }

// Ping 返回最后一次界面心跳时间。
func (s *Server) Ping() time.Time { return time.Unix(0, s.lastPing.Load()) }

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/health", s.handleHealth)
	mux.HandleFunc("GET /api/lunar-months", s.handleLunarMonths)
	mux.HandleFunc("POST /api/chart", s.handleChart)
	mux.HandleFunc("GET /api/history", s.handleHistoryList)
	mux.HandleFunc("POST /api/history", s.handleHistorySave)
	mux.HandleFunc("GET /api/history/{id}", s.handleHistoryGet)
	mux.HandleFunc("PATCH /api/history/{id}", s.handleHistoryUpdate)
	mux.HandleFunc("DELETE /api/history/{id}", s.handleHistoryDelete)
	mux.HandleFunc("GET /api/history/{id}/export", s.handleHistoryExport)
	mux.HandleFunc("GET /legal/notices.md", s.handleNotices)
	mux.HandleFunc("POST /api/theme", s.handleTheme)
	mux.HandleFunc("POST /api/ping", s.handlePing)
	mux.HandleFunc("POST /api/quit", s.handleQuit)

	fileServer := http.FileServer(http.FS(s.ui))
	mux.Handle("GET /", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, "/")
		if path == "" {
			path = "index.html"
		}
		// 所有静态资源都来自内嵌文件系统；缺失时回落到首页（单页应用）。
		if _, err := fs.Stat(s.ui, path); err != nil {
			path = "index.html"
			r = r.Clone(r.Context())
			r.URL.Path = "/index.html"
		}
		if strings.HasSuffix(path, ".html") {
			w.Header().Set("Cache-Control", "no-store")
		} else {
			w.Header().Set("Cache-Control", "public, max-age=300")
		}
		fileServer.ServeHTTP(w, r)
	}))
	return mux
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, err error) {
	writeJSON(w, status, map[string]any{"ok": false, "error": err.Error()})
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	count, _ := s.store.Count()
	writeJSON(w, http.StatusOK, map[string]any{
		"ok":          true,
		"app":         "观象桌面版",
		"version":     s.version,
		"engine":      "guanxiang-desktop/go",
		"lunar_lib":   "lunar-go v1.4.7",
		"offline":     true,
		"login":       false,
		"history_db":  s.store.Path(),
		"history_cnt": count,
	})
}

func (s *Server) handleLunarMonths(w http.ResponseWriter, r *http.Request) {
	year, err := strconv.Atoi(r.URL.Query().Get("year"))
	if err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("year 参数无效"))
		return
	}
	leap, months, err := bazi.LunarMonths(year)
	if err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "leap_month": leap, "months": months})
}

func (s *Server) handleChart(w http.ResponseWriter, r *http.Request) {
	var input bazi.Input
	if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&input); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("请求 JSON 解析失败"))
		return
	}
	chart, err := bazi.Build(input)
	if err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "chart": chart})
}

func (s *Server) handleHistoryList(w http.ResponseWriter, r *http.Request) {
	items, err := s.store.List(r.URL.Query().Get("q"))
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "items": items})
}

type saveRequest struct {
	Title string          `json:"title"`
	Note  string          `json:"note"`
	Chart json.RawMessage `json:"chart"`
}

func (s *Server) handleHistorySave(w http.ResponseWriter, r *http.Request) {
	var req saveRequest
	if err := json.NewDecoder(io.LimitReader(r.Body, 4<<20)).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("请求 JSON 解析失败"))
		return
	}
	if len(req.Chart) == 0 {
		writeError(w, http.StatusBadRequest, fmt.Errorf("缺少命盘数据"))
		return
	}
	var chart bazi.Chart
	if err := json.Unmarshal(req.Chart, &chart); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("命盘数据无法解析: %v", err))
		return
	}
	rec := store.Record{
		Title: req.Title, Note: req.Note, Solar: chart.Input.Solar, Lunar: chart.Lunar,
		Pillars: pillarString(&chart), DayMaster: chart.DayMaster, Sex: chart.Input.Sex,
		Chart: req.Chart,
	}
	if rec.Title == "" {
		rec.Title = defaultTitle(&chart)
	}
	inputJSON, _ := json.Marshal(chart.Input)
	rec.Input = inputJSON
	saved, err := s.store.Save(rec)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "item": saved})
}

func pillarString(c *bazi.Chart) string {
	var b strings.Builder
	for _, p := range c.Pillars {
		b.WriteString(p.GanZhi)
	}
	return b.String()
}

func defaultTitle(c *bazi.Chart) string {
	return c.Input.Original + " " + c.Input.Sex
}

func (s *Server) handleHistoryGet(w http.ResponseWriter, r *http.Request) {
	rec, err := s.store.Get(r.PathValue("id"))
	if err != nil {
		if store.IsNotFound(err) {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "item": rec})
}

type updateRequest struct {
	Title string `json:"title"`
	Note  string `json:"note"`
}

func (s *Server) handleHistoryUpdate(w http.ResponseWriter, r *http.Request) {
	var req updateRequest
	if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("请求 JSON 解析失败"))
		return
	}
	if strings.TrimSpace(req.Title) == "" {
		writeError(w, http.StatusBadRequest, fmt.Errorf("标题不能为空"))
		return
	}
	rec, err := s.store.Update(r.PathValue("id"), strings.TrimSpace(req.Title), req.Note)
	if err != nil {
		if store.IsNotFound(err) {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "item": rec})
}

func (s *Server) handleHistoryDelete(w http.ResponseWriter, r *http.Request) {
	err := s.store.Delete(r.PathValue("id"))
	if err != nil {
		if store.IsNotFound(err) {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

func (s *Server) handleHistoryExport(w http.ResponseWriter, r *http.Request) {
	rec, err := s.store.Get(r.PathValue("id"))
	if err != nil {
		if store.IsNotFound(err) {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	var chart bazi.Chart
	if err := json.Unmarshal(rec.Chart, &chart); err != nil {
		writeError(w, http.StatusInternalServerError, fmt.Errorf("命盘数据损坏: %v", err))
		return
	}
	format := r.URL.Query().Get("format")
	if format == "txt" {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="guanxiang-%s.txt"`, rec.ID))
		_, _ = io.WriteString(w, chart.ToText())
		return
	}
	w.Header().Set("Content-Type", "text/markdown; charset=utf-8")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="guanxiang-%s.md"`, rec.ID))
	_, _ = io.WriteString(w, chart.ToMarkdown())
}

func (s *Server) handlePing(w http.ResponseWriter, r *http.Request) {
	s.lastPing.Store(time.Now().UnixNano())
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

func (s *Server) handleQuit(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
	select {
	case <-s.quit:
	default:
		close(s.quit)
	}
}

// SetNotices 注入随包第三方声明（内容由 desktop/legal 内嵌）。
func (s *Server) SetNotices(notices []byte) { s.notices = notices }

func (s *Server) handleNotices(w http.ResponseWriter, r *http.Request) {
	if len(s.notices) == 0 {
		writeError(w, http.StatusNotFound, fmt.Errorf("未内置第三方声明"))
		return
	}
	w.Header().Set("Content-Type", "text/markdown; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(s.notices)
}

// SetThemeHandler 注册标题栏主题回调（未注册时为空操作）。
func (s *Server) SetThemeHandler(hook func(mode string)) { s.themeHandler = hook }

func (s *Server) handleTheme(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Mode string `json:"mode"`
	}
	if err := json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Errorf("请求 JSON 解析失败"))
		return
	}
	if req.Mode != "dark" && req.Mode != "light" {
		writeError(w, http.StatusBadRequest, fmt.Errorf("mode 只能是 dark 或 light"))
		return
	}
	if s.themeHandler != nil {
		s.themeHandler(req.Mode)
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "mode": req.Mode})
}
