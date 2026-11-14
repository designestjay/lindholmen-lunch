# Lindholmen Lunch — Next Update Plan

Status: planning document only. No app code changes in this PR.
Base: `main` at `81b2519` ("Point the site at the GitHub Pages URL (#7)").
Live: https://iamjaydesign.com/lindholmen-lunch/ (GitHub Pages, deployed from `docs/` by `.github/workflows/update-and-deploy.yml`).
Audience: the implementing agent, which builds Part 3 as **one PR**, and Jay, who answers Part 4.

Most of the earlier `docs-plan/PLAN.md` shipped in PR #6 and PR #7: the Jay Digital Studio (JDS) tokens, self-hosted Onest, no GA or AdSense, three off-peak crons, a health report, same-day-only stale data, dish-level filters, the missing-restaurants group and date banners. This document only covers what is still wrong or missing, plus Jay's floating-button idea.

How the review was done (14 Nov 2026, a Saturday):

- Read `templates/index.html`, `generate_html.py`, `main.py`, `utils/*`, `scrapers/*`, `tests/*`, the workflow, the manifest and the generated `docs/index.html`.
- Loaded the live site in headless Chrome at 375×667 (mobile emulation) and 1280×800. The page was loaded twice: as-is (weekend state) and with `?asof=2026-11-13T11:20`, the page's own hook for simulating a weekday at 11:20.
- Ran Lighthouse 12 against the live URL: mobile weekend, mobile weekday, and desktop weekday.
- Ran every scraper once from this VM, and fetched the source pages of the restaurants that came back empty.
- `pytest -q`: 13 passed, 12 skipped. All 12 skipped tests are the scraper tests, which are marked network-only.

---

## Part 1 — The floating "Pick for me" button

### 1.1 What happens today

| Viewport | Where the button is | What a press does | Can you press again without scrolling? |
|---|---|---|---|
| 375 px (S/M) | `#pick-sm`, inline in the trust row at the top of the page | Picks a random **restaurant**, then smooth-scrolls to it. Measured: `scrollY` 0 → 1,774 px on a 4,154 px page. Adds a lime outline and a "Ditt val" badge, and moves focus to the card's `h2`. | **No.** The button has scrolled off-screen, so re-rolling means scrolling back up. |
| 1280 px (L/XL) | `#pick-lg`, inside the sticky toolbar | Same as above, but the scroll is short (133 px) | Yes, because the toolbar is sticky |
| Weekend (any width) | Same buttons | **Bug:** it picks a card inside the hidden `#menus` and announces "Ditt val: Encounter Asian" to screen readers, but nothing visible happens and focus stays on the button | n/a |

Other problems with the current pick:

- It picks a restaurant, not a dish, so "Masala" still leaves 25 dishes to read. The "decide for me" job is only half done.
- Every re-roll moves focus to a different heading, so keyboard users lose their place, and pressing Enter again does nothing because focus is no longer on the button.
- The "Ditt val" badge text is created in JS once and doesn't update when the language changes.
- It only avoids repeating the last pick. With 9 restaurants, repeats within 3–4 rolls are common.

### 1.2 Evaluation of Jay's idea

| Concern | Assessment | What the spec does about it |
|---|---|---|
| Re-roll without scrolling | This is the core win on phones, and it's real: the button disappears after the first pick today. | A persistent button, and the result is shown **next to the button**, not by scrolling the page. |
| Thumb reach | Bottom of the screen is the easy zone for one-handed use. Bottom-right suits right-handed users and is the platform convention (Android extended FAB, iOS bottom actions). | Bottom-right, 16 px from the edges, as an extended pill with a text label, not an icon-only circle. |
| Safe-area insets | iPhones with a home indicator need `env(safe-area-inset-bottom)`. The page already uses `viewport-fit=cover`. | `bottom: calc(16px + env(safe-area-inset-bottom, 0px))` and `right: calc(16px + env(safe-area-inset-right, 0px))`. |
| Covering menu content | A fixed button covers the bottom-right corner, where prices and the last line of a card sit. | The list gets `padding-bottom` equal to the button zone, so the last dish can always scroll clear. `scroll-padding-bottom` on `html` keeps keyboard focus from landing under the button (WCAG 2.2 SC 2.4.11). |
| Covering the footer | A plain `position: fixed` button would sit on top of the dark footer and its links. | Use `position: sticky` on a dock at the **end of `<main>`**, not `position: fixed`. It sticks to the viewport bottom while the list scrolls and then parks above the footer by itself, with no scroll listener. |
| Keyboard and screen reader | Repeated rolls must not move focus, or Enter-Enter-Enter stops working. | Focus **stays on the button** after each roll. The result is announced through a polite live region. `Esc` closes the result. "Visa i listan" is the one action that moves focus, to the restaurant heading. |
| Reduced motion | A dice or slot animation is fun once and tiring by the tenth roll, and must disappear under `prefers-reduced-motion`. | A short 280 ms crossfade plus a 180° turn of the dice icon. Under reduced motion the swap is instant. A press during an animation finishes it at once, so input never queues. |
| Result near the button vs scrolling to it | Scrolling to the card is disorienting on a 4,000 px page and breaks rapid re-rolls. Showing the result next to the button keeps the user in place. | The result card opens just above the button. The list does **not** scroll. The matching restaurant row also gets the lime outline, so it is easy to find when the user does scroll. |
| Re-roll animation | It should signal "new result" without slowing the user down. | See reduced motion above. There is no artificial delay before the result appears. |
| History of last picks | Useful for "the one before was better". | The last 3 picks show as small text buttons inside the result card. Tapping one shows it again. History lives **in memory only**, so there's nothing to declare on the privacy page. |
| Respect active filters and search | Required. Picking a meat dish while "Vego" is on would break trust. | The pool is the dishes currently matching the filters and search (`li.menu-item[data-match="true"]` in visible cards). If the pool is empty the button is disabled and says why. |
| Respect language | Required. | All button, card and announcement text comes from the `sv`/`en` copy table and updates on language switch, including a card that is already open. |

