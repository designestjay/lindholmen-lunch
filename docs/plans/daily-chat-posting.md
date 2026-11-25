# Daily lunch posts to Slack and Teams

Plan only. No scraper changes, no new menu source, no customer channels yet. The owner tests on his own Slack and Teams first.

This is the year-1 webhook post from `docs-plan/BUSINESS-PLAN.md` (decision D10: incoming webhooks, no Slack OAuth app, no polls). It does not include the sponsor line, diet filters, "Pick for me", or the paid tiers. Those stay out of this change.

## What the repo does today

Weekday menus are scraped by `main.py` into one JSON file per weekday. `generate_html.py` renders `docs/`. GitHub Pages publishes that folder from `.github/workflows/update-and-deploy.yml` (`name: Update Lunch Data and Deploy`). The live page is `generate_html.SITE`, which is `https://iamjaydesign.com/lindholmen-lunch`.

### Menu files to reuse

Do not scrape anything new. Read the files the morning job already writes.

| File | Role |
|---|---|
| `data/lunch_data_{monday\|tuesday\|wednesday\|thursday\|friday}.json` | Object keyed by scraper class name (`KooperativetScraper`, …). |
| `data/scrape_meta_{day}.json` | `day`, `scraped_at` (ISO with a Stockholm offset), `fresh`, `stale`, `missing`, `wrong_week`, `closed`, `missing_reason`. |
| `data/sources.json` | `active` and `link_only`. Mimolett is `active: false` and `link_only: true`. Mat & Minnen is `active: false`. |
| `utils/restaurants.py` `DISPLAY_NAMES` | Channel-facing names. |
| `utils/holidays.py` `is_holiday` | Dates in `data/holidays_se.json`. |
| `generate_html.SITE` | The button URL. Do not hard-code a second copy. |
| `generate_html.SV_DAY_LONG` | Swedish weekday names, lowercase. |

A restaurant value looks like this (tags and `source_week` may be present; ignore them):

```json
{
  "day": "wednesday",
  "items": [
    {"name": "Caesarsallad", "category": "SALLADER", "description": "…", "price": "130 kr"}
  ],
  "stale": false,
  "fetched_at": "2026-11-25T08:16+01:00"
}
```

`stale: true` means the re-scrape failed and `main.py` kept an earlier same-day payload (`_carried_payload`). `closed: true` means the text said the kitchen is shut. `fetched_at` is when that payload was actually fetched. `scraped_at` on the meta file is when this scrape run finished. A Wednesday file is not "today" just because today is Wednesday. Last Wednesday's file has the same name.

### How the deploy workflow runs

`.github/workflows/update-and-deploy.yml`:

- Triggers: four weekday crons, `push` to `main`, and `workflow_dispatch`.
- Crons (UTC), already off the top of the hour: `7 5`, `37 6`, `7 8`, `37 9`, Monday–Friday. In Europe/Stockholm that is 06:07 / 07:37 / 09:07 / 10:37 in winter and one hour later in summer. The `37 9` run is `--gaps-only` (retry missing, stale, and wrong-week restaurants).
- One job `scrape-and-build`, then `deploy` (`needs: scrape-and-build`) using `actions/deploy-pages`.
- Concurrency group `lindholmen-lunch-daily`, `cancel-in-progress: false`.
- The scrape job commits `data/` and `docs/` and pushes to `main`. A coverage failure after the artifact upload fails `scrape-and-build`, which skips `deploy`. The workflow conclusion is then `failure`.
- Weekend: the scrape step exits without scraping and the page is rebuilt from Friday's file. A push to `main` still runs the whole workflow.

GitHub documents that `schedule` can start late, and that under high load some queued jobs are dropped, with the start of each hour called out as a busy time ([Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)). This repo already avoids minute 0. That does not keep the runs in the morning. From `gh run list --workflow update-and-deploy.yml` on 25 Nov 2026:

- Scheduled runs on 19, 20, 23 and 24 Nov all started at or after 13:56 UTC, which is 14:56 Europe/Stockholm or later. Several started around 18:00–21:40 UTC.
- The runs that finished before lunch were manual `workflow_dispatch` runs: 25 Nov 07:15 UTC (08:15 Stockholm), 24 Nov 07:19 UTC, 23 Nov 07:20 UTC, 20 Nov 08:06 UTC.

