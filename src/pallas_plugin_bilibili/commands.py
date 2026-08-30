import re

from nonebot import logger, on_message
from nonebot.rule import fullmatch, startswith
from pallas.api.perm import group_message_permission_for_command

from .client import BilibiliApiError, BilibiliClient, BilibiliRiskControlError
from .config import DEFAULT_UIDS, plugin_config
from .storage import SubscriptionStore

ENABLE_REPLY = "收到，博士，米诺斯的众英雄为我们守望"
DISABLE_REPLY = "米诺斯的众英雄已不再守望…"


def _parse_uids(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"\d+", text)]

enable_command = on_message(
    rule=fullmatch("牛牛订阅B站动态", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.enable"),
    priority=5,
    block=True,
)
disable_command = on_message(
    rule=fullmatch("牛牛取消订阅B站动态", ignorecase=True),
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
add_uid_command = on_message(
    rule=startswith("牛牛B站添加UID", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.add_uid"),
    priority=5,
    block=True,
)
remove_uid_command = on_message(
    rule=startswith("牛牛B站删除UID", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.remove_uid"),
    priority=5,
    block=True,
)
view_uid_command = on_message(
    rule=fullmatch("牛牛B站查看UID", ignorecase=True),
    permission=group_message_permission_for_command("bilibili_dynamic.view_uid"),
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
    uids = list(plugin_config.uids) or list(DEFAULT_UIDS)
    client = BilibiliClient(cookie=plugin_config.cookie)
    lines: list[str] = []
    for uid in uids:
        try:
            items = await client.fetch_latest(uid)
        except BilibiliRiskControlError as error:
            await ctx.finish(
                f"B站动态连接失败：UID {uid} 触发B站风控（{error}），"
                "请在控制台填写有效 Cookie。"
            )
            return
        except BilibiliApiError as error:
            logger.warning("bilibili dynamic probe failed: {}", error)
            await ctx.finish(
                f"B站动态连接失败：UID {uid} 请求 B站接口失败，请稍后再试。"
            )
            return
        except Exception as error:
            logger.exception("bilibili dynamic probe failed: {}", error)
            await ctx.finish(
                f"B站动态连接失败：UID {uid} 请求 B站接口失败，请稍后再试。"
            )
            return
        if not items:
            lines.append(f"UID {uid}，当前没有可推送的新动态")
        else:
            lines.append(
                f"UID {uid}，获取到 {len(items)} 条最新动态"
                f"（最新 ID {items[0].dynamic_id}）"
            )
    await ctx.finish(f"B站动态连接正常：{'；'.join(lines)}。")


async def handle_add_uid(ctx, uids: list[int]) -> None:
    if ctx.group_id is None:
        return
    store = SubscriptionStore()
    added = [u for u in uids if store.add_group_uid(int(ctx.bot.self_id), ctx.group_id, u)]
    if not added:
        await ctx.finish("这些 B站 UID 已在当前群关注列表中")
        return
    await ctx.finish(f"已为当前群添加 B站 UID：{'、'.join(str(u) for u in added)}")


async def handle_remove_uid(ctx, uids: list[int]) -> None:
    if ctx.group_id is None:
        return
    store = SubscriptionStore()
    removed = [u for u in uids if store.remove_group_uid(int(ctx.bot.self_id), ctx.group_id, u)]
    if not removed:
        await ctx.finish("这些 B站 UID 不在当前群关注列表中")
        return
    await ctx.finish(f"已为当前群删除 B站 UID：{'、'.join(str(u) for u in removed)}")


async def handle_view_uid(ctx) -> None:
    if ctx.group_id is None:
        return
    group_uids = SubscriptionStore().group_uids(int(ctx.bot.self_id), ctx.group_id)
    if group_uids:
        await ctx.finish(f"当前群关注的 B站 UID：{'、'.join(str(u) for u in group_uids)}")
        return
    global_uids = list(plugin_config.uids) or list(DEFAULT_UIDS)
    await ctx.finish(
        f"当前群未单独设置 B站 UID，使用全局配置：{'、'.join(str(u) for u in global_uids)}"
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


@add_uid_command.handle()
async def _add_uid_handler(bot, event) -> None:
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return
    uids = _parse_uids(event.get_plaintext())
    if not uids:
        await add_uid_command.finish("请提供要添加的 B站 UID，例如：牛牛B站添加UID 12345")
        return
    await handle_add_uid(add_uid_command, uids)


@remove_uid_command.handle()
async def _remove_uid_handler(bot, event) -> None:
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return
    uids = _parse_uids(event.get_plaintext())
    if not uids:
        await remove_uid_command.finish("请提供要删除的 B站 UID，例如：牛牛B站删除UID 12345")
        return
    await handle_remove_uid(remove_uid_command, uids)


@view_uid_command.handle()
async def _view_uid_handler(bot, event) -> None:
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return
    await handle_view_uid(view_uid_command)
