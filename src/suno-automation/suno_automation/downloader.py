"""
downloader.py

職責：將 Suno 生成的歌曲音訊檔案下載至本機指定資料夾，
      並在同目錄存入同名 .json 記錄（filename、style、prompt、parts）。
"""

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .suno_client import SunoSong


class Downloader:
    """
    負責將 SunoSong 的音訊 URL 下載並儲存至本機，
    同時寫出對應的 .json metadata 檔案。

    使用方式：
        downloader = Downloader(download_dir=Path("./output"))
        saved_path = await downloader.download(song, metadata={"style": "night", ...})
    """

    def __init__(
        self,
        download_dir: Path,
        filename_format: str = "{timestamp}_{title}",
    ) -> None:
        self._download_dir = download_dir
        self._filename_format = filename_format
        self._download_dir.mkdir(parents=True, exist_ok=True)

    async def download(
        self,
        song: SunoSong,
        metadata: dict | None = None,
    ) -> Path:
        """
        下載單首歌曲音訊至本機資料夾，並寫出同名 .json metadata。

        參數：
            song:     包含 audio_url 的 SunoSong 物件
            metadata: 額外記錄資訊（style、prompt、parts 等）

        回傳：
            儲存的本機 .mp3 檔案路徑

        拋出：
            ValueError:      audio_url 為空時
            httpx.HTTPError: 下載失敗時
        """
        if not song.audio_url:
            raise ValueError(f"歌曲 '{song.title}' 的 audio_url 為空，無法下載")

        filename = self._build_filename(song)
        save_path = self._download_dir / filename

        print(f"[Downloader] 開始下載：{song.title} → {save_path}")

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(song.audio_url)
            response.raise_for_status()
            save_path.write_bytes(response.content)

        print(f"[Downloader] 下載完成：{save_path} ({save_path.stat().st_size // 1024} KB)")

        self._write_metadata(save_path, song, metadata)
        return save_path

    async def download_batch(
        self,
        songs: list[SunoSong],
        metadatas: list[dict] | None = None,
    ) -> list[Path]:
        """
        批次下載多首歌曲。

        參數：
            songs:     歌曲列表
            metadatas: 與 songs 對應的 metadata 列表（長度可不同，多餘部分忽略）
        """
        paths: list[Path] = []
        for idx, song in enumerate(songs):
            meta = metadatas[idx] if metadatas and idx < len(metadatas) else None
            try:
                path = await self.download(song, metadata=meta)
                paths.append(path)
            except Exception as e:
                print(f"[Downloader] 下載失敗 '{song.title}'：{e}")
        return paths

    # ── 私有方法 ────────────────────────────────────────────────

    def _build_filename(self, song: SunoSong) -> str:
        """根據格式設定產生檔名，副檔名依 audio_url 決定。"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = self._sanitize_filename(song.title or "untitled")
        safe_id = song.song_id[:8] if song.song_id else "00000000"

        name = (
            self._filename_format
            .replace("{timestamp}", timestamp)
            .replace("{title}", safe_title)
            .replace("{id}", safe_id)
        )
        return f"{name}{self._resolve_extension(song.audio_url)}"

    @staticmethod
    def _resolve_extension(audio_url: str) -> str:
        """從音訊 URL 解析副檔名，未知時退回 .mp3。"""
        path = urlparse(audio_url).path
        suffix = Path(path).suffix.lower()
        return suffix if suffix else ".mp3"

    def _write_metadata(
        self,
        mp3_path: Path,
        song: SunoSong,
        extra: dict | None,
    ) -> None:
        """
        將 metadata 寫入與 MP3 同名的 .json 檔案。

        JSON 結構：
            {
                "filename": "20240512_143022_night_lofi.mp3",
                "song_id":  "abc12345-...",
                "title":    "Night Lofi",
                "style":    "night",
                "prompt":   "quiet night streets lofi, ..., no vocals",
                "parts": {
                    "context":     ["quiet night streets lofi"],
                    "mood":        ["dreamy and calm mood"],
                    "instrument":  ["ambient synth", "synthesizer pads"],
                    "texture":     ["city night ambience", "vinyl crackle"],
                    "rhythm":      ["late night tempo"],
                    "purpose":     ["for calm night sessions"],
                    "restriction": ["no bright uplifting sounds"],
                    "fixed_tags":  ["no vocals"]
                }
            }
        """
        record: dict = {
            "filename": mp3_path.name,
            "song_id":  song.song_id,
            "title":    song.title,
        }
        if extra:
            record.update(extra)

        json_path = mp3_path.with_suffix(".json")
        json_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[Downloader] Metadata 已寫入：{json_path.name}")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """移除檔名中的非法字元，並限制長度。"""
        sanitized = re.sub(r'[\\/:*?"<>|]', "_", name)
        sanitized = re.sub(r"\s+", "_", sanitized.strip())
        return sanitized[:50]
