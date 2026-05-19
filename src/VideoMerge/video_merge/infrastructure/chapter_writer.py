"""YouTube 章節檔產生器。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..domain.models import AudioProbeResult, ChapterEntry


def build_chapter_entries(audio_probes: Sequence[AudioProbeResult]) -> list[ChapterEntry]:
    """依音檔時長累加產生章節資訊。"""
    entries: list[ChapterEntry] = []
    current_start = 0.0
    for probe in audio_probes:
        entries.append(
            ChapterEntry(
                title=probe.title,
                start_seconds=current_start,
                duration_seconds=probe.duration_seconds,
                source_path=probe.path,
            )
        )
        current_start += probe.duration_seconds
    return entries


def _format_timestamp(seconds: float, *, force_hours: bool) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if force_hours or hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_youtube_chapters(entries: Sequence[ChapterEntry]) -> list[str]:
    """輸出可直接貼到 YouTube 說明欄的章節文字。"""
    force_hours = any(entry.start_seconds >= 3600 for entry in entries)
    return [f"{_format_timestamp(entry.start_seconds, force_hours=force_hours)} {entry.title}" for entry in entries]


def write_youtube_chapters(chapter_path: Path, entries: Sequence[ChapterEntry]) -> Path:
    """將 YouTube 章節內容寫入文字檔。"""
    chapter_path.parent.mkdir(parents=True, exist_ok=True)
    chapter_path.write_text("\n".join(format_youtube_chapters(entries)) + "\n", encoding="utf-8")
    return chapter_path
