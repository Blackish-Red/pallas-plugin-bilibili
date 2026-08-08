from pallas_plugin_bilibili.startup import JOB_ID, reschedule_poll_job


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
