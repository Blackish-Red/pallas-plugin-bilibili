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
        usage_line("牛牛订阅B站动态", "订阅配置的 B站账号动态"),
        usage_line("牛牛取消订阅B站动态", "停止推送 B站动态"),
        usage_line("牛牛B站添加UID 12345", "为当前群添加关注的 B站 UID"),
        usage_line("牛牛B站删除UID 12345", "从当前群移除关注的 B站 UID"),
        usage_line("牛牛B站查看UID", "查看当前群关注的 B站 UID"),
        usage_line("牛牛测试B站推送", "检查 B站接口连通性，不发送动态"),
    ),
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "reload_policy": "metadata",
        "disable_scope": "bot",
        "exact_plaintexts": [
            "牛牛订阅B站动态",
            "牛牛订阅b站动态",
            "牛牛取消订阅B站动态",
            "牛牛取消订阅b站动态",
            "牛牛测试B站推送",
            "牛牛测试b站推送",
            "牛牛B站添加UID",
            "牛牛B站删除UID",
            "牛牛B站查看UID",
        ],
        "command_permissions": command_perm_list(
            command_perm_row(
                "bilibili_dynamic.enable", "牛牛订阅B站动态", "group_moderator"
            ),
            command_perm_row(
                "bilibili_dynamic.disable", "牛牛取消订阅B站动态", "group_moderator"
            ),
            command_perm_row("bilibili_dynamic.probe", "牛牛测试B站推送", "superuser"),
            command_perm_row(
                "bilibili_dynamic.add_uid", "牛牛B站添加UID", "group_moderator"
            ),
            command_perm_row(
                "bilibili_dynamic.remove_uid", "牛牛B站删除UID", "group_moderator"
            ),
            command_perm_row(
                "bilibili_dynamic.view_uid", "牛牛B站查看UID", "group_moderator"
            ),
        ),
        "command_limits": command_limit_list(
            command_limit_row("bilibili_dynamic.enable", 3),
            command_limit_row("bilibili_dynamic.disable", 3),
            command_limit_row("bilibili_dynamic.probe", 10),
            command_limit_row("bilibili_dynamic.add_uid", 10),
            command_limit_row("bilibili_dynamic.remove_uid", 10),
            command_limit_row("bilibili_dynamic.view_uid", 10),
        ),
        "menu_data": [
            {
                "func": "B站动态推送",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛订阅B站动态 / 牛牛取消订阅B站动态",
                "command_permissions": [
                    "bilibili_dynamic.enable",
                    "bilibili_dynamic.disable",
                ],
                "brief_des": "订阅或停止 B站动态推送",
                "detail_des": "群内订阅控制台配置的 B站账号（默认明日方舟官方号）的新动态。",
            },
            {
                "func": "B站动态连通性检查",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛测试B站推送",
                "command_permission": "bilibili_dynamic.probe",
                "brief_des": "检查 B站动态接口连通性",
                "detail_des": "不会发送动态或改动投递游标。",
            },
            {
                "func": "B站动态 UID 管理",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛B站添加UID / 牛牛B站删除UID / 牛牛B站查看UID",
                "command_permissions": [
                    "bilibili_dynamic.add_uid",
                    "bilibili_dynamic.remove_uid",
                    "bilibili_dynamic.view_uid",
                ],
                "brief_des": "管理当前群关注的 B站 UID",
                "detail_des": "群可独立订阅自己的 B站 UID 列表；未设置时使用全局配置。",
            },
        ],
    },
)
