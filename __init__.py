"""社区插件安装入口。"""

import sys
from pathlib import Path

_SRC = str(Path(__file__).parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from pallas_plugin_bilibili import __plugin_meta__ as __plugin_meta__  # noqa: E402
