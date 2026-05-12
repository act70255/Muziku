"""
prompt_builder.py

職責：從元素庫 JSON 檔案中隨機組合 Suno 風格描述提示詞。

支援兩種元素庫格式：
  - 通用格式（prompt_elements.json）：genre / mood / instrument / tempo / vocal / production
  - 風格特化格式（PromptPool/prompt_elements_<style>.json）：
      context / mood / instrument / texture / rhythm / purpose / restriction
"""

import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Windows 終端機強制 UTF-8 輸出，避免中文亂碼
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


# 風格特化元素庫目錄名稱
POOL_DIR_NAME = "PromptPool"


@dataclass
class PromptConfig:
    """各元素類別的選取數量設定。"""

    # ── 風格特化格式（PromptPool）─────────────────────────────
    elements_per_context: int = 1       # 情境詞
    elements_per_mood: int = 1          # 情緒詞
    elements_per_instrument: int = 2    # 樂器詞
    elements_per_texture: int = 2       # 質感詞
    elements_per_rhythm: int = 1        # 節奏限制詞
    elements_per_purpose: int = 1       # 用途詞
    elements_per_restriction: int = 2   # 限制詞

    # ── 通用格式（prompt_elements.json）─────────────────────
    elements_per_genre: int = 1
    elements_per_tempo: int = 1
    elements_per_vocal: int = 1
    elements_per_production: int = 0    # 預設不加入

    # ── 固定附加詞（每次生成都強制加入，不受隨機取樣影響）────────
    fixed_tags: list[str] = field(default_factory=list)


@dataclass
class PromptResult:
    """build_detail() 的回傳值。"""

    prompt: str                      # 完整提示詞字串
    parts: dict[str, list[str]]      # 各類別實際取樣的元素，例如：
                                     #   {"context": ["late night lofi"],
                                     #    "instrument": ["piano", "guitar"],
                                     #    "fixed_tags": ["no vocals"]}


