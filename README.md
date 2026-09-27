# TikTok Caption Cue Lab

An offline-first marketer demo that inventories literal TikTok caption cues and turns them into human-review experiment briefs. It analyzes caption text only: no video visuals, audio, editing, or creative performance analysis.

## Use cases and architecture

Use a small set of campaign or competitor video URLs to inventory literal first-person openings, question marks, contrast phrases, numbered-list phrases, CTA phrases, and returned public post counters. Flow: `explicit --live + CSV video URLs -> Bright Data TikTok Posts dataset -> literal cue counts -> controlled-test briefs for human review`. No video is downloaded, transcribed, or visually analyzed. Python 3.10+ standard library runtime.

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
python patterns.py video_urls.csv patterns.json --live
python patterns.py video_urls.csv patterns.json --live --dry-run
```

Dry-run is local-only and makes no billable request. Synchronous collection is capped at the documented 20 URLs per request. Check current [Web Scraper pricing](https://brightdata.com/pricing/web-scraper) and account billing before live calls. Async responses are surfaced as unsupported rather than hidden.

## Output schema

JSON contains `pattern_summary` with literal cue counts/shares, `experiment_briefs` (hypothesis, proposed single variable, evaluation guidance, human-review flag), and evidence-linked `observations`. CSV is one row per observed post with cue labels, documented TikTok Posts-by-URL counters `play_count`, `collect_count`, `comment_count`, `share_count`, and associated hypothesis text; the summary and caveat are JSON-only. Counters are passed through only when supplied and validated as non-negative integers; they are not renamed to generic views or likes. CSV formula-leading text is prefixed to reduce spreadsheet formula injection risk. No winner is scored because this dataset does not provide controlled ad delivery metrics.

Illustrative use: if 6/15 captions contain a question mark, a marketer may place that cue in a test matrix and compare two controlled variants using their own ad platform’s primary metric. The count is not a performance result and does not mean the cue caused attention or conversion.

## How this differs from existing tools

Despite the repository slug, this is a caption-cue lab, not a visual creative analyzer or performance-ranking product. It is not creator discovery, buyer-comment qualification, or outreach: unlike `bright-data-tiktok-outreach` and `brightdata-mcp-tiktok-buyer-intent-finder`, it does not find creators, extract contact details, qualify individuals, or draft replies. Its output is literal text-cue counts plus a proposed human-reviewed test matrix. Video-level execution and performance measurement must happen elsewhere.

## Boundaries and troubleshooting

Use public URLs for research only. This tool does not log in, evade access controls, download media, infer sensitive traits, identify people, or publish/comment/message. Public visibility is not authorization; follow platform terms, applicable law, and retention/deletion requirements. Metrics vary over time and aren't comparable without controlled sampling.

- Missing API key: offline sample and dry-run do not need one.
- URL-only CSV without `--live`: rejected without a request; add `--live` only when you intend to collect and may incur charges.
- 401/403: verify key and TikTok dataset permissions.
- 429: stop, reduce volume and wait; no rapid retry loop is implemented.
- Empty patterns: this means no literal cue rule matched, not that no creative technique exists.

```bash
python3 -m pytest -q
```

The cue names intentionally say `cue`, not `hook`: the first-person cue only matches a pronoun at the caption opening, question cue a literal `?`, and other cues literal phrase rules. They are not semantic classifications. Tests cover documented metric fields, pattern aggregation, experiment briefs, explicit live opt-in, mocked request shape, unsafe CSV cells, missing URLs, and CSV output. Fixtures are illustrative. MIT License.
