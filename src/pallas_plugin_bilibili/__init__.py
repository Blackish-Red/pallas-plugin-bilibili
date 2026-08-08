from nonebot.plugin import PluginMetadata

from pallas.api.commands import (
    command_limit_list,
    command_limit_row,
    command_perm_list,
    command_perm_row,
)
from pallas.api.metadata import SCENE_GROUP, join_usage, usage_line

from . import commands as _commands  # noqa: F401
from . import startup as _startup  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="B站动态推送",
    description="将配置的 B站账号新增动态推送到指定群。",
    usage=join_usage(
        usage_line("牛牛开启B站推送", "订阅明日方舟官方 B站动态"),
        usage_line("牛牛关闭B站推送", "停止推送明日方舟官方 B站动态"),
    ),
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "reload_policy": "metadata",
        "disable_scope": "bot",
        "exact_plaintexts": [
            "牛牛开启B站推送",
            "牛牛开启b站推送",
            "牛牛关闭B站推送",
            "牛牛关闭b站推送",
        ],
        "command_permissions": command_perm_list(
            command_perm_row(
                "bilibili_dynamic.enable", "牛牛开启B站推送", "group_moderator"
            ),
            command_perm_row(
                "bilibili_dynamic.disable", "牛牛关闭B站推送", "group_moderator"
            ),
        ),
        "command_limits": command_limit_list(
            command_limit_row("bilibili_dynamic.enable", 3),
            command_limit_row("bilibili_dynamic.disable", 3),
        ),
        "menu_data": [
            {
                "func": "B站动态推送",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛开启B站推送 / 牛牛关闭B站推送",
                "command_permissions": [
                    "bilibili_dynamic.enable",
                    "bilibili_dynamic.disable",
                ],
                "brief_des": "订阅或停止明日方舟官方动态",
                "detail_des": "群内订阅明日方舟官方 B站账号的新动态。",
            }
        ],
    },
)
