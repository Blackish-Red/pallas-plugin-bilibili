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
    image_urls: tuple[str, ...] = ()


def render_dynamic(item: DynamicItem) -> RenderedDynamic:
    if item.video_url:
        title = item.text.strip() or "发布了视频"
        if len(title) > 480:
            title = f"{title[:479]}…"
        text = f"【B站动态】{item.author_name}\n{title}\n{item.video_url}"
        return RenderedDynamic(text=text, image_urls=item.image_urls)
    content = item.text.strip() or _KIND_TEXT.get(item.kind, "发布了动态")
    if len(content) > 480:
        content = f"{content[:479]}…"
    return RenderedDynamic(
        text=f"【B站动态】{item.author_name}\n{content}\nhttps://t.bilibili.com/{item.dynamic_id}",
        image_urls=item.image_urls,
    )
