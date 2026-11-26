# Daily autopilot playbook (GorkhaPay + News Nepal)

A scheduled Claude session follows this file Monday to Saturday. The weekly run (PLAYBOOK.md) does Sundays and
sends the weekly report. **All hard rules in PLAYBOOK.md apply here too** (no invented figures, general visa/tax
information only with MARA / registered tax agent disclaimers, nothing signed up, paid, posted or emailed in the
owner's name, big decisions go in the weekly report, never weaken a test).

## Repos
- `uniquepoudell/gorkhapay`: remittance comparison and guides (this repo).
- `uniquepoudell/newsnepal`: News Nepal, an auto-updating news site. Other work may be in progress there
  (for example a Nepali visa news section and agent check, and a redesign with images). Read its README and any
  playbook or GUIDE it has before changing it.

## Working safely alongside other work
1. Always start from a fresh `git fetch origin main` and branch `autopilot/daily-<YYYY-MM-DD>` from `origin/main`.
2. List open pull requests in the repo first. Don't edit files that an open PR not made by the autopilot changes,
   unless your change is tiny and clearly needed; prefer a different task that day.
3. If main moved while you worked, rebase your own branch onto the new `origin/main` (or merge it in) and re-run
   the tests. Never force-push to `main` or to anyone else's branch, never rewrite someone else's history,
   never close or edit another PR.
4. Keep each day's change small and in one PR per repo. Merge it yourself only when tests pass and it only adds or
   improves content or small fixes. Anything structural, risky or uncertain: leave the PR open and note it in the log.

## Each day (in order, stop when you've done one meaningful improvement plus any fixes)
1. **Fix broken builds first.** Check the latest Actions runs in both repos and any open "Site health" issue.
   If a build or deploy is red, find the cause and fix it. This beats everything else.
2. **Learn what is working.** Read `autopilot/MONETIZATION.md` first (income options, target search terms, what
   not to promote) and keep it up to date when you learn something new. Use what you can actually see: which pages exist, recent news in the feeds, web
   search for what Nepalis in Australia are asking about this week (remittance, students, visas, tax time,
   jobs), and any analytics or Search Console data the owner has connected. Never claim traffic numbers you
   don't have. Write one or two lines of findings in `autopilot/learnings.md` (newest at the top).
3. **Improve one thing**, alternating between the two sites day by day (even day of month = GorkhaPay,
   odd = News Nepal, unless one has a clearly more valuable task):
   - GorkhaPay: publish the next guide from `autopilot/content-queue.md`, or refresh an old guide's facts
     against the official source, or improve a page's title, description, FAQ or internal links.
   - News Nepal: improve feed choice or keyword filters if irrelevant items show up, add a useful explainer or
     section page with general information, improve page titles and descriptions, or link to GorkhaPay where a
     money-transfer topic genuinely fits.
4. **Log it.** Append one row to `autopilot/log.md` in this repo (date, site, change, PR link, problems).
   No GitHub issue on daily runs unless something is broken that needs the owner; then open or update
   a "Site health" issue assigned to `uniquepoudell`.
