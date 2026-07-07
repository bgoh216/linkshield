from app.main import app
from app.dependencies import get_security_pipeline
from app import models

from conftest import FakeRejectPipeline


def test_create_link_generates_random_short_code(client):
    res = client.post("/api/links", json={"long_url": "https://example.com/a"})
    assert res.status_code == 200
    body = res.json()
    assert len(body["short_code"]) == 7
    assert body["click_count"] == 0
    assert body["is_flagged"] is False


def test_create_link_with_custom_code(client):
    res = client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "mycode"})
    assert res.status_code == 200
    assert res.json()["short_code"] == "mycode"


def test_create_link_custom_code_collision_returns_409(client):
    client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "dup"})
    res = client.post("/api/links", json={"long_url": "https://example.com/b", "custom_code": "dup"})
    assert res.status_code == 409


def test_create_link_rejected_by_pipeline_returns_400(client):
    app.dependency_overrides[get_security_pipeline] = lambda: FakeRejectPipeline("blacklist", "blocked domain")
    res = client.post("/api/links", json={"long_url": "https://badsite.com/x"})
    assert res.status_code == 400
    assert "blacklist" in res.json()["detail"]


def test_list_links_orders_by_created_at_desc(client, db_session):
    from datetime import datetime, timedelta

    client.post("/api/links", json={"long_url": "https://example.com/first", "custom_code": "first"})
    client.post("/api/links", json={"long_url": "https://example.com/second", "custom_code": "second"})

    # SQLite's server_default=func.now() only has whole-second resolution, so
    # two rapid inserts can land in the same second — pin distinct timestamps
    # explicitly rather than relying on real-time ordering.
    first = db_session.query(models.Link).filter(models.Link.short_code == "first").first()
    second = db_session.query(models.Link).filter(models.Link.short_code == "second").first()
    first.created_at = datetime(2024, 1, 1)
    second.created_at = datetime(2024, 1, 1) + timedelta(seconds=1)
    db_session.commit()

    res = client.get("/api/links")
    assert res.status_code == 200
    codes = [item["short_code"] for item in res.json()]
    assert codes == ["second", "first"]


def test_link_stats_404_for_unknown_code(client):
    res = client.get("/api/links/doesnotexist/stats")
    assert res.status_code == 404


def test_link_stats_reflects_click_count(client):
    client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "stats1"})
    client.post("/api/links/stats1/click", json={})
    res = client.get("/api/links/stats1/stats")
    assert res.status_code == 200
    assert res.json()["total_clicks"] == 1


def test_redirect_returns_302_to_long_url_and_records_click(client, db_session):
    client.post("/api/links", json={"long_url": "https://example.com/target", "custom_code": "red1"})
    res = client.get("/r/red1")
    assert res.status_code == 302
    assert res.headers["location"] == "https://example.com/target"

    link = db_session.query(models.Link).filter(models.Link.short_code == "red1").first()
    assert len(link.clicks) == 1


def test_redirect_404_for_unknown_code(client):
    res = client.get("/r/doesnotexist")
    assert res.status_code == 404


def test_redirect_403_when_link_already_flagged(client, db_session):
    client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "flagged1"})
    link = db_session.query(models.Link).filter(models.Link.short_code == "flagged1").first()
    link.is_flagged = True
    db_session.commit()

    res = client.get("/r/flagged1")
    assert res.status_code == 403


def test_redirect_403_and_flags_link_when_pipeline_fails_at_click_time(client, db_session):
    client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "willflag"})

    app.dependency_overrides[get_security_pipeline] = lambda: FakeRejectPipeline("ssrf", "now unsafe")
    res = client.get("/r/willflag")
    assert res.status_code == 403

    link = db_session.query(models.Link).filter(models.Link.short_code == "willflag").first()
    assert link.is_flagged is True


def test_click_endpoint_returns_redirect_url_without_redirecting(client, db_session):
    client.post("/api/links", json={"long_url": "https://example.com/enriched", "custom_code": "click1"})
    res = client.post(
        "/api/links/click1/click",
        json={"screen_width": 1920, "screen_height": 1080, "timezone": "UTC", "language": "en-US"},
    )
    assert res.status_code == 200
    assert res.json()["redirect_url"] == "https://example.com/enriched"

    link = db_session.query(models.Link).filter(models.Link.short_code == "click1").first()
    assert link.clicks[0].device_metadata["timezone"] == "UTC"


def test_delete_link_cascades_and_returns_404_after(client, db_session):
    client.post("/api/links", json={"long_url": "https://example.com/a", "custom_code": "del1"})
    client.post("/api/links/del1/click", json={})
    link_id = db_session.query(models.Link).filter(models.Link.short_code == "del1").first().id

    res = client.delete("/api/links/del1")
    assert res.status_code == 204

    assert client.get("/api/links/del1/stats").status_code == 404
    assert db_session.query(models.Click).filter(models.Click.link_id == link_id).count() == 0


def test_delete_link_404_for_unknown_code(client):
    res = client.delete("/api/links/doesnotexist")
    assert res.status_code == 404
