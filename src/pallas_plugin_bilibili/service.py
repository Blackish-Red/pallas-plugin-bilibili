from collections.abc import Awaitable, Callable
from typing import Any

from nonebot import logger
from pallas.api.logging import format_plugin_event

from .config import PushTarget
from .models import DynamicItem
from .render import render_dynamic
from .storage import DeliveryCursorStore


class DynamicPushService:
    def __init__(
        self,
        *,
        client: Any,
        store: DeliveryCursorStore,
        send: Callable[..., Awaitable[bool]] | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self.send = send or self._send_group_message

    @staticmethod
    async def _send_group_message(*args: Any, **kwargs: Any) -> bool:
        from pallas.api.platform import send_group_message_as_bot

        return await send_group_message_as_bot(*args, **kwargs)

    async def poll_target_uid(self, target: PushTarget, uid: int) -> None:
        items: list[DynamicItem] = await self.client.fetch_latest(uid)
        await self._deliver_items(target, uid, items)

    async def poll(self, uids: list[int], targets: list[PushTarget]) -> None:
        for uid in uids:
            try:
                items: list[DynamicItem] = await self.client.fetch_latest(uid)
            except Exception as e:
                logger.warning(f"Bilibili dynamic poll failed for uid [{uid}]: {e}")
                continue
            for target in targets:
                await self._deliver_items(target, uid, items)

    async def _deliver_items(
        self, target: PushTarget, uid: int, items: list[DynamicItem]
    ) -> None:
        state_uid = str(uid)
        delivery_key = str(target.group_id)
        if not self.store.is_primed(state_uid, delivery_key):
            self.store.prime(
                state_uid, delivery_key, [item.dynamic_id for item in items]
            )
            return
        for item in sorted(items, key=lambda row: row.published_at):
            if self.store.was_delivered(state_uid, delivery_key, item.dynamic_id):
                continue
            rendered = render_dynamic(item)
            image_bytes = None
            if rendered.image_url:
                try:
                    image_bytes = await self.client.download_image(rendered.image_url)
                except Exception as e:
                    logger.warning(
                        f"Bilibili dynamic [{item.dynamic_id}] media fallback, "
                        f"image download failed: {e}"
                    )
            sent = await self.send(
                target.bot_qq, target.group_id, rendered.text, image_bytes=image_bytes
            )
            if sent:
                self.store.mark_delivered(state_uid, delivery_key, item.dynamic_id)
                logger.info(
                    format_plugin_event(
                        "bilibili_push",
                        f"Bot [{target.bot_qq}] pushed B站 dynamic [{item.dynamic_id}] "
                        f"to group [{target.group_id}]",
                    )
                )
            else:
                logger.warning(
                    f"Bot [{target.bot_qq}] failed to push dynamic [{item.dynamic_id}] "
                    f"to group [{target.group_id}]"
                )
