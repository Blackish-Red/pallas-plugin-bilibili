from pallas_plugin_bilibili.storage import SubscriptionStore


def test_subscription_store_enables_and_disables_a_group(tmp_path) -> None:
    store = SubscriptionStore(tmp_path / "subscriptions.json")

    assert store.enable(10001, 733291779) is True
    assert store.enable(10001, 733291779) is False
    assert [(item.bot_qq, item.group_id) for item in store.targets()] == [
        (10001, 733291779)
    ]
    assert store.disable(10001, 733291779) is True
    assert store.targets() == []
