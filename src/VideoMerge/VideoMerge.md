# VideoMerge

## 目的

`VideoMerge` 是一個以 `Python + ffmpeg/ffprobe` 為核心的 CLI 工具，用來把：

- 一張圖片
- 多個 `m4a` 音檔

合併成一支長影片，並同時產出可貼到 YouTube 說明欄的章節檔。

## 執行方式

目前主要使用方式：

```powershell
uv run .\main.py <command> [options]
```

例如：

```powershell
uv run .\main.py help
uv run .\main.py template
uv run .\main.py probe .\music
uv run .\main.py build --image .\cover.jpg --audio-dir .\music --output .\output.mp4
```

## 環境需求

- Python 3.11+
- `uv`
- `ffmpeg`
- `ffprobe`

若系統找不到 `ffmpeg` 或 `ffprobe`，請：

1. 安裝它們並加入系統 `PATH`
2. 或在 `config/settings.toml` 中設定完整路徑

## 安裝 ffmpeg / ffprobe

### Windows 建議安裝方式

建議優先使用系統套件管理工具安裝，這樣通常會一起安裝 `ffmpeg` 與 `ffprobe`。

#### 方式 1：使用 winget

```powershell
winget install Gyan.FFmpeg
```

#### 方式 2：使用 Chocolatey

```powershell
choco install ffmpeg
```

#### 方式 3：使用 Scoop

```powershell
scoop install ffmpeg
```

### 安裝完成後驗證

請先在終端機檢查：

```powershell
ffmpeg -version
ffprobe -version
```

若兩個指令都能正常顯示版本資訊，代表安裝完成，`VideoMerge` 就能直接使用系統 `PATH` 中的執行檔。

## 設定 ffmpeg / ffprobe 路徑

若你不想依賴系統 `PATH`，或安裝位置不是預設路徑，可以直接在 `config/settings.toml` 中指定完整路徑。

範例：

```toml
[ffmpeg]
binary = "C:/ffmpeg/bin/ffmpeg.exe"
probe_binary = "C:/ffmpeg/bin/ffprobe.exe"
overwrite_output = true
```

注意：

1. Windows 路徑建議使用 `/`，避免跳脫字元問題
2. `binary` 對應 `ffmpeg.exe`
3. `probe_binary` 對應 `ffprobe.exe`

如果你已經把 `ffmpeg` 與 `ffprobe` 加到系統 `PATH`，則可保留預設值：

```toml
[ffmpeg]
binary = "ffmpeg"
probe_binary = "ffprobe"
overwrite_output = true
```

## 設定檔

設定檔位置：

```text
config/settings.toml
```

目前主要設定區段：

- `[ffmpeg]`：`ffmpeg` / `ffprobe` 執行檔
- `[audio]`：音訊標準化、位元率、是否預設正規化
- `[video]`：解析度、FPS、CRF、編碼設定
- `[output]`：中介檔與章節檔輸出位置
- `[template]`：預設模板與模板參數

## 指令

### help

顯示 CLI 說明。

```powershell
uv run .\main.py help
```

### template

列出目前可用的視覺模板。

```powershell
uv run .\main.py template
```

目前支援：

- `static`
- `ken-burns`
- `pan`
- `waveform`

### probe

探測單一 `m4a` 檔，或整個資料夾內的 `m4a`。

```powershell
uv run .\main.py probe .\music
uv run .\main.py probe .\music\01-track.m4a
```

輸出資訊包含：

- `codec`
- `sample_rate`
- `channels`
- `duration`

### build

將圖片與多個 `m4a` 合併成 `mp4`。

```powershell
uv run .\main.py build --image .\cover.jpg --audio-dir .\music --output .\output.mp4
```

常用參數：

- `--image`：主視覺圖片路徑
- `--audio-dir`：音檔資料夾
- `--output`：輸出 `mp4` 路徑
- `--template`：指定模板
- `--normalize-audio`：啟用 `loudnorm`
- `--no-normalize-audio`：停用 `loudnorm`
- `--dry-run`：只顯示計畫執行的命令
- `--config` / `-c`：指定設定檔路徑

範例：

```powershell
uv run .\main.py build --image .\cover.jpg --audio-dir .\music --output .\output.mp4 --template ken-burns
uv run .\main.py build --image .\cover.jpg --audio-dir .\music --output .\output.mp4 --normalize-audio
uv run .\main.py build --image .\cover.jpg --audio-dir .\music --output .\output.mp4 --dry-run
```

## 輸出內容

`build` 完成後，會產出：

1. 最終影片，例如 `output.mp4`
2. 合併後主音軌的中介檔
3. 標準化後音檔與 concat manifest
4. YouTube 章節檔，例如 `output.chapters.txt`

章節檔格式範例：

```text
0:00 01 First Song
3:42 02 Night Drive
7:15 03 Rain Window
```

章節標題目前直接使用音檔檔名去掉副檔名後的文字。

## 目前限制

- MVP 目前只支援 `m4a`
- 圖片格式以 `.jpg`、`.jpeg`、`.png`、`.webp` 為主
- YouTube 章節目前是輸出文字檔，不是直接嵌入平台章節

## 建議操作順序

1. 先確認 `ffmpeg` / `ffprobe` 可用
2. 用 `template` 看可用模板
3. 用 `probe` 檢查音檔資訊
4. 先跑一次 `build --dry-run`
5. 再執行正式 `build`
