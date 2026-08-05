from collections import defaultdict, deque
from time import monotonic
from fastapi import HTTPException, Request, status
from app.core.config import settings


class InMemoryRateLimiter:
    """Bezpieczny limiter lokalny; w wielu instancjach zastąp go współdzielonym Redisem."""
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        now = monotonic()
        window = self._requests[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zbyt wiele żądań. Spróbuj ponownie za chwilę.")
        window.append(now)


rate_limiter = InMemoryRateLimiter()

