"""
File-backed persistent navigation queue.

Saves queue state to JSON on disk so crawl progress survives crashes.
On restart, loads pending actions and skips completed ones.
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .navigation_queue import NavigationAction, NavigationQueue

logger = logging.getLogger(__name__)


class PersistentQueue:
    """Navigation queue that persists state to disk for crash recovery.

    Wraps NavigationQueue with file-backed persistence. State is saved
    to a JSON file periodically (every ``save_interval`` operations) and
    on explicit ``save()`` calls.

    On construction, if ``persist_path`` already exists the queue is
    restored from it — completed actions are skipped automatically.

    Args:
        persist_path: Path to the JSON file used for persistence.
        max_depth: Maximum crawl depth forwarded to the inner queue.
        save_interval: Number of mutating operations between auto-saves.
    """

    def __init__(
        self,
        persist_path: str,
        max_depth: int = 8,
        save_interval: int = 10,
    ) -> None:
        self.persist_path = Path(persist_path)
        self.max_depth = max_depth
        self.save_interval = save_interval

        self._queue = NavigationQueue(max_depth=max_depth)
        self._completed: List[Dict[str, Any]] = []
        self._completed_sigs: set = set()
        self._ops_since_save = 0

        # Restore from disk if a previous run left state behind
        if self.persist_path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, action: NavigationAction) -> bool:
        """Add an action to the queue unless it was already completed.

        Args:
            action: The navigation action to enqueue.

        Returns:
            True if the action was added, False if rejected (duplicate,
            over depth limit, or already completed).
        """
        sig = self._queue._action_signature(action)
        if sig in self._completed_sigs:
            return False

        added = self._queue.add(action)
        if added:
            self._tick()
        return added

    def next(self) -> Optional[NavigationAction]:
        """Pop and return the highest-priority pending action.

        Returns:
            The next ``NavigationAction``, or ``None`` when the queue is
            empty.
        """
        return self._queue.next()

    def mark_completed(self, action: NavigationAction) -> None:
        """Record an action as completed so it is skipped on reload.

        Args:
            action: The action that was successfully processed.
        """
        sig = self._queue._action_signature(action)
        if sig not in self._completed_sigs:
            self._completed_sigs.add(sig)
            self._completed.append(asdict(action))
            self._tick()

    def save(self) -> None:
        """Persist current queue and completed state to disk."""
        state = {
            "max_depth": self.max_depth,
            "pending": [asdict(a) for a in self._queue.queue],
            "completed": self._completed,
            "actions_processed": self._queue.actions_processed,
        }
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.persist_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2))
            tmp.replace(self.persist_path)
            logger.debug("Queue state saved to %s", self.persist_path)
        except Exception as e:
            logger.error("Failed to save queue state: %s", e)

    def get_stats(self) -> Dict[str, Any]:
        """Return queue and completion statistics.

        Returns:
            Dictionary with ``queue_size``, ``completed_count``,
            ``actions_processed``, ``max_depth``, and ``persist_path``.
        """
        stats = self._queue.get_stats()
        stats["completed_count"] = len(self._completed)
        stats["persist_path"] = str(self.persist_path)
        return stats

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Bump the operation counter and auto-save if interval reached."""
        self._ops_since_save += 1
        if self._ops_since_save >= self.save_interval:
            self.save()
            self._ops_since_save = 0

    def _load(self) -> None:
        """Restore queue state from the persistence file."""
        try:
            data = json.loads(self.persist_path.read_text())

            # Rebuild completed set first so add() can skip them
            for item in data.get("completed", []):
                action = NavigationAction(**item)
                sig = self._queue._action_signature(action)
                self._completed_sigs.add(sig)
                self._completed.append(item)

            # Re-enqueue pending actions (add() filters completed ones)
            for item in data.get("pending", []):
                action = NavigationAction(**item)
                self._queue.add(action)

            self._queue.actions_processed = data.get("actions_processed", 0)
            logger.info(
                "Restored queue: %d pending, %d completed",
                self._queue.size(),
                len(self._completed),
            )
        except Exception as e:
            logger.error("Failed to load queue state from %s: %s", self.persist_path, e)
