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
                                    "pics": [
                                        {"url": "https://i0.hdslb.com/a.gif"},
                                        {"url": "//i0.hdslb.com/b.gif"},
                                    ],
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
    assert items[0].image_urls == (
        "https://i0.hdslb.com/a.gif",
        "https://i0.hdslb.com/b.gif",
    )


@pytest.mark.asyncio
async def test_fetch_latest_maps_risk_control_response() -> None:
    client = BilibiliClient(
        get_json=AsyncMock(return_value={"code": -352, "message": "risk"}),
        get_bytes=AsyncMock(),
    )

    with pytest.raises(BilibiliRiskControlError):
        await client.fetch_latest(161775300)


@pytest.mark.asyncio
async def test_fetch_latest_handles_desc_none() -> None:
    response = {
        "code": 0,
        "data": {
            "items": [
                {
                    "id_str": "101",
                    "type": "DYNAMIC_TYPE_DRAW",
                    "modules": {
                        "module_author": {"name": "明日方舟", "pub_ts": 1},
                        "module_dynamic": {
                            "topic": None,
                            "desc": None,
                            "major": {
                                "type": "MAJOR_TYPE_ARCHIVE",
                                "archive": {"title": "x", "pic": "https://i0.hdslb.com/a.gif"},
                            },
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

    assert [item.dynamic_id for item in items] == ["101"]
    assert items[0].text == "x"


@pytest.mark.asyncio
async def test_fetch_latest_parses_video_title_cover_and_url() -> None:
    response = {
        "code": 0,
        "data": {
            "items": [
                {
                    "id_str": "102",
                    "type": "DYNAMIC_TYPE_AV",
                    "modules": {
                        "module_author": {"name": "明日方舟", "pub_ts": 1},
                        "module_dynamic": {
                            "major": {
                                "type": "MAJOR_TYPE_ARCHIVE",
                                "archive": {
                                    "title": "视频标题",
                                    "bvid": "BV1xx411c7mD",
                                    "pic": "//i0.hdslb.com/video.jpg",
                                },
                            }
                        },
                    },
                }
            ]
        },
    }
    client = BilibiliClient(
        get_json=AsyncMock(return_value=response), get_bytes=AsyncMock()
    )

    items = await client.fetch_latest(161775300)

    assert items[0].text == "视频标题"
    assert items[0].image_urls == ("https://i0.hdslb.com/video.jpg",)
    assert items[0].video_url == "https://www.bilibili.com/video/BV1xx411c7mD"
