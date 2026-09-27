# TikTok Creative Patterns

An offline-first marketer demo that labels visible caption-level structures on public TikTok posts. Patterns are research hypotheses to help organize manual creative review, not findings that a hook caused performance.

## Use cases and architecture

Use a small set of campaign or competitor video URLs to inventory first-person hooks, questions, contrast language, numbered lists, and explicit caption CTAs. Flow: `CSV video URLs -> Bright Data TikTok Posts dataset -> deterministic caption rules -> JSON/CSV`. No video is downloaded, transcribed, or visually analyzed. Python 3.10+ standard library runtime.

## Setup and Bright Data

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Create a key from [Bright Data account settings](https://brightdata.com/cp/setting/users), export `BRIGHT_DATA_API_KEY`; `.env` is a template only and the CLI reads process environment. Official references: [TikTok Scraper API](https://docs.brightdata.com/products/scrapers/tiktok/introduction.md), [synchronous requests](https://docs.brightdata.com/api-reference/scrapers/synchronous-requests), [async requests](https://docs.brightdata.com/products/scrapers/scrapers-library/async-requests.md). This example uses the documented TikTok Posts dataset `gd_lu702nij2f790tmv9h` and post URL collection, not assumptions about search ranking or arbitrary discovery input.

## Run

```bash
python patterns.py sample_posts.json creative_patterns.json
python patterns.py sample_posts.json creative_patterns.csv
```

For live data provide CSV `url` values for public TikTok videos:

```bash
python patterns.py video_urls.csv patterns.json
python patterns.py video_urls.csv patterns.json --dry-run
```

Dry-run is local-only and makes no billable request. Synchronous collection is capped at the documented 20 URLs per request. Check current [Web Scraper pricing](https://brightdata.com/pricing/web-scraper) and account billing before live calls. Async responses are surfaced as unsupported rather than hidden.

## Output schema

`evidence_url`, `caption`, `posted_at`, documented TikTok Posts-by-URL counters `play_count`, `collect_count`, `comment_count`, `share_count`, `patterns` (array in JSON; semicolon-separated CSV), and `interpretation=observable_caption_hypotheses_not_causal_findings`. These counters are passed through only when supplied by the collector; they are not renamed to generic views or likes. Missing fields remain empty/null. The deterministic rules are intentionally simple, may miss language/context, and do not score success or recommend copying a creative.

## Boundaries and troubleshooting

Use public URLs for research only. This tool does not log in, evade access controls, download media, infer sensitive traits, identify people, or publish/comment/message. Public visibility is not authorization; follow platform terms, applicable law, and retention/deletion requirements. Metrics vary over time and aren't comparable without controlled sampling.

- Missing API key: offline sample and dry-run do not need one.
- 401/403: verify key and TikTok dataset permissions.
- 429: stop, reduce volume and wait; no rapid retry loop is implemented.
- Empty patterns: this means no literal cue rule matched, not that no creative technique exists.

```bash
python3 -m pytest -q
```

Tests cover deterministic captions, empty inputs, source URLs, and CSV output. Fixtures are illustrative. MIT License.
