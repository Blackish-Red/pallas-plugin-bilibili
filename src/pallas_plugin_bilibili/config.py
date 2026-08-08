from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from pallas.console.webui import install_hot_reload_config, plugin_config_proxy


class PushTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_qq: PositiveInt
    group_id: PositiveInt

    @property
    def key(self) -> str:
        return f"{self.bot_qq}:{self.group_id}"


class Config(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(
        default=True,
        description="是否启用 B站动态轮询。",
        json_schema_extra={"label": "启用 B站动态推送"},
    )
    uids: list[PositiveInt] = Field(
        default_factory=list,
        description="要关注的 B站 UID 列表。",
        json_schema_extra={"ui_hidden": True},
    )
    targets: list[PushTarget] = Field(
        default_factory=list,
        description="投递目标：Bot QQ 与群号。",
        json_schema_extra={"ui_hidden": True},
    )
    poll_interval_sec: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="轮询间隔（秒）。",
        json_schema_extra={"label": "轮询间隔（秒）"},
    )
    cookie: str = Field(
        default="",
        json_schema_extra={"secret": True, "label": "B站登录 Cookie"},
        description="可选 B站登录 Cookie。",
    )


def _on_reload(config: Config) -> None:
    from .startup import reschedule_poll_job

    reschedule_poll_job(interval_sec=config.poll_interval_sec)


plugin_webui = install_hot_reload_config(
    Config,
    config_module=__name__,
    register_keys=(__name__, "local.plugins.bilibili_dynamic.config"),
    on_reload=_on_reload,
)
get_bilibili_config = plugin_webui.get
plugin_config = plugin_config_proxy(get_bilibili_config)
