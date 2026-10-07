import asyncio
from types import SimpleNamespace

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pallas_plugin_bilibili import startup
from pallas_plugin_bilibili.config import PushTarget
from pallas_plugin_bilibili.models import DynamicItem
from pallas_plugin_bilibili.storage import DeliveryCursorStore


@pytest.fixture(autouse=True)
def isolate_primed_routes():
    startup._primed_routes.clear()
    yield
    startup._primed_routes.clear()


def test_reschedule_uses_configured_interval(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "pallas_plugin_bilibili.startup.scheduler.add_job",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    startup.reschedule_poll_job(interval_sec=300)

    assert calls[0][1]["id"] == startup.JOB_ID
    assert calls[0][1]["replace_existing"] is True
    assert calls[0][1]["seconds"] == 300
    assert calls[0][1]["max_instances"] == 1
    assert calls[0][1]["coalesce"] is True


@pytest.mark.asyncio
async def test_startup_does_not_fetch_dynamics(monkeypatch) -> None:
    scheduled: list[int] = []
    fetched: list[int] = []

    class Client:
        async def fetch_latest(self, uid):
            fetched.append(uid)
            return []

    monkeypatch.setattr(
        startup,
        "plugin_config",
        SimpleNamespace(poll_interval_sec=180, enabled=True, cookie="", uids=[123]),
    )
    monkeypatch.setattr(
        startup,
        "reschedule_poll_job",
        lambda *, interval_sec: scheduled.append(interval_sec),
    )
    monkeypatch.setattr(startup, "BilibiliClient", lambda **_: Client())
    monkeypatch.setattr(
        startup,
        "SubscriptionStore",
        lambda: SimpleNamespace(targets=lambda: [PushTarget(bot_qq=1, group_id=2)]),
    )

    await startup.start_bilibili_dynamic_poll()
    await asyncio.sleep(0)

    assert scheduled == [180]
    assert fetched == []


def configure_poll(monkeypatch, tmp_path, targets, responses, *, enabled=True):
    store = DeliveryCursorStore(tmp_path / "cursors.json")

    class Client:
        async def fetch_latest(self, uid):
            response = responses[uid].pop(0)
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(
        startup,
        "plugin_config",
        SimpleNamespace(enabled=enabled, cookie="", uids=[]),
    )
    monkeypatch.setattr(
        startup,
        "SubscriptionStore",
        lambda: SimpleNamespace(targets=lambda: targets),
    )
    monkeypatch.setattr(startup, "DeliveryCursorStore", lambda: store)
    monkeypatch.setattr(startup, "BilibiliClient", lambda **_: Client())
    sent: list[str] = []

    async def send(_self, _bot, _group, text, _images):
        sent.append(text)
        return True

    monkeypatch.setattr(startup.DynamicPushService, "_send_group_forward", send)
    return store, sent


def item(dynamic_id: str) -> DynamicItem:
    return DynamicItem(dynamic_id, 1, "作者", 1, "word", dynamic_id)


@pytest.mark.asyncio
async def test_first_poll_silently_aligns_short_history_then_sends_new_item(
    monkeypatch, tmp_path
) -> None:
    target = PushTarget(bot_qq=1, group_id=2, uids=[123])
    store, sent = configure_poll(
        monkeypatch,
        tmp_path,
        [target],
        {
            123: [
                RuntimeError("-352"),
                [],
                [item("old-a"), item("old-b")],
                [item("new"), item("old-a"), item("old-b")],
            ]
        },
    )
    store.prime("123", "2", ["stale"])

    await startup.poll_job()
    assert not store.is_primed("123", "2")
    await startup.poll_job()
    assert not store.is_primed("123", "2")
    await startup.poll_job()
    assert store.was_delivered("123", "2", "old-a")
    assert sent == []
    await startup.poll_job()

    assert len(sent) == 1
    assert "\nnew\n" in sent[0]


@pytest.mark.asyncio
async def test_poll_deduplicates_requests_by_uid_across_groups(
    monkeypatch, tmp_path
) -> None:
    group_a = PushTarget(bot_qq=1, group_id=2, uids=[123, 456])
    group_b = PushTarget(bot_qq=1, group_id=3, uids=[123])
    store, _ = configure_poll(
        monkeypatch,
        tmp_path,
        [group_a, group_b],
        {123: [[item("a")]], 456: [[item("b")]]},
    )
    calls = []
    original = startup.BilibiliClient

    class CountingClient:
        async def fetch_latest(self, uid):
            calls.append(uid)
            return await original().fetch_latest(uid)

    monkeypatch.setattr(startup, "BilibiliClient", lambda **_: CountingClient())

    await startup.poll_job()

    assert calls == [123, 456]
    assert store.is_primed("123", "2")
    assert store.is_primed("123", "3")
    assert store.is_primed("456", "2")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "enabled,targets", [(False, [PushTarget(bot_qq=1, group_id=2)]), (True, [])]
)
async def test_poll_skips_disabled_or_unsubscribed(
    monkeypatch, tmp_path, enabled, targets
):
    store, _ = configure_poll(monkeypatch, tmp_path, targets, {}, enabled=enabled)
    monkeypatch.setattr(
        startup,
        "BilibiliClient",
        lambda **_: (_ for _ in ()).throw(AssertionError("unexpected network client")),
    )

    await startup.poll_job()

    assert not store._routes


