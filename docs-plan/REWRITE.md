# Lindholmen Lunch: Clean-Room Rewrite Plan

Status: planning only; no code in this repo changes. Date: 20 Nov 2026. Owner: Jay Digital Studio AB. Builder: Grok 4.7, in a **new** repository.
Implements BUSINESS-PLAN.md D1 (clean-room rewrite now), phase 0 (BP-0a to BP-0f) and the pilot items (BP-1a to BP-1d), following INDEPENDENCE.md option B.

**[ASSUMPTION]** = estimate. **[VERIFY]** = third-party fact to check at its source. **[JAY]** = Jay's decision or action. No company, legal or contact fact is stated here unless it is already in the repo.

---

## 0. Clean-room procedure

The code written by the original creator (Tomas Nilsson, GitHub user Fawenah) has no licence (INDEPENDENCE 0, 1.1). The rewrite must be provably independent of it.

| Role | Who | Opens the old repo? | Produces |
|---|---|---|---|
| Spec author | This planning agent and Jay | Yes, for facts and provenance only | This plan → `SPEC.md` (sections 1–11, appendix A removed) and `SPEC-DESIGN.md` |
| Gatekeeper | Jay | Yes | Approves assets, makes the import commit, merges |
| Builder | Grok 4.7 | **Never** | All code in the new repo |