### 1.3 Recommendation

Build it, but as a **"pick dock"** rather than a lone FAB. On phones and tablets (≤820 px), use a sticky extended button at the bottom-right that never covers the footer. Show the result as a small card right above the button, so the user can re-roll as many times as they like without the page moving. Pick a **dish** (restaurant + dish + price), not just a restaurant.

On desktop (≥821 px), keep the existing button in the sticky toolbar and open the same result card. A floating button there would duplicate a control that is already always visible.

### 1.4 Spec

#### Markup and placement

- Remove `#pick-sm` from the trust row. Keep `#pick-lg` in the toolbar for L/XL.
- Add one dock as the **last child of `<main>`**, inside `.wrap`:

```html
<div class="pick-dock" id="pick-dock">
  <section class="pick-card" id="pick-card" hidden aria-labelledby="pick-card-title"> … </section>
  <button type="button" class="pick-fab" id="pick-fab" aria-controls="pick-card" aria-expanded="false"> … </button>
</div>
```

- Render the dock only when `restaurants` is non-empty.
- `.pick-dock`:
  - `position: sticky; bottom: calc(16px + env(safe-area-inset-bottom, 0px));`
  - `display: flex; flex-direction: column; align-items: flex-end; gap: 8px;`
  - `margin-inline-start: auto; width: fit-content; max-width: 100%;`
  - `pointer-events: none;` with `pointer-events: auto` on its children, so the empty area of the dock never blocks taps.
  - `z-index: 35`, which puts it above the toolbar (30) and below the skip link (80).
- `.restaurant-list` gets `padding-bottom: calc(56px + 32px + env(safe-area-inset-bottom, 0px))` on S/M. Add `html { scroll-padding-bottom: 96px; }` on S/M.
- **≥821 px:** hide `.pick-fab` (`display: none`). The dock stays and only hosts the card. Pin the card at the bottom-right with `position: fixed; right: var(--gutter); bottom: 24px; width: 360px`. `#pick-lg` drives it.

#### The button (`.pick-fab`)

