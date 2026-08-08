"""社区安装目录的控制台配置入口。"""

import sys
from pathlib import Path

_SRC = str(Path(__file__).parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from pallas_plugin_bilibili.config import Config  # noqa: E402

__all__ = ["Config"]
