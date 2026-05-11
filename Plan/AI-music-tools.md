# AI 音樂工具比較

[README.md](./README.md)
[plan-technical.md](./plan-technical.md)

## 目標

整理目前主流 AI 音樂服務，從 `YouTube 廣告分潤適配度`、`授權清晰度`、`Lo-fi 長影片適配度` 與 `實務風險` 四個角度，選出最適合本專案的候選工具。

## 結論摘要

### 建議優先序

1. `AIVA Pro`
2. `Suno Pro / Premier`
3. `Loudly`
4. `SOUNDRAW`

### 不建議直接當主力

- `Beatoven`
- `Mubert`
- `Udio`

## 快速比較表

| 服務 | YouTube 營利適配 | 授權清晰度 | Lo-fi 長影片適配 | 主要風險 | 建議 |
|---|---|---|---|---|---|
| `AIVA Pro` | 高 | 高 | 中高 | 單段長度較短，需要自行拼接 | 穩健主力 |
| `Suno Pro / Premier` | 中高 | 中 | 高 | 同質化、AI 輸出權利不保證完整成立 | 快速 MVP 主力 |
| `Loudly` | 中高 | 中 | 中 | 權利多為授權，不適合當完整自有音樂 IP | 候補 |
| `SOUNDRAW` | 中高 | 中 | 中 | Lo-fi / Relaxation 類型需特別看授權條件 | 條件式候補 |
| `Beatoven` | 中 | 中 | 低 | 更偏配樂用途，限制較多 | 不建議主力 |
| `Mubert` | 中 | 中低 | 低 | Content ID、發行與功能型頻道用途限制多 | 不建議主力 |
| `Udio` | 低 | 低 | 中 | 官方靜態條款對商用與平台發布偏保守 | 暫不建議 |

## 逐項分析

### AIVA

- 方案觀察：官方公開頁面可確認 `Free`、`Standard`、`Pro` 三類主方案
- 授權重點：
  - `Free` 不可營利
  - `Standard` 主打可在 YouTube、Twitch、TikTok、Instagram 等社群平台營利
  - `Pro` 主打 `Copyright owned by YOU` 與 `Full monetization`
- 優點：
  - 權利敘述相對清楚
  - 比較適合做長期可持續經營
  - 對需要保存權利證據的經營模式友善
- 缺點：
  - 每首長度有限
  - 做 45 到 90 分鐘影片仍需自行重組
- 建議：
  - 若你重視合規與長期穩定，`AIVA Pro` 很適合當主力

### Suno

- 方案觀察：官方 pricing 頁可確認 `Free`、`Pro`、`Premier`
- 授權重點：
  - `Free` 明確標示 `No commercial use`
  - `Pro / Premier` 明確標示 `Commercial use rights for new songs made`
  - 官方條款顯示，付費期間生成之 output 會有權利讓與邏輯，但不保證每個 output 都一定成立著作權
- 優點：
  - 生成速度快
  - 適合快速做題材測試
  - 很適合做情境式 Lo-fi 素材池
- 缺點：
  - 風格容易撞型
  - 需額外人工做品質控管與長片編排
- 建議：
  - 若你要先衝產量與驗證題材，`Suno Pro` 是高效率首選

### Loudly

- 方案觀察：官方頁面明確主打 AI 音樂、social media、streaming 與創作者用途
- 授權重點：
  - 付費授權可將音樂整合到影音專案並在 YouTube 等平台營利
  - 不可對其輸出主張 `YouTube Content ID`
  - 串流平台發行需透過 Loudly 自家的 distribution 服務
  - 平台保留較多 output 權利，本質偏使用授權
- 優點：
  - 很適合影音創作者工作流
  - 對社群與影音平台用途描述清楚
- 缺點：
  - 不適合把輸出視為完整自有音樂資產
- 建議：
  - 適合當 `YouTube 專用型` 候補工具

### SOUNDRAW

- 方案觀察：Creator 與 Artist 類型方案清楚，並主打可商用與可營利
- 授權重點：
  - 官方頁面強調商用安全與 worldwide perpetual license
  - 但 license 頁特別指出 `Meditation / Lo-Fi / Relaxation Content` 類型若直接使用原始下載版本，發布條件需注意是否與訂閱狀態綁定
  - 若要上 DSP，通常需經過明顯修改，而不是直接原封不動發行
- 優點：
  - 可調整長度、結構與 stem
  - 適合需要做後製編排的人
