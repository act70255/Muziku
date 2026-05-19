# Suno Operation Notes

## 目的

記錄目前已驗證可用的 Suno 登入分析與操作方式，避免後續再次踩到相同問題，並作為調整 `suno_automation/suno_client.py` 時的依據。

## 適用範圍

- `auth login`
- `auth status`
- `gen`
- Playwright 操作 Suno 登入流程
- Google OAuth 與 Suno workspace 回跳判斷

## Prompt 設計理念

目前 prompt 系統的主要目標不是單純堆疊風格形容詞，而是讓 Suno 更穩定地生成「有完整前後段、較有鋪陳、尾奏不會太急促收掉」的音樂。

### 1. 預設目標：完整度優先，其次才是長度

- 目標不是把歌曲硬拉長
- 目標是提高生成結果保有前奏、發展段、收尾段的機率
- 若只有時長變長，但內容仍像短 loop 重複，並不符合目前設計方向

### 2. prompt 應同時描述風格與曲式

目前 `PromptPool` 不只保留傳統的風格詞：

- `context`
- `mood`
- `instrument`
- `texture`
- `rhythm`
- `purpose`

也額外加入三組與完整曲式直接相關的欄位：

- `structure`
- `development`
- `ending`

這三類詞的目的如下：

- `structure`：告訴模型這不是單段循環，而是完整曲式或多段落發展
- `development`：告訴模型中段需要逐步鋪陳、層次增加、和聲或動態演進
- `ending`：告訴模型不要太快收尾，而是保留較完整的尾奏或淡出

### 3. 盡量避免過強的 loop 導向語意

像以下語意雖然適合背景音樂，但若比例過高，容易把模型推向「可循環段落」而不是「完整作品」：

- `looping feel`
- `repetitive`
- 過度強調 `stable` 但缺少段落描述

這類詞不是禁止使用，而是應避免壓過 `structure / development / ending`。

### 4. 保留背景音樂的穩定性，但不要只剩循環感

目前專案的 style 多半仍屬於：

- lofi
- focus
- sleep
- rain ambience
- cafe background
- night atmosphere

因此不能把 prompt 調成過度戲劇化或過度 cinematic，否則會破壞使用場景。

正確方向是：

- 保留穩定節奏
- 保留低干擾特性
- 但補上完整編曲與收尾語意

### 5. 預設使用單一路徑，不做標準 / 長曲雙模式

目前設計不區分 `standard` 與 `long_form` 模式。

原因：

- 使用者主要需求是讓預設輸出就更完整、更耐聽
- 若分成多模式，會增加 CLI、設定檔與詞庫維護成本
- 在目前專案規模下，單一路徑較乾淨，也較容易持續微調

### 6. 固定附加詞的角色

目前固定附加詞預設包含：

- `instrumental`
- `no vocals`

目的不是保證歌曲一定更長，而是避免模型把有限的生成預算拿去做人聲段落，讓更多空間留給編曲發展、間奏與尾奏。

### 7. 後續詞庫微調方向

若後續實測仍覺得生成結果偏短、偏像背景 loop，優先調整順序如下：

1. 先降低 `rhythm` 類別內過強的 loop 語意
2. 再提高 `structure / development / ending` 的抽樣權重
3. 最後才考慮新增更多固定附加詞

原則上不要一開始就大幅增加大量提示詞，避免 prompt 過長、語意互相衝突，反而讓模型判讀不穩。

## 目前確認可用的登入流程

1. 先進入 `https://suno.com/create`
2. 若已有有效 session，直接略過手動登入
3. 若尚未登入，導向 `https://suno.com/sign-in`
4. 使用者手動完成 Google 登入
5. 回到 Suno 頁面後，由程式輪詢目前 `browser context` 內的既有頁面
6. 判斷為已登入後，將 `storage_state` 寫入 `config/.browser_state.json`

## 目前確認可用的生成流程

