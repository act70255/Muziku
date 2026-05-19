"""檔案掃描與輸入驗證。"""

from __future__ import annotations

from pathlib import Path


SUPPORTED_AUDIO_SUFFIXES = {".m4a"}
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image_path(image_path: Path) -> Path:
    """確認圖片存在且副檔名可接受。"""
    resolved_path = image_path.expanduser().resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        raise FileNotFoundError(f"找不到圖片檔：{resolved_path}")
    if resolved_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"不支援的圖片格式：{resolved_path.suffix}")
    return resolved_path


def scan_audio_files(audio_dir: Path) -> list[Path]:
    """掃描資料夾中的 m4a 音檔並依檔名排序。"""
    resolved_dir = audio_dir.expanduser().resolve()
    if not resolved_dir.exists() or not resolved_dir.is_dir():
        raise FileNotFoundError(f"找不到音訊資料夾：{resolved_dir}")

    audio_files = [
        path.resolve()
        for path in resolved_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_SUFFIXES
    ]
    audio_files.sort(key=lambda path: path.name.lower())

    if not audio_files:
        raise ValueError(f"資料夾中沒有可用的 m4a 音檔：{resolved_dir}")

    return audio_files


def resolve_output_path(output_path: Path) -> Path:
    """正規化輸出路徑。"""
    resolved_output = output_path.expanduser().resolve()
    if resolved_output.suffix.lower() != ".mp4":
        raise ValueError("輸出檔案必須為 .mp4")
    return resolved_output
