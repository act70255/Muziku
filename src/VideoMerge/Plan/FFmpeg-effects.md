# FFmpeg 可用特效與模板建議

這份文件整理 `FFmpeg` 在 `單張圖片 + 多音檔 + 長影片` 場景下最實用的特效類型、模板選型與指令範例，目標是協助快速決定 MVP 視覺方案，並作為後續自動化實作參考。

## 常用特效類型

- `zoompan`：慢速縮放、平移、Ken Burns 效果
- `fade`：畫面淡入淡出
- `xfade`：片段間畫面轉場
- `overlay`：疊加雪花、雨、粒子、光斑
- `blend`：使用 `screen`、`overlay` 等混合模式做氣氛疊加
- `colorkey`：去除黑底或指定顏色背景
- `eq`：亮度、對比、飽和度調整
- `hue`：色相與飽和度調整
- `curves`：進階色調曲線調整
- `colorbalance`：冷暖色偏移
- `gblur`、`boxblur`：柔焦與模糊
- `unsharp`：輕微銳化
- `vignette`：暗角
- `noise`：膠片顆粒感
- `drawtext`：標題、歌名、浮水印
- `drawbox`：進度條、資訊框
- `rotate`：輕微旋轉或晃動
- `showwaves`：音波視覺化
- `showspectrum`：頻譜視覺化

## 最適合長影片的特效組合

對 `Lo-fi`、`Study`、`Chill` 類型的長片，最實用且最省資源的效果通常是：

- 單圖慢速縮放
- 單圖慢速平移
- 粒子或雪花循環覆蓋
- 輕微色調校正
- 暗角與少量顆粒
- 簡單浮水印或系列名稱

## 推薦模板 1：純靜態封面

適用情境：

- 先做 MVP
- 要求最快輸出
- 不想增加任何額外視覺計算

參考指令：

```bash
ffmpeg -loop 1 -i cover.jpg -i final.mp3 \
  -c:v libx264 -tune stillimage -r 10 -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

## 推薦模板 2：慢速縮放

適用情境：

- 最常見的 Lo-fi 長片視覺
- 希望畫面有生命感，但維持低資源消耗

參考指令：

```bash
ffmpeg -loop 1 -i cover.jpg -i final.mp3 \
  -filter_complex "[0:v]scale=1920:1080,zoompan=z='min(zoom+0.00015,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fps=10[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

## 推薦模板 3：慢速縮放加雪花粒子

適用情境：

- 夜晚、冬季、雨景、夢幻氛圍主題
- 希望視覺更完整，但仍維持長片可量產

參考指令：

```bash
ffmpeg -loop 1 -i cover.jpg -stream_loop -1 -i snow.mp4 -i final.mp3 \
  -filter_complex "[0:v]scale=1920:1080,zoompan=z='min(zoom+0.00015,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fps=10[bg];[1:v]scale=1920:1080[fx];[bg][fx]blend=all_mode='screen':all_opacity=0.35[v]" \
  -map "[v]" -map 2:a \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

## 推薦模板 4：慢速平移加色調微調

適用情境：

- 城市夜景
- 咖啡廳
- 房間場景
- 希望畫面更有電影感

參考指令：

```bash
ffmpeg -loop 1 -i cover.jpg -i final.mp3 \
  -filter_complex "[0:v]scale=2200:1238,crop=1920:1080:x='(in_w-out_w)*t/3600':y='(in_h-out_h)/2',eq=brightness=-0.03:saturation=1.1:contrast=1.05,fps=10[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

## 推薦模板 5：靜態圖加音波視覺化

適用情境：

- 希望畫面不要太靜
- 想保留明顯的音樂感
- 願意接受稍微偏工具風的視覺語言

參考指令：

