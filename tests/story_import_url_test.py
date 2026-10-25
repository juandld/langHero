def test_story_import_supports_source_url(app_client, monkeypatch):
    # url_fetch is imported into routes.import_routes (which hosts the
    # /api/stories/import handler at line 117); patch there, not on main.
    import routes.import_routes as import_routes_mod

    def fake_fetch(url: str, **_kwargs):
        return {
            "url": url,
            "final_url": url,
            "content_type": "text/html; charset=utf-8",
            "title": "Example Page",
            "text": "A stranger approaches.\nThey ask for help.",
        }

    monkeypatch.setattr(import_routes_mod.url_fetch, "fetch_url_text", fake_fetch, raising=True)

    res = app_client.post(
        "/api/stories/import",
        json={
            "source_url": "https://example.com/story",
            "max_scenes": 2,
            "attest_rights": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data.get("scenarios"), list) and len(data["scenarios"]) == 2
    assert data.get("source", {}).get("title") == "Example Page"
