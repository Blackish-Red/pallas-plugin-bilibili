"""B站动态推送的运行时入口。"""

from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler

from .client import BilibiliClient
from .config import plugin_config
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
        service = DynamicPushService(
            client=BilibiliClient(cookie=config.cookie),
            store=DeliveryCursorStore(),
        )
        await service.poll([161775300], targets)
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


@driver.on_startup
async def start_bilibili_dynamic_poll() -> None:
    reschedule_poll_job(interval_sec=plugin_config.poll_interval_sec)