1. 進入 `https://suno.com/create`
2. 確認目前頁面可見 `Advanced` / `Simple` 切換
3. 切到 `Advanced` mode
4. 在新版 style prompt 輸入區寫入風格描述
5. 記錄按下 `Create` 前已存在的 `song_id`
6. 點擊 `Create song`
7. 輪詢 `clip-row`，只接受這次新生成且狀態為 `complete` 的歌曲
8. 對每首完成歌曲點擊播放區，從 `#active-audio-play.src` 取得實際音訊 URL

## 登入完成判斷原則

目前不要只靠單一 selector 判斷是否登入成功，應使用下列綜合訊號：

1. `URL` 狀態
- 若頁面仍在 `/sign-in` 或 `/login`，視為尚未登入
- 若頁面已回到 Suno 非登入頁，可進一步檢查 UI 與 cookie

2. `頁面 UI` 狀態
- 在 `/create` 頁，優先檢查創作工作區輸入框
- 在其他 Suno 頁面，可檢查使用者頭像等登入後元素

3. `context 授權狀態`
- 檢查目前 `BrowserContext` 是否已有 Suno / Clerk 相關授權 cookie
- 若 UI selector 因版型調整未命中，但 cookie 已存在，且頁面已回到 Suno 非登入頁，可視為登入完成

## create 頁目前有效的操作重點

### 1. 不要再使用舊版 `Custom` 模式判斷

目前實測有效的是 `Advanced` / `Simple` 模式，不是舊版 `Custom`。

結論：

- 生成前先確認 `Advanced` 按鈕存在
- 寫入 style prompt 前先切到 `Advanced` mode

### 2. style prompt 已不是舊版 selector

舊版的：

- `textarea[placeholder*='style']`
- `textarea[aria-label*='Style']`
- `[data-testid='style-input']`

在新版頁面不可靠。

目前有效做法：

- 先找舊 selector 作為相容路徑
- 若找不到，從 `textarea:visible` 中排除 lyrics 欄與 simple prompt 欄
- 保留真正的 style prompt 輸入框

### 3. 新版 textarea 用 `fill()` 不穩

新版頁面存在覆蓋層或受控元件，直接 `locator.fill()` 可能找得到元素，但無法穩定寫入。

目前有效做法：

- 使用 DOM setter 寫入 `textarea.value`
- 補送 `input` / `change` 事件

### 4. Create 按鈕應使用新版 selector

目前有效 selector：

- `button[aria-label='Create song']`
- 其餘 `Create` selector 只保留作相容用途

## 已確認的踩坑

### 1. 用過寬 selector 會誤判已登入

曾經使用過於寬鬆的 `Create` 相關 selector，導致未登入頁也可能被誤判為登入成功。

影響：

- `ensure_logged_in()` 提前返回
- `async with client:` 很快結束
- 瀏覽器立刻被關閉
- `storage_state` 根本沒有寫入

結論：

- 不要把任何「未登入頁可能出現」的按鈕直接當作登入成功訊號

### 2. 背景 probe page 會干擾 Google OAuth

曾經在等待登入時額外開一個背景頁，並持續重新導向 `/create` 做探測。

影響：

- Google 登入流程在輸入帳號後可能被打斷
- 進入密碼頁後又跳回 Suno 未登入首頁

結論：

- 登入等待期間不要建立背景 probe page
- 不要在同一個 context 中反覆背景導頁測試 session
- 只觀察使用者實際登入過程中的既有頁面

### 3. 回到 workspace 不代表 selector 一定穩定

使用者可能已經成功回到 Suno workspace，但頁面 DOM 不一定包含預期 selector。

影響：

- 程式會卡在等待
- 看起來像是「已登入但沒反應」

結論：

- 需要把 cookie 狀態納入登入判斷
- URL、UI、cookie 必須一起判斷

### 4. `/create` 頁已改版，舊版 style input 會直接 timeout

舊邏輯仍假設頁面有 `Custom` 模式與舊版 `Style of Music` 輸入框，結果是進到頁面後看起來沒動作，最後卡在 `wait_for()` timeout。

結論：

