# suno-automation

Suno AI 音樂自動化 CLI 工具。

透過 Playwright 操作 Suno 網頁，支援：

- 手動登入並保存 session
- 依風格隨機組合 prompt
- 送出歌曲生成
- 下載音訊與 metadata
- 寫入本機事件 log

---

## 目錄結構

```text
src/suno-automation/
├── config/
│   ├── settings.toml
│   └── PromptPool/
├── output/
├── suno_operation.md
├── suno_automation/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── downloader.py
│   ├── prompt_builder.py
│   ├── suno_client.py
│   └── workflow_hook.py
├── main.py
└── pyproject.toml
```

說明：

- `main.py` 是相容入口
- `suno_automation/` 是正式 Python package
- `suno_operation.md` 是維護紀錄，不是使用手冊

---

## 環境需求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

---

## 安裝

```bash
# 1. 進入專案目錄
cd src/suno-automation

# 2. 安裝依賴
uv sync

# 3. 安裝 Playwright Chromium
uv run playwright install chromium
```

---

## 設定

編輯 `config/settings.toml`：

```toml
[suno]
headless = false
generation_timeout_seconds = 300
songs_per_run = 1

[output]
download_dir = "./output"
filename_format = "{timestamp}_{title}"

[workflow]
event_log_path = "./output/events.jsonl"

[prompt]
default_style = "study_focus"

elements_per_context = 1
elements_per_mood = 1
elements_per_instrument = 2
elements_per_texture = 2
elements_per_rhythm = 1
elements_per_purpose = 1
elements_per_structure = 1
elements_per_development = 1
elements_per_ending = 1
elements_per_restriction = 2

elements_per_genre = 1
elements_per_tempo = 1
elements_per_vocal = 1

fixed_tags = ["instrumental", "no vocals"]
```

重點：

- `headless`
  - `gen` 會使用這個設定
  - `auth login` 會強制開可見瀏覽器
  - `auth status` 會強制使用 headless
- `songs_per_run`
  - 沒有帶 `--count` 時會使用這個值
  - 有帶 `--count` 時以命令列參數為主
- `prompt`
  - 預設會同時組入風格詞、用途詞、編曲結構詞、鋪陳發展詞與收尾詞
  - 目標是提升生成結果的完整度，讓前奏、發展與尾奏更容易被保留下來
- 實際下載副檔名會依 Suno 回傳格式決定，可能是 `.m4a`

---

## 使用方式

主要建議使用：

```bash
uv run suno ...
```

相容舊入口也可用：

```bash
uv run python main.py ...
```

### 首次登入

首次使用請先建立 session：

```bash
uv run suno auth login
```

登入完成後，session 會保存到：

```text
config/.browser_state.json
```

---

## CLI 指令

### `auth login`

開啟瀏覽器，手動登入 Suno，並保存 session。

```bash
uv run suno auth login
```

### `auth status`

檢查目前保存的 session 是否仍可用。

```bash
uv run suno auth status
```

### `auth clear`

刪除本機 session，強制下次重新登入。

```bash
uv run suno auth clear
```

### `gen`

生成歌曲。

```bash
# 使用 settings.toml 的預設風格與 songs_per_run
uv run suno gen

# 指定風格
uv run suno gen --style rain

# 指定完整 prompt
uv run suno gen --prompt "jazz, melancholic, piano, slow, female vocals"

# 覆蓋設定檔中的 songs_per_run
uv run suno gen --count 2

# 僅顯示 prompt，不實際生成
uv run suno gen --dry-run

# 指定其他設定檔
uv run suno gen --config ./config/settings.toml
```

說明：

- 未指定 `--prompt` 時，會依 `--style` 或 `prompt.default_style` 從 `PromptPool` 隨機組合提示詞
- 未指定 `--count` 時，會使用 `suno.songs_per_run`
- Suno 每次最多 2 首，超過也會被限制到 2

### `prompt-random`

只預覽隨機提示詞，不執行生成。

```bash
uv run suno prompt-random
uv run suno prompt-random --style night
uv run suno prompt-random --count 10
```

### `prompt`

列出目前可用的 prompt 風格。

```bash
uv run suno prompt
```

也可以使用較直覺的 alias：

```bash
uv run suno style
```

### `help` / `?`

顯示 CLI 指令說明。

```bash
uv run suno help
uv run suno ?
```

---

## 生成結果

生成成功後，工具會：

1. 下載音訊檔到 `output/`
2. 產生同名 metadata `.json`
3. 將事件追加寫入 `output/events.jsonl`

metadata 範例：

```json
{
  "filename": "20260513_220000_Rain_Glass_Chords.m4a",
  "song_id": "4d336b66-3249-4662-9542-28473d618d5d",
  "title": "Rain-Glass Chords",
  "style": "rain",
  "prompt": "pouring rain outside lofi, ...",
  "parts": {
    "context": ["pouring rain outside lofi"]
  }
}
```

事件 log 範例：

```jsonl
{"event":"suno.generation.completed","timestamp":"2026-05-13T12:00:00+00:00","songs":[...]}
```

---

## 注意事項

- `config/.browser_state.json` 包含登入狀態，不要提交到版本控制
- 首次登入請用 `auth login`，不要直接期待 `gen` 自動幫你完成登入
- `headless = true` 時，`gen` 會在背景執行，看不到瀏覽器畫面
- Suno 網頁 UI 可能改版，若某個步驟突然失效，通常是 selector 需要更新
- 下載格式不一定是 `.mp3`，目前實測可能為 `.m4a`

---

## 常見問題

### Q：`auth login` 登入後沒有保存 session？

A：先執行：

```bash
uv run suno auth status
```

若狀態失效，清掉後重新登入：

```bash
uv run suno auth clear
uv run suno auth login
```

### Q：`gen` 沒有帶 `--count` 時，會用哪個值？

A：會使用 `config/settings.toml` 裡的 `suno.songs_per_run`。

### Q：`headless` 有沒有作用？

A：有，但只對一般執行流程直接生效：

- `gen`：使用 `config` 的 `headless`
- `auth login`：固定可見瀏覽器
- `auth status`：固定 headless

### Q：生成成功了，但工具還在等？

A：目前已改成依新版 `clip-row` 與完成狀態判斷。若之後又發生，通常代表 Suno 再次改版，需要更新偵測 selector。
