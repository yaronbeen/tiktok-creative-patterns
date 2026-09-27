import patterns


def test_detects_caption_level_hypotheses_without_causal_claim():
    result = patterns.analyze({"url": "https://www.tiktok.com/@brand/video/123", "description": "I tried this so you don't have to. Before and after! Shop now #skincare", "create_time": "2026-09-25T10:00:00Z", "play_count": 1000, "collect_count": 50})
    assert "first_person_hook" in result["patterns"]
    assert "contrast_hook" in result["patterns"]
    assert result["evidence_url"].endswith("/123")
    assert result["interpretation"] == "observable_caption_hypotheses_not_causal_findings"


def test_empty_caption_is_unknown_pattern():
    result = patterns.analyze({"url": "https://tiktok.com/@x/video/2"})
    assert result["patterns"] == []
    assert result["caption"] == ""


def test_uses_documented_tiktok_post_metric_fields():
    result = patterns.analyze({"url": "https://www.tiktok.com/@x/video/1", "description": "x", "play_count": 500, "collect_count": 20, "comment_count": 4, "share_count": 2})
    assert result["play_count"] == 500
    assert result["collect_count"] == 20
    assert result["comment_count"] == 4
    assert result["share_count"] == 2


def test_csv(tmp_path):
    patterns.write_csv(tmp_path / "out.csv", [patterns.analyze({"url": "https://tiktok.com/@x/video/2"})])
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
    assert patterns.main([str(source), str(tmp_path / "out.json")]) == 2
    assert "URL" in capsys.readouterr().err