@pytest.mark.asyncio
async def test_cursor_clear_failure_skips_route_and_retries_next_poll(
    monkeypatch, tmp_path
) -> None:
    target = PushTarget(bot_qq=1, group_id=2, uids=[123])
    store, _ = configure_poll(monkeypatch, tmp_path, [target], {123: [[item("old")]]})
    original_clear = store.clear_route
    attempts = 0

    def fail_once(uid, group_id):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("storage unavailable")
        original_clear(uid, group_id)

    monkeypatch.setattr(store, "clear_route", fail_once)
    calls = []
    original_client = startup.BilibiliClient

    class CountingClient:
        async def fetch_latest(self, uid):
            calls.append(uid)
            return await original_client().fetch_latest(uid)

    monkeypatch.setattr(startup, "BilibiliClient", lambda **_: CountingClient())

    await startup.poll_job()
    assert calls == []
    await startup.poll_job()

    assert attempts == 2
    assert calls == [123]
    assert store.is_primed("123", "2")


@pytest.mark.asyncio
async def test_reschedule_does_not_reset_route_baseline(monkeypatch, tmp_path) -> None:
    target = PushTarget(bot_qq=1, group_id=2, uids=[123])
    store, sent = configure_poll(
        monkeypatch,
        tmp_path,
        [target],
        {123: [[item("old")], [item("new"), item("old")]]},
    )
    await startup.poll_job()
    monkeypatch.setattr(startup.scheduler, "add_job", lambda *args, **kwargs: None)

    startup.reschedule_poll_job(interval_sec=300)
    await startup.poll_job()

    assert len(sent) == 1
    assert "\nnew\n" in sent[0]
    assert store.was_delivered("123", "2", "new")


@pytest.mark.asyncio
async def test_scheduler_shutdown_cancels_in_flight_poll(monkeypatch, tmp_path) -> None:
    entered = asyncio.Event()
    cancelled = asyncio.Event()
    target = PushTarget(bot_qq=1, group_id=2, uids=[123])
    monkeypatch.setattr(
        startup,
        "plugin_config",
        SimpleNamespace(enabled=True, cookie="", uids=[]),
    )
    monkeypatch.setattr(
        startup,
        "SubscriptionStore",
        lambda: SimpleNamespace(targets=lambda: [target]),
    )
    monkeypatch.setattr(
        startup,
        "DeliveryCursorStore",
        lambda: DeliveryCursorStore(tmp_path / "cursors.json"),
    )

    class Client:
        async def fetch_latest(self, _uid):
            entered.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

    monkeypatch.setattr(startup, "BilibiliClient", lambda **_: Client())
    scheduler = AsyncIOScheduler(event_loop=asyncio.get_running_loop())
    scheduler.start()
    scheduler.add_job(
        startup.poll_job, "interval", seconds=0.05, id="test_in_flight_poll"
    )
    await asyncio.wait_for(entered.wait(), timeout=2)

    scheduler.shutdown(wait=False)
    await asyncio.wait_for(cancelled.wait(), timeout=2)
