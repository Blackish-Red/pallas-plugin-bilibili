from collections.abc import Awaitable, Callable
from typing import Any

from pallas.api.utils import HTTPXClient

from .models import DynamicItem

_DYNAMIC_URL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
_SUPPORTED_TYPES = {
    "DYNAMIC_TYPE_DRAW": "draw",
    "DYNAMIC_TYPE_WORD": "word",
    "DYNAMIC_TYPE_AV": "video",
    "DYNAMIC_TYPE_ARTICLE": "article",
    "DYNAMIC_TYPE_FORWARD": "forward",
}


class BilibiliApiError(RuntimeError):
    pass


class BilibiliRiskControlError(BilibiliApiError):
    pass


class BilibiliClient:
    def __init__(
        self,
        *,
        cookie: str = "",
        get_json: Callable[..., Awaitable[dict[str, Any]]] | None = None,
        get_bytes: Callable[..., Awaitable[bytes]] | None = None,
    ) -> None:
        self._cookie = cookie.strip()
        self._get_json = get_json or self._request_json
        self._get_bytes = get_bytes or self._request_bytes

    def _headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Pallas-Bot/1.0)",
            "Referer": "https://www.bilibili.com/",
        }
        if self._cookie:
            headers["Cookie"] = self._cookie
        return headers

    async def fetch_latest(self, uid: int) -> list[DynamicItem]:
        payload = await self._get_json(
            _DYNAMIC_URL,
            params={"host_mid": str(uid), "offset": "", "features": "itemOpusStyle"},
            headers=self._headers(),
            timeout=10.0,
        )
        code = int(payload.get("code", -1))
        if code in {-352, -412}:
            raise BilibiliRiskControlError(str(payload.get("message") or code))
        if code != 0:
            raise BilibiliApiError(str(payload.get("message") or code))
        rows = payload.get("data", {}).get("items", [])
        if not isinstance(rows, list):
            return []
        return [
            item for row in rows if (item := self._parse_item(row, uid)) is not None
        ]

    async def download_image(
        self, url: str, *, max_bytes: int = 10 * 1024 * 1024
    ) -> bytes:
        raw = await self._get_bytes(url, headers=self._headers(), timeout=15.0)
        if not raw or len(raw) > max_bytes:
            raise BilibiliApiError("invalid media size")
        return raw

    @staticmethod
    def _parse_item(row: Any, uid: int) -> DynamicItem | None:
        if not isinstance(row, dict):
            return None
        modules = row.get("modules")
        if not isinstance(modules, dict):
            return None
        tag = modules.get("module_tag")
        if isinstance(tag, dict) and tag.get("text") == "置顶":
            return None
        kind = _SUPPORTED_TYPES.get(str(row.get("type") or ""))
        dynamic_id = str(row.get("id_str") or "")
        author = modules.get("module_author")
        dynamic = modules.get("module_dynamic")
        if (
            not kind
            or not dynamic_id
            or not isinstance(author, dict)
            or not isinstance(dynamic, dict)
        ):
            return None
        major = dynamic.get("major")
        opus = major.get("opus") if isinstance(major, dict) else None
        summary = opus.get("summary") if isinstance(opus, dict) else None
        text = (
            str(summary.get("text") or "")
            if isinstance(summary, dict)
            else str(dynamic.get("desc", {}).get("text") or "")
        )
        pics = opus.get("pics") if isinstance(opus, dict) else []
        image_url = (
            str(pics[0].get("url") or "")
            if isinstance(pics, list) and pics and isinstance(pics[0], dict)
            else ""
        )
        return DynamicItem(
            dynamic_id=dynamic_id,
            uid=uid,
            author_name=str(author.get("name") or uid),
            published_at=int(author.get("pub_ts") or 0),
            kind=kind,
            text=text,
            image_url=image_url or None,
        )

    async def _request_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        response = await HTTPXClient.get(url, **kwargs)
        if response is None:
            raise BilibiliApiError("request failed")
        if response.status_code == 412:
            raise BilibiliRiskControlError("HTTP 412")
        data = response.json()
        if not isinstance(data, dict):
            raise BilibiliApiError("invalid response")
        return data

    async def _request_bytes(self, url: str, **kwargs: Any) -> bytes:
        response = await HTTPXClient.get(url, **kwargs)
        if response is None:
            raise BilibiliApiError("media request failed")
        return response.content
