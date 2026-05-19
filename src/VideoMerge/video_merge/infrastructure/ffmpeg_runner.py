"""ffmpeg 與 ffprobe 呼叫封裝。"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from ..domain.models import AudioProbeResult, AudioSettings, FFmpegSettings, TemplateSettings, VideoSettings


TEMPLATE_DESCRIPTIONS: dict[str, str] = {
    "static": "純靜態封面輸出",
    "ken-burns": "慢速縮放的 Ken Burns 視覺",
    "pan": "慢速橫向平移視覺",
    "waveform": "底部疊加音波視覺化",
}


class FFmpegExecutionError(RuntimeError):
    """代表 ffmpeg 或 ffprobe 執行失敗。"""


class FFmpegRunner:
    """統一管理 ffmpeg / ffprobe 指令呼叫。"""

    def __init__(
        self,
        ffmpeg_settings: FFmpegSettings,
        audio_settings: AudioSettings,
        video_settings: VideoSettings,
        template_settings: TemplateSettings,
    ) -> None:
        self.ffmpeg_settings = ffmpeg_settings
        self.audio_settings = audio_settings
        self.video_settings = video_settings
        self.template_settings = template_settings
        self.command_log: list[str] = []

    @staticmethod
    def get_template_descriptions() -> dict[str, str]:
        """回傳所有支援的模板名稱與說明。"""
        return TEMPLATE_DESCRIPTIONS.copy()

    def probe_audio(self, audio_path: Path) -> AudioProbeResult:
        """讀取單一音檔的編碼與時長資訊。"""
        command = [
            self.ffmpeg_settings.ffprobe_binary,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio_path),
        ]
        output = self._run_capture(command)
        payload = json.loads(output)

        streams = payload.get("streams", [])
        if not streams:
            raise FFmpegExecutionError(f"音檔沒有可讀取的音訊 stream：{audio_path}")

        stream = streams[0]
        format_info = payload.get("format", {})
        duration_value = format_info.get("duration")
        if duration_value is None:
            raise FFmpegExecutionError(f"無法取得音檔時長：{audio_path}")

        return AudioProbeResult(
            path=audio_path,
            codec_name=str(stream.get("codec_name", "unknown")),
            sample_rate=int(stream.get("sample_rate", 0)),
            channels=int(stream.get("channels", 0)),
            duration_seconds=float(duration_value),
        )

    def normalize_audio(
        self,
        input_path: Path,
        output_path: Path,
        *,
        apply_loudnorm: bool,
        dry_run: bool,
    ) -> None:
        """將輸入音檔轉成統一規格。"""
        command = [
            self.ffmpeg_settings.ffmpeg_binary,
            *self._overwrite_flags(),
            "-i",
            str(input_path),
            "-vn",
        ]

        if apply_loudnorm:
            command.extend(["-af", self.audio_settings.loudnorm_filter])

        command.extend(
            [
                "-ar",
                str(self.audio_settings.sample_rate),
                "-ac",
                str(self.audio_settings.channels),
                "-c:a",
                self.audio_settings.codec,
                "-b:a",
                self.audio_settings.bitrate,
                str(output_path),
            ]
        )
        self._run_command(command, dry_run=dry_run)

    def concat_audio(self, manifest_path: Path, output_path: Path, *, dry_run: bool) -> None:
        """將多個標準化後音檔合併為單一主音軌。"""
        command = [
            self.ffmpeg_settings.ffmpeg_binary,
            *self._overwrite_flags(),
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest_path),
            "-c:a",
            self.audio_settings.codec,
            "-b:a",
            self.audio_settings.bitrate,
            str(output_path),
        ]
        self._run_command(command, dry_run=dry_run)

    def render_video(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        *,
        template_name: str,
        total_duration_seconds: float,
        dry_run: bool,
    ) -> None:
        """依指定模板輸出最終影片。"""
        command = [
            self.ffmpeg_settings.ffmpeg_binary,
            *self._overwrite_flags(),
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-i",
            str(audio_path),
        ]

        filter_mode, filter_value = self._build_filter(template_name, total_duration_seconds)
        if filter_mode == "vf":
            command.extend([
                "-vf",
                filter_value,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
            ])
        else:
            command.extend([
                "-filter_complex",
                filter_value,
                "-map",
                "[v]",
                "-map",
                "1:a:0",
            ])

        command.extend(
            [
                "-c:v",
                self.video_settings.codec,
                "-r",
                str(self.video_settings.fps),
                "-pix_fmt",
                self.video_settings.pixel_format,
                "-c:a",
                self.audio_settings.codec,
                "-b:a",
                self.audio_settings.bitrate,
                "-crf",
                str(self.video_settings.crf),
            ]
        )

        if self.video_settings.tune_stillimage:
            command.extend(["-tune", "stillimage"])
        if self.video_settings.faststart:
            command.extend(["-movflags", "+faststart"])

        command.extend(["-shortest", str(output_path)])
        self._run_command(command, dry_run=dry_run)

    def _build_filter(self, template_name: str, total_duration_seconds: float) -> tuple[str, str]:
        if template_name not in TEMPLATE_DESCRIPTIONS:
            available = ", ".join(sorted(TEMPLATE_DESCRIPTIONS))
            raise ValueError(f"不支援的模板：{template_name}；可用模板：{available}")

        width = self.video_settings.width
        height = self.video_settings.height
        fps = self.video_settings.fps
        waveform_y = max(height - self.template_settings.waveform_height, 0)
        base_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        )

        if template_name == "static":
            return "vf", base_filter

        if template_name == "ken-burns":
            return (
                "filter_complex",
                (
                    f"[0:v]{base_filter},"
                    f"zoompan=z='min(zoom+{self.template_settings.ken_burns_zoom_speed},1.15)':"
                    f"d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                    f"s={width}x{height}:fps={fps}[v]"
                ),
            )

        if template_name == "pan":
            pan_duration = max(min(total_duration_seconds, float(self.template_settings.pan_seconds)), 1.0)
            expanded_width = int(width * 1.12)
            expanded_height = int(height * 1.12)
            return (
                "filter_complex",
                (
                    f"[0:v]scale={expanded_width}:{expanded_height}:force_original_aspect_ratio=increase,"
                    f"crop={width}:{height}:x='min((in_w-out_w)*(t/{pan_duration:.3f}),in_w-out_w)':"
                    f"y='(in_h-out_h)/2',setsar=1[v]"
                ),
            )

        return (
            "filter_complex",
            (
                f"[0:v]{base_filter}[bg];"
                f"[1:a]showwaves=s={width}x{self.template_settings.waveform_height}:"
                f"mode=line:colors=White@{self.template_settings.waveform_opacity}[sw];"
                f"[bg][sw]overlay=0:{waveform_y}[v]"
            ),
        )

    def _overwrite_flags(self) -> list[str]:
        return ["-y"] if self.ffmpeg_settings.overwrite_output else ["-n"]

    def _run_capture(self, command: list[str]) -> str:
        self.command_log.append(self._format_command(command))
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as error:
            raise FFmpegExecutionError(
                f"找不到執行檔：{command[0]}；請先安裝 ffmpeg/ffprobe，或在 config/settings.toml 設定完整路徑"
            ) from error
        except subprocess.CalledProcessError as error:
            stderr = error.stderr.strip() if error.stderr else ""
            raise FFmpegExecutionError(stderr or "指令執行失敗") from error
        return completed.stdout

    def _run_command(self, command: list[str], *, dry_run: bool) -> None:
        self.command_log.append(self._format_command(command))
        if dry_run:
            return
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as error:
            raise FFmpegExecutionError(
                f"找不到執行檔：{command[0]}；請先安裝 ffmpeg/ffprobe，或在 config/settings.toml 設定完整路徑"
            ) from error
        except subprocess.CalledProcessError as error:
            stderr = error.stderr.strip() if error.stderr else ""
            raise FFmpegExecutionError(stderr or "指令執行失敗") from error

    def _format_command(self, command: list[str]) -> str:
        return shlex.join(command)