- 先看目前模式是不是 `Advanced`
- 再用新版 visible textarea 規則定位 style prompt
- 不要把 simple prompt 或 lyrics 欄誤當 style prompt

### 5. 生成完成列已不是舊版 song card

舊邏輯使用：

- `[data-testid='song-card']`
- `.song-card`
- `[class*='SongCard']`

新版完成列實測為：

- `data-testid='clip-row'`
- `data-clip-status='complete'`

結論：

- 完成判斷應改成檢查 `clip-row`
- 若仍用舊版 song card selector，會一直顯示 `仍在生成中...`

### 6. 音檔 URL 不直接掛在 row 內的 `audio[src]`

新版頁面裡的 `audio` 標籤常常沒有實際歌曲 src，或只會看到靜音音訊。

目前有效做法：

- 點擊完成列中的播放區
- 從全域 `#active-audio-play.src` 讀出實際 CDN URL
- 若仍取不到，再退回 `https://cdn1.suno.ai/{song_id}.m4a`

## 目前建議的等待模型

等待登入時，應持續輪詢以下狀態：

1. `Browser` 是否仍存活
- 使用者若直接關閉瀏覽器，登入流程應終止

2. `Context` 內是否仍有開啟中的頁面
- 若所有登入相關頁面都被關閉，也應視為取消登入

3. 是否已有任何 Suno 頁面符合登入完成條件
- 任一頁面符合即可保存 session

4. 生成流程中是否已有新的完成歌曲
- 先排除按下 `Create` 前已存在的舊 `song_id`
- 只接受新的 `clip-row[data-clip-status='complete']`

對應分流：

- 已登入：保存 `storage_state`
- 尚未登入但瀏覽器仍開著：繼續等待
- 所有頁面關閉：取消登入
- 瀏覽器關閉：取消登入

生成流程分流：

- 找到新的完成歌曲：提取 `song_id / title / audio_url`
- 只有舊歌曲存在：繼續等待
- 新歌曲仍未完成：繼續等待

## 後續調整守則

未來若 Suno UI 改版，優先依這個順序排查：

1. 先看登入後回到的實際 URL
2. 再看 workspace 是否有新的穩定 selector
3. 再檢查 Suno / Clerk 授權 cookie 是否仍存在
4. 生成頁先確認 `Advanced` / `Simple` 模式有沒有改名或改結構
5. 完成列先確認 `clip-row` / `data-clip-status` 是否仍存在
6. 最後才調整等待條件與 selector

不要直接做的事：

- 不要只靠單一按鈕文字判斷登入成功
- 不要在登入等待期間背景新開分頁反覆 `goto()`
- 不要看到 workspace 沒反應就立刻延長 timeout，先檢查判斷條件是否錯
- 不要假設音訊格式永遠是 `.mp3`
- 不要把歷史歌曲誤當作本次新生成結果

## CLI 參數規劃

目前 CLI 的設計原則是：

- 常用操作優先短路徑
- 生成相關參數集中在 `gen`
- 查詢型指令盡量語意直覺
- 不把太多一次性開關塞進命令列，避免使用成本過高

### 1. 目前主要指令

- `gen`
- `prompt-random`
- `prompt`
- `style`
- `help`
- `?`
- `auth login`
- `auth status`
- `auth clear`

### 2. `gen` 參數定位

`gen` 目前保留以下核心參數：

- `--prompt`：直接指定完整 prompt，優先權最高
- `--style`：指定風格名稱，由 `PromptPool` 自動組 prompt
- `--count`：指定本次生成數量，但仍受 Suno 上限約束
- `--config`：切換設定檔
- `--dry-run`：只顯示 prompt，不實際生成

目前不把 `headless` 做成命令列參數，而是由 `config/settings.toml` 控制。

理由：

- `headless` 屬於執行環境偏好，不是歌曲內容參數
- 放在設定檔可避免每次執行都重複指定
- `auth login` 與 `auth status` 本身已經各自覆蓋對應行為

若未來需要更高彈性，可再考慮增加：