1. **[JAY]** Create the new repo under a GitHub account or organisation owned by Jay Digital Studio AB (whether an org exists: **[VERIFY]**). Commit the chosen `LICENSE` (section 2) first.
2. **[JAY]** One import commit: `SPEC.md`, `SPEC-DESIGN.md` (design tokens, components, states and copy extracted from PLAN.md part 2 and NEXT-UPDATE part 1, facts and rules only), and the files marked "Yes" in appendix A. `docs/ASSET_MANIFEST.md` lists each file, its SHA-256 and its source commit.
3. The builder gets access to the new repo only: a token or app installation scoped to that repo and a fresh session or environment that has never held the old repo **[VERIFY how Grok 4.7's runtime is scoped]**.
4. Every builder prompt starts: *"Work only in this repository. Do not open, clone, search or fetch `designestjay/lindholmen-lunch`, `Fawenah/lindholmen_lunch`, `lindholmenlunch.nu`, or the HTML source of `iamjaydesign.com/lindholmen-lunch`. Write each adapter by inspecting the restaurant's own live page."*
5. The builder keeps `docs/CLEAN_ROOM.md`: date, task, spec sections used, external URLs inspected, and "No inherited code consulted". Whether this is enough evidence for an AI-built clean room is **[VERIFY in the lawyer review, D11]**.
6. Before each merge, Jay (or a separate agent, never the builder) scans the new repo for strings unique to the old code: regular expressions, selectors, comments, identifiers. The new stack is a different language (3.1), so copying stands out. A hit means revert and redo the task in a new session.
7. If the builder needs a missing fact, it asks Jay, who answers with facts (a URL, a behaviour, a field), never old code.

---

## 1. Goals and non-goals

| # | Goal | Measured by |
|---|---|---|
| G-1 | Correct and on time every weekday | ≥ 10 consecutive weekdays fresh before 09:00 Stockholm (G0) |
| G-2 | Multi-area from day one | A test area needs only new files in `areas/`, `restaurants/` and adapters |
| G-3 | One data contract | Page, screens and chat posts read only `today.json` (+ `sponsor.json` where allowed) |
| G-4 | Revenue surfaces built in | `/screen/`, Slack/Teams posts and sponsor slot pass section 9 |
| G-5 | Free hosting that allows commercial use (D9) | Running cost: domain only, unless Jay approves a paid Umami fallback |
| G-6 | Honest gaps | Missing, closed and wrong-week menus shown as such, never guessed |
| G-7 | Cheap upkeep (2–4 h/week, $20/month cap) | A broken source is a one-adapter fix with a fixture test |

**Non-goals (year 1):** logins; an OAuth Slack app or polls (D10); paid restaurant placement or ranking; office-supplied text on screens (D12); sponsors on screens or paid tiers (D4); AI in the daily pipeline; a native app; scraping aggregators or social media (FOOD-IMAGES B-2).

---

## 2. Licence for the new repository [JAY decides]

| Option | What others may do | Fit |
|---|---|---|
| **Proprietary ("All rights reserved")** | Only view it, if the repo is public **[VERIFY GitHub terms]** | Keeps the product exclusive; can be opened later (an open licence can't be withdrawn) |
| MIT / Apache-2.0 | Anything, including selling the same product (Apache adds a patent grant) | Portfolio fit, weak product fit |
| AGPL-3.0 | Anything, but a hosted modified version must publish its changes | Competitors can still run it |
| FSL-1.1 or BUSL-1.1 | Use except for a competing product; becomes Apache/MIT after a set period **[VERIFY texts]** | Middle ground, less familiar |

**Recommendation: proprietary, private repo.** Check the free GitHub Actions minutes for private repos against ~440 min/month (BP 6.1) **[VERIFY]**; Pages from a private repo needs a paid plan **[VERIFY]**, another reason for the host in 7.1. Separately: menus belong to the restaurants (shown as facts with a link back); Jay's illustrations, copy and brand are all rights reserved; fonts keep their OFL files.

---

## 3. Architecture

### 3.1 Shape and stack

```text
external scheduler ─dispatch─▶ GitHub Actions build: adapters → normalise → validate
                                  → data/<area>/<date>.json → render → deploy ─▶ <domain>/<area>/
external scheduler (every 15 min, weekdays) ─▶ poster reads public today.json → Slack/Teams webhooks
monitor ◀─ start/success/fail pings + dead-man alert      Umami (self-hosted) ◀─ page/screen/sponsor events
```

- **TypeScript on Node.js LTS [VERIFY version]** for pipeline, renderer, browser scripts and poster: one language across build, site and serverless poster, and different from the old Python.
- Static files only at runtime; the only running code is the poster (scheduled function) and Umami.
- Daily JSON is committed under `data/<area>/`; built HTML is deployed as an artifact, never committed.
- All dates use the area's time zone. Core functions take `now` as a parameter; `src/core` never reads the system clock.

Layout: `areas/`, `restaurants/<area>/`, `src/{core,adapters,render,poster}/`, `content/` (copy, dish library, holidays, sponsors), `assets/`, `screens/<area>/`, `schemas/`, `tests/`, `docs/`.

### 3.2 Area config

`areas/lindholmen.yml` → published at `<domain>/lindholmen/`. The umbrella domain is TBD (D2, BP-0f), so the origin is a build setting (`SITE_ORIGIN`), never hard-coded.

| Field | Lindholmen |
|---|---|
| `id` / `slug` | `lindholmen` |
| `name` | `{sv: "Lindholmen", en: "Lindholmen"}` |
| `timezone`, `holidays` | `Europe/Stockholm`, `se` |
| `default_lang` | `sv` (UI SV/EN; menu text stays as published) |
| `restaurants` | Ordered ids (default display order) |
| `times` | `post_default 10:45`, `fresh_deadline 09:00`, `failed_day_cutoff 10:30` |
| `status` | `live`, `preview` or `paused` (paused areas show a notice and get no chat posts, BP 9.2) |

`<domain>/` lists live areas; with one area it is a short landing page.

### 3.3 Menu adapters

An adapter is a **pure function**: (restaurant config, target date, fetched documents) → `AdapterResult`. A shared fetcher does all network access, so tests feed saved documents.

`AdapterResult`: `status` (`fresh`, `closed`, `no_menu_published`, `wrong_week`, `missing`, `link_only`); `reason` (`http_<code>`, `timeout`, `empty`, `parse_error`, `robots_disallowed`, `holiday`); `source_week` (ISO week the page claims, or null); `menu_date`; `dishes[]` (name, description, `price_sek` or null, `price_text`, `scope` day/week, source category); `fetched_at`; `source_url`; content hash.

| Pattern adapter | For pages that… |
|---|---|
| `html-weekdays` | list Mon–Fri under weekday headings (config: URL, selectors, week-marker pattern) |
| `html-fixed` | show the same menu daily (scraped weekly, hash-compared) |
| `rotation` | follow a published multi-week cycle (cycle length, anchor week) |
| `feed-rss` | publish a structured feed |
| `json-endpoint` | load the menu from an endpoint their own page calls (only if the source record allows) |
| `headless` | need a browser and expose no endpoint (Playwright, last resort) |
| `manual` | have no machine-readable menu (restaurant- or Jay-entered file; later BP-3c) |
| `link-only` | can't or mustn't be fetched ("Menu on their site") |

Bespoke adapters only when no pattern fits, with the reason in the PR. **Polite fetcher** (INDEPENDENCE 1.5): honest User-Agent with a contact URL; timeouts (10 s connect, 20 s total **[ASSUMPTION]**); one request per source per run plus one retry after 30 s; honour `robots.txt` and `Crawl-delay`; skip sources already fresh today; no logins, CAPTCHAs or block bypassing; no AI training use.

### 3.4 Per-source terms and robots record

Each `restaurants/<area>/<id>.yml` has a `source` block. **The build fails if an active source lacks one or it is older than 12 months.** `docs/SOURCES.md` is generated from them.

| Field | Meaning |
|---|---|
| `url`, `human_url`, `adapter`, `cadence` | What is fetched, what users see, how, how often (`weekly`, `daily`, `fixed`, `rotation`) |
| `terms_url`, `terms_summary`, `scraping_allowed` | `yes` / `no` / `unclear`; `no` forces `link-only` or `manual` |
| `robots_checked_at`, `robots_allows_path`, `crawl_delay_s`, `ai_signals` | From the live `robots.txt` and headers |
| `permission`, `opt_out` | Restaurant permission (`none/pending/yes/no` + date); `opt_out: true` hides it within 24 h |
| `checked_by`, `checked_at`, `notes` | Facts only, e.g. "shows next week's menu from Friday afternoon" |

### 3.5 Lindholmen restaurants (facts to re-verify, not adapter specs)

From the public sites, the README and Jay's source register (14 Nov 2026), and the pipeline result for Fri 20 Nov 2026.

| Restaurant | Public page | Observed format | 20 Nov |
|---|---|---|---|
| Kooperativet | kooperativet.se | Weekly, week marked; Friday often absent | Missing (empty) |
| District One | districtone.se | Weekly | **Missing (HTTP 404)**: find the new menu location |
| Bombay Bistro | bombaybistro.se/lunch/ | Rotation | Fresh |
| Cuckoo's Nest | cuckoosnest.se/menyer/lunch | Weekly; crawl delay set **[VERIFY]** | Fresh |
| Uni3 World of Food | Compass Group page; Compass publishes a feed | Weekly feed **[VERIFY terms]** | Fresh |
| Miss F | missf.se | Fixed | Fresh |
| Benne Pastabar | bennepastabar.se | Fixed | Fresh |
| LS Kitchen | Plate Impact menu screen (JS app) | Weekly **[VERIFY terms]** | Missing (empty) |
| Bistrot | bistrot.se | Weekly, week marked; shows next week early | **Wrong week** |
| Mimolett | Kvartersmenyn page; old domain redirects to an unrelated site | Link only, inactive | Not shown |
| Oishii | oishii.se/lunchmeny/ | Fixed | Fresh |
| Mat & Minnen | matminnen.se | Closed for lunch since 27 Jun 2025 per Jay's register **[VERIFY]** | Hidden |
| Encounter Asian | tamed.se (JS app; `Crawl-delay: 10`) | Fixed | Fresh |
| Masala Kitchen | masalakitchen.se/lunch/ | Four-week rotation | Fresh |
| Pier 11 | ericssonbynordrest.se (Nordrest) | Weekly | Fresh |

Candidates **[JAY]** (INDEPENDENCE decision 7): Alkemisten, Gansu; The Social only in a "nearby" group (it is in Eriksberg).

---

## 4. Data contract and outputs

### 4.1 `/<area>/today.json` (BP-0c)

Validated against `schemas/today.schema.json`. **A failing build doesn't deploy:** the last good site stays up and an alert fires.

| Field | Notes |
|---|---|
| `schema_version` | 1; additive changes only within a version |
| `area` | `{id, slug, name{sv,en}, timezone}` |
| `date`, `weekday`, `iso_week` | The menu day, in area time |
| `day_type`, `holiday_name` | `weekday`, `weekend`, `holiday`, `eve`, `bridge`; name `{sv,en}` or null |
| `generated_at`, `data_as_of` | ISO 8601 with offset |
| `coverage` | `{fresh, expected, listed}` (`expected` excludes closed and link-only) |
| `restaurants[]` | `id`, `name`, `status` (3.3 plus `stale` = same-day data kept after a later failed fetch), `reason`, `menu_date`, `source_week`, `fetched_at`, `links{website, menu, map}`, `dishes[]` (name, description, `price_sek`, `price_text`, `tags[]`, `illustration`, `scope`), `auto_read: false` |
| `ideas[]` | Dish-library slugs, weekends and holidays only |

**No sponsor data in `today.json`;** it lives in `/<area>/sponsor.json` so screens never load it. Also published: `/<area>/days/<date>.json` (archive, same schema) and `/status.json` (latest health per area).

### 4.2 Area page `/<area>/`

Design and behaviour from Jay's post-takeover work, via `SPEC-DESIGN.md`:

- Server-rendered HTML with all dishes visible without JS; JS adds filters, search, collapse, Pick for me.
- Trust line (date · n of N menus · updated time); diet/cuisine chips (OR per dish); search; results live region.
- Rows: name, up to 3 dishes (matches first), price, text tags, map and website links, "Show all n dishes"; stale and wrong-week variants with the real date; a collapsed "No menu found today" group.
- **Pick for me:** restaurant first, then dish; no repeats until the pool is empty; skips sides and drinks; non-modal card with "Show in list" and recent picks.
- **Weekend ideas:** on weekends and holidays, six seeded dish-library suggestions; Pick for me spins among them. Hidden once a weekday's menus are shown.
- States decided **before first paint**: fresh, partial, wrong day, before update, weekend, holiday, no data, no matches.
- SV/EN in `localStorage`; menu text `lang="sv"`; self-hosted fonts; no third-party requests except Umami; privacy, about and sponsor-policy pages; `robots.txt`, sitemap, Open Graph, manifest scoped to `/<area>/`.
- Dish illustrations: a deterministic classifier (no network, no AI) maps dish text to a dish-library category and diet tags. No confident match means no illustration.

### 4.3 `/<area>/screen/` kiosk (BP-1a)

- **Menus only (D12):** date, restaurants with 2–3 dishes, diet tags, an honest "n menus missing" line. No sponsor, free text, QR or promotion.
- `?office=<slug>` loads public `screens/<area>/<slug>.json`: office name, logo, two brand colours (contrast-checked at build), restaurant set and order, layout, language mode. Logos pending BP 12.2 q5 **[JAY confirm]**.
- 16:9 and 9:16 layouts, readable at ~3 m (dish text ≥ 28 px at 1080p **[ASSUMPTION]**), optional SV/EN rotation.
- Re-fetch every 10 min and just after midnight; on failure keep the last render and show its time. Weekend, holiday, wrong-day and all-missing states.
- No external requests except Umami (`screen_view` with office slug, at most hourly). Works in smart-TV browsers **[VERIFY per customer]**.

### 4.4 Sponsor slot (BP-1d)

- `content/sponsors/<area>.json`: ISO week, dates, name, logo, text ≤ 80 characters, one link, `approved_by`, `approved_at`. Published as `/<area>/sponsor.json` only during its dates.
- Shown **only** on the area page and in free-tier chat posts, always labelled `Annons · Veckans sponsor` / `Ad · This week's sponsor`. Never on screens, paid posts or in Pick for me; never affects order or selection.
- Tests: the screen bundle has no sponsor code or fetch; paid posts have no sponsor line; the page with and without a sponsor differs only in the slot; the label is always present. Category policy (D4, BP 5.4) is enforced by Jay's approval, not code.

### 4.5 Slack and Teams posts (BP-1b/1c, webhooks only)

- Subscriptions live in scheduler secrets or key-value storage, never in the repo: channel type, webhook URL, local time (default 10:45), tier (`free`/`team`/`office`), restaurant set, diet-first filter, language.
- The poster runs every 15 min on weekdays, converts to area time (DST-safe) and posts once per subscription per day (idempotency record).
- Content: date, coverage, highlights by diet, one pick, link with `?src=slack|teams`. Free tier adds the labelled sponsor line and an "Add to your channel" footer.
- No post on weekends and holidays by default. Below 50% coverage at post time: wait up to 30 min, then post with an honest note **[ASSUMPTION]**.
- Slack incoming webhooks **[VERIFY setup for external workspaces]**; Teams via Microsoft's current inbound path (Workflows webhooks as connectors retire) **[VERIFY payload and limits]**. One retry, then reported in health output by internal id only.

---

## 5. Data quirks to handle

| Quirk | Example | Required behaviour |
|---|---|---|
| Weekends | Every week | `day_type: weekend`; Friday behind "Show Friday's menus"; ideas; no post; no alerts |
| Holidays, eves, bridge days | Trettondedag jul, Långfredagen, midsommar, klämdagar | `content/holidays/se.json` (bundle covers 2026–27; builder extends through 2028 from an official source **[VERIFY]**). Holidays: closed state, no alerts. Eves/bridge days: normal runs, misses don't count as failures. |
| Closure periods | Christmas–Trettondagen, July **[ASSUMPTION]** | Date-range switch for expectations; failed-day count paused |
| Next week's menu early | Bistrot, week 47 on Fri 13 Nov | `source_week` ≠ target ISO week → `wrong_week`, never shown as today |
| Last week's menu Monday morning | Weekly pages | Same check; no alert before the second run |
| One day absent | Kooperativet Fridays | `no_menu_published` ("No Friday menu on their site") |
| 404 / moved site | **districtone.se, 404 on 20 Nov 2026** | `missing` + `http_404`; keep the link; issue after 2 weekdays |
| 200 with no menu | Kooperativet, LS Kitchen (20 Nov) | `missing` + `empty`; never an empty card |
| Domain taken over | Mimolett's old domain | Final host after redirects must match the record, else link removed and Jay alerted |
| Long-term closure | Mat & Minnen | `active: false` |
| JS-only menus | LS Kitchen, Encounter Asian | `json-endpoint` if allowed, else `headless` |
| Fixed / rotating menus | Miss F, Benne, Oishii; Bombay Bistro, Masala | `html-fixed` weekly with hash; `rotation` from cycle config |
| "All week" dishes, messy text | Weekly pages | `scope: week`; all-caps → sentence case; several prices (first in `price_sek`); å ä ö é; non-breaking spaces |
| DST | Last Sunday of Mar/Oct | Time-zone database only; tests on both weeks |

---

## 6. Scheduling, health checks and alerts

| Trigger layer | What | Local time |
|---|---|---|
| 1. External scheduler (approved, free) | `workflow_dispatch` via the GitHub API, token limited to the new repo and Actions read/write | ~06:15, ~07:45; gap-fill ~10:30 for `missing`/`wrong_week` only |
| 2. Assistant routine | Already dispatches the old workflow at 08:00 via the API; repoint it at the new repo for the parallel run | 08:00; retire after layer 1 has 10 green weekdays, or keep as backup **[JAY]** |
| 3. GitHub cron | Backup at odd minutes | Same slots |

Scheduler candidates: Cloudflare Workers Cron Triggers or cron-job.org **[VERIFY free limits and commercial terms]**; prefer the same platform as the host and poster (7.1). Runs are idempotent (fresh sources skipped) with a per-day concurrency group.

Each run writes `data/<area>/health/<date>.json` (per-restaurant status and reason, timings, trigger layer) and updates `/status.json`.

| Alert | Rule |
|---|---|
| No run | Dead-man: no success ping by 09:00 on a non-holiday weekday (Healthchecks.io-style free tier **[VERIFY]**) |
| Run failed / deploy blocked | `/fail` ping and GitHub failure email |
| Low coverage | fresh/expected < 70% at 09:30 |
| Broken source | Same restaurant missing or `parse_error` on 2 consecutive weekdays → auto GitHub issue |
| Chat post failed | Not delivered by its time + 45 min |
| Unsafe link | Outbound host changed (5) |

Alerts go to the address Jay reads (support@jaydigitalstudio.com unless Jay chooses another). **Failed day** (BP 6.2, D8): the page or `today.json` lacks the day's menus at 10:30, or < 50% of expected restaurants are fresh. Holidays and closures don't count. Monthly totals in `data/<area>/health/<YYYY-MM>.json`.

---

## 7. Hosting, analytics, privacy (free only, D9)

**7.1 Host and poster.** Recommended: **Cloudflare Pages + Workers** (redirect rules, CI deploys, cron and secrets in one account, private repo OK); commercial use on the free tier **[VERIFY terms and limits]**. Alternatives: Netlify free **[VERIFY]**. GitHub Pages is a fallback only (its terms discourage commercial/SaaS use **[VERIFY]**; private repos need a paid plan). Vercel Hobby is non-commercial **[VERIFY]**: excluded.

**7.2 Umami, self-hosted (D3).** Needs Node and PostgreSQL **[VERIFY]**. Candidates, each checked for limits, commercial use, EU region and database pausing: (a) an always-free EU VM (for example Oracle Cloud Always Free) running Umami and Postgres in Docker **[VERIFY]**; (b) a free PaaS service plus free managed Postgres in the EU **[VERIFY sleep and pause rules]**; (c) fallback paid VM ~50–100 SEK/month **[ASSUMPTION]**, needs Jay's OK. Events: pageview with `src`, `pick_used`, `filter_used`, `search_used` (no text), `outbound_click`, `lang_switch`, `screen_view`, `sponsor_view`, `sponsor_click`. No cookies or stored identifiers.

**7.3 Privacy.** Data: Umami aggregates, host logs, webhook URLs and customer contacts (private, outside the repo). Jay's privacy page (appendix A) is updated to name Umami and its host and region, the static host, the scheduler and the payment provider. Organisation number and postal address stay placeholders until Jay supplies them **[JAY]**. Lawyer review before the first sale (D11).

---

## 8. Deterministic tests

| Rule | How |
|---|---|
| No live data | The runner blocks the network; any fetch in unit or fixture tests fails |
| No dependence on today | Core takes `now`; browser scripts accept an `asof` override only in test builds; CI also runs with `TZ=UTC` and a non-European `TZ` |
| Fixtures | Captured by the builder from live restaurant pages, trimmed to the menu, with URL and date. **Never** from the old repo. Fresh-week fixture per adapter, plus wrong-week/empty where relevant |
| Golden outputs | Fixed fixtures + fixed `now` → committed `today.json` and HTML |
| Calendar | Weekend, each 2026–27 holiday, an eve, a bridge day, Monday before first run, Friday with next week's menu, both DST weeks |
| Browser | Playwright on built output at 375/768/1440 px and both screen layouts, fixed `asof`, seeded random: states, filters, Pick for me, ideas, no sponsor on `/screen/` |
| Live canary | Separate daily non-blocking job reporting source drift; never gates merges |

---

## 9. Phased build plan (PR-sized milestones)

Grok rules (INDEPENDENCE 5): one task = one narrow PR; fixture tests, at most one live fetch per task; stop after two failed fix-up rounds; update `CLEAN_ROOM.md` each PR. Dates **[ASSUMPTION]**, back-planned from **G0 = 29 Jan 2027**: 10 green weekdays means the pipeline must be live by **Thu 14 Jan**.

| ID | Milestone | Acceptance criteria | Target |
|---|---|---|---|
| M0 | **[JAY]** Licence, repo name/owner, host and scheduler accounts, import commit | Repo has `LICENSE`, `SPEC.md`, `SPEC-DESIGN.md`, `ASSET_MANIFEST.md`; builder token scoped to it | 27 Nov |
| M1 | Scaffold: TS, lint, tests with network blocked, CI, injected clock, config loaders + schema | CI green; invalid config fails clearly; a test proves fetches fail | 2 Dec |
| M2 | `today.json` schema, normaliser, status, holiday and week logic | Golden file validates; calendar cases (8) pass | 4 Dec |
| M3 | Polite fetcher, adapter framework, source-record check, fixture-capture command | Missing/old source record fails the build; robots disallow → `robots_disallowed` | 8 Dec |
| M4 | Area page: tokens, rows, filters, search, states, SV/EN, privacy/about/sponsor-policy pages | Golden HTML; browser tests at 3 widths; works without JS; Lighthouse a11y ≥ 95 **[ASSUMPTION]** | 11 Dec |
| M5 | Pick for me, weekend ideas, classifier and illustrations | Seeded tests: no repeats until empty, sides skipped, idea mode on a fixed Saturday | 16 Dec |
| M6a–d | Adapters, 3–4 restaurants per PR: (a) weekly HTML with week check; (b) feed and fixed; (c) rotations; (d) JS apps and District One's new source | Per restaurant: fixture test, source record, one live run fresh or a documented `link-only`/`manual` decision | 18 Dec–13 Jan |
| M7 | Workflow, deploy to host preview URL, health files, pings, alerts | Forced failure alerts; invalid schema blocks deploy and keeps the last site | 18 Dec |
| M8 | External scheduler; repoint assistant routine | Dispatched runs start ≤ 5 min after trigger on 3 weekdays | 8 Jan |
| M9 | Umami live (BP-0d) | Events visible; privacy page updated | 13 Jan |
| M10 | `/screen/` (BP-1a) with a demo office | Both layouts on a real screen **[JAY]**; no sponsor fetch in bundle; refresh/failure tested | 15 Jan |
| M11 | Slack and Teams poster (BP-1b/1c) | Posts to Jay's test channels; no double posts; DST-correct with fixed time | 20 Jan |
| M12 | Sponsor slot (BP-1d) | Tests in 4.4 pass; empty file renders nothing | 22 Jan |
| M13 | Parallel run vs old site, daily comparison | 10 consecutive weekdays fresh before 09:00 (from 14 Jan); coverage ≥ old site | 14–28 Jan |
| M14 | Cutover (10) | Section 10 checks pass; old pipeline off | by 29 Jan (G0) |

Christmas–New Year (≈ 21 Dec–6 Jan) has few menus: good for holiday-state tests, poor for adapter work. **Slip rule:** if M13 isn't green by 29 Jan, G0 moves and no pilots start. If the rewrite isn't live by **31 Mar 2027**, stop revenue work (BP 10) and keep only the free area page.

---

## 10. Migration and cutover

Until the umbrella domain exists the new site runs only on the host's preview URL, unannounced. Register the domain by **8 Jan 2027** **[ASSUMPTION]** so users move once.

| Old (`https://iamjaydesign.com/lindholmen-lunch/…`) | New |
|---|---|
| `/`, `/index.html`, `/preview.html` | `<domain>/lindholmen/` |
| `/privacy.html` | `<domain>/privacy/` |
| `/manifest.webmanifest` | Kept, `start_url` pointing to the stub **[VERIFY installed-app behaviour]** |
| `/sitemap.xml` | Removed; new `<domain>/sitemap.xml` |
| `?src=`, `?asof=`, `#…` | Preserved by the stubs |

GitHub Pages can't send server 301s **[VERIFY]**, so each old path gets a new tiny stub page (`rel="canonical"`, meta refresh, `location.replace()` keeping query and fragment), written fresh for Jay.

1. M13 met; domain verified, HTTPS on; `robots.txt`, sitemap and link previews checked.
2. Early morning: publish the stubs from the old repo, disable its scheduled workflow, stop the assistant routine's old-repo dispatch.
3. Verify every old URL lands correctly with its query string; `today.json` and `/screen/` load on the new domain.
4. Update MARKETING.md links (D13 note) and the old README.
5. Keep the old repo intact 30 days for rollback, then archive it (stays public, so stubs keep working free) rather than make it private (Pages would need a paid plan **[VERIFY]**) **[JAY]**. Keep stubs ≥ 12 months **[ASSUMPTION]**.
6. `lindholmenlunch.nu` isn't Jay's: no redirect.

**Rollback:** re-enable the old workflow and restore the pre-stub files (minutes); the new site keeps running.

---

## 11. Risks and open questions

| Risk | Likelihood / impact **[ASSUMPTION]** | Mitigation |
|---|---|---|
| Clean-room contamination | Low / high | Section 0; different language; gatekeeper scan; lawyer review (D11) |
| Rewrite misses G0 | Medium / high | Small milestones; 31 Mar stop rule |
| Sources break (like districtone.se) | Certain / medium | Pattern adapters, 2-day issues, link-only fallback, honest UI |
| Free tiers change | Medium / medium | Portable static output and cron specs; monthly check |
| Scheduler token leak | Low / medium | One-repo, Actions-only token; yearly rotation |
| Teams webhook path changes | Medium / medium | Verify before selling Teams; Slack first |
| Sponsor on a screen or paid tier | Low / high | Separate `sponsor.json`; tests in 4.4 |
| Builder runtime can't be sandboxed | Medium / medium | Prompt rule, scoped token, fresh environment, log, scan |

**Open questions for Jay**

1. **Licence:** proprietary (recommended), MIT/Apache-2.0, AGPL-3.0 or FSL/BUSL? Private or public repo?
2. **New repo name and owner:** a Jay Digital Studio AB GitHub organisation and a neutral working name until the brand exists (renamed repos redirect **[VERIFY]**).
3. **Umbrella name and domain** (D2): needed by ~8 Jan for a single cutover.
4. **Host and scheduler:** Cloudflare Pages + Workers after **[VERIFY]**?
5. **Umami host**, and is a ~50–100 SEK/month fallback acceptable?
6. **Assistant routine** after cutover: retire or keep as backup?
7. **Restaurant scope:** Alkemisten, Gansu, a "nearby" group, Mimolett as link only?
8. **Asset approvals:** approve appendix A and resolve its **[VERIFY]** rows.
9. **Old repo at cutover:** archive (recommended) or private?

---

## Appendix A. File provenance (for Jay; remove before handing the spec to the builder)

Method: `git log --follow` per file on `main` at `2f2ddb5`, ignoring automated data commits. **Jay-era** = commits from Jay's account (`designestjay` / `JAY`) on or after **13 Nov 2026** (CI fix PR #1 on 13 Nov, rebuild PR #6 on 14 Nov) **[VERIFY Jay counts 13 Nov as post-takeover]**. Commits by "Justbob Fawenah" / "Tomas Nilsson" (May–Jun 2025) are the original creator's. Jay's June 2025 commits edited the inherited code base, so files they touched count as **inherited or mixed**. Most Jay-era commits are co-authored by a Cursor agent; copyright in AI-assisted output is **[VERIFY in lawyer review]**, though it raises no third-party claim.

A line-level comparison found no shared lines (> 20 characters) between Jay-era `templates/index.html` and inherited `templates/summary_template.html`, and only `<meta charset>` in common between the Jay-era and inherited privacy pages. Both are treated as Jay rewrites.

| Files | Classification | Carry over? |
|---|---|---|
| `docs-plan/*.md` | Jay-era | Facts and design rules only, via `SPEC.md`/`SPEC-DESIGN.md` (the files cite old paths) |
| `docs/assets/fonts/*` incl. OFL texts | Third-party OFL, added Jay-era | **Yes** |
| `docs/assets/og.png`, `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, `apple-touch-icon.png` | Jay-era | **Yes** for the Lindholmen area; replace with umbrella brand later |
| `docs/assets/dishes/*.svg` (21) | Jay-era (PR #10) | **Yes [VERIFY]** how they were made and the tool's commercial terms |
| `data/dish_library.json` (50 categories, Jay's SV/EN texts) | Jay-era | **Yes** |
| `data/dish_taxonomy.json` | Jay-era; 60 terms also appear in inherited `data/food_tags.json` (common dish words) | **[VERIFY]** Carry slugs and names only; builder writes new keyword lists |
| `data/holidays_se.json` (2026–27) | Jay-era, factual | **Yes**, re-checked against an official source |
| `templates/index.html` | Jay-era rewrite; scripts read the inherited data shape | Tokens, copy and behaviour via `SPEC-DESIGN.md`; file itself **no** |
| `templates/privacy.html` | Jay-era rewrite | **Yes** (text and structure), updated per 7.3 |
| `docs/assets/analytics.js`, `docs/manifest.webmanifest` | Jay-era | Analytics: behaviour only (Umami replaces it). Manifest: **yes**, as reference |
| `utils/{restaurants,scrape_health,sources,scraper_issues,week_guard,holidays,dish_category,dish_svg}.py`, `data/sources.json`, `data/image-queue.json`, tests and fixtures added 13–20 Nov, `pytest.ini`, `.github/workflows/preview.yml` | Jay-era but built around the inherited pipeline, or copies of restaurant pages | **No** (source facts are already in 3.5) |
| `main.py`, `generate_html.py`, `scrapers/*` (15 scrapers, `base.py`, `__init__.py`, `masala_lunch_all_weeks.json`), `utils/{utils,annotate_food_types,__init__,UNUSUED_ocr_masala_svgs}.py`, `tests/__init__.py`, the 12 `tests/test_<restaurant>.py` first added in 2025, `tests/fixtures/friday_page_lunch_data.json`, `templates/summary_template.html`, `flyer.html`, `requirements.txt`, `.gitignore`, `README.md`, `data/food_tags.json`, `data/restaurant_links.json`, `docs/sitemap.xml` | Inherited or mixed | **Never** |
| `docs/index.html`, `docs/preview.html`, root and `docs/privacy.html`, `data/lunch_data_*`, `data/scrape_meta_*`, `data/scraper_status_history.json`, `data/issue_actions.json` | Generated by the mixed pipeline | **No** |
| `scrape.js`, `server.js`, `package*.json`, `prototype/*`, `docs/service-architecture.md`, `.github/workflows/update-and-deploy.yml` | Jay, June 2025, before takeover; `scrape.js` came from a "convert Python project to Node.js" commit, possibly derived from inherited scrapers **[VERIFY]** | **No** (not needed) |
