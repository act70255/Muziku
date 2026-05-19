"""VideoMerge 的核心型別定義。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class FFmpegSettings:
    ffmpeg_binary: str
    ffprobe_binary: str
    overwrite_output: bool


@dataclass(slots=True)
class AudioSettings:
    codec: str
    bitrate: str
    sample_rate: int
    channels: int
    normalize_by_default: bool
    loudnorm_filter: str


@dataclass(slots=True)
class VideoSettings:
    width: int
    height: int
    fps: int
    codec: str
    pixel_format: str
    crf: int
    tune_stillimage: bool
    faststart: bool


@dataclass(slots=True)
class OutputSettings:
    work_dir: Path
    merged_audio_filename: str
    manifest_filename: str
    normalized_dirname: str
    chapters_suffix: str


@dataclass(slots=True)
class TemplateSettings:
    default_template: str
    ken_burns_zoom_speed: float
    pan_seconds: int
    waveform_height: int
    waveform_opacity: float


@dataclass(slots=True)
class AppConfig:
    ffmpeg: FFmpegSettings
    audio: AudioSettings
    video: VideoSettings
    output: OutputSettings
    template: TemplateSettings
    base_dir: Path


@dataclass(slots=True)
class AudioProbeResult:
    path: Path
    codec_name: str
    sample_rate: int
    channels: int
    duration_seconds: float

    @property
    def title(self) -> str:
        return self.path.stem


@dataclass(slots=True)
class BuildRequest:
    image_path: Path
    audio_dir: Path
    output_path: Path
    template_name: str | None
    normalize_audio: bool | None
    dry_run: bool


@dataclass(slots=True)
class ChapterEntry:
    title: str
    start_seconds: float
    duration_seconds: float
    source_path: Path


@dataclass(slots=True)
class BuildResult:
    output_path: Path
    merged_audio_path: Path
    chapter_path: Path
    total_duration_seconds: float
    audio_probes: list[AudioProbeResult]
    chapter_entries: list[ChapterEntry]
    command_log: list[str]
    normalized_audio_paths: list[Path]
    dry_run: bool
