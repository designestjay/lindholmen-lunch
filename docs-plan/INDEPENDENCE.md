# Lindholmen Lunch — Independence Plan

Owner: Jay Digital Studio AB, Gothenburg (data controller; contact support@jaydigitalstudio.com).
Goal: run Lindholmen Lunch fully on infrastructure Jay Digital Studio AB owns, independent of the original creator (GitHub user **Fawenah**), with every known issue fixed legally and properly.
Status: **planning only.** No app code is changed by this document.
Companion documents: `docs-plan/PLAN.md` (PR #3, task IDs `P-*` and `U-*`), `docs-plan/MARKETING.md` (PR #4), redesign PR #2. This plan references those task IDs instead of repeating them. New tasks here use the prefix `I-`.

> **Not legal advice.** Every legal statement below is a summary for planning. Anything marked **[counsel]** should be checked with a Swedish lawyer (IT/IP and data protection) if there is any doubt. Facts that could not be verified are marked **[UNKNOWN]** or **[ASSUMPTION]**.

---

## Decisions for Jay

1. **Code path.** Recommended: **clean-room rewrite in a new repository** owned by Jay Digital Studio AB, whatever Fawenah answers. Alternative: rely on a written licence from Fawenah. (See 1.1.)
2. **Domain path.** Ask Fawenah once, in writing, to hand over `lindholmenlunch.nu` (Case A). If there is no clear yes within a deadline you set (suggested: 14 days), go to Case B: a new domain registered to Jay Digital Studio AB. (See 1.3.)
3. **Name.** Keep "Lindholmen Lunch" only if Fawenah agrees (Case A) or stops running his site. If he keeps running his site, pick a distinct name to avoid confusing users (and any passing-off claim). (See 1.4.)
4. **Remove Google Analytics and AdSense now** (PLAN.md U-1). The IDs in our templates (`G-LMDT71XZ0C`, `ca-pub-7499028717075061`) were added by Fawenah and match his live site, so our visitors' data and any ad revenue very likely go to **his** Google accounts. Choose a cookieless analytics vendor (Plausible, Umami or GoatCounter; check current prices).
5. **Hosting.** Recommended: GitHub Pages + GitHub Actions + a free external scheduler (Cloudflare Workers Cron or cron-job.org) + Healthchecks.io alerting. Expected running cost: about **0 SEK/month** plus the domain fee. Vercel is not recommended for production (Hobby plan is non-commercial; Pro costs money per seat). (See 2.1.)
6. **Restaurant permission model.** Approve sending a short permission email to every listed restaurant, with an opt-out honoured within 24 h, and a restaurant-submitted menu form as the fallback source. (See 1.5 and 3.)
7. **Scope.** Decide whether to add Alkemisten and Gansu (likely yes, if in the area) and The Social (it is in **Eriksberg**, not Lindholmen; suggest no, or a separate "nearby" group). Decide whether to drop Mimolett until its website is fixed.
8. **Interim repo visibility.** The current public repo distributes Fawenah's code with no licence. Options: (a) keep it public until the new repo replaces it (low practical risk, but not clean), or (b) make it private now (GitHub Pages from a private repo needs a paid plan; check current price). Recommended: (a), and make the old repo private or archive it at cutover.
9. **Pause build-agent work on Fawenah-written files** (scrapers, `main.py`, `generate_html.py`, `utils/`) until decision 1 is made, so no money is spent improving code that will be replaced. UI and legal tasks (U-1, U-2 to U-12) can continue.
10. **Counsel budget.** Decide whether to pay for a short lawyer review of the Fawenah agreement (if any) and the privacy page. Recommended if Fawenah sends anything other than a plain "yes, MIT licence".

---

## 0. What we verified (read-only audit, 2026-11-14)

| Area | Fact | Evidence |
|---|---|---|
| Code licence | **Neither repo has a LICENSE file.** GitHub reports `license: null` for both `Fawenah/lindholmen_lunch` and `designestjay/lindholmen-lunch`. | GitHub API |
| Fawenah's terms | Fawenah's README says: *"This project is for educational and personal use. Please respect the terms of use of the restaurant websites being scraped."* That is a statement of intent, not an open-source licence. | `Fawenah/lindholmen_lunch` README, "License" section |
| Our README | Our README says *"open source and available under the MIT License"* and links to a `LICENSE` file that does not exist. Jay cannot put Fawenah's code under MIT, so this claim is wrong and must be removed. It also lists `fawenah@gmail.com` as contact. | `README.md` lines 158–165 |
| Code origin | Our repo is a **copy with full history**, not a GitHub fork (`fork: false`). The first commits are by Fawenah (May 2025). Fawenah is the only author of 13 of 15 scrapers, `scrapers/__init__.py`, all of `utils/`, all of `tests/`, and `flyer.html`; he co-authored `main.py`, `generate_html.py`, `scrapers/base.py`, `privacy.html`, `sitemap.xml` and the old template. Files only Jay wrote: `package.json`, `scrape.js`, `server.js`, `prototype/*`, the workflow (in its current form), and PR #2's new template. | `git log --follow` per file |
| Tracking IDs | GA4 `G-LMDT71XZ0C` and AdSense `ca-pub-7499028717075061` were first added by Fawenah (2025-06-08 and 2025-05-25) and are the **same IDs** used on Fawenah's live site. Who controls these Google accounts: **[UNKNOWN, very likely Fawenah]**. Jay to confirm he has no access. | `git log -S`; Fawenah `docs/index.html` |
| Domain | `lindholmenlunch.nu` resolves to GitHub Pages IPs (185.199.108–111.153), name servers `ns1–4.webb.net`. It is served by Fawenah's repo (`docs/CNAME`). Registrant: **[UNKNOWN]** (not visible in public lookup). | `dig` |
| Our Pages site | Source is branch `main`, folder `/` (root). Custom domain on the Pages setting: none. **HTTPS enforced: false.** Public URL `iamjaydesign.com/lindholmen-lunch/`. Root `CNAME`, `docs/CNAME` and `sitemap.xml` still say `lindholmenlunch.nu`. | GitHub Pages API; repo files |
| Fawenah still active | His repo's scheduled job still pushes daily (last 2026-11-13). Two sites currently scrape the same restaurants. | GitHub API |
| Restaurant robots.txt | No source disallows general crawling of the menu pages. `tamed.se` asks for `Crawl-delay: 10`. `matminnen.se` and `restaurangmimolett.se` block named AI crawlers and Mimolett publishes `Content-Signal: search=yes, ai-train=no, use=reference`. A plain scraper with an honest User-Agent is allowed, but must not be used for AI training. | `curl https://<host>/robots.txt` |
| Pipeline | Facts from the brief: 14 failed weekdays (fixed by PR #1), no alerting, GitHub cron starts 5–9 h late, `ubuntu-latest` unpinned, failed restaurants vanish (PR #2 adds stale badges), `generate_html.py` hardcodes UTC+2 (lines 36–37 and 70–71). | brief; code |

---

## 1. Legal

### 1.1 Fawenah's code: what "no licence" means, and our options

**What it means.** Under the Swedish Copyright Act (*upphovsrättslagen*, 1960:729) and the Berne Convention, code is protected automatically from creation. With no licence, the author keeps all rights. Publishing on GitHub gives other users only the right to view and fork **within GitHub** (GitHub Terms of Service, section D.5); it does not give a right to modify, redistribute or run the code commercially elsewhere. Fawenah's README limits use to "educational and personal use". Jay Digital Studio AB is a company with revenue plans (PLAN.md Part 3), so our current use is most likely **outside** what Fawenah has allowed. **[counsel]** Small scrapers may have low originality, but we should assume they are protected.

**Moral rights.** Swedish law gives the author a right to be named "as good practice requires" (*ideell rätt*, 3 § URL). This cannot be transferred, only waived for specific uses. If we keep any of his code, we must credit him in a way he accepts.

**Options (can be combined):**

| Option | What happens | Pros | Cons |
|---|---|---|---|
| **A. Written licence from Fawenah** | He adds a standard licence (ideally MIT) to his repo, or signs a short letter granting Jay Digital Studio AB a perpetual, irrevocable, worldwide, commercial licence (or assignment) to the code. | Fast; keeps working code | Depends on him; the wording must be clear **[counsel]** if it is anything other than a standard licence |
| **B. Clean-room rewrite** (recommended) | New repository with no Fawenah history. A written functional spec (facts only: restaurant list, public source URLs, output fields, page behaviour) is the only input. The implementer works only in the new repo and does not open the old code. All Fawenah-written files are retired. | Independent of his answer; also fixes the broken parts; clean history | Costs build-agent time; the AI agent must work in a fresh repo/session so it does not copy old code |
| **C. Keep using without permission** | — | — | Not acceptable. Copyright risk and the README's MIT claim is false. |

**Clean-room rules for B** (task I-10 onwards):
- The spec (`SPEC.md`) contains only facts and requirements: restaurant names, addresses, public menu URLs, which weekdays they serve, the JSON fields we want, and UI behaviour from PLAN.md. No code, no regular expressions, no CSS selectors copied from old files.
- The build agent runs in the **new** repo, starting a fresh session, and is told in its task prompt not to read `designestjay/lindholmen-lunch` or `Fawenah/lindholmen_lunch`. Each scraper is written by looking at the restaurant's live page, not old code.
- Keep a short log (`docs/CLEAN_ROOM.md` in the new repo): date, task, sources used. This is evidence if ever needed. **[counsel]** on whether an AI-assisted clean room is strong enough evidence; it is still far better than copying.
- Jay's own files (`scrape.js`, `server.js`, `prototype/*`, PR #2's new template and CSS) can be reused because Jay wrote them. **Check before reuse:** PR #2's template may contain markup carried over from Fawenah's `summary_template.html`; if in doubt, redo it from PLAN.md section 2.4.
- Test fixtures (saved restaurant HTML) are copies of restaurants' pages. Keep them small and only in the repo for testing, or fetch-and-cache them in CI instead of committing.

**Attribution.**
- If A: credit as he wishes, for example in the README and footer: "Originally created by Fawenah". Ask him how he wants to be named.
- If B: no legal credit is needed for code we did not copy. An optional, friendly "Inspired by the original Lindholmen Lunch by Fawenah" line is a courtesy; only add it with his consent.
- In all cases: remove `fawenah@gmail.com` and his name as contact from our README, privacy page and footer (task I-01).

### 1.2 What to ask Fawenah (Jay sends; one email, in writing)

1. Will you license your `lindholmen_lunch` code to Jay Digital Studio AB for commercial use? (Easiest: add an MIT `LICENSE` file to your repo.)
2. Do you own `lindholmenlunch.nu`? Who is the registrar? Would you transfer the registration to Jay Digital Studio AB? If yes, on what terms (free, or a price)?
3. Do you plan to keep running your site? If not, can you point visitors to our site (a notice or redirect) and stop your scheduled job so restaurants are not scraped twice?
4. Do the GA4 property `G-LMDT71XZ0C` and AdSense `ca-pub-7499028717075061` belong to you? We will remove them from our site. (We do **not** ask to transfer historic analytics data; it is visitor personal data and we do not need it.)
5. Have any restaurants given you permission, asked to be removed, or complained? (So we can honour existing opt-outs.)
6. Do you claim any right to the name "Lindholmen Lunch"? Are you OK with us using it?
7. How would you like to be credited, if at all?

If the answer is unclear, partial, or has conditions, **[counsel]** before relying on it.

### 1.3 Domain: two cases

**Case A — formal handover of `lindholmenlunch.nu`**
1. Written agreement (email is fine for a simple free transfer; **[counsel]** if money or conditions are involved): Fawenah transfers the registration to Jay Digital Studio AB.
2. Registrant change at the registrar. For `.nu` (run by Internetstiftelsen) the current holder must approve the change of holder; the exact steps depend on his registrar **[UNKNOWN which registrar; DNS is at webb.net]**. Jay Digital Studio AB then moves the domain to its own registrar account.
3. Before DNS changes: Fawenah removes the custom domain from his Pages settings and deletes `docs/CNAME` (otherwise GitHub may refuse to attach the domain to our repo).
4. Jay verifies the domain in GitHub (account or org settings → Pages → Verified domains). This blocks domain takeover by other GitHub users.
5. Cutover as in section 4.

**Case B — new domain owned by Jay Digital Studio AB**
1. Pick and register a new domain in the company's name (check availability; `.se` or `.nu` cost roughly 100–300 SEK/year **[ASSUMPTION, check registrar]**). If Fawenah keeps running `lindholmenlunch.nu`, choose a clearly different name to avoid confusion.
2. Remove every `lindholmenlunch.nu` claim from our repo: root `CNAME`, `docs/CNAME`, `sitemap.xml`, canonical URL in PLAN.md U-12, README (task I-02). Until the new domain exists, the canonical URL is `https://iamjaydesign.com/lindholmen-lunch/`.
3. Verify the new domain in GitHub, set it as the Pages custom domain, enforce HTTPS.
4. Update marketing assets in MARKETING.md (QR codes, posters, links) **only after** the domain is final, so nothing is printed with a URL we do not control.

**Rule for both cases:** do not print QR codes or posters (MARKETING.md T-QR) and do not launch (T-LAUNCH) until the domain is owned by Jay Digital Studio AB.

### 1.4 Name

"Lindholmen Lunch" is descriptive (a place plus a meal), so it is probably hard to register as a trademark, but using the same name as an existing site run by someone else still risks user confusion and a passing-off style claim under Swedish marketing law. **[counsel]** Steps: search PRV and EUIPO trademark databases for "Lindholmen Lunch" (task I-03, Jay does it); keep the name only in Case A or if Fawenah agrees in writing.

### 1.5 Restaurant menus: copyright, database right, terms, robots.txt

- **Menus are mostly facts** (dish names, prices, days). Facts are not protected by copyright. Longer creative descriptions can be. **Photos are protected**: never copy restaurant photos without permission.
- **Compilations:** the Swedish "catalogue protection" (49 § URL, Sweden's version of the EU database right) protects compilations of many items or those that took substantial investment. One restaurant's weekly menu is a small compilation; the risk is low but not zero, especially for structured feeds from large operators (Compass Group, Nordrest, Plate Impact). **[counsel]** if we sell data (PLAN.md R6).
- **Website terms of use** can forbid scraping and can be binding. Before writing each scraper, read the site's terms (task I-20 records this per source).
- **robots.txt:** respected as policy, even where not legally binding. Current result: allowed for all sources; honour `Crawl-delay: 10` on `tamed.se`; never use menu data for AI training (Mimolett's `ai-train=no` signal).
- **Polite scraping rules for the new scraper:** an honest User-Agent, for example `LindholmenLunchBot/1.0 (+https://<our-domain>/om; support@jaydigitalstudio.com)`; at most one request per source per run; a source already fresh today is skipped on later runs (so the backup runs in 2.2 add almost no load); no login walls, no CAPTCHAs, no bypassing blocks.
- **Permission-based model (recommended):** Jay sends each restaurant a short email: what we show, that we link to them, how to correct or opt out, and an offer to submit the menu themselves. Keep replies in a simple log (`restaurants.yml` field `permission: yes/no/pending`, date). Honour opt-outs within 24 h. This is also the start of MARKETING.md T-REST and PLAN.md R1.
- **Always link back** to the restaurant's own page and show "Source: <restaurant site>" per row.

### 1.6 GDPR and Swedish cookie law (LEK)

Covered in PLAN.md 3.6 and task U-1. Additions for independence:
- **Remove GA4 and AdSense immediately**, not only because they load without consent (LEK ch. 9 § 28 requires prior consent for non-essential cookies), but because they very likely send our visitors' data to **another person's** Google accounts. We cannot be the data controller for processing we do not control.
- **Hosting logs:** GitHub Pages (or any host) processes visitor IP addresses. Name the host as a processor/recipient in the privacy page and link its privacy statement. **[counsel]** whether GitHub acts as processor or independent controller here; describe it neutrally either way.
- **External fonts and scripts:** self-host fonts (PLAN.md U-3). No other third-party requests without consent.
- **Language choice in `localStorage`** is a user-requested functional setting; mention it in the privacy page.
- **Analytics:** cookieless, EU-hosted, with a data processing agreement (DPA) signed by Jay Digital Studio AB. Legal basis: legitimate interest for aggregate statistics.

### 1.7 Privacy page content (task I-04 writes it; Swedish and English)

1. Who we are: Jay Digital Studio AB, org. no. **[Jay to fill in]**, Gothenburg; contact support@jaydigitalstudio.com.
2. What we collect: no accounts, no forms (until a restaurant form exists), cookieless page statistics (which vendor, what is counted, IP not stored or truncated, per vendor docs), hosting server logs (IP, user agent, time) by the host.
3. Why and legal basis: statistics to improve the service (legitimate interest); hosting logs for security and delivery (legitimate interest).
4. Recipients and transfers: analytics vendor (EU), hosting provider (GitHub, Inc., USA; transfers under the EU–US Data Privacy Framework if certified **[verify current status]**).
5. Retention: per vendor settings (state the number of days once chosen).
6. Cookies and local storage: none for tracking; language setting stored locally.
7. Your rights: access, erasure, objection, etc.; right to complain to IMY (imy.se).
8. Restaurant-submitted menus (when added): what is stored, contact person data, retention.
9. Date of last update.

No mention of Fawenah's email, AdSense or "consent banner" unless those exist.

---

## 2. Infrastructure we own

### 2.1 Hosting choice

| Option | Monthly cost | Commercial use | Fit |
|---|---|---|---|
| **GitHub Pages + Actions** (recommended) | 0 SEK for a public repo (Actions minutes are free for public repos) | Allowed for a normal website (no "free web hosting for commerce" abuse; check current GitHub Pages limits) | Already working; free HTTPS; simple static output |
| Cloudflare Pages + Workers Cron | 0 SEK on free plan **[verify current limits]** | Allowed | Good alternative if we need headers/redirect control or move scheduling into one account |
| Vercel | Hobby: free but **personal, non-commercial** use only; Pro: paid per seat **[check current price]** | Pro only | Not needed for a static site; current preview `lindholmen-lunch-preview.vercel.app` should be moved or removed once a GitHub preview exists |
| Own VPS | ~50–100 SEK/month **[ASSUMPTION]** + maintenance | Yes | Overkill |

Recommendation: **GitHub Pages**, owned by the Jay Digital Studio AB GitHub account or organisation (create an org if the repo is under a personal account, so the company owns it). Deploy with the official Pages action (artifact upload) instead of committing built HTML to `main` every day; only `data/*.json` gets committed. This also removes the duplicate root `index.html` vs `docs/index.html` confusion.

### 2.2 Reliable scheduling (GitHub cron starts 5–9 h late)

GitHub's `schedule` is best-effort and is delayed under load. Fix in layers:
1. **Keep GitHub crons as backup** at odd minutes (PLAN.md P-1: `7 5`, `37 6`, `7 8` UTC, Monday–Friday).
2. **Primary trigger from outside GitHub:** a Cloudflare Worker with Cron Triggers (free) or cron-job.org (free) calls the GitHub REST API `POST /repos/{owner}/{repo}/actions/workflows/update-and-deploy.yml/dispatches` at 05:15 and 07:15 UTC. Authentication: a **fine-grained personal access token** limited to this one repo with "Actions: read and write" only, stored as a secret in the scheduler. Rotate yearly. (Task I-31.)
3. `concurrency` group per day so runs never overlap; runs are idempotent and skip restaurants that are already fresh today.
4. Note winter/summer time: UTC times above are 06:15/08:15 CET in winter and 07:15/09:15 CEST in summer. That is fine; both are before lunch.

### 2.3 Alerting

- **Healthchecks.io** (free tier **[verify limits]**): one check, cron schedule `15 5 * * 1-5` UTC, grace 3 h. The workflow pings `/start` at the beginning and the success URL at the end, or `/fail` with the health summary. If **no** run happens at all (the failure mode we had for 14 days), Healthchecks emails support@jaydigitalstudio.com. (Task I-32.)
- **GitHub failure email** plus the step summary and threshold from PLAN.md P-3.
- **Weekly coverage line:** P-3's summary is enough; no extra service.

### 2.4 Pinned and tested runners

- `runs-on: ubuntu-24.04` (not `ubuntu-latest`), Python `3.12`, actions pinned to a major version or commit SHA. Dependabot for GitHub Actions and pip, monthly. (Task I-33, extends PLAN.md P-4.)
- `requirements.txt` pinned (P-4). `pytest` in CI on saved fixtures (P-4).

### 2.5 Time zone

Replace the hardcoded `timezone(timedelta(hours=2))` with `zoneinfo.ZoneInfo("Europe/Stockholm")` everywhere a date or time is shown or a weekday is chosen. In winter Sweden is UTC+1, so today's code shows times an hour wrong. In the clean-room rewrite this is a requirement in `SPEC.md`; if decision 1 is "licence", it is task I-34 on the old code.

### 2.6 HTTP → HTTPS and site basics

- In the Pages settings of **both** this repo and Jay's user site repo (which serves `iamjaydesign.com`), tick **Enforce HTTPS**. If the box is greyed out, remove and re-add the custom domain to trigger the certificate. Verify: `curl -I http://<domain>/` returns `301` to `https://`. (Task I-35.)
- `robots.txt` (allow all; link the sitemap), `favicon.ico` + `apple-touch-icon.png`, Open Graph tags and canonical (PLAN.md U-12, with the canonical set to the **owned** domain), real README (task I-05), remove `node_modules` (P-6).

### 2.7 Domain and DNS steps (both cases)

1. Domain registered to **Jay Digital Studio AB** (not a private person), with the company's registrar account and 2FA, auto-renew on, renewal email to support@jaydigitalstudio.com.
2. Verify the domain in GitHub (Verified domains).
3. DNS records at the registrar (or Cloudflare DNS, free): apex `A` records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (and `AAAA` `2606:50c0:8000::153` to `8003::153`), `www` `CNAME` to `<owner>.github.io`. Check GitHub's docs for current values before changing.
4. Lower TTL to 300 s one day before cutover; raise to 3600 s after.
5. Add the custom domain in Pages, wait for the certificate, enforce HTTPS.
6. Optional: a `CAA` record allowing `letsencrypt.org`.

### 2.8 Monthly cost summary (lean)

| Item | Cost |
|---|---|
| GitHub Pages + Actions (public repo) | 0 |
| Scheduler (Cloudflare Workers free or cron-job.org) | 0 |
| Healthchecks.io free tier | 0 |
| Cookieless analytics | 0 (GoatCounter or self-hosted Umami) to a small monthly fee (Plausible) **[check prices]** |
| Domain | ~100–300 SEK/year **[ASSUMPTION]** |
| Build agent (Cursor on-demand) | capped at **$20/month**; see section 5 |

---

## 3. Per-restaurant fix plan

Approach order of preference: **(1)** structured source the restaurant publishes (JSON API, RSS, feed) → **(2)** plain HTML parsing → **(3)** headless browser (Playwright, only where the page is a JavaScript app and no API is found) → **(4)** restaurant-submitted menu (form). Every restaurant also gets a **fallback** of "show link to their menu" when nothing is parsed, with the stale/missing states from PR #2 and PLAN.md P-2.

Restaurant-submitted form (task I-25): a Google Form or Tally form in Jay Digital Studio AB's account writes to a sheet; the pipeline reads the published CSV; entries are matched by a per-restaurant secret code so only the restaurant can submit for itself. This is also PLAN.md R1.

| Restaurant | Current source | Status today | Planned approach | Fallback |
|---|---|---|---|---|
| Kooperativet | kooperativet.se | Works Mon–Thu; **Friday empty at the source** | HTML parse. Treat "no Friday menu" as `no_menu_published` (show "No Friday menu on their site"), not as a scrape failure. | Link; ask restaurant if Friday is closed or just unlisted |
| District One | districtone.se/lunch.html | **404** | Find the new menu URL from their home page; if none, ask the restaurant where the menu is published | Form; link to home page |
| Bombay Bistro | bombaybistro.se/lunch | Works | HTML parse | Link |
| Cuckoo's Nest | cuckoosnest.se/menyer/lunch | Works | HTML parse | Link |
| Uni3 World of Food | compass-group.se menu API (RSS) | Works | Keep RSS feed (structured). Check Compass Group's terms for the feed. | Link |
| Miss F | missf.se | Works | HTML parse | Link |
| Benne Pastabar | bennepastabar.se | Works | HTML parse | Link |
| LS Kitchen | plateimpact-screen.azurewebsites.net (JavaScript app) | Needs selenium, not installed | Inspect the app's network calls for the JSON endpoint it loads; use that if the provider's terms allow. Else Playwright. Ask restaurant/Plate Impact for permission. | Form; link |
| Bistrot | bistrot.se | Works | HTML parse | Link |
| Mimolett | restaurangmimolett.se/lunch | **Site redirects to unrelated grainesdemane.fr; kvartersmenyn URL 404** | Remove the outbound link now (it sends users to an unrelated site, possible security risk). Jay checks if the restaurant still operates and where it publishes its menu. | Hide restaurant until a source is confirmed; form |
| Oishii | oishii.se/lunchmeny | Works | HTML parse | Link |
| Mat & Minnen | matminnen.se/lunchmeny | **Parses nothing** | Inspect the live page: menu may now be an image, PDF or embedded widget. If text/HTML: new parser. If image/PDF only: ask for permission and a text source, or use the form. (No OCR of images by default; it is fragile.) | Form; link |
| Encounter Asian | tamed.se (JavaScript app) | Needs selenium, not installed | Find the JSON endpoint the app calls; respect `Crawl-delay: 10`. Else Playwright. | Form; link |
| Masala Kitchen | masalakitchen.se/lunch | Works (weekly) | HTML parse | Link |
| Pier 11 | ericssonbynordrest.se (Nordrest) | **Parses nothing** | Inspect the page; Nordrest may load the menu from a feed or widget. Prefer that structured source. | Form; link |
| Alkemisten | — (only in Fawenah's repo) | Not in our repo | If decision 7 = yes: new scraper written from the restaurant's own site (not from Fawenah's code) | Link |
| Gansu | — (only in Fawenah's repo) | Not in our repo | Same as Alkemisten | Link |
| The Social | — (only in Fawenah's repo; **Eriksberg**) | Not in our repo | Only if decision 7 adds a "nearby" group | — |

Headless browser policy: Playwright (Python) with Chromium, installed only in the workflow job that needs it, browser cached with `actions/cache`. Only used for sources with no API. Remove all selenium references.

All sources live in one config file (`restaurants.yml`: name, area, address, map URL, menu URL, method, terms checked date, permission status, active flag). Adding or disabling a restaurant becomes a one-line change.

---

## 4. Migration and cutover sequence

### Phase 0 — Now, no dependency on Fawenah (risk reduction)
I-01 (remove false MIT claim and Fawenah contact), U-1 + I-04 (remove GA4/AdSense, new privacy page), I-02 only if Case B is already decided, I-31 to I-35 (scheduler, alerting, pinning, time zone, HTTPS). Jay sends the email in 1.2 and starts the restaurant permission emails (1.5).

**Rollback:** each is a single PR; revert the PR.

### Phase 1 — Clean-room build (parallel with waiting for Fawenah)
I-10 to I-27 in a **new repo** owned by Jay Digital Studio AB. It deploys to a preview URL only (GitHub Pages of the new repo, without custom domain, or a `preview` path). The old site keeps running.

**Gate to Phase 2:** for 5 consecutive weekdays, the new pipeline's health summary shows at least as many fresh restaurants as the old one, at least one successful run before 08:30 Stockholm each day, and Lighthouse targets from PLAN.md U-11 are met.

### Phase 2 — Domain cutover
Case A (handover done) or Case B (new domain registered):
1. Day −1: lower DNS TTL to 300 s. Record the current DNS records in `docs/DNS_ROLLBACK.md` in the new repo.
2. Day 0, early morning before 06:00: (Case A) Fawenah has removed his custom domain; add the domain to the new repo's Pages, verify, wait for certificate, enforce HTTPS.
3. Point DNS (only needed if records change).
4. Check: `curl -I http://<domain>/` → 301; `https://<domain>/` → 200 with today's menu; `robots.txt`, `sitemap.xml`, OG preview in Slack.
5. Old Jay repo: replace its Pages content with a single redirect page to the new domain (`<meta http-equiv="refresh">` + canonical link), disable its scheduled workflow, then make it private or archive it (decision 8).
6. Case B with Fawenah still running his site: no redirect from his domain is possible; announce the new address via MARKETING.md channels only after cutover.

**Rollback:** restore DNS from `docs/DNS_ROLLBACK.md` (TTL 300 s means about 5 minutes), or remove the custom domain from the new repo and re-enable the old repo's Pages. Keep the old repo intact (not deleted) for 30 days after cutover.

### Phase 3 — Settle (2 weeks)
Watch Healthchecks and step summaries daily. Raise TTL. Then delete the Vercel preview project if not used, rotate the scheduler token, and start the MARKETING.md launch.

---

## 5. Ordered task list for the build agent (Grok 4.7)

**Cost rules (Cursor on-demand cap $20/month):**
- One task = one small PR with a narrow file scope and the acceptance check written below. No task touches more than about five files unless stated.
- Use saved fixtures for tests. At most **one** live scrape per task, for final verification.
- If a task needs more than two fix-up rounds, stop and report to Jay instead of continuing.
- Do not run Lighthouse, Playwright installs or full test suites repeatedly; once at the end of the task.
- Tasks marked **(Jay)** are human actions, not agent work.

**Phase 0 — current repo (`designestjay/lindholmen-lunch`)**

| ID | Task | Acceptance check | Depends on |
|---|---|---|---|
| I-01 | README: remove the MIT claim and the `LICENSE` link, remove `fawenah@gmail.com` and Fawenah contact, state "Operated by Jay Digital Studio AB, support@jaydigitalstudio.com", replace placeholder text with what the site does and how it runs. | `grep -i -E "mit license|fawenah@" README.md` returns nothing | — |
| U-1 | (PLAN.md) Remove GA4 + AdSense, add cookieless analytics. Also remove the IDs from `templates/summary_template.html`, root `privacy.html`, `docs/privacy.html`, `docs/index.html`, root `index.html`. | `grep -rE "G-LMDT71XZ0C|ca-pub-" --exclude-dir=node_modules .` returns nothing | Decision 4 (vendor) |
| I-04 | Rewrite privacy page per 1.7 (SV + EN). | Page contains company name, support email, IMY link; no Fawenah email | U-1 |
| I-02 | Case B only: remove `lindholmenlunch.nu` from `CNAME`, `docs/CNAME`, `sitemap.xml`; canonical = current owned URL. | `grep -r lindholmenlunch.nu --exclude-dir=node_modules .` returns only docs-plan files | Decision 2 |
| I-03 | **(Jay)** Trademark search PRV + EUIPO for the name; send Fawenah email (1.2); send restaurant permission emails (1.5); confirm no access to the GA/AdSense accounts. | Notes saved in a private place | — |
| I-31 | External trigger: Cloudflare Worker (or cron-job.org) calling `workflow_dispatch` at 05:15 and 07:15 UTC weekdays; fine-grained PAT. Worker code in `infra/scheduler/` with a README. **(Jay)** creates the token and the account. | `gh run list --event workflow_dispatch` shows runs starting within 5 min of the trigger for 3 weekdays | P-1 |
| I-32 | Healthchecks.io ping in the workflow (`/start`, success, `/fail`), URL from a repo secret. | Manually failing a run sends an email to support@jaydigitalstudio.com | P-3 |
| I-33 | Pin `runs-on: ubuntu-24.04`, pin actions, add `.github/dependabot.yml` (actions + pip, monthly). | Workflow passes on `workflow_dispatch` | P-4 |
| I-34 | Only if decision 1 = licence: replace hardcoded UTC+2 with `ZoneInfo("Europe/Stockholm")`. | Unit test: a UTC timestamp in January renders as UTC+1 | Decision 1 |
| I-35 | **(Jay)** Enforce HTTPS in Pages settings (this repo and the user-site repo). Agent then verifies with curl and adds `robots.txt` and favicon. | `curl -I http://…` → 301; `/robots.txt` and `/favicon.ico` → 200 | — |

**Phase 1 — new repo (clean room)** — the build agent starts a **fresh session in the new repo** and must not open the old repos.

| ID | Task | Acceptance check | Depends on |
|---|---|---|---|
| I-10 | **(Jay)** Create GitHub org/repo owned by Jay Digital Studio AB, add MIT (or proprietary) licence of Jay's choice, enable Pages via Actions. | Repo exists with `LICENSE` | Decision 1 |
| I-11 | Write `SPEC.md` (facts only, see 1.1) and `docs/CLEAN_ROOM.md` log. Written by Jay or a separate planning agent, not the implementer. | Spec has no code or selectors from old repos | I-10 |
| I-12 | Skeleton: `restaurants.yml`, data schema (`today.json` with `fresh / stale / missing / no_menu_published` per restaurant, `fetched_at` with Stockholm time zone), runner script, `pytest`, pinned deps, `ubuntu-24.04`. | `pytest` passes; empty run produces valid JSON | I-11 |
| I-13 | Static page generator using PLAN.md design (U-2 to U-12 behaviour), Jay-owned template code only. | Renders from a fixture JSON at 375/768/1440 px | I-12 |
| I-14 | Workflow: scrape → health summary (P-3 behaviour) → Healthchecks ping → deploy via Pages artifact; commit only `data/`. | Manual run deploys preview | I-12, I-13 |
| I-15 | Port the external trigger (I-31) and alerting (I-32) to the new repo. | As I-31/I-32 | I-14 |
| I-20 | Record terms-of-use and robots.txt check per source in `restaurants.yml` (`terms_checked`, `robots_ok`). | Every active source has both fields | I-12 |
| I-21 | Scrapers, simple HTML/RSS group: Bombay Bistro, Cuckoo's Nest, Uni3 (RSS), Miss F, Benne, Bistrot, Oishii, Masala, Kooperativet (with `no_menu_published`). One PR per 2–3 restaurants. | Fixture test per restaurant; one live run shows each fresh | I-12, I-20 |
| I-22 | Investigate and fix District One, Mat & Minnen, Pier 11 (find current source; parse it or mark `form`). | Each is fresh, or set to `method: form` with a note | I-21 |
| I-23 | JS-app sources: LS Kitchen, Encounter Asian via JSON endpoint; Playwright only if needed (cached). | Fresh in one live run; job time increase < 2 min | I-21 |
| I-24 | New restaurants per decision 7 (Alkemisten, Gansu; The Social only if "nearby" group). | Fresh in one live run | I-21 |
| I-25 | Restaurant-submitted menu: form → published CSV → importer with per-restaurant code. Mimolett and any `method: form` restaurant use it. | A test submission appears on the preview page the next run | I-12 |
| I-26 | Privacy page (from I-04), `robots.txt`, `sitemap.xml`, OG tags, favicon, manifest (U-12) on the new repo; canonical = owned domain. | Slack link preview works; Lighthouse targets (U-11) | I-13 |
| I-27 | 5-weekday parallel run comparison report (old vs new fresh counts, start times). | Gate in Phase 1 met | all above |

**Phase 2–3 — cutover** (mostly Jay, agent verifies)

| ID | Task | Acceptance check |
|---|---|---|
| I-40 | **(Jay)** Domain secured (Case A transfer or Case B registration), verified in GitHub. | Registrant is Jay Digital Studio AB |
| I-41 | Cutover per Phase 2, agent writes `docs/DNS_ROLLBACK.md` first and runs the checks. | All checks in Phase 2 step 4 pass |
| I-42 | Old repo: redirect page, disable schedule, then private/archive (decision 8). | Old URL redirects; no more scheduled runs |
| I-43 | After 2 weeks: remove Vercel preview if unused, rotate PAT, raise TTL, start MARKETING.md launch. | — |

PLAN.md tasks **P-0 to P-6** on the old repo: do P-1 and P-3 now (they protect today's users); **skip P-2, P-4, P-5, P-6 on the old code** if decision 1 is the clean-room rewrite, and implement their behaviour in I-12 to I-21 instead. The U-tasks' design carries over to I-13.

---

## 6. Open questions and unknowns

- Who registered `lindholmenlunch.nu`, with which registrar, and when it expires. **[UNKNOWN]**
- Who controls GA4 `G-LMDT71XZ0C` and AdSense `ca-pub-7499028717075061`. **[UNKNOWN, very likely Fawenah]**
- Whether Fawenah will keep running his site.
- Whether Mimolett is still operating, and where District One, Mat & Minnen and Pier 11 now publish menus.
- Terms of use for Compass Group's menu feed, Plate Impact and tamed.se.
- Jay Digital Studio AB's organisation number for the privacy page.
- Current prices/limits for the free tiers named here (GitHub, Cloudflare, Healthchecks.io, analytics vendors): check before choosing.