- 缺點：
  - 剛好與本專案目標類型高度重疊，因此授權要特別審慎
- 建議：
  - 可用，但不能在未驗證授權前直接當主力

### Beatoven

- 方案觀察：偏向內容創作者背景配樂場景
- 授權重點：
  - 官方頁面提到 `exclusive music license`
  - 但同時明示不可 resale、不可 register、不可 distribute 到 streaming platforms
- 優點：
  - 背景配樂用途明確
  - 成本結構容易理解
- 缺點：
  - 不適合把音樂本身當主內容產品
- 建議：
  - 不建議作為 Lo-fi 長影片頻道主力

### Mubert

- 方案觀察：偏向 royalty-free 背景音與生成式配樂服務
- 授權重點：
  - 官方 pricing 頁明寫不授權用於 `Content ID`
  - 不可作為串流平台的獨立正式發行內容
  - FAQ 甚至有 `YouTube functional music channel` 類問題，代表這類用法本身就是敏感場景
- 優點：
  - 功能型與背景音場景清楚
- 缺點：
  - 對你要做的長時數 Lo-fi 頻道不是理想型
- 建議：
  - 除非拿到明確書面授權，不建議作為主力

### Udio

- 方案觀察：官方頁面重度動態載入，未登入時可可靠讀到的資訊有限
- 授權重點：
  - 我目前從官方靜態條款可確認的內容偏保守
  - 現有可見條款傾向不鼓勵商用、平台發布與對 output 主張所有權
  - 付費方案例外授權是否存在，單靠靜態頁面無法可靠確認
- 優點：
  - 生成品質與市場聲量高
- 缺點：
  - 權利與商用風險過高
- 建議：
  - 在沒有進一步逐條驗證前，不應放進主線營利流程

## 推薦選型策略

### 策略 A：穩健經營

- 主力：`AIVA Pro`
- 輔助：`Suno Pro`
- 適用情境：
  - 優先追求授權穩定與長期可持續性
  - 願意自己做較多片段拼接與品質控管

### 策略 B：快速驗證

- 主力：`Suno Pro / Premier`
- 輔助：`AIVA Pro` 或 `Loudly`
- 適用情境：
  - 優先追求上片速度
  - 目標是在 30 到 60 天內快速找出高表現題材

## 最適合現在起步的工具組合

若以你目前的目標來看，最實際的起步方式不是一次買很多服務，而是先建立 `1 個高效率主力 + 1 個穩健備援 + 1 套固定製作流程`。

### 起步首選組合

- 音樂主力：`Suno Pro`
- 音樂備援：`AIVA Pro`
- 縮圖與封面：`Canva` 或任何你熟悉的靜態設計工具
- 長影片組裝：`DaVinci Resolve`、`CapCut Desktop` 或任何可做長片輸出的剪輯工具
- 素材追蹤：`Google Sheets`、`Notion` 或本機表格檔

### 為什麼這樣配

- `Suno Pro` 負責速度與大量測題材
- `AIVA Pro` 負責在你需要較穩健授權邏輯時補位
- 靜態封面足夠支撐 MVP，不必一開始做複雜動畫
- 表格追蹤可降低未來授權追溯與素材混亂風險

### 不建議的起步方式

- 不要一開始同時訂閱 4 到 5 個 AI 音樂平台
- 不要先投資高成本動態視覺或直播系統
- 不要在沒有數據前先做大量外包

## 每週建議節奏

以下節奏適合 `每週 3 支長影片` 的 MVP 模式。

### 星期 1：選題與 prompt 準備

1. 選出本週 3 個情境題材
2. 每個題材準備 3 到 5 組 prompt 變體
3. 定義每支影片的目標長度，例如 45 分鐘、60 分鐘、90 分鐘

### 星期 2：批次生成音樂

1. 用 `Suno Pro` 為每個題材生成 8 到 12 段候選片段
2. 把可用片段記錄到素材表
3. 若某題材生成品質不穩，再用 `AIVA Pro` 補候選素材

### 星期 3：篩選與長片編排

1. 每個題材保留 6 到 10 段可用音樂
2. 依照情緒與節奏排序
3. 組成 1 支 45 到 90 分鐘的長影片音軌

### 星期 4：封面、上架與複盤

1. 製作 3 張系列化縮圖
2. 寫標題、描述與播放清單分類
3. 上傳並排程
4. 更新追蹤表，記錄使用工具、方案、發布日期與觀察指標

