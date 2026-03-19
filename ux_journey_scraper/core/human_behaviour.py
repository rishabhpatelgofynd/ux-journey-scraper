"""
Human behavior simulation for anti-bot detection.

Implements realistic mouse movements, typing patterns, and timing delays
to make automated browsing indistinguishable from human interaction.
"""
import asyncio
import math
import random
from typing import List, Tuple


class HumanBehaviour:
    """Simulates human-like browser interactions."""

    @staticmethod
    def bezier_curve(
        start: Tuple[float, float],
        end: Tuple[float, float],
        control_points: int = 2,
        steps: int = 20,
    ) -> List[Tuple[float, float]]:
        """
        Generate a Bezier curve path from start to end.

        Human mouse movements don't travel in straight lines - they follow
        curved paths with slight deviations.

        Args:
            start: Starting (x, y) coordinate
            end: Ending (x, y) coordinate
            control_points: Number of control points (default 2 = cubic Bezier)
            steps: Number of points along the curve

        Returns:
            List of (x, y) coordinates forming a smooth curve
        """
        # Generate random control points between start and end
        controls = []
        for _ in range(control_points):
            # Add random deviation perpendicular to the straight line
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2

            # Random offset perpendicular to the line
            offset_x = random.uniform(-50, 50)
            offset_y = random.uniform(-50, 50)

            controls.append((mid_x + offset_x, mid_y + offset_y))

        # Combine all points: start + controls + end
        all_points = [start] + controls + [end]

        # Generate Bezier curve points
        curve = []
        for t in range(steps + 1):
            t_normalized = t / steps
            point = HumanBehaviour._bezier_point(all_points, t_normalized)
            curve.append(point)

        return curve

    @staticmethod
    def _bezier_point(points: List[Tuple[float, float]], t: float) -> Tuple[float, float]:
        """Calculate a single point on a Bezier curve using De Casteljau's algorithm."""
        if len(points) == 1:
            return points[0]

        # Linearly interpolate between consecutive points
        new_points = []
        for i in range(len(points) - 1):
            x = (1 - t) * points[i][0] + t * points[i + 1][0]
            y = (1 - t) * points[i][1] + t * points[i + 1][1]
            new_points.append((x, y))

        return HumanBehaviour._bezier_point(new_points, t)

    @staticmethod
    async def human_mouse_move(
        page,
        to_x: float,
        to_y: float,
        from_x: float = None,
        from_y: float = None,
        duration_ms: int = None,
    ) -> None:
        """
        Move mouse cursor in a human-like curved path.

        Args:
            page: Playwright page object
            to_x: Target x coordinate
            to_y: Target y coordinate
            from_x: Starting x (defaults to current position estimate)
            from_y: Starting y (defaults to current position estimate)
            duration_ms: Movement duration in milliseconds (auto-calculated if None)
        """
        # Estimate current position if not provided
        if from_x is None or from_y is None:
            # Default to center of viewport
            viewport = page.viewport_size
            from_x = viewport["width"] / 2
            from_y = viewport["height"] / 2

        # Calculate duration based on distance (faster for short moves)
        if duration_ms is None:
            distance = math.sqrt((to_x - from_x) ** 2 + (to_y - from_y) ** 2)
            # Human moves ~1000px/sec on average, but varies
            base_speed = random.uniform(800, 1200)  # px/sec
            duration_ms = int((distance / base_speed) * 1000)
            duration_ms = max(50, min(duration_ms, 2000))  # Clamp to 50-2000ms

        # Generate Bezier curve path
        steps = max(10, duration_ms // 50)  # More steps for longer movements
        path = HumanBehaviour.bezier_curve((from_x, from_y), (to_x, to_y), steps=steps)

        # Move along the path with variable speed
        delay_per_step = duration_ms / len(path)
        for x, y in path:
            await page.mouse.move(x, y)
            # Add slight timing variation
            jitter = random.uniform(0.8, 1.2)
            await asyncio.sleep((delay_per_step * jitter) / 1000)

    @staticmethod
    async def human_click(
        page,
        x: float,
        y: float,
        button: str = "left",
        move_to_target: bool = True,
    ) -> None:
        """
        Click at coordinates with human-like behavior.

        Args:
            page: Playwright page object
            x: X coordinate
            y: Y coordinate
            button: Mouse button ("left", "right", "middle")
            move_to_target: Whether to move mouse to target first
        """
        if move_to_target:
            # Move mouse to target with human-like curve
            await HumanBehaviour.human_mouse_move(page, x, y)

        # Small delay before click (human reaction time)
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # Click with slight positional jitter (humans don't click exact pixels)
        click_x = x + random.uniform(-2, 2)
        click_y = y + random.uniform(-2, 2)

        await page.mouse.click(click_x, click_y, button=button)

        # Small delay after click (before next action)
        await asyncio.sleep(random.uniform(0.08, 0.2))

    @staticmethod
    async def human_type(
        page,
        selector: str,
        text: str,
        typo_rate: float = 0.02,
        min_delay_ms: int = 50,
        max_delay_ms: int = 200,
    ) -> None:
        """
        Type text with human-like delays and occasional typos.

        Args:
            page: Playwright page object
            selector: Element selector to type into
            text: Text to type
            typo_rate: Probability of typo per character (0.0 - 1.0)
            min_delay_ms: Minimum delay between keystrokes (ms)
            max_delay_ms: Maximum delay between keystrokes (ms)
        """
        element = await page.query_selector(selector)
        if not element:
            raise ValueError(f"Element not found: {selector}")

        # Click to focus
        await element.click()
        await asyncio.sleep(random.uniform(0.05, 0.1))

        # Type character by character
        for i, char in enumerate(text):
            # Occasionally make a typo
            if random.random() < typo_rate:
                # Type a random wrong character
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                await page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

                # Realize mistake and backspace
                await page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.1, 0.2))

            # Type the correct character
            await page.keyboard.type(char)

            # Variable delay between keystrokes
            # Longer pauses at word boundaries (spaces)
            if char == " ":
                delay = random.uniform(min_delay_ms * 1.5, max_delay_ms * 2)
            else:
                delay = random.uniform(min_delay_ms, max_delay_ms)

            await asyncio.sleep(delay / 1000)

    @staticmethod
    async def human_delay(
        min_ms: int = 600,
        max_ms: int = 1400,
        reason: str = "default",
    ) -> None:
        """
        Wait with human-like timing variation.

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
            reason: Reason for delay (affects distribution)
        """
        # Different delays for different actions
        if reason == "page_load":
            # Longer delays when waiting for page loads
            min_ms = max(min_ms, 800)
            max_ms = max(max_ms, 2000)
        elif reason == "form_think":
            # Thinking before filling a form field
            min_ms = max(min_ms, 400)
            max_ms = max(max_ms, 1200)
        elif reason == "scroll_pause":
            # Brief pause while scrolling
            min_ms = max(min_ms, 200)
            max_ms = max(max_ms, 600)

        # Use beta distribution for more realistic timing
        # Beta(2,5) gives a left-skewed distribution (most delays are shorter)
        alpha, beta = 2, 5
        t = random.betavariate(alpha, beta)
        delay_ms = min_ms + (max_ms - min_ms) * t

        await asyncio.sleep(delay_ms / 1000)

    @staticmethod
    async def human_scroll(
        page,
        direction: str = "down",
        distance: int = None,
        smooth: bool = True,
    ) -> None:
        """
        Scroll page with human-like behavior.

        Args:
            page: Playwright page object
            direction: "down", "up", "to_bottom", "to_top"
            distance: Scroll distance in pixels (auto if None)
            smooth: Use smooth scrolling with pauses
        """
        if direction == "to_bottom":
            # Scroll to bottom progressively
            height = await page.evaluate("document.body.scrollHeight")
            current = 0
            step = random.randint(400, 800)

            while current < height:
                current += step
                await page.evaluate(f"window.scrollTo(0, {current})")
                await HumanBehaviour.human_delay(150, 400, reason="scroll_pause")

        elif direction == "to_top":
            await page.evaluate("window.scrollTo(0, 0)")
            await HumanBehaviour.human_delay(200, 500, reason="scroll_pause")

        else:
            # Scroll by distance
            if distance is None:
                distance = random.randint(300, 600)

            delta = distance if direction == "down" else -distance

            if smooth:
                # Smooth scroll in chunks
                chunks = random.randint(3, 6)
                chunk_size = delta // chunks

                for _ in range(chunks):
                    await page.evaluate(f"window.scrollBy(0, {chunk_size})")
                    await asyncio.sleep(random.uniform(0.05, 0.15))
            else:
                await page.evaluate(f"window.scrollBy(0, {delta})")

            await HumanBehaviour.human_delay(150, 400, reason="scroll_pause")

    @staticmethod
    async def human_hover(page, selector: str, duration_ms: int = None) -> None:
        """
        Hover over an element with human-like movement.

        Args:
            page: Playwright page object
            selector: Element selector to hover over
            duration_ms: Hover duration (auto if None)
        """
        element = await page.query_selector(selector)
        if not element:
            return

        # Get element position
        box = await element.bounding_box()
        if not box:
            return

        # Target center of element with slight randomness
        target_x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        target_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)

        # Move to element
        await HumanBehaviour.human_mouse_move(page, target_x, target_y)

        # Stay on element briefly
        if duration_ms is None:
            duration_ms = random.randint(300, 800)

        await asyncio.sleep(duration_ms / 1000)

    @staticmethod
    def random_viewport_position(
        viewport_width: int,
        viewport_height: int,
        margin: int = 50,
    ) -> Tuple[int, int]:
        """
        Generate a random position within viewport bounds.

        Useful for simulating random mouse movements.

        Args:
            viewport_width: Width of viewport
            viewport_height: Height of viewport
            margin: Margin from edges

        Returns:
            (x, y) coordinates
        """
        x = random.randint(margin, viewport_width - margin)
        y = random.randint(margin, viewport_height - margin)
        return (x, y)
