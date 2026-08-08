from dataclasses import dataclass

from .models import DynamicItem

_KIND_TEXT = {
    "article": "发布了专栏",
    "forward": "转发了动态",
    "video": "发布了视频",
    "word": "发布了动态",
}


@dataclass(frozen=True)
class RenderedDynamic:
    text: str
    image_url: str | None


def render_dynamic(item: DynamicItem) -> RenderedDynamic:
    content = item.text.strip() or _KIND_TEXT.get(item.kind, "发布了动态")
    if len(content) > 480:
        content = f"{content[:479]}…"
    return RenderedDynamic(
        text=f"【B站动态】{item.author_name}\n{content}\nhttps://t.bilibili.com/{item.dynamic_id}",
        image_url=item.image_url if item.kind != "video" else None,
    )
