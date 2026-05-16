"""
PhD Tracker Scraper — run from repo root: python scraper/scrape.py
Sources: EURAXESS, jobs.ac.uk
Note: academicpositions.com & findaphd.com are Cloudflare-blocked
"""

import json, re, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "data.json"

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

def scrape_eui(page):
    print("\n→ EUI Florence")
    results = []

    try:
        page.goto("https://www.eui.eu/apply", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # Dismiss cookie banner if present
        try:
            page.click("text=Decline Non Essential", timeout=3000)
        except: pass

        # Find all doctoral programme links
        prog_links = page.evaluate('''() =>
            [...document.querySelectorAll("a")]
            .filter(a => a.href.includes("apply?id=doctoral") || a.href.includes("apply?id=marie"))
            .map(a => ({text: a.innerText.trim(), href: a.href}))
        ''')

        relevant_ids = [
            "doctoral-programme-in-political-and-social-sciences",
            "doctoral-programme-in-law",
            "doctoral-programme-in-history-and-civilisation",
        ]

        for prog in prog_links:
            href = prog['href']
            prog_id = href.split("id=")[-1] if "id=" in href else ""
            if not any(r in prog_id for r in relevant_ids):
                continue

            try:
                page.goto(href, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2000)

                body = page.inner_text("body")

                # Extract deadline
                deadline = ""
                import re
                dl_match = re.search(r'deadline[^\n]*?(\d{1,2}\s+\w+\s+\d{4})', body, re.IGNORECASE)
                if dl_match:
                    deadline = dl_match.group(1)
                else:
                    dl_match2 = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', body)
                    if dl_match2:
                        deadline = dl_match2.group(1)

                # Extract start date
                start_match = re.search(r'Programme Start Date\s*\n\s*(\S[^\n]+)', body)
                start = start_match.group(1).strip() if start_match else ""

                # Get description snippet
                desc_match = re.search(r'Programme Description\s*\n(.{100,400})', body, re.DOTALL)
                desc = desc_match.group(1).strip()[:300] if desc_match else ""

                title = prog['text'].strip() or f"EUI {prog_id.replace('-',' ').title()}"

                results.append(entry(
                    title, href,
                    institution="European University Institute (EUI)",
                    location="Florence, Italy",
                    deadline=deadline or (f"Starts {start}" if start else ""),
                    description=desc,
                    source="EUI Florence"
                ))
                time.sleep(1)

            except Exception as e:
                print(f"  ✗ {prog_id}: {e}")

    except Exception as e:
        print(f"  ✗ {e}")

    print(f"  → {len(results)} programmes")
    return results


# ── Bocconi University ────────────────────────────────────────────────────────

def scrape_bocconi(page):
    print("\n→ Bocconi University")
    results = []

    relevant = [
        ("PhD in Social and Political Science", "https://www.unibocconi.it/en/programs/phd/phd-social-and-political-science"),
        ("PhD in Legal Studies", "https://www.unibocconi.it/en/programs/phd/phd-legal-studies"),
        ("PhD in Economics and Finance", "https://www.unibocconi.it/en/programs/phd/phd-economics-and-finance"),
    ]

    # Also get admissions page for deadline
    deadline_global = ""
    try:
        page.goto("https://www.unibocconi.it/en/programs/phd/admissions", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        body = page.inner_text("body")
        import re
        dl = re.search(r'(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})', body)
        if dl:
            deadline_global = dl.group(1)
    except: pass

    for title, url in relevant:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            body = page.inner_text("body")

            # Extract key info
            import re
            desc_match = re.search(r'(Four-year|Three-year|PhD Program|At a glance)(.{200,500})', body, re.DOTALL)
            desc = desc_match.group(0).strip()[:300] if desc_match else ""

            results.append(entry(
                title, url,
                institution="Bocconi University",
                location="Milan, Italy",
                deadline=deadline_global,
                description=desc,
                source="Bocconi University"
            ))
            time.sleep(1)

        except Exception as e:
            print(f"  ✗ {title}: {e}")

    print(f"  → {len(results)} programmes")
    return results


# ── LUISS Rome ────────────────────────────────────────────────────────────────

def scrape_luiss(page):
    print("\n→ LUISS Rome")
    results = []

    try:
        page.goto("https://phd.luiss.it/phd-programs/", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)

        # Get all programme links
        prog_links = page.evaluate('''() =>
            [...document.querySelectorAll("a")]
            .filter(a => a.href.includes("phd.luiss.it") && a.href.length > 30 &&
                !["phd-programs","open-calls","ammissione","procedure","services",
                  "contact","informazioni","faq","external"].some(x => a.href.includes(x)) &&
                a.innerText.trim().length > 4)
            .map(a => ({text: a.innerText.trim(), href: a.href}))
        ''')

        # Also check open calls
        page.goto("https://phd.luiss.it/open-calls/", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        open_calls_text = page.inner_text("body")

        import re
        has_open = "no open calls" not in open_calls_text.lower()
        call_links = []
        if has_open:
            call_links = page.evaluate('''() =>
                [...document.querySelectorAll(".entry-content a, article a, main a")]
                .map(a => ({text: a.innerText.trim(), href: a.href}))
                .filter(l => l.href.includes("luiss") && l.text.length > 5)
            ''')

        relevant_progs = ["politics", "law", "political", "international", "economics", "government"]

        # Create entries for relevant programmes
        seen = set()
        for prog in (prog_links + call_links):
            text = prog['text'].lower()
            href = prog['href']
            if href in seen: continue
            if not any(k in text or k in href.lower() for k in relevant_progs): continue
            seen.add(href)

            results.append(entry(
                prog['text'], href,
                institution="LUISS Guido Carli",
                location="Rome, Italy",
                deadline="See open calls" if has_open else "No open calls currently",
                source="LUISS Rome"
            ))

    except Exception as e:
        print(f"  ✗ {e}")

    # Always add LUISS Politics programme as a standing entry
    if not any("politics" in r['title'].lower() for r in results):
        results.append(entry(
            "PhD in Politics",
            "https://phd.luiss.it/phd-programs/",
            institution="LUISS Guido Carli",
            location="Rome, Italy",
            deadline="Check site for open calls",
            description="PhD in Politics at LUISS Rome. Research areas: comparative politics, international relations, EU politics.",
            source="LUISS Rome"
        ))

    print(f"  → {len(results)} programmes")
    return results


# ── Bologna University ────────────────────────────────────────────────────────

def scrape_bologna(page):
    print("\n→ University of Bologna")
    results = []

    RELEVANT_KEYWORDS = [
        "political", "international", "law", "governance",
        "european", "global", "society", "social", "history",
        "economics", "migration", "peace", "conflict",
    ]

    # Bologna lists all PhD programmes - find the current cycle page
    urls_to_try = [
        "https://www.unibo.it/en/study/phd-professional-masters-specialisation-schools-and-other-programmes/phd/phd-programmes-2025-26",
        "https://www.unibo.it/en/study/phd-professional-masters-specialisation-schools-and-other-programmes/phd/phd-programmes-2024-25",
    ]

    for list_url in urls_to_try:
        try:
            page.goto(list_url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000)

            # Accept cookies if needed
            try:
                page.click("text=Accept All", timeout=2000)
                page.wait_for_timeout(1000)
            except: pass

            prog_links = page.evaluate('''() =>
                [...document.querySelectorAll("a")]
                .filter(a => a.href.includes("unibo.it") &&
                    (a.href.includes("phd-programme") || a.href.includes("dottorat")) &&
                    a.innerText.trim().length > 5)
                .map(a => ({text: a.innerText.trim(), href: a.href}))
            ''')

            if not prog_links:
                continue

            print(f"  Found {len(prog_links)} programmes at {list_url}")

            import re
            for prog in prog_links:
                text_lower = prog['text'].lower()
                if not any(k in text_lower for k in RELEVANT_KEYWORDS):
                    continue

                results.append(entry(
                    prog['text'], prog['href'],
                    institution="University of Bologna",
                    location="Bologna, Italy",
                    source="University of Bologna"
                ))

            if results:
                break

        except Exception as e:
            print(f"  ✗ {list_url}: {e}")

    if not results:
        # Fallback: add known relevant PhD programmes
        known = [
            ("PhD in Political and Social Sciences", "https://www.unibo.it/en/study/phd-professional-masters-specialisation-schools-and-other-programmes/phd"),
            ("PhD in International Studies", "https://www.unibo.it/en/study/phd-professional-masters-specialisation-schools-and-other-programmes/phd"),
        ]
        for title, url in known:
            results.append(entry(title, url, institution="University of Bologna", location="Bologna, Italy", source="University of Bologna"))

    print(f"  → {len(results)} relevant programmes")
    return results

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

            for fn in [scrape_euraxess, scrape_jobsacuk, scrape_eui, scrape_bocconi, scrape_luiss, scrape_bologna]:
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


# ── EUI Florence ──────────────────────────────────────────────────────────────
# Scrapes the EUI apply page for doctoral programmes


if __name__ == "__main__":
    main()