A post that follows "a successful deploy" will therefore usually wake up after lunch, unless the owner dispatched the scrape in the morning or GitHub happened to start a cron on time. The cutoff below is what makes that safe. It is also why this plan does not add a fifth cron for posting: that cron would sit in the same queue.

## Behaviour

A new workflow posts after a successful deploy, and can also be run by hand. For each configured target it sends at most one message per Stockholm date. It never sends yesterday's file, a weekend file, or a message at or after 13:00 Europe/Stockholm.

Guards, in order. The first match wins. A skip logs one line and does not write state, so a later run the same day can still post.

1. **Weekend.** `now` in `Europe/Stockholm` is Saturday or Sunday. Log `Post skip: weekend.`
2. **Holiday.** `utils.holidays.is_holiday(now.date())` is true. That helper is every date in `data/holidays_se.json`, including `kind` of `public`, `bridge` (klämdag), and `eve` (julafton, midsommarafton, nyårsafton). The health report already treats that whole set as a holiday. Log `Post skip: holiday.`
3. **Before this target's post time.** If the target has `post_time` (`HH:MM`, Stockholm), and `now` is earlier, log `Post skip: before post time for <name>.` and try the other targets. If `post_time` is omitted, there is no morning floor. The first successful deploy before the cutoff posts. A 09:00 floor would drop the manual morning dispatches that are the only runs currently finishing before lunch (they land around 08:15). The owner sets `post_time` when he wants to wait for a later scrape.
4. **Cutoff.** Local time `>= 13:00`. Log `Post skip: past the 13:00 Europe/Stockholm cutoff.` Compare the clock when the post job starts, not the cron timestamp and not `workflow_run.created_at`. A run GitHub starts at 16:41 Stockholm skips even though the cron said 07:37.
5. **Not today's menus.** `data/scrape_meta_{weekday}.json` is missing, `day` does not match today's English weekday, or `scraped_at` is missing or its Stockholm calendar date is not today. Log `Post skip: lunch data is for <date or none>, not <today>.` Do not build a message from that file.
6. **Nothing fresh to say.** Meta is for today, but no restaurant passes the per-restaurant filter below. Log `Post skip: no fresh menus for today.`
7. **Already posted.** This target's name is recorded for today's date. Log `Post skip: already posted <name>.`

Per restaurant, include a row only when all of these hold:

- The key is a scraper that `utils.sources` does not mark inactive or link-only.
- The value is an object with a non-empty `items` list.
- `stale` is not true.
- `closed` is not true.
- `fetched_at` parses and its Stockholm date is today. A missing or unparseable `fetched_at` excludes the row. Naive timestamps are treated as Stockholm, same as `main._same_stockholm_date`.

Use dish `name` only, in file order. Drop empty names. Do not include `description`, `price`, `category`, or tags. Show the first two names. If more remain, append `och N till`. Truncate a name at 80 characters and end it with `…`. Cap the list at 12 restaurants, sorted by `display_name` casefold (do not depend on a Swedish locale being installed). If any were cut, add the line `Fler menyer på sidan.` One fresh restaurant is enough to send. There is no coverage percentage.

The message is Swedish, because the dish names are Swedish.

- Header: weekday with an initial capital plus the date, for example `Onsdag 25 november`. Weekday from `SV_DAY_LONG`. Month names live next to the poster (`januari` … `december`). The page only has the short forms in `SV_MONTH`.
- Then one block per restaurant: display name, then the dish lines.
- A link button `Öppna menyn` to `generate_html.SITE`.
- A small footer: `För att stoppa de här inläggen, ta bort webhooken. [Jay's contact]`

`[Jay's contact]` stays as that placeholder. Do not fill it from the README or the privacy page.

Lime `#c8ff36` is used once, and only where the platform has a real colour field. See the payloads.

`dry_run` still evaluates the guards. If a guard fails, it logs the skip and does not print a menu. If the guards pass, it prints the payload and the masked target, and sends nothing. So an afternoon dry run after a late scrape logs the cutoff and does not show dishes. A morning dry run shows the message. A real `workflow_dispatch` uses the same guards as a scheduled run, including the cutoff and "already posted".

## Payloads

### Slack

