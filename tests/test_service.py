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
        "https://i0.hdslb.com/a.gif",
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

    assert send.await_args.kwargs["image_bytes"] is None
    assert store.was_delivered(str(item.uid), target.key, item.dynamic_id)
