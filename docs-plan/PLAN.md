# Lindholmen Lunch — Review, Redesign and Growth Plan

Status: planning document only. No app code is changed by this PR.
Base: `cursor/lunch-ux-pipeline-5ed7` (PR #2, redesign, not yet merged).
Audience: the implementing agent (builds Part 2 task by task) and Jay (decides on Part 3).

Conventions used below:

- **[ASSUMPTION]** marks every number or market claim that has not been verified. Treat these as hypotheses to test, not facts.
- File and selector references point at this branch: `templates/index.html` (single Jinja template, inline CSS and JS), `generate_html.py`, `main.py`, `scrapers/*`, `utils/*`, `.github/workflows/update-and-deploy.yml`, `docs/privacy.html`.
- "SV" means Swedish UI copy and "EN" means English UI copy.

---

## Part 1 — Review of the current page and pipeline

Ranked by impact on the core job, which is answering "where do I eat today?" correctly before lunch. Severity: **P0** means the site gives wrong or late answers, or carries legal risk. **P1** hurts the task noticeably. **P2** is polish.

### 1.1 Top findings (ranked)

| # | Sev | Area | Finding | Evidence |
|---|-----|------|---------|----------|
| 1 | P0 | Pipeline | **Scheduled runs start 5.5–9 h late, i.e. after lunch.** The cron is `0 6 * * 1-5` (07:00 CET), but GitHub started the last 14 scheduled runs between 11:38 and 15:17 UTC (12:38–16:17 Stockholm). Auto-update commits in October landed around 10:47–12:14 UTC. Visitors at 11:30 usually see yesterday's page. | `gh run list --workflow update-and-deploy.yml`; `git log` "Auto-update" timestamps |
| 2 | P0 | Pipeline | **The site was stale for 3 weeks with no alert.** Every scheduled run from 27 Oct to 13 Nov failed within ~10 s because an older workflow ran Python 3.9 against `dict \| None` syntax in `main.py`. PR #1 (`5ef280e`) fixed the interpreter, but nothing notifies anyone when the run fails or when coverage drops. | `gh run list` shows 14 consecutive `failure`; last good commit before the fix was 23 Oct |
| 3 | P0 | Legal | **Tracking and ads load before consent.** `<head>` loads `gtag.js` (GA4 `G-LMDT71XZ0C`) and `adsbygoogle.js` unconditionally, and there is no consent banner. `docs/privacy.html` claims ads show "only after the user has accepted cookies" and that a cookie stores the consent choice, but neither exists. The privacy contact is `fawenah@gmail.com`, not the current owner. | `templates/index.html` lines 4–12; `docs/privacy.html` |
| 4 | P0 | Data | **Stale fallback can show last week's menu as today's.** `main.py::scrape_for_day` carries over `previous[name]` from `data/lunch_data_<weekday>.json`. That file holds the same weekday from the previous run, usually 7 days old or older. The UI only says "Earlier data", without a date. | `main.py` lines 147–161; `.tag.stale` in the template |
| 5 | P0 | Data | **The page does not know what day it is.** It is static, so on Saturday or Sunday (no cron), or before the morning run, it still says "Today · Friday". The "Updated" pill uses render time (`datetime.now()` in `generate_index_page`), not scrape time (`scrape_meta.scraped_at`). | `generate_html.py` line 182; `.hero-kicker`, `.status-pill` |
| 6 | P1 | Data | **40% of restaurants silently missing.** The 13 Nov scrape had 9 fresh and 6 missing (Kooperativet, District One, LS Kitchen, Mimolett, Mat & Minnen, Pier 11). Missing restaurants are simply not rendered, so a user can't tell "no menu found" from "closed" or "not covered". | `data/scrape_meta_friday.json`; `prepare_restaurants` only iterates `lunch_data` |
| 7 | P1 | Usability | **Above the fold on a phone is chrome, not food.** The sticky `.site-header` (~60 px) plus the sticky `.toolbar` (search, chips and meta, ~150 px), plus `.hero` (kicker, H1, paragraph, pills) push the first dish below the fold on a 375×667 viewport. While scrolling, 30%+ of the viewport is sticky chrome. | `.site-header`, `.toolbar { position: sticky }`, `.hero` |
| 8 | P1 | Usability | **Filters and search work per restaurant, not per dish.** Choosing "Fish" shows the whole Masala card (25 items) even if one dish matches, and matching dishes are not highlighted. Several chips combine with AND at restaurant level, so "Fish + Veggie" means a restaurant that has both, not a dish that is either. | `applyFilters()`; `card.dataset.tags` |
| 9 | P1 | Usability | **Card lengths vary from 1 to 25 items** (Uni3 has 1, Masala 25, Miss F and Oishii 22). The grid becomes a wall, and scanning "what's good" means reading every card. Cards are sorted alphabetically, which carries no meaning for the task. | `data/lunch_data_friday.json`; `restaurants.sort(key=name)` |
| 10 | P1 | Data | **Tagging is a naive substring match.** `food_tags.json` "vegan" includes the keyword `veg`, which matches "vegetables", "grönsaksbuljong"-style text and so on. "Veggie" can therefore appear on meat dishes. The chip label says "Veggie" for the key `vegan`. | `utils/annotate_food_types.py::_match_tags` (`kw in full_text`); `FILTER_CATALOG` |
| 11 | P1 | A11y | **Dietary info is invisible to screen readers.** Dish tags render only as emoji with `aria-hidden="true"`, with no text alternative. | `.dish-meta .tag[aria-hidden]` |
| 12 | P1 | A11y / i18n | **Language flash and wrong `lang`.** `<html lang="en">` is the default. Swedish is applied after `DOMContentLoaded` by toggling `.hidden` on every `.en` and `.sv` node, so SV users see EN first. Swedish dish names sit inside `lang="en"`, so screen readers mispronounce them. The default ignores `navigator.language`. | `toggleLanguage()`; `<html lang="en">` |
| 13 | P1 | Perf | **Third-party weight on a menu page.** AdSense (`adsbygoogle.js`, which pulls many follow-up requests), GA4, and Google Fonts (Syne and DM Sans with italics) all load on the critical path. Google-hosted fonts also send visitor IPs to Google (a GDPR concern; see LG München 2022). The HTML is 188 KB uncompressed. | `<head>`; `ls -la docs/index.html` |
| 14 | P2 | A11y | "Surprise me" (`.surprise`, fixed at the bottom) can cover focused content (WCAG 2.2 SC 2.4.11). The pick is shown only by a coloured border (`.restaurant-card.highlighted`). Focus doesn't move to the pick, and nothing is announced. | `.surprise`; `selectRandomRestaurant()` |
| 15 | P2 | A11y | The search `<label>` uses `.hidden` (`display:none`); use a visually-hidden pattern instead. `#filter-chips` has `aria-label` but no `role="group"`, so the label is ignored. `.brand` is a `<button>` that scrolls to the top, where a link or plain heading would be semantic. | template lines 666–677, 613 |
| 16 | P2 | Pipeline | Unpinned `requirements.txt` (`requests`, `selenium` and others) risks silent breakage. `tests/` exist but CI never runs `pytest`. `main.py` calls `generate_index_page()` and the workflow calls it again. A push on a weekend fails the job (argparse rejects `saturday`). | `requirements.txt`; workflow |
| 17 | P2 | Repo | `node_modules/` (1,552 files), `example/`, `flyer.html`, `generate.js`, `generate_html.js` and a root `index.html` are committed. The bot commits generated HTML daily, which bloats history. | `git ls-files` |
| 18 | P2 | Visual | Two display fonts plus radial-gradient backgrounds, shadows, hover lift and staggered `rise` animations on every card. It works, but it is busier than the Jay Digital Studio language and adds nothing to the task. | `body { background: radial-gradient… }`, `.restaurant-card { animation }` |

### 1.2 What is already good (keep)

- Mobile safety: `overflow-x: clip`, `minmax(0,1fr)` grids, `overflow-wrap:anywhere`, 44 px tap targets (`--tap`), safe-area insets, and `prefers-reduced-motion`.
- Graceful structure: an empty state when `restaurants` is empty, a `#no-match` state, and `aria-live` on `#results-meta`.
- The stale-carry concept and the `scrape_meta_<day>.json` record. These only need a date guard (see P-2).
- Bilingual UI, and filter chips rendered only when that tag exists today (`available_filters`).

### 1.3 Pipeline reliability summary

Current flow: one cron → `main.py --day <today> --refresh` (3 shell retries, each with 2 per-scraper retries) → `generate_html.py` → commit to `main` → Pages artifact from `docs/`.

Weak points, in order:

1. Timing. GitHub cron is best effort, and the top of the hour is the most congested slot.
2. No observability. Nothing reports coverage or job failure.
3. Week-old fallback data.
4. Selenium and Chrome dependency for Encounter Asian.
5. Unpinned dependencies.
6. Scrapers are untested in CI.
7. Fragile HTML scraping of 15 different sites. Long term, restaurant-submitted menus are more robust (see Part 3).

---

## Part 2 — UX/UI plan: sleeker, minimal, faster

### 2.1 Jay Digital Studio design language (measured from jaydigitalstudio.com)

Sources: the homepage HTML and `/assets/index-B_8PB_x2.css`, fetched 14 Nov 2026. Values are taken directly from the CSS unless marked "inferred".

**Type**
- Primary font: **Onest** (300–800 loaded; the CSS uses 500 most, then 600, rarely 400 and 700). `font-family: Onest, system-ui, sans-serif`.
- Secondary font: **JetBrains Mono** 400/500, loaded for small technical labels. Inferred usage: index numbers like `(001)`, `01`, and metadata.
- Display headings are very large and very tight: `clamp(46px,15vw,74px)` on mobile up to `clamp(88px,16.5vw,262px)` for the hero. `letter-spacing` runs from -0.03em to -0.09em (most common -0.05em), with `line-height` 0.76–0.98.
- Body text is 14–20 px (14 px most common, then 16, 18 and 20), with `line-height` around 1.25 for UI.
- Headings end with a full stop: "Work.", "Services.", "FAQ.", "How the work moves."

**Colour**
| Token | Value | Use on JDS |
|---|---|---|
| `--bg` | `#f2f2f0` | page background (warm off-white) |
| `--bg-raised` | `#f7f7f3` | light raised surface |
| `--ink` | `#111` | text, dark pills |
| `--ink-2` | `#555` | secondary text |
| `--ink-3` | `#aaa` | tertiary, decoration only (fails contrast as text on `#f2f2f0`) |
| `--line` | `#d7d7d1` / `#dcdcd6` / `#deded9` | hairlines, borders |
| `--dark` | `#171717` | dark sections (services, contact, metric cards) |
| `--accent` | `#c8ff36` (lime) | `::selection`, `:focus-visible` outline, pill hover fill — **always with `#111` text, never as text colour on light** |
| header | `#f2f2f0e0` + `backdrop-filter: blur(14px)` | sticky header |

**Shape and spacing**
- Radii: pills at 999px, cards at 18/20/22/24/28px.
- Gaps: 4, 8, 12, 16, 20 and 36px, plus fluid `clamp(14px,1.6vw,24px)` and `clamp(20px,2.2vw,32px)`.
- Side gutter: `clamp(14px,2.4vw,38px)`. Section padding: `clamp(70px,8vw,120px)` vertical. Card padding: `clamp(18px,2.4vw,32px)` or 22px.
- Pills: `padding: 7px 12px` / `8px 14px`.
- Max text measure: `52ch`. Content caps of 580, 640, 720 and 900px.

**Grid and breakpoints**
- Grids: `minmax(0,1fr)` → `repeat(2,minmax(0,1fr))` → `repeat(3,minmax(0,1fr))`, plus `1fr auto` rows.
- Breakpoints: `width<=460px`, `<=700px`, `<=820px`, `<=1024px`. Hover effects are gated by `(hover:hover) and (pointer:fine)`.

**Motion**
- Easing: `cubic-bezier(.22,1,.36,1)` (used 10×); reveals use `cubic-bezier(.16,1,.3,1)`.
- Durations: about 0.2–0.22s for colour and border, 0.35s for background, 0.55–0.75s for opacity and transform reveals.
- Honours `prefers-reduced-motion`.

**Tone**
- Plain, senior, confident, and short. "No theatre, no inflated promises." Copy states facts ("Typical start two to three weeks out."), uses numbered lists (`01`–`12`, `(001)`), and keeps headings to one or two words with a full stop.
- Wordmark pattern: `jay ◦ digital studio`, lowercase with a ring separator.

### 2.2 Target design tokens for Lindholmen Lunch

Replace the whole `:root` block in `templates/index.html` with the following:

```css
:root {
  --bg: #f2f2f0;  --bg-raised: #fafaf7;  --surface: #ffffff;
  --ink: #111111; --ink-2: #555555;      --line: #dcdcd6;
  --dark: #171717; --on-dark: #f2f2f0;    --on-dark-2: #a6a6a0;
  --accent: #c8ff36; --on-accent: #111111;
  --warn-bg: #fff4cc; --warn-ink: #6b5200;  /* stale; >= 4.5:1 */
  --font: "Onest", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --gutter: clamp(14px, 2.4vw, 38px);
  --gap-1: 4px; --gap-2: 8px; --gap-3: 12px; --gap-4: 16px; --gap-5: 20px; --gap-6: 36px;
  --r-pill: 999px; --r-card: 20px; --r-card-lg: 24px;
  --ease: cubic-bezier(.22,1,.36,1); --ease-reveal: cubic-bezier(.16,1,.3,1);
  --t-fast: 200ms; --t-med: 350ms; --t-reveal: 600ms;
  --tap: 44px; --max: 1280px; --measure: 52ch;
}
```

Rules:
- One sans family, Onest at weights 400, 500 and 600. Mono is only for numbers: index `01`, time `10:42`, and price `125 kr`.
- Fonts are **self-hosted** under `docs/assets/fonts/` as woff2, latin and latin-ext (å ä ö é), with `font-display: swap`. Preload Onest 500. No Google Fonts request.
- No gradients, no drop shadows on cards (1px `--line` border only), and no hover lift. Lime appears only for focus, selection, active chips and "Your pick".
- Text contrast is at least 4.5:1 everywhere (`--ink-2` on `--bg` is about 6.6:1). Never use `#aaa` for text.

### 2.3 The 5-second task: information hierarchy

User story: *It's 11:20, I'm at my desk in Lindholmen, I open the site on my phone and want to decide in under 5 seconds.*

What must be visible in the first 667 px on mobile, in this order:

1. **Trust line** (one line): today's date, how many menus are fresh, and when they were updated. Example: `Fre 14 nov · 12/15 menyer · uppdaterad 07:12`. If the page date isn't today, a warning replaces this line (see 2.6).
2. **Quick filters** (one horizontally scrolling row): `Vego`, `Fisk`, `Kyckling`, `Under 130 kr` (if price parsing allows; otherwise omit), `Pasta`, `Asiatiskt`, `Indiskt`. A search icon sits at the start of the row and expands into a field.
3. **Restaurant rows**, each showing the name, a 1–3 dish preview with prices, and tags as text. The first two rows must be visible without scrolling.

Everything else (the H1 marketing line, about text, the full menus) is secondary and sits behind a tap or below the fold.

Ordering of restaurant rows:
1. Fresh menus with dishes matching the active filters, sorted by number of matching dishes and then by name.
2. Other fresh menus, by name.
3. Stale menus (only same-day stale; see P-2).
4. A collapsed "No menu found today" group.

Optional later: a "Favourites first" sort, with up to 3 favourites starred and stored in `localStorage`.

### 2.4 Component spec

Breakpoints match JDS: **S** ≤460, **M** 461–820, **L** 821–1024, **XL** >1024.

#### C1. Header (`.site-header`)
- Content: the wordmark `lindholmen ◦ lunch` (Onest 600, lowercase, `letter-spacing:-0.04em`, 18px on S and 20px from M up) on the left, and the language toggle (`SV` / `EN` segmented pill, 2 options, `aria-pressed`) on the right.
- Not sticky on S and M; the filter row is the sticky element instead (C3). Sticky with `#f2f2f0e0` and `blur(14px)` on L and XL.
- The wordmark is an `<a href="#top">`. Remove `.brand-meta`; the date moves to C2.
- Height: 56px.

#### C2. Today line and hero (`.hero`)
- S and M: no big H1 visible. Use `<h1 class="visually-hidden">Lunch på Lindholmen idag</h1>` and show the **trust line** only. Mono for the numbers, 14px, `--ink-2`, with one dot separator.
- L and XL: show a display H1 `Lunch idag.` / `Lunch today.` at `clamp(48px,7vw,110px)`, `letter-spacing:-0.05em`, `line-height:.9`, with the trust line under it. Maximum hero height is 40vh.
- Trust line states:
  - Fresh: `Fre 14 nov · 12 av 15 menyer · uppdaterad 07:12`
  - Partial (fresh < 70%): the same line, plus an `--ink` link `3 saknas ↓` that jumps to the C6 group.
  - Wrong day: see 2.6.

#### C3. Filter row (`.toolbar`)
- One row: a `[search icon button]` followed by chips. Height is 44px plus 8px padding. Sticky at `top:0` on S and M, and under the header on L and XL. The background is `--bg` with a 1px bottom `--line` that only shows once the page has scrolled (toggle a class via `IntersectionObserver`, not a scroll listener).
- Chips are pills, `padding: 8px 14px`, Onest 500, 14px, with a 1px `--line` border. The active chip has a `--ink` background and `--on-dark` text. Keyboard focus shows a lime outline. Chips are text-first; drop the emoji except for an optional leading glyph that stays `aria-hidden`.
- Tapping search expands it into a full-width input in the same row, with the chips hidden while the input is focused and holds a value. `Esc` or `×` clears and collapses it. Use `type="search"`, a visible `<label>` that is visually hidden, and `enterkeyhint="search"`.
- Filter semantics are **OR within the chip set, applied per dish**. A restaurant is shown if at least one dish matches any active chip. Matching dishes are shown first and marked; non-matching dishes collapse.
- Search text matches the restaurant name or dish text; per-dish matches are handled the same way as filters.
- Results count: a live region below the row (`aria-live="polite"`) reading `5 restauranger · 9 rätter`. Hide it when no filter is active.
- A "Rensa" / "Clear" text button appears at the end of the row when anything is active.
- `role="search"` sits on the wrapper; the chips container gets `role="group"` with `aria-label="Filtrera på mat"`.

#### C4. Restaurant row (replaces `.restaurant-card`)
- Container: `--surface` background, 1px `--line` border, `--r-card` radius, padding of 18px on S and 22px from M up, and no shadow.
- Top line: a mono index `01` (`--ink-2`, 12px), the restaurant name (Onest 600, 20px on S and 22px from L, `-0.03em`), and on the right two 44px icon links (`Karta` map, `Webb` website) with visible text from L and icon plus `aria-label` on S.
- Dish preview: the **first 3 dishes**. When filters are active, show the first 3 *matching* dishes. Each line is a dish name (500, 16px) and its price (mono, right-aligned), with the description on a second line at 14px in `--ink-2`, clamped to 2 lines. Dietary tags appear as small text pills after the name (`Vego`, `Fisk`), not emoji-only. Each pill carries the actual label text.
- Expand: use a `<details>`-style disclosure (a `button[aria-expanded]` that toggles the `hidden` remainder) labelled `Visa alla 22 rätter` / `Show all 22 dishes`. It opens with a 350ms height and opacity transition on `--ease`. Instant under reduced motion.
- Stale variant: a `--warn-bg` pill `Meny från tis 11 nov` (with the real date) next to the name, plus 14px `--warn-ink` text: `Kunde inte hämta dagens meny. Kolla restaurangens sida.` / `Couldn't fetch today's menu. Check the restaurant's site.`
- Menu content (dish names and descriptions) is wrapped in `lang="sv"`, regardless of UI language.
- Grid:
  - S: 1 column, gap 12px.
  - M: 1 column, max width 720px, centred. One wide column reads faster than two narrow ones on tablets.
  - L: 2 columns, gap 16px.
  - XL: 3 columns, gap 20px, max width 1280px. Use CSS `columns` or `grid-auto-flow: dense` only if row heights become ragged. Otherwise keep `align-items: start`.
- No entrance animations on rows. At most, the first paint fades in the list as a whole over 200ms.

#### C5. "Your pick" (replaces fixed `.surprise`)
- An inline pill button at the end of the filter row on L and XL. On S and M it sits in the trust line area as `Välj åt mig` / `Pick for me`. It is not fixed-position, so it never obscures content.
- Behaviour: pick randomly from the visible rows; when filters are active, prefer rows with matches. Scroll the row to the top, offset for the sticky filter row (use `scroll-margin-top` on rows). Add a lime 2px outline and a lime `Ditt val` / `Your pick` pill in the row. Move focus to the row's heading (`tabindex="-1"`), and announce `Ditt val: Bistrot` in the live region. A second press picks a different row than last time.

#### C6. Missing group
- A single collapsed row at the end: `Ingen meny hittad idag (3)` / `No menu found today (3)`. Expanded, it lists names with website and map links. Data comes from `scrape_meta.missing` mapped through `display_name()` and `restaurant_links.json`.

#### C7. Footer
- `--dark` (`#171717`) full-width section, the JDS signature. Content:
  - Line 1: `Lunchmenyer från Lindholmen, uppdateras varje vardag.`
  - Line 2 (CTA for restaurants, the B2B entry point): `Driver du en restaurang här? Skicka din meny →` (mailto or form link).
  - Line 3: `Integritet · Källkod · Gjord av Jay Digital Studio ↗`, keeping the attribution "Baserat på arbete av Fawenah".
- Padding is `clamp(44px,7vw,100px)` vertical. Links are `--on-dark`, underlined on hover, with a lime focus outline.

#### C8. Consent and analytics surface
- If cookieless analytics are used (recommended in 2.7), there is **no banner**. The privacy page explains what is measured.
- If GA4 or AdSense is kept, show a bottom sheet with "Acceptera" and "Avböj" given equal visual weight, plus a link to the policy. No tracking script loads before the user accepts. The choice is stored in `localStorage`, and a footer "Cookie-inställningar" link reopens the sheet.

### 2.5 Interactions and motion

| Interaction | Spec |
|---|---|
| Chip toggle | Background and colour over 200ms `--ease`. No layout shift; the chip width stays constant at weight 500 in both states. |
| Search expand | Input width animates over 350ms `--ease`. Focus goes to the input. |
| Row expand | Height and opacity over 350ms `--ease`. Instant under reduced motion. |
| Your pick | Smooth scroll (instant under reduced motion) and a 600ms outline fade-in on `--ease-reveal`. |
| Language toggle | Instant. No flash on load (see T2). |
| Hover | Only under `(hover:hover) and (pointer:fine)`: the row border darkens to `#bcbcbc` and links get an underline. |

### 2.6 Empty, stale and edge states (copy in SV / EN)

| State | Trigger | UI |
|---|---|---|
| Wrong day | Client JS: `data-menu-date` on `<html>` ≠ today in `Europe/Stockholm` | Replace the trust line with a `--warn-bg` bar: **"Det här är menyn från fredag 13 nov. Dagens menyer kommer runt 08:00."** / **"This is Friday 13 Nov's menu. Today's menus arrive around 08:00."** Rows are dimmed slightly (opacity .85) and still usable. |
| Weekend | Today is Sat or Sun (client) | Bar: **"Helg. Lunchen är tillbaka på måndag."** / **"It's the weekend. Lunch is back on Monday."** Friday's rows are collapsed under a `Visa fredagens menyer` button. |
| Before update (weekday, morning) | Wrong day, and the local time is before 09:30 | The same as "Wrong day", but the copy says "kommer snart" / "coming soon". |
| No data at all | `restaurants` empty | **"Inga menyer just nu."** / **"No menus right now."** + "Vi hämtar menyerna varje vardagsmorgon. Under tiden: …" followed by the full restaurant link list from `restaurant_links.json`. |
| No matches | Filters or search give 0 | **"Inget som matchar."** / **"Nothing matches."** + a `Rensa filter` button. Also suggest the nearest chip that has matches today. |
| Partial coverage | missing > 0 | The C6 group, plus `N saknas ↓` in the trust line. |
| Stale restaurant | `stale` and same-day | The C4 stale variant, with the real date. |
| JS disabled | n/a | Everything renders and every dish is visible (disclosures default open via `<noscript>` style, or progressive enhancement: rows render fully and JS collapses them). |

UI copy table (keep it terse; JDS tone, with headings ending in a full stop on L and XL):

| Key | SV | EN |
|---|---|---|
| h1 | Lunch idag. | Lunch today. |
| trust | {Dag} {d} {mån} · {n} av {N} menyer · uppdaterad {hh:mm} | {Day} {d} {Mon} · {n} of {N} menus · updated {hh:mm} |
| search placeholder | Sök rätt eller restaurang | Search dish or restaurant |
| clear | Rensa | Clear |
| pick | Välj åt mig | Pick for me |
| pick badge | Ditt val | Your pick |
| expand | Visa alla {n} rätter | Show all {n} dishes |
| collapse | Visa färre | Show fewer |
| map / web | Karta / Webb | Map / Website |
| missing | Ingen meny hittad idag ({n}) | No menu found today ({n}) |
| restaurant CTA | Driver du en restaurang här? Skicka din meny → | Run a restaurant here? Send us your menu → |
| tags | Vego, Fisk, Kyckling, Pasta, Sallad, Sushi, Indiskt, Asiatiskt | Veggie, Fish, Chicken, Pasta, Salad, Sushi, Indian, Asian |

### 2.7 Ordered, independently shippable tasks

Each task is one PR off `cursor/lunch-ux-pipeline-5ed7`, or off `main` once PR #2 is merged. After every task, run `python generate_html.py`, open `docs/index.html` at 375×667, 768×1024 and 1440×900, and attach screenshots.

**Testing prerequisite:** P-0 adds `--day` to `generate_html.py`, so the page can be rendered on a weekend using the committed `data/lunch_data_friday.json`.

#### Track P — Pipeline (do first; these fix wrong or late answers)

**P-0 · Renderable on any day**
- Change: `generate_html.py` gets `argparse` with `--day {monday..friday}` (default: today), passed into `generate_index_page(day=None)`. Also pass `menu_date` (ISO date of the scrape, from `scrape_meta.scraped_at`) and `scraped_at_hhmm` to the template. Render `<html data-menu-date="{{ menu_date }}">`. Use `scraped_at` for "updated" instead of `datetime.now()`.
- AC: `python generate_html.py --day friday` on a Saturday produces a page with Friday's 9 restaurants. "uppdaterad" shows `16:13` (from `scrape_meta_friday.json`), not the render time. Existing behaviour without `--day` is unchanged.

**P-1 · Run on time, more than once**
- Change: in `.github/workflows/update-and-deploy.yml`, replace the cron with three off-peak runs: `'7 5 * * 1-5'`, `'37 6 * * 1-5'` and `'7 8 * * 1-5'` (UTC). Avoid `:00`. Each run uses `--refresh`. Add `concurrency` per day so runs don't overlap.
- If measured start delay (see P-3) is still over 60 min after two weeks, add an external trigger: a free external cron service calling `workflow_dispatch` via a fine-grained PAT stored as a secret. As an alternative, use a Vercel Cron on the preview project that calls a GitHub `repository_dispatch` endpoint.
- AC: over 5 weekdays, at least one successful run starts before 08:30 Stockholm each day, verified with `gh run list --json createdAt,event`.

**P-2 · Same-day stale only**
- Change: in `main.py::scrape_for_day`, carry over a previous entry only if `previous_meta.scraped_at` has the same date as today (a later run on the same day lost a restaurant that an earlier run found). Otherwise, put the restaurant in `missing`. Store `scraped_at` per restaurant in the payload (`"fetched_at": "2026-11-14T07:12+01:00"`), and surface it as the stale date in the UI.
- AC: a unit test in `tests/test_stale_policy.py` covers both cases. A previous file dated 7 days ago leads to missing. A previous file from 2 hours ago leads to stale with `fetched_at` kept. `pytest` passes.

**P-3 · Health report and alert**
- Change: after scraping, write `$GITHUB_STEP_SUMMARY` with a table of fresh, stale and missing per restaurant, plus the job start delay versus the cron. Fail the job, which makes GitHub email the repository owner, when `fresh < 50%` of `SCRAPERS` on the **last** scheduled run of the day. Optional: open or update a GitHub issue titled `Scrape health {date}` using `actions/github-script`.
- AC: forcing two scrapers to raise in a test branch shows them as missing in the summary. Forcing more than 50% to fail makes the job red.

**P-4 · Pin and test in CI**
- Change: pin `requirements.txt` to the currently working versions (`pip freeze` subset). Add a `pytest -q` step before scraping. The existing `tests/` use saved fixtures; mark any network-dependent test `@pytest.mark.network` and skip it in CI.
- AC: CI runs pytest and fails on a broken parser. No network tests run in CI.

**P-5 · Tag accuracy**
- Change: in `utils/annotate_food_types.py::_match_tags`, match on word boundaries (`re.search(r'\b' + re.escape(kw), text)`). Remove the `veg` keyword. Split `vegan` into `veg` (vegetarian) and keep the `vegan` key only for explicit "vegansk/vegan". Map the chip `Vego` to both.
- AC: a test confirms "Kycklinggryta med grönsaker" is not tagged veg, and "Vegetarisk lasagne" is. The Friday data yields no veg tag on any dish containing kyckling, fläsk, nöt or fisk.

**P-6 · Repo hygiene (optional, low risk)**
- Change: remove `node_modules/`, `example/`, `generate.js`, `generate_html.js` and the root `index.html` (the workflow `git add` references must be updated too), and add them to `.gitignore`. Keep `flyer.html` only if it is still used.
- AC: the workflow still deploys, and `git ls-files | wc -l` drops by about 1,550.

#### Track U — UI (ordered; each is shippable alone)

**U-1 · Consent-safe analytics (legal P0)**
- Change: delete the AdSense script and the GA4 snippet from `templates/index.html` and `docs/privacy.html`. Add one cookieless analytics script (recommended: Plausible, Umami or GoatCounter, EU-hosted or self-hosted, with no cookies or `localStorage` identifiers). Define events: `filter_toggle{tag}`, `search_used`, `pick_used`, `row_expand`, `outbound{type: map|web, restaurant}`, `lang_switch`. Rewrite `docs/privacy.html` (SV and EN): what is collected, the processor, legal basis (legitimate interest for aggregate stats), retention, the owner's contact (Jay Digital Studio AB, support@jaydigitalstudio.com or a dedicated address), and IMY complaint rights.
- AC: DevTools shows no request to `googletagmanager.com`, `googlesyndication.com` or `fonts.googleapis.com`, and `document.cookie === ""` after load. Events appear in the analytics dashboard during a manual test.

**U-2 · Language without flash**
- Change: add an inline `<script>` at the top of `<head>` that sets `document.documentElement.lang` from `localStorage.language`, or else from `navigator.language.startsWith('sv') ? 'sv' : 'en'`. Replace class toggling with CSS: `html[lang="sv"] .en, html[lang="en"] .sv { display:none }`. Delete the `.hidden`-based loops in `toggleLanguage()`. Wrap the menu content `<ul>` in `lang="sv"`.
- AC: with `localStorage.language='sv'`, a hard reload shows no English frame (Performance panel filmstrip). With an `sv-SE` browser and empty storage, the page loads in SV. axe reports no `valid-lang` issues.

**U-3 · Tokens and fonts**
- Change: replace `:root` with 2.2. Self-host Onest 400/500/600 and JetBrains Mono 500 (woff2, latin and latin-ext) in `docs/assets/fonts/` with a `@font-face` block. Remove Syne and DM Sans links. Remove the body gradients, card shadows, `rise` animations and hover translate.
- AC: there is no third-party font request. Lighthouse (mobile) shows no "ensure text remains visible" warning. The visual check matches the token sheet: background `#f2f2f0`, text `#111`, focus outline lime.

**U-4 · Header and trust line (C1, C2)**
- Change: implement C1 and C2, including the visually-hidden H1 on S and M. Show the trust line with `n of N` (N = `len(SCRAPERS)`, passed from the generator as `total_restaurants`).
- AC: at 375×667 the first restaurant row's name is visible without scrolling and the trust line shows date, coverage and time. The header is not sticky on S.

**U-5 · Date awareness and weekend (2.6 wrong-day and weekend)**
- Change: client JS compares `data-menu-date` with today in `Europe/Stockholm` (`Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Stockholm'})`) and swaps in the warning bar and copy.
- AC: on a Saturday the weekend bar shows and Friday's rows are collapsed behind a button. Simulating a Tuesday 07:30 with Monday data shows the "coming soon" copy. Matching dates show no bar.

**U-6 · Restaurant row with preview and expand (C4)**
- Change: render all dishes server-side, and add the `data-rank` index. JS hides dishes after the 3rd behind the disclosure button. Replace emoji-only tags with text pills (keep the emoji `aria-hidden` if wanted). Pass `day_label` and dates into the stale pill. Rows use `scroll-margin-top: calc(var(--toolbar-h) + 8px)`.
- AC: Masala shows 3 dishes plus "Visa alla 25 rätter", and expands and collapses with the keyboard (Enter/Space), with `aria-expanded` updated. With JS disabled, all dishes are visible. axe reports no violations for the list.

**U-7 · Filter row with dish-level matching (C3)**
- Change: implement C3. Rewrite `applyFilters()` so each `.menu-item` gets `data-match=true|false`. A restaurant is visible if any item matches. Matching items are ordered first in the preview (reorder DOM nodes or toggle with CSS `order`). The OR semantics, the clear button, the search expand and the live count all follow C3. Rows sort by match count.
- AC: selecting `Fisk` shows only restaurants with a fish dish, and each shows its fish dishes first with the `Fisk` pill. `Fisk + Vego` shows restaurants with either. The live region reads "N restauranger · M rätter". `Esc` clears search.

**U-8 · Missing group (C6) and stale variant**
- Change: the generator passes `missing_restaurants` (name, url and map from `scrape_meta.missing`) into the template, which renders C6.
- AC: with the 13 Nov data, the group lists 6 restaurants with working links, collapsed by default. The trust line shows `9 av 15` and `6 saknas ↓`, which jumps to the group.

**U-9 · Pick for me (C5)**
- Change: delete `.surprise` and its fixed positioning. Implement C5 with focus management and a live announcement.
- AC: a keyboard-only user can trigger it, focus lands on the chosen restaurant's heading, and a screen reader (VoiceOver or NVDA) announces "Ditt val: …". Pressing it twice never picks the same row twice in a row when more than one is visible.

**U-10 · Footer and restaurant CTA (C7)**
- Change: implement the dark footer. The CTA links to `mailto:` with a prefilled subject `Lindholmen Lunch – min meny` (or a form, see Part 3).
- AC: contrast is at least 4.5:1, there is a visible lime focus ring on dark, and the outbound links carry the `outbound` event.

**U-11 · Performance budget**
- Change: inline CSS stays. Defer JS (`<script defer>` or end of body). Remove unused CSS selectors left over from the old design.
- AC: on Lighthouse mobile (Moto G Power, slow 4G) for `docs/index.html`, Performance ≥ 95, Accessibility = 100, and Best Practices ≥ 95. LCP < 1.8s, CLS < 0.02, total transfer < 120 KB gzip including fonts. Run `npx lighthouse` locally and paste the results in the PR.

**U-12 · Social and SEO basics**
- Change: add `og:title`, `og:description` and `og:image` (a static 1200×630 PNG in JDS style: `#f2f2f0` background, `lindholmen ◦ lunch` wordmark, lime dot), plus `<link rel="canonical" href="https://lindholmenlunch.nu/">`, `theme-color #f2f2f0` and a `manifest.webmanifest` (name, icons, `display: standalone`) so "Add to Home Screen" works. Update `docs/sitemap.xml` `lastmod` from the generator.
- AC: the link preview renders in Slack and iMessage, and "Add to Home Screen" on iOS shows the icon and name.

Suggested order: P-0 → U-1 → P-1 → P-2 → P-3 → U-2 → U-3 → U-4 → U-5 → U-6 → U-7 → U-8 → U-9 → U-10 → P-4 → P-5 → U-11 → U-12 → P-6.

---

## Part 3 — Scale and revenue plan

### 3.1 Audience and reach (all sizes are assumptions to verify)

| Segment | Why they care | Reach channel | Size |
|---|---|---|---|
| Office workers at Lindholmen Science Park and the surrounding buildings | Daily lunch decision, 5 days a week | QR posters in lunch areas and elevators; office managers; internal Slack/Teams; LinkedIn posts from Jay's network | **[ASSUMPTION]** Lindholmen is often described as having tens of thousands of people working and studying there. Get the current figure from Lindholmen Science Park before using it anywhere. |
| Students: Chalmers Lindholmen campus, Yrgo, and the upper secondary schools in the area | Price-sensitive, phone-first, word of mouth | Student unions, Discord/WhatsApp groups, campus screens, intro-week flyers (`flyer.html` already exists) | **[ASSUMPTION]** low thousands on site daily; verify with the schools |
| Visitors and conference guests (Lindholmen Conference Centre and events) | One-off, need a quick answer | Event organisers' info packs; SEO for "lunch lindholmen" | unknown |
| Restaurants (15 listed now) | Lunch covers between 11:00 and 13:30 | Direct visits; the footer CTA | 15 known; **[ASSUMPTION]** 20–30 within a 10-minute walk |

Today's traffic is unknown in this plan: GA4 exists, but no numbers were provided. **The first action in Part 3 is to read the last 90 days of GA4 weekday users before removing it**, so the baseline survives the analytics swap.

### 3.2 Expansion: other areas and cities

The approach that scales is **one config-driven core with many area pages**, not a copy of the repository per area.

- Refactor `SCRAPERS` into `areas/<slug>.yml`, listing scraper class, display name, links and coordinates per area. Render `/<slug>/index.html` and keep `lindholmenlunch.nu` pointing at `/lindholmen/` or the root.
- Publish `docs/<slug>/today.json` (a static "API") on every build. This also feeds the bots and screens.
- Gothenburg candidates, in order of assumed fit:
  1. Johanneberg / Chalmers main campus (students plus staff, the same university brand).
  2. Gårda (dense offices).
  3. Inom Vallgraven / Centrum.
  4. Torslanda / Volvo area.
  5. Mölndal / Krokslätt.

  **[ASSUMPTION]** about density and the number of restaurants with weekly menus; verify by counting restaurants that publish weekly menus online.
- Other cities only after a second Gothenburg area works. National lunch-menu aggregators already exist (for example Kvartersmenyn; verify current coverage and competitors). A local, design-led, office-integrated niche is the differentiator, not a national directory.
- Cost of each new area: about 1 scraper per restaurant (roughly 50–180 LOC each, judging by `scrapers/*`) plus ongoing fixes when sites change. Restaurant-submitted menus (3.3 R1) are the only way to scale beyond a few areas.

### 3.3 Revenue options

Revenue formulas are given so Jay can plug in real numbers. Every price is an **[ASSUMPTION]**.

| # | Option | Effort | Revenue model (assumption) | Main risks | What must be true |
|---|---|---|---|---|---|
| R1 | **Restaurant self-serve menu and "Featured" listing.** A restaurant enters its weekly menu in a simple form (Google Form or Sheet → Action, later a tiny admin). Free tier: listed. Paid tier: pinned "Utvald" slot (max 2 per day, clearly labelled "Annons"), photo, "Dagens tips" highlight, and a monthly click report. | Med: form → JSON importer (1 new "scraper" that reads a Sheet CSV), a featured flag in the template, and a stats export from analytics outbound events | `paying restaurants × SEK/month`. **[ASSUMPTION]** 300–800 SEK/month; 3–6 paying out of about 20 within 6 months gives roughly 1–5k SEK/month | Perceived bias (neutrality is the product); small market; restaurants churn; Swedish marketing law (marknadsföringslagen) requires ads to be clearly identifiable | Outbound clicks per restaurant are measurable (U-1) and big enough to show value; at least ~1k weekday visitors **[ASSUMPTION threshold]** |
| R2 | **Weekly sponsor slot.** One tasteful sponsor line or card per week. Best fit: Lindholmen employers recruiting engineers and designers, gyms, local services. | Low: one template slot driven by `data/sponsor.json` | `weeks sold × SEK/week`. **[ASSUMPTION]** 1–3k SEK per week; sell-through 30–60% | Clashes with the minimal brand if overdone; needs a sales effort per week | Audience is provably local office workers (analytics by time of day); Jay can sell to his network |
| R3 | **B2B office screens.** A `/screen/?area=lindholmen&office=<id>` kiosk view: large type, auto-rotating, auto-refreshing, optional company logo and the canteen's own menu. | Low–Med: one more template plus an `office.json` config | `offices × SEK/month`. **[ASSUMPTION]** 200–1,000 SEK/month per screen; 5–15 offices gives roughly 1–15k SEK/month | Office IT and signage procurement is slow; many offices already have canteens | Office managers want it (validate with 5 interviews); a reliable morning update (P-1, P-3) |
| R4 | **Slack/Teams daily post.** It posts today's menus (filtered to team preferences) at 10:45 to a channel. Free for 1 channel; paid for custom filters, multiple channels, "vote where to eat" polls, and the company canteen menu. | Med: Slack incoming webhook (simplest, no app review) first; a proper Slack app or Teams bot later; reads `today.json` | `workspaces × SEK/month`. **[ASSUMPTION]** 99–299 SEK/month; conversion from free 5–10% | Enterprise Slack/Teams approval; support burden; bots get muted | Free installs above 20 **[ASSUMPTION]**; at least one champion per company |
| R5 | **Newsletter** (weekly "Veckans lunch" with highlights and new places) | Low | Sponsorship of the email **[ASSUMPTION]** 500–2k SEK per send at a few hundred subscribers, often less | Low value for a daily decision; marketing opt-in rules; list hygiene | Mainly a retention and owned channel, not a revenue line; combine with R2 |
| R6 | **Public API / data licence** (`today.json`, history) | Low (static JSON exists after 3.2) | Mostly zero at first; occasional licence **[ASSUMPTION]** | Restaurants' rights to their menu content (see 3.6); scraping terms | Use it as an enabler for R3 and R4, not a product |
| R7 | **Display ads (AdSense)** | Already wired (to be removed in U-1) | **[ASSUMPTION]** very low at local traffic levels; requires a certified CMP in the EEA | Hurts speed, the brand and trust; consent complexity | Revisit only if traffic is very large; R2 replaces it |
| R8 | **Studio lead generation for Jay Digital Studio** | Already free | Indirect: the site is a live portfolio piece of UX and engineering seen by Lindholmen companies (the JDS client base already includes Volvo and others) | None material | Footer attribution and a "case study" page on jaydigitalstudio.com |

Recommendation: start with **R8 plus R3 and R4 pilots (free)**, then **R1** once outbound-click data exists, and **R2** only once traffic is proven. Remove R7 now.

### 3.4 90-day roadmap

| Window | Product | Growth | Revenue | Exit criteria |
|---|---|---|---|---|
| Days 1–14 | Export the GA4 baseline, then ship P-0, U-1, P-1, P-2, P-3; merge PR #2 | None yet (fix trust first) | n/a | 10 consecutive weekdays with a successful run before 08:30 and coverage ≥ 70% |
| Days 15–30 | U-2 to U-8 (the redesign) | QR poster (JDS style) in 5 buildings and Chalmers Lindholmen; one LinkedIn post by Jay; ask 3 office managers for intranet links | Draft the restaurant one-pager | Weekday visitors measured; time to first outbound click measured |
| Days 31–60 | U-9 to U-12, P-4, P-5; `today.json`; Slack webhook (R4 free); `/screen/` view (R3) | 5 office-manager interviews; 3 free Slack installs; 2 free screen pilots; student-union post | Restaurant form (R1 free tier) live; onboard 5 restaurants on self-serve menus | ≥ 3 active Slack channels; ≥ 2 screens live for 2 weeks |
| Days 61–90 | Featured flag (R1), click reports; area config refactor (3.2) | Second Gothenburg area spike: count restaurants with online weekly menus in Johanneberg | Offer paid R1 to 10 restaurants; offer paid R3/R4 to the pilots; first R2 sponsor via Jay's network | Go/no-go: ≥ 1 paying customer in any line **and** weekday visitors growing month over month. Otherwise stay a portfolio piece (R8) and stop sales effort. |

### 3.5 Metrics

North star: **weekday users who click through to a restaurant (map or website) before 13:00.** This is a proxy for "the site helped someone choose lunch", and it is also the number restaurants pay for.

| Layer | Metric | Target to aim for **[ASSUMPTION]** |
|---|---|---|
| Reliability | % of weekdays with a successful run before 08:30 Stockholm | ≥ 95% |
| Reliability | Fresh coverage at 10:30 (fresh ÷ total restaurants) | ≥ 80% |
| Reliability | Days showing wrong-day data after 09:30 | 0 |
| Usage | Weekday unique visitors; share of visits 10:30–12:30 | baseline first, then +20% per month in Days 15–90 |
| Usage | Returning visitors (weekly) | ≥ 40% |
| Task | Outbound clicks per visit; time from load to first outbound click | median < 20s |
| Task | Filter, search and pick usage rates; zero-result search rate | zero-result < 10% |
| Channels | Visits by source (QR `?src=qr-<building>`, `?src=slack`, `?src=screen`); Slack installs; screens live | n/a |
| Business | Paying restaurants, sponsors, screens, workspaces; MRR; churn | first paying customer by day 90 |

Use UTM-style `?src=` parameters (stored in the analytics event, never in cookies). Report weekly via a simple dashboard in the chosen analytics tool, plus a GitHub Actions summary for reliability.

### 3.6 Analytics and legal in Sweden (high level, not legal advice)

**Cookies and terminal-device storage.** In Sweden this is governed by *lagen (2022:482) om elektronisk kommunikation* (LEK), chapter 9 section 28, supervised by PTS. Storing or reading anything on the user's device that isn't strictly necessary (analytics cookies, ad cookies, `localStorage` IDs) requires **prior, informed, freely given consent**, with refusing as easy as accepting. Storing the user's language choice in `localStorage` is a user-requested functional setting and is generally considered strictly necessary, but say so in the privacy page.

**GDPR** (supervised by IMY):
- IP addresses and online identifiers are personal data, so any analytics needs a legal basis. Legitimate interest can work for minimal, aggregate, cookieless stats; ads and profiling need consent.
- IMY found GA use unlawful at four Swedish companies in 2023, over transfers to the US before the EU–US Data Privacy Framework. The DPF is now in place, but GA still requires consent under LEK, and the framework's long-term stability is debated.
- **Recommendation:** EU-hosted cookieless analytics (U-1) means no banner is needed for the analytics itself, and the processing is described in the privacy policy, with a data processing agreement (DPA) with the vendor.
- The current setup (GA4 and AdSense loading without consent, plus a privacy policy that claims consent exists) is the single biggest legal risk. Fix it first (U-1).

**AdSense in the EEA** requires a Google-certified CMP (IAB TCF) for EEA traffic. That is another reason to drop it.

**Google Fonts.** Hot-linking sends IPs to Google; LG München (2022) found this unlawful without consent. Self-host the fonts (U-3).

**Newsletter (R5).** Marketing email to individuals requires prior opt-in under *marknadsföringslagen* (2008:486), section 19. Use double opt-in, an unsubscribe link in every send, and a list in an EU-hosted tool.

**Sponsored and featured content (R1, R2).** Ads must be clearly identifiable as advertising (*marknadsföringslagen*, section 9). Label them "Annons" or "Sponsrad".

**Menu content and scraping.** Menus are facts, but compiled menus and descriptions can be protected (copyright in the text, and the Swedish "katalogskydd" in *upphovsrättslagen*, section 49, for compilations). Website terms may also forbid scraping.
- **Mitigation:** contact each restaurant, get explicit permission (an email is enough to start), honour opt-outs within 24h, link back prominently, and move to restaurant-submitted menus (R1).
- This becomes material before charging for an API (R6) or expanding.

**Accessibility.** The European Accessibility Act (Swedish implementation in force from 28 June 2025) mainly targets e-commerce and certain services, and microenterprises providing services are exempt. A free menu site is likely out of scope, but meeting WCAG 2.2 AA (U-tasks) is cheap and matters for B2B buyers (R3, R4).

**Company and tax.** Revenue flows through Jay Digital Studio AB. Invoice with 25% VAT on ads, sponsorships and SaaS to Swedish customers. Check the reverse charge for EU B2B. Add simple terms of service for paid restaurant listings: what's promised, cancellation, and the "Annons" labelling.

---

## Appendix — Quick reference for the implementer

- Template: `templates/index.html` (Jinja2, autoescaped). Variables available today: `day`, `day_label_en`, `day_label_sv`, `last_updated`, `restaurants[]` (`id`, `name`, `dishes[]`, `tags`, `emoji_tags`, `stale`, `links{url,map}`, `search_text`), `restaurant_ids`, `restaurant_count`, `stale_count`, `filter_options[]`, `scrape_meta`.
- New variables to add (P-0, U-4, U-8): `menu_date`, `scraped_at_hhmm`, `total_restaurants`, `missing_restaurants[]` (`name`, `url`, `map`).
- Render locally: `pip install -r requirements.txt && python generate_html.py --day friday` (after P-0), then open `docs/index.html`.
- Tests: `python -m pytest -q`.
- Do not edit `docs/index.html` by hand; it is generated.
- Visual reference: https://jaydigitalstudio.com (tokens in 2.1). Current preview: https://lindholmen-lunch-preview.vercel.app/.
