"""
PhD Tracker Scraper — run from repo root: python scraper/scrape.py
Sources: EURAXESS, jobs.ac.uk
Note: academicpositions.com & findaphd.com are Cloudflare-blocked
"""

import json, re, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "data" / "positions.json"

KEYWORDS = [
    "political science","international relations","global governance",
    "european studies","european politics","comparative politics",
    "world politics","foreign policy","peace studies","security studies",
    "public policy","political economy","diplomacy","geopolitics",
    "human rights","migration","conflict","peacebuilding","democracy",
    "elections","parliament","nato","united nations","multilateral",
    "international organization","political theory","area studies",
    "eu politics","transatlantic","development studies",
]

EUROPEAN = [
    "italy","france","germany","netherlands","spain","belgium","sweden",
    "denmark","norway","austria","switzerland","finland","portugal",
    "ireland","czech","poland","hungary","greece","luxembourg","estonia",
    "latvia","lithuania","slovakia","slovenia","croatia","romania",
    "bulgaria","europe","european","bologna","milan","rome","florence",
    "pavia","naples","turin","venice","padova","trento","trieste",
    "london","oxford","cambridge","edinburgh","amsterdam","berlin",
    "paris","madrid","vienna","brussels","copenhagen","stockholm",
    "oslo","helsinki","lisbon","warsaw","budapest","prague","odense",
    "uk","united kingdom","england","scotland","wales","ireland",
]

def is_relevant(title, desc=""):
    t = f"{title} {desc}".lower()
    return any(k in t for k in KEYWORDS)

def is_european(loc):
    if not loc:
        return True  # if no location info, include by default
    l = loc.lower()
    return any(c in l for c in EUROPEAN)

def clean(t):
    return re.sub(r'\s+', ' ', (t or "").strip())

def entry(title, url, **kw):
    return {
        "title": clean(title), "url": url or "",
        "location": clean(kw.get("location","")),
        "institution": clean(kw.get("institution","")),
        "deadline": clean(kw.get("deadline","")),
        "description": clean(kw.get("description",""))[:350],
        "source": kw.get("source",""),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }

# ── EURAXESS ──────────────────────────────────────────────────────────────────

def scrape_euraxess(page):
    print("\n→ EURAXESS")
    results = []
    search_terms = [
        "political+science", "international+relations",
        "european+studies", "global+governance",
        "comparative+politics", "foreign+policy",
        "political+theory", "development+studies",
    ]
    seen = set()

    for term in search_terms:
        # No researcher_profile filter — it returns 0 results
        url = f"https://euraxess.ec.europa.eu/jobs/search?keywords={term}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(4000)

            cards = page.query_selector_all("article.ecl-content-item")
            print(f"  '{term}': {len(cards)} cards")

            for card in cards:
                try:
                    title_el = card.query_selector(".ecl-content-block__title a")
                    if not title_el:
                        continue
                    title = clean(title_el.inner_text())
                    href = title_el.get_attribute("href") or ""
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    link = href if href.startswith("http") else "https://euraxess.ec.europa.eu" + href

                    desc_el = card.query_selector(".ecl-content-block__description")
                    desc = clean(desc_el.inner_text()) if desc_el else ""

                    loc_el = card.query_selector(".id-Work-Locations .ecl-text-standard")
                    loc_raw = clean(loc_el.inner_text()) if loc_el else ""
                    # "Number of offers: 1, Italy, Institution Name, City" -> "Italy"
                    loc = re.sub(r'Number of offers:\s*\d+,\s*', '', loc_raw).strip()
                    loc = loc.split(',')[0].strip() if ',' in loc else loc

                    # Deadline from secondary meta
                    deadline = ""
                    for item in card.query_selector_all(".ecl-content-block__secondary-meta-item"):
                        t = item.inner_text()
                        if "deadline" in t.lower():
                            deadline = clean(t)
                            break

                    if not is_relevant(title, desc):
                        continue
                    if not is_european(loc):
                        continue

                    results.append(entry(title, link, location=loc,
                                        deadline=deadline, description=desc,
                                        source="EURAXESS"))
                except:
                    continue
            time.sleep(2)
        except Exception as e:
            print(f"  ✗ {term}: {e}")

    print(f"  → {len(results)} relevant")
    return results

