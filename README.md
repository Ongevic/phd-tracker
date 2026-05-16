# 🎓 PhD Tracker — Political Science & IR in Europe

Automatically scrapes and lists PhD positions in **Political Science, International Relations, European Studies, and Global Governance** across Italy and Europe.

**Live site:** `https://YOUR-USERNAME.github.io/phd-tracker/`

Updated every day at 6am UTC via GitHub Actions.

---

## Sources

| Source | Fields covered |
|---|---|
| [EURAXESS](https://euraxess.ec.europa.eu/jobs/search) | Political Sciences, European Studies, Governance, International Law |
| [Academic Positions](https://academicpositions.com) | Political Science, International Relations, Social Science |
| [jobs.ac.uk](https://www.jobs.ac.uk) | Politics & Government PhDs |

---

## Setup (5 minutes)

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR-USERNAME/phd-tracker.git
cd phd-tracker
```

### 2. Enable GitHub Pages

Go to your repo → **Settings → Pages**
- Source: **GitHub Actions**

### 3. Enable GitHub Actions

Go to **Actions** tab → click **Enable Actions**

The workflow will run automatically:
- Every day at 6am UTC
- On every push to `main`
- Manually via the **Run workflow** button

### 4. Run locally (optional)

```bash
pip install playwright
playwright install chromium
cd scraper
python scrape.py
```

Then open `docs/index.html` in your browser.

---

## Project Structure

```
phd-tracker/
├── .github/
│   └── workflows/
│       └── scrape-and-deploy.yml   # Daily scrape + GitHub Pages deploy
├── scraper/
│   └── scrape.py                   # Playwright scraper
├── data/
│   └── positions.json              # Auto-updated by scraper
├── docs/
│   └── index.html                  # The website (served by GitHub Pages)
└── README.md
```

---

## Customisation

**Add keywords** — edit `KEYWORDS` list in `scraper/scrape.py`

**Add countries** — edit `TARGET_COUNTRIES` list in `scraper/scrape.py`

**Change scrape schedule** — edit the `cron` line in `.github/workflows/scrape-and-deploy.yml`

---

Made with ❤️ for academic job hunting.
