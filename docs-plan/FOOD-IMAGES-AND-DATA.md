# Food images and data: plan

Planner: Cloud Agent, 14 Nov 2026. Planning only: this document contains no app code.

This is the second plan doc. [`NEXT-UPDATE.md`](https://github.com/designestjay/lindholmen-lunch/pull/8) (PR #8) is being built by Grok 4.7 on another branch. Section 0 lists what overlaps and what must wait for that PR.

- **Part A** is a library of hairline dish illustrations, plus a classifier that maps every scraped dish to a generic category, so people who don't know a dish can see what it is and what's typically in it.
- **Part B** is a per-restaurant source audit and a reliability plan: correct sources, the right week, alerting, tests, polite scraping and a permission track.

Evidence labels used throughout:

- **[verified 14 Nov 2026]** means checked by fetching the page or reading the repo on that date.
- **[observed once]** means seen in a single snapshot. Treat it as a hint, not a schedule.
- **[UNVERIFIED]** means plausible but not checked. Someone must confirm it before relying on it.
- **[estimate]** means a number derived from our own history data, with the method stated.

No restaurant facts here are invented. Where a fact could not be checked, the doc says so.

---

## 0. Overlap with NEXT-UPDATE (PR #8, items B4–B6)

| PR #8 item | What it does | Overlap with this plan | Rule |
|---|---|---|---|
| **B4** `fetch_html()` in `scrapers/base.py`, timeouts, job and step `timeout-minutes` | One shared HTTP helper for all 12 `requests.get` scrapers | Part B's polite-scraping policy (B-6.4: honest user agent, robots.txt, conditional requests, per-host rate) **extends that same helper**. Note that B4 specifies a *desktop browser* UA; this plan recommends an *identifying* bot UA (see the Jay decision on the user agent). | **Wait for B4 to merge.** Then change the UA and add robots, crawl-delay and ETag handling inside `fetch_html()`. Do not add a second HTTP helper. |
| **B5** Fix Pier 11 (`.castit-day`) and District One, with fixtures `tests/fixtures/pier11.html` and `district_one.html` | Repairs two broken scrapers and adds the first offline tests | Part B recommends a **better District One source** (the restaurant's own public Google Sheet CSV that its site loads; see B-2 #2) and a **fixture and contract-test convention** for all scrapers (B-6.3). | **Wait for B5.** If B5 already ships the homepage parser, keep it as the fallback and add the CSV source on top. Reuse B5's fixture layout and move it into `tests/fixtures/<restaurant>/` only if the PR #8 layout makes that cheap. |
| **B6** `missing_reason` map (`http_<code>`, `timeout`, `error:<Exc>`, `empty`) in `scrape_meta`, plus a Reason column in the health summary | Explains why a restaurant is missing | Part B adds three more statuses (`wrong_week`, `closed`, `static`), per-restaurant GitHub issues, and per-weekday staleness rules (B-6.1, B-6.2). | **Wait for B6.** Extend its reason vocabulary; don't create a parallel one. |
| B2 (floating pick dock) and B7/B8 (template and visual changes) | Edits `templates/index.html` and `generate_html.py` | Part A's thumbnail and "What is it?" sheet touch the same dish-row markup and CSS. | **Wait for PR #8 to merge** before any UI work in Part A. The classifier and library data (A-2, A-3) don't touch the template and can be built at any time. |

**Can ship before PR #8 merges** (no file conflict with B4–B6, and each is a small, separate PR after Jay says yes):

1. **Remove the Mimolett link to the hijacked domain** (B-2 #10). This is a one-line edit in `data/restaurant_links.json`. The link currently sends users to a French gardening magazine, so it is urgent.
2. **Mark Mat & Minnen as closed** (B-2 #12). This needs Jay's decision.
3. **The Part A pilot**: generating six test illustrations in Krea (A-5). This happens outside the repo until approved.

---

# Part A: Dish illustration library

## A-1. Category taxonomy

**Principle:** dishes map to *generic, visually distinct* categories, never to an exact restaurant dish. For example, "Pho med kyckling", "Beef pho" and "Pho bo" all map to `pho`. A plant-based variant shares the picture when it looks the same: "Vegobullar med gräddsås" maps to `kottbullar`, and the variant is carried in text, not in the image.

### Size estimate from our own history [estimate]

Method:

- **Source:** every `data/lunch_data_*.json` file that a commit actually changed. That is 19 May – 19 Jun 2025 plus 13–14 Nov 2026: 883 dish entries, **755 unique dishes** after normalisation and **24,836 dish appearances**. Fixed menus repeat daily, so appearances are much higher than unique dishes.
- **Noise filtered out:** weekday headers, "stängt", "dessert", "tillval", prices and holiday greetings.
- **Classifier:** a 97-category prototype rule set (ordered keyword and regex rules over the dish name, then the description).

| Categories, ranked by unique-dish frequency | Coverage of unique dishes | Coverage of all appearances |
|---|---|---|
| Top 10 | 36% | n/a |
| Top 20 | 54% | 47% |
| Top 40 | 76% | 73% |
| Top 60 | 86% | 81% |
| Top 80 | 92% | 88% |
| All 97 (87 matched at least once) | 93% | 89% |

**Recommendation: about 115 categories at full build-out**, made of the 97 prototype categories plus about 18 identified gaps (below).

- **Seed the top 40 first.** That covers about three quarters of what a user sees.
- **Phase 2 adds categories up to 80**, which covers about 90%.

The remaining long tail is handled weekly (A-6).

**Caveat:** the history is biased. It is about five weeks of early summer 2025 plus one day in 2026, and some restaurants have changed since. Phase 0 therefore includes **a hand-labelled gold set of about 300 dishes** (A-2), and the ranking is recomputed after four weeks of live data.

### Proposed taxonomy (about 115 categories, slug order is not priority)

Observed counts (unique dishes matched in history) are in brackets. **(new)** marks a gap found in the unmatched 7%. **(anticipated)** marks a classic Swedish lunch dish that wasn't in our sample but is common at Gothenburg lunch restaurants. Anticipated categories are generated only once the classifier actually sees one.

**East and Southeast Asian (27):**

- **Noodles and soups:** `ramen` [4], `pho` [–], `noodle-soup` [2], `wonton` (new), `hot-pot` [–]
- **Rice and bowls:** `bibimbap` [6], `poke-bowl` [3], `fried-rice` [4], `bento` [–]
- **Japanese:** `sushi-mix` [30], `tempura` [1], `teriyaki` [4], `yakitori` [2]
- **Dumplings and buns:** `dumplings` [3], `bao` [6]
- **Fried noodles and stir-fries:** `yakisoba-fried-noodles` [12], `wok` [9]
- **Thai and Lao:** `thai-curry` [14], `pad-kra-pao` [1], `larb` [1]
- **Korean:** `korean-fried-chicken` [8], `korean-bbq` [6]
- **Other:** `spring-rolls` (new), `satay` (new), `curry-generic` [6], `tofu-dish` [3], `tempeh` (new)

**Indian (19):**

- **Curries:** `tikka-masala` [36], `butter-chicken` [8], `korma` [11], `vindaloo` [5], `madras-curry` [21], `saag-palak` [5], `paneer-curry` [3], `chana-masala` [3], `indian-curry` [16]
- **Dal and vegetables:** `dal` [4], `aloo-gobi` [2]
- **Grill and rice dishes:** `tandoori` [12], `biryani` [–], `kofta` [4], `thali` [1]
- **Breads and sides:** `naan` [10], `raita-chutney` [7], `samosa-pakora` (new)
- **Lamb:** `lamb-curry` (new; currently falls into `lamb` or `indian-curry`)

**Italian (12):**

- **Pasta:** `lasagne` [7], `carbonara` [4], `bolognese` [3], `pasta-pesto` [9], `pasta-tomato` [4], `pasta-cream` [33], `tortellini-gnocchi` [12], `risoni-orzo` (new)
- **Other:** `risotto` [9], `pizza` [2], `garlic-bread` [3], `arancini` (new)

**International mains (19):**

- **Fast food and street food:** `burger` [13], `taco-burrito` [11], `kebab` [3], `souvlaki-gyros` (new), `falafel` [5], `halloumi-dish` [3], `bbq-pulled` [2]
- **Fried and breaded:** `schnitzel` [15], `fish-and-chips` [2]
- **Bread and bakes:** `ciabatta-sandwich` [2], `wrap` (new), `quiche-pie` [–]
- **Stews:** `stew-bourguignon` [21], `moqueca-fish-stew` [3], `chili-con-carne` (new)
- **Roasts and grill:** `steak` [26], `chicken-roast` [11], `herb-lemon-chicken` (new), `pork-roast` [16], `lamb` [4], `duck` (new), `game-venison` (new), `grill-plate` (new)

**Swedish husman (24):**

- **Mince dishes:** `kottbullar` [10], `pannbiff` [7], `kottfarslimpa` (new), `kaldolmar` [2], `biff-rydberg` (anticipated)
- **Pork:** `stekt-flask` [–], `flasklagg` [2], `kassler` (new), `flaskpannkaka` (anticipated)
- **Potato dishes:** `raggmunk` [4], `pytt-i-panna` [2], `janssons` [–], `kroppkakor` (anticipated)
- **Stews and casseroles:** `kalops-skav` [2], `sjomansbiff` [–], `dillkott` (anticipated)
- **Sausage:** `korv-stroganoff` [1], `falukorv-stuvad-makaroner` (anticipated)
- **Soups and pancakes:** `arter-med-flask` [–], `pannkakor` (anticipated)
- **Fish dishes:** `fiskgratang` [11], `fish-patty` [–], `laxpudding` (anticipated)
- **Chicken:** `flygande-jacob` (anticipated)

**Fish and seafood (8):** `fried-fish` [16], `poached-fish` [19], `salmon` [18], `white-fish` [47], `shrimp` [8], `gravlax` [1], `mussels` (new), `fish-soup` (new)

**Salads (4):** `caesar-salad` [3], `chevre-salad` [4], `grain-salad` [4], `salad-bowl` [20]

**Soups (2):** `soup` [1] (generic), `tomato-soup` (new)

**Vegetarian and vegan (6):** `quorn-soy` [2], `roasted-cauliflower` [2], `roasted-vegetables` [9], `bean-lentil` [6], `omelette-egg` [1], `gratin-veg` [2]

**Sweet (2, optional):** `dessert-cake` (new), `pancake-dessert` (new). These depend on Jay's decision to show desserts at all; today the scrapers mostly drop them.

That totals about 123 slugs, of which about 105–115 are expected to see real use. Ten anticipated Swedish categories stay unused until they appear.

### Explicitly not categories

The classifier must recognise these and return `null`, with no queue entry and no image:

- **Drinks and add-ons:** "dryck", "läsk", "kaffe", "tillval", "extra ris".
- **Sides on their own:** "sallad & bröd ingår".
- **Price and info lines.**
- **Closed or holiday markers.** "Stängt", "Sveriges Nationaldag, stängt" and "Glad midsommar" are already seen in Kooperativet and Bistrot history. These mark the day as **closed**, which Part B uses.

## A-2. Classifier (in the pipeline, deterministic, no network)

**New module:** `utils/dish_category.py`. It is called from `generate_html.py::prepare_restaurants()` right after tagging (`annotate_food_types`), so each item gains:

```json
{ "category": "pho", "category_confidence": 0.92, "category_rule": "kw:pho" }
```

The existing `item["category"]` is the restaurant's own section label (e.g. "FISK"). To avoid clobbering it, **name the new field `dish_category`**.

**Rule data:** `data/dish_taxonomy.json` is hand-edited and reviewed in PRs.

```json
{
  "version": 1,
  "categories": {
    "pho": {
      "group": "asian",
      "priority": 80,
      "keywords": ["pho", "phở"],
      "keywords_desc": ["risnudelsoppa", "rice noodle soup"],
      "exclude": [],
      "restaurant_hint": []
    },
    "tikka-masala": {
      "group": "indian", "priority": 70,
      "keywords": ["tikka masala", "tikka"], "exclude": ["paneer tikka"]
    }
  },
  "aliases": { "kyckling tikka masala": "tikka-masala" },
  "ignore": ["^dryck", "^tillval", "^extra ", "ingår$"],
  "closed": ["stängt", "closed", "glad midsommar", "nationaldag"]
}
```

**Algorithm (ordered, first decisive step wins):**

1. **Normalise.**
   - Lowercase and apply Unicode NFC.
   - Strip prices (`\d+ ?kr`), counts ("10 bitar"), spice markers (🌶️), allergen codes ("(G, L)", Pier 11 style), and leading labels such as "Veckans:", "Vegetarisk Mån–Tis:", "Dagens 1:".
   - Collapse whitespace.
2. **Ignore and closed check.** Return `null`, or the `closed` flag.
3. **Exact alias.** Look up the normalised name in `aliases`. This table grows weekly as unknown dishes are resolved (A-6).
4. **Keyword rules on the name.** Every category's `keywords` are matched with word boundaries, reusing the regex approach in `utils/annotate_food_types.py`, with `exclude` applied. Score = `priority` plus specificity (the length of the matched phrase). Specific beats generic: `butter-chicken` beats `indian-curry`, and `carbonara` beats `pasta-cream`.
5. **Keyword rules on the description**, weighted lower. Many restaurants put the real dish in the description, e.g. Cuckoo's Nest Friday items with empty names, or LS Kitchen.
6. **Restaurant hint.** It only breaks ties or upgrades generic matches: a "curry" at Masala or Bombay becomes `indian-curry`, at Encounter it becomes `curry-generic`. It never assigns a category alone.
7. **Cheap fallback: nearest labelled neighbour.**
   - Compare token-set similarity (stdlib `difflib.SequenceMatcher` over sorted tokens, or character trigrams; no new dependency) between the dish and every dish in the labelled set (`aliases` plus the gold set).
   - Accept at similarity ≥ 0.85 with confidence `0.6`.
   - **No LLM and no network in CI.**
8. **Otherwise unknown.** `dish_category = null`, and append to the queue.

**Confidence thresholds:**

| Confidence | What happens |
|---|---|
| ≥ 0.8 | The illustration is shown. |
| 0.6–0.8 | The illustration is shown, and the dish is also queued for review with the suggestion. |
| < 0.6 | Not shown, and queued. |

**Queue file:** `data/image-queue.json`. It is written by the pipeline and committed with the daily data. It is deterministic, sorted, and de-duplicated by normalised name.

```json
{
  "generated_at": "2026-11-16T05:09:12+01:00",
  "items": [
    {
      "key": "lemon pepper chicken med rostad potatis",
      "name": "Lemon pepper chicken med rostad potatis",
      "description": "...",
      "restaurants": ["Bistrot"],
      "first_seen": "2026-11-16",
      "last_seen": "2026-11-17",
      "seen_count": 2,
      "suggestion": "chicken-roast",
      "confidence": 0.55,
      "reason": "no_rule"
    }
  ]
}
```

- `reason` is one of `no_rule | low_confidence | unknown_category_requested`.
- Items unseen for 28 days are pruned automatically, so the file stays small.
- CI never calls Krea and never generates images.

**Tests** (`tests/test_dish_category.py`, offline):

- **Gold set:** `tests/fixtures/dish_gold.json`, about 300 hand-labelled dishes sampled from history across all restaurants and both languages. Assert at least 90% exact-category accuracy and **zero false positives on the ignore/closed list**.
- **Unit cases** for specificity ("Butter chicken" maps to `butter-chicken`, not `indian-curry`), exclusions, normalisation, and English/Swedish pairs (District One and Pier 11 publish English).
- **Metrics:** `utils/scrape_health.py` (or a sibling script) prints a coverage line in the job summary: *"Dish illustrations: 71/94 dishes (76%) shown · 9 unclassified · queue +3 new"*.

## A-3. Library format

```
docs/assets/dishes/<slug>.svg      # deployed, one file per category, approved only
data/dish_library.json             # manifest (not deployed; the generator inlines what it needs)
art/dishes/                        # not deployed; source of truth for art
  STYLE.md                         # the style spec and prompt template (A-5)
  refs/                            # 3–4 approved style-reference images
  src/<slug>.png                   # transparent master from Krea (kept for re-vectorising)
  review/                          # contact sheets (generated locally, git-ignored)
scripts/dish_art/                  # local-only tools, never run in CI
```

**Manifest** `data/dish_library.json`:

```json
{
  "version": 1,
  "categories": {
    "pho": {
      "status": "approved",
      "image": "assets/dishes/pho.svg",
      "name": { "sv": "Pho", "en": "Pho" },
      "what": {
        "sv": "Vietnamesisk nudelsoppa med risnudlar i klar, kryddig buljong.",
        "en": "Vietnamese noodle soup with rice noodles in a clear, spiced broth."
      },
      "typical": {
        "sv": ["risnudlar", "buljong", "kött eller tofu", "färska örter", "lime", "böngroddar"],
        "en": ["rice noodles", "broth", "meat or tofu", "fresh herbs", "lime", "bean sprouts"]
      },
      "text_source": "model-draft",
      "text_reviewed_by": "Jay",
      "text_reviewed_at": "2026-11-20",
      "art": {
        "model": "openai/gpt-image-2.6-flare",
        "krea_job_id": "…",
        "prompt_version": "v1",
        "refs": ["art/dishes/refs/ref-01.png"],
        "approved_at": "2026-11-20"
      }
    }
  }
}
```

**`status` values:**

- `draft` exists only on the art branch.
- `approved` is rendered.
- `retired` is kept for history and not rendered.

The generator renders a thumbnail only when both the SVG exists **and** the status is `approved`. A text-only category (approved text, no image yet) can still show the "What is it?" sheet; this depends on Jay's decision.

**Content rules (enforced in review, not by code):**

- `what` is one sentence, at most about 120 characters, generic, and **never names a restaurant or claims to be its recipe**.
- `typical` lists 3–7 common components, phrased as typical ("kött eller tofu"), not definitive.
- **No allergen statements, no "contains gluten" and no diet claims.** Diet tags remain the restaurant-text-based tags that already exist.
- `text_source` is one of `hand` or `model-draft`. A model draft must be reviewed by a person (`text_reviewed_by`) before `status: approved`.

## A-4. How the UI shows it (after PR #8 merges)

**Dish row thumbnail:**

- A 36×36 px illustration to the left of the dish name (32 px below 400 px viewport width).
- It sits in a fixed square, so rows without an image stay aligned. Use an empty slot, not a placeholder icon, so there is no visual noise.
- Markup:

  ```html
  <img src="assets/dishes/pho.svg" width="36" height="36" loading="lazy" decoding="async" alt="">
  ```

- `alt=""` because the image is decorative next to the dish name. The meaningful content lives in the sheet.
- No layout shift, because the dimensions are explicit.

**"What is it?" control:**

- A small text button after the dish name ("Vad är det?" / "What is it?"), plus the thumbnail itself, both open the same sheet.
- A real `<button aria-haspopup="dialog">`. Minimum hit area 44×44 via padding.
- Shown only when the category has approved text.

**Sheet (one shared `<dialog>`):**

- **Content:**
  - the illustration at 160 px;
  - the category name in sv/en;
  - the `what` sentence;
  - a "Typiska ingredienser" / "Typical ingredients" list;
  - the disclaimer, verbatim:
    > **sv:** "Generell beskrivning av rätten – inte restaurangens recept. Ingredienser kan variera. Fråga restaurangen om allergener."
    > **en:** "General description of the dish – not the restaurant's recipe. Ingredients may vary. Ask the restaurant about allergens."
  - a link back to the restaurant's own menu (from `data/restaurant_links.json`).
- **Behaviour:**
  - `Esc` and a close button dismiss it.
  - Focus returns to the trigger.
  - It respects `prefers-reduced-motion` (no slide when reduced).
  - On mobile it is a bottom sheet with `env(safe-area-inset-bottom)`.
  - It reuses the dialog and pick-dock patterns from PR #8's B2 instead of inventing a second overlay system.
- Bilingual through the existing `.sv`/`.en` spans. The language toggle needs no re-render.

**Allergens are never inferred** from the category. "Typical ingredients" is explicitly not an allergen list.

**Weight and performance budgets** (enforced by a local QA script and a CI size check):

| Budget | Limit |
|---|---|
| Single SVG | ≤ 7 KB raw and ≤ 2.5 KB gzip after `svgo`. Jay locked the detailed style at about 4–6.5 KB raw on 14 Nov 2026. |
| Paths per SVG | ≤ 40, with no `<image>`, `<text>`, filters or gradients |
| Total illustration bytes downloaded for a typical day (about 40 distinct categories on the page) | ≤ 60 KB gzip, lazily loaded |
| Above-the-fold added weight on a 375 px first view (about 4–6 thumbnails) | ≤ 15 KB gzip |
| HTML growth from inlined sheet text | ≤ 8 KB gzip. Inline only categories present that day, as one `<script type="application/json" id="dish-info">` block |
| Lighthouse (mobile) | Performance must not drop more than 2 points vs. the PR #8 baseline; CLS stays at 0 |

**Why separate `<img>` files rather than a sprite or inline SVG:**

- `loading="lazy"` works per image.
- Each file is cached independently by the browser (GitHub Pages ETags), so a new category doesn't invalidate the rest.
- It keeps the HTML small.
- The single-colour line art needs no CSS recolouring.

If request count becomes an issue, a per-build sprite is an easy later switch.

**Hairline consistency at any size:** every path uses `stroke="#111" stroke-width="1.25" fill="none" vector-effect="non-scaling-stroke"`. The line stays about 1.25 CSS px both at 36 px and at 160 px, which gives the JDS hairline look.

## A-5. Krea generation: model, prompt template, style lock and review

**Model [verified 14 Nov 2026 via the Krea connector `list_models` / `get_model_schema`]:**

- **`openai/gpt-image-2.6-flare`** ("GPT Image 2.6 Flare, with transparent background support") is the newest GPT image model in Jay's Krea account.
- **Relevant inputs:**
  - `prompt`;
  - `aspect_ratio` (use `1:1`);
  - `resolution` (`1K` is enough);
  - `quality` (`high` default; `low` for drafts);
  - `background: "transparent"` (requires PNG);
  - `image_urls` (up to 10 references);
  - `output_format: "svg"`.
- **Constraint:** SVG output is **text-to-image only** and cannot be combined with `image_urls`.
- The sibling `openai/gpt-image-2.6-sunburst` is the faster variant, for drafts.

This gives two candidate paths. **Phase 0 pilots both** on the same six categories and Jay picks one:

| | Path 1: PNG and local vectorising (recommended default) | Path 2: native SVG |
|---|---|---|
| Call | `background: transparent`, `image_urls: [3–4 approved refs]`, PNG 1K | `output_format: svg`, prompt only |
| Consistency | Strong. Reference images lock line weight, view angle and level of detail. | Prompt only, so expect drift across 100+ images. |
| Post-processing | Threshold, then centreline trace (`autotrace --centerline` or `vtracer`), then re-stroke uniformly, then `svgo` | Clean up: strip fills, force stroke, normalise the viewBox, then `svgo` |
| Risk | Tracing artefacts on dense details, so prompts must ask for sparse lines | Messy SVG structure, inconsistent stroke |

**Style lock:**

1. In Phase 0, generate the six pilot categories: `pho`, `kottbullar`, `tikka-masala`, `pasta-cream`, `salad-bowl`, `sushi-mix`. Iterate the prompt until Jay approves three or four of them as the **style references** (`art/dishes/refs/`).
2. Every later generation passes those refs in `image_urls`.
3. Optional: if drift persists after about 30 images, train a Krea style from the approved set (connector `create_style`, poll `get_job`) and use it with a model that supports styles. **[UNVERIFIED]** whether trained styles apply to GPT Image 2.6 Flare; check `get_model_schema` at that time.

**Prompt template (v1)**, stored in `art/dishes/STYLE.md` with a version number. A `{subject}` line per category is added to `data/dish_library.json` as `art.subject`.

```
Minimal hairline line drawing of {subject}, single continuous-weight thin black
outline (#111111), no fill, no shading, no hatching, no gradients, no colour,
transparent background. Three-quarter top-down view, the dish centred and
filling about 80% of a square frame with even margins. Simple, elegant,
editorial icon style, few lines, generous negative space, rounded line ends.
Only the food and its plate/bowl, plus at most one simple utensil.
No text, no letters, no logos, no hands, no table, no background objects,
no steam swirls unless essential to recognise the dish.
Match the line weight, perspective and level of detail of the reference images.
```

**Example subject lines:**

- `pho`: "a deep bowl of pho: rice noodles in clear broth, thin slices of meat, a few herb leaves, bean sprouts, a lime wedge on the rim, chopsticks resting across the bowl"
- `kottbullar`: "a plate of Swedish meatballs with mashed potato, a pool of cream sauce, a spoon of lingonberries and a few pickled cucumber slices"
- `tikka-masala`: "a shallow bowl of chicken tikka masala curry next to a small mound of rice and a folded piece of naan"

**Line colour:** Jay rejected colour fills, then chose a bolder monoline. Each file uses `stroke="currentColor"` inside `<g id="art">`, with a stroke width from 1.25 to 3 in the 64 grid. `vector-effect="non-scaling-stroke"` is allowed and not required. A path may use `fill="currentColor"` for a small solid band such as nori. The page sets the line colour per dish with CSS on the `<use>` host: beef `#b4360f`, pork `#b03a5b`, chicken `#8a5a00`, fish `#1f5f99`, veg `#2f6b1e`, otherwise `#111`. The list thumbnail is 48px and the sheet drawing is 160px. The six pilot files are in `docs/assets/dishes/`: `pho`, `kottbullar`, `tikka-masala`, `pasta-cream`, `salad-bowl`, `sushi-mix`. Other categories keep the placeholder.

**Post-processing tools** (`scripts/dish_art/`, run by the assistant locally or in a Cloud Agent session, never in CI):

1. `fetch.py`: download the Krea result (the connector `generate_image` result URL), and save it to `art/dishes/src/<slug>.png` along with the job id.
2. `vectorise.py`:
   - Pillow alpha threshold, then denoise.
   - Centreline trace to SVG.
   - Rewrite every path to `fill="none" stroke="#111" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"`.
   - Normalise to `viewBox="0 0 64 64"`, with the artwork fitted to a 56×56 safe box.
   - Run `svgo` with precision 1.
3. `qa.py` (`utils/dish_svg.py`, also run by `tests/test_dish_assets.py`): fails on any of:
   - a fill other than `none`, `transparent`, or `currentColor`;
   - a stroke other than `currentColor`;
   - a stroke width outside 1.25–3;
   - `<text>`, `<image>`, `<filter>`, `<mask>`, `<clipPath>`, `<pattern>`, `<symbol>`, `<use>`, or a gradient;
   - a `transform`, or path data with more than one decimal place;
   - fewer than 5 or more than 12 paths, or more than 160 subpaths;
   - more than 7 KB raw or 2.5 KB gzip;
   - a viewBox other than `0 0 64 64`;
   - a bounding box outside the safe area.

   The same checks run in CI as `tests/test_dish_assets.py`. That test only reads committed files, so it is offline.
4. `sheet.py`: build `art/dishes/review/contact-sheet.html`, showing every approved and draft icon at 36 px and 160 px on `#f2f2f0` and on white, in a grid next to its neighbours, with the slug, sv/en name and text.

**Review step (a person must approve):**

1. The assistant opens a PR titled "Dish art: +N categories" with the SVGs, manifest entries as `draft`, and the contact sheet attached as a screenshot.
2. Jay or a reviewer checks:
   - Is it recognisable at 48 px?
   - Is the line weight the same as the refs?
   - No text, logos or hands?
   - Is it culturally respectful and accurate (no stereotyped props)?
   - Does the `what` and `typical` text match the drawing and avoid restaurant or allergen claims?
3. Approval flips the status to `approved` in the same PR before merge. Rejected images are regenerated (with a different subject wording) or the category stays text-only.

**Cost:** each Krea call consumes compute units from Jay's Pro plan. **[UNVERIFIED]** the unit cost per GPT Image 2.6 Flare `high`/1K image; check with the connector `get_balance` before and after the pilot. Plan for about 3 generations per approved category: 115 × 3 ≈ 350 generations for the full set, and about 120 for the top 40.

## A-6. Rollout

| Phase | Scope | Exit criteria |
|---|---|---|
| **0. Pilot** (outside the repo) | Six categories, both Krea paths, prompt v1 to vN, 3–4 refs chosen | Jay approves the style and picks Path 1 or 2 and the lime decision; credit cost per image is known |
| **1. Classifier and data** (one PR, can run in parallel with PR #8) | `utils/dish_category.py`, `data/dish_taxonomy.json` (about 115 categories of rules, all of them, even without art), gold set and tests, `data/image-queue.json`, coverage line in the job summary | Gold-set accuracy ≥ 90%; zero ignore/closed false positives; pipeline green; no UI change yet |
| **2. Seed art and text** (art PRs) | The top 40 categories by frequency, recomputed from the first four weeks of Phase 1 live data: SVGs and reviewed text | QA script passes; contact sheet approved |
| **3. UI** (one PR, after PR #8 merges) | Thumbnail, "What is it?" sheet, disclaimer, budgets | Budgets met; keyboard and screen-reader checks pass; Lighthouse within budget; tested at 375 and 1280 px in both languages |
| **4. Fill out** | Categories 41–80, then the long tail | About 88–90% appearance coverage |

**Coverage metrics** (job summary, daily):

- **Shown:** dishes with an approved illustration ÷ all classifiable dishes today, both unique-weighted and appearance-weighted.
- **Classified:** dishes with any category ÷ classifiable dishes.
- **Queue:** new items today, total open items, and the top 10 by `seen_count`.
- **Per restaurant:** the share classified, which shows when a restaurant's naming style needs rules.

**Weekly loop** (Monday afternoon, after the 08:07 UTC run has the new week's menus; done by the assistant in a Cloud Agent session):

1. Read `data/image-queue.json`.
2. For each item, take the first action that applies:
   - **(a)** It fits an existing category: add an alias or keyword to `data/dish_taxonomy.json`. No image needed. This is the common case.
   - **(b)** It is noise: add it to `ignore`.
   - **(c)** It needs a new category: propose one only if it was seen on at least two days or at at least two restaurants, *and* no existing category is visually close.
3. Generate art for new categories (A-5), open one PR with the taxonomy changes and new art, get review, and merge.
4. Target: **queue at most 10 open items after the weekly loop** and **at most 3 new categories per week** at steady state.

---

# Part B: Missing info and scraping correctly and always up to date

## B-1. What's wrong today [verified 14 Nov 2026 unless marked]

**1. Wrong week can be shown.**

- The live Friday 13 Nov page listed **Bistrot's week-47 dishes**. Bistrot had published next week's menu, and the 16:13 local run scraped it as "Friday".
- Kooperativet and Bistrot both already show "v.47" on Saturday 14 Nov.
- No scraper checks the week number. This is the most serious *correctness* bug, and it is not in PR #8's scope.

**2. Three restaurants return nothing because the source has moved or closed:**

- District One (`/lunch.html` is a 404);
- Pier 11 (markup changed);
- Mimolett (the domain was taken over by an unrelated French magazine).

**3. One restaurant has closed:** Mat & Minnen.

**4. LS Kitchen** returns nothing; its operator page is a 404 and its status is **[UNVERIFIED]**.

**5. Rotation-based restaurants rely on unverified formulas:**

- Bombay uses `(week % 4) + 1`.
- Masala uses `((week - 1) % 4) + 1`.

These two formulas are inconsistent with each other, and neither is checked against what the restaurant shows as the current week.

**6. Testing and health gaps:**

- The 12 scraper tests are network-only and assert nothing.
- The health check only fails the job when fewer than 50% of restaurants are fresh, on the last cron run.

## B-2. Per-restaurant audit (the 15 in `main.py`)

**Legend for status:**

| Status | Meaning |
|---|---|
| ✅ ok | The scraper returns the current week |
| ⚠️ risk | It works, but has a correctness or fragility risk |
| ❌ broken | Returns nothing |
| ⛔ closed | The restaurant is closed |

"Publish" means when new content appeared, **[observed once]** unless stated otherwise. A fixed menu is the same every day and changes rarely.

| # | Restaurant | Current source and method | Status (14 Nov) | Best source | Extraction | Publishes | Fallback |
|---|---|---|---|---|---|---|---|
| 1 | **Kooperativet** | kooperativet.se, HTML (week text "v.NN", day blocks) | ⚠️ Mon–Thu 9 dishes each; **no Friday entry at all** (history shows Fridays as free text such as "Fredags Grillen – …", which the parser likely skips **[UNVERIFIED cause]**); page already shows v.47 on Saturday | Official site (keep) | HTML parse **plus week validation**. WordPress REST (`/wp-json/wp/v2/pages`) may expose the same content as JSON **[UNVERIFIED]** | Next week visible by Saturday morning **[observed once]** | Same-day stale carry-forward, then "see menu" link |
| 2 | **District One** | `districtone.se/lunch.html`, HTML | ❌ 404 | **The restaurant's own public Google Sheet**, which its homepage script `lunch.js` reads as CSV (`docs.google.com/spreadsheets/d/<id>/gviz/tq?tqx=out:csv`). It has a "Vecka 46" row, sv **and** en dish names, and categories. Its `menu.json` fallback is stuck at week 42. **Use the sheet only with the restaurant's permission** (it is public, but it's their data feed). | Read `lunch.js` each run to discover the sheet URL (it can change), then CSV parse and validate the week row | Unknown; still week 46 on Saturday **[UNVERIFIED]** | B5 homepage `#lunch` parser, then the link |
| 3 | **Bombay Bistro** | `/lunch/`, HTML with four "LUNCH 1–4" sections; the scraper picks one using `(ISO week % 4) + 1` | ⚠️ Returns 6 dishes per day, but **which LUNCH is current is unverified** | Official site (keep) | HTML parse. Find a "current week" marker on the page if one exists **[UNVERIFIED]**; otherwise confirm the rotation anchor with the restaurant | Page last modified Fri 13 Nov **[observed once]** | Show all four, labelled "Rotating lunch, ask which is served this week"? (Jay decision) |
| 4 | **Cuckoo's Nest** | `/menyer/lunch`, HTML with "Vecka 46" and day text | ✅ (Friday items have empty names; the text is in the description) | Official site (keep) | HTML parse **plus week validation** (the page states "Vecka NN") | Last-Modified **Mon 9 Nov 00:27 GMT**, i.e. overnight to Monday **[observed once]** | Stale carry-forward. **robots.txt sets `Crawl-delay: 10`**; honour it |
| 5 | **Uni3 World of Food** | Compass Group RSS `menuapi/feed/rss/current-week?costNumber=448305&language=sv` | ✅ (Thu 3 dishes, Fri 1) | RSS feed (keep). It's the operator's own machine-readable feed, the best kind of source | XML parse; the items carry dates, so **validate the date** | `current-week` rolls over automatically **[UNVERIFIED exact time]** | Compass restaurant page HTML, then the link |
| 6 | **Miss F** | missf.se, HTML (fixed menu) | ✅ (22 dishes, same every day) | Official site (keep) | HTML parse; **weekly** hash check | Fixed menu | Last good copy (fixed menus may be shown up to 35 days old, labelled "Fast meny") |
| 7 | **Benne Pastabar** | bennepastabar.se, HTML (fixed menu) | ✅ (10 dishes) | Official site (keep) | Same as Miss F | Fixed menu | Same as Miss F |
| 8 | **LS Kitchen** | Plate Impact screen (`plateimpact-screen.azurewebsites.net/menu/week/ls-kitchen/<id>`), via Selenium | ❌ 0 items | **[UNVERIFIED]** The Chalmers Konferens LS Kitchen page now returns 404 and `lskitchen.se` doesn't lead to a menu. The Plate Impact page is a third-party display system; its backend API is undocumented, so **don't call it without permission**. | First confirm the restaurant still operates (Jay: visit or phone). Then either ask for a text feed or permission for the Plate Impact source, or use OCR on menu images as a last resort | Unknown | Hide "today" and show "Menu unavailable" plus the link |
| 9 | **Bistrot** | bistrot.se, HTML (`li.fdm-item`, "Meny vecka NN") | ⚠️ **Showed week 47 on Fri 13 Nov** (the proven wrong-week bug) | Official site (keep) | HTML parse **plus week validation (must match the ISO week of the target day)** | Next week online by Friday afternoon **[observed once]** | Stale carry-forward, but never a different week's content |
| 10 | **Mimolett** | `restaurangmimolett.se/lunch/` | ❌ **That domain now serves an unrelated French magazine.** The live site links users to it. | The restaurant appears open (third-party listings show week-46 dishes) **[verify by visit or phone]**. Its menu page is `mimolett.kvartersmenyn.se` (Kvartersmenyn, behind a Cloudflare bot challenge, so **no automated access**). Menydags (`menydags.se/restaurang/mimolett`) mirrors it; robots allows it, but **terms are unchecked, so use it only with written permission**. | Interim: a hand-maintained fixed-menu JSON (like Masala's), verified monthly. With permission: parse Menydags or the restaurant's own feed | Weekly **[UNVERIFIED]** | **Immediately** point the link to the Kvartersmenyn page (a human-readable page is fine to link to) and stop scraping the hijacked domain |
| 11 | **Oishii** | `/lunchmeny/`, HTML (fixed menu) | ✅ (22 dishes) | Official site (keep) | Same as Miss F | Fixed menu | Same as Miss F |
| 12 | **Mat & Minnen** | `/lunchmeny` | ⛔ **Closed for lunch.** The restaurant's LinkedIn post (around 23 Jun 2025) announced the last lunch as **27 June 2025**; catering continues on a smaller scale | n/a | n/a | n/a | **Remove from the daily list** (or show "Closed since June 2025"); Jay decides. Removal changes the restaurant set, so it needs Jay's explicit OK |
| 13 | **Encounter Asian** | tamed.se take-away page (React app, Firebase backend), via Selenium | ✅ (19 dishes, fixed) | Keep Selenium for now. The Firebase JSON behind the ordering app belongs to the Tamed platform, so **use it only with Tamed's or the restaurant's permission**. | Rendered-DOM parse; **weekly** hash check (fixed menu) | Fixed menu | Last good copy, labelled "Fast meny" |
| 14 | **Masala Kitchen** | Static, hand-transcribed JSON of a **4-week rotation**, picked with `((week−1) % 4) + 1` | ⚠️ 25 dishes per day; the rotation anchor is unverified | `masalakitchen.se/lunch/` shows "Veckans Meny / Nästa Veckas Meny" tabs, each an **SVG image of the menu (outlined paths, no text)**. The site confirms four rotating menus. | **No OCR needed:** read which SVG file (`lunch-*.svg`) is in the "Veckans Meny" tab, map that file name to rotation 1–4, and pick the transcribed menu. OCR (rasterise, then Tesseract `swe`) only if the file names change | The tab switches weekly **[UNVERIFIED day]** | The formula, then the link |
| 15 | **Pier 11** (Ericsson by Nordrest) | `ericssonbynordrest.se/restaurang/restaurant-pier-11/`, Castit Menus plugin | ❌ 0 items (the scraper targets old `div.weekday-item`) | Official site (keep), `.castit-day` blocks, dishes with allergen letters, a language toggle | HTML parse of `.castit-day` (B5); strip allergen codes into a separate field; prefer the sv text if present | Last-Modified Sat 14 Nov 07:06 GMT, so the plugin auto-refreshes **[observed once]** | Stale carry-forward, then the link |

**Aggregators and social media** [verified 14 Nov 2026 unless marked]:

| Source | Finding | Use? |
|---|---|---|
| **Kvartersmenyn** | Returns 403 / Cloudflare challenge to scripted clients | **No** automated use. Linking to its pages for humans is fine. |
| **Mat och Mat** | Restaurant-paid listings; robots allows; no reuse terms found **[UNVERIFIED]** | **No** without written permission. |
| **Lunchkollen** | The TLS certificate didn't match the domain on 14 Nov | **No.** |
| **Menydags** | robots allows `/restaurang/`; has Mimolett; terms not reviewed **[UNVERIFIED]** | Only with written permission, and only for restaurants with no first-party source. |
| **Instagram / Facebook** | Login walls; Meta's terms forbid automated collection | **No** automated use. A person may read a post to update a fixed menu by hand. |

## B-3. Week and date validation (new, not in PR #8)

Every weekly-menu scraper returns a `source_week` (ISO week parsed from the page: "v.47", "Vecka 46", "Meny vecka 47", a dated RSS item, or District One's "Vecka 46" row) alongside the days.

- `main.py` compares it with the ISO week of the **target day** (Europe/Stockholm).
- **On a mismatch,** the content is discarded and status = `wrong_week`. It is **never** shown as today's menu.
- **If no week marker is found**, the scraper reports `source_week: null` and the health report flags `no_week_marker`. That is allowed only for restaurants listed as `rotation` or `fixed` in `data/sources.json` (B-6.5).
- **Friday-afternoon guard:** after 13:00 local on a Friday, runs only refresh if the week matches. This closes the 13 Nov bug even before every scraper has a week parser.
- **Offline tests:** a fixture with "v.47" scraped for a week-46 date must give `wrong_week`.

## B-4. Closed days and holidays

- The classifier's `closed` patterns (A-1) plus explicit day text ("stängt", "nationaldag", "midsommar") set day status = `closed`. The UI then shows "Stängt idag" / "Closed today" instead of "no menu".
- A small `data/holidays_se.json` (Swedish public holidays plus *klämdagar*, maintained yearly by hand) lets the health check expect closures, so it doesn't alert on them.

## B-5. Retry timing aligned with publish times

The current weekday crons are 05:07, 06:37 and 08:07 UTC (06:07/07:37/09:07 local in winter, 07:07/08:37/10:07 in summer).

Observations so far:

- Weekly menus are already up by Saturday (Kooperativet, Bistrot) or overnight to Monday (Cuckoo's Nest).
- The Compass RSS rolls over by itself.
- Pier 11 auto-refreshes.
- **No restaurant was observed publishing *after* 08:00 local on the day.** The data is thin, so treat this as a hypothesis.

Proposal:

1. **Keep the three crons.** Add **one light "gap-fill" run at 09:37 UTC** (10:37 local in winter, 11:37 in summer), Mon–Fri. It re-scrapes **only** restaurants that are `missing` or `wrong_week`, then regenerates. Cost: one GitHub Actions run (free on public repos). This needs Jay's decision.
2. **Monday guard:** at 05:07 UTC on Monday, `wrong_week` from last week's page is expected for some restaurants, so don't alert until the 08:07 run.
3. **Per-restaurant cadence** from `data/sources.json`:
   - `daily` and `weekly` sources are scraped every run until fresh for the day, then skipped on later runs (saves requests).
   - `fixed` sources are scraped once per week (Monday 05:07) with a content-hash check.
   - `rotation` sources are scraped once per day.
4. **Retry inside a run:** at most one retry per host, with a 30 s backoff. The existing 3-attempt loop around `main.py` stays, but each retry now only re-fetches the failed restaurants (depends on B6's per-restaurant reasons).
5. **Record publish times empirically:** store `first_seen_at` for each new `source_week` per restaurant in `data/sources.json`. After about 6 weeks we'll know the real publish windows and can tune the crons.

## B-6. Change detection, alerting, tests, provenance, politeness

### B-6.1 Health report (extends B6 after it merges)

Status per restaurant per run:

| Status | Meaning |
|---|---|
| `fresh` | Scraped this run |
| `stale` | Carried forward from earlier today |
| `missing` | Nothing today (with B6's reason) |
| `wrong_week` | The page shows a different week |
| `closed` | The restaurant says it's closed today |
| `static_ok` | Fixed menu within its age limit |
| `static_old` | Fixed menu past its age limit |

Plus:

- a **content hash** of the parsed menu, for change detection;
- the **source hash** of the raw page, to detect markup changes that silently return zero dishes.

**Staleness rules by weekday:**

| When | Rule | Alert level |
|---|---|---|
| Mon, 05:07 UTC | `wrong_week` allowed (last week's page) | none |
| Mon–Fri, 08:07 UTC | Weekly sources must be `fresh`, `stale` or `closed`, with `source_week == ISO week` | warning per restaurant |
| Any weekday | Same restaurant missing, wrong_week or static_old on **2 consecutive weekdays** | **per-restaurant issue** (B-6.2) |
| Any weekday, last run | Less than 50% fresh overall | job fails, plus the global issue (exists today) |
| Fixed menus | Menu hash unchanged is fine; `last_verified` older than 35 days means `static_old` | warning |
| Holidays (`holidays_se.json`) | All rules suspended | none |

### B-6.2 Automatic GitHub issues

The workflow already opens one issue when coverage is under 50%. Add, using `actions/github-script` with the built-in `GITHUB_TOKEN` and `issues: write`, which is free:

- **One issue per restaurant**, titled `Scraper: <Display name> failing`, labelled `scraper`.
  - Opened on the 2-consecutive-weekdays rule.
  - The body has the status, reason, source URL, last fresh date, and the last 5 runs' statuses.
  - Each later failing day adds a comment, not a new issue.
  - The issue is **closed automatically** when the restaurant is `fresh` again, with a comment.
- **One weekly "Source contracts" issue** if the weekly contract job (B-6.3) fails.

### B-6.3 Offline fixtures and contract tests per scraper

**Layout:** `tests/fixtures/<restaurant_key>/<YYYY-MM-DD>.html`, or `.xml` / `.csv` / `.json` for RSS, CSV and Firebase. Each has a sidecar `<YYYY-MM-DD>.expected.json` holding the parsed result.

**Capture:** `scripts/capture_fixtures.py` runs locally or in a Cloud Agent session, never in CI. It saves raw responses using the same `fetch_html()` and writes expected JSON for a person to review. Refresh it when a scraper changes, and at least monthly.

**Offline tests** (`tests/test_scrapers_offline.py`), run in every CI run:

- Each scraper parses its fixture and must equal the expected JSON.
- Week-mismatch cases.
- Empty and closed-day cases.
- Allergen-code stripping (Pier 11).
- District One CSV with sv/en.

This requires scrapers to separate **fetch** from **parse** (`parse(html, target_day) -> menu`). That refactor is mechanical, scraper by scraper, and B5 already starts it for two scrapers.

**Contract tests:** `tests/test_source_contracts.py` with the `network` marker. They run in a **separate weekly workflow** (`source-contracts.yml`, Monday 06:00 UTC) and never block the daily deploy. For each live source they assert:

- the HTTP status is 200;
- the key selector or column exists;
- a week marker is present (where expected);
- at least N dishes are parsed.

A failure opens or updates the "Source contracts" issue.

**Replace the 12 assertion-free network tests** with these two layers.

### B-6.4 Polite-scraping policy (applied inside B4's `fetch_html()` once merged)

- **User agent:** identify honestly, e.g. `LindholmenLunchBot/1.0 (+https://iamjaydesign.com/lindholmen-lunch/; support@jaydigitalstudio.com)`. This conflicts with B4's desktop-browser UA; see the Jay decision. Test each site with the bot UA before switching. If a site blocks it, ask the site for permission rather than disguising the request.
- **robots.txt:** fetch it once per host per run (`urllib.robotparser`) and skip disallowed paths. Honour `Crawl-delay`; Cuckoo's Nest sets 10 s. All 15 current hosts allowed generic crawlers on 14 Nov 2026.
- **Rate:**
  - at most 1 page request per host per run, plus at most 1 retry;
  - at most about 8 requests per host per weekday (4 runs × 2);
  - fixed menus once a week;
  - no parallel requests to the same host.
- **Conditional requests:** send `If-None-Match` / `If-Modified-Since` with stored ETags and Last-Modified values (Bombay, Cuckoo's Nest and Pier 11 send Last-Modified). On a 304, reuse the cached parse.
- **Never:**
  - log in;
  - solve or bypass CAPTCHAs, Cloudflare challenges or rate limits;
  - call undocumented backend APIs (Plate Impact, Firebase) without permission;
  - scrape social networks.
- **Back off** on 403, 429 or a challenge page: mark `missing` with reason `blocked`, don't retry that host this run, and alert a person.
- **Timeouts** as in B4.

### B-6.5 Per-restaurant source registry with "last verified"

`data/sources.json` replaces the scattered knowledge in this doc. It is hand-maintained, except for the `auto` block.

```json
{
  "Bistrot": {
    "display": "Bistrot",
    "status": "open",
    "cadence": "weekly",
    "source": { "url": "https://www.bistrot.se/", "method": "html", "week_marker": true },
    "fallback": ["stale_same_day", "link"],
    "human_link": "https://www.bistrot.se/",
    "publish_window": "by Fri afternoon (observed once)",
    "robots_checked": "2026-11-14",
    "terms_note": "first-party site",
    "permission": "none",
    "last_verified": "2026-11-14",
    "verified_by": "agent",
    "notes": "Showed week 47 on Fri 13 Nov – week validation required.",
    "auto": { "last_fresh": "…", "last_source_week": 47, "first_seen_at": { "47": "…" }, "etag": "…" }
  }
}
```

**Field values:**

- `status`: `open | closed | unverified`.
- `cadence`: `daily | weekly | rotation | fixed`.
- `permission`: `none | asked | granted | declined`.

**How it's used:**

- **`last_verified`** is the date a person (or the agent, on request) last confirmed by hand that the source, link and method are right. A verification older than 90 days is listed in the weekly contract issue.
- The UI shows **"Menu checked <date>"** per restaurant, in the footer or details. That is the auto `last_fresh` date, not `last_verified`.
- `utils/restaurants.py` (`DISPLAY_NAMES`, `LINK_KEYS`) and `data/restaurant_links.json` stay as they are. The registry references the same keys; merging them is optional later work.

### B-6.6 Restaurant permission and partnership track (drafts only; nothing is sent)

**Priority order:**

1. District One (sheet);
2. Mimolett (menu feed or permission for Menydags);
3. LS Kitchen (status and feed);
4. Bombay Bistro (rotation anchor);
5. Masala (rotation anchor);
6. Encounter (Tamed source);
7. everyone else, as a courtesy.

**What we ask for:**

1. OK to read their public menu automatically, at most a few times per weekday.
2. Their preferred source, and when they publish.
3. A contact for corrections.
4. Optional: if it's easier for them, a **shared Google Sheet template** we provide, with columns `week, day, dish_sv, dish_en, price, tags`. That is the same pattern District One already uses, and it is the most robust source we could have.

**Draft email (Swedish)**, which Jay sends himself if he chooses:

> **Ämne:** Er lunchmeny på Lindholmen Lunch
>
> Hej!
>
> Jag heter Jay och driver Lindholmen Lunch (https://iamjaydesign.com/lindholmen-lunch/), en gratis, reklamfri sida som samlar dagens lunch på Lindholmen. Vi visar [restaurang]s meny med länk till er egen sida, och hämtar den automatiskt från er webbplats några gånger per vardagsmorgon.
>
> Är det okej för er? Och finns det en källa ni hellre vill att vi använder – och ungefär när brukar veckans meny komma upp?
>
> Om ni vill kan vi också ge er ett enkelt Google-kalkylark att fylla i, så blir menyn alltid rätt hos oss.
>
> Hör gärna av er om något visas fel – då rättar vi direkt.
>
> Vänliga hälsningar,
> Jay
> Jay Digital Studio · support@jaydigitalstudio.com

Track each restaurant's `permission` and the date asked in `data/sources.json`. A `declined` means: stop scraping and show the link only.

## B-7. Build order for Part B (after PR #8 merges)

1. **Hotfix PR (can go before PR #8; needs Jay's OK):**
   - Mimolett link to `mimolett.kvartersmenyn.se`.
   - Disable the Mimolett scraper against the hijacked domain.
   - Mat & Minnen marked closed or removed.
2. **PR "Correct week":**
   - B-3 week validation for Kooperativet, Bistrot, Cuckoo's Nest, Uni3 and District One.
   - The Friday guard.
   - B-4 closed days.
   - `data/sources.json` (static fields only).
3. **PR "Sources":**
   - District One CSV (only if permission is granted; otherwise keep B5).
   - Masala current-tab detection.
   - Fetch/parse split.
   - Offline fixtures for all scrapers.
4. **PR "Ops":**
   - Per-restaurant issues.
   - Staleness rules.
   - Gap-fill cron (if approved).
   - Weekly contract workflow.
   - Polite `fetch_html()` changes.
   - "Menu checked" date in the UI.
5. **Track:** LS Kitchen status, Bombay rotation anchor, outreach replies.

---

## Decisions for Jay

**Part A, illustrations:**

1. **Style lock:** approve the Phase 0 pilot style (6 images) and pick **Path 1 (PNG references, then vectorise)** or **Path 2 (native SVG)**. The recommendation is Path 1.
2. **Lime accent:** none (recommended) or one lime shape per illustration.
3. **Krea budget:** about 120 generations for the top 40, about 350 for the full set (about 3 attempts per category). Confirm the unit cost per image with `get_balance` during the pilot.
4. **Text without image:** may the "What is it?" sheet show approved text for categories that don't have art yet?
5. **Desserts:** show them and illustrate them (`dessert-cake`, `pancake-dessert`), or keep dropping them as today?
6. **Who reviews:** Jay alone, or Jay plus one Swedish-speaking reviewer for the sv texts? Review is required before any text or image goes live.

**Part B, data and sources:**

7. **Mat & Minnen:** remove from the list, or show "Closed since June 2025"? It is closed for lunch per the restaurant's own LinkedIn post.
8. **Mimolett:** relink now to `mimolett.kvartersmenyn.se`. Then choose either a hand-maintained fixed menu, asking the restaurant, or asking Menydags for permission.
9. **District One:** OK to ask permission to read their public menu sheet, and use it once granted?
10. **LS Kitchen:** can you confirm on site (or by phone) whether it still serves lunch and who runs it? Until then it shows "Menu unavailable".
11. **Bombay and Masala rotation:** ask both restaurants which week is "LUNCH 1" / "Meny 1". Until then, should Bombay show all four rotations, or keep the formula with a "rotating menu" note?
12. **Encounter:** keep Selenium (heavy but permission-free), or ask Tamed or the restaurant for the menu source?
13. **User agent:** an honest bot UA (recommended; this changes PR #8's B4 desktop UA) or keep the browser UA?
14. **Gap-fill cron:** add a fourth weekday run at 09:37 UTC that only re-tries missing restaurants?
15. **Aggregators:** confirm the policy of no automated use of Kvartersmenyn, Mat och Mat or Lunchkollen, and Menydags only with written permission.
16. **Outreach:** OK to use the draft email (B-6.6)? You send it; nothing is sent automatically.
17. **Holidays:** show "Closed today" from a maintained Swedish holiday list?