Incoming webhook: HTTP POST JSON to the webhook URL. Docs: [Sending messages using incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/).

Block Kit has no hex colour. Slack's own migration note says the attachment `color` field is the one that still takes a hex, and that blocks can sit inside an attachment to keep the bar: [Migrating outmoded message compositions to blocks](https://docs.slack.dev/legacy/legacy-messaging/migrating-outmoded-message-compositions-to-blocks/). The colour field accepts a hex such as `#439FE0`: [Legacy secondary message attachments](https://docs.slack.dev/legacy/legacy-messaging/legacy-secondary-message-attachments/).

Use that bar once. Do not set a button `style`, do not add emoji as a colour substitute, and do not repeat the hex.

Top-level `text` is the notification fallback (header plus `Lunch på Lindholmen`). Layout goes in `attachments[0].blocks`. Keep under Slack's block limits: header plain text 150 characters, section mrkdwn 3000, button text 75 ([header](https://docs.slack.dev/reference/block-kit/blocks/header-block/), [section](https://docs.slack.dev/reference/block-kit/blocks/section-block/), [button](https://docs.slack.dev/reference/block-kit/block-elements/button-element/)). One section per restaurant stays far under that with the caps above.

```json
{
  "text": "Onsdag 25 november · Lunch på Lindholmen",
  "attachments": [
    {
      "color": "#c8ff36",
      "blocks": [
        {
          "type": "header",
          "text": {"type": "plain_text", "text": "Onsdag 25 november", "emoji": false}
        },
        {
          "type": "section",
          "text": {"type": "mrkdwn", "text": "*Kooperativet*\nCaesarsallad\nFrench Style Caramelized Onion and Chili Ramen\noch 6 till"}
        },
        {
          "type": "actions",
          "elements": [
            {
              "type": "button",
              "text": {"type": "plain_text", "text": "Öppna menyn", "emoji": false},
              "url": "https://iamjaydesign.com/lindholmen-lunch",
              "action_id": "open_menu"
            }
          ]
        },
        {
          "type": "context",
          "elements": [
            {"type": "mrkdwn", "text": "För att stoppa de här inläggen, ta bort webhooken. [Jay's contact]"}
          ]
        }
      ]
    }
  ]
}
```

The webhook URL is the POST target. It is not a field in this JSON. Incoming webhooks cannot change the channel, username, or icon; those come from the Slack app settings (same doc).

### Teams

Office 365 connectors, including connector incoming webhooks, were retired in May 2026. Microsoft's rollout was 18–22 May 2026: [Retirement of Office 365 connectors within Microsoft Teams](https://devblogs.microsoft.com/microsoft365dev/retirement-of-office-365-connectors-within-microsoft-teams/). The replacement is the Workflows app.

Create the webhook from the channel's **Workflows** menu with the template **Send webhook alerts to a channel**, then POST to the URL the template copies. Steps and the envelope are in [Create an Incoming Webhook](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook). The Adaptive Card shape (`type: message`, `attachments[].contentType` of `application/vnd.microsoft.card.adaptive`, card under `content`) is in [Send Adaptive Cards using an Incoming Webhook](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/connectors-using). Supported actions there are `Action.OpenUrl`, `Action.ShowCard`, and `Action.ToggleVisibility`. `Action.Submit` is not. Message size limit on that page's parent is 28 KB.

Use Adaptive Card **version 1.2**, which is the version in the Learn sample. Do not send a MessageCard. Do not put a hex colour on the card: Teams does not document an arbitrary colour for this webhook, and `#c8ff36` would be invented. Lime stays on the Slack bar only.

