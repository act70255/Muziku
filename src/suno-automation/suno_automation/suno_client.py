"""
suno_client.py

職責：使用 Playwright 控制瀏覽器，登入 Suno 並送出音樂生成請求。
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    async_playwright,
)


# Suno 網頁各功能的 URL
SUNO_BASE_URL = "https://suno.com"
SUNO_CREATE_URL = f"{SUNO_BASE_URL}/create"
DEFAULT_STATE_FILE = Path(__file__).resolve().parent.parent / "config" / ".browser_state.json"
USER_AVATAR_SELECTOR = "[data-testid='user-avatar']"
CREATE_STUDIO_SELECTOR = ", ".join([
    "[data-testid='profile-menu-button']",
    "[data-testid='lyrics-textarea']",
    "button[aria-label='Advanced']",
    "button[aria-label='Simple']",
])
ADVANCED_MODE_SELECTOR = "button[aria-label='Advanced'], button:has-text('Advanced')"
CREATE_BUTTON_SELECTOR = "button[aria-label='Create song'], button[aria-label='Create'], button:has-text('Create')"
CLIP_ROW_SELECTOR = "[data-testid='clip-row']"
AUTH_COOKIE_KEYWORDS = (
    "session",
    "auth",
    "token",
    "clerk",
    "user",
)


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
        generation_timeout: int = 300,
        songs_per_run: int = 2,
        state_file: Path | None = None,
    ) -> None:
        self._headless = headless
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

        await self._page.goto(SUNO_CREATE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        if await self._is_logged_in():
            print("[Suno] 已偵測到有效登入狀態，略過手動登入")
            return

        print("[Suno] 尚未登入，請在瀏覽器視窗中完成登入流程...")
        await self._page.goto(f"{SUNO_BASE_URL}/sign-in", wait_until="domcontentloaded")

        # 有些 OAuth 流程會停在 Google 中繼頁或另開分頁，改為輪詢整個 context 的登入狀態。
        await self._wait_for_manual_login()

        # 儲存登入後的 session 狀態
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(self._state_file))  # type: ignore[union-attr]
        print(f"[Suno] 登入成功，session 已儲存至 {self._state_file}")

    async def has_valid_session(self) -> bool:
        """檢查目前儲存的 session 是否仍可用。"""
        assert self._page is not None

        await self._page.goto(SUNO_CREATE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        return await self._is_logged_in()

    async def _is_logged_in(self) -> bool:
        """檢查目前頁面是否已登入。"""
        assert self._page is not None
        has_auth_state = await self._context_has_auth_state()
        return await self._page_has_logged_in_signal(self._page, has_auth_state)

    async def _wait_for_manual_login(self) -> None:
        """等待使用者手動完成登入，直到登入成功或使用者主動關閉瀏覽器。"""
        assert self._context is not None
        assert self._browser is not None

        while self._browser.is_connected():
            if await self._find_logged_in_page():
                return

            # 使用者若把所有登入相關頁面都關掉，也視為取消流程，避免無限等待。
            open_pages = [page for page in self._context.pages if not page.is_closed()]
            if not open_pages:
                raise RuntimeError("登入頁面已全部關閉，登入流程已取消")

            await asyncio.sleep(2)

        raise RuntimeError("瀏覽器已關閉，登入流程已取消")

    async def _find_logged_in_page(self) -> bool:
        """檢查目前 context 中是否已有任何 Suno 頁面完成登入。"""
        assert self._context is not None
        has_auth_state = await self._context_has_auth_state()

        for page in self._context.pages:
            if page.is_closed():
                continue

            if await self._page_has_logged_in_signal(page, has_auth_state):
                self._page = page
                return True

        return False

    async def _page_has_logged_in_signal(self, page: Page, has_auth_state: bool = False) -> bool:
        """判斷指定頁面是否已呈現登入後可用的 Suno 介面。"""
        if page.is_closed() or not page.url.startswith(SUNO_BASE_URL):
            return False

        current_url = page.url.lower()
        if "/sign-in" in current_url or "/login" in current_url:
            return False

        try:
            if current_url.startswith(SUNO_CREATE_URL):
                await page.wait_for_selector(CREATE_STUDIO_SELECTOR, timeout=5_000)
                return True

            await page.wait_for_selector(USER_AVATAR_SELECTOR, timeout=5_000)
            return True
        except Exception:
            return has_auth_state and current_url != SUNO_BASE_URL

    async def _context_has_auth_state(self) -> bool:
        """檢查目前 browser context 是否已持有 Suno 可用的授權 cookie。"""
        assert self._context is not None

        cookies = await self._context.cookies()
        for cookie in cookies:
            domain = str(cookie.get("domain", "")).lower()
            name = str(cookie.get("name", "")).lower()
            if "suno.com" not in domain and "clerk" not in domain:
                continue

            if any(keyword in name for keyword in AUTH_COOKIE_KEYWORDS):
                return True

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

        # 新版 Suno create 頁以 Advanced mode 顯示 style prompt。
        await self._ensure_custom_mode()

        # 填入風格描述
        await self._fill_style_prompt(prompt)

        known_song_ids = await self._list_visible_song_ids()

        # 點擊生成按鈕
        await self._click_create_button()

        # 等待生成完成並取得歌曲資訊
        songs = await self._wait_for_songs(prompt, known_song_ids)

        return songs

    async def _ensure_custom_mode(self) -> None:
        """確保切換到 Advanced mode，顯示 style prompt 輸入區。"""
        assert self._page is not None
        try:
            advanced_toggle = self._page.locator(ADVANCED_MODE_SELECTOR).first
            await advanced_toggle.wait_for(timeout=5_000)

            is_active = (
                await advanced_toggle.get_attribute("aria-pressed")
                or await advanced_toggle.get_attribute("aria-selected")
                or await advanced_toggle.get_attribute("data-state")
            )
            if is_active not in {"true", "active", "checked", "on"}:
                await advanced_toggle.click()
                await asyncio.sleep(1)
        except Exception:
            # 若找不到 Advanced 切換，假設目前頁面已可直接輸入。
            pass

    async def _fill_style_prompt(self, prompt: str) -> None:
        """在 Style of Music 欄位填入提示詞。"""
        assert self._page is not None
        style_input = await self._locate_style_prompt()
        await self._set_textarea_value(style_input, prompt)
        await asyncio.sleep(0.5)

    async def _click_create_button(self) -> None:
        """點擊 Create 按鈕送出生成請求。"""
        assert self._page is not None
        create_btn = self._page.locator(CREATE_BUTTON_SELECTOR).first
        await create_btn.wait_for(timeout=10_000)
        await create_btn.click()
        await asyncio.sleep(2)

    async def _locate_style_prompt(self) -> Locator:
        """定位新版 create 頁可編輯的 style prompt 輸入框。"""
        assert self._page is not None

        legacy_selector = self._page.locator(
            "[data-testid='style-input']:visible, "
            "textarea[aria-label*='Style']:visible, "
            "textarea[placeholder*='style' i]:visible"
        ).first
        if await legacy_selector.count():
            return legacy_selector

        visible_textareas = self._page.locator("textarea:visible")
        await visible_textareas.first.wait_for(timeout=10_000)

        candidates = await visible_textareas.count()
        for index in range(candidates):
            candidate = visible_textareas.nth(index)
            placeholder = (await candidate.get_attribute("placeholder") or "").strip().lower()
            testid = (await candidate.get_attribute("data-testid") or "").strip().lower()

            if testid == "lyrics-textarea":
                continue
            if placeholder == "describe the sound you want":
                continue
            if "lyrics" in placeholder:
                continue

            return candidate

        raise TimeoutError("找不到可用的 style prompt 輸入框")

    async def _set_textarea_value(self, locator: Locator, value: str) -> None:
        """以 DOM setter 寫入 textarea，兼容新版 Suno 的覆蓋層與受控元件。"""
        await locator.wait_for(timeout=10_000)
        await locator.evaluate(
            """(element, nextValue) => {
                const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
                setter?.call(element, nextValue);
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            value,
        )

    async def _wait_for_songs(self, prompt: str, known_song_ids: set[str]) -> list[SunoSong]:
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

            songs = await self._extract_completed_songs(prompt, known_song_ids)
            if songs:
                print(f"[Suno] 生成完成，共 {len(songs)} 首歌曲")
                return songs

            print(f"[Suno] 仍在生成中... ({elapsed}s)")

        raise TimeoutError(
            f"歌曲生成逾時（{self._generation_timeout} 秒），請確認 Suno 網頁狀態"
        )

    async def _extract_completed_songs(self, prompt: str, known_song_ids: set[str]) -> list[SunoSong]:
        """
        從頁面中解析已完成生成的歌曲資訊。
        回傳空列表表示尚未完成。
        """
        assert self._page is not None
        songs: list[SunoSong] = []

        try:
            song_rows = self._page.locator(f"{CLIP_ROW_SELECTOR}[data-clip-status='complete']")
            row_count = await song_rows.count()

            for index in range(row_count):
                card = song_rows.nth(index)
                song_id = await self._extract_song_id(card)
                if not song_id or song_id in known_song_ids:
                    continue

                title = await self._extract_song_title(card)
                audio_url = await self._extract_audio_url(card)

                if audio_url:
                    songs.append(SunoSong(
                        title=title,
                        song_id=song_id,
                        audio_url=audio_url,
                        prompt=prompt,
                    ))

                if len(songs) >= self._songs_per_run:
                    break
        except Exception as e:
            print(f"[Suno] 解析歌曲資訊時發生例外：{e}")

        return songs

    async def _list_visible_song_ids(self) -> set[str]:
        """列出目前 create 頁已存在的歌曲 ID，用於排除舊生成結果。"""
        assert self._page is not None

        song_ids: set[str] = set()
        rows = self._page.locator(CLIP_ROW_SELECTOR)
        row_count = await rows.count()
        for index in range(row_count):
            song_id = await self._extract_song_id(rows.nth(index))
            if song_id:
                song_ids.add(song_id)
        return song_ids

    async def _extract_song_title(self, card: object) -> str:
        """從歌曲卡片提取標題。"""
        try:
            title_el = card.locator(  # type: ignore[union-attr]
                ".clip-title-wrapper a, [data-testid='song-title'], .song-title, h3, h4"
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
        assert self._page is not None
        try:
            song_id = await self._extract_song_id(card)
            if not song_id:
                return ""

            play_target = card.locator(  # type: ignore[union-attr]
                "[aria-label^='Play '], .clip-image-container[role='button']"
            ).first
            current_src = await self._page.locator("#active-audio-play").get_attribute("src") or ""

            await play_target.click(force=True)
            audio_url = await self._wait_for_active_audio_src(song_id, current_src)
            if audio_url:
                return audio_url

            return self._build_fallback_audio_url(song_id)
        except Exception:
            return ""

    async def _wait_for_active_audio_src(self, song_id: str, previous_src: str) -> str:
        """等待播放列載入指定歌曲的實際音訊 URL。"""
        assert self._page is not None

        active_audio = self._page.locator("#active-audio-play")
        for _ in range(20):
            src = await active_audio.get_attribute("src") or ""
            if src and song_id in src:
                return src
            if src and src != previous_src and "sil-100.mp3" not in src:
                return src
            await asyncio.sleep(0.5)

        return ""

    @staticmethod
    def _build_fallback_audio_url(song_id: str) -> str:
        """新版 Suno 播放來源通常遵循固定 CDN 命名。"""
        return f"https://cdn1.suno.ai/{song_id}.m4a"