```bash
ffmpeg -loop 1 -i cover.jpg -i final.mp3 \
  -filter_complex "[0:v]scale=1920:1080[bg];[1:a]showwaves=s=1920x220:mode=line:colors=White@0.7[sw];[bg][sw]overlay=0:860[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

## 模板選型建議

- 若要最快上線，先用 `純靜態封面`
- 若要在成本與觀感之間取平衡，優先用 `慢速縮放`
- 若要提高氛圍感，再加上 `雪花`、`粒子` 或 `雨景` 疊加
- 若影片主要用於長時間陪伴播放，不建議一開始就加入太強烈的音波或頻譜動畫

## 參數建議

- 解析度：`1920x1080`
- FPS：`10` 到 `12`
- 影片編碼：`libx264`
- 音訊編碼：`aac`
- 音訊位元率：`256k` 到 `320k`
- 靜態圖優化：`-tune stillimage`
- 壓縮平衡：`CRF 20` 到 `24`

## 實務注意事項

- `zoompan` 的速度要非常小，否則長片看起來會不自然
- 黑底粒子素材通常要搭配 `screen` 或 `colorkey`
- 長片畫面以穩定為主，不要堆疊過多濾鏡
- 若特效素材本身解析度太低，放大後容易破壞整體質感
- 若未來要把這些模板自動化，建議把模板名稱、FPS、色調參數、特效素材路徑都做成設定檔

## 特效總覽

### 鏡頭動態類

| 特效 | 主要濾鏡 | 用途 | 成本 | 建議程度 |
| --- | --- | --- | --- | --- |
| 慢速縮放 | `zoompan` | 讓單圖有生命感 | 低 | 很高 |
| 慢速平移 | `scale` + `crop` | 做出橫移或縱移鏡頭感 | 低 | 很高 |
| 輕微旋轉 | `rotate` | 增加微弱漂浮感 | 低到中 | 中 |

### 氣氛疊加類

| 特效 | 主要濾鏡 | 用途 | 成本 | 建議程度 |
| --- | --- | --- | --- | --- |
| 雪花 / 粒子 | `overlay`、`blend` | 增加氛圍 | 低到中 | 很高 |
| 雨景疊加 | `overlay`、`blend` | 強化場景情緒 | 中 | 高 |
| 顆粒感 | `noise` | 增加膠片或復古感 | 低 | 中 |
| 暗角 | `vignette` | 聚焦畫面中心 | 低 | 高 |

### 色彩調整類

| 特效 | 主要濾鏡 | 用途 | 成本 | 建議程度 |
| --- | --- | --- | --- | --- |
| 亮度 / 對比 / 飽和度 | `eq` | 快速修正整體風格 | 低 | 很高 |
| 冷暖色偏移 | `colorbalance` | 做夜景、黃昏、室內氛圍 | 低 | 高 |
| 色調曲線 | `curves` | 精細調色 | 中 | 中 |
| 色相調整 | `hue` | 做特殊風格變化 | 低 | 中 |

### 資訊疊加類

| 特效 | 主要濾鏡 | 用途 | 成本 | 建議程度 |
| --- | --- | --- | --- | --- |
| 標題 / 浮水印 | `drawtext` | 顯示系列名、頻道名 | 低 | 高 |
| 進度條 / 框線 | `drawbox` | 做資訊區塊 | 低 | 中 |
| 音波 | `showwaves` | 提升音樂感 | 中 | 中 |
| 頻譜 | `showspectrum` | 偏向工具風或電子感 | 中 | 低到中 |

## 模板範例

### 模板 A：Lo-fi Night

- 主視覺：夜晚房間、城市窗景、暖燈桌面
- 建議效果：慢速縮放 + 雪花粒子 + 輕微暗角
- 適合題材：`Late Night Study`、`Rainy Coding Session`

### 模板 B：Cafe Ambience

- 主視覺：咖啡廳窗邊、木桌、街景
- 建議效果：慢速平移 + 暖色調 + 少量顆粒
- 適合題材：`Cafe Lo-fi`、`Morning Focus`

### 模板 C：Minimal Cover

- 主視覺：簡單插畫、極簡封面、品牌化視覺
- 建議效果：純靜態或極慢縮放 + 浮水印
- 適合題材：系列化大量產出

### 模板 D：Dreamy Ambient

- 主視覺：雲層、星空、霧氣、抽象插畫
- 建議效果：慢速縮放 + 柔焦 + 冷色調偏移
- 適合題材：`Sleep`、`Ambient`、`Meditation`

### 模板 E：Music Reactive

- 主視覺：封面圖搭配底部音波
- 建議效果：純靜態 + `showwaves`
- 適合題材：想保留較強音樂存在感的版本

## 參數調校指南

### FPS

- `8` 到 `10 FPS`：最省資源，適合幾乎純靜態畫面
- `10` 到 `12 FPS`：最平衡，適合多數長影片
- `15 FPS` 以上：只有在特效明顯動態化時才有意義

### CRF

- `18` 到 `20`：畫質優先，檔案較大
- `21` 到 `24`：最建議的平衡區間
- `25` 以上：檔案更小，但靜態漸層與粒子細節容易變差

### 音訊設定

- `aac 256k`：通常已足夠
- `aac 320k`：想保守維持較高音質時使用
- 若來源音訊品質不一致，應先做標準化再輸出

### overlay / blend 透明度

- `0.15` 到 `0.25`：很淡，安全
- `0.25` 到 `0.4`：最常用區間
- `0.4` 以上：容易搶畫面，不建議長時間使用

### zoompan 速度

- 建議從 `0.00008` 到 `0.0002` 起測
- 長影片應避免太快，否則觀感會像持續推鏡過頭
- 若圖片構圖很滿，縮放幅度應更保守

### 色調調整

- `brightness` 建議微調，通常在 `-0.05` 到 `0.05`
- `contrast` 建議控制在 `0.95` 到 `1.08`
- `saturation` 建議控制在 `0.95` 到 `1.15`
- 夜景通常偏冷或偏暗，但不要讓主體細節完全吃掉

### 自動化建議欄位

若未來要把模板參數化，建議至少抽出以下欄位：

- `template_name`
- `resolution`
- `fps`
- `video_codec`
- `audio_bitrate`
- `crf`
- `zoom_speed`
- `overlay_path`
- `overlay_opacity`
- `color_profile`
- `watermark_text`

### 調校順序建議

1. 先固定輸出解析度與 FPS
2. 再決定是否使用縮放或平移
3. 再加疊加素材，例如雪花或粒子
4. 最後才調色與加字

這樣比較容易判斷每一層效果對渲染時間與視覺品質的實際影響。

## 多個 MP3 的處理流程

### 整體流程

1. 掃描輸入檔案
2. 驗證音訊格式
3. 判斷要用 `串接` 還是 `混音`
4. 先做音訊標準化
5. 輸出單一主音軌
6. 圖片與主音軌合成影片
7. 套用視覺模板
8. 輸出與檢查結果

這個流程的核心原則是先把音訊問題處理乾淨，再進入影片輸出。不要一開始就把所有圖片、音訊、特效一次塞進同一條超長指令，否則錯誤會很難追。

### 節點 1：掃描輸入檔案

先明確區分三種素材：

- 主視覺圖片，例如 `cover.jpg`
- 主音樂清單，例如多個 `mp3`
- 可選的環境音或特效音，例如 `rain.mp3`、`noise.mp3`

建議做法：

- 依檔名排序主音樂清單
- 排除空檔案與不支援格式
- 保留一份輸入清單，方便後續追蹤

如果未來要自動化，這一步通常由 `Python` 掃描資料夾後，產生一份 manifest，例如 `music_list.txt`。

### 節點 2：驗證音訊格式

多個 `MP3` 不一定可以直接安全串接，因為它們可能有不同的：

- codec
- sample rate
- channels
- bitrate
- duration

建議先用 `ffprobe` 取得基本資訊，例如：

```bash
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -show_entries format=duration -of default=noprint_wrappers=1 song1.mp3
```

若來源規格差異很大，應先走標準化流程，不要直接做 `concat`。

### 節點 3：判斷要用串接還是混音

這是最重要的分支點。

#### 情境 A：串接

適合：

- `song1 -> song2 -> song3`
- 做成 30 分鐘到 3 小時的播放清單型長片

這時應使用 `concat demuxer`。

先建立：

```txt
file 'song1.mp3'
file 'song2.mp3'
file 'song3.mp3'
```

再執行：

```bash
ffmpeg -f concat -safe 0 -i music_list.txt -c:a aac -b:a 320k merged.m4a
```

#### 情境 B：混音

適合：

- 背景音樂加雨聲
- 背景音樂加白噪音
- 多條音訊同時播放

這時應使用 `amix`。

範例：

```bash
ffmpeg -i music.mp3 -i rain.mp3 -filter_complex "amix=inputs=2:duration=longest" -c:a aac -b:a 320k mixed.m4a
```

#### 實務判斷原則

- 多首歌排成長片：先 `串接`
- 主音樂搭配環境音：在串接完成後再 `混音`
- 不建議把所有來源在第一步就全部 `amix`

### 節點 4：音訊標準化

標準化的目的是避免：

- 直接串接失敗
- 每段音量忽大忽小
- 最終音軌聽感不一致

建議至少統一：

- sample rate，例如 `48000`
- channels，例如 `2`
- codec 或中介格式

範例：

```bash
ffmpeg -i song1.mp3 -ar 48000 -ac 2 -c:a aac -b:a 320k normalized-song1.m4a
```

若要進一步處理音量，可加入 `loudnorm`，但建議先完成基本可用流程，再決定是否把音量正規化納入正式管線。

### 節點 5：輸出單一主音軌

正式建議是分兩步做：

1. 先把所有主音樂標準化
2. 再把標準化後的檔案串接成一條主音軌

這樣可以降低合併失敗率，也更容易除錯。

如果要再加環境音，建議在主音軌輸出完成後，再用 `amix` 產生第二條最終音軌。

範例流程：

1. `song1.mp3 -> normalized-song1.m4a`
2. `song2.mp3 -> normalized-song2.m4a`
3. `normalized-* -> merged.m4a`
4. `merged.m4a + rain.mp3 -> final-audio.m4a`

### 節點 6：圖片與主音軌合成影片

當你已經得到最終音軌，例如 `final-audio.m4a`，就可以再接圖片輸出影片。

最基本範例：

```bash
ffmpeg -loop 1 -i cover.jpg -i final-audio.m4a \
  -c:v libx264 -tune stillimage -r 10 -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest output.mp4
