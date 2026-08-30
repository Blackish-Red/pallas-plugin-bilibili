from types import SimpleNamespace

from pallas_plugin_bilibili.storage import DeliveryCursorStore, SubscriptionStore


def test_subscription_store_enables_and_disables_a_group(tmp_path, monkeypatch) -> None:
    cleared: list[int] = []
    monkeypatch.setattr(
        "pallas_plugin_bilibili.storage.DeliveryCursorStore",
        lambda: SimpleNamespace(clear_group=lambda group_id: cleared.append(group_id)),
    )
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.enable(10001, 733291779) is True
    assert store.enable(10001, 733291779) is False
    assert [(item.bot_qq, item.group_id) for item in store.targets()] == [
        (10001, 733291779)
    ]
    assert store.disable(10001, 733291779) is True
    assert store.targets() == []


def test_enable_clears_group_cursor_to_reestablish_position(
    tmp_path, monkeypatch
) -> None:
    cleared: list[int] = []
    monkeypatch.setattr(
        "pallas_plugin_bilibili.storage.DeliveryCursorStore",
        lambda: SimpleNamespace(clear_group=lambda group_id: cleared.append(group_id)),
    )
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.enable(10001, 733291779) is True
    assert cleared == [733291779]

    # 已订阅时重复 enable 不重复清游标
    assert store.enable(10001, 733291779) is False
    assert cleared == [733291779]


def test_clear_group_removes_route_for_group(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "cursors.json")
    store.prime("161775300", "733291779", ["a"])
    store.prime("161775300", "88888888", ["b"])
    store.prime("13148307", "733291779", ["c"])

    store.clear_group(733291779)

    assert not store.is_primed("161775300", "733291779")
    assert store.is_primed("161775300", "88888888")
    assert not store.is_primed("13148307", "733291779")


def test_clear_group_removes_legacy_bot_qq_route(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "cursors.json")
    store.prime("161775300", "10001:733291779", ["a"])

    store.clear_group(733291779)

    assert not store.is_primed("161775300", "733291779")


def test_group_uids_returns_none_when_not_set(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.group_uids(10001, 733291779) is None


def test_set_group_uids_replaces_list(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.set_group_uids(10001, 733291779, [1, 2]) is True
    assert store.group_uids(10001, 733291779) == [1, 2]

    assert store.set_group_uids(10001, 733291779, [3]) is True
    assert store.group_uids(10001, 733291779) == [3]


def test_add_group_uid_appends_and_dedupes(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.add_group_uid(10001, 733291779, 1) is True
    assert store.add_group_uid(10001, 733291779, 2) is True
    assert store.add_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) == [1, 2]


def test_remove_group_uid_removes_and_reports(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)
    store.set_group_uids(10001, 733291779, [1, 2])

    assert store.remove_group_uid(10001, 733291779, 1) is True
    assert store.remove_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) == [2]


def test_group_uid_methods_noop_for_unsubscribed_group(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.set_group_uids(10001, 733291779, [1]) is False
    assert store.add_group_uid(10001, 733291779, 1) is False
    assert store.remove_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) is None
