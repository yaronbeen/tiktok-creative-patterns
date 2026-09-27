"""Describe caption-level creative cues as hypotheses, never performance causes."""
import argparse, csv, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "gd_lu702nij2f790tmv9h"
FIELDS = ["evidence_url", "caption", "posted_at", "patterns", "play_count", "collect_count", "comment_count", "share_count", "interpretation"]
RULES = {"first_person_hook": (r"\b(i|my)\b",), "question_hook": (r"\?",), "contrast_hook": (r"\b(before and after|before/after|but then|until i)\b",), "numbered_list": (r"\b\d+\s+(ways|tips|things|steps)\b",), "explicit_cta": (r"\b(shop now|link in bio|follow for|comment below|try it)\b",)}

def analyze(raw):
    caption=str(raw.get("description") or raw.get("caption") or "")
    text=caption.lower()
    found=[name for name, patterns in RULES.items() if any(re.search(pattern,text) for pattern in patterns)]
    return {"evidence_url":raw.get("url") or "", "caption":caption, "posted_at":raw.get("create_time") or raw.get("date_posted") or None, "patterns":found, "play_count":raw.get("play_count"), "collect_count":raw.get("collect_count"), "comment_count":raw.get("comment_count"), "share_count":raw.get("share_count"), "interpretation":"observable_caption_hypotheses_not_causal_findings"}

def write_csv(path, rows):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
        for row in rows: w.writerow({**row,"patterns":";".join(row["patterns"])})

def collect(urls, token):
    if len(urls) > 20: raise ValueError("Synchronous TikTok collection supports at most 20 URLs")
    if not token: raise ValueError("Set BRIGHT_DATA_API_KEY for live collection")
    req=Request("https://api.brightdata.com/datasets/v3/scrape?"+urlencode({"dataset_id":DATASET,"format":"json"}),data=json.dumps([{"url":u} for u in urls]).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=90) as r: data=json.loads(r.read())
    except HTTPError as e: raise RuntimeError("Bright Data returned HTTP "+str(e.code)) from None
    except (URLError,TimeoutError) as e: raise RuntimeError("Bright Data request failed: "+str(e)) from None
    if not isinstance(data,list): raise RuntimeError("This demo supports synchronous post URL results, not async snapshots")
    return data

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("input",help="JSON records or CSV with public TikTok video URLs"); p.add_argument("output",nargs="?",default="creative_patterns.json"); p.add_argument("--dry-run",action="store_true"); a=p.parse_args(argv)
    try:
        text=Path(a.input).read_text(encoding="utf-8"); rows=json.loads(text) if a.input.endswith(".json") else list(csv.DictReader(text.splitlines()))
        if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows): raise ValueError("input must be an array or record CSV")
        live=bool(rows) and "url" in rows[0] and not any("description" in r or "caption" in r for r in rows)
        urls=[str(r.get("url") or "").strip() for r in rows] if live else []
        if live and any(not u.startswith("https://www.tiktok.com/") for u in urls): raise ValueError("Every row must contain a public TikTok video URL beginning https://www.tiktok.com/")
        if a.dry_run: print(f"Dry run: {len(rows)} inputs; 0 requests made"); return 0
        if live: rows=collect(urls,os.getenv("BRIGHT_DATA_API_KEY"))
        out=[analyze(r) for r in rows]
        if a.output.endswith(".csv"): write_csv(a.output,out)
        else: Path(a.output).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"Wrote {len(out)} observations to {a.output}"); return 0
    except (ValueError,OSError,RuntimeError,json.JSONDecodeError) as e: print("Error: "+str(e),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
