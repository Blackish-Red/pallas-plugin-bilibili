from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bilibili import commands
from pallas_plugin_bilibili.client import BilibiliRiskControlError
from pallas_plugin_bilibili.models import DynamicItem


@pytest.mark.asyncio
async def test_enable_binds_group_and_replies(monkeypatch) -> None:
    store = SimpleNamespace(enable=lambda bot_qq, group_id: True)
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_enable(ctx)

    ctx.finish.assert_awaited_once_with("收到，博士，米诺斯的众英雄为我们守望")


@pytest.mark.asyncio
async def test_disable_replies_even_when_group_was_not_subscribed(monkeypatch) -> None:
    store = SimpleNamespace(disable=lambda bot_qq, group_id: False)
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_disable(ctx)

    ctx.finish.assert_awaited_once_with("米诺斯的众英雄已不再守望…")


def test_enable_command_uses_single_case_insensitive_subscription_matcher() -> None:
    rule = next(iter(commands.enable_command.rule.checkers)).call

    assert rule.ignorecase is True
    assert rule.msg == ("牛牛订阅b站动态",)


def test_disable_command_uses_single_case_insensitive_unsubscribe_matcher() -> None:
    rule = next(iter(commands.disable_command.rule.checkers)).call

    assert rule.ignorecase is True
    assert rule.msg == ("牛牛取消订阅b站动态",)


@pytest.mark.asyncio
async def test_probe_reports_latest_dynamic_without_delivery(monkeypatch) -> None:
    client = SimpleNamespace(
        fetch_latest=AsyncMock(
            return_value=[DynamicItem("100", 161775300, "明日方舟", 1, "word", "活动")]
        )
    )
    monkeypatch.setattr(commands, "BilibiliClient", lambda *, cookie: client)
    monkeypatch.setattr(
        commands,
        "plugin_config",
        SimpleNamespace(cookie="", uids=[161775300]),
    )
    monkeypatch.setattr(
        commands,
        "SubscriptionStore",
        lambda: SimpleNamespace(group_uids=lambda bot_qq, group_id: None),
    )
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_probe(ctx)

    ctx.finish.assert_awaited_once_with(
        "B站动态连接正常：UID 161775300，获取到 1 条最新动态（最新 ID 100）。"
    )


@pytest.mark.asyncio
async def test_probe_reports_bilibili_risk_control(monkeypatch) -> None:
    client = SimpleNamespace(
        fetch_latest=AsyncMock(side_effect=BilibiliRiskControlError("HTTP 412"))
    )
    monkeypatch.setattr(commands, "BilibiliClient", lambda *, cookie: client)
    monkeypatch.setattr(
        commands,
        "plugin_config",
        SimpleNamespace(cookie="", uids=[161775300]),
    )
    monkeypatch.setattr(
        commands,
        "SubscriptionStore",
        lambda: SimpleNamespace(group_uids=lambda bot_qq, group_id: None),
    )
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_probe(ctx)

    ctx.finish.assert_awaited_once_with(
        "B站动态连接失败：UID 161775300 触发B站风控（HTTP 412），"
        "请在控制台填写有效 Cookie。"
    )


@pytest.mark.asyncio
async def test_probe_reports_each_configured_uid(monkeypatch) -> None:
    async def fetch_latest(uid: int):
        if uid == 2:
            return []
        return [DynamicItem("100", uid, "作者", 1, "word", "活动")]

    client = SimpleNamespace(fetch_latest=fetch_latest)
    monkeypatch.setattr(commands, "BilibiliClient", lambda *, cookie: client)
    monkeypatch.setattr(
        commands,
        "plugin_config",
        SimpleNamespace(cookie="", uids=[1, 2]),
    )
    monkeypatch.setattr(
        commands,
        "SubscriptionStore",
        lambda: SimpleNamespace(group_uids=lambda bot_qq, group_id: None),
    )
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_probe(ctx)

    ctx.finish.assert_awaited_once_with(
        "B站动态连接正常：UID 1，获取到 1 条最新动态（最新 ID 100）；"
        "UID 2，当前没有可推送的新动态。"
    )


