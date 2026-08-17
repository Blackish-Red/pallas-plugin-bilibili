from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bilibili.config import PushTarget
from pallas_plugin_bilibili.models import DynamicItem
from pallas_plugin_bilibili.service import DynamicPushService
from pallas_plugin_bilibili.storage import DeliveryCursorStore


@pytest.mark.asyncio
async def test_first_poll_only_primes_target(tmp_path) -> None:
    item = DynamicItem("100", 161775300, "明日方舟", 1, "draw", "活动预告")
    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[item])})()
    send = AsyncMock(return_value=True)
    service = DynamicPushService(
        client=client, store=DeliveryCursorStore(tmp_path / "state.json"), send=send
    )
    target = PushTarget(bot_qq=10001, group_id=733291779)

    await service.poll_target_uid(target, 161775300)

    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_media_failure_falls_back_to_text_and_marks_success(tmp_path) -> None:
    item = DynamicItem(
        "100",
        161775300,
        "明日方舟",
        1,
        "draw",
        "活动预告",
        ("https://i0.hdslb.com/a.gif",),
    )
    client = type(
        "Client",
        (),
        {
            "fetch_latest": AsyncMock(return_value=[item]),
            "download_image": AsyncMock(side_effect=RuntimeError("failed")),
        },
    )()
    send = AsyncMock(return_value=True)
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])
    service = DynamicPushService(client=client, store=store, send=send)

    await service.poll_target_uid(target, item.uid)

    assert send.await_args.kwargs["image_bytes"] == []
    assert store.was_delivered(str(item.uid), str(target.group_id), item.dynamic_id)


@pytest.mark.asyncio
async def test_poll_deduplicates_same_dynamic_across_bots_in_one_group(
    tmp_path,
) -> None:
    item = DynamicItem("100", 161775300, "明日方舟", 1, "draw", "活动预告")
    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[item])})()
    send = AsyncMock(return_value=True)
    store = DeliveryCursorStore(tmp_path / "state.json")
    targets = [
        PushTarget(bot_qq=10001, group_id=733291779),
        PushTarget(bot_qq=10002, group_id=733291779),
    ]
    for target in targets:
        store.prime(str(item.uid), target.key, ["old"])
    service = DynamicPushService(client=client, store=store, send=send)

    await service.poll([item.uid], targets)

    send.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_sends_all_images_in_one_message(tmp_path) -> None:
    item = DynamicItem(
        "101",
        161775300,
        "明日方舟",
        1,
        "draw",
        "活动预告",
        ("https://i0.hdslb.com/a.gif", "https://i0.hdslb.com/b.gif"),
    )
    client = type(
        "Client",
        (),
        {
            "fetch_latest": AsyncMock(return_value=[item]),
            "download_image": AsyncMock(side_effect=[b"one", b"two"]),
        },
    )()
    send = AsyncMock(return_value=True)
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])

    await DynamicPushService(client=client, store=store, send=send).poll_target_uid(
        target, item.uid
    )

    assert send.await_args.kwargs["image_bytes"] == [b"one", b"two"]


@pytest.mark.asyncio
async def test_poll_can_use_forward_for_multiple_images(tmp_path, monkeypatch) -> None:
    item = DynamicItem(
        "102",
        161775300,
        "明日方舟",
        1,
        "draw",
        "活动预告",
        ("https://i0.hdslb.com/a.gif", "https://i0.hdslb.com/b.gif"),
    )
    client = type(
        "Client",
        (),
        {
            "fetch_latest": AsyncMock(return_value=[item]),
            "download_image": AsyncMock(side_effect=[b"one", b"two"]),
        },
    )()
    forwarded = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])

    await DynamicPushService(
        client=client,
        store=store,
        send=AsyncMock(return_value=True),
        forward_multiple_images=True,
    ).poll_target_uid(target, item.uid)

    forwarded.assert_awaited_once()
    assert "[CQ:image" in forwarded.await_args.args[2][0]["data"]["content"]