The trigger URL is an `https` host ending in `.logic.azure.com`, with the secret in the query string (`sig`). Treat the whole URL as a secret.

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
          {"type": "TextBlock", "text": "Onsdag 25 november", "weight": "Bolder", "size": "Large", "wrap": true},
          {"type": "TextBlock", "text": "Lunch på Lindholmen", "isSubtle": true, "wrap": true, "spacing": "None"},
          {"type": "TextBlock", "text": "Kooperativet", "weight": "Bolder", "wrap": true, "spacing": "Medium"},
          {"type": "TextBlock", "text": "Caesarsallad\n\nFrench Style Caramelized Onion and Chili Ramen\n\noch 6 till", "wrap": true, "spacing": "None"},
          {"type": "TextBlock", "text": "För att stoppa de här inläggen, ta bort webhooken. [Jay's contact]", "wrap": true, "size": "Small", "isSubtle": true, "spacing": "Medium"}
        ],
        "actions": [
          {"type": "Action.OpenUrl", "title": "Öppna menyn", "url": "https://iamjaydesign.com/lindholmen-lunch"}
        ]
      }
    }
  ]
}
```

Workflows posts as the Flow bot. Microsoft's retirement note says a custom name and icon are not available for this path. Do not try to set one.

## Secret

One Actions secret, `CHAT_WEBHOOKS`. A JSON list:

```json
[
  {"name": "jay-slack", "type": "slack", "url": "https://hooks.slack.com/services/REPLACE"},
  {"name": "jay-teams", "type": "teams", "url": "https://REPLACE.logic.azure.com/workflows/REPLACE", "post_time": "09:15"}
]
```

| Field | Rule |
|---|---|
| `name` | Short stable id. Idempotency key, and the `only` input. Unique in the list. |
| `type` | `slack` or `teams`. Anything else: log `Post skip: unknown type for <name>.` and do not send. |
| `url` | HTTPS. Slack host must be exactly `hooks.slack.com`. Teams host must end with `.logic.azure.com`. Anything else: log `Post skip: refused host for <name> https://<host>/***.` and do not send. |
| `post_time` | Optional `HH:MM` on a 24-hour clock, Europe/Stockholm. Bad values are a config error for that target, not a send. |

Pass the secret only as the env var `CHAT_WEBHOOKS`. Never as a workflow `run` argument, never in a commit, never in an issue.

GitHub masks a secret in logs only when the full secret string is printed. A URL pulled out of the JSON is not the full secret, and a Teams URL hides the real secret in `sig`. Mask in code.

- `mask_url` keeps `https://` and the host, replaces the rest with `/***`. No path, no query, no port.
- `dry_run` logs `Post dry-run: <name> <type> https://<host>/***` and then the payload JSON. The payload must not contain a webhook URL.
- On HTTP errors, log the target name and the status code only (`Post failed: jay-teams status=403`). For a timeout or connection error, `status=timeout` or `status=error`. Do not log `str(exception)`, `response.url`, or `response.text`. `requests` puts the full URL, including `sig`, in the exception. Catch it and run a redactor over any string that might be logged: replace the raw secret and each target URL with `***`.
- Tests must show that a URL containing `sig=supersecret` never appears in log records.

Missing or empty secret: log `Post skip: CHAT_WEBHOOKS is not set.` and exit 0. The workflow can land on `main` before the owner adds the secret. Invalid JSON, or a send that was attempted and failed: exit 1. A skip (weekend, holiday, cutoff, stale, already posted) exits 0.

## Idempotency

At most one successful POST per target name per Stockholm date.

State file: `data/chat_post_state.json`, committed to `main` by the post workflow.

```json
{
  "version": 1,
  "days": {
    "2026-11-25": {
      "jay-slack": {"posted_at": "2026-11-25T08:21+01:00", "status": "ok"}
    }
  }
}
```

Record a target only after a 2xx response. Write every success from the run, including when a later target fails, then commit once. Prune dates older than 14 days in that write. Commit message: `Chat post state: 2026-11-25`. Git identity matches the scrape workflow (`GitHub Action`, `action@github.com`). `git add` only this file. Pull with rebase, push, retry up to three times. Never force-push. If rebase fails, abort and exit 1.

A failed POST is not recorded, so a later run the same day retries that target only.

Why a file in the repo, not Actions cache:

- Cache entries that are not accessed for 7 days are removed, and GitHub evicts caches when the repo is over its quota ([Dependency caching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)). An eviction would send a second lunch post.
- `workflow_run` is a low-trust trigger. On the default branch it can restore caches and cannot save them, unless the workflow opts out of that restriction (same doc). The post workflow could not record "already sent".
- The file is visible. The scrape job already commits `data/` to `main`, so a second small data file fits the way this repo deploys.

Known hole: a 2xx followed by a failed state push can send a duplicate on the next run. Webhooks cannot delete the first message. Log `Post failed: <name> posted but state was not saved.` A timeout is treated as a failure and not recorded, so a retry can also duplicate if the server had accepted the request. That is the chosen side: a missed state write beats marking a message sent when it was not.