| Property | Value |
|---|---|
| Size | Height 56 px, `min-width: 56px`, padding `0 20px 0 16px`. The whole pill is the tap target (≥44 px). |
| Shape | `border-radius: var(--r-pill)` |
| Colour | `background: var(--ink)` (#111), `color: var(--on-dark)` (#f2f2f0). A 6 px lime dot (`--accent`) sits before the label. This is the only lime on the button, which keeps lime sparing. |
| Content | An 18 px dice icon (`aria-hidden`) and the label `Välj åt mig` / `Pick for me`. After the first roll, the label changes to `En till` / `Another`. |
| Type | Onest 500, 15 px |
| Shadow | `0 6px 20px rgb(0 0 0 / .18)`. This is the one shadow on the page. It is needed because the button floats over content. |
| Focus | `:focus-visible` has a 2 px lime outline with a 2 px offset, the same as the rest of the site. |
| Hover | Only under `(hover:hover) and (pointer:fine)`: background `#2a2a2a` |

States:

| State | Trigger | UI |
|---|---|---|
| Idle | Default | Label `Välj åt mig` / `Pick for me` |
| Open | The result card is showing | Label `En till` / `Another`, and `aria-expanded="true"` |
| Rolling | Up to 280 ms after a press, motion allowed | The dice icon turns 180°. The label doesn't change. |
| Disabled | No matching dishes (filters or search give 0) | `aria-disabled="true"` (not `disabled`, so it stays focusable). Opacity .5. A press announces `Inget att välja bland – ändra filtren.` / `Nothing to pick from – change the filters.` |
| Hidden | The search field is focused on S/M (the on-screen keyboard is open), **or** it's the weekend and the Friday menus are collapsed | The dock gets the `hidden` attribute. On the weekend it appears once `Visa fredagens menyer` is pressed. |

#### Pick logic

1. Build the pool from the DOM after `applyFilters()` has run. A restaurant is eligible when it is not hidden, the list isn't hidden by the weekend state, and the restaurant has at least one dish with `data-match="true"`. When nothing is filtered, every dish counts as matching.
2. Exclude stale restaurants unless no fresh restaurant is eligible.
3. Exclude dishes whose `category` matches `/tillbehör|sides|dryck|dessert|extra/i`, and dishes with no name. The generator must emit the category as `data-category` on each `li.menu-item` for this to work.
4. **Choose a restaurant first, then a dish within it**, so Masala (25 items) and Oishii (22) don't dominate.
5. **No repeats until the pool is exhausted:** use a shuffle bag of restaurants that refills when empty or when filters change. Never show the same restaurant twice in a row while more than one is eligible.
6. Mark the chosen restaurant's row with `.is-pick` (the existing lime outline) and remove the mark from the previous one. **Do not scroll.**

#### The result card (`.pick-card`)

- Container: `--surface` background, 1 px `--line` border, `--r-card` (20 px) radius, 16 px padding, and the same shadow as the button.
- Width: on S, `min(100vw - 2 * var(--gutter), 420px)`. On L/XL, 360 px.
- Content, top to bottom:
  1. A small lime pill `Ditt val` / `Your pick` (`--accent` with `--on-accent` text) and a close button (`×`, 44×44, `aria-label` `Stäng` / `Close`) on the right.
  2. `h2#pick-card-title`: the restaurant name (Onest 600, 20 px, `-0.03em`).
  3. The dish name (500, 16 px, `lang="sv"`) with the price on the right (mono). The dish's text pills follow, using the same `.pill` markup as the list.
  4. The description, clamped to 2 lines, in `--ink-2`.
  5. An action row: `Visa i listan` / `Show in list` (a text button that scrolls to the row, offset for the sticky toolbar, and moves focus to its `h2`), plus `Karta` / `Map` and `Webb` / `Website` links with `data-outbound` attributes, so the existing `outbound` event fires.
  6. When history exists: `Senaste:` / `Recent:` followed by up to 3 text buttons with the restaurant name and a short dish name, newest first. Tapping one shows that pick again without adding to history.
- The card is **non-modal**: no focus trap, and the page stays scrollable. `Esc`, or the close button, hides it and returns focus to whichever trigger opened it. Tapping outside does **not** close it, so scrolling the list while the card is open works.
- On S, if the card would cover more than 45% of the viewport height, clamp the description to 1 line and hide the history row.

#### Announcements

- Keep the existing `#pick-live` element (`aria-live="polite"`). On each roll, clear it, then after 30 ms set it to `Ditt val: {restaurant} – {dish}, {price}` / `Your pick: {restaurant} – {dish}, {price}`. Leave out `, {price}` when there's no price.
- Focus stays on the trigger (`#pick-fab` or `#pick-lg`).

#### Motion

- Card open: opacity 0→1 and `translateY(8px)`→0 over 280 ms on `--ease-reveal`.
- Re-roll: crossfade the card contents over 200 ms on `--ease`, and turn the dice icon 180° over 280 ms.
- Under `prefers-reduced-motion: reduce`, everything is instant. The existing global rule already does this as long as the new rules use `transition` and `animation`.

#### Copy (sv / en)

| Key | SV | EN |
|---|---|---|
| fab idle | Välj åt mig | Pick for me |
| fab open | En till | Another |
| badge | Ditt val | Your pick |
| show in list | Visa i listan | Show in list |
| close | Stäng | Close |
| recent | Senaste: | Recent: |
| live | Ditt val: {r} – {d}, {p} | Your pick: {r} – {d}, {p} |
| empty pool | Inget att välja bland – ändra filtren. | Nothing to pick from – change the filters. |
| fallback dish name | Dagens rätt | Today's dish |

#### Analytics

- Keep `track("pick_used", {})` and add `{ n: <roll count this session> }`. Add `track("pick_show_in_list", {})`. `analytics.js` stays disabled while `data-endpoint` is empty, and the `[CONFIRM: analytics processor]` placeholders stay as they are.

---

## Part 2 — Review of the current build

### 2.1 What is already good (keep)

- **Weekday performance is excellent.** Lighthouse mobile on the live site with `?asof=` a weekday scored Performance 100, Accessibility 100, Best Practices 100 and SEO 100. LCP 1.4 s, CLS 0, TBT 0 ms, 94 KiB total transfer (23 KB gzip HTML) and no third-party requests.
- **The JDS language is applied faithfully:** Onest 400/500/600 self-hosted with latin-ext, `#f2f2f0` background, `#111` ink, and lime only on focus, selection and the pick. Pills, a 20 px card radius, mono for numbers, and "Lunch idag." with a full stop.
- **Mobile is safe:** no horizontal overflow at 375 px, 44 px tap targets, safe-area padding on the header and footer, and `prefers-reduced-motion` respected.
- **Data honesty is much better:** same-day-only stale data, a `Meny från {date}` pill, `9 av 15 menyer · uppdaterad 16:13`, the `6 saknas ↓` group, and wrong-day, weekend and before-08:00 banners.
- **The pipeline:** three off-peak crons (05:07, 06:37 and 08:07 UTC), a concurrency group, pinned requirements, `pytest` in CI, a health summary, and a red job plus a GitHub issue when coverage is under 50% on the last run.

### 2.2 Findings, ranked by impact

Severity: **P0** means users see wrong, broken or missing content. **P1** hurts the core task noticeably. **P2** is polish or hygiene.

| # | Sev | Area | Finding | Evidence |
|---|---|---|---|---|
| 1 | P0 | Weekend state | **On weekends the page renders every menu, then JS hides them after first paint.** Lighthouse mobile measured CLS **0.395** and Performance **81** (the footer jumps up about 3,000 px). In the same state, "Välj åt mig" picks a card inside the hidden list and announces it to screen readers, but nothing visible happens. The filter chips and search act on the hidden list. The copy is also wrong for the day: the H1 says "Lunch idag." and the missing group says "Ingen meny hittad idag (6)". Every Saturday and Sunday visit is affected. | `applyDateState()` runs at the end of `<body>` and adds `body.is-weekend`, and `body.is-weekend #menus { display:none }` applies after the first render. Lighthouse `layout-shifts`: `footer.site-footer` scores 0.394. The pick probe gave `pickedVisible:false` with live text "Ditt val: Encounter Asian". |
| 2 | P0 | Coverage | **6 of 15 restaurants are missing, and 5 of them fail silently** (0 items, no exception), so the health report can't tell a broken parser from a closed kitchen. Probed today: **District One**'s `lunch.html` returns **HTTP 404** (the homepage now has a `#lunch` section). **Pier 11**'s page contains the menu as text ("Måndag Kebab spiced soy strips…"), but the markup changed and `div.weekday-item` is gone. **Mimolett** returns 200 but parses 0 dishes. **Mat & Minnen** returns 200 with no menu text in the static HTML (probably rendered by JS). **LS Kitchen** is image-only (known). **Kooperativet** parses Mon–Thu only, with no Friday menu. | `scrape_meta_friday.json`. A local run of every scraper on 14 Nov: 0 items for DistrictOne, LsKitchen, Mimolett, MatMinnen and Pier11. `curl` status codes as listed. |
| 3 | P1 | Pipeline | **A hanging restaurant site can stall the whole day.** 12 of the 15 scrapers call `requests.get(url)` with **no timeout**, and the job has no `timeout-minutes`, so GitHub's default of 360 minutes applies. Because of `concurrency: lindholmen-lunch-daily`, a hung 05:07 run holds the lock while the later runs queue, and GitHub keeps only one pending run, so the 06:37 run gets replaced. The page would then stay on yesterday's menu all day. | `grep requests.get scrapers/*.py`. The workflow has no `timeout-minutes`. |
| 4 | P1 | Pick UX | **On phones, the pick can't be re-rolled without scrolling back up** (Part 1). It also picks restaurants rather than dishes, moves focus on every roll, and the badge doesn't follow language changes. | Measured `scrollY` 0 → 1,774 px. `pickButtonOnScreenAfterPick: false` at 375 px. |
| 5 | P1 | PWA | **"Add to Home Screen" opens the wrong site.** `manifest.webmanifest` has `"start_url": "/"` and `"scope": "/"`. These resolve to `https://iamjaydesign.com/`, Jay's portfolio, not `/lindholmen-lunch/`. PR #7 moved the site to the subpath but didn't touch the manifest. There is also no maskable icon (Android shows a white square around the icon) and no `id`. | `docs/manifest.webmanifest`. `https://iamjaydesign.com/manifest.webmanifest` → 404, showing the root is a different site. |
| 6 | P1 | Data truth | **"Fresh" doesn't mean "this week's menu".** Nothing compares the menu's week number with the current ISO week. If a restaurant forgets to update its site, last week's dishes are labelled fresh. **Masala** is a static 4-week rotation JSON (`scrapers/masala_lunch_all_weeks.json`) and **Bombay Bistro** computes its rotation from the week number. Both always count as fresh, even if the restaurant has changed its menu. | `scrapers/masala.py`, `scrapers/bombay_bistro.py` (`(week % 4) + 1`). Masala uses `((week - 1) % 4) + 1`. Neither formula is checked against what the restaurant actually serves. |
| 7 | P2 | Visual | **Long price strings squeeze the dish name at 375 px.** Masala's price `119 kr, takeaway 114 kr` takes about 60% of the row, so `MURG METHI MALAI` wraps to 2 lines and the description becomes a narrow column. Benne and Masala dish names are ALL CAPS while the others are sentence case, which looks uneven in a JDS layout. | Screenshot, live 375 px after pick. `.dish-line { grid-template-columns: minmax(0,1fr) auto }` |
| 8 | P2 | A11y | The footer credit link "Fawenah" is `#f2f2f0` inside `#a6a6a0` text with no underline: a **2.18:1** link-to-text contrast, and colour alone distinguishes it. This is the only item behind desktop Lighthouse Accessibility **96**. On L/XL, the `#pick-lg` label sits about 3 px higher than the chip labels because `.pick` is `inline-flex` without `align-items: center`. | Lighthouse desktop `link-in-text-block`. 1280 px screenshot. |
| 9 | P2 | Tests | The scraper tests only print output, make no assertions, need the network, and are skipped in CI (12 of 25). There is no offline HTML fixture for any parser, so the breakages in #2 couldn't be caught. There is no browser test of the page JS (pick, filters, date states), even though Chrome and Selenium are already on the runner. | `tests/test_*.py`, `tests/conftest.py` |
| 10 | P2 | Perf | `assets/analytics.js` is a synchronous `<script>`, which Lighthouse flags as render-blocking (it's small, but free to fix with `defer`). GitHub Pages serves fonts with `max-age=600`, which can't be changed on Pages. That's acceptable at about 50 KB of fonts with ETag revalidation. | Lighthouse `render-blocking-insight`, `uses-long-cache-ttl` |
| 11 | P2 | Health | The health summary only knows fresh, stale and missing. It doesn't record **why** something is missing (HTTP status, exception, or 0 items), so a 404 looks the same as an empty Friday. The first scheduled runs under the new crons haven't happened yet (the crons were added on Saturday 14 Nov), so start delay is still unmeasured. | `utils/scrape_health.py`, `main.py::scrape_for_day` |
| 12 | P2 | Docs/repo | `README.md` still documents cron `0 6 * * 1-5`, Python 3.9, "I'm feeling hungry!", and `fawenah@gmail.com` as the contact. The Node leftovers (`server.js`, `scrape.js`, `package.json` with express and axios) and `prototype/` are not used by the pipeline. | Files listed |
| 13 | P2 | SEO | `https://lindholmenlunch.nu/` still serves the **old** Fawenah page with GA4 and AdSense under the same brand name. That causes brand confusion and duplicate content. The `google-site-verification` meta was removed in #7, so Search Console needs re-verifying for the new URL. `<title>` is static, and `og:description` is Swedish only. There's no `robots.txt`, which can't be fixed from a subpath anyway (it must live at `iamjaydesign.com/robots.txt`). | `curl lindholmenlunch.nu`; Lighthouse SEO 100 otherwise |

### 2.3 Error and empty states, checked

| State | Today | Verdict |
|---|---|---|
| Weekday, all good | Trust line, list and filters work. Lighthouse 100. | OK |
| Weekday before the first run (Mon 06:00) | "Det här är menyn från fredag 13 nov. Dagens menyer kommer snart." | OK |
| Weekend | Banner and "Visa fredagens menyer" are correct, but see finding #1 (CLS, a pick on hidden cards, filters on a hidden list, "idag" copy) | **Fix** |
| One scraper fails | Listed in "Ingen meny hittad idag (n)" with website and map links | OK. The wording on weekends needs fixing (#1). |
| Most scrapers fail | The job turns red and opens a "Scrape health" issue, but only on the 08:07 UTC run | OK |
| Total failure, no data | "Inga menyer just nu." plus the full directory | OK |
| Filters give 0 | "Inget som matchar." plus Clear and a nearest-chip suggestion | OK. The pick button must handle this too (Part 1). |
| Scraper hangs | The job can block for up to 6 h (#3) | **Fix** |
| Public holiday (e.g. 24 Dec, Midsummer Eve) | Scrapers may still return the weekly menu, so the page shows dishes for closed kitchens | Jay decision (Part 4) |

---

## Part 3 — The next update (one PR, built by Grok 4.7)

Branch: `cursor/next-update-<suffix>` off `main`. Title: `Pick dock, weekend fix, PWA path, scraper hardening`.

Ground rules:

- No new paid services, no analytics vendor and no tracking. Don't reintroduce GA or AdSense. Don't add restaurants or new scraping targets. Fixing an existing restaurant's moved page **on its own domain** is in scope.
- Leave every `[CONFIRM: …]` placeholder in `templates/privacy.html`, `docs/privacy.html` and `assets/analytics.js` as it is.
- Don't hand-edit `docs/index.html` or `docs/privacy.html`. Regenerate them with `python generate_html.py --day friday`.
- Keep the existing data flow, the JDS tokens and the sv/en pattern (`html[lang] .sv/.en`).
- One commit per item below, in this order. Items 1–6 are **must-ship**. Items 7–9 are **should-ship**: drop them only if they would put the PR at risk, and list what was dropped in the PR body.

### B1 · Weekend and wrong-day state before first paint (finding #1) — must

- **Change:**
  - Move the date-state decision into the existing inline `<head>` script. Read `data-menu-date` from `<html>`, compute the Stockholm date, weekday and minutes, honour `?asof=`, and add `html.is-weekend`, `html.is-wrong-day` or `html.is-soon` **before the body renders**.
  - Change the CSS selectors from `body.is-*` to `html.is-*`. Keep `bannerState()` as the single source of truth: define it in the head script, expose it as `window.lunchDateState`, and have the end-of-body code reuse it.
  - On the weekend, while the Friday menus are collapsed, hide `#toolbar` and the pick dock. Show them when `Visa fredagens menyer` is pressed. That button gets `aria-expanded` and `aria-controls="menus"`.
  - Weekend copy:
    - H1 on L/XL: `Fredagens lunch.` / `Friday's lunch.`
    - Hidden H1 on S/M: `Lunch på Lindholmen i fredags` / `Lunch in Lindholmen last Friday`.
    - Missing group: `Ingen meny hittad i fredags ({n})` / `No menu found on Friday ({n})`.
  - On wrong-day (weekday) states, replace `idag` / `today` with the menu's day: `Ingen meny hittad {day} ({n})`. Put the alternate strings in `date_copy` from `generate_html.py`, and swap them in with `html.is-*` CSS classes so nothing shifts.
- **Files:** `templates/index.html`, `generate_html.py`.
- **AC:**
  - Lighthouse mobile on the generated page with no `asof`, run on a Saturday or with a weekend `asof` value: **CLS ≤ 0.02** and Performance ≥ 95.
  - On the weekend, pressing a pick trigger is impossible until Friday's menus are revealed. After revealing, the pick shows a visible result.
  - `?asof=2026-11-14T10:00` shows "Fredagens lunch." and "Ingen meny hittad i fredags (6)". `?asof=2026-11-13T11:20` shows "Lunch idag." and "Ingen meny hittad idag (6)".
  - No change in weekday behaviour.

### B2 · Pick dock (Part 1) — must

- **Change:** implement section 1.4 exactly.
  - Remove `#pick-sm` from the trust row.
  - Add `data-category` and `data-price` on `li.menu-item`, plus `data-map` and `data-url` on `article.restaurant`, so the card can be built from the DOM without another JSON blob.
  - Replace `pickForMe()` with the new pool and shuffle-bag logic and the card renderer. Keep `#pick-lg` as the L/XL trigger.
  - Re-render an open card's text on `setLang()`. The language-switch fix for the badge comes with this.
- **Files:** `templates/index.html`, `generate_html.py` (category and price attributes).
- **AC:**
  - At 375×667, press the button 10 times: `window.scrollY` doesn't change, the button stays in the same place on screen, focus stays on the button, and every result names a restaurant and a dish.
  - No restaurant repeats until all eligible restaurants have been shown once (with 9 restaurants and no filters, the first 9 rolls are 9 distinct restaurants).
  - With `Vego` active, every picked dish has the `vego` token. With a search that matches nothing, the button is `aria-disabled` and announces the empty-pool copy.
  - Scrolled to the bottom of the page, the dock sits above the footer and doesn't overlap it. The last dish of the last card can be scrolled fully above the button.
  - `Esc` closes the card and returns focus to the trigger. "Visa i listan" scrolls the row under the sticky toolbar and focuses its `h2`.
  - With reduced motion emulated in DevTools, there are no transitions.
  - Switching SV↔EN with the card open translates every string in it.
  - At 1280 px there is no floating button, `#pick-lg` opens the card at the bottom-right, and repeated presses re-roll in place.
  - VoiceOver (iOS) or NVDA reads "Ditt val: Masala – Murg methi malai, 119 kr" (or similar) after each roll.

### B3 · Manifest on the subpath (finding #5) — must

- **Change:**
  - Set `"id": "./"`, `"start_url": "./"` and `"scope": "./"`. These resolve relative to the manifest URL, so they keep working if the site moves again.
  - Add `"lang": "sv"` (already there) and `"dir": "ltr"`.
  - Add a maskable 512×512 icon `assets/icon-maskable-512.png`: the existing mark centred within the inner 80% safe zone on `#f2f2f0`. Use `"purpose": "maskable"`, and keep the existing `"any"` icons.
- **Files:** `docs/manifest.webmanifest`, `docs/assets/icon-maskable-512.png`.
- **AC:**
  - Chrome DevTools → Application → Manifest shows no errors, the start URL is `https://iamjaydesign.com/lindholmen-lunch/`, and the maskable preview looks right.
  - On Android Chrome, "Install app" opens `/lindholmen-lunch/`.
  - On iOS Safari, "Add to Home Screen" shows the icon and opens `/lindholmen-lunch/`.

### B4 · Timeouts everywhere (finding #3) — must

- **Change:**
  - Add `fetch_html(url, *, timeout=(5, 20), headers=None) -> str` in `scrapers/base.py`. It uses a shared `requests.Session` with a desktop User-Agent and `Accept-Language: sv-SE,sv;q=0.9`, calls `raise_for_status()` and returns `response.text`.
  - Replace every bare `requests.get(...)` in `scrapers/*.py` with it. For the Selenium scrapers (Encounter Asian, LS Kitchen), keep `set_page_load_timeout(15)` and add one to LS Kitchen if it's missing.
  - In the workflow, add `timeout-minutes: 20` to `scrape-and-build` and `timeout-minutes: 10` to the scrape step.
- **Files:** `scrapers/base.py`, `scrapers/{benne_pastabar,bistrot,bombay_bistro,cuckoos_nest,district_one,kooperativet,mat_minnen,miss_f,mimolett,oishii,restaurant_pier_11,uni3_world_of_food}.py` (all 12 call `requests.get` today), `.github/workflows/update-and-deploy.yml`.
- **AC:**
  - `grep -n "requests.get(" scrapers/` returns nothing outside `base.py`.
  - A unit test monkeypatches `requests.Session.get` to raise `requests.Timeout`, and `scrape_for_day` records that restaurant as missing within the retry budget without hanging.
  - The workflow YAML validates (for example, `actionlint` passes or the Actions tab shows no syntax error on push).

### B5 · Fix the two scrapers with clear evidence, with offline fixtures (finding #2) — must

- **Change:**
  - **Pier 11** (`scrapers/restaurant_pier_11.py`): the menu is in the static HTML at `https://ericssonbynordrest.se/restaurang/restaurant-pier-11/`, but `div.weekday-item` no longer exists. The day headings are now `<span … data-en="Monday">Måndag</span>`. Rewrite the parser for the current markup, and keep the Swedish dish text.
  - **District One** (`scrapers/district_one.py`): `https://www.districtone.se/lunch.html` returns 404. The lunch content is now on `https://www.districtone.se/` in the `#lunch` section. Point the scraper there and adapt the parser. This is the same domain and the same restaurant. If the homepage only links to a PDF for lunch, stop and list that under Part 4 instead of parsing PDFs.
  - Save each page's HTML on build day as `tests/fixtures/pier11.html` and `tests/fixtures/district_one.html`. Give each parser an injectable `html` argument (or a `parse(html)` method) so tests run offline.
- **Files:** the two scrapers, `tests/fixtures/*.html`, `tests/test_restaurant_pier_11.py`, `tests/test_district_one.py`. Rewrite both tests as offline, assertion-based tests, and drop `pytestmark = pytest.mark.network` from them.
- **AC:**
  - `pytest -q` (offline) passes. Each fixture test asserts at least 3 dishes for at least one weekday, non-empty names, and a Swedish weekday mapping.
  - A local `python main.py --day <weekday> --refresh` on a weekday lists both restaurants as fresh, as long as their sites publish that day.

### B6 · Record why a restaurant is missing (finding #11) — must

- **Change:**
  - In `main.py::scrape_for_day`, add `missing_reason` to `scrape_meta_<day>.json`, as a map of `scraper → "http_<code>" | "timeout" | "error:<ExceptionName>" | "empty"`. Catch `requests.HTTPError` to get the status code.
  - In `utils/scrape_health.py`, add a "Reason" column to the summary table.
  - Leave the UI unchanged: the missing group keeps the website and map links only.
- **Files:** `main.py`, `utils/scrape_health.py`, `tests/test_stale_policy.py` or a new `tests/test_missing_reason.py`, `tests/test_health_report.py`.
- **AC:** unit tests cover all four reasons. The summary for a fixture meta shows e.g. `| District One | missing | http_404 |`.

### B7 · Visual and accessibility polish (findings #7, #8, #10) — should

- **Change:**
  - **Price column:** set `.price { max-width: 38%; text-align: right; white-space: normal; overflow-wrap: anywhere; }`. In `generate_html.py`, when `price_raw` holds more than one amount (for example `119 kr, takeaway 114 kr`), show the first amount in the price column (`119 kr`) and move the rest to a small second line (`takeaway 114 kr`) under the description, in `--ink-2` at 13 px.
  - **Dish name case:** when a dish name is fully uppercase and longer than 3 characters, render it with `text-transform: none` using a sentence-case version computed in `generate_html.py`: lowercase it, capitalise the first letter, and keep known acronyms (`BBQ`, `IPA`) as they are. Search stays case-insensitive.
  - **Footer credit link:** add `text-decoration: underline; text-underline-offset: 3px`.
  - **`.pick` alignment:** add `align-items: center`.
  - Load `assets/analytics.js` with `defer`.
- **Files:** `templates/index.html`, `generate_html.py`, `tests/test_generate_index.py`.
- **AC:**
  - At 375 px, the Masala first row shows `Murg methi malai` on one line with `119 kr` on the right.
  - Lighthouse desktop Accessibility is 100.
  - Lighthouse reports no render-blocking requests.

### B8 · Browser smoke test in CI (finding #9) — should

- **Change:**
  - Add `tests/test_page_smoke.py`, marked `@pytest.mark.browser`. It uses Selenium with headless Chrome to load `docs/index.html` over `file://` (or a `python -m http.server` fixture) at 375×667 with `?asof=2026-11-13T11:20`.
  - It asserts four things: the pick dock rolls 10 times with `scrollY` unchanged and distinct restaurants for the first N rolls; `Vego`, then a pick, gives a dish with `vego` in `data-tags`; the weekend `asof` hides `#menus` and `#toolbar` **before** any script at the end of the body runs (check `html.classList` right after load); and there are no `SEVERE` console errors.
  - Register the `browser` marker in `pytest.ini`. Skip it automatically when Chrome isn't available.
  - In the workflow, run the test step after `Generate fresh HTML page` (it needs a rendered page): `pytest -q -m browser`. The existing early `pytest -q` keeps excluding it via `-m "not browser"`.
- **Files:** `tests/test_page_smoke.py`, `tests/conftest.py`, `pytest.ini`, `.github/workflows/update-and-deploy.yml`.
- **AC:** passes locally and in Actions. Deliberately breaking `pickForMe` (for example, by making it scroll) makes the test fail.

### B9 · README refresh (finding #12) — should

- **Change:** update the live URL, the schedule (three crons, with Stockholm times for winter and summer), Python 3.12, `python generate_html.py --day friday` for local rendering, `pytest -q` and `RUN_NETWORK=1`, and the contact (`support@jaydigitalstudio.com`). Keep the Fawenah credit. Remove the emoji headings to match the JDS tone. Don't delete any files; that's a Jay decision (Part 4).
- **Files:** `README.md`.
- **AC:** every command in the README runs as written on a fresh clone.

### Test steps for the whole PR

1. `pip install -r requirements.txt && python -m pytest -q` (offline). All pass, with only `network` tests skipped.
2. `python generate_html.py --day friday`. `git diff docs/` shows only the intended template changes.
3. `cd docs && python -m http.server 8000`, then open:
   - `http://localhost:8000/?asof=2026-11-13T11:20` at 375×667 and 1280×800, in SV and EN. Run B2's AC by hand, including keyboard-only and the reduced-motion emulation.
   - `?asof=2026-11-14T10:00` (weekend): B1's AC.
   - `?asof=2026-11-16T07:00` (Monday before the run): the "kommer snart" banner, with the dock usable on Friday's menus.
4. `npx lighthouse http://localhost:8000/ --form-factor=mobile` (weekend state on a weekend, or temporarily set `data-menu-date` to an old date), and again with `?asof=` a weekday. Targets: Performance ≥ 95, CLS ≤ 0.02, and Accessibility 100 on both mobile and desktop.
5. `python -m pytest -q -m browser` (B8).
6. Chrome DevTools → Application → Manifest (B3).
7. Attach screenshots to the PR: 375 px idle, card open after 3 rolls (showing history), the dock at the footer boundary, 1280 px card open, and the weekend state.
8. After merge, on the first weekday (Mon 16 Nov), check `gh run list --workflow update-and-deploy.yml --json createdAt,event,conclusion` and the job summaries. Record the start delay for each cron and the missing reasons in the PR thread.

### Out of scope for this PR (later)

- Week-number validation for scrapers whose pages print `vecka NN` (Bistrot, Kooperativet). This needs per-scraper work.
- Mimolett and Mat & Minnen parsers. Investigate after B6 shows their exact reason. Mat & Minnen probably needs JS rendering.
- An offline service worker (show the last menu with no network).
- `today.json` static export.

---

## Part 4 — Needs Jay's decision

1. **Pick unit.** Recommended: dish (restaurant + dish). The alternative is to keep restaurant-only. B2 assumes dish.
2. **Floating button on desktop.** Recommended: no. The toolbar button is already always visible. Say so if you want the FAB on every size.
3. **`lindholmenlunch.nu`.** It still serves the old Fawenah page with GA4 and AdSense under the same name. Should Fawenah be asked for a redirect to `https://iamjaydesign.com/lindholmen-lunch/`, a takedown, or nothing?
4. **Search Console.** The verification meta tag was removed in #7. Re-verify the new URL (as a URL-prefix property for `iamjaydesign.com/lindholmen-lunch/`) if search traffic matters. This needs a new token from Jay.
5. **Masala and Bombay Bistro rotations.** Masala comes from a hand-made 4-week JSON, and Bombay is computed from the week number. Both always show as "fresh". Options: verify them with the restaurants, label them `Fast meny` / `Set menu`, or keep as is.
6. **LS Kitchen.** Its menu is an image, so it's always "missing". Keep it listed in the missing group, label it `Meny som bild – se webb` / `Menu is an image – see website`, or drop it from the total so coverage reads `9 av 14`.
7. **Kooperativet on Fridays.** The scraper finds Mon–Thu only. Check whether the kitchen is closed on Fridays or the parser is missing the day. If it's closed, show `Stängt fredagar` / `Closed Fridays` instead of counting it as missing.
8. **Public holidays.** Should the page show a "Röd dag – många kök är stängda" / "Public holiday – many kitchens are closed" banner, computed from a static list of Swedish holidays in the repo (no service)?
9. **Repo cleanup.** Can `server.js`, `scrape.js`, `package.json`, `package-lock.json`, `prototype/`, `templates/summary_template.html` (with the unused `generate_lunch_summary()`) and `flyer.html` be deleted? None is used by the pipeline. The root `privacy.html` is still written by `write_privacy()`, so it would need a one-line generator change too. Is `flyer.html` still needed for posters?
10. **Analytics processor.** This stays `[CONFIRM]`. Until it's decided, the pick dock and every other event stay local, with nothing sent.
