# Bright Data TikTok Caption Cue Lab

**Repository:** [bright-data-tiktok-creative-patterns](https://github.com/yaronbeen/bright-data-tiktok-creative-patterns) · **Data provider:** [Bright Data](https://brightdata.com/)

You have already saved a set of public TikTok video URLs that feel relevant to a campaign. Now you want to compare how their captions frame the opening message without manually opening and sorting every example. **TikTok Caption Cue Lab turns that curated URL set into a literal caption-cue inventory and human-reviewed test hypotheses.** It examines caption text only: it does not analyze video visuals, audio, editing, or creative performance.

## The marketer's workflow

1. An agency or brand manually selects a small, relevant sample of public TikTok posts, such as competitor posts in the same product category. This tool does not find the URLs or discover trends.
2. Put the video URLs in a CSV and explicitly run live collection. The collector requests records from Bright Data's TikTok Posts dataset.
3. The local script checks each returned caption for five literal text patterns, then reports counts/shares for cues found in the sample. It also passes through certain public post counters when returned.
4. Review the source captions and evidence URLs. Use the counts and experiment hypotheses as a starting point to manually draft distinct caption variants and a test matrix for your own content.
5. Run any creative test on your own platform and judge it with a metric and controlled delivery. This tool does not measure that test or predict a winning caption.

The practical payoff is organization: instead of manually sorting every saved example into rough caption categories, you get a repeatable first-pass count and a clearly labeled set of ideas to review. The output is descriptive of the URLs you supplied, not a statement about TikTok as a whole.

## What the cues mean

The matcher uses small, literal phrase rules, not semantic or AI interpretation:

| Output cue | What the current rule matches |
| --- | --- |
| `first_person_opening_cue` | `I`, `my`, `we`, or `our` at the beginning of the caption |
| `question_mark_cue` | A literal `?` anywhere in the caption |
| `contrast_phrase_cue` | One of: `before and after`, `before/after`, `but then`, `until I` |
| `numbered_list_phrase_cue` | A number followed by `ways`, `tips`, `things`, or `steps` |
| `cta_phrase_cue` | One of: `shop now`, `link in bio`, `follow for`, `comment below`, `try it` |

A cue match does not establish that a caption is a good hook, that a person noticed it, or that it caused an outcome. Captions can use creative techniques these simple rules do not recognize.

## Synthetic example: URLs to a test decision

The following values are invented to illustrate the workflow; they are not scraped results or performance findings.

Input file `saved_posts.csv`:

```csv
url
https://www.tiktok.com/@samplebrand/video/7000000000000000001
https://www.tiktok.com/@samplecreator/video/7000000000000000002
https://www.tiktok.com/@sampledemo/video/7000000000000000003
```

After a live collection, imagine 12 returned captions from a marketer's manually selected sample produce these JSON summary rows:

```json
{
  "sample_size": 12,
  "pattern_summary": [
    {"pattern": "first_person_opening_cue", "post_count": 5, "share_of_sample": 0.417},
    {"pattern": "question_mark_cue", "post_count": 4, "share_of_sample": 0.333},
    {"pattern": "contrast_phrase_cue", "post_count": 3, "share_of_sample": 0.25}
  ],
  "experiment_briefs": [
    {
      "pattern": "first_person_opening_cue",
      "hypothesis": "Test whether an opening first-person phrase helps this creative communicate its premise.",
      "human_review_required": true
    }
  ],
  "caveat": "Caption-only pattern extraction; does not inspect the video, establish causality, or identify a winning creative."
}
```

A reasonable human decision is: “We have seen first-person openings in five of these 12 examples. For our next campaign, should we test one first-person opening against a non-first-person version while keeping the offer and delivery conditions as consistent as practical?” The marketer writes and reviews those variants, chooses the primary success metric before launch, and measures results in their ad platform. **The 5/12 count is not evidence that first-person captions perform better.** It only helps turn a pile of examples into a specific test question.

## Start without an API call

Requirements: Python 3.10 or newer. Runtime code uses the standard library; pytest is only needed for development tests. No API key is needed for the bundled local sample or a dry run.

Analyze bundled sample records and write JSON or CSV:

```bash
python3 patterns.py sample_posts.json creative_patterns.json
python3 patterns.py sample_posts.json creative_patterns.csv
```

Validate a URL CSV without making a network request:

```bash
python3 patterns.py saved_posts.csv patterns.json --live --dry-run
```

`--dry-run` prints the number of validated URLs and confirms that zero requests were made. It does not fetch captions or write an analysis report.

## Run with live TikTok data

Live collection requires internet access, a Bright Data API token, and access to the TikTok Posts dataset. The key must be present in the process environment as `BRIGHT_DATA_API_KEY`. The repository's `.env.example` is a template; the CLI does **not** read `.env` automatically.

Linux/macOS:

```bash
export BRIGHT_DATA_API_KEY="your-key"
python3 patterns.py saved_posts.csv patterns.json --live
```

PowerShell:

```powershell
$env:BRIGHT_DATA_API_KEY = "your-key"
python patterns.py saved_posts.csv patterns.json --live
```

Use public TikTok video URLs in a CSV with a `url` column. A live call may incur Bright Data charges. The synchronous request is limited to 20 URLs; the tool validates canonical public video URLs and reports asynchronous snapshot responses as unsupported rather than silently changing collection modes. Check current [Web Scraper pricing](https://brightdata.com/pricing/web-scraper) and your Bright Data account before collecting.

## Output files

JSON is the default format. It includes:

- `sample_size`: number of records analyzed.
- `pattern_summary`: count and share of the sample for each cue found at least once. Shares use all analyzed records as the denominator; cues can overlap, so shares do not add to 100%.
- `observations`: one record per post, with evidence URL, caption, posting time when available, matched cues, returned counters, and a literal-rule interpretation label.
- `experiment_briefs`: a hypothesis and suggested single-cue comparison for each observed cue, with human-review and causal limitations.
- `caveat`: an explicit statement of the analysis boundary.

To write a per-post CSV instead, use a `.csv` output path:

```bash
python3 patterns.py sample_posts.json creative_patterns.csv
```

CSV has one row per observed post, with cue labels, returned `play_count`, `collect_count`, `comment_count`, and `share_count` when supplied, plus related hypothesis text. The aggregate summary and full caveat are JSON-only. Counter fields are passed through only when present and valid; the script does not rename them to generic “views” or “likes.” CSV text that could be interpreted as a spreadsheet formula is prefixed for safety.

## What this is not

- **Not trend discovery:** you provide the URLs; the tool does not search TikTok or decide which posts are relevant.
- **Not video or audio analysis:** it reads returned post text and selected fields only. It does not download, watch, transcribe, or inspect media, editing, on-screen text, or sound.
- **Not performance analysis:** it does not compare creative outcomes, normalize counters by exposure or time, or identify winners. Returned public counters are not controlled ad-delivery measurements.
- **Not a semantic classifier:** literal regex rules can miss paraphrases and can match a phrase without understanding its meaning.
- **Not an automatic test generator:** it supplies hypotheses and evaluation guidance. A marketer must draft variants, review them, run the experiment elsewhere, and interpret its results.

## Relationship to other TikTok tools

This repository is a caption-cue inventory for a curated set of posts. It is different from [`bright-data-tiktok-scraper`](https://github.com/yaronbeen/bright-data-tiktok-scraper), a general-purpose TikTok profiles/posts/comments data scraper, and [`bright-data-tiktok-outreach`](https://github.com/yaronbeen/bright-data-tiktok-outreach), a creator/profile contact workflow. It is also not the [TikTok buyer-intent finder skill](https://github.com/yaronbeen/brightdata-mcp-tiktok-buyer-intent-finder), which looks for public buyer-intent signals in comments and drafts replies for human review.

## Data, safety, and troubleshooting

Use public URLs for research and follow TikTok's terms, applicable law, and your organization's privacy and retention requirements. The tool does not log in, evade access controls, contact people, or publish content. Public visibility alone is not authorization for every downstream use.

- Missing API key: local sample analysis and `--dry-run` do not need one; live collection does.
- URL-only CSV without `--live`: rejected without making a request. Add `--live` only when you intend a live collection that may incur charges.
- HTTP 401/403: check the token and TikTok dataset permissions.
- HTTP 429: pause and reduce volume; this script does not implement an automatic rapid retry loop.
- No cue matches: no literal rule matched. This does not mean the captions contain no creative technique.
- Missing counters: the dataset may not have returned them. Their absence is not zero performance.

## Tests

Run the offline test suite (mocked network interactions; no Bright Data request):

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

The tests cover cue matching and aggregation, documented counter fields, URL validation, explicit live opt-in, mocked request shape, CSV output and formula safety, and error cases. Fixtures and the example above are illustrative, not claims about real campaign performance.

## License

MIT