The post workflow's push would otherwise start `update-and-deploy.yml` again (`on.push` to `main`), which would deploy again and wake the poster again. Stop that loop with `paths-ignore` on the push trigger only:

```yaml
on:
  push:
    branches: [main]
    paths-ignore:
      - data/chat_post_state.json
```

Schedule and `workflow_dispatch` stay as they are. A commit that touches this file and anything else still runs the scrape, which is fine. The post job's concurrency group is separate (`lindholmen-lunch-chat`, `cancel-in-progress: false`) so it queues behind itself and does not cancel a scrape.

Race: the queued run pulls `main` before it reads state, and checks the state again immediately before each POST.

## Workflow

New file `.github/workflows/post-chat.yml`, name `Post lunch to chat`.

Do not add the poster as a job in `update-and-deploy.yml`. A failed job there fails the run that already deployed, and the scrape job would have the webhook secret in its environment. A separate workflow keeps a bad post off the deploy run. `continue-on-error` on a job in the deploy workflow would hide the failure. Here a failed post turns this workflow red and leaves the deploy workflow as it was.

```yaml
on:
  workflow_run:
    workflows: ["Update Lunch Data and Deploy"]
    types: [completed]
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Print the payload and send nothing"
        type: boolean
        default: false
      only:
        description: "Post to this target name only. Empty means every target."
        type: string
        default: ""

permissions:
  contents: write

concurrency:
  group: lindholmen-lunch-chat
  cancel-in-progress: false
```

`workflow_run` runs only from the default branch, and it runs for every conclusion ([Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)). The job condition is:

`github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'`

A coverage failure skips `deploy` and the parent conclusion is `failure`, so this job does not run. A weekend push that still deploys Friday's page does run the poster, which then hits the weekend guard.

`inputs` is not available on `workflow_run`. Pass flags from `github.event.inputs`, which is empty on that event:

- `CHAT_DRY_RUN`: `${{ github.event.inputs.dry_run || 'false' }}`
- `CHAT_ONLY`: `${{ github.event.inputs.only || '' }}`
- `CHAT_WEBHOOKS`: `${{ secrets.CHAT_WEBHOOKS }}`

Checkout `ref: main` with `fetch-depth: 0` and the default token, then `git pull` before reading data. A dispatch from another branch still reads and writes `main`, so a test post counts for the day. The workflow file has to be on the branch you dispatch; the scheduled path starts working only after this file is on `main`.

Steps: setup Python 3.12, `pip install -r requirements.txt`, `python -m utils.chat_post`. Timeout 10 minutes. No Chrome, no pytest, no `git add data/` in bulk.

How late runs are handled, end to end:

1. GitHub may start the 06:07 Stockholm cron at 16:00 or not at all. This poster does not have its own clock. It wakes up when that deploy workflow finishes with `success`.
2. It looks at Stockholm time at that moment. At or after 13:00 it logs the cutoff and exits 0. It does not post "today's lunch" in the evening, and it does not record state, so a morning dispatch later the same calendar day can still post. After midnight the date has changed anyway.
3. If one of the four crons, or a manual dispatch, finishes successfully before 13:00 and the meta file is for today, the first such run posts. The other three see the state file and skip.
4. A dropped cron is not recovered by this poster. The next cron that does start is subject to the same cutoff. Building an external scheduler (business plan BP-0b) is out of scope. See open decisions.

`only` limits the run to the target with that exact `name`. Unknown name: log `Post skip: no target named <only>.` and exit 1. Do not fall through to every target.

HTTP: one POST per target, `Content-Type: application/json`, timeout 15 seconds, no retry. A retry after an ambiguous timeout is a second message.

## Tests

New file `tests/test_chat_post.py` only. Do not edit existing tests, `pytest.ini`, or `tests/conftest.py`. Do not mark the new tests `network` or `browser`. `python -m pytest -q -m "not browser"` must pass, including the new tests. HTTP is `unittest.mock` or `monkeypatch` on the function that calls `requests`. No new dependency. `requests` is already in `requirements.txt`.

Cover at least:

