package store

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

// 本地历史库：纯本地 SQLite 文件（modernc 纯 Go 驱动，无需 CGO，离线可用）。

// Record 一条排盘历史。
type Record struct {
	ID        string          `json:"id"`
	CreatedAt string          `json:"created_at"`
	UpdatedAt string          `json:"updated_at"`
	Title     string          `json:"title"`
	Note      string          `json:"note"`
	Solar     string          `json:"solar"`
	Lunar     string          `json:"lunar"`
	Pillars   string          `json:"pillars"`
	DayMaster string          `json:"day_master"`
	Sex       string          `json:"sex"`
	Input     json.RawMessage `json:"input,omitempty"`
	Chart     json.RawMessage `json:"chart,omitempty"`
}

// Summary 历史列表项（不含完整命盘，列表更快）。
type Summary struct {
	ID        string `json:"id"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
	Title     string `json:"title"`
	Note      string `json:"note"`
	Solar     string `json:"solar"`
	Lunar     string `json:"lunar"`
	Pillars   string `json:"pillars"`
	DayMaster string `json:"day_master"`
	Sex       string `json:"sex"`
}

type Store struct {
	db   *sql.DB
	path string
}

// Open 打开（或创建）历史库；目录不存在时自动创建。
func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, fmt.Errorf("创建数据目录失败: %w", err)
	}
	dsn := "file:" + filepath.ToSlash(path) + "?_pragma=busy_timeout(5000)&_pragma=journal_mode(WAL)"
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("打开历史库失败: %w", err)
	}
	db.SetMaxOpenConns(1)
	st := &Store{db: db, path: path}
	if err := st.migrate(); err != nil {
		db.Close()
		return nil, err
	}
	return st, nil
}

func (s *Store) migrate() error {
	const schema = `
CREATE TABLE IF NOT EXISTS charts (
  id          TEXT PRIMARY KEY,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  title       TEXT NOT NULL,
  note        TEXT NOT NULL DEFAULT '',
  solar       TEXT NOT NULL,
  lunar       TEXT NOT NULL,
  pillars     TEXT NOT NULL,
  day_master  TEXT NOT NULL,
  sex         TEXT NOT NULL,
  input_json  TEXT NOT NULL,
  chart_json  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_charts_created ON charts(created_at DESC);
`
	if _, err := s.db.Exec(schema); err != nil {
		return fmt.Errorf("初始化历史库失败: %w", err)
	}
	return nil
}

func (s *Store) Close() error { return s.db.Close() }

// Path 返回数据库文件路径（用于界面显示"数据保存在本机何处"）。
func (s *Store) Path() string { return s.path }

func newID() string {
	buf := make([]byte, 6)
	if _, err := rand.Read(buf); err != nil {
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return fmt.Sprintf("%s-%s", time.Now().Format("20060102-150405"), hex.EncodeToString(buf))
}

// Save 新增记录，返回带 id 与时间戳的结果。
func (s *Store) Save(rec Record) (Record, error) {
	now := time.Now().Format("2006-01-02 15:04:05")
	if rec.ID == "" {
		rec.ID = newID()
	}
	rec.CreatedAt, rec.UpdatedAt = now, now
	if strings.TrimSpace(rec.Title) == "" {
		rec.Title = strings.TrimSpace(rec.Solar + " " + rec.Sex)
	}
	if len(rec.Input) == 0 {
		rec.Input = json.RawMessage("{}")
	}
	if len(rec.Chart) == 0 {
		rec.Chart = json.RawMessage("{}")
	}
	_, err := s.db.Exec(`INSERT INTO charts
		(id, created_at, updated_at, title, note, solar, lunar, pillars, day_master, sex, input_json, chart_json)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`,
		rec.ID, rec.CreatedAt, rec.UpdatedAt, rec.Title, rec.Note, rec.Solar, rec.Lunar,
		rec.Pillars, rec.DayMaster, rec.Sex, string(rec.Input), string(rec.Chart))
	if err != nil {
		return Record{}, fmt.Errorf("保存历史失败: %w", err)
	}
	return rec, nil
}

// List 返回历史列表；query 非空时按标题/干支/农历做包含匹配。
func (s *Store) List(query string) ([]Summary, error) {
	sqlText := `SELECT id, created_at, updated_at, title, note, solar, lunar, pillars, day_master, sex FROM charts`
	args := []any{}
	if q := strings.TrimSpace(query); q != "" {
		sqlText += ` WHERE title LIKE ? OR pillars LIKE ? OR lunar LIKE ? OR note LIKE ?`
		like := "%" + q + "%"
		args = append(args, like, like, like, like)
	}
	sqlText += ` ORDER BY created_at DESC, id DESC`
	rows, err := s.db.Query(sqlText, args...)
	if err != nil {
		return nil, fmt.Errorf("读取历史失败: %w", err)
	}
	defer rows.Close()
	out := []Summary{}
	for rows.Next() {
		var item Summary
		if err := rows.Scan(&item.ID, &item.CreatedAt, &item.UpdatedAt, &item.Title, &item.Note,
			&item.Solar, &item.Lunar, &item.Pillars, &item.DayMaster, &item.Sex); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	return out, rows.Err()
}

var errNotFound = fmt.Errorf("记录不存在")

// Get 读取完整记录（含命盘 JSON）。
func (s *Store) Get(id string) (Record, error) {
	var rec Record
	var input, chart string
	err := s.db.QueryRow(`SELECT id, created_at, updated_at, title, note, solar, lunar, pillars,
		day_master, sex, input_json, chart_json FROM charts WHERE id = ?`, id).
		Scan(&rec.ID, &rec.CreatedAt, &rec.UpdatedAt, &rec.Title, &rec.Note, &rec.Solar, &rec.Lunar,
			&rec.Pillars, &rec.DayMaster, &rec.Sex, &input, &chart)
	if err == sql.ErrNoRows {
		return Record{}, errNotFound
	}
	if err != nil {
		return Record{}, err
	}
	rec.Input = json.RawMessage(input)
	rec.Chart = json.RawMessage(chart)
	return rec, nil
}

// Update 更新标题与备注。
func (s *Store) Update(id, title, note string) (Record, error) {
	now := time.Now().Format("2006-01-02 15:04:05")
	result, err := s.db.Exec(`UPDATE charts SET title = ?, note = ?, updated_at = ? WHERE id = ?`, title, note, now, id)
	if err != nil {
		return Record{}, fmt.Errorf("更新历史失败: %w", err)
	}
	affected, _ := result.RowsAffected()
	if affected == 0 {
		return Record{}, errNotFound
	}
	return s.Get(id)
}

// Delete 删除一条历史。
func (s *Store) Delete(id string) error {
	result, err := s.db.Exec(`DELETE FROM charts WHERE id = ?`, id)
	if err != nil {
		return fmt.Errorf("删除历史失败: %w", err)
	}
	affected, _ := result.RowsAffected()
	if affected == 0 {
		return errNotFound
	}
	return nil
}

// Count 返回历史条数。
func (s *Store) Count() (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM charts`).Scan(&n)
	return n, err
}

// IsNotFound 判断错误是否为记录不存在。
func IsNotFound(err error) bool { return err == errNotFound }

// DefaultPath 返回默认历史库路径（Windows: %APPDATA%\GuanXiang\guanxiang.db）。
func DefaultPath() string {
	if dir, err := os.UserConfigDir(); err == nil {
		return filepath.Join(dir, "GuanXiang", "guanxiang.db")
	}
	return filepath.Join(".", "guanxiang.db")
}
