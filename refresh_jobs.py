#!/usr/bin/env python3
"""Discover likely vacancy links from selected official Zimbabwe career portals.

This is intentionally conservative: it only follows links found on the configured
official portals, never invents a salary, email, or deadline, and labels scraped
items as requiring confirmation. A source page may block automated requests or
change its markup; manual review remains necessary.
"""
from __future__ import annotations
import json, re, hashlib, html, os, urllib.request, urllib.parse
from datetime import datetime, timezone, date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "jobs.json"
SOURCES = [
    {"name": "Public Service Commission", "key": "PSC", "url": "https://erecruitment.psc.gov.zw/", "category": "Government", "location": "Zimbabwe"},
    {"name": "ZINARA", "key": "ZINARA", "url": "https://careers.zinara.co.zw/", "category": "Revenue & Transport", "location": "Zimbabwe"},
    {"name": "City of Harare", "key": "City of Harare", "url": "https://hararecity.co.zw/careers", "category": "Local Government", "location": "Harare"},
]
KEYWORDS = re.compile(r"\b(job|jobs|vacanc(?:y|ies)|career|careers|recruit(?:ment|ing)?|apply|position|positions|tendered post)\b", re.I)
NAV_WORDS = re.compile(r"^(home|about|contact|login|log in|register|privacy|terms|read more|view all|careers?)$", re.I)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links=[]; self.current=None
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a": self.current={"href":dict(attrs).get("href", ""), "text":[]}
    def handle_data(self, data):
        if self.current is not None: self.current["text"].append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current is not None:
            self.links.append({"href":self.current["href"], "text":" ".join(" ".join(self.current["text"]).split())})
            self.current=None

def fetch(url: str) -> str:
    req=urllib.request.Request(url, headers={"User-Agent":"ZimJobsDailyVacancyIndexer/1.0 (+official-source-linking; contact site owner)", "Accept":"text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=20) as res:
        if res.status >= 400: raise RuntimeError(f"HTTP {res.status}")
        raw=res.read(3_000_000)
        charset=res.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

def main():
    data=json.loads(FEED.read_text(encoding="utf-8")) if FEED.exists() else {"jobs":[]}
    now=datetime.now(timezone.utc)
    today=date.today().isoformat()
    # Keep current curated jobs and drop only jobs whose explicit deadline has passed.
    jobs=[]
    for j in data.get("jobs", []):
        deadline=j.get("deadline", "")
        if deadline and re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline) and deadline < today:
            continue
        jobs.append(j)
    by_source_url={j.get("source", "") for j in jobs}
    discovered=[]; errors=[]
    for source in SOURCES:
        try:
            parser=Links(); parser.feed(fetch(source["url"]))
            base=urllib.parse.urlparse(source["url"])
            for a in parser.links:
                title=html.unescape(a["text"]).strip()
                href=urllib.parse.urljoin(source["url"], a["href"].strip())
                parsed=urllib.parse.urlparse(href)
                if not title or len(title)<5 or len(title)>140 or NAV_WORDS.fullmatch(title): continue
                if not KEYWORDS.search(title) and not KEYWORDS.search(parsed.path): continue
                if parsed.scheme not in ("http", "https") or parsed.netloc != base.netloc: continue
                if href.rstrip("/") == source["url"].rstrip("/") or href in by_source_url: continue
                # Skip fragments, query-only links, and obvious account/navigation endpoints.
                if parsed.path.rstrip("/") in ("", "/login", "/register", "/contact", "/about"): continue
                if any(word in parsed.path.lower() for word in ("login", "logout", "register", "privacy", "terms")): continue
                jid=hashlib.sha1(href.encode()).hexdigest()[:12]
                job={
                    "id":"auto-"+jid, "title":title, "employer":source["name"], "employerKey":source["key"],
                    "location":source["location"], "category":source["category"], "deadline":"",
                    "deadlineText":"Check official notice", "source":href, "sourceLabel":source["name"]+" official portal",
                    "status":"Auto-discovered · verify notice", "summary":"This link was discovered on an official employer portal. Confirm that it is a current vacancy, check eligibility and deadline, and follow the original notice before applying.",
                    "needsReview":True, "discoveredAt":now.isoformat()
                }
                if jid not in {x.get("id","").replace("auto-","") for x in jobs}:
                    discovered.append(job); by_source_url.add(href)
        except Exception as e:
            errors.append({"source":source["url"], "error":str(e)[:240]})
    # Deduplicate by source URL, then add newly discovered items. No fabricated fields.
    existing={j.get("source") for j in jobs}
    jobs.extend(j for j in discovered if j.get("source") not in existing)
    data={"updatedAt":now.isoformat(), "sources":[s["url"] for s in SOURCES], "lastRunErrors":errors, "jobs":jobs}
    FEED.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Saved {len(jobs)} jobs; discovered {len(discovered)} new links; source errors: {len(errors)}")
    for err in errors: print(f"WARN {err['source']}: {err['error']}")

if __name__ == "__main__": main()
