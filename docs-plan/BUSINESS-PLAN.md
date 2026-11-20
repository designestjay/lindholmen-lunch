# Lindholmen Lunch — Business Plan

Status: planning document only. No site code is changed by this PR.
Date: 20 Nov 2026 (updated the same day with Jay's answers, section 0.2). Owner: Jay Digital Studio AB (Gothenburg), solo operator.
Builds on: `docs-plan/PLAN.md` (Part 3: revenue options R1–R8, 90-day roadmap, metrics, legal notes 3.6) and `docs-plan/MARKETING.md` (unmerged, branch `cursor/marketing-plan-22ef`, PR #4). This document references those by ID instead of repeating them. It also leans on `docs-plan/INDEPENDENCE.md` (unmerged, PR #5) for the clean-room rewrite.

Conventions:

- **[ASSUMPTION]** marks every number, price or market claim that has not been verified.
- **[VERIFY]** marks a fact about a third party (platform terms, organisation, area, law) that must be checked at its source before it is relied on.
- Prices are in SEK, excluding VAT (exkl. moms).

---

## 0. Decisions

### 0.1 Starting decisions

1. **Goal:** a product that can expand to other areas and cities, not only a portfolio piece.
2. **Time:** Jay spends 2–4 hours a week. An AI assistant does most build, ops and marketing legwork. Jay approves, sells and sends.
3. **Revenue lines:** (a) paid B2B office screens and Slack/Teams daily posts (PLAN R3 + R4); (b) a weekly sponsor slot (PLAN R2).
   **Not chosen:** restaurant featured spots (R1 paid tier) and display ads (R7). Restaurant listings and picks stay neutral and unpaid.

### 0.2 Decisions (20 Nov 2026)

| # | Decision | What it changes in this plan |
|---|---|---|
| D1 | **Licence: clean-room rewrite now.** Don't wait for the original author. | BP-0a is the rewrite in a new repository (INDEPENDENCE option B and its clean-room rules). All revenue features (BP-0c onwards) are built in the new repo only. No more build work on the inherited scrapers, `main.py`, `generate_html.py` or `utils/`. G0 moves to 29 Jan 2027 (section 10). |
| D2 | **Brand: a new umbrella name and domain.** The name isn't chosen yet. Lindholmen becomes an area page. | BP-0f (choose the name, check trademark and domain, register). Area URLs follow `<domain>/<area>/`. Nothing is printed until the domain exists (9.4). |
| D3 | **Analytics: Umami, self-hosted.** It must stay free or low-cost. | BP-0d uses Umami. Hosting options are listed in 6.1 as [VERIFY]. |
| D4 | **Sponsors: no restaurants or food delivery. Paid tiers never carry sponsors.** | Sponsor policy in 5.4 is final on these points. Screens never carry sponsors, whether pilot or paid. |
| D5 | **Prices as proposed are OK, plus a founding discount.** | Founding offer in 5.0 [ASSUMPTION]. |
| D6 | **Billing: online payment links, not invoices.** | BP-2b and 6.1 use payment links. VAT and receipt requirements are [VERIFY] in 5.0 and section 11. |
| D7 | **Warm network: 1–3 people at Lindholmen companies.** | The pilot funnel relies mostly on cold B2B outreach. G1 expects ≥ 2 pilots, not 3 (7.2, 10). |
| D8 | **Support: weekdays. Pro-rata credit if menus fail on more than 2 days in a month.** | Support terms and the credit formula in 6.2. |
| D9 | **Hosting: OK to move host and open a scheduler account, but only if free.** | 6.1 lists only free options. If no free option fits, the item stays where it is. |
| D10 | **Slack/Teams: simple webhook posts for the first year.** | No OAuth app and no polls in year 1 (BP-3d moved to "after year 1"). The Office tier loses the poll. |
| D11 | **Lawyer: a short paid review before the first sale.** | BP-2e is a G2 entry condition. It is the one budgeted cash cost above "free" (6.1). |
| D12 | **Screens show menus only. No office-supplied text.** | The canteen line, custom message and tenant notice are removed from the screen tiers (5.1). Screen Plus is now about branding and restaurant choice. |
| D13 | **Merge order: fix the domain links in the marketing plan, then merge all the plans.** | The MARKETING.md URLs now point at the live URL (PR #4). Jay merges PLAN, MARKETING, INDEPENDENCE and this plan after that. |

---

## 1. Thesis

Every office area has the same 11:00 question, "var äter vi idag?", and the answer is scattered across restaurant websites. Lindholmen Lunch already answers it for one area automatically, at almost zero running cost. The individual luncher won't pay for that, but **the employer will pay to put the answer where the team already is**: on the lunch-room screen and in the team's Slack or Teams channel. A **weekly sponsor slot** sells the same local, office-worker audience to employers and local services, without touching the neutrality of the menus. The product grows by **adding areas, not features**: each new area is a page under one umbrella brand, a set of menu adapters, and a few local B2B customers. It is worth expanding only if one area proves that (1) the morning update is reliable, (2) offices pay, and (3) the work fits in Jay's 2–4 hours a week. This plan is built around testing exactly those three things before spending more.

---

## 2. Where things stand (facts from the repo, 20 Nov 2026)

These facts shape the plan. Anything that blocks charging money is marked **blocker**.

| Area | Fact | Source | Consequence |
|---|---|---|---|
| Coverage | 15 scrapers are configured. On the five weekdays 16–20 Nov, 10–11 restaurants were fresh and 1–3 were missing each day (for example on 20 Nov: Kooperativet empty, District One HTTP 404, LS Kitchen empty). | `main.py` `SCRAPERS`; `data/scrape_meta_*.json` | Roughly 13 restaurants in practice. Paid screens need coverage to be reliably high, and need missing restaurants to be shown honestly. The clean-room rewrite (D1) is the chance to fix the broken sources. |
| **Timing (blocker)** | The cron fires at 05:07, 06:37, 08:07 and 09:37 UTC, but GitHub starts scheduled runs late, and later every month: about 06:40 UTC in August, 10:40–14:30 in September and October, and 13:30–19:50 in November. On 20 Nov the only morning update was a manual `workflow_dispatch` at 08:06 UTC. | `gh run list --workflow update-and-deploy.yml` | A paid screen or a 10:45 Slack post cannot depend on GitHub's cron. A free external trigger is required before any pilot (BP-0b, D9). |
| **Code licence (blocker, decided)** | The repo has no `LICENSE`. Most scrapers and utilities were written by the original author (Fawenah), whose README says "educational and personal use". | INDEPENDENCE.md 1.1 | D1: clean-room rewrite in a new repository now. Nothing is sold from the inherited code. |
| Name and domain | The live site is `https://iamjaydesign.com/lindholmen-lunch/`. `lindholmenlunch.nu` still serves the original creator's site. | `docs/sitemap.xml`, canonical tag; NEXT-UPDATE Part 4 q3 | D2: new umbrella brand and domain. Until then, MARKETING.md uses the live URL (D13), and nothing is printed. |
| Analytics | Cookieless `assets/analytics.js` is in place, but `data-endpoint` is empty, so nothing is measured. The old GA4 data very likely belongs to the original creator. | `docs/index.html`; INDEPENDENCE decision 4 | D3: self-hosted Umami. **There is no traffic baseline yet**, so sponsors stay at the launch rate until 8 weeks of data exist. |
| Product | The site is static (GitHub Pages), bilingual SV/EN, and has "Pick for me" and weekend meal ideas. There is no `today.json`, no `/screen/` view and no chat integration yet. | `templates/index.html` | Everything B2B reads from a static `today.json`. That file is part of the rewrite spec. |

---

## 3. Customers: who pays and who uses

| Line | Buyer (signs, pays) | User (sees it daily) | Why the buyer cares | Budget it comes from **[ASSUMPTION]** |
|---|---|---|---|---|
| Office screen | Office or workplace manager; at small companies the CEO or an operations lead | Everyone in the lunch room or reception | A useful, good-looking screen that needs no updates from them; one less "where do we eat" question | Office running costs or facilities |
| Building or reception screen | Property owner, building manager, coworking operator **[VERIFY who runs lobby screens at Lindholmen]** | Tenants and visitors | A tenant service that costs little and looks local | Tenant services or marketing |
| Slack/Teams post | Team lead or engineering manager (small plan); office manager or IT for company-wide (bigger plan) | The team in a `#lunch` channel | It replaces the daily lunch thread and keeps the team eating together | Team budget, often on a company card (which suits payment links, D6) |
| Weekly sponsor slot | HR or employer-branding lead (recruiting), local businesses (gyms, services, events). Never restaurants or food delivery (D4). | All site visitors, plus free-tier Slack/Teams posts | Reach local office workers and students in a calm, trusted, local channel | Recruitment marketing, local marketing |

Primary target for the first 6 months: **office managers at Lindholmen companies that have a lunch room but no in-house restaurant** (they are buyer and champion in one person), and **team leads** for Slack and Teams. With only 1–3 warm contacts (D7), most of these come from cold B2B outreach. HR and employer branding is the main sponsor buyer. **[ASSUMPTION]** to validate in the first 10 conversations (MARKETING 1.5).

---

## 4. Value proposition per line

**A. Office screen (`/screen/`)**: "Today's lunch around you on the lunch-room screen. It updates itself every weekday morning." It works in any browser-based screen (smart TV browser, signage player, a small computer behind the screen) **[VERIFY with each office's hardware]**. It shows large type, today's restaurants with 2–3 dishes each, and diet tags. Screens show **menus only** (D12): no office-supplied text and no sponsors. The paid tiers add the company's logo and colours and a chosen set of restaurants. No login and no IT project: it is a URL.

**B. Slack/Teams daily post**: "The lunch thread, done for you, at 10:45." One message per weekday in a chosen channel, with today's highlights by diet, a "Pick for me" suggestion and a link. Setup is pasting one webhook URL (D10). It reads no messages and stores no employee data.

**C. Weekly sponsor slot**: "One week, one sponsor, in front of the people who work at Lindholmen." One clearly labelled `Annons` slot on the site, and one line in free-tier chat posts, for Monday to Friday. Exclusive: one sponsor per area per week. Neutrality rule: the sponsor never changes which restaurants appear, their order, or the picks.

What none of the lines sells: restaurant placement, ranking or paid picks (decision 3 in 0.1).

---

## 5. Pricing and packaging (every number is [ASSUMPTION]; the levels are approved, D5)

### 5.0 Principles, founding offer and payment

- Few tiers. Paid tiers are ad-free (D4). A free tier only where it spreads the product (chat).
- **Payment by online payment link** (D6), not invoice. The default is a yearly payment link per tier. Monthly is available as a subscription link at +20%.
- **Founding offer [ASSUMPTION]:** the first 5 paying B2B customers (screens or chat, counted together) get **30% off for the first 12 months**, if they pay yearly. The price is locked for that year, and the renewal is at list price. The first 3 sponsors get the launch rate for up to 4 weeks, even after the standard rate applies.
- **VAT and receipts [VERIFY]:**
  - Swedish B2B customers are charged 25% VAT.
  - EU B2B customers outside Sweden need a VAT number for reverse charge.
  - The receipt from the payment provider must carry the details a VAT document needs: seller name, org. and VAT number, buyer name, date, amounts, VAT rate and amount. Check that the provider's receipt or invoice-style receipt qualifies, so customers can deduct the VAT. Check also that the payouts and fees can be booked correctly in Jay Digital Studio AB's accounts.
  - Some companies can only pay against an invoice. A lost sale for that reason is logged, not solved with manual invoicing in year 1.

### 5.1 Office screens (menus only, no sponsors)

| Tier | Price per month (billed yearly) | What's included |
|---|---|---|
| Pilot | 0 SEK for 4 weeks | One screen, standard view, success criteria agreed up front (6.2) |
| **Screen** | **290 SEK** per screen | Standard area view, auto-refresh, SV/EN, wrong-day and weekend states, office name in the corner |
| **Screen Plus** | **490 SEK** per screen | Logo and colours; a chosen set of restaurants and their order (for example the five nearest); portrait or landscape layout; SV/EN rotation |
| **Building** | **990 SEK** for up to 5 screens | For receptions, property owners and coworking: Plus features on every screen, and a different restaurant set per screen |

Logos are brand assets supplied by the office. They aren't text content, so D12 doesn't exclude them (confirm, 12.2).

### 5.2 Slack and Teams posts (webhooks only in year 1, D10)

| Tier | Price per month (billed yearly) | What's included |
|---|---|---|
| **Free** | 0 SEK | 1 channel, standard 10:45 post, carries the week's sponsor line and a small "Add to your channel" footer |
| **Team** | **99 SEK** per workspace | Up to 3 channels, choose the post time, diet filters (for example vego first), no sponsor line |
| **Office** | **390 SEK** per company | Unlimited channels, Slack and Teams, chosen restaurant set, no sponsor line |

The old "canteen line" and "poll" features have been removed (D10, D12).

### 5.3 Bundle

**Office pack: 590 SEK per month** (1 Screen Plus + Office chat). This is the default offer to office managers, because one buyer then gets both surfaces.

### 5.4 Weekly sponsor slot: rate card and policy

| Item | Price **[ASSUMPTION]** | Notes |
|---|---|---|
| Launch rate, 1 week (Mon–Fri) | **1,500 SEK** | Until at least 8 weeks of Umami data exist |
| Standard rate, 1 week | **2,500 SEK** | Only after the audience gate (section 10) |
| 4-week pack | **7,500 SEK** at standard rate (−25%) | Fits employer-branding campaigns |
| Report | Included | Views of the slot, clicks, and clicks by `src` (site, Slack, Teams); aggregate only |

What the sponsor gets: one `Annons · Veckans sponsor` line or card on the site (logo, max 80 characters, one link), plus one line in every free-tier Slack/Teams post that week. **Screens and paid chat tiers never carry sponsors** (D4).

Sanity check against reach: 2,500 SEK a week only makes sense if the slot is seen by a meaningful local audience. A simple floor: `price ≈ weekly slot views × local CPM`. Example: 3,000 views at a 300 SEK CPM gives 900 SEK, which shows that the premium is for exclusivity and local targeting, not volume. **Re-price after 8 weeks of real data.** The formula, the view count and the CPM are all [ASSUMPTION].

Sponsor policy:

- **Decided (D4):** no restaurants and no food-delivery services, and no sponsor on screens or paid tiers.
- **Proposed:** it must be clearly labelled (section 11). Excluded categories are alcohol, gambling, tobacco and nicotine, and political or religious messages. Copy is approved by Jay, and Jay can refuse any sponsor without giving a reason.
- **Before the first sale:** the lawyer review checks the policy (D11).

### 5.5 What 12 months at Lindholmen could look like

| Scenario | Screens | Chat (paid) | Sponsor weeks sold / year | MRR (month 12, list price) | Year-1 revenue |
|---|---|---|---|---|---|
| Conservative | 3 × 290 | 2 × 99 | 8 × 1,500 | ~2,100 SEK | ~12–17k SEK |
| Base | 8 (average 390) | 6 (average 200) | 20 × 2,000 | ~7,600 SEK | ~40–60k SEK |
| Upside | 20 (average 420) | 15 (average 250) | 35 × 2,500 | ~19,400 SEK | ~110–150k SEK |

All counts, prices and sell-through rates are **[ASSUMPTION]**. Year-1 revenue is lower than 12 × MRR for three reasons: customers arrive gradually, the first sale comes only after G2 (May 2027), and the first 5 customers pay 30% less. The point of the table: **one area probably supports a side income, not a business**. Expansion (section 9) is what changes the ceiling, which is why the per-area cost has to stay small.

---

## 6. Unit economics and running costs

### 6.1 Cash costs (all [ASSUMPTION] until paid; only free options for hosting and scheduling, D9)

| Item | Cost | Notes |
|---|---|---|
| Static site hosting | 0 SEK | GitHub Pages today. **[VERIFY]** GitHub's terms say Pages is not meant for running an online business or SaaS. Before the first sale, either confirm it's acceptable (lawyer review, D11) or move to a static host whose **free** tier allows commercial use **[VERIFY candidates' terms]**. If none is free, stay on Pages and record the risk. |
| Scraping (GitHub Actions) | 0 SEK | The clean-room repo can stay public: Actions are free for public repos. If private, about 4 runs × 22 weekdays × ~5 min ≈ 440 min/month, likely within the free private quota **[VERIFY current quota]**. |
| Scheduler (trigger and chat posts) | 0 SEK | A free-tier cron on a serverless platform that allows commercial use **[VERIFY limits and terms]**. Webhook URLs are stored as its secrets. |
| **Umami (self-hosted, D3)** | 0 SEK target | Umami needs a small Node server and a PostgreSQL database **[VERIFY current requirements]**. Free options to check: (a) a serverless or PaaS free tier plus a free managed Postgres tier; (b) an always-free small VM running Docker; (c) running it on the same free account as the scheduler, if supported. Each needs **[VERIFY]**: free-tier limits, commercial use allowed, EU region (for GDPR), and whether the database pauses or expires on free tiers. If no free option holds up, a small paid VM is the fallback (an expected ~50–100 SEK/month, **[ASSUMPTION]**, needs Jay's OK because D3 says "low-cost"). |
| Domain (umbrella brand, D2) | ~150–350 SEK/year | One domain; areas are paths, not domains |
| AI assistant (Cursor on-demand) | **≤ ~$20/month cap** (≈ 200 SEK **[ASSUMPTION exchange rate]**) | The hard budget for build and ops agent runs. The clean-room rewrite uses most of it in the first months (6.3). |
| Payment links (D6) | Provider fee per payment, an expected ~1.5–3% **[VERIFY]** | No monthly fee wanted. Choose a provider with no fixed fee. |
| **Lawyer review (D11)** | One-off, **[ASSUMPTION]** 3,000–8,000 SEK | Before the first sale: terms of service, sponsor policy, privacy page, payment and credit terms, and the Pages question |
| **Running total** | **~200–250 SEK/month** plus payment fees | Marketing print and fika are one-offs, budgeted in MARKETING 6.6 |

### 6.2 Per-customer economics and support terms

- **Marginal cost per screen or chat customer is close to 0 SEK.** Every customer reads the same `today.json`.
- **The real cost is Jay's time:** about 1–2 h to sell and set up a customer (email, short demo, config, sending the payment link), then about 10 min a month for support **[ASSUMPTION]**.
- **Cash break-even:** about 1–2 Screen customers.
- **Time break-even:** 2–4 h/week is about 9–17 h/month. At an internal rate of, say, 1,000 SEK/h **[ASSUMPTION, Jay to set]**, that is ~9–17k SEK/month of opportunity cost. **Lindholmen alone pays for Jay's time only in the upside case.** This is why expansion must be cheap and gated.

**Support terms (D8):**

- Support is on weekdays only, by email, with a best-effort answer the same or the next weekday.
- No uptime guarantee.
- **Failed day [ASSUMPTION definition]:** a weekday when the customer's area page or `today.json` doesn't show that day's menus by 10:30 Stockholm time, or when fewer than 50% of the area's restaurants are fresh at 10:30. The health report (BP-0e) counts these days automatically.
- **Credit:** if a month has **more than 2 failed days**, the customer gets a pro-rata credit of `monthly price × failed days ÷ weekdays in that month`. For example, at 490 SEK with 3 failed days out of 21, that is about 70 SEK. For yearly payers, the credit is given as extra days added to the subscription, or as a partial refund through the payment provider (12.2).

**Pilot success criteria**, agreed with the customer (template):

- The screen or post was up on ≥ 18 of 20 weekdays before 10:30.
- The menus were correct when spot-checked.
- At least N people (the customer's estimate) used it.

If met, the customer converts at the founding price.

### 6.3 Working within the $20/month assistant cap

1. **The clean-room rewrite comes first** (D1) and will likely use most of the cap through December and January **[ASSUMPTION]**. Revenue features are written as part of the rewrite spec (BP-0c to BP-1d), not bolted on later, so nothing is built twice.
2. **Build in small, planned PRs.** Prefer one well-specified task per run over open-ended runs.
3. **Ops runs are cheap and scheduled:** weekly KPI report and weekly coverage check (MARKETING B13, B14). Daily work (scraping, posting) is plain code, not an agent.
4. **No AI in the daily pipeline** unless the cost per call is known and capped (9.2).
5. If a month hits the cap, the order of priority is:
   1. fix broken scrapers for paying customers;
   2. finish the rewrite;
   3. customer setup;
   4. marketing drafts;
   5. new features.

---

## 7. Go-to-market at Lindholmen (2–4 h/week)

MARKETING.md covers audience channels (QR, restaurants, LinkedIn, SEO, launch week). This section adds only the **B2B sales motion** on top of it. MARKETING's launch week (11–15 Jan 2027) is subject to its own reliability gate. With the rewrite (D1), it should move to the first full week after G0, proposed **1–5 Feb 2027 [ASSUMPTION]**. Update MARKETING's calendar when it is next edited.

### 7.1 Jay's weekly time budget

| Block | Time | What Jay does | What the assistant prepares |
|---|---|---|---|
| Approvals | 30 min | Approve drafts, posts, configs, payment links | Everything, batched once a week (MARKETING 4.2) |
| Sales | 60–90 min | Send ≤ 5 individually written emails from Gmail drafts; 1 short demo or call; reply to leads | Company list from public pages, drafts, a demo link with the prospect's name on the screen view (MARKETING B1, B2, B9) |
| In person | 0–60 min | One walk-in or one local event every other week (reception, office, LSP event **[VERIFY schedule]**). These matter more with a small warm network. | Route, leave-behind (printed only after the domain exists, D2) |
| Ops review | 15–30 min | Read the weekly health and KPI report, decide fixes | Report, fix PRs (MARKETING B13, B14) |
| **Total** | **~2–3.5 h** | | |

### 7.2 Sales sequence (adjusted for 1–3 warm contacts, D7)

1. **Warm (as soon as G0 is met):** each of Jay's 1–3 contacts gets a personal note offering a free 4-week pilot of the Office pack. Expect **1–2 pilots** from this **[ASSUMPTION]**. Ask each for one introduction to another office.
2. **Cold B2B list (start research now, send after G0):** companies within ~10 minutes' walk, from public pages only, approved row by row by Jay (MARKETING B1, B2, 4.4 GDPR notes). ≤ 5 emails a week, so ~40 contacts over 8 weeks.
3. **Channel partners:** ask Lindholmen Science Park and building receptions for a reception-screen pilot and a mention to tenant office managers (MARKETING T-LSP) **[VERIFY routes]**. With a small network, this is the main multiplier.
4. **Product-led loop:** every free Slack/Teams post has an "Add to your channel" footer. Screens carry no QR or promo (D12).
5. **Sponsors (after the lawyer review):** start with recruiting employers found through the same B2B list, then local services. One sponsor email a week at most.

Funnel to plan against **[ASSUMPTION]**:

- Warm: 1–3 contacts give 1–2 pilots.
- Cold: 40 contacts give ~8 replies and 1–3 pilots.
- Total: **2–4 pilots by G1, plan for 2**, leading to 1–2 paying customers by G2.

### 7.3 Sales kit (assistant drafts, Jay approves, lawyer reviews before the first sale)

- A one-page offer (SV and EN) with the tiers from section 5 and the founding offer.
- A live demo URL per prospect (`/<area>/screen/?office=demo-<company>`), removed after the pilot.
- A pilot agreement (half a page: what's provided, dates, success criteria, no cost, how to convert or stop).
- Short terms of service for paid tiers, including the support and credit terms (6.2).
- A sponsor one-pager with the policy from 5.4.

---

## 8. Product roadmap for revenue

The rewrite (D1) happens in a **new repository** under the umbrella brand (D2), following INDEPENDENCE's clean-room rules. The spec (`SPEC.md`) includes the revenue items below from the start. IDs (`BP-*`) are this plan's.

### Phase 0: Foundation (must be done before any pilot; target G0, 29 Jan 2027)

| ID | Item | Done when |
|---|---|---|
| BP-0a | **Clean-room rewrite** in a new repo (INDEPENDENCE option B). Area-ready from day one: `areas/lindholmen.yml`, output to `/lindholmen/` (PLAN 3.2, previously BP-3a). | The new repo serves the Lindholmen area page and the old repo's pipeline is switched off. The inherited code isn't opened by the implementing agent. |
| BP-0b | **Reliable trigger:** a free external scheduler (D9) calls `workflow_dispatch` at about 06:30 and 08:30 local time. GitHub's cron stays only as a backup. | 10 consecutive weekdays with fresh data before 09:00 Stockholm time |
| BP-0c | **`/<area>/today.json`** on every build: date, scraped_at, per-restaurant status (fresh, missing, closed), dishes, tags, links | Schema documented; a test validates it; the page and integrations read only this file |
| BP-0d | **Umami live** (D3) on a free host (6.1), with `src` on every channel (MARKETING 6.2) and events `screen_view`, `sponsor_view`, `sponsor_click`. The tracker is either Umami's own script or the existing `analytics.js` pointed at Umami's collection API **[VERIFY API]**. | Events visible in Umami; privacy page names Umami, the host and the region |
| BP-0e | **Health alert and failed-day count** (PLAN P-3; 6.2 definition), sent somewhere Jay actually reads | A forced failure triggers the alert; the monthly failed-day count is in the report |
| BP-0f | **Umbrella name and domain** (D2): shortlist, trademark check, domain check, register. Set up redirects from `iamjaydesign.com/lindholmen-lunch/` to the new area URL. | Domain registered to Jay Digital Studio AB; old URL redirects; MARKETING links updated a second time (D13 note) |

### Phase 1: Pilot-ready (target: by G0 + 2 weeks)

| ID | Item | Notes |
|---|---|---|
| BP-1a | **`/<area>/screen/` kiosk view** | Static page reading `today.json`. Reloads about every 10 min and at the day change. 16:9 and portrait layouts, large type, SV/EN, wrong-day and weekend states. Config in `screens/<office>.json` (name, logo, colours, restaurant set). **Menus only, no free-text fields (D12), no sponsors (D4).** The config is public, so it holds no secrets. |
| BP-1b | **Slack post via incoming webhook** (D10) | The customer creates a webhook for their channel and sends Jay the URL. It is stored as a scheduler secret, never in the repo. At the chosen time, the scheduler reads `today.json` and posts. **[VERIFY]** Slack's current incoming-webhook setup for external workspaces. |
| BP-1c | **Teams post via webhook** (D10) | **[VERIFY]** Microsoft's currently supported way to post into a channel from outside. Office 365 connectors have been retiring in favour of Workflows webhooks. Same flow as BP-1b. |
| BP-1d | **Sponsor slot component** | `data/sponsor.json` (week, name, logo, text, link, dates). Rendered with an `Annons` label on the site and in **free-tier** posts only. Empty means nothing is rendered. |
| BP-1e | **Customer register** | A private sheet: customer, tier, channels, start, renewal, payment link, failed-day credits. Never in the public repo. |

### Phase 2: Paid (after the lawyer review; G2 entry)

| ID | Item | Notes |
|---|---|---|
| BP-2a | Screen Plus features: logo, colours, restaurant set, layout | Config changes only |
| BP-2b | **Payment links** (D6): one per tier, yearly and monthly; founding-offer links for the first 5 | VAT and receipt checks from 5.0 are done |
| BP-2c | Monthly customer and sponsor report: on-time days, failed days and credit, views, clicks (aggregate) | Generated by the weekly ops run |
| BP-2d | Public status line (`status.json`, or the trust line on the screen) | Honest when a restaurant is missing |
| BP-2e | **Lawyer review (D11)** of terms, sponsor policy, privacy, payment and credit terms, and hosting terms | Signed off before the first payment link is sent |

### Phase 3: Scale (after G3)

| ID | Item | Notes |
|---|---|---|
| BP-3b | **Generic adapters** (9.2) | Lowers the cost per restaurant |
| BP-3c | **Free restaurant menu submission** (form or sheet) | For coverage only, never paid placement |
| BP-3e | Area health dashboard: coverage, timing, failed days and broken scrapers per area | One view for the weekly ops run |
| BP-3d | *(After year 1 only, D10)* "Add to Slack" app and polls | Only if webhook setup proves to be a sales blocker. Needs a small serverless endpoint and Slack's distribution rules **[VERIFY]**. |

BP-3a (area config) moved into BP-0a.

---

## 9. Expansion model: other areas and cities

### 9.1 What makes an area viable (score before building anything)

| Criterion | Threshold **[ASSUMPTION]** | How to check |
|---|---|---|
| Restaurants with a weekly lunch menu published online | ≥ 10 within about 10 minutes' walk | The assistant counts them from public pages and records the format (HTML, PDF, image, Instagram only) |
| Share in a machine-readable format (HTML or text PDF) | ≥ 70% | Same count |
| Office density without in-house restaurants | Enough to list ≥ 30 target companies | Public company pages and building tenant lists **[VERIFY per area]** |
| A local foothold | ≥ 1 warm contact or channel partner | Jay's network, the local science park or business association. Jay's network is small (D7), so channel partners count double. |
| Competition | No local aggregator already integrated into offices | The assistant checks existing aggregators and listings in the area **[VERIFY per area]** |
| Build and run cost | ≤ 2 days of assistant build and ≤ 30 min/week of upkeep | Estimated from the format mix |

### 9.2 How scrapers scale

In the inherited code there is one class per restaurant (about 50–180 lines each, PLAN 3.2). That cost grows linearly with every new restaurant, and sites break regularly (1–3 missing a day in the 16–20 Nov sample). The clean-room spec should build it differently from the start:

1. **Pattern adapters before bespoke code:** many restaurant sites share a layout (weekday headings in HTML, a weekly PDF, a shared menu platform). Write one configurable adapter per pattern, then configure each restaurant with a URL and selectors. Measure the share of restaurants that are config only.
2. **Restaurant self-submission** (BP-3c): free, for menus that are images or Instagram-only.
3. **AI-assisted extraction as a fallback only:** with a per-call cost cap and a monthly budget, always marked "auto-read" in `today.json`. Not in the daily path until its cost is measured against the $20 cap (6.3).
4. **Per-source checks:** terms of use and `robots.txt` are recorded before each new source (INDEPENDENCE 1.5, task I-20).
5. **Each area has the same health report.** An area whose coverage stays below 70% for 2 weeks is paused, not silently left broken.

### 9.3 Candidate areas (all **[VERIFY]**; nothing here is a measured fact)

**Gothenburg first** (same city, Jay can visit, one sales trip covers several areas). The candidates come from PLAN 3.2: Johanneberg/Chalmers main campus, Gårda, Inom Vallgraven/Centrum, Torslanda/Volvo area, Mölndal/Krokslätt. Pick area #2 by the 9.1 score, not by gut. Score at least three before choosing.

**Other Swedish cities** (only after G4): look for areas that, like Lindholmen, mix a science park or tech cluster with offices and students. Examples to research: office and tech districts in Stockholm, Malmö/Lund, Linköping and Uppsala **[VERIFY each: restaurant count, menu formats, existing aggregators, office density]**. Selling remotely needs a local channel partner or champion per city, because Jay cannot walk in. No city is announced before its coverage meets the reliability gate.

### 9.4 Brand for expansion (D2)

- **Structure:** one umbrella brand and domain, with areas as paths (`<domain>/lindholmen/`, `<domain>/garda/`). "Lindholmen Lunch" survives only as the area page's title. The structure also removes the conflict with the original creator's `lindholmenlunch.nu`, so INDEPENDENCE decisions 2–3 (asking for the `.nu` domain, or keeping the name) are no longer needed.
- **Naming criteria:** works in Swedish and English; not tied to one city; short; the `.se` or `.com` is available; no conflicting trademark in the relevant classes **[VERIFY with PRV and EUIPO search]**; social handles available (MARKETING 1.2 process).
- **Sequence:** the assistant proposes a shortlist of 10, and Jay picks 3. The assistant checks them, Jay chooses and registers, then BP-0f.
- **Before printing:** no QR codes or printed material are produced until the domain is live and redirects work.

---

## 10. Milestones, go/no-go gates and kill criteria

Dates are **[ASSUMPTION]**, re-planned for the clean-room rewrite (D1) and a small warm network (D7).

| Gate | Target date | Go when all are true | If not met |
|---|---|---|---|
| **G0 Foundation** | 29 Jan 2027 | Rewrite live in the new repo (BP-0a); 10 consecutive weekdays fresh before 09:00; Umami live ≥ 2 weeks; `today.json` and `/screen/` working on a real screen; domain chosen (BP-0f) | Don't start pilots. If the rewrite isn't live by **31 Mar 2027**, stop revenue work and keep the free site. |
| **G1 Pilots** | 26 Mar 2027 | ≥ 2 pilots live (any mix of screen and chat) and ≥ 8 B2B conversations held; the pilots meet the 6.2 criteria | < 1 pilot after 30 cold contacts: re-test the offer once (price, message or buyer). If still < 2 pilots after 4 more weeks, **kill the paid B2B line** and keep only the free chat post. |
| **Lawyer review done** | before the first payment link | BP-2e signed off | No payment links are sent |
| **G2 First revenue** | 28 May 2027 | ≥ 1 paying B2B customer **and** ≥ 1 sponsor week sold, or ≥ 2 paying B2B customers; MRR ≥ 500 SEK; Jay's time ≤ 4 h/week on average | Revenue but over 4 h/week: cut channels (MARKETING 6.3). No revenue: return to portfolio mode (PLAN R8) and keep the site free. |
| **Audience gate (sponsor standard rate)** | when met | ≥ 8 weeks of Umami data; slot views and clicks reportable | Keep the launch rate, or pause sponsor sales |
| **G3 Lindholmen proven** | 29 Oct 2027 | MRR ≥ 3,000 SEK; ≤ 1 cancellation a quarter; ≤ 2 credit months a year per customer; coverage ≥ 85%; Jay ≤ 4 h/week | Stay one area. Optimise or stop sales. |
| **G4 Area #2 proven** | ~6 months after the area #2 launch | Area #2 reaches ≥ 50% of Lindholmen's MRR with ≤ 1 extra h/week | Do not expand to other cities. Keep the areas that pay. |

The summer gap (Swedish holiday season, roughly July **[ASSUMPTION]**) lowers traffic and sponsor inventory. Yearly payment smooths screen revenue. Don't read July numbers as churn, and pause the failed-day credit count for weeks when the area's restaurants are mostly closed (the terms should say so).

**Standing kill criteria** (any of these, two months in a row, triggers a stop-or-shrink review):

- More than 2 failed days a month for paying customers.
- Jay's time over 5 h/week.
- Assistant costs above the cap.
- Hosting or analytics that can no longer be run for free (D9).
- A credible legal complaint from a restaurant or platform that can't be resolved by removal.

---

## 11. Risks

| Risk | Likelihood / impact **[ASSUMPTION]** | Mitigation |
|---|---|---|
| **Rewrite slips** (D1) under the $20 cap | Medium / high | The rewrite is the first priority (6.3); the spec is small and staged; the G0 kill date is 31 Mar 2027 |
| **Clean-room contamination** (the agent copies old code) | Low / high | Fresh repo and session; the spec holds facts only (INDEPENDENCE clean-room rules); lawyer review covers the process (D11) |
| **Menu content rights** (descriptions, compilations, photos) | Medium / medium | Show facts and short text, link back, no restaurant photos without permission, permission email and 24-hour opt-out (PLAN 3.6, MARKETING T-REST). Ask each restaurant before G1. |
| **Scraping terms and robots.txt** | Medium / medium | Record terms per source (INDEPENDENCE 1.5); honour crawl delays and AI signals; move to self-submission where scraping is forbidden |
| **Restaurants object** to others earning from their menus | Medium / medium | Neutrality is visible (no paid placement, no restaurant sponsors, D4); free traffic reports; opt-out honoured |
| **Ad labelling** (marknadsföringslagen § 9: ads must be identifiable) | Low if followed / high if not | `Annons` on every sponsor surface, including free-tier Slack/Teams lines; never on picks; sponsor policy page; lawyer review |
| **Restricted sponsor categories** (alcohol, gambling) | Low / high | Excluded in the sponsor policy (5.4) |
| **GDPR** | Low–medium / medium | Self-hosted Umami in an EU region, no cookies; B2B outreach rules (MARKETING 4.4); webhook URLs and customer contacts stored privately; the posts read no messages; the privacy page lists Umami's host, the scheduler and the payment provider |
| **Payment links vs B2B buying habits** (D6) | Medium / medium | **[VERIFY]** that receipts qualify for VAT deduction; target card-friendly buyers first (team leads, small offices); log invoice-only lost deals and revisit after year 1 |
| **VAT handling** (Swedish 25%, EU reverse charge) | Low / medium | **[VERIFY]** the provider's VAT settings and receipts; lawyer review or accountant check before the first sale |
| **Free tiers change or end** (hosting, scheduler, Umami database) | Medium / medium | Keep everything portable (static files, Docker for Umami, a plain cron spec); monthly check in the ops report; the standing kill criterion if nothing is free |
| **Slack and Teams platform changes** | Medium / medium | Webhooks only in year 1 (D10); **[VERIFY]** the Teams Workflows webhook path before selling Teams |
| **GitHub cron unreliability** | Certain (measured) / high | BP-0b external trigger; health alert; GitHub cron only as backup |
| **GitHub Pages commercial-use terms** | Medium / medium | **[VERIFY]** in the lawyer review; move to a free host that allows commercial use if needed (D9) |
| **Single operator** (illness, holidays) | Medium / medium | Weekday-only support, no uptime guarantee, automatic pro-rata credit (D8); the assistant can fix most scraper breaks |
| **Small warm network** (D7) | High / medium | Channel partners (LSP, receptions), walk-ins, and introductions from each pilot; G1 lowered to 2 pilots |
| **Small market per area** | High / medium | Gates; expand only on proof; low per-area cost (9.2) |
| **Competing aggregators** | Unknown / medium | Differentiate on office integration and design **[VERIFY competitors per area]** |
| **Name and domain** (choice, trademark) | Medium / medium | Naming process in 9.4; nothing printed before the domain is live |

---

## 12. Decisions resolved, and what is still open

### 12.1 Resolved (20 Nov 2026)

| Question in the first draft | Answer | Where it's applied |
|---|---|---|
| 1. Licence path | Clean-room rewrite now (D1) | 8 BP-0a, 10 G0, 11 |
| 2. Brand | New umbrella name and domain; Lindholmen is an area page (D2) | 8 BP-0f, 9.4 |
| 3. Analytics vendor | Umami, self-hosted, free or low-cost (D3) | 6.1, 8 BP-0d |
| 4. Restaurant or delivery sponsors | No (D4) | 5.4 |
| 5. Paid tiers ad-free | Yes; screens never carry sponsors (D4) | 5.1, 5.2, 5.4 |
| 6. Billing | Online payment links, not invoices (D6) | 5.0, 8 BP-2b, 11 |
| 7. Prices and founding discount | As proposed, plus 30% off for 12 months for the first 5 (D5) | 5.0 |
| 8. Warm network | 1–3 people (D7) | 7.2, 10 G1 |
| 9. Support promise | Weekdays; pro-rata credit above 2 failed days a month (D8) | 6.2 |
| 10. Hosting and scheduler | Move or open accounts only if free (D9) | 6.1 |
| 11. Slack/Teams depth | Webhooks only in year 1 (D10) | 5.2, 8 |
| 12. Area #2 | Not answered as a separate preference; use the 9.1 score | 9.3 |
| 13. Lawyer | Short paid review before the first sale (D11) | 6.1, 8 BP-2e, 10 |
| 14. Office-supplied content | Screens show menus only (D12) | 4, 5.1, 8 BP-1a |
| 15. Merge order | Fix MARKETING domain links, then merge all plans (D13) | PR #4 updated; Jay merges |

### 12.2 Still open (short)

1. **Umbrella name.** The assistant drafts a shortlist of 10; Jay picks (9.4).
2. **Umami host.** Pick one free option from 6.1 after [VERIFY]. If none is free, OK to pay ~50–100 SEK/month?
3. **Payment provider.** Pick one with no monthly fee, with VAT-compliant receipts [VERIFY].
4. **Credit for yearly payers.** Extra days added, or a partial refund? (Recommended: extra days.)
5. **Logos on screens.** Confirm that an office logo is allowed under "menus only" (D12).
6. **Lawyer.** Who, and a budget cap for the review (the plan assumes 3,000–8,000 SEK).
7. **Launch week date.** Move MARKETING's launch week to 1–5 Feb 2027 (after G0)?
