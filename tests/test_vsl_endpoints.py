import pytest
from fastapi.testclient import TestClient
from server import app
from modules.database import (
    create_db_vsl_video, 
    get_db_vsl_video, 
    get_db_vsl_videos, 
    delete_db_vsl_video, 
    add_db_vsl_analytics_event, 
    get_db_vsl_analytics_summary
)

client = TestClient(app)

def test_vsl_db_crud():
    # 1. Test create
    vsl = create_db_vsl_video(
        title="Test VSL Title",
        video_url="https://test.com/video.mp4",
        nicho="Finanças",
        delay_seconds=60,
        headline_a="Headline A",
        headline_b="Headline B",
        headline_c="Headline C"
    )
    assert vsl["id"] is not None
    assert vsl["title"] == "Test VSL Title"
    assert vsl["video_url"] == "https://test.com/video.mp4"
    assert vsl["nicho"] == "Finanças"
    assert vsl["delay_seconds"] == 60
    assert vsl["headline_a"] == "Headline A"

    # 2. Test get
    retrieved = get_db_vsl_video(vsl["id"])
    assert retrieved["id"] == vsl["id"]
    assert retrieved["title"] == "Test VSL Title"

    # 3. Test list
    videos = get_db_vsl_videos()
    assert len(videos) >= 1
    assert any(v["id"] == vsl["id"] for v in videos)

    # 4. Test analytics events
    event = add_db_vsl_analytics_event(
        vsl_id=vsl["id"],
        session_id="session_test_123",
        seconds_watched=30,
        max_percentage=50,
        converted=True,
        headline_variant="B"
    )
    assert event["session_id"] == "session_test_123"
    assert event["max_percentage"] == 50
    assert event["converted"] is True
    assert event["headline_variant"] == "B"

    # 5. Test analytics summary
    summary = get_db_vsl_analytics_summary(vsl["id"])
    assert summary["total_plays"] == 1
    assert summary["conversions"] == 1
    assert summary["ctr"] == 100.0
    assert summary["retention"]["p50"] == 100.0
    assert summary["headline_performance"]["B"]["plays"] == 1
    assert summary["headline_performance"]["B"]["conversions"] == 1

    # 6. Test delete
    deleted = delete_db_vsl_video(vsl["id"])
    assert deleted is True
    assert get_db_vsl_video(vsl["id"]) == {}
