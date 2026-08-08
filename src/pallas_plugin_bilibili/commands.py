from nonebot import on_message
from nonebot.rule import fullmatch

from pallas.api.perm import group_message_permission_for_command

from .storage import SubscriptionStore

ENABLE_REPLY = "收到，博士，米诺斯的众英雄为我们守望"
DISABLE_REPLY = "米诺斯的众英雄已不再守望…"

enable_command = on_message(
    rule=fullmatch("牛牛订阅B站动态", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.enable"),
    priority=5,
    block=True,
)
disable_command = on_message(
    rule=fullmatch("牛牛关闭B站推送", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.disable"),
    priority=5,
    block=True,
)


async def handle_enable(ctx) -> None:
    if ctx.group_id is None:
        return
    SubscriptionStore().enable(int(ctx.bot.self_id), ctx.group_id)
    await ctx.finish(ENABLE_REPLY)


async def handle_disable(ctx) -> None:
    if ctx.group_id is None:
        return
    SubscriptionStore().disable(int(ctx.bot.self_id), ctx.group_id)
    await ctx.finish(DISABLE_REPLY)


@enable_command.handle()
async def _enable_handler(bot, event) -> None:
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return
    SubscriptionStore().enable(int(bot.self_id), int(group_id))
    await enable_command.finish(ENABLE_REPLY)


@disable_command.handle()
async def _disable_handler(bot, event) -> None:
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return
    SubscriptionStore().disable(int(bot.self_id), int(group_id))
    await disable_command.finish(DISABLE_REPLY)
