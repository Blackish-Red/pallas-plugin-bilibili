"""B站动态推送的运行时入口。"""

from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler
from pallas.api.logging import register_plugin_startup_ready

from .client import BilibiliClient
from .config import DEFAULT_UIDS, PushTarget, plugin_config
from .service import DynamicPushService
from .storage import DeliveryCursorStore, SubscriptionStore

JOB_ID = "bilibili_dynamic_poll"
driver = get_driver()
_primed_routes: set[tuple[int, int]] = set()


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
        store = DeliveryCursorStore()
        poll_targets: dict[int, list[PushTarget]] = {}
        for uid, uid_route_targets in uid_targets.items():
            for target in uid_route_targets:
                route = (uid, target.group_id)
                if route not in _primed_routes:
                    try:
                        store.clear_route(*route)
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "Bilibili dynamic cursor clear failed for uid [{}], group [{}]",
                            *route,
                        )
                        continue
                    _primed_routes.add(route)
                poll_targets.setdefault(uid, []).append(target)
        if not poll_targets:
            return
        service = DynamicPushService(
            client=BilibiliClient(cookie=config.cookie),
            store=store,
        )
        await service.poll(poll_targets)
    except Exception:  # noqa: BLE001
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


@driver.on_startup
async def start_bilibili_dynamic_poll() -> None:
    reschedule_poll_job(interval_sec=plugin_config.poll_interval_sec)
    register_plugin_startup_ready(
        "bilibili",
        detail=f"Bilibili 动态轮询调度已注册：每 [{plugin_config.poll_interval_sec}] 秒执行一次",
    )
