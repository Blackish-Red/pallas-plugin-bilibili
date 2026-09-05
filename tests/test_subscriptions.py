from pallas_plugin_bilibili.storage import DeliveryCursorStore, SubscriptionStore


class _CursorRecorder:
    """记录 enable / uid 列表变更触发的游标清除调用。"""

    def __init__(self) -> None:
        self.clear_groups: list[int] = []
        self.clear_routes: list[tuple[int, int]] = []

    def clear_group(self, group_id: int) -> None:
        self.clear_groups.append(group_id)

    def clear_route(self, uid: int, group_id: int) -> None:
        self.clear_routes.append((uid, group_id))


def _patch_cursor(monkeypatch) -> _CursorRecorder:
    recorder = _CursorRecorder()
    monkeypatch.setattr(
        "pallas_plugin_bilibili.storage.DeliveryCursorStore",
        lambda: recorder,
    )
    return recorder


def test_subscription_store_enables_and_disables_a_group(tmp_path, monkeypatch) -> None:
    recorder = _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.enable(10001, 733291779) is True
    assert store.enable(10001, 733291779) is False
    assert [(item.bot_qq, item.group_id) for item in store.targets()] == [
        (10001, 733291779)
    ]
    assert store.disable(10001, 733291779) is True
    assert store.targets() == []
    assert recorder.clear_groups == [733291779]


def test_enable_clears_group_cursor_to_reestablish_position(
    tmp_path, monkeypatch
) -> None:
    recorder = _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.enable(10001, 733291779) is True
    assert recorder.clear_groups == [733291779]

    # 已订阅时重复 enable 不重复清游标
    assert store.enable(10001, 733291779) is False
    assert recorder.clear_groups == [733291779]


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


def test_clear_route_removes_only_that_uid_for_group(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "cursors.json")
    store.prime("161775300", "733291779", ["a"])
    store.prime("13148307", "733291779", ["b"])
    store.prime("161775300", "88888888", ["c"])

    store.clear_route(161775300, 733291779)

    assert not store.is_primed("161775300", "733291779")
    assert store.is_primed("13148307", "733291779")
    assert store.is_primed("161775300", "88888888")


def test_clear_route_removes_legacy_bot_qq_route(tmp_path) -> None:
    store = DeliveryCursorStore(tmp_path / "cursors.json")
    store.prime("161775300", "10001:733291779", ["a"])

    store.clear_route(161775300, 733291779)

    assert not store.is_primed("161775300", "733291779")


def test_group_uids_returns_none_when_not_set(tmp_path, monkeypatch) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.group_uids(10001, 733291779) is None


def test_set_group_uids_replaces_list(tmp_path, monkeypatch) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.set_group_uids(10001, 733291779, [1, 2]) is True
    assert store.group_uids(10001, 733291779) == [1, 2]

    assert store.set_group_uids(10001, 733291779, [3]) is True
    assert store.group_uids(10001, 733291779) == [3]


def test_add_group_uid_appends_and_dedupes(tmp_path, monkeypatch) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.add_group_uid(10001, 733291779, 1) is True
    assert store.add_group_uid(10001, 733291779, 2) is True
    assert store.add_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) == [1, 2]


def test_remove_group_uid_removes_and_reports(tmp_path, monkeypatch) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)
    store.set_group_uids(10001, 733291779, [1, 2])

    assert store.remove_group_uid(10001, 733291779, 1) is True
    assert store.remove_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) == [2]


def test_group_uid_methods_noop_for_unsubscribed_group(tmp_path, monkeypatch) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.set_group_uids(10001, 733291779, [1]) is False
    assert store.add_group_uid(10001, 733291779, 1) is False
    assert store.remove_group_uid(10001, 733291779, 1) is False
    assert store.group_uids(10001, 733291779) is None


def test_is_subscribed_true_for_subscribed_false_for_unknown(
    tmp_path, monkeypatch
) -> None:
    _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.is_subscribed(10001, 733291779) is True
    assert store.is_subscribed(10001, 626266902) is False


def test_add_uid_rejects_non_positive_instead_of_poisoning_file(
    tmp_path, monkeypatch
) -> None:
    _patch_cursor(monkeypatch)
    path = tmp_path / "subscriptions.json"
    store = SubscriptionStore(path)
    store.enable(10001, 733291779)

    assert store.add_group_uid(10001, 733291779, 0) is False
    assert store.group_uids(10001, 733291779) in (None, [])

    reloaded = SubscriptionStore(path)
    assert (reloaded.targets()[0].bot_qq, reloaded.targets()[0].group_id) == (
        10001,
        733291779,
    )


def test_add_group_uid_clears_route_cursor_to_reestablish_position(
    tmp_path, monkeypatch
) -> None:
    recorder = _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)

    assert store.add_group_uid(10001, 733291779, 13148307) is True
    assert (13148307, 733291779) in recorder.clear_routes

    # 重复添加不触发清除
    assert store.add_group_uid(10001, 733291779, 13148307) is False
    assert recorder.clear_routes.count((13148307, 733291779)) == 1


def test_set_group_uids_clears_only_newly_added_uids(tmp_path, monkeypatch) -> None:
    recorder = _patch_cursor(monkeypatch)
    store = SubscriptionStore(tmp_path / "subscriptions.json")
    store.enable(10001, 733291779)
    store.set_group_uids(10001, 733291779, [13148307])
    recorder.clear_routes.clear()

    # 从 [13148307] 变为 [13148307, 3546592848120041]：只清新增的 uid
    assert store.set_group_uids(10001, 733291779, [13148307, 3546592848120041]) is True
    assert (3546592848120041, 733291779) in recorder.clear_routes
    assert (13148307, 733291779) not in recorder.clear_routes
