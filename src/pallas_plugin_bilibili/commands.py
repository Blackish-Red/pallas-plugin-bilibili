from nonebot import logger, on_message
from nonebot.rule import fullmatch

from pallas.api.perm import group_message_permission_for_command

from .client import BilibiliApiError, BilibiliClient, BilibiliRiskControlError
from .config import plugin_config
from .storage import SubscriptionStore

ENABLE_REPLY = "收到，博士，米诺斯的众英雄为我们守望"
DISABLE_REPLY = "米诺斯的众英雄已不再守望…"
_OFFICIAL_UID = 161775300

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
probe_command = on_message(
    rule=fullmatch("牛牛测试B站推送", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.probe"),
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


async def handle_probe(ctx) -> None:
    try:
        items = await BilibiliClient(cookie=plugin_config.cookie).fetch_latest(
            _OFFICIAL_UID
        )
    except BilibiliRiskControlError as error:
        await ctx.finish(
            f"B站动态连接失败：B站风控（{error}），请在控制台填写有效 Cookie。"
        )
        return
    except BilibiliApiError as error:
        logger.warning("bilibili dynamic probe failed: {}", error)
        await ctx.finish("B站动态连接失败：请求 B站接口失败，请稍后再试。")
        return
    except Exception as error:
        logger.exception("bilibili dynamic probe failed: {}", error)
        await ctx.finish("B站动态连接失败：请求 B站接口失败，请稍后再试。")
        return
    if not items:
        await ctx.finish(
            f"B站动态连接正常：UID {_OFFICIAL_UID}，当前没有可推送的新动态。"
        )
        return
    await ctx.finish(
        f"B站动态连接正常：UID {_OFFICIAL_UID}，获取到 {len(items)} 条最新动态"
        f"（最新 ID {items[0].dynamic_id}）。"
    )


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


@probe_command.handle()
async def _probe_handler(bot, event) -> None:
    await handle_probe(probe_command)
