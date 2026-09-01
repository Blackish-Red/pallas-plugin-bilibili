from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bilibili.config import PushTarget
from pallas_plugin_bilibili.models import DynamicItem
from pallas_plugin_bilibili.service import DynamicPushService
from pallas_plugin_bilibili.storage import DeliveryCursorStore


@pytest.mark.asyncio
async def test_first_poll_only_primes_target(tmp_path, monkeypatch) -> None:
    item = DynamicItem("100", 161775300, "明日方舟", 1, "draw", "活动预告")
    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[item])})()
    forwarded = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    service = DynamicPushService(
        client=client, store=DeliveryCursorStore(tmp_path / "state.json")
    )
    target = PushTarget(bot_qq=10001, group_id=733291779)

    await service.poll_target_uid(target, 161775300)

    forwarded.assert_not_awaited()
    assert service.store.is_primed(str(161775300), str(target.group_id))


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
    forwarded = AsyncMock(return_value=True)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])
    service = DynamicPushService(client=client, store=store)

    await service.poll_target_uid(target, item.uid)

    forwarded.assert_awaited_once()
    assert store.was_delivered(str(item.uid), str(target.group_id), item.dynamic_id)


@pytest.mark.asyncio
async def test_poll_deduplicates_same_dynamic_across_bots_in_one_group(
    tmp_path, monkeypatch
) -> None:
    item = DynamicItem("100", 161775300, "明日方舟", 1, "draw", "活动预告")
    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[item])})()
    forwarded = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    store = DeliveryCursorStore(tmp_path / "state.json")
    targets = [
        PushTarget(bot_qq=10001, group_id=733291779),
        PushTarget(bot_qq=10002, group_id=733291779),
    ]
    for target in targets:
        store.prime(str(item.uid), target.key, ["old"])
    service = DynamicPushService(client=client, store=store)

    await service.poll({item.uid: targets})

    forwarded.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_sends_all_images_as_forward_nodes(tmp_path, monkeypatch) -> None:
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
    forwarded = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])

    await DynamicPushService(client=client, store=store).poll_target_uid(
        target, item.uid
    )

    forwarded.assert_awaited_once()
    nodes = forwarded.await_args.args[2]
    assert len(nodes) == 3
    assert "活动预告" in nodes[0]["data"]["content"]
    assert "[CQ:image" in nodes[1]["data"]["content"]
    assert "[CQ:image" in nodes[2]["data"]["content"]


@pytest.mark.asyncio
async def test_poll_always_uses_forward_even_for_single_image(
    tmp_path, monkeypatch
) -> None:
    item = DynamicItem(
        "102",
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
            "download_image": AsyncMock(return_value=b"one"),
        },
    )()
    forwarded = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "pallas.api.platform.send_group_forward_message_as_bot", forwarded
    )
    store = DeliveryCursorStore(tmp_path / "state.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    store.prime(str(item.uid), target.key, ["old"])

    await DynamicPushService(client=client, store=store).poll_target_uid(
        target, item.uid
    )

    forwarded.assert_awaited_once()
    nodes = forwarded.await_args.args[2]
    assert len(nodes) == 2
    assert "活动预告" in nodes[0]["data"]["content"]
    assert "[CQ:image" in nodes[1]["data"]["content"]
