"""
suno_client.py

職責：使用 Playwright 控制瀏覽器，登入 Suno 並送出音樂生成請求。
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)


# Suno 網頁各功能的 URL
SUNO_BASE_URL = "https://suno.com"
SUNO_CREATE_URL = f"{SUNO_BASE_URL}/create"
DEFAULT_STATE_FILE = Path(__file__).resolve().parent.parent / "config" / ".browser_state.json"


@dataclass
class SunoSong:
    """代表一首生成完成的歌曲資訊。"""
    title: str
    song_id: str
    audio_url: str
    prompt: str
    duration_seconds: float = 0.0
    extra: dict = field(default_factory=dict)


class SunoClient:
    """
    以 Playwright 控制 Suno 網頁，執行登入與音樂生成流程。

    使用方式（async context manager）：
        async with SunoClient(config) as client:
            songs = await client.generate(prompt="pop, upbeat, piano")
    """

    def __init__(
        self,
        headless: bool = False,
        login_method: str = "google",
        generation_timeout: int = 300,
        songs_per_run: int = 2,
        state_file: Path | None = None,
    ) -> None:
        self._headless = headless
        self._login_method = login_method
        self._generation_timeout = generation_timeout
        self._songs_per_run = min(songs_per_run, 2)  # Suno 每次最多 2 首
        # 儲存已登入的 browser state，避免每次重新登入
        self._state_file: Path = state_file or DEFAULT_STATE_FILE

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # ── 生命週期管理 ────────────────────────────────────────────────────────

    async def __aenter__(self) -> "SunoClient":
        await self._start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._stop()

    async def _start(self) -> None:
        """啟動 Playwright 瀏覽器並載入已儲存的登入狀態。"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        # 若存在已儲存的登入狀態則直接載入，避免重複登入
        if self._state_file.exists():
            self._context = await self._browser.new_context(
                storage_state=str(self._state_file)
            )
        else:
            self._context = await self._browser.new_context()

        self._page = await self._context.new_page()

    async def _stop(self) -> None:
        """關閉瀏覽器並釋放資源。"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # ── 登入流程 ────────────────────────────────────────────────────────────

    async def ensure_logged_in(self) -> None:
        """
        確保目前已登入 Suno。
        若尚未登入則引導使用者完成手動登入後儲存 session。
        """
        assert self._page is not None

        await self._page.goto(SUNO_BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        if await self._is_logged_in():
            return

        print("[Suno] 尚未登入，請在瀏覽器視窗中完成登入流程...")
        await self._page.goto(f"{SUNO_BASE_URL}/sign-in", wait_until="domcontentloaded")

        # 等待使用者手動完成登入（偵測登入成功的特徵元素出現）
        await self._page.wait_for_selector(
            "[data-testid='user-avatar'], [aria-label='Create']",
            timeout=120_000,  # 給使用者 2 分鐘完成登入
        )

        # 儲存登入後的 session 狀態
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(self._state_file))  # type: ignore[union-attr]
        print(f"[Suno] 登入成功，session 已儲存至 {self._state_file}")

    async def has_valid_session(self) -> bool:
        """檢查目前儲存的 session 是否仍可用。"""
        assert self._page is not None

        await self._page.goto(SUNO_BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        return await self._is_logged_in()

    async def _is_logged_in(self) -> bool:
        """檢查目前頁面是否已登入。"""
        assert self._page is not None
        try:
            await self._page.wait_for_selector(
                "[data-testid='user-avatar'], [aria-label='Create']",
                timeout=5_000,
            )
            return True
        except Exception:
            return False

    # ── 音樂生成流程 ─────────────────────────────────────────────────────────

    async def generate(self, prompt: str) -> list[SunoSong]:
        """
        送出音樂生成請求並等待完成，回傳生成的歌曲列表。

        參數：
            prompt: 風格描述提示詞，例如 "pop, upbeat, piano, female vocals"

        回傳：
            SunoSong 列表（通常 1~2 首）
        """
        assert self._page is not None

        await self._page.goto(SUNO_CREATE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 確認是否在 Custom Mode（有獨立的 Style 輸入框）
        await self._ensure_custom_mode()

        # 填入風格描述
        await self._fill_style_prompt(prompt)

        # 點擊生成按鈕
        await self._click_create_button()

        # 等待生成完成並取得歌曲資訊
        songs = await self._wait_for_songs(prompt)

        return songs

    async def _ensure_custom_mode(self) -> None:
        """確保切換到 Custom Mode（顯示 Style of Music 輸入框）。"""
        assert self._page is not None
        try:
            custom_toggle = self._page.locator("button:has-text('Custom')")
            await custom_toggle.wait_for(timeout=5_000)
            # 若按鈕未被選取則點擊切換
            is_active = await custom_toggle.get_attribute("aria-pressed")
            if is_active != "true":
                await custom_toggle.click()
                await asyncio.sleep(1)
        except Exception:
            # 若找不到 Custom 按鈕，假設已在正確模式
            pass

    async def _fill_style_prompt(self, prompt: str) -> None:
        """在 Style of Music 欄位填入提示詞。"""
        assert self._page is not None
        style_input = self._page.locator(
            "textarea[placeholder*='style'], "
            "textarea[aria-label*='Style'], "
            "[data-testid='style-input']"
        ).first
        await style_input.wait_for(timeout=10_000)
        await style_input.click()
        await style_input.fill(prompt)
        await asyncio.sleep(0.5)

    async def _click_create_button(self) -> None:
        """點擊 Create 按鈕送出生成請求。"""
        assert self._page is not None
        create_btn = self._page.locator(
            "button:has-text('Create'), button[aria-label='Create']"
        ).first
        await create_btn.wait_for(timeout=10_000)
        await create_btn.click()
        await asyncio.sleep(2)

    async def _wait_for_songs(self, prompt: str) -> list[SunoSong]:
        """
        輪詢等待歌曲生成完成，回傳 SunoSong 列表。
        超過 generation_timeout 則拋出 TimeoutError。
        """
        assert self._page is not None
        print(f"[Suno] 等待歌曲生成（最長 {self._generation_timeout} 秒）...")

        elapsed = 0
        poll_interval = 5

        while elapsed < self._generation_timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            songs = await self._extract_completed_songs(prompt)
            if songs:
                print(f"[Suno] 生成完成，共 {len(songs)} 首歌曲")
                return songs

            print(f"[Suno] 仍在生成中... ({elapsed}s)")

        raise TimeoutError(
            f"歌曲生成逾時（{self._generation_timeout} 秒），請確認 Suno 網頁狀態"
        )

    async def _extract_completed_songs(self, prompt: str) -> list[SunoSong]:
        """
        從頁面中解析已完成生成的歌曲資訊。
        回傳空列表表示尚未完成。
        """
        assert self._page is not None
        songs: list[SunoSong] = []

        try:
            # 尋找歌曲卡片（Suno 使用動態渲染，選擇器可能因版本異動）
            song_cards = await self._page.locator(
                "[data-testid='song-card'], .song-card, [class*='SongCard']"
            ).all()

            for card in song_cards[:self._songs_per_run]:
                # 確認是否已完成（有播放按鈕或下載按鈕）
                is_done = await card.locator(
                    "button[aria-label*='Download'], button[aria-label*='Play']"
                ).count()
                if not is_done:
                    continue

                title = await self._extract_song_title(card)
                song_id = await self._extract_song_id(card)
                audio_url = await self._extract_audio_url(card)

                if audio_url:
                    songs.append(SunoSong(
                        title=title,
                        song_id=song_id,
                        audio_url=audio_url,
                        prompt=prompt,
                    ))
        except Exception as e:
            print(f"[Suno] 解析歌曲資訊時發生例外：{e}")

        return songs

    async def _extract_song_title(self, card: object) -> str:
        """從歌曲卡片提取標題。"""
        try:
            title_el = card.locator(  # type: ignore[union-attr]
                "[data-testid='song-title'], .song-title, h3, h4"
            ).first
            return (await title_el.inner_text()).strip()
        except Exception:
            return "untitled"

    async def _extract_song_id(self, card: object) -> str:
        """從歌曲卡片提取歌曲 ID。"""
        try:
            link = card.locator("a[href*='/song/']").first  # type: ignore[union-attr]
            href = await link.get_attribute("href") or ""
            return href.split("/song/")[-1].split("?")[0]
        except Exception:
            return ""

    async def _extract_audio_url(self, card: object) -> str:
        """從歌曲卡片提取音訊檔案 URL。"""
        try:
            audio_el = card.locator("audio").first  # type: ignore[union-attr]
            return await audio_el.get_attribute("src") or ""
        except Exception:
            return ""
