import importlib.util
import sys
from pathlib import Path


def test_root_entrypoint_exports_plugin_metadata() -> None:
    root = Path(__file__).parents[1]
    entrypoint = root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "bilibili_dynamic",
        entrypoint,
        submodule_search_locations=[str(root)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)

    assert module.__plugin_meta__.name == "B站动态推送"