| Case | Expect |
|---|---|
| Slack payload | Header text, restaurant name, two dishes, `och N till`, button URL equals `generate_html.SITE`, a single `#c8ff36`, no webhook URL anywhere in the JSON. |
| Teams payload | `type` is `message`, `contentType` is `application/vnd.microsoft.card.adaptive`, `version` is `1.2`, one `Action.OpenUrl` to `SITE`, no `Action.Submit`, no `#c8ff36`. |
| Truncation | 81-character name ends with `…` at 80. Restaurant 13 becomes `Fler menyer på sidan.` |
| Freshness | `scraped_at` yesterday skips and the poster is not called. `scraped_at` today with `stale: true` omits that restaurant. `fetched_at` yesterday omits it even if meta is today. `closed: true` omits it. Inactive and link-only keys are omitted. Missing `fetched_at` omits it. |
| Calendar | Saturday skips. A date in `data/holidays_se.json` skips, including one `bridge` and one `eve` if those kinds stay in the chosen rule. 12:59 posts. 13:00 skips. `post_time` of `09:15` skips at 09:00 and posts at 09:15. Omitted `post_time` posts at 08:15. |
| Idempotency | Second `run` does not call the poster. A non-2xx does not write state. A 2xx for one target and a failure for the other writes only the success, and the next run posts only the failure. `only` posts one name. |
| Dry run | Guards passing: no HTTP, state file unchanged, log has `https://hooks.slack.com/***` and does not contain `sig=` or the path. Guards failing: skip line, no payload. |
| Secret handling | Invalid JSON exits 1 and the raw string is absent from logs. Empty secret exits 0. Refused host does not call the poster. |
| Redaction | A raised `requests` error whose message contains the Teams URL is logged without `sig`. |

Build the lunch JSON in `tmp_path`. Pass `now` into the pure functions so tests do not depend on the clock. The CLI reads `CHAT_*` env vars; tests that call `main` set those in the test and unset them afterward.

## Owner setup

Do this after the implementation is on `main`. Until then, `workflow_run` will not see the new file.

### Slack webhook

Follow [Sending messages using incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/).

1. Create an app at the Slack API site for his own workspace.
2. Turn on Incoming Webhooks and add one to the test channel.
3. Copy the `https://hooks.slack.com/services/...` URL. Slack shows it once in the app settings. It is a secret.

### Teams webhook

Follow [Create an Incoming Webhook](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook).

1. In his team, open the test channel, **More options (…) → Workflows**.
2. Pick **Send webhook alerts to a channel**. Do not use an Office 365 connector. Those URLs stopped working in May 2026.
3. Save and copy the webhook link. It looks like `https://….logic.azure.com/workflows/…?…&sig=…`. The `sig` value is the secret.
4. Turning that workflow off, or deleting it, stops Teams posts. The same page describes turn off and delete.

If the copied host does not end in `.logic.azure.com`, do not put it in the secret yet. The allowlist would refuse it. Note the host only (not the URL) and widen the allowlist in a follow-up.

### Secret

Repo **Settings → Secrets and variables → Actions → New repository secret**. Name: `CHAT_WEBHOOKS`. Value: the JSON list above, with the real URLs and the names `jay-slack` and `jay-teams`. Leave `post_time` off for the first test so an 08:15 dispatch is allowed. Do not paste the URLs into an issue, a commit, or this plan.

### Dry run, then a real post

The menu file has to be for today, which means a successful `Update Lunch Data and Deploy` earlier the same Stockholm day. The owner already does that with a morning `workflow_dispatch` on that workflow. Then:

1. **Actions → Post lunch to chat → Run workflow.** Set `dry_run` on and leave `only` empty. The log should show both targets masked (`https://hooks.slack.com/***`, `https://….logic.azure.com/***`) and the JSON. Nothing arrives in the channels.
2. Run it again with `dry_run` off and `only` set to `jay-slack`. One Slack message. The log says `Post ok: jay-slack` and does not contain the URL.
3. Run it again with `only` set to `jay-teams`. One Teams card.
4. Run the Slack one again. The log says `Post skip: already posted jay-slack.` and Slack does not get a second message.

All three real runs have to be on a weekday that is not in `data/holidays_se.json`, before 13:00 Stockholm. After 13:00 a real run logs the cutoff and sends nothing. Use the dry run earlier in the day to read the copy.