@pytest.mark.asyncio
async def test_add_uid_appends_and_replies(monkeypatch) -> None:
    store = SimpleNamespace(
        group_uids=lambda bot_qq, group_id: [], add_group_uid=lambda bot_qq, group_id, uid: True
    )
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_add_uid(ctx, [12345])

    ctx.finish.assert_awaited_once_with("已为当前群添加 B站 UID：12345")


@pytest.mark.asyncio
async def test_add_uid_reports_when_already_present(monkeypatch) -> None:
    store = SimpleNamespace(
        group_uids=lambda bot_qq, group_id: [], add_group_uid=lambda bot_qq, group_id, uid: False
    )
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_add_uid(ctx, [12345])

    ctx.finish.assert_awaited_once_with("这些 B站 UID 已在当前群关注列表中")


@pytest.mark.asyncio
async def test_remove_uid_removes_and_replies(monkeypatch) -> None:
    store = SimpleNamespace(
        group_uids=lambda bot_qq, group_id: [], remove_group_uid=lambda bot_qq, group_id, uid: True
    )
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_remove_uid(ctx, [12345])

    ctx.finish.assert_awaited_once_with("已为当前群删除 B站 UID：12345")


@pytest.mark.asyncio
async def test_remove_uid_reports_when_absent(monkeypatch) -> None:
    store = SimpleNamespace(
        group_uids=lambda bot_qq, group_id: [], remove_group_uid=lambda bot_qq, group_id, uid: False
    )
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_remove_uid(ctx, [12345])

    ctx.finish.assert_awaited_once_with("这些 B站 UID 不在当前群关注列表中")


@pytest.mark.asyncio
async def test_view_uid_shows_group_list(monkeypatch) -> None:
    store = SimpleNamespace(group_uids=lambda bot_qq, group_id: [1, 2])
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_view_uid(ctx)

    ctx.finish.assert_awaited_once_with("当前群关注的 B站 UID：1、2")


@pytest.mark.asyncio
async def test_view_uid_falls_back_to_global(monkeypatch) -> None:
    store = SimpleNamespace(group_uids=lambda bot_qq, group_id: [])
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    monkeypatch.setattr(
        commands, "plugin_config", SimpleNamespace(uids=[161775300])
    )
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_view_uid(ctx)

    ctx.finish.assert_awaited_once_with(
        "当前群未单独设置 B站 UID，使用全局配置：161775300"
    )


@pytest.mark.asyncio
async def test_view_uid_hints_subscribe_when_group_unsubscribed(monkeypatch) -> None:
    store = SimpleNamespace(group_uids=lambda bot_qq, group_id: None)
    monkeypatch.setattr(commands, "SubscriptionStore", lambda: store)
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_view_uid(ctx)

    ctx.finish.assert_awaited_once_with("当前群尚未订阅 B站动态，请先发送：牛牛订阅B站动态")


@pytest.mark.asyncio
async def test_probe_uses_group_uids_when_set(monkeypatch) -> None:
    client = SimpleNamespace(
        fetch_latest=AsyncMock(
            return_value=[DynamicItem("100", 12345, "作者", 1, "word", "活动")]
        )
    )
    monkeypatch.setattr(commands, "BilibiliClient", lambda *, cookie: client)
    monkeypatch.setattr(
        commands,
        "plugin_config",
        SimpleNamespace(cookie="", uids=[161775300]),
    )
    monkeypatch.setattr(
        commands,
        "SubscriptionStore",
        lambda: SimpleNamespace(group_uids=lambda bot_qq, group_id: [12345]),
    )
    ctx = SimpleNamespace(
        bot=SimpleNamespace(self_id=10001), group_id=733291779, finish=AsyncMock()
    )

    await commands.handle_probe(ctx)

    ctx.finish.assert_awaited_once_with(
        "B站动态连接正常：UID 12345，获取到 1 条最新动态（最新 ID 100）。"
    )
