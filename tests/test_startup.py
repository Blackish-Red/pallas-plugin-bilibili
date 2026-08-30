from types import SimpleNamespace

import pytest
from pallas_plugin_bilibili.startup import (
    JOB_ID,
    poll_job,
    prime_initial_cursors,
    reschedule_poll_job,
    start_bilibili_dynamic_poll,
)


def test_reschedule_uses_configured_interval(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.scheduler.add_job",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    reschedule_poll_job(interval_sec=300)

    assert calls[0][1]["id"] == JOB_ID
    assert calls[0][1]["replace_existing"] is True
    assert calls[0][1]["seconds"] == 300
    assert calls[0][1]["max_instances"] == 1


@pytest.mark.asyncio
async def test_startup_reads_the_plugin_config_proxy(monkeypatch) -> None:
    scheduled: list[int] = []
    spawned: list[str] = []
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(poll_interval_sec=180),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.reschedule_poll_job",
        lambda *, interval_sec: scheduled.append(interval_sec),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.asyncio.create_task",
        lambda coro: spawned.append("prime"),
    )

    await start_bilibili_dynamic_poll()

    assert scheduled == [180]
    assert spawned == ["prime"]


@pytest.mark.asyncio
async def test_poll_job_reads_the_plugin_config_proxy(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(enabled=True, cookie=""),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.SubscriptionStore.targets",
        lambda _self: [],
    )

    await poll_job()


@pytest.mark.asyncio
async def test_poll_job_polls_configured_uids(monkeypatch) -> None:
    from pallas_plugin_bilibili.config import PushTarget

    polled: list[tuple[list[int], list[PushTarget]]] = []

    class FakeService:
        def __init__(self, **kwargs) -> None:
            pass

        async def poll(self, uids, targets) -> None:
            polled.append((uids, targets))

    target = PushTarget(bot_qq=10001, group_id=733291779)
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(
            enabled=True, cookie="", forward_multiple_images=False, uids=[111, 222]
        ),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.SubscriptionStore.targets",
        lambda _self: [target],
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.DynamicPushService", FakeService
    )

    await poll_job()

    assert polled == [([111, 222], [target])]


@pytest.mark.asyncio
async def test_poll_job_falls_back_to_default_uid_when_config_empty(monkeypatch) -> None:
    from pallas_plugin_bilibili.config import DEFAULT_UIDS, PushTarget

    polled: list[list[int]] = []

    class FakeService:
        def __init__(self, **kwargs) -> None:
            pass

        async def poll(self, uids, targets) -> None:
            polled.append(uids)

    target = PushTarget(bot_qq=10001, group_id=733291779)
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(enabled=True, cookie="", forward_multiple_images=False, uids=[]),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.SubscriptionStore.targets",
        lambda _self: [target],
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.DynamicPushService", FakeService
    )

    await poll_job()

    assert polled == [list(DEFAULT_UIDS)]


def _prime_env(monkeypatch, *, config, targets, client, store) -> None:
    monkeypatch.setattr("pallas_plugin_bilibili.startup.plugin_config", config)
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.SubscriptionStore",
        lambda: SimpleNamespace(targets=lambda: targets),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.BilibiliClient",
        lambda **kwargs: client,
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.DeliveryCursorStore",
        lambda: store,
    )


@pytest.mark.asyncio
async def test_prime_initial_cursors_marks_current_page_as_seen(
    monkeypatch, tmp_path
) -> None:
    from unittest.mock import AsyncMock

    from pallas_plugin_bilibili.config import PushTarget
    from pallas_plugin_bilibili.models import DynamicItem
    from pallas_plugin_bilibili.storage import DeliveryCursorStore

    item = DynamicItem("100", 161775300, "明日方舟", 1, "draw", "活动预告")
    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[item])})()
    store = DeliveryCursorStore(tmp_path / "delivery-cursors.json")
    target = PushTarget(bot_qq=10001, group_id=733291779)
    _prime_env(
        monkeypatch,
        config=SimpleNamespace(enabled=True, cookie="", uids=[161775300]),
        targets=[target],
        client=client,
        store=store,
    )

    await prime_initial_cursors()

    assert store.is_primed(str(item.uid), str(target.group_id))
    assert store.was_delivered(str(item.uid), str(target.group_id), item.dynamic_id)


@pytest.mark.asyncio
async def test_prime_initial_cursors_keeps_cursor_on_empty_page(
    monkeypatch, tmp_path
) -> None:
    from unittest.mock import AsyncMock

    from pallas_plugin_bilibili.config import PushTarget
    from pallas_plugin_bilibili.storage import DeliveryCursorStore

    client = type("Client", (), {"fetch_latest": AsyncMock(return_value=[])})()
    store = DeliveryCursorStore(tmp_path / "delivery-cursors.json")
    store.prime("161775300", "733291779", ["old"])
    target = PushTarget(bot_qq=10001, group_id=733291779)
    _prime_env(
        monkeypatch,
        config=SimpleNamespace(enabled=True, cookie="", uids=[161775300]),
        targets=[target],
        client=client,
        store=store,
    )

    await prime_initial_cursors()

    assert store.was_delivered("161775300", str(target.group_id), "old")


@pytest.mark.asyncio
async def test_prime_initial_cursors_noop_when_disabled(monkeypatch) -> None:
    def unexpected_client(**kwargs):
        raise AssertionError("should not fetch when disabled")

    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(enabled=False, cookie="", uids=[161775300]),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.SubscriptionStore",
        lambda: SimpleNamespace(targets=list),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.BilibiliClient", unexpected_client
    )

    await prime_initial_cursors()
