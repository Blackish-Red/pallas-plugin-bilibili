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
    ctx = SimpleNamespace(finish=AsyncMock())

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
    ctx = SimpleNamespace(finish=AsyncMock())

    await commands.handle_probe(ctx)

    ctx.finish.assert_awaited_once_with(
        "B站动态连接失败：B站风控（HTTP 412），请在控制台填写有效 Cookie。"
    )
