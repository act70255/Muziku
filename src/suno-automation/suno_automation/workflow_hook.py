"""
workflow_hook.py

職責：音樂生成完成後，將結果以 JSONL 格式寫入本機事件 log。
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .suno_client import SunoSong


class WorkflowHook:
    """
    將生成結果寫入本機 JSONL 事件 log，供後續查詢或工作流輪詢讀取。

    使用方式：
        hook = WorkflowHook(event_log_path=Path("./output/events.jsonl"))
        await hook.notify(songs, saved_paths)
    """

    def __init__(
        self,
        event_log_path: Path = Path("./output/events.jsonl"),
    ) -> None:
        self._event_log_path = event_log_path

    async def notify(
        self,
        songs: list[SunoSong],
        saved_paths: list[Path],
    ) -> None:
        """
        將本次生成結果寫入事件 log。

        參數：
            songs:       生成的歌曲物件列表
            saved_paths: 對應的本機儲存路徑列表
        """
        payload = self._build_payload(songs, saved_paths)
        self._write_local_event(payload)

    def _build_payload(
        self,
        songs: list[SunoSong],
        saved_paths: list[Path],
    ) -> dict:
        """建立事件 payload 資料結構。"""
        return {
            "event": "suno.generation.completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "songs": [
                {
                    **asdict(song),
                    "local_path": str(saved_paths[idx]) if idx < len(saved_paths) else None,
                }
                for idx, song in enumerate(songs)
            ],
        }

    def _write_local_event(self, payload: dict) -> None:
        """將事件 payload 以 JSONL 格式追加寫入本機事件 log 檔案。"""
        self._event_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._event_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        print(f"[WorkflowHook] 事件已寫入：{self._event_log_path}")
