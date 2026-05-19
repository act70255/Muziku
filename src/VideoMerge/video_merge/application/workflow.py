"""VideoMerge 工作流程編排。"""

from __future__ import annotations

from pathlib import Path

from ..domain.models import AppConfig, AudioProbeResult, BuildRequest, BuildResult
from ..infrastructure.chapter_writer import build_chapter_entries, write_youtube_chapters
from ..infrastructure.ffmpeg_runner import FFmpegRunner
from ..infrastructure.file_scanner import resolve_output_path, scan_audio_files, validate_image_path
from ..infrastructure.manifest_writer import write_concat_manifest


class VideoBuildWorkflow:
    """負責串接掃描、探測、標準化、合併與輸出流程。"""

    def __init__(self, config: AppConfig, runner: FFmpegRunner) -> None:
        self.config = config
        self.runner = runner

    def probe_target(self, target_path: Path) -> list[AudioProbeResult]:
        """探測單一音檔或整個資料夾。"""
        resolved_target = target_path.expanduser().resolve()
        if not resolved_target.exists():
            raise FileNotFoundError(f"找不到目標路徑：{resolved_target}")

        if resolved_target.is_file():
            return [self.runner.probe_audio(resolved_target)]

        audio_files = scan_audio_files(resolved_target)
        return [self.runner.probe_audio(audio_path) for audio_path in audio_files]

    def build(self, request: BuildRequest) -> BuildResult:
        """執行完整 build 流程。"""
        self.runner.command_log.clear()

        image_path = validate_image_path(request.image_path)
        output_path = resolve_output_path(request.output_path)
        audio_files = scan_audio_files(request.audio_dir)
        audio_probes = [self.runner.probe_audio(audio_path) for audio_path in audio_files]

        total_duration_seconds = sum(probe.duration_seconds for probe in audio_probes)
        template_name = request.template_name or self.config.template.default_template
        normalize_audio = (
            self.config.audio.normalize_by_default
            if request.normalize_audio is None
            else request.normalize_audio
        )

        work_dir = self._build_work_dir(output_path)
        normalized_dir = work_dir / self.config.output.normalized_dirname
        normalized_paths = [normalized_dir / f"{index:03d}_{audio_path.stem}.m4a" for index, audio_path in enumerate(audio_files, start=1)]
        manifest_path = work_dir / self.config.output.manifest_filename
        merged_audio_path = work_dir / self.config.output.merged_audio_filename
        chapter_entries = build_chapter_entries(audio_probes)
        chapter_path = output_path.with_suffix(self.config.output.chapters_suffix)

        if not request.dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            normalized_dir.mkdir(parents=True, exist_ok=True)

        for source_path, normalized_path in zip(audio_files, normalized_paths):
            self.runner.normalize_audio(
                source_path,
                normalized_path,
                apply_loudnorm=normalize_audio,
                dry_run=request.dry_run,
            )

        if request.dry_run:
            self.runner.concat_audio(manifest_path, merged_audio_path, dry_run=True)
        else:
            write_concat_manifest(manifest_path, normalized_paths)
            self.runner.concat_audio(manifest_path, merged_audio_path, dry_run=False)

        self.runner.render_video(
            image_path,
            merged_audio_path,
            output_path,
            template_name=template_name,
            total_duration_seconds=total_duration_seconds,
            dry_run=request.dry_run,
        )

        if not request.dry_run:
            write_youtube_chapters(chapter_path, chapter_entries)

        return BuildResult(
            output_path=output_path,
            merged_audio_path=merged_audio_path,
            chapter_path=chapter_path,
            total_duration_seconds=total_duration_seconds,
            audio_probes=audio_probes,
            chapter_entries=chapter_entries,
            command_log=list(self.runner.command_log),
            normalized_audio_paths=normalized_paths,
            dry_run=request.dry_run,
        )

    def _build_work_dir(self, output_path: Path) -> Path:
        safe_name = output_path.stem.replace(" ", "_")
        return (self.config.output.work_dir / safe_name).resolve()