## 單支影片實際操作流程

以下流程以 `60 分鐘 Lo-fi Study` 類型為例。

### Step 1：定義情境

- 題材名稱：`Rainy Night Study Lo-fi`
- 使用目的：讀書、專注、夜間陪伴
- 情緒關鍵字：calm、warm、soft drums、vinyl texture、late night

### Step 2：準備生成 prompt

- 主 prompt 應固定核心情境
- 每次只微調 1 到 2 個變數，例如節奏、樂器、氛圍
- 不要每次都完全重寫，否則難以比較結果

#### Prompt 結構

建議用這個格式組：

`情境 + 使用目的 + 情緒 + 樂器 + 節奏描述 + 質感關鍵字`

示例結構：

`late night study lofi, calm and focused mood, soft drums, warm piano, mellow bass, vinyl texture, gentle rain ambience, for deep concentration`

#### 可直接使用的 prompt 範本

1. `late night study lofi, calm and focused mood, soft drums, warm piano, mellow bass, vinyl texture, gentle rain ambience, for deep concentration`
2. `rainy cafe lofi, cozy and warm mood, jazz chords, soft kick and snare, mellow electric piano, light vinyl crackle, for reading and studying`
3. `deep focus coding lofi, minimal and steady groove, clean piano motif, soft bass, subtle drums, no sudden changes, for long work sessions`
4. `midnight library lofi, quiet and introspective mood, dusty piano, soft percussion, warm tape texture, smooth looping feel, for study and concentration`
5. `morning desk chill lofi, fresh and peaceful mood, bright keys, soft beat, light bassline, clean atmosphere, for relaxed productivity`
6. `lofi beats for exams, steady rhythm, soft drums, warm piano chords, subtle ambient texture, emotionally neutral, designed for long study sessions`

#### Suno 分組 prompt 範例

##### Group 1：讀書 / 專注

1. `late night study lofi, calm and focused mood, soft drums, warm piano, mellow bass, vinyl texture, steady and smooth, for deep concentration`
2. `deep focus study lofi, minimal groove, soft piano chords, subtle bass, light vinyl crackle, no sudden changes, for long study sessions`
3. `midnight library lofi, quiet and focused mood, dusty piano, soft percussion, tape warmth, smooth looping feel, for exam preparation`
4. `lofi beats for studying, emotionally neutral mood, warm keys, soft kick and snare, gentle ambient texture, consistent rhythm, for concentration`
5. `calm desk study lofi, soft jazz harmony, mellow piano, subtle drums, warm tape texture, stable and repetitive, for reading and focus`

###### Group 1 關鍵元素

- 情境詞：`study desk`、`library`、`exam prep`、`late night study`
- 用途詞：`for concentration`、`for studying`、`for exam preparation`、`for deep focus`
- 情緒詞：`focused`、`calm`、`neutral`、`steady`
- 樂器詞：`warm piano`、`soft keys`、`mellow bass`、`subtle drums`
- 質感詞：`vinyl texture`、`light crackle`、`tape warmth`
- 節奏詞：`steady and smooth`、`consistent rhythm`、`minimal groove`

###### Group 1 限制詞

- `no vocals`
- `no dramatic transitions`
- `no aggressive drums`
- `no sudden drop`
- `keep the mood stable`

##### Group 2：睡前放鬆

1. `sleepy night lofi, deeply calm mood, soft piano, mellow bass, very gentle drums, warm ambience, slow and soothing, for bedtime relaxation`
2. `late night relax lofi, peaceful and dreamy mood, soft electric piano, subtle percussion, tape warmth, no harsh transitions, for winding down`
3. `moonlight bedroom lofi, quiet and sleepy mood, warm keys, soft vinyl texture, gentle bassline, minimal rhythm, for sleep and relaxation`
4. `soft lofi for bedtime, calm and cozy mood, mellow piano chords, light ambient texture, very smooth groove, no dramatic changes`
5. `midnight calm lofi, dreamy atmosphere, soft pads, warm piano, subtle tape hiss, slow gentle beat, for deep relaxation before sleep`

###### Group 2 關鍵元素

- 情境詞：`bedroom`、`moonlight`、`late night relax`、`sleepy night`
- 用途詞：`for bedtime relaxation`、`for winding down`、`for sleep and relaxation`
- 情緒詞：`deeply calm`、`dreamy`、`sleepy`、`peaceful`
- 樂器詞：`soft piano`、`soft pads`、`gentle bassline`、`very gentle drums`
- 質感詞：`warm ambience`、`soft vinyl texture`、`subtle tape hiss`
- 節奏詞：`slow and soothing`、`minimal rhythm`、`very smooth groove`

