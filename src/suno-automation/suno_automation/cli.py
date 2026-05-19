"""CLI 入口，串接 PromptBuilder、SunoClient、Downloader、WorkflowHook。"""

import asyncio
import sys
import tomllib
from pathlib import Path
from typing import Annotated, Optional

# Windows 終端機強制 UTF-8 輸出，避免中文亂碼
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .downloader import Downloader
from .prompt_builder import PromptBuilder, PromptConfig, PromptResult
from .suno_client import SunoClient
from .workflow_hook import WorkflowHook

app = typer.Typer(
    name="suno-automation",
    help="Suno AI 音樂自動化生成工具",
    add_completion=False,
)
auth_app = typer.Typer(help="登入狀態管理")
app.add_typer(auth_app, name="auth")
console = Console()

# 預設設定檔與元素庫路徑
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_CONFIG = DEFAULT_CONFIG_DIR / "settings.toml"
DEFAULT_STATE_FILE = DEFAULT_CONFIG_DIR / ".browser_state.json"


def _load_config(config_path: Path) -> dict:
    """載入 TOML 設定檔。"""
    if not config_path.exists():
        console.print(f"[red]找不到設定檔：{config_path}[/red]")
        console.print("[yellow]請確認 config/settings.toml 存在並填入設定值[/yellow]")
        raise typer.Exit(1)
    with config_path.open("rb") as f:
        return tomllib.load(f)


def _build_prompt_config(cfg: dict) -> PromptConfig:
    """從設定檔建立 PromptConfig 物件。"""
    p = cfg.get("prompt", {})
    return PromptConfig(
        # 風格特化格式
        elements_per_context=p.get("elements_per_context", 1),
        elements_per_mood=p.get("elements_per_mood", 1),
        elements_per_instrument=p.get("elements_per_instrument", 2),
        elements_per_texture=p.get("elements_per_texture", 2),
        elements_per_rhythm=p.get("elements_per_rhythm", 1),
        elements_per_purpose=p.get("elements_per_purpose", 1),
        elements_per_structure=p.get("elements_per_structure", 1),
        elements_per_development=p.get("elements_per_development", 1),
        elements_per_ending=p.get("elements_per_ending", 1),
        elements_per_restriction=p.get("elements_per_restriction", 2),
        # 通用格式
        elements_per_genre=p.get("elements_per_genre", 1),
        elements_per_tempo=p.get("elements_per_tempo", 1),
        elements_per_vocal=p.get("elements_per_vocal", 1),
        # 固定附加詞（不受隨機取樣影響，每次都附加）
        fixed_tags=p.get("fixed_tags", []),
    )


def _resolve_style(style: str | None, cfg: dict) -> str | None:
    """解析風格名稱：CLI 參數 > settings.toml default_style > None（通用庫）"""
    if style:
        return style
    return cfg.get("prompt", {}).get("default_style") or None


def _create_suno_client(
    cfg: dict,
    *,
    count: int | None = None,
    headless_override: bool | None = None,
) -> SunoClient:
    """建立使用固定 session 路徑的 SunoClient。"""
    suno_cfg = cfg["suno"]
    songs_per_run = suno_cfg.get("songs_per_run", 2) if count is None else count
    headless = suno_cfg.get("headless", False) if headless_override is None else headless_override

    return SunoClient(
        headless=headless,
        generation_timeout=suno_cfg.get("generation_timeout_seconds", 300),
        songs_per_run=min(songs_per_run, 2),
        state_file=DEFAULT_STATE_FILE,
    )