To stop the posts: delete the Slack webhook, turn off or delete the Teams workflow, and remove the entries from `CHAT_WEBHOOKS` (or delete the secret). The footer tells readers the same thing, with `[Jay's contact]` left for the owner to replace when he wants a name there.

## Implementation steps

One PR, in this order. Each step should leave `pytest -q -m "not browser"` green. No real webhook calls. No secret in the repo.

### 1. Pure functions and payload tests

Add `utils/chat_post.py` with the date guards, menu selection, truncation, `mask_url`, `parse_targets`, and `build_slack_payload` / `build_teams_payload`. No `requests` yet.

Acceptance: the payload, truncation, freshness, and calendar tests pass. Importing the module does not read `CHAT_WEBHOOKS` and does not open a socket.

### 2. State and the runner

In the same module, add load/save/prune of `data/chat_post_state.json` and a `run(now, env, data_dir, state_path, poster)` that applies guards, `only`, dry-run, host checks, and per-target idempotency. `poster` is an injected callable so tests do not touch the network. `main()` reads the env and calls `requests.post` inside a wrapper that redacts errors.

Acceptance: idempotency, dry-run, secret, and redaction tests pass. A 500 from the fake poster leaves state unchanged. Exit codes match the secret section.

### 3. Wire the workflow

Add `.github/workflows/post-chat.yml` as specified. Add `paths-ignore` for `data/chat_post_state.json` on the `push` trigger of `.github/workflows/update-and-deploy.yml` and change nothing else in that file. Add an initial `data/chat_post_state.json` of `{"version": 1, "days": {}}`. Add a short subsection to `README.md` under Schedule: the post workflow name, that it follows a successful deploy, the 13:00 Stockholm cutoff, and that targets live in the `CHAT_WEBHOOKS` secret. No URL examples with real-looking tokens. Point at this plan for setup.

Acceptance: the YAML has `workflow_run` limited to `Update Lunch Data and Deploy`, both inputs, `contents: write`, the chat concurrency group, checkout of `main`, and the secret only in `env`. `paths-ignore` is on `push` only. Existing tests still pass. The README does not contain `hooks.slack.com/services/` plus a path that looks like a real webhook.

### 4. Check the suite

Run `python -m pytest -q -m "not browser"` and `python -m pytest -q tests/test_chat_post.py`. Do not run the browser tests unless Chrome is already there; they are unchanged. Do not dispatch the workflow against real URLs.

## Out of scope

- New or changed scrapers, and any write to `lunch_data_*.json` or `scrape_meta_*.json` from the poster.
- Editing or deleting a message after the gap-fill cron. One post per target per day. Restaurants that appear only in the later run are not added. Set `post_time` if that run is the one that should be sent, and only if a deploy actually finishes between `post_time` and 13:00.
- An external scheduler. The business plan calls the late cron a blocker for a paid 10:45 post (BP-0b). This change does not add one.
- Sponsor line, diet ordering, "Pick for me", Slack OAuth, Teams `Action.Submit`, custom bot name.
- Customer channels. The secret starts with the owner's two test targets. Adding a customer later is another entry in the same JSON.
- Replacing `[Jay's contact]`.

## Open decisions

1. **Holiday set.** The plan uses `is_holiday`, so klämdagar and julafton / midsommarafton / nyårsafton are skipped, not only `kind: public`. Say if posts should run on bridge days.
2. **No default `post_time`.** Omitted means "the first successful deploy before 13:00". Set `09:15` or similar on an entry to wait. With this month's schedule, a time after about 08:30 only fires if something dispatches the scrape again before 13:00.
3. **Late crons.** This design skips them. It does not fix them. If the test week produces no automatic post, that matches the run history above. A trigger outside GitHub Actions is a separate decision.
4. **Swedish only.** Say if the message should be English or both.
5. **Thin mornings.** One fresh restaurant is enough. Say if the post should wait until at least N restaurants are fresh. Waiting only helps if another deploy finishes before 13:00.
6. **Teams host.** The allowlist is `*.logic.azure.com`. If the Workflows URL uses another host, sending is refused until the allowlist is widened. Share the host, not the URL.
7. **Footer contact.** `[Jay's contact]` is deliberate. Replace it in a later change if the footer should name an address already printed on the site.