# ── jobs.ac.uk ────────────────────────────────────────────────────────────────

def scrape_jobsacuk(page):
    print("\n→ jobs.ac.uk")
    results = []
    urls = [
        "https://www.jobs.ac.uk/search/politics-and-government/phd",
        "https://www.jobs.ac.uk/search/?keywords=phd+political+science&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+international+relations&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+european+studies&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+global+governance&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+foreign+policy&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+security+studies&type%5B%5D=PhD",
        "https://www.jobs.ac.uk/search/?keywords=phd+development+studies&type%5B%5D=PhD",
    ]
    seen = set()

    for url in urls:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3000)
            cards = page.query_selector_all(".j-search-result__result")
            label = url.split("=")[-1][:25] if "?" in url else url.split("/")[-1]
            print(f"  '{label}': {len(cards)} cards")

            for card in cards:
                try:
                    title_el = card.query_selector(".j-search-result__text a")
                    if not title_el:
                        continue
                    title = clean(title_el.inner_text())
                    href = title_el.get_attribute("href") or ""
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    link = "https://www.jobs.ac.uk" + href if not href.startswith("http") else href

                    emp_el = card.query_selector(".j-search-result__employer b")
                    institution = clean(emp_el.inner_text()) if emp_el else ""

                    loc = ""
                    for div in card.query_selector_all("div"):
                        t = div.inner_text().strip()
                        if t.startswith("Location:"):
                            loc = clean(t.replace("Location:", "").strip())
                            break

                    dl_el = card.query_selector(".j-search-result__date--blue")
                    closes_el = card.query_selector(".j-search-result__date-span.j-search-result__date")
                    deadline = ""
                    if dl_el:
                        prefix = clean(closes_el.inner_text()) if closes_el else "Closes"
                        deadline = f"{prefix} {clean(dl_el.inner_text())}"

                    if not is_relevant(title):
                        continue

                    results.append(entry(title, link, location=loc,
                                        institution=institution, deadline=deadline,
                                        source="jobs.ac.uk"))
                except:
                    continue
            time.sleep(1.5)
        except Exception as e:
            print(f"  ✗ {e}")

    print(f"  → {len(results)} relevant")
    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def dedupe(positions):
    seen, out = set(), []
    for p in positions:
        k = re.sub(r'\W+', '', p["title"].lower())[:60]
        if k and k not in seen:
            seen.add(k); out.append(p)
    return out

def main():
    print(f"PhD Tracker — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if OUTPUT_FILE.exists():
        try:
            existing = json.loads(OUTPUT_FILE.read_text()).get("positions", [])
            print(f"Existing: {len(existing)} positions")
        except: pass

    all_pos, errors = [], []

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True,
                args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"])
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width":1280,"height":900})
            pg = ctx.new_page()

            for fn in [scrape_euraxess, scrape_jobsacuk]:
                try:
                    all_pos += fn(pg)
                except Exception as e:
                    errors.append(f"{fn.__name__}: {e}")
                    traceback.print_exc()

            browser.close()
    except Exception as e:
        print(f"Playwright error: {e}")
        errors.append(str(e))

    if all_pos:
        all_pos = dedupe(all_pos)
        all_pos.sort(key=lambda x: x.get("deadline") or "zzz")
        print(f"\nFinal: {len(all_pos)} unique positions")
    else:
        print("Nothing scraped — keeping existing data")
        all_pos = existing

    out = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total": len(all_pos),
        "errors": errors,
        "positions": all_pos,
    }
    OUTPUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"✅ Saved {len(all_pos)} positions")
    sys.exit(0)

if __name__ == "__main__":
    main()