class PromptBuilder:
    """
    從元素庫隨機組合 Suno 風格描述提示詞。

    使用方式（手動指定路徑）：
        builder = PromptBuilder(elements_path, config)
        prompt = builder.build()

    使用方式（依風格名稱載入）：
        builder = PromptBuilder.from_style("rain", config_dir)
        prompt = builder.build()
    """

    def __init__(
        self,
        elements_path: Path,
        config: PromptConfig | None = None,
    ) -> None:
        self._elements: dict[str, list[str]] = self._load_elements(elements_path)
        self._config: PromptConfig = config or PromptConfig()
        # 偵測格式：有 "context" key → 風格特化格式
        self._is_lofi_format: bool = "context" in self._elements

    # ── 類別方法 ────────────────────────────────────────────────

    @classmethod
    def from_style(
        cls,
        style: str | None,
        config_dir: Path,
        config: PromptConfig | None = None,
    ) -> "PromptBuilder":
        """
        依指定風格名稱載入對應的元素庫檔案。

        - style 有效 → 載入對應 PromptPool 檔案
        - style 為 None 或找不到對應風格 → 從 PromptPool 隨機挑選一個

        拋出：
            FileNotFoundError: PromptPool 目錄下找不到任何風格檔時
        """
        available = cls.list_available_styles(config_dir)
        if not available:
            raise FileNotFoundError(
                f"PromptPool 目錄下找不到任何風格檔：{config_dir / POOL_DIR_NAME}"
            )

        if style and style in available:
            chosen = style
        else:
            if style:
                print(f"[PromptBuilder] 找不到 '{style}' 風格，隨機挑選")
            chosen = random.choice(available)

        pool_path = config_dir / POOL_DIR_NAME / f"prompt_elements_{chosen}.json"
        print(f"[PromptBuilder] 載入風格元素庫：{pool_path.name}")
        return cls(pool_path, config)

    @classmethod
    def list_available_styles(cls, config_dir: Path) -> list[str]:
        """掃描 PromptPool 目錄，回傳目前可用的風格名稱清單。"""
        pool_dir = config_dir / POOL_DIR_NAME
        if not pool_dir.exists():
            return []
        return [
            p.stem.removeprefix("prompt_elements_")
            for p in sorted(pool_dir.glob("prompt_elements_*.json"))
        ]

    # ── 靜態方法 ────────────────────────────────────────────────

    @staticmethod
    def _load_elements(path: Path) -> dict[str, list[str]]:
        """載入元素庫 JSON 檔案，自動過濾 _meta 欄位。"""
        if not path.exists():
            raise FileNotFoundError(f"元素庫檔案不存在：{path}")
        with path.open(encoding="utf-8") as f:
            data: dict = json.load(f)
        # 過濾以 "_" 開頭的 meta key
        return {k: v for k, v in data.items() if not k.startswith("_")}

    # ── 私有方法 ────────────────────────────────────────────────

    def _sample(self, category: str, count: int) -> list[str]:
        """從指定類別隨機取樣，若 count <= 0 或類別不存在則回傳空列表。"""
        if count <= 0:
            return []
        pool: list[str] = self._elements.get(category, [])
        if not pool:
            return []
        return random.sample(pool, min(count, len(pool)))

    # ── 公開方法 ────────────────────────────────────────────────

    def build(self) -> str:
        """隨機組合一組 Suno 風格描述提示詞，回傳純字串。"""
        return self.build_detail().prompt

    def build_detail(self) -> "PromptResult":
        """
        隨機組合一組 Suno 風格描述提示詞。

        回傳 PromptResult，包含：
          - prompt: 完整提示詞字串
          - parts:  各類別實際取樣的元素（可用於儲存 metadata）
        """
        sampled: dict[str, list[str]] = {}

        if self._is_lofi_format:
            # 風格特化格式：依 AI-music-tools.md 架構
            # 公式：[情境], [情緒], [樂器], [質感], [節奏限制], [用途], [限制詞]
            sampled["context"]     = self._sample("context",     self._config.elements_per_context)
            sampled["mood"]        = self._sample("mood",        self._config.elements_per_mood)
            sampled["instrument"]  = self._sample("instrument",  self._config.elements_per_instrument)
            sampled["texture"]     = self._sample("texture",     self._config.elements_per_texture)
            sampled["rhythm"]      = self._sample("rhythm",      self._config.elements_per_rhythm)
            sampled["purpose"]     = self._sample("purpose",     self._config.elements_per_purpose)
            sampled["restriction"] = self._sample("restriction", self._config.elements_per_restriction)
        else:
            # 通用格式：原有結構
            sampled["genre"]      = self._sample("genre",      self._config.elements_per_genre)
            sampled["mood"]       = self._sample("mood",       self._config.elements_per_mood)
            sampled["instrument"] = self._sample("instrument", self._config.elements_per_instrument)
            sampled["tempo"]      = self._sample("tempo",      self._config.elements_per_tempo)
            sampled["vocal"]      = self._sample("vocal",      self._config.elements_per_vocal)
            sampled["production"] = self._sample("production", self._config.elements_per_production)

        # 附加固定標籤，空字串與已出現的跳過（避免重複或污染 prompt）
        all_parts: list[str] = [item for items in sampled.values() for item in items]
        existing: set[str] = set(all_parts)
        fixed_added: list[str] = []
        for tag in self._config.fixed_tags:
            if tag.strip() and tag not in existing:
                all_parts.append(tag)
                fixed_added.append(tag)

        if fixed_added:
            sampled["fixed_tags"] = fixed_added

        # 過濾空類別，保持 JSON 整潔
        clean_parts = {k: v for k, v in sampled.items() if v}

        return PromptResult(prompt=", ".join(all_parts), parts=clean_parts)

    def build_batch(self, count: int) -> list[str]:
        """一次產出多個不同的提示詞組合（純字串）。"""
        return [self.build() for _ in range(count)]
