from dataclasses import dataclass


@dataclass(frozen=True)
class DynamicItem:
    dynamic_id: str
    uid: int
    author_name: str
    published_at: int
    kind: str
    text: str
    image_url: str | None = None
