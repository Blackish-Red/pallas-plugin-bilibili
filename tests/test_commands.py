from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bilibili import commands


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


def test_commands_use_single_case_insensitive_matcher() -> None:
    rule = next(iter(commands.enable_command.rule.checkers)).call

    assert rule.ignorecase is True
    assert rule.msg == ("牛牛开启b站推送",)
