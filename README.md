# Lindholmen Lunch

Lunch menus from Lindholmen, Gothenburg. The page is static HTML, regenerated on weekday mornings and published from `docs/` with GitHub Pages.

Live site: https://iamjaydesign.com/lindholmen-lunch

Based on work by [Fawenah](https://github.com/Fawenah/lindholmen_lunch).

## What it does

- Scrapes the weekday lunch menus and renders one page.
- Swedish and English, remembered in the browser.
- Pick a dish from the menus that match the current filters and search.
- Links to each restaurant's website and map.

Restaurants: Kooperativet, District One, Bombay Bistro, Cuckoo's Nest, Uni3 World of Food, Miss F, Benne Pastabar, LS Kitchen, Bistrot, Mimolett, Oishii, Mat & Minnen, Encounter Asian, Masala, Pier 11.

## Schedule

GitHub Actions runs four times each weekday (Monday–Friday). The times below are Europe/Stockholm. The 10:37 run only retries restaurants that were missing, stale or the wrong week.

| Cron (UTC) | Winter (CET) | Summer (CEST) |
|---|---|---|
| `7 5 * * 1-5` | 06:07 | 07:07 |
| `37 6 * * 1-5` | 07:37 | 08:37 |
| `7 8 * * 1-5` | 09:07 | 10:07 |
| `37 9 * * 1-5` | 10:37 | 11:37 |

The workflow is `.github/workflows/update-and-deploy.yml`. It scrapes, renders `docs/`, and pushes the page. Mat & Minnen is hidden. Mimolett is a link to its Kvartersmenyn page.

## Local setup

Python 3.12 and Chrome (the two JavaScript menus use Selenium).

```bash
git clone https://github.com/designestjay/lindholmen-lunch.git
cd lindholmen-lunch
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Render the page from the saved Friday data:

```bash
python generate_html.py --day friday
```

Serve it:

```bash
cd docs
python -m http.server 8000
```

Then open http://127.0.0.1:8000/

## Tests

Offline tests skip anything that hits a restaurant site:

```bash
python -m pytest -q
```

Opt in to the live scraper tests:

```bash
RUN_NETWORK=1 python -m pytest -q -m network
```

Headless Chrome checks the pick dock and the weekend state:

```bash
python -m pytest -q -m browser
```

## Contact

support@jaydigitalstudio.com
