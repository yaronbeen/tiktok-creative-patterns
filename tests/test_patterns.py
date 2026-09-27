import patterns


def test_detects_caption_level_hypotheses_without_causal_claim():
    result = patterns.analyze({"url": "https://www.tiktok.com/@brand/video/123", "description": "I tried this so you don't have to. Before and after! Shop now #skincare", "create_time": "2026-09-25T10:00:00Z", "play_count": 1000, "collect_count": 50})
    assert "first_person_opening_cue" in result["patterns"]
    assert "contrast_phrase_cue" in result["patterns"]
    assert result["evidence_url"].endswith("/123")
    assert result["interpretation"] == "literal_caption_cues_for_human_review_not_semantic_or_causal_findings"


def test_empty_caption_is_unknown_pattern():
    result = patterns.analyze({"url": "https://tiktok.com/@x/video/2"})
    assert result["patterns"] == []
    assert result["caption"] == ""


def test_first_person_hook_only_matches_caption_opening():
    result = patterns.analyze({"description": "A product demo first. Later, I tried it at home."})
    assert "first_person_opening_cue" not in result["patterns"]


def test_uses_documented_tiktok_post_metric_fields():
    result = patterns.analyze({"url": "https://www.tiktok.com/@x/video/1", "description": "x", "play_count": 500, "collect_count": 20, "comment_count": 4, "share_count": 2})
    assert result["play_count"] == 500
    assert result["collect_count"] == 20
    assert result["comment_count"] == 4
    assert result["share_count"] == 2


def test_csv(tmp_path):
    patterns.write_csv(tmp_path / "out.csv", patterns.build_report([{"url": "https://tiktok.com/@x/video/2"}])["observations"])
    assert "patterns" in (tmp_path / "out.csv").read_text()


def test_sync_collection_limit_is_explicit():
    try:
        patterns.collect(["https://www.tiktok.com/@x/video/1"] * 21, "token")
    except ValueError as exc:
        assert "20" in str(exc)
    else:
        assert False, "sync collector must reject more than 20 URLs"


def test_live_csv_rejects_rows_without_urls(tmp_path, capsys):
    source = tmp_path / "videos.csv"
    source.write_text("url,note\nhttps://www.tiktok.com/@x/video/1,valid\n,missing\n")
    assert patterns.main([str(source), str(tmp_path / "out.json"), "--live"]) == 2
    assert "URL" in capsys.readouterr().err


def test_rejects_lookalike_hosts_and_non_video_routes():
    for url in ("https://www.tiktok.com.evil.example/@user/video/123", "https://www.tiktok.com/@user"):
        try:
            patterns.validate_video_url(url)
        except ValueError:
            continue
        assert False, f"non-video TikTok URL accepted: {url}"


def test_report_groups_observed_patterns_and_generates_review_briefs():
    report = patterns.build_report([
        {"url": "https://www.tiktok.com/@x/video/1", "description": "I tried this before and after. Shop now", "play_count": 1000},
        {"url": "https://www.tiktok.com/@y/video/2", "description": "I tested a different method", "play_count": 800},
    ])
    first_person = next(row for row in report["pattern_summary"] if row["pattern"] == "first_person_opening_cue")
    assert first_person["post_count"] == 2
    brief = next(row for row in report["experiment_briefs"] if row["pattern"] == "first_person_opening_cue")
    assert brief["human_review_required"] is True
    assert "not causal" in brief["limitation"].lower()


def test_live_mode_is_explicit_and_validates_all_urls_before_request(tmp_path, monkeypatch):
    source = tmp_path / "videos.csv"
    source.write_text("url\nhttps://tiktok.com/@x/video/1\nhttps://tiktok.com.evil.test/@x/video/2\n")
    monkeypatch.setattr(patterns, "collect", lambda *args: (_ for _ in ()).throw(AssertionError("request happened before validation")))
    assert patterns.main([str(source), "--live", "--dry-run"]) == 2


def test_csv_formula_values_are_neutralized(tmp_path):
    row = patterns.analyze({"url": "https://tiktok.com/@x/video/1", "description": "=HYPERLINK(\"x\")"})
    patterns.write_csv(tmp_path / "safe.csv", [row])
    assert "'=HYPERLINK" in (tmp_path / "safe.csv").read_text()


def test_collect_request_contract(monkeypatch):
    import json
    captured = {}
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'[]'
    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data)
        return Response()
    monkeypatch.setattr(patterns, "urlopen", fake_urlopen)
    patterns.collect(["https://tiktok.com/@x/video/1"], "token")
    assert "dataset_id=" + patterns.DATASET in captured["url"]
    assert captured["payload"] == {"input": [{"url": "https://tiktok.com/@x/video/1"}]}


def test_offline_csv_with_url_and_counter_is_not_treated_as_url_list(tmp_path):
    source = tmp_path / "records.csv"
    source.write_text("url,play_count\nhttps://tiktok.com/@x/video/1,100\n")
    assert patterns.main([str(source), str(tmp_path / "out.json")]) == 0