```

如果要套用模板，就把前面章節的 `zoompan`、`overlay`、`showwaves` 等濾鏡加上去。

### 節點 7：套用視覺模板

建議順序：

1. 先確認純靜態封面版能正常輸出
2. 再改成慢速縮放
3. 最後才增加雪花、粒子、音波等額外效果

這樣可以快速判斷問題到底出在音訊合併、畫面濾鏡，還是輸出封裝。

### 節點 8：輸出與檢查結果

每次輸出後至少確認：

- 影片可播放
- 畫面存在
- 音訊存在
- 總時長正確
- 首尾沒有異常黑畫面或靜音

若有自動化需求，建議把以下資訊記錄到報告：

- 使用了哪些輸入檔
- 總音訊時長
- 輸出影片大小
- 處理耗時
- 使用的模板名稱

## 常見錯誤與避坑

### 問題 1：多個 MP3 無法直接 concat

常見原因：

- 編碼規格不同
- 聲道數不同
- 取樣率不同

建議：

- 先統一轉成相同格式後再串接

### 問題 2：音量忽大忽小

常見原因：

- 不同來源的母帶音量差太大

建議：

- 加入音量標準化流程
- 至少先做人工抽查

### 問題 3：畫面特效很多但輸出變慢

常見原因：

- 疊加過多濾鏡
- 特效素材太大
- FPS 設太高

建議：

- 回到 `10` 到 `12 FPS`
- 優先保留縮放與一層疊加素材

### 問題 4：想同時串接又混音，指令變得很難維護

建議：

- 不要一步完成所有事情
- 先輸出 `主音軌`
- 再輸出 `最終混音`
- 最後才輸出影片

這種分段式流程最適合後續做成 `Python + FFmpeg` 的可維護工作流。
