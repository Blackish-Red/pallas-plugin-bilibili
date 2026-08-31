from pallas_plugin_bilibili.models import DynamicItem
from pallas_plugin_bilibili.render import render_dynamic
from pallas_plugin_bilibili.storage import DeliveryCursorStore


def test_cursor_primes_each_target_independently(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "delivery-cursors.json")
    store.prime("161775300", "10001:733291779", ["new", "old"])

    assert store.was_delivered("161775300", "10001:733291779", "new")
    assert not store.was_delivered("161775300", "10002:733291779", "new")


def test_prime_with_empty_page_does_not_mark_primed(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "delivery-cursors.json")
    store.prime("161775300", "733291779", [])

    assert not store.is_primed("161775300", "733291779")


def test_is_primed_ignores_empty_route_rows(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "delivery-cursors.json")
    store.prime("161775300", "733291779", ["a", "b"])
    store._routes.setdefault("161775300", {})["88888888"] = []

    assert store.is_primed("161775300", "733291779")
    assert not store.is_primed("161775300", "88888888")


def test_render_includes_dynamic_link_and_keeps_image_urls() -> None:
    item = DynamicItem(
        "100",
        161775300,
        "明日方舟",
        1,
        "draw",
        "x" * 600,
        ("https://i0.hdslb.com/a.gif", "https://i0.hdslb.com/b.gif"),
    )

    rendered = render_dynamic(item)

    assert "https://t.bilibili.com/100" in rendered.text
    assert len(rendered.text) <= 550
    assert rendered.image_urls == (
        "https://i0.hdslb.com/a.gif",
        "https://i0.hdslb.com/b.gif",
    )


def test_render_video_uses_video_url_and_cover() -> None:
    item = DynamicItem(
        "101",
        161775300,
        "明日方舟",
        1,
        "video",
        "视频标题",
        ("https://i0.hdslb.com/video.jpg",),
        "https://www.bilibili.com/video/BV1xx411c7mD",
    )

    rendered = render_dynamic(item)

    assert "视频标题" in rendered.text
    assert "https://www.bilibili.com/video/BV1xx411c7mD" in rendered.text
    assert rendered.image_urls == ("https://i0.hdslb.com/video.jpg",)


def test_push_target_accepts_optional_uids() -> None:
    from pallas_plugin_bilibili.config import PushTarget

    target = PushTarget(bot_qq=10001, group_id=733291779, uids=[1, 2])
    assert target.uids == [1, 2]

    plain = PushTarget(bot_qq=10001, group_id=733291779)
    assert plain.uids is None
