"""
Perceptual-hash-based screen deduplication for native app crawling.

Native apps have no URLs, so deduplication is based on a combination of
a perceptual hash of the screenshot and a text summary of visible elements.
"""
import base64
import hashlib
import io
import logging
from typing import Set

logger = logging.getLogger(__name__)

try:
    import imagehash
    from PIL import Image
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    _IMAGEHASH_AVAILABLE = False


class MobileStateRegistry:
    """
    Tracks which screens have already been visited during a native crawl.

    Uses a perceptual hash (pHash) of the screenshot combined with a short
    text summary of the visible element labels. This means two screens that
    look visually identical and have the same labels are treated as the same
    state even if their underlying view hierarchy IDs differ.

    Falls back to an MD5 of the raw bytes when ``imagehash`` is not installed.
    """

    def __init__(self):
        self._seen: Set[str] = set()

    def has_seen(self, screenshot_b64: str, element_text_summary: str) -> bool:
        """
        Return True if this screen state has been visited before.

        Args:
            screenshot_b64: Base-64-encoded PNG from driver.get_screenshot_as_base64()
            element_text_summary: Pipe-joined text of the top visible elements

        Returns:
            True if the state is already in the registry
        """
        return self._key(screenshot_b64, element_text_summary) in self._seen

    def register(self, screenshot_b64: str, element_text_summary: str) -> None:
        """
        Mark a screen state as visited.

        Args:
            screenshot_b64: Base-64-encoded PNG
            element_text_summary: Pipe-joined text of the top visible elements
        """
        self._seen.add(self._key(screenshot_b64, element_text_summary))

    def size(self) -> int:
        """Return the number of unique states registered so far."""
        return len(self._seen)

    # ------------------------------------------------------------------

    def _key(self, screenshot_b64: str, element_text_summary: str) -> str:
        """
        Build a deduplication key from the screenshot and element summary.

        When imagehash is available the key uses pHash (tolerates minor
        rendering differences); otherwise falls back to MD5 of raw bytes.
        """
        if _IMAGEHASH_AVAILABLE:
            img_hash = self._phash(screenshot_b64)
        else:
            raw_bytes = base64.b64decode(screenshot_b64)
            img_hash = hashlib.md5(raw_bytes).hexdigest()

        combined = f"{img_hash}:{element_text_summary}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _phash(self, screenshot_b64: str) -> str:
        """Compute perceptual hash string from a base-64 PNG."""
        try:
            raw = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(raw))
            return str(imagehash.phash(img))
        except Exception as exc:
            logger.debug(f"pHash computation failed, using MD5 fallback: {exc}")
            raw = base64.b64decode(screenshot_b64)
            return hashlib.md5(raw).hexdigest()