@app.command("gen")
def gen(
    prompt: Annotated[
        Optional[str],
        typer.Option("--prompt", "-p", help="手動指定完整提示詞（不填則依風格隨機組合）"),
    ] = None,
    style: Annotated[
        Optional[str],
        typer.Option("--style", "-s", help="指定風格（study_focus / sleep_relax / work_home / rain / cafe / night）"),
    ] = None,
    count: Annotated[
        Optional[int],
        typer.Option("--count", "-n", help="產出歌曲數量（每次最多 2 首）"),
    ] = None,
    config_path: Annotated[
        Path,
        typer.Option("--config", "-c", help="設定檔路徑"),
    ] = DEFAULT_CONFIG,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="僅顯示將使用的提示詞，不實際執行生成"),
    ] = False,
) -> None:
    """
    觸發 Suno 音樂生成流程。

    未指定 --prompt 時，依 --style 從 PromptPool 隨機組合提示詞。
    未指定 --style 時，使用 settings.toml 的 default_style。
    """
    cfg = _load_config(config_path)
    resolved_style = _resolve_style(style, cfg)

    # 建立提示詞
    if prompt:
        final_prompt = prompt
        prompt_result: PromptResult | None = None
    else:
        prompt_cfg = _build_prompt_config(cfg)
        builder = PromptBuilder.from_style(resolved_style, DEFAULT_CONFIG_DIR, prompt_cfg)
        prompt_result = builder.build_detail()
        final_prompt = prompt_result.prompt

    style_label = f"[dim]（風格：{resolved_style}）[/dim]" if resolved_style else ""
    console.print(Panel(
        f"[bold cyan]Prompt:[/bold cyan] {final_prompt}\n{style_label}",
        title="Suno 自動化生成",
        border_style="blue",
    ))

    if dry_run:
        console.print("[yellow]--dry-run 模式：未實際執行生成[/yellow]")
        return

    asyncio.run(_run_generation(cfg, final_prompt, count, resolved_style, prompt_result))


async def _run_generation(
    cfg: dict,
    prompt: str,
    count: int | None,
    style: str | None = None,
    prompt_result: PromptResult | None = None,
) -> None:
    """執行完整的生成、下載、通知流程。"""
    output_cfg = cfg["output"]
    workflow_cfg = cfg["workflow"]

    client = _create_suno_client(cfg, count=count)
    downloader = Downloader(
        download_dir=Path(output_cfg.get("download_dir", "./output")),
        filename_format=output_cfg.get("filename_format", "{timestamp}_{title}"),
    )
    hook = WorkflowHook(
        event_log_path=Path(workflow_cfg.get("event_log_path", "./output/events.jsonl")),
    )

    async with client:
        await client.ensure_logged_in()
        songs = await client.generate(prompt)

    if not songs:
        console.print("[red]未取得任何歌曲，請確認 Suno 頁面狀態[/red]")
        return

    # 為每首歌組出對應的 metadata
    metadata_base: dict = {"style": style, "prompt": prompt}
    if prompt_result:
        metadata_base["parts"] = prompt_result.parts
    metadatas = [metadata_base for _ in songs]

    saved_paths = await downloader.download_batch(songs, metadatas=metadatas)
    await hook.notify(songs, saved_paths)

    # 顯示結果摘要
    table = Table(title="生成結果", show_lines=True)
    table.add_column("標題", style="cyan")
    table.add_column("Song ID", style="dim")
    table.add_column("本機路徑", style="green")

    for song, path in zip(songs, saved_paths):
        table.add_row(song.title, song.song_id[:12], str(path))

    console.print(table)


@auth_app.command("login")
def auth_login(
    config_path: Annotated[
        Path,
        typer.Option("--config", "-c", help="設定檔路徑"),
    ] = DEFAULT_CONFIG,
) -> None:
    """開啟瀏覽器完成登入，並保存 session。"""
    cfg = _load_config(config_path)
    console.print(f"[cyan]Session 檔案位置：{DEFAULT_STATE_FILE}[/cyan]")
    console.print("[yellow]即將開啟可見瀏覽器，請手動完成 Suno 登入[/yellow]")
    console.print("[yellow]登入成功後程式會自動保存 session；若先關閉瀏覽器則視為取消登入[/yellow]")
    asyncio.run(_run_auth_login(cfg))


async def _run_auth_login(cfg: dict) -> None:
    """執行登入並保存 session。"""
    client = _create_suno_client(cfg, headless_override=False)
    async with client:
        await client.ensure_logged_in()

    if DEFAULT_STATE_FILE.exists():
        console.print(f"[green]登入狀態已保存：{DEFAULT_STATE_FILE}[/green]")
    else:
        console.print("[red]登入流程已完成，但未找到 session 檔案，請重新執行 auth login[/red]")


