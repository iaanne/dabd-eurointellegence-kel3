from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from .config import Settings


def build_client(settings: Settings) -> httpx.Client:
    return httpx.Client(
        timeout=settings.http_timeout_seconds,
        headers={
            "User-Agent": settings.user_agent,
            "Accept": "application/json",
        },
        follow_redirects=True,
    )


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


@retry(
    retry=retry_if_exception(_retryable),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=1, max=15),
    reraise=True,
)
def get_json(client: httpx.Client, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.get(url, params=params)
    if response.status_code >= 400:
        raise httpx.HTTPStatusError(
            f"GET {response.request.url} gagal dengan status {response.status_code}: "
            f"{response.text[:300]}",
            request=response.request,
            response=response,
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Respons dari {url} bukan objek JSON.")
    return payload