- `--headless`
- `--no-headless`

但目前不是優先需求。

### 3. 查詢型 alias 規劃

為了降低記憶成本，保留以下 alias：

- `style`：作為 `prompt` 的直覺別名，用來列出所有 style
- `help` / `?`：直接顯示 CLI 指令說明

原則是：

- alias 只加在高頻、低風險、無副作用的查詢動作
- 生成或登入這類有副作用的命令不另外做太多縮寫，避免誤操作

### 4. 後續 CLI 擴充原則

若未來要再擴充 CLI，優先順序如下：

1. 先確認需求是否能用設定檔解決
2. 若確實需要臨時覆蓋，再新增命令列參數
3. 若只是查詢或說明，再考慮加 alias

避免的方向：

- 不要把 prompt 微調細節全部暴露成 CLI 參數
- 不要讓 `gen` 同時承擔太多不常用開關
- 不要加入語意重疊的多組參數名稱

## 標準 Python Package 撰寫原則

之後若持續擴充這個專案，程式結構應維持標準 Python package 寫法，而不是往單檔腳本或零散工具函式堆疊的方向發展。

### 1. 套件結構原則

- 正式程式碼放在 `suno_automation/` package 內
- 以模組分工，而不是把所有邏輯寫進 `main.py`
- `main.py` 只保留相容入口，不作為主要實作位置
- CLI 入口由 `pyproject.toml` 的 `project.scripts` 指向 package 內的 app

目前結構方向：

- `suno_automation/cli.py`：CLI 組裝與參數入口
- `suno_automation/suno_client.py`：Suno 網頁操作
- `suno_automation/prompt_builder.py`：prompt 組裝邏輯
- `suno_automation/downloader.py`：下載與 metadata 寫入
- `suno_automation/workflow_hook.py`：流程事件通知
- `suno_automation/__main__.py`：模組執行入口

### 2. import 與入口原則

- package 內模組優先使用 package import 或相對 import
- 不要把執行路徑依賴寫死成只能用腳本方式啟動
- CLI 應可同時支援：
  - `uv run suno ...`
  - `uv run python -m suno_automation ...`
- `main.py` 只作為過渡或相容用途

### 3. 模組責任切分原則

- CLI 負責接參數、讀設定、組流程
- client 負責瀏覽器互動與 Suno 頁面操作
- builder 負責 prompt 生成規則
- downloader 負責檔案下載與 metadata
- 不要讓單一模組同時負責 CLI、業務邏輯、I/O 與網頁控制

### 4. 擴充時的寫法原則

- 新功能優先放進既有 package 模組系統
- 若責任明確，再新增新模組
- 先看是否能擴充現有類別與函式，不要急著再開一層 framework
- 保持函式與類別名稱清楚、英文命名一致

### 5. 第三方依賴原則

目前專案使用的 Python 依賴維持在最小可用集合，避免為了單一便利功能引入過多額外套件。

目前依賴：

- `playwright`
- `typer`
- `rich`
- `httpx`
- `tomllib`

原則：

- 優先使用標準庫
- 只有在明顯降低實作複雜度時才引入第三方套件
- CLI、下載、瀏覽器自動化各自只保留一套主要工具

### 6. 環境層需求

除了 package 結構本身，執行上還需要：

- Python 3.11+
- `uv`
- Playwright Chromium 瀏覽器執行檔

對應安裝步驟：

- `uv sync`
- `uv run playwright install chromium`

## 建議的手動驗證指令

```powershell
uv run .\main.py auth login
uv run .\main.py auth status
uv run .\main.py gen --style rain
uv run suno auth login
uv run suno auth status
uv run suno gen --style rain
```

## 目前相關程式位置

- `suno_automation/cli.py`
- `suno_automation/suno_client.py`
- `config/.browser_state.json`

## 備註

這份文件主要記錄「處理方式」與「判斷邏輯」，不是使用說明文件。
若未來要更新正式操作手冊，應另外同步更新 `suno-automation.md`。
