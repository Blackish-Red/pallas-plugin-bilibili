from types import SimpleNamespace

import pytest
from pallas_plugin_bilibili.startup import (
    JOB_ID,
    poll_job,
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
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.plugin_config",
        SimpleNamespace(poll_interval_sec=180),
    )
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.reschedule_poll_job",
        lambda *, interval_sec: scheduled.append(interval_sec),
    )

    await start_bilibili_dynamic_poll()

    assert scheduled == [180]


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
