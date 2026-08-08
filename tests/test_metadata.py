from pallas_plugin_bilibili import __plugin_meta__


def test_plugin_metadata_declares_onebot_and_metadata_reload() -> None:
    assert __plugin_meta__.name == "B站动态推送"
    assert __plugin_meta__.supported_adapters == {"~onebot.v11"}
    assert __plugin_meta__.extra["reload_policy"] == "metadata"
    assert __plugin_meta__.extra["disable_scope"] == "bot"
