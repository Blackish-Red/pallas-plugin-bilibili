from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bilibili.client import BilibiliClient, BilibiliRiskControlError


@pytest.mark.asyncio
async def test_fetch_latest_skips_pinned_and_parses_opus() -> None:
    response = {
        "code": 0,
        "data": {
            "items": [
                {"id_str": "pinned", "modules": {"module_tag": {"text": "置顶"}}},
                {
                    "id_str": "100",
                    "type": "DYNAMIC_TYPE_DRAW",
                    "modules": {
                        "module_author": {"name": "明日方舟", "pub_ts": 1},
                        "module_dynamic": {
                            "major": {
                                "type": "MAJOR_TYPE_OPUS",
                                "opus": {
                                    "summary": {"text": "活动预告"},
                                    "pics": [{"url": "https://i0.hdslb.com/a.gif"}],
                                },
                            }
                        },
                    },
                },
            ]
        },
    }
    client = BilibiliClient(
        get_json=AsyncMock(return_value=response), get_bytes=AsyncMock()
    )

    items = await client.fetch_latest(161775300)

    assert [item.dynamic_id for item in items] == ["100"]
    assert items[0].text == "活动预告"
    assert items[0].image_url == "https://i0.hdslb.com/a.gif"


@pytest.mark.asyncio
async def test_fetch_latest_maps_risk_control_response() -> None:
    client = BilibiliClient(
        get_json=AsyncMock(return_value={"code": -352, "message": "risk"}),
        get_bytes=AsyncMock(),
    )

    with pytest.raises(BilibiliRiskControlError):
        await client.fetch_latest(161775300)
