"""Describe caption-level creative cues as hypotheses, never performance causes."""
import argparse, csv, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

DATASET = "gd_lu702nij2f790tmv9h"
FIELDS = ["evidence_url", "caption", "posted_at", "patterns", "play_count", "collect_count", "comment_count", "share_count", "interpretation"]
RULES = {"first_person_opening_cue": (r"^\s*(i|my|we|our)\b",), "question_mark_cue": (r"\?",), "contrast_phrase_cue": (r"\b(before and after|before/after|but then|until i)\b",), "numbered_list_phrase_cue": (r"\b\d+\s+(ways|tips|things|steps)\b",), "cta_phrase_cue": (r"\b(shop now|link in bio|follow for|comment below|try it)\b",)}
HYPOTHESES = {"first_person_opening_cue": "Test whether an opening first-person phrase helps this creative communicate its premise.", "question_mark_cue": "Test whether a question-mark caption changes attention to the stated problem.", "contrast_phrase_cue": "Test whether explicit contrast language clarifies the promised change.", "numbered_list_phrase_cue": "Test whether a numbered-list phrase improves scannability.", "cta_phrase_cue": "Test whether an explicit CTA phrase clarifies the next action."}

def csv_safe(value):
    if isinstance(value, str) and value.lstrip(" \t\r\n\x00").startswith(("=", "+", "-", "@")): return "'" + value
    return value

def metric_value(value, field):
    if value is None or value == "": return None
    if isinstance(value, bool): raise ValueError(field + " must be a non-negative integer")
    try: number=int(value)
    except (TypeError,ValueError): raise ValueError(field + " must be a non-negative integer") from None
    if str(number) != str(value).strip() or number < 0: raise ValueError(field + " must be a non-negative integer")
    return number

def analyze(raw):
    if not isinstance(raw,dict): raise ValueError("each TikTok post record must be an object")
    caption=str(raw.get("description") or raw.get("caption") or "")
    text=caption.lower()
    found=[name for name, patterns in RULES.items() if any(re.search(pattern,text) for pattern in patterns)]
    counters={field:metric_value(raw.get(field),field) for field in ("play_count","collect_count","comment_count","share_count")}
    return {"evidence_url":raw.get("url") or "", "caption":caption, "posted_at":raw.get("create_time") or raw.get("date_posted") or None, "patterns":found, **counters, "interpretation":"literal_caption_cues_for_human_review_not_semantic_or_causal_findings"}

def validate_video_url(url):
    try:
        parsed=urlsplit(url); host=parsed.hostname; port=parsed.port
    except (TypeError,ValueError):
        raise ValueError("URL must be a canonical public TikTok video URL") from None
    if parsed.scheme!="https" or host not in {"tiktok.com","www.tiktok.com"} or parsed.username or parsed.password or port not in {None,443} or not re.fullmatch(r"/@[^/]+/video/\d+/?",parsed.path):
        raise ValueError("URL must be a canonical public TikTok video URL")
    return url

def write_csv(path, rows):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        fields=FIELDS + ["experiment_hypotheses"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows:
            safe={key:csv_safe(value) for key,value in row.items()}
            safe.update({"patterns":";".join(row["patterns"]),"experiment_hypotheses":";".join(HYPOTHESES[item] for item in row["patterns"])})
            w.writerow(safe)


def build_report(records):
    observations = [analyze(row) for row in records]
    counts = {name: sum(name in row["patterns"] for row in observations) for name in RULES}
    summary = [{"pattern": name, "post_count": count, "share_of_sample": round(count / len(observations), 3) if observations else 0} for name, count in counts.items() if count]
    summary.sort(key=lambda row: (-row["post_count"], row["pattern"]))
    briefs = [{"pattern": row["pattern"], "hypothesis": HYPOTHESES[row["pattern"]], "test_design": "Compare two creative variants while holding offer, audience, spend, length, and placement as constant as practical; vary only this format cue.", "evaluation_guidance": "Choose a platform-measured primary metric before the test and compare equivalent delivery windows.", "human_review_required": True, "limitation": "This observed public sample is descriptive, not causal; validate the idea with a controlled test. No performance winner is inferred."} for row in summary]
    return {"sample_size": len(observations), "pattern_summary": summary, "observations": observations, "experiment_briefs": briefs, "caveat": "Caption-only pattern extraction; does not inspect the video, establish causality, or identify a winning creative."}

def collect(urls, token):
    if len(urls) > 20: raise ValueError("Synchronous TikTok collection supports at most 20 URLs")
    urls=[validate_video_url(url) for url in urls]
    if not token: raise ValueError("Set BRIGHT_DATA_API_KEY for live collection")
    req=Request("https://api.brightdata.com/datasets/v3/scrape?"+urlencode({"dataset_id":DATASET,"format":"json"}),data=json.dumps({"input":[{"url":u} for u in urls]}).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=90) as r: data=json.loads(r.read())
    except HTTPError as e: raise RuntimeError("Bright Data returned HTTP "+str(e.code)) from None
    except (URLError,TimeoutError) as e: raise RuntimeError("Bright Data request failed: "+str(e)) from None
    if not isinstance(data,list): raise RuntimeError("This demo supports synchronous post URL results, not async snapshots")
    return data

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",help="JSON records or CSV with public TikTok video URLs"); p.add_argument("output",nargs="?",default="creative_patterns.json"); p.add_argument("--live",action="store_true",help="Explicitly collect the supplied public video URLs (may incur charges)"); p.add_argument("--dry-run",action="store_true"); a=p.parse_args(argv)
    try:
        text=Path(a.input).read_text(encoding="utf-8"); rows=json.loads(text) if a.input.endswith(".json") else list(csv.DictReader(text.splitlines()))
        if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows): raise ValueError("input must be an array or record CSV")
        record_fields={"description","caption","create_time","date_posted","play_count","collect_count","comment_count","share_count"}
        url_only=bool(rows) and "url" in rows[0] and not any(record_fields.intersection(row) for row in rows)
        if a.live:
            if not rows: raise ValueError("live collection requires at least one public TikTok video URL")
            urls=[validate_video_url(str(row.get("url") or "").strip()) for row in rows]
            if a.dry_run: print(f"Dry run: {len(urls)} TikTok URL(s); 0 requests made"); return 0
            rows=collect(urls,os.getenv("BRIGHT_DATA_API_KEY"))
        elif url_only: raise ValueError("URL-only input is not collected automatically; pass --live to explicitly request billable collection")
        elif a.dry_run: print(f"Dry run: {len(rows)} local record(s); 0 requests made"); return 0
        report=build_report(rows)
        if a.output.endswith(".csv"): write_csv(a.output,report["observations"])
        else: Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"Analyzed {report['sample_size']} posts across {len(report['pattern_summary'])} patterns; wrote {a.output}"); return 0
    except (ValueError,OSError,RuntimeError,json.JSONDecodeError) as e: print("Error: "+str(e),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
