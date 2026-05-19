"""ffmpeg concat manifest 寫入工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def _escape_manifest_path(path: Path) -> str:
    normalized = path.resolve().as_posix()
    return normalized.replace("'", r"'\''")


def write_concat_manifest(manifest_path: Path, audio_files: Sequence[Path]) -> Path:
    """將音檔清單寫為 ffmpeg concat manifest。"""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"file '{_escape_manifest_path(audio_path)}'" for audio_path in audio_files]
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path
