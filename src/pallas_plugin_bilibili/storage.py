import json
from pathlib import Path

from nonebot import logger

from pallas.core.foundation.paths import plugin_data_dir

from .config import PushTarget

_MAX_IDS = 50


class DeliveryCursorStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = (
            path or plugin_data_dir("bilibili_dynamic") / "delivery-cursors.json"
        )
        self._routes = self._load()

    def is_primed(self, uid: str, route_key: str) -> bool:
        return bool(self._matching_routes(uid, route_key))

    def was_delivered(self, uid: str, route_key: str, dynamic_id: str) -> bool:
        return any(
            dynamic_id in rows
            for rows in self._matching_routes(uid, route_key).values()
        )

    def prime(self, uid: str, route_key: str, dynamic_ids: list[str]) -> None:
        self._routes.setdefault(uid, {})[route_key] = list(dict.fromkeys(dynamic_ids))[
            :_MAX_IDS
        ]
        self._save()

    def mark_delivered(self, uid: str, route_key: str, dynamic_id: str) -> None:
        rows = self._routes.setdefault(uid, {}).setdefault(route_key, [])
        if dynamic_id in rows:
            return
        rows.insert(0, dynamic_id)
        del rows[_MAX_IDS:]
        self._save()

    def _matching_routes(self, uid: str, route_key: str) -> dict[str, list[str]]:
        routes = self._routes.get(uid, {})
        matching = {route_key: routes[route_key]} if route_key in routes else {}
        if route_key.isdigit():
            matching.update(
                {
                    key: rows
                    for key, rows in routes.items()
                    if key.endswith(f":{route_key}")
                }
            )
        return matching

    def _load(self) -> dict[str, dict[str, list[str]]]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as e:
            logger.warning("bilibili dynamic cursor load failed: {}", e)
            return {}
        routes = raw.get("routes") if isinstance(raw, dict) else None
        if not isinstance(routes, dict):
            return {}
        return {
            str(uid): {
                str(route): [str(item) for item in ids if str(item)]
                for route, ids in rows.items()
                if isinstance(ids, list)
            }
            for uid, rows in routes.items()
            if isinstance(rows, dict)
        }

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._path.with_suffix(".tmp")
        temp.write_text(
            json.dumps({"version": 1, "routes": self._routes}, ensure_ascii=False),
            encoding="utf-8",
        )
        temp.replace(self._path)


class SubscriptionStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or plugin_data_dir("bilibili_dynamic") / "subscriptions.json"

    def targets(self) -> list[PushTarget]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as e:
            logger.warning("bilibili subscriptions load failed: {}", e)
            return []
        rows = raw.get("targets") if isinstance(raw, dict) else None
        if not isinstance(rows, list):
            return []
        return [
            target for row in rows if (target := self._parse_target(row)) is not None
        ]

    def enable(self, bot_qq: int, group_id: int) -> bool:
        targets = self.targets()
        if any(
            target.bot_qq == bot_qq and target.group_id == group_id
            for target in targets
        ):
            return False
        targets.append(PushTarget(bot_qq=bot_qq, group_id=group_id))
        self._save(targets)
        return True

    def disable(self, bot_qq: int, group_id: int) -> bool:
        targets = self.targets()
        kept = [
            target
            for target in targets
            if (target.bot_qq, target.group_id) != (bot_qq, group_id)
        ]
        if len(kept) == len(targets):
            return False
        self._save(kept)
        return True

    @staticmethod
    def _parse_target(row: object) -> PushTarget | None:
        try:
            return PushTarget.model_validate(row)
        except ValueError:
            return None

    def _save(self, targets: list[PushTarget]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {"version": 1, "targets": [target.model_dump() for target in targets]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temp.replace(self._path)
