"""B站动态推送的运行时入口。"""

import asyncio

from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler

from pallas.api.logging import register_plugin_startup_ready

from .client import BilibiliClient
from .config import DEFAULT_UIDS, PushTarget, plugin_config
from .service import DynamicPushService
from .storage import DeliveryCursorStore, SubscriptionStore

JOB_ID = "bilibili_dynamic_poll"
driver = get_driver()


async def poll_job() -> None:
    config = plugin_config
    targets = SubscriptionStore().targets()
    if not config.enabled or not targets:
        return
    try:
        uid_targets: dict[int, list[PushTarget]] = {}
        for target in targets:
            uids = target.uids or list(config.uids) or list(DEFAULT_UIDS)
            for uid in uids:
                uid_targets.setdefault(uid, []).append(target)
        service = DynamicPushService(
            client=BilibiliClient(cookie=config.cookie),
            store=DeliveryCursorStore(),
            forward_multiple_images=config.forward_multiple_images,
        )
        await service.poll(uid_targets)
    except Exception:
        logger.exception("bilibili dynamic poll failed")


def reschedule_poll_job(*, interval_sec: int) -> None:
    scheduler.add_job(
        poll_job,
        "interval",
        seconds=interval_sec,
        id=JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )


async def prime_initial_cursors() -> None:
    """启动时以当前最新动态静默对齐投递游标，不补推停机期间积压的动态。"""
    config = plugin_config
    targets = SubscriptionStore().targets()
    if not config.enabled or not targets:
        return
    try:
        uid_targets: dict[int, list[PushTarget]] = {}
        for target in targets:
            uids = target.uids or list(config.uids) or list(DEFAULT_UIDS)
            for uid in uids:
                uid_targets.setdefault(uid, []).append(target)
        client = BilibiliClient(cookie=config.cookie)
        store = DeliveryCursorStore()
        aligned = 0
        for uid, targets_for_uid in uid_targets.items():
            try:
                items = await client.fetch_latest(uid)
            except Exception as e:
                logger.warning(
                    f"Bilibili dynamic startup prime failed for uid [{uid}]: {e}"
                )
                continue
            if not items:
                continue
            ids = [item.dynamic_id for item in items]
            for target in targets_for_uid:
                store.prime(str(uid), str(target.group_id), ids)
                aligned += 1
        if aligned:
            logger.info(
                "Bilibili 动态启动游标已对齐 [{}] 个投递目标，不补发停机期间积压的动态",
                aligned,
            )
    except Exception:
        logger.exception("bilibili dynamic startup prime failed")


@driver.on_startup
async def start_bilibili_dynamic_poll() -> None:
    reschedule_poll_job(interval_sec=plugin_config.poll_interval_sec)
    register_plugin_startup_ready(
        "bilibili",
        detail=f"Bilibili 动态轮询调度已注册：每 [{plugin_config.poll_interval_sec}] 秒执行一次",
    )
    asyncio.create_task(prime_initial_cursors())
