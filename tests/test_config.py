import pytest
from pydantic import ValidationError

from pallas_plugin_bilibili.config import Config


def test_target_requires_positive_bot_and_group_ids() -> None:
    with pytest.raises(ValidationError):
        Config.model_validate({"targets": [{"bot_qq": 0, "group_id": 733291779}]})


def test_cookie_is_secret_and_poll_interval_is_bounded() -> None:
    field = Config.model_fields["cookie"]
    assert field.json_schema_extra["secret"] is True
    assert Config().poll_interval_sec == 300
    with pytest.raises(ValidationError):
        Config.model_validate({"poll_interval_sec": 30})


def test_uids_default_to_official_account_and_accept_custom_list() -> None:
    assert Config().uids == [161775300]
    assert "ui_hidden" not in (Config.model_fields["uids"].json_schema_extra or {})
    assert Config.model_validate({"uids": [1, 2]}).uids == [1, 2]
    with pytest.raises(ValidationError):
        Config.model_validate({"uids": [0]})


def test_root_config_module_exposes_plugin_config() -> None:
    from config import Config as RootConfig

    assert RootConfig is Config
    assert RootConfig.model_fields["cookie"].json_schema_extra["secret"] is True
