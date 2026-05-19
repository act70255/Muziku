"""CLI 入口，負責組裝設定與工作流程。"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Annotated

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import typer

from .application.workflow import VideoBuildWorkflow
from .domain.models import (
    AppConfig,
    AudioSettings,
    BuildRequest,
    FFmpegSettings,
    OutputSettings,
    TemplateSettings,
    VideoSettings,
)
from .infrastructure.chapter_writer import format_youtube_chapters
from .infrastructure.ffmpeg_runner import FFmpegExecutionError, FFmpegRunner


app = typer.Typer(
    name="video-merge",
    help="以 Python 與 ffmpeg 建立長影片的 CLI 工具",
    add_completion=False,
)

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_CONFIG = DEFAULT_CONFIG_DIR / "settings.toml"


def _load_config(config_path: Path) -> AppConfig:
    """載入 TOML 設定檔並轉為型別化設定。"""
    resolved_config = config_path.expanduser().resolve()
    if not resolved_config.exists():
        typer.secho(f"找不到設定檔：{resolved_config}", fg=typer.colors.RED)
        raise typer.Exit(1)

    with resolved_config.open("rb") as file:
        payload = tomllib.load(file)

    ffmpeg_section = payload.get("ffmpeg", {})
    audio_section = payload.get("audio", {})
    video_section = payload.get("video", {})
    output_section = payload.get("output", {})
    template_section = payload.get("template", {})

    base_dir = resolved_config.parent
    work_dir = Path(output_section.get("work_dir", "./output/work"))
    if not work_dir.is_absolute():
        work_dir = (base_dir / work_dir).resolve()

    return AppConfig(
        ffmpeg=FFmpegSettings(
            ffmpeg_binary=str(ffmpeg_section.get("binary", "ffmpeg")),
            ffprobe_binary=str(ffmpeg_section.get("probe_binary", "ffprobe")),
            overwrite_output=bool(ffmpeg_section.get("overwrite_output", True)),
        ),
        audio=AudioSettings(
            codec=str(audio_section.get("codec", "aac")),
            bitrate=str(audio_section.get("bitrate", "320k")),
            sample_rate=int(audio_section.get("sample_rate", 48000)),
            channels=int(audio_section.get("channels", 2)),
            normalize_by_default=bool(audio_section.get("normalize_by_default", False)),
            loudnorm_filter=str(audio_section.get("loudnorm_filter", "loudnorm=I=-16:LRA=11:TP=-1.5")),
        ),
        video=VideoSettings(
            width=int(video_section.get("width", 1920)),
            height=int(video_section.get("height", 1080)),
            fps=int(video_section.get("fps", 10)),
            codec=str(video_section.get("codec", "libx264")),
            pixel_format=str(video_section.get("pixel_format", "yuv420p")),
            crf=int(video_section.get("crf", 22)),
            tune_stillimage=bool(video_section.get("tune_stillimage", True)),
            faststart=bool(video_section.get("faststart", True)),
        ),
        output=OutputSettings(
            work_dir=work_dir,
            merged_audio_filename=str(output_section.get("merged_audio_filename", "merged.m4a")),
            manifest_filename=str(output_section.get("manifest_filename", "concat.txt")),
            normalized_dirname=str(output_section.get("normalized_dirname", "normalized")),
            chapters_suffix=str(output_section.get("chapters_suffix", ".chapters.txt")),
        ),
        template=TemplateSettings(
            default_template=str(template_section.get("default_template", "static")),
            ken_burns_zoom_speed=float(template_section.get("ken_burns_zoom_speed", 0.00015)),
            pan_seconds=int(template_section.get("pan_seconds", 900)),
            waveform_height=int(template_section.get("waveform_height", 220)),
            waveform_opacity=float(template_section.get("waveform_opacity", 0.7)),
        ),
        base_dir=base_dir,
    )


def _create_workflow(config: AppConfig) -> VideoBuildWorkflow:
    runner = FFmpegRunner(config.ffmpeg, config.audio, config.video, config.template)
    return VideoBuildWorkflow(config, runner)


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


@app.command("build")
def build(
    image_path: Annotated[Path, typer.Option("--image", help="主視覺圖片路徑")],
    audio_dir: Annotated[Path, typer.Option("--audio-dir", help="m4a 音檔資料夾")],
    output_path: Annotated[Path, typer.Option("--output", help="輸出的 mp4 路徑")],
    template_name: Annotated[str | None, typer.Option("--template", help="視覺模板名稱")]=None,
    normalize_audio: Annotated[
        bool | None,
        typer.Option("--normalize-audio/--no-normalize-audio", help="是否啟用 loudnorm 音量正規化"),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="只顯示流程與 ffmpeg 指令，不實際輸出檔案")] = False,
    config_path: Annotated[Path, typer.Option("--config", "-c", help="設定檔路徑")] = DEFAULT_CONFIG,
) -> None:
    """將單張圖片與多個 m4a 合併為長影片。"""
    try:
        config = _load_config(config_path)
        workflow = _create_workflow(config)
        result = workflow.build(
            BuildRequest(
                image_path=image_path,
                audio_dir=audio_dir,
                output_path=output_path,
                template_name=template_name,
                normalize_audio=normalize_audio,
                dry_run=dry_run,
            )
        )
    except (FileNotFoundError, ValueError, FFmpegExecutionError) as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit(1) from error

    typer.secho("Build 流程完成" if not dry_run else "Dry run 完成", fg=typer.colors.GREEN)
    typer.echo(f"輸出影片：{result.output_path}")
    typer.echo(f"合併音軌：{result.merged_audio_path}")
    typer.echo(f"章節檔：{result.chapter_path}")
    typer.echo(f"總時長：{_format_duration(result.total_duration_seconds)}")
    typer.echo(f"音檔數量：{len(result.audio_probes)}")

    typer.echo("\nYouTube 章節預覽：")
    for line in format_youtube_chapters(result.chapter_entries):
        typer.echo(f"  {line}")

    typer.echo("\n計畫執行的命令：")
    for command in result.command_log:
        typer.echo(f"  {command}")


@app.command("probe")
def probe(
    target_path: Annotated[Path, typer.Argument(help="單一 m4a 檔案，或包含 m4a 的資料夾")],
    config_path: Annotated[Path, typer.Option("--config", "-c", help="設定檔路徑")] = DEFAULT_CONFIG,
) -> None:
    """探測音檔資訊。"""
    try:
        config = _load_config(config_path)
        workflow = _create_workflow(config)
        probes = workflow.probe_target(target_path)
    except (FileNotFoundError, ValueError, FFmpegExecutionError) as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit(1) from error

    for probe_result in probes:
        typer.echo(probe_result.path.name)
        typer.echo(f"  codec      : {probe_result.codec_name}")
        typer.echo(f"  sample_rate: {probe_result.sample_rate}")
        typer.echo(f"  channels   : {probe_result.channels}")
        typer.echo(f"  duration   : {_format_duration(probe_result.duration_seconds)}")


@app.command("template")
def template_list() -> None:
    """列出所有可用模板。"""
    for name, description in FFmpegRunner.get_template_descriptions().items():
        typer.echo(f"{name:10} {description}")


@app.command("?")
@app.command("help")
def help_command(ctx: typer.Context) -> None:
    """顯示 CLI 指令說明。"""
    help_context = ctx.parent or ctx
    typer.echo(help_context.get_help())


if __name__ == "__main__":
    app()
