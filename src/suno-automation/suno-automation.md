# suno-automation

Suno AI 音樂自動化生成工具，使用 Playwright 瀏覽器自動化操作 Suno 網頁，搭配隨機 Prompt 元素庫產出音樂並下載至本機，可串接外部工作流系統。

---

## 目錄結構

```
src/suno-automation/
├── config/
│   ├── settings.toml          # 主要設定檔（帳號、路徑、Webhook 等）
│   └── prompt_elements.json   # Prompt 元素庫（風格、情緒、樂器等）
├── src/
│   ├── prompt_builder.py      # 隨機組合提示詞
│   ├── suno_client.py         # Playwright 瀏覽器自動化
│   ├── downloader.py          # 音訊下載至本機
│   └── workflow_hook.py       # 工作流通知（Webhook / 本機事件 log）
├── output/                    # 下載音樂預設存放位置
├── main.py                    # CLI 入口
└── pyproject.toml
```

---

## 環境需求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 套件管理工具

---

## 安裝步驟

```bash
# 1. 進入專案目錄
cd src/suno-automation

# 2. 初始化虛擬環境並安裝依賴
uv sync

# 3. 安裝 Playwright 瀏覽器核心（Chromium）
uv run playwright install chromium
```

---

## 設定

### 1. 編輯 `config/settings.toml`

開啟檔案並依照說明填入設定值：

```toml
[suno]
email = "your@email.com"      # 你的 Suno 帳號 Email
login_method = "google"        # 登入方式：google | discord | apple | email
headless = false               # false = 顯示瀏覽器視窗（首次登入建議保持 false）
generation_timeout_seconds = 300
songs_per_run = 2

[output]
download_dir = "./output"      # 音樂下載目錄（絕對或相對路徑皆可）
filename_format = "{timestamp}_{title}"

[workflow]
event_log_path = "./output/events.jsonl"

[prompt]
# 預設風格；可用值：study_focus | sleep_relax | work_home | rain | cafe | night
default_style = "study_focus"

# 風格特化格式（PromptPool）
elements_per_context = 1
elements_per_mood = 1
elements_per_instrument = 2
elements_per_texture = 2
elements_per_rhythm = 1
elements_per_purpose = 1
elements_per_restriction = 2

# 通用格式（prompt_elements.json）
elements_per_genre = 1
elements_per_tempo = 1
elements_per_vocal = 1

# 每次都附加的固定標籤
fixed_tags = ["no vocals"]
```

### 2. 自訂 Prompt 元素庫（選填）

編輯 `config/prompt_elements.json`，可在各類別（`genre`、`mood`、`instrument`、`tempo`、`vocal`、`production`）中新增、刪除或修改元素：

```json
{
  "genre": ["pop", "rock", "jazz", "..."],
  "mood": ["upbeat", "melancholic", "..."],
  "instrument": ["piano", "guitar", "..."],
  "tempo": ["slow", "mid-tempo", "fast"],
  "vocal": ["female vocals", "no vocals", "..."],
  "production": ["lo-fi", "polished", "..."]
}
```

---

## 使用方式

### 首次執行（需要手動登入）

建議先使用 `auth login` 完成一次登入。程式會開啟瀏覽器視窗，請手動完成 Suno 登入。登入成功後，session 會自動儲存至 `config/.browser_state.json`，後續 `gen` 指令會直接重用這份登入狀態。

```bash
uv run python main.py auth login
```

### CLI 指令一覽

#### `auth login` — 手動登入並保存 session

```bash
# 開啟瀏覽器完成登入，保存 Suno session
uv run python main.py auth login
```

#### `auth status` — 檢查目前登入狀態

```bash
# 檢查本機保存的登入狀態是否仍可用
uv run python main.py auth status
```

#### `auth clear` — 清除登入狀態

```bash
# 刪除本機保存的登入狀態，強制下次重新登入
uv run python main.py auth clear
```

#### `gen` — 生成音樂

```bash
# 使用預設風格隨機組合提示詞生成 2 首（預設）
uv run python main.py gen

# 指定風格
uv run python main.py gen --style rain

# 指定提示詞（指定後不再走隨機風格組合）
uv run python main.py gen --prompt "jazz, melancholic, piano, slow, female vocals"

# 指定生成數量（最多 2）
uv run python main.py gen --count 1

# 僅預覽提示詞，不實際執行
uv run python main.py gen --dry-run

# 指定設定檔路徑
uv run python main.py gen --config /path/to/my_settings.toml
```

說明：

- 未指定 `--prompt` 時，CLI 會依 `--style` 對應的 PromptPool 風格元素庫隨機組合提示詞
- 未指定 `--style` 時，會使用 `settings.toml` 中的 `prompt.default_style`
- 若 `--style` 不存在，程式會退回隨機挑選一個可用風格

#### `prompt-random` — 預覽隨機提示詞

```bash
# 預覽 5 組隨機提示詞（預設）
uv run python main.py prompt-random

# 指定風格預覽
uv run python main.py prompt-random --style night

# 預覽 10 組
uv run python main.py prompt-random --count 10
```

#### `prompt` — 列出可用風格

```bash
# 列出目前 PromptPool 中所有可用風格與說明
uv run python main.py prompt
```

---

## 工作流串接

### 方式 A：本機事件 log（JSONL）

預設啟用。每次生成完成後，會在 `output/events.jsonl` 追加一行 JSON 事件記錄：

```jsonl
{"event": "suno.generation.completed", "timestamp": "2026-05-12T10:00:00+00:00", "songs": [...]}
```

你的工作流系統可輪詢此檔案，或使用 `watchdog` 等套件監聽檔案變更。

事件 payload 結構：

```json
{
  "event": "suno.generation.completed",
  "timestamp": "ISO8601 時間戳",
  "songs": [
    {
      "title": "歌曲標題",
      "song_id": "Suno 歌曲 ID",
      "audio_url": "音訊 URL",
      "prompt": "使用的提示詞",
      "local_path": "本機下載路徑"
    }
  ]
}
```

### 方式 B：HTTP Webhook

目前程式尚未實作 HTTP Webhook 傳送；現階段僅支援本機 `JSONL` 事件 log。

若後續要補上 Webhook，建議以 `workflow_hook.py` 為延伸點，新增 `POST` 通知實作，而不是直接依賴本文件中的舊設定欄位。

---

## 注意事項

| 項目 | 說明 |
|------|------|
| **登入 session** | 儲存於 `config/.browser_state.json`，建議先用 `auth login` 建立；請勿提交至版本控制 |
| **headless 模式** | 首次登入建議設為 `false`（顯示視窗）；session 儲存後可改為 `true` |
| **選擇器穩定性** | Suno 網頁改版可能導致 `suno_client.py` 中的 CSS 選擇器失效，需手動更新 |
| **每月額度** | Pro 方案每月 2,500 Credits，每首歌約消耗 10 Credits，請注意用量 |
| **ToS 風險** | 瀏覽器自動化屬灰色地帶，使用前請自行評估帳號風險 |

---

## 常見問題

**Q：登入後還是跳到登入頁面？**  
A：先執行 `uv run python main.py auth status` 檢查 session 是否仍有效。若已失效，執行 `uv run python main.py auth clear` 後，再用 `uv run python main.py auth login` 重新登入。

**Q：生成逾時（TimeoutError）？**  
A：增加 `settings.toml` 中的 `generation_timeout_seconds` 值，或確認 Suno 服務狀態。

**Q：找不到歌曲卡片（songs 為空）？**  
A：Suno 網頁可能已更新，需檢查並更新 `src/suno_client.py` 中的 CSS 選擇器。