@auth_app.command("status")
def auth_status(
    config_path: Annotated[
        Path,
        typer.Option("--config", "-c", help="設定檔路徑"),
    ] = DEFAULT_CONFIG,
) -> None:
    """檢查本機保存的 Suno 登入狀態是否可用。"""
    if not DEFAULT_STATE_FILE.exists():
        console.print(f"[red]找不到登入狀態檔：{DEFAULT_STATE_FILE}[/red]")
        console.print("[yellow]請先執行 `uv run suno auth login`[/yellow]")
        raise typer.Exit(1)

    cfg = _load_config(config_path)
    console.print(f"[cyan]檢查 session：{DEFAULT_STATE_FILE}[/cyan]")
    is_valid = asyncio.run(_run_auth_status(cfg))
    if is_valid:
        console.print("[green]目前登入狀態可用[/green]")
        return

    console.print("[red]目前登入狀態已失效，請重新執行 auth login[/red]")
    raise typer.Exit(1)


async def _run_auth_status(cfg: dict) -> bool:
    """回傳目前 session 是否仍可使用。"""
    client = _create_suno_client(cfg, headless_override=True)
    async with client:
        return await client.has_valid_session()


@auth_app.command("clear")
def auth_clear() -> None:
    """刪除本機保存的 Suno 登入狀態。"""
    if not DEFAULT_STATE_FILE.exists():
        console.print(f"[yellow]目前沒有登入狀態檔：{DEFAULT_STATE_FILE}[/yellow]")
        return

    DEFAULT_STATE_FILE.unlink()
    console.print(f"[green]已刪除登入狀態檔：{DEFAULT_STATE_FILE}[/green]")


@app.command("prompt-random")
def prompt_random(
    style: Annotated[
        Optional[str],
        typer.Option("--style", "-s", help="指定風格（study_focus / sleep_relax / work_home / rain / cafe / night）"),
    ] = None,
    count: Annotated[
        int,
        typer.Option("--count", "-n", help="預覽幾組隨機提示詞"),
    ] = 5,
    config_path: Annotated[
        Path,
        typer.Option("--config", "-c", help="設定檔路徑"),
    ] = DEFAULT_CONFIG,
) -> None:
    """預覽隨機組合的提示詞（不執行生成）。"""
    cfg = _load_config(config_path)
    resolved_style = _resolve_style(style, cfg)
    prompt_cfg = _build_prompt_config(cfg)
    builder = PromptBuilder.from_style(resolved_style, DEFAULT_CONFIG_DIR, prompt_cfg)

    title = f"隨機提示詞預覽｜風格：{resolved_style}（{count} 組）" if resolved_style else f"隨機提示詞預覽（{count} 組）"

    prompts = builder.build_batch(count)

    table = Table(title=title, show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Prompt", style="cyan")

    for i, p in enumerate(prompts, 1):
        table.add_row(str(i), p)

    console.print(table)


@app.command("prompt")
def prompt_list() -> None:
    """列出所有可用的 Prompt 風格群組與說明。"""
    import json

    pool_dir = DEFAULT_CONFIG_DIR / "PromptPool"
    styles = PromptBuilder.list_available_styles(DEFAULT_CONFIG_DIR)

    if not styles:
        console.print("[yellow]PromptPool 目錄中尚無風格檔案[/yellow]")
        return

    table = Table(title="可用風格清單", show_lines=True)
    table.add_column("風格名稱", style="cyan", width=20)
    table.add_column("中文名稱", style="bold", width=16)
    table.add_column("說明", style="dim")

    for s in styles:
        path = pool_dir / f"prompt_elements_{s}.json"
        try:
            with path.open(encoding="utf-8") as f:
                meta = json.load(f).get("_meta", {})
            name = meta.get("name", "-")
            desc = meta.get("description", "-")
        except Exception:
            name = desc = "-"
        table.add_row(s, name, desc)

    console.print(table)


@app.command("style")
def style_list() -> None:
    """列出所有可用的 style（prompt 指令別名）。"""
    prompt_list()


@app.command("?")
@app.command("help")
def help_command(ctx: typer.Context) -> None:
    """顯示 CLI 指令說明。"""
    help_context = ctx.parent or ctx
    console.print(help_context.get_help())


if __name__ == "__main__":
    app()
