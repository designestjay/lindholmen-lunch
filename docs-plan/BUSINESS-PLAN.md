# Lindholmen Lunch — Business Plan

Status: planning document only. No site code is changed by this PR.
Date: 20 Nov 2026. Owner: Jay Digital Studio AB (Gothenburg), solo operator.
Builds on: `docs-plan/PLAN.md` (Part 3: revenue options R1–R8, 90-day roadmap, metrics, legal notes 3.6) and `docs-plan/MARKETING.md` (unmerged, branch `cursor/marketing-plan-22ef`, PR #4). This document references those by ID instead of repeating them. It also leans on `docs-plan/INDEPENDENCE.md` (unmerged, PR #5) for the code-licence question.

Conventions:

- **[ASSUMPTION]** marks every number, price or market claim that has not been verified.
- **[VERIFY]** marks a fact about a third party (platform terms, organisation, area) that must be checked at its source before it is relied on.
- Prices are in SEK, excluding VAT (exkl. moms).

### Jay's decisions this plan is built on (20 Nov 2026)

1. **Goal:** a product that can expand to other areas and cities, not only a portfolio piece.
2. **Time:** Jay spends 2–4 hours a week. An AI assistant does most build, ops and marketing legwork. Jay approves, sells and sends.
3. **Revenue lines:** (a) paid B2B office screens and Slack/Teams daily posts (PLAN R3 + R4); (b) a weekly sponsor slot (PLAN R2).
   **Not chosen:** restaurant featured spots (R1 paid tier) and display ads (R7). Restaurant listings and picks stay neutral and unpaid.

---

## 1. Thesis

Every office area has the same 11:00 question, "var äter vi idag?", and the answer is scattered across restaurant websites. Lindholmen Lunch already answers it for one area automatically, at almost zero running cost. The individual luncher won't pay for that, but **the employer will pay to put the answer where the team already is**: on the lunch-room screen and in the team's Slack or Teams channel. A **weekly sponsor slot** sells the same local, office-worker audience to employers and local services, without touching the neutrality of the menus. The product grows by **adding areas, not features**: each new area is a config file, a set of menu adapters and a few local B2B customers. It is worth expanding only if one area proves that (1) the morning update is reliable, (2) offices pay, and (3) the work fits in Jay's 2–4 hours a week. This plan is built around testing exactly those three things before spending more.

---

## 2. Where things stand (facts from the repo, 20 Nov 2026)

These facts shape the plan. Anything that blocks charging money is marked **blocker**.

| Area | Fact | Source | Consequence |
|---|---|---|---|
| Coverage | 15 scrapers are configured. On the five weekdays 16–20 Nov, 10–11 restaurants were fresh and 1–3 were missing each day (for example on 20 Nov: Kooperativet empty, District One HTTP 404, LS Kitchen empty). | `main.py` `SCRAPERS`; `data/scrape_meta_*.json` | Roughly 13 restaurants in practice. Paid screens need coverage to be reliably high, and need missing restaurants to be shown honestly. |
| **Timing (blocker)** | The cron fires at 05:07, 06:37, 08:07 and 09:37 UTC, but GitHub starts scheduled runs late, and later every month: about 06:40 UTC in August, 10:40–14:30 in September and October, and 13:30–19:50 in November. On 20 Nov the only morning update was a manual `workflow_dispatch` at 08:06 UTC. | `gh run list --workflow update-and-deploy.yml` | A paid screen or a 10:45 Slack post cannot depend on GitHub's cron. An external trigger is required before any pilot (PLAN P-1 fallback). |
| **Code licence (blocker)** | The repo has no `LICENSE`. Most scrapers and utilities were written by the original author (Fawenah), whose README says "educational and personal use". | INDEPENDENCE.md 1.1 | Do not charge money until there is a written licence or a clean-room rewrite (INDEPENDENCE decision 1). |
| Name and domain | The live site is `https://iamjaydesign.com/lindholmen-lunch/`. `lindholmenlunch.nu` still serves the original creator's site. MARKETING.md assumes the `.nu` domain. | `docs/sitemap.xml`, canonical tag; NEXT-UPDATE Part 4 q3 | An expandable product needs its own brand and domain (section 7, Q2). MARKETING.md's URLs and QR codes must be updated before printing. |
| Analytics | Cookieless `assets/analytics.js` is in place, but `data-endpoint` is empty, so nothing is measured. The old GA4 data very likely belongs to the original creator. | `docs/index.html`; INDEPENDENCE decision 4 | **There is no traffic baseline.** Sponsor pricing cannot be justified until analytics has run for at least 4 weeks. |
| Product | The site is static (GitHub Pages), bilingual SV/EN, and has "Pick for me" and weekend meal ideas. There is no `today.json`, no `/screen/` view and no chat integration yet. | `templates/index.html` | Everything B2B reads from a static `today.json`. That file is the first build item. |

---

## 3. Customers: who pays and who uses

| Line | Buyer (signs, pays) | User (sees it daily) | Why the buyer cares | Budget it comes from **[ASSUMPTION]** |
|---|---|---|---|---|
| Office screen | Office or workplace manager; at small companies the CEO or an operations lead | Everyone in the lunch room or reception | A useful, good-looking screen that needs no updates from them; one less "where do we eat" question | Office running costs or facilities |
| Building or reception screen | Property owner, building manager, coworking operator **[VERIFY who runs lobby screens at Lindholmen]** | Tenants and visitors | A tenant service that costs little and looks local | Tenant services or marketing |
| Slack/Teams post | Team lead or engineering manager (small plan); office manager or IT for company-wide (bigger plan) | The team in a `#lunch` channel | It replaces the daily lunch thread and keeps the team eating together | Team budget, often on a company card |
| Weekly sponsor slot | HR or employer-branding lead (recruiting), local businesses (gyms, services, events) | All site visitors, plus free-tier Slack/Teams posts | Reach local office workers and students in a calm, trusted, local channel | Recruitment marketing, local marketing |

Primary target for the first 6 months: **office managers at Lindholmen companies that have a lunch room but no in-house restaurant** (they are buyer and champion in one person), and **team leads in Jay's existing network** for Slack and Teams. HR and employer branding is the main sponsor buyer. **[ASSUMPTION]** to validate in the first 10 conversations (MARKETING 1.5).

---

## 4. Value proposition per line

**A. Office screen (`/screen/`)**: "Today's lunch around you on the lunch-room screen. It updates itself every weekday morning." It works in any browser-based screen (smart TV browser, signage player, a small computer behind the screen) **[VERIFY with each office's hardware]**. It shows large type, today's restaurants with 2–3 dishes each, diet tags, and walking time if added. The paid tiers add the company's logo, their own canteen or fika note, and a chosen restaurant subset. No login and no IT project: it is a URL.

**B. Slack/Teams daily post**: "The lunch thread, done for you, at 10:45." One message per weekday in a chosen channel, with today's highlights by diet, a "Pick for me" suggestion and a link. Setup is pasting one webhook URL; it reads no messages and stores no employee data.

**C. Weekly sponsor slot**: "One week, one sponsor, in front of the people who work at Lindholmen." One clearly labelled `Annons` slot on the site, and one line in free-tier posts, for Monday to Friday. Exclusive: one sponsor per area per week. Neutrality rule: the sponsor never changes which restaurants appear, their order, or the picks.

What none of the lines sells: restaurant placement, ranking or paid picks (Jay's decision 3).

---

## 5. Pricing and packaging (every number is [ASSUMPTION])

Principles: few tiers; annual billing as the default, because invoicing 99 SEK a month costs more admin than it earns; a free tier only where it spreads the product (chat); paid tiers are ad-free; the first 5 customers get a founding price locked for 12 months.

### 5.1 Office screens

| Tier | Price per month (billed yearly) | What's included |
|---|---|---|
| Pilot | 0 SEK for 4 weeks | One screen, standard view, success criteria agreed up front (6.2) |
| **Screen** | **290 SEK** per screen | Standard area view, auto-refresh, office name, SV/EN, no ads |
| **Screen Plus** | **490 SEK** per screen | Logo and colours, own canteen or fika line (sent by email, entered by the assistant), chosen restaurants, a custom message line |
| **Building** | **990 SEK** for up to 5 screens | For receptions, property owners and coworking: Plus features on every screen, plus a tenant notice line |

Founding price: −30% for the first 12 months for the first 5 customers. Monthly billing, if offered at all, costs +20%.

### 5.2 Slack and Teams posts

| Tier | Price per month (billed yearly) | What's included |
|---|---|---|
| **Free** | 0 SEK | 1 channel, standard 10:45 post, carries the week's sponsor line and a small "Add to your channel" footer |
| **Team** | **99 SEK** per workspace | Up to 3 channels, choose post time, diet filters (for example vego first), no sponsor line |
| **Office** | **390 SEK** per company | Unlimited channels, Slack and Teams, canteen menu line, the company's own lunch spots added, later a "where are we eating?" poll (Phase 3) |

### 5.3 Bundle

**Office pack: 590 SEK per month** (1 Screen Plus + Office chat). This is the default offer to office managers, because one buyer then gets both surfaces.

### 5.4 Weekly sponsor slot: rate card

| Item | Price **[ASSUMPTION]** | Notes |
|---|---|---|
| Launch rate, 1 week (Mon–Fri) | **1,500 SEK** | Until at least 8 weeks of analytics exist |
| Standard rate, 1 week | **2,500 SEK** | Only after the audience gate in 8 is met |
| 4-week pack | **7,500 SEK** at standard rate (−25%) | Fits employer-branding campaigns |
| Report | Included | Views of the slot, clicks, and clicks by `src` (site, Slack, Teams); aggregate only |

What the sponsor gets: one `Annons · Veckans sponsor` line or card on the site (logo, max 80 characters, one link), plus one line in every free-tier Slack/Teams post that week. Paid screens and paid chat tiers never carry sponsors.

Sanity check against reach: 2,500 SEK a week only makes sense if the slot is seen by a meaningful local audience. A simple floor: `price ≈ weekly slot views × local CPM`. Example: 3,000 views at a 300 SEK CPM gives 900 SEK, which shows that the premium is for exclusivity and local targeting, not volume. **Re-price after 8 weeks of real data.** The formula, the view count and the CPM are all [ASSUMPTION].

Sponsor policy (draft, Jay decides): it must be clearly labelled (8.3). Excluded categories: alcohol, gambling, tobacco and nicotine, political or religious messages, and any restaurant or food-delivery service listed in or competing with the area (protects neutrality, open question Q4). Copy is approved by Jay, and Jay can refuse any sponsor without giving a reason.

### 5.5 What 12 months at Lindholmen could look like

| Scenario | Screens | Chat (paid) | Sponsor weeks sold / year | MRR (month 12) | Year-1 revenue |
|---|---|---|---|---|---|
| Conservative | 3 × 290 | 2 × 99 | 8 × 1,500 | ~2,100 SEK | ~15–20k SEK |
| Base | 8 (average 390) | 6 (average 200) | 20 × 2,000 | ~7,600 SEK | ~50–70k SEK |
| Upside | 20 (average 420) | 15 (average 250) | 35 × 2,500 | ~19,400 SEK | ~130–170k SEK |

All counts, prices and sell-through rates are **[ASSUMPTION]**. Year-1 revenue is lower than 12 × MRR because customers arrive gradually. The point of the table: **one area probably supports a side income, not a business**. Expansion (section 9) is what changes the ceiling, which is why the per-area cost has to stay small.

---

## 6. Unit economics and running costs

### 6.1 Cash costs per month (all [ASSUMPTION] until invoiced)

| Item | Cost | Notes |
|---|---|---|
| Hosting | ~0 SEK | GitHub Pages today. **[VERIFY]** GitHub's terms say Pages is not meant for running an online business or SaaS; check whether paid screens on Pages are acceptable, or plan a move to a static host whose free or low tier allows commercial use. |
| Scraping (GitHub Actions) | 0 SEK | Free for public repos. If the repo goes private (for example a clean-room rewrite), about 4 runs × 22 weekdays × ~5 min ≈ 440 min/month, likely within the free private quota **[VERIFY current quota]**. |
| Reliable scheduler (trigger + chat posts) | 0 SEK | A free-tier cron on a serverless platform **[VERIFY limits and commercial-use terms]** |
| Analytics (EU, cookieless) | 0–120 SEK | Depends on vendor (INDEPENDENCE decision 4) **[VERIFY prices]** |
| Domain(s) | ~15–30 SEK | ~150–350 SEK/year per domain |
| AI assistant (Cursor on-demand) | **≤ ~$20/month cap** (≈ 200 SEK **[ASSUMPTION exchange rate]**) | The hard budget for build and ops agent runs. See 6.3. |
| Payments | ~1.5–3% per card payment, or 0 with invoice | **[VERIFY]** provider fees; invoices through Jay Digital Studio AB's existing accounting |
| **Total** | **~250–500 SEK** | Marketing print and fika are one-offs, budgeted in MARKETING 6.6 |

### 6.2 Per-customer economics

- **Marginal cost per screen or chat customer is close to 0 SEK.** Every customer reads the same `today.json`.
- **The real cost is Jay's time:** about 1–2 h to sell and set up a customer (email, short demo, config, invoice), then about 10 min a month for support **[ASSUMPTION]**.
- **Cash break-even:** about 2 Screen customers.
- **Time break-even:** 2–4 h/week is about 9–17 h/month. At an internal rate of, say, 1,000 SEK/h **[ASSUMPTION, Jay to set]**, that is ~9–17k SEK/month of opportunity cost. That is roughly the Base-to-Upside MRR in 5.5. **Lindholmen alone pays for Jay's time only in the upside case.** This is the strongest argument for keeping the per-area effort low and expanding only through gates.
- Pilot to paid: a 4-week pilot with agreed success criteria (see below). Conversion ask in week 3. Invoice yearly up front.

Pilot success criteria agreed with the customer (template): the screen or post was up on ≥ 18 of 20 weekdays before 10:30; the menus were correct when spot-checked; and at least N people (the customer's estimate) used it. If met, the customer converts at the founding price.

### 6.3 Working within the $20/month assistant cap

The cap is a real constraint on "AI does the legwork". Rules:

1. **Build in small, planned PRs** (this repo's style). Prefer one well-specified task per run over open-ended runs.
2. **Ops runs are cheap and scheduled:** weekly KPI report, weekly coverage check (MARKETING B13, B14). Avoid daily agent runs. Daily work (scraping, posting) is plain code, not an agent.
3. **No AI in the daily pipeline** unless the cost per call is known and capped (section 9.2, generic adapters).
4. If a month hits the cap, the order of priority is: fix broken scrapers for paying customers, then customer setup, then marketing drafts, then new features.

---

## 7. Go-to-market at Lindholmen (2–4 h/week)

MARKETING.md covers audience channels (QR, restaurants, LinkedIn, SEO, launch week 11–15 Jan 2027). This section adds only the **B2B sales motion** on top of it.

### 7.1 Jay's weekly time budget

| Block | Time | What Jay does | What the assistant prepares |
|---|---|---|---|
| Approvals | 30 min | Approve drafts, posts, configs, invoices | Everything, batched once a week (MARKETING 4.2) |
| Sales | 60–90 min | Send ≤ 5 individually written emails from Gmail drafts; 1 short demo or call; reply to leads | Company list from public pages, drafts, demo link with the prospect's name on the screen view (MARKETING B1, B2, B9) |
| In person | 0–60 min | One walk-in or one local event every other week (reception, office, LSP event **[VERIFY schedule]**) | Route, leave-behind, printed QR |
| Ops review | 15–30 min | Read the weekly health and KPI report, decide fixes | Report, fix PRs (MARKETING B13, B14) |
| **Total** | **~2–3.5 h** | | |

### 7.2 Sales sequence

1. **Warm first (Weeks 1–4 after Gate 0):** Jay lists the people he already knows at Lindholmen companies (number only in this plan, Q8). Each gets a personal note offering a free 4-week pilot of the Office pack.
2. **Public B2B list (from Week 3):** companies within ~10 minutes' walk, from public pages only, approved row by row by Jay (MARKETING B1, B2, 4.4 GDPR notes). ≤ 5 emails a week.
3. **Channel partners:** ask Lindholmen Science Park and building receptions for a reception-screen pilot and a mention to tenant office managers (MARKETING T-LSP) **[VERIFY routes]**.
4. **Product-led loop:** every free Slack/Teams post has an "Add to your channel" footer, and every screen has a small QR code "Get this for your office". Installs feed the paid ask.
5. **Sponsors (after the audience gate):** start with employers in Jay's network that are recruiting, then local services. One sponsor email per week at most.

Funnel to plan against **[ASSUMPTION]**: 30 companies contacted → 10 replies → 5 pilots → 2–3 paying within 3 months.

### 7.3 Sales kit (assistant drafts, Jay approves)

A one-page offer (SV and EN) with the tiers from 5; a live demo URL per prospect (`/screen/?office=demo-<company>`, removed after the pilot); a pilot agreement (half a page: what's provided, dates, success criteria, no cost, how to convert or stop); short terms of service for paid tiers (8.3); a sponsor one-pager with the policy from 5.4.

---

## 8. Product roadmap for revenue

All items are small and static-first. Each phase is a set of PRs following the PLAN/NEXT-UPDATE style. IDs (`BP-*`) are new.

### Phase 0: Foundation (must be done before any pilot)

| ID | Item | Done when |
|---|---|---|
| BP-0a | **Licence path decided and executed** (INDEPENDENCE decision 1: written licence or clean-room rewrite) | Written licence received, or the new repository serves the site |
| BP-0b | **Reliable trigger:** an external scheduler calls `workflow_dispatch` at about 06:30 and 08:30 local time; the GitHub cron stays only as a backup | 10 consecutive weekdays with fresh data before 09:00 Stockholm time (`gh run list` plus `scrape_meta.scraped_at`) |
| BP-0c | **`today.json`** published next to `index.html` on every build: date, scraped_at, per-restaurant status (fresh, missing, closed), dishes, tags, links | Schema documented; a test validates it; the page and later integrations read only this file |
| BP-0d | **Analytics live** (vendor decided), with `src` on every channel (MARKETING 6.2) and new events `screen_view`, `sponsor_view`, `sponsor_click` | Events visible in the dashboard; privacy page updated |
| BP-0e | **Health alert** when coverage is low or data is late (PLAN P-3), sent somewhere Jay actually reads | A forced failure in a test branch triggers the alert |

### Phase 1: Pilot-ready (target: in place for launch week, 11–15 Jan 2027)

| ID | Item | Notes |
|---|---|---|
| BP-1a | **`/screen/` kiosk view** | Static page, reads `today.json`, reloads about every 10 min and at the day change, 16:9 and portrait layouts, large type, SV/EN, wrong-day and weekend states (reuse the existing logic), office config from `screens/<office>.json` (name, logo, colours, subset, message). No secrets in config: it is a public static file. |
| BP-1b | **Slack post via incoming webhook** | The customer creates a webhook for their channel and sends the URL to Jay. The URL is stored as a secret in the scheduler, never in the repo. The scheduler reads `today.json` at the chosen time and posts. **[VERIFY]** current Slack incoming-webhook setup for external workspaces. |
| BP-1c | **Teams post via webhook** | **[VERIFY]** Microsoft's current supported way to post into a channel from outside (Office 365 connectors have been retiring in favour of Workflows webhooks). Same flow as BP-1b. |
| BP-1d | **Sponsor slot component** | `data/sponsor.json` (week, name, logo, text, link, start and end dates). Rendered with an `Annons` label on the site and in free-tier posts. Empty means nothing is rendered. |
| BP-1e | **Customer register** | A private sheet or private repo file: customer, tier, channels, start date, renewal date. Never in the public repo. |

### Phase 2: Paid (after Gate 1)

| ID | Item | Notes |
|---|---|---|
| BP-2a | Screen Plus features: canteen or fika line, custom message, chosen restaurants | Customer emails the content; the assistant updates the config |
| BP-2b | Billing: yearly invoice from Jay Digital Studio AB, or payment links | Q6 |
| BP-2c | Monthly customer and sponsor report: uptime before 10:30, views, clicks (aggregate) | Generated by the weekly ops run |
| BP-2d | Public status line (`status.json`, or the trust line on the screen) | Honest when a restaurant is missing |
| BP-2e | Terms of service and a sponsor policy page | 8.3; lawyer review if budget allows (Q13) |

### Phase 3: Scale (after Gate 2, mostly for expansion)

| ID | Item | Notes |
|---|---|---|
| BP-3a | **Area config refactor** (PLAN 3.2): `areas/<slug>.yml`, `/<slug>/`, `/<slug>/today.json`, `/<slug>/screen/` | Lindholmen becomes area #1 |
| BP-3b | **Generic adapters** (9.2) | Reduces cost per restaurant |
| BP-3c | **Free restaurant menu submission** (form or sheet) | For coverage only, never paid placement |
| BP-3d | "Add to Slack" app (OAuth install) and a "where are we eating?" poll | Needs a small serverless endpoint and Slack's distribution rules **[VERIFY]**. Only if webhook setup turns out to be a sales blocker. |
| BP-3e | Area health dashboard: coverage, timing and broken scrapers per area | One view for the weekly ops run |

---

## 9. Expansion model: other areas and cities

### 9.1 What makes an area viable (score before building anything)

| Criterion | Threshold **[ASSUMPTION]** | How to check |
|---|---|---|
| Restaurants with a weekly lunch menu published online | ≥ 10 within about 10 minutes' walk | The assistant counts them from public pages and records the format (HTML, PDF, image, Instagram only) |
| Share in a machine-readable format (HTML or text PDF) | ≥ 70% | Same count |
| Office density without in-house restaurants | Enough to list ≥ 30 target companies | Public company pages and building tenant lists **[VERIFY per area]** |
| A local foothold | ≥ 1 warm contact or channel partner | Jay's network, the local science park or business association |
| Competition | No local aggregator already integrated into offices | The assistant checks existing aggregators and listings in the area **[VERIFY per area]** |
| Build and run cost | ≤ 2 days of assistant build and ≤ 30 min/week of upkeep | Estimated from the format mix |

### 9.2 How scrapers scale

Today, one class per restaurant (about 50–180 lines each, PLAN 3.2). That cost grows linearly with every new restaurant, and sites break regularly (1–3 missing a day in the 16–20 Nov sample). To keep the per-area cost low:

1. **Pattern adapters before bespoke code:** many restaurant sites share a layout (weekday headings in HTML, a weekly PDF, a shared menu platform). Write one configurable adapter per pattern, then configure each restaurant with a URL and selectors. Measure: the share of restaurants handled by config only.
2. **Restaurant self-submission** (BP-3c): free, for menus that are images or Instagram-only.
3. **AI-assisted extraction as a fallback only:** text, PDF or image in, structured dishes out. It must have a per-call cost cap and a monthly budget, and it must always be marked "auto-read" in `today.json`. Not in the daily path until its cost is measured against the $20 cap (6.3).
4. **Per-source checks:** terms of use and `robots.txt` are recorded before each new source (INDEPENDENCE 1.5, task I-20).
5. **Each area has the same health report**, and an area whose coverage stays below 70% for 2 weeks is paused, not silently left broken.

### 9.3 Candidate areas (all **[VERIFY]**; nothing here is a measured fact)

**Gothenburg first** (same city, Jay can visit, one sales trip covers several areas). The candidates come from PLAN 3.2: Johanneberg/Chalmers main campus, Gårda, Inom Vallgraven/Centrum, Torslanda/Volvo area, Mölndal/Krokslätt. Pick area #2 by the 9.1 score, not by gut. Score at least three before choosing.

**Other Swedish cities** (only after Gate 3): look for areas that, like Lindholmen, mix a science park or tech cluster with offices and students. Examples to research: office and tech districts in Stockholm, Malmö/Lund, Linköping and Uppsala **[VERIFY each: restaurant count, menu formats, existing aggregators, office density]**. Selling remotely changes the GTM: it needs a local channel partner or champion per city, because Jay cannot walk in. Each city gets its own score in 9.1, and no city is announced before its coverage meets the reliability gate.

### 9.4 Brand for expansion

"Lindholmen Lunch" works as an area product name. An expandable product needs an umbrella brand and domain, with area pages under it (for example `<brand>/lindholmen`), which also resolves the conflict with the original creator's `lindholmenlunch.nu` (INDEPENDENCE decisions 2–3). The name is Jay's decision (Q2). **[VERIFY]** trademark and domain availability before choosing.

---

## 10. Milestones, go/no-go gates and kill criteria

Dates assume today (20 Nov 2026) and MARKETING's launch week (11–15 Jan 2027). All thresholds are **[ASSUMPTION]**.

| Gate | Target date | Go when all are true | If not met |
|---|---|---|---|
| **G0 Foundation** | 8 Jan 2027 | Licence resolved (BP-0a); 10 consecutive weekdays fresh before 09:00; analytics live ≥ 2 weeks; `today.json` and `/screen/` working on a real screen | Do not start pilots. If the licence is unresolved by end of January and a rewrite isn't approved, **stop all revenue work** and keep the free site. |
| **G1 Pilots** | 26 Feb 2027 | ≥ 3 pilots live (any mix of screen and chat) and ≥ 10 B2B conversations held; pilots meet the 6.2 criteria | < 2 pilots after 25 contacts: re-test the offer once (price, message or buyer). If still < 2 after 4 more weeks, **kill the B2B line** and keep only the free chat post. |
| **G2 First revenue** | 30 Apr 2027 | ≥ 2 paying B2B customers **or** ≥ 2 sponsor weeks sold; MRR ≥ 1,000 SEK; Jay's time ≤ 4 h/week on average | Revenue but over 4 h/week: cut channels (MARKETING 6.3). No revenue: return to portfolio mode (PLAN R8), keep the site free. |
| **Audience gate (sponsor standard rate)** | when met | ≥ 8 weeks of analytics; slot views and clicks reportable | Keep the launch rate, or pause sponsor sales |
| **G3 Lindholmen proven** | 30 Sep 2027 | MRR ≥ 4,000 SEK; ≤ 1 cancellation a quarter; 30-day on-time rate ≥ 95%; coverage ≥ 85%; Jay ≤ 4 h/week | Stay one area. Optimise or stop sales. |
| **G4 Area #2 proven** | ~6 months after the area #2 launch | Area #2 reaches ≥ 50% of Lindholmen's MRR with ≤ 1 extra h/week | Do not expand to other cities. Keep the areas that pay. |

The summer gap (Swedish holiday season, roughly July **[ASSUMPTION]**) lowers traffic and sponsor inventory. Yearly billing smooths screen revenue. Don't read July numbers as churn.

**Standing kill criteria** (any of these, two months in a row, triggers a stop-or-shrink review): on-time rate < 90% for paying customers; Jay's time > 5 h/week; assistant costs above the cap; a credible legal complaint from a restaurant or platform that can't be resolved by removal.

---

## 11. Risks

| Risk | Likelihood / impact **[ASSUMPTION]** | Mitigation |
|---|---|---|
| **Code licence** (inherited code without a licence) | High / blocking | BP-0a; nothing is sold before it is resolved (INDEPENDENCE 1.1) |
| **Menu content rights** (descriptions, compilations, photos) | Medium / medium | Show facts and short text, link back, no restaurant photos without permission, the permission email and 24-hour opt-out (PLAN 3.6, MARKETING T-REST). Paid B2B makes this more material, so ask each restaurant before Gate 1. |
| **Scraping terms and robots.txt** | Medium / medium | Record terms per source (INDEPENDENCE 1.5); honour crawl delays and AI signals; move to self-submission where a site forbids scraping |
| **Restaurants object** to others earning from their menus | Medium / medium | Neutrality is visible (no paid placement); restaurants get free traffic reports; opt-out honoured |
| **Ad labelling** (marknadsföringslagen § 9: ads must be identifiable) | Low if followed / high if not | An `Annons` label on every sponsor surface, including Slack and Teams lines; never on picks; sponsor policy page |
| **Restricted sponsor categories** (alcohol, gambling) | Low / high | Excluded in the sponsor policy (5.4) |
| **GDPR** | Low–medium / medium | Cookieless analytics; B2B outreach rules (MARKETING 4.4); webhook URLs and customer contacts stored privately; the posts read no messages and process no employee data; privacy page lists processors; DPA with the analytics vendor |
| **Slack and Teams platform rules** | Medium / medium | Webhooks first (no app review); OAuth app or marketplace listing only if needed **[VERIFY each platform's current distribution and review rules]**; Teams connector changes **[VERIFY]** |
| **GitHub cron unreliability** | Certain (measured) / high | BP-0b external trigger; health alert; GitHub cron only as backup |
| **GitHub Pages commercial-use terms** | Medium / medium | **[VERIFY]**; be ready to move the static site to a host that allows commercial use (no code change, only deployment) |
| **Single operator** (illness, holidays) | Medium / medium | No uptime SLA in the terms; best-effort support with stated hours; a pro-rata credit if the update fails more than 2 days in a month; the assistant can fix most scraper breaks |
| **Assistant budget cap** | Medium / low–medium | Priority order in 6.3 |
| **Small market per area** | High / medium | Gates; expand only on proof; per-area cost kept low (9.2) |
| **Competing aggregators** | Unknown / medium | Differentiate on office integration and design, not directory size (PLAN 3.2) **[VERIFY competitors per area]** |
| **Name and domain confusion** with the original creator's site | High / medium | Umbrella brand (9.4); update MARKETING URLs before printing |

---

## 12. Open questions for Jay

1. **Licence path:** ask the original author for a written licence, or go straight to the clean-room rewrite (INDEPENDENCE decision 1)? This blocks everything paid.
2. **Brand:** keep "Lindholmen Lunch" as the area name under a new umbrella brand and domain? Any name ideas to check?
3. **Analytics vendor:** which EU cookieless tool (INDEPENDENCE decision 4)? Without it, sponsors can't be priced.
4. **Sponsor categories:** may a restaurant or food-delivery service buy the weekly sponsor slot? (Recommended: no, to protect neutrality.)
5. **Paid tiers ad-free:** confirm that paying screens and paid chat tiers never carry sponsors.
6. **Billing:** yearly invoices through Jay Digital Studio AB's existing accounting, or payment links? Which accounting system?
7. **Prices:** are 290 / 490 / 990 (screens), 99 / 390 (chat), 590 (bundle) and 1,500–2,500 per sponsor week in the right range for you? Founding discount OK?
8. **Warm network:** roughly how many people do you know at Lindholmen companies who could pilot? (A number only.)
9. **Support promise:** which hours, and what credit if the update fails?
10. **Hosting:** OK to move the site to another static host if GitHub Pages terms don't fit a paid product? OK to open a free serverless account for the scheduler?
11. **Slack/Teams depth:** is webhook-only acceptable for the first year, or do you want a proper "Add to Slack" app (more build, a small server, platform rules)?
12. **Area #2:** any area where you already have contacts, which should weigh the 9.1 score?
13. **Legal review budget:** pay for a short lawyer review of the terms, the sponsor policy and the licence answer?
14. **Canteen content:** will you accept office-supplied text (canteen menu, messages) on screens, given you're responsible for what's shown?
15. **Merge order:** PLAN (PR #3), MARKETING (PR #4) and INDEPENDENCE (PR #5) are unmerged. Should this plan be merged with them as the reference, with MARKETING's domain and URLs updated first?