###### Group 2 限制詞

- `no bright lead melody`
- `no strong snare`
- `no energetic rhythm`
- `no sudden volume jump`
- `keep it soft and sleepy`

##### Group 4：下雨 / 咖啡廳 / 夜晚

1. `rainy cafe lofi, cozy and warm mood, jazz chords, soft kick and snare, mellow electric piano, vinyl crackle, for reading and studying`
2. `rainy window night lofi, melancholic but calm mood, electric piano, soft vinyl noise, mellow drums, gentle ambience, perfect for reading`
3. `city lights night lofi, dreamy and calm mood, mellow synth keys, soft beat, vinyl crackle, smooth bass, for late night focus`
4. `night cafe lofi, warm and intimate mood, soft jazz piano, subtle bass, brushed drums, tape warmth, smooth and steady, for quiet work`
5. `rainy street midnight lofi, reflective mood, dusty piano, soft percussion, gentle rain ambience, warm low bass, for calm night sessions`

###### Group 4 關鍵元素

- 情境詞：`rainy cafe`、`rainy window`、`city lights night`、`night cafe`、`rainy street midnight`
- 用途詞：`for reading`、`for quiet work`、`for late night focus`、`for calm night sessions`
- 情緒詞：`cozy`、`warm`、`dreamy`、`reflective`、`melancholic but calm`
- 樂器詞：`electric piano`、`soft jazz piano`、`mellow synth keys`、`brushed drums`
- 質感詞：`vinyl crackle`、`soft vinyl noise`、`tape warmth`、`gentle rain ambience`
- 節奏詞：`smooth and steady`、`soft beat`、`mellow drums`

###### Group 4 限制詞

- `no harsh percussion`
- `no fast tempo`
- `no crowded arrangement`
- `no intense climax`
- `keep the rainy night mood consistent`

#### Suno 重要元素字庫

- 情境：`late night study`、`rainy cafe`、`midnight library`、`cozy room`、`city lights night`、`rainy window`
- 用途：`for studying`、`for reading`、`for deep work`、`for concentration`、`for long work sessions`
- 情緒：`calm`、`cozy`、`peaceful`、`dreamy`、`melancholic`、`focused`
- 樂器：`warm piano`、`electric piano`、`dusty piano`、`mellow bass`、`soft drums`、`brushed drums`
- 質感：`vinyl texture`、`vinyl crackle`、`tape warmth`、`tape hiss`、`gentle rain ambience`
- 穩定限制：`steady and smooth`、`minimal and steady groove`、`no sudden changes`、`smooth looping feel`、`consistent rhythm`

#### Suno 自行組合公式

`[情境], [情緒], [樂器], [質感], [節奏限制], [用途]`

示例：

`cozy room study lofi, peaceful mood, warm piano, soft drums, vinyl crackle, no sudden changes, for concentration`

#### 30 / 60 / 120 分鐘 prompt 寫法差異

同一個題材在做不同長度素材時，prompt 應該強調不同重點。

##### 30 分鐘版本

- 適合：較容易保留一點旋律記憶點與情緒起伏
- 關鍵詞：`gentle variation`、`light melodic movement`、`soft progression`
- 寫法重點：可以允許少量變化，但仍要避免突然轉折
- 示例：
  - `late night study lofi, calm and focused mood, warm piano, soft drums, vinyl texture, gentle variation, soft progression, for a 30 minute focus session`

##### 60 分鐘版本

- 適合：主力長影片長度，最平衡
- 關鍵詞：`steady and smooth`、`consistent rhythm`、`stable mood`
- 寫法重點：情緒穩定優先，旋律不要太搶
- 示例：
  - `late night study lofi, calm and focused mood, warm piano, mellow bass, soft drums, vinyl texture, steady and smooth, consistent rhythm, stable mood for a 60 minute study session`

##### 120 分鐘版本

- 適合：超長背景播放，但最怕疲勞與突兀
- 關鍵詞：`minimal`、`repetitive but soothing`、`no dramatic changes`、`long-form consistency`
- 寫法重點：降低旋律存在感，強調長時間穩定與不打擾
- 示例：
  - `late night study lofi, minimal and calming mood, soft piano, subtle bass, very gentle drums, vinyl texture, repetitive but soothing, no dramatic changes, long-form consistency for a 120 minute concentration session`

