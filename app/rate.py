import time
from collections import deque

from app.config import TPM_LIMIT as DEFAULT_TPM


class TokenPacer:
    def __init__(self, tokens_per_minute: int = DEFAULT_TPM) -> None:
        self.tokens_per_minute = tokens_per_minute
        self.events: deque[tuple[float, int]] = deque()

    def wait(self, tokens_used: int, floor: float = 0.0) -> None:
        if floor:
            time.sleep(floor)
        now = time.time()
        while self.events and now - self.events[0][0] >= 60:
            self.events.popleft()
        used = sum(tokens for _, tokens in self.events)
        if self.events and used + tokens_used > self.tokens_per_minute:
            time.sleep(max(0.0, 60 - (now - self.events[0][0]) + 0.5))
            self.events.clear()
        self.events.append((time.time(), tokens_used))