##### 長度調整原則

- `30 分鐘`：可保留少量情緒推進
- `60 分鐘`：以穩定、耐聽、低干擾為主
- `120 分鐘`：優先降低存在感與情緒波動
- 長度越長，越要增加 `steady`、`minimal`、`consistent`、`no dramatic changes` 這類詞

#### 變體調整方式

每次只改一到兩個元素：

- 情境：`rainy cafe`、`night room`、`library`、`city window`
- 使用目的：`for studying`、`for reading`、`for deep work`、`for concentration`
- 情緒：`calm`、`cozy`、`melancholic`、`peaceful`
- 樂器：`warm piano`、`electric piano`、`soft guitar`、`dusty keys`
- 質感：`vinyl texture`、`tape warmth`、`soft ambience`、`rain sound`

#### 實務原則

- 先固定 1 套核心 prompt，再做小幅變體
- 避免一次塞太多互相衝突的形容詞
- Suno 若沒有獨立 negative prompt 欄位，可直接把限制詞寫進主 prompt，例如 `no vocals, no dramatic transitions, keep the mood stable`
- 若平台支援 negative prompt，排除 `harsh transitions`、`aggressive drums`、`sudden drop`
- 若要做長影片素材，優先使用 `steady`、`smooth`、`minimal`、`consistent` 這類詞

### Step 3：批次生成候選素材

- 先生成 8 到 12 段
- 每段目標 2 到 5 分鐘
- 立即淘汰有明顯突兀、異音、情緒錯位的片段

### Step 4：做第一次篩選

保留片段時只看四件事：

1. 是否適合長時間播放
2. 是否與情境一致
3. 是否能和其他段落自然相接
4. 是否沒有明顯 AI 失真

### Step 5：編排成長片

- 先排開場：前 30 秒要容易進入狀態
- 中段保持穩定，不要突然切成完全不同情緒
- 尾段可再收得更柔和，讓整體播放更完整
- 必要時加極短淡入淡出，但不要過度剪接

### Step 6：配上視覺與輸出影片

- 使用固定系列封面模板
- 輸出 `16:9`、`1080p`
- 檔名包含日期、題材、時長、版本號

### Step 7：上架與記錄

每支影片至少記錄：

- 使用哪個 AI 平台
- 使用哪個付費方案
- 生成日期
- 音樂片段代號
- 標題版本
- 上傳日期

## 起步 30 天實作建議

### 第 1 週

- 決定 3 個主題系列
- 建好素材表
- 訂閱 `Suno Pro`
- 生成第一批測試片段

### 第 2 週

- 做出前 3 支影片
- 建立固定縮圖模板
- 開始記錄標題公式與關鍵字

### 第 3 週

- 再做 3 到 4 支影片
- 分析哪種情境最穩定
- 若有需要，再補上 `AIVA Pro`

### 第 4 週

- 完成至少 8 到 10 支影片
- 回顧點擊率、平均觀看時長、觀看時數
- 決定下個月是否維持單平台或改成雙平台策略

## 上線前授權檢查清單

1. 保存當期訂閱方案頁截圖
2. 保存授權條款頁截圖與日期
3. 確認是否明確允許 `YouTube 營利`
4. 確認是否明確允許 `Lo-fi / Relaxation / Functional music channel`
5. 確認取消訂閱後，已發布影片是否能持續保留
6. 確認是否禁止 `Content ID`、DSP 發行或第三方 distribution
7. 把每支影片使用的工具與方案版本記錄到素材表

## 官方來源

- `https://suno.com/pricing`
- `https://suno.com/legal/terms`
- `https://www.aiva.ai/`
- `https://soundraw.io/`
- `https://soundraw.io/license`
- `https://www.loudly.com/`
- `https://www.loudly.com/license-agreement`
- `https://www.beatoven.ai/pricing`
- `https://www.mubert.com/render/pricing`
- `https://www.udio.com/`
- `https://www.udio.com/terms-of-service`

## 最後建議

如果只選一套主力，優先選 `AIVA Pro` 或 `Suno Pro`。

- 想穩：選 `AIVA Pro`
- 想快：選 `Suno Pro`
- 想做影音導向候補：看 `Loudly`

對本專案來說，最危險的不是音樂生成品質不夠，而是 `誤判授權可用範圍`。因此工具選型時，授權清晰度應優先於花俏功能。
