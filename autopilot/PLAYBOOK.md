# GorkhaPay weekly autopilot playbook

A scheduled Claude session follows this file once a week. Humans can edit it to change what the routine does.

## Goal
Grow useful, trustworthy traffic to GorkhaPay (Nepalis in Australia sending money home, and families in Nepal),
so that affiliate links, the featured-agent spot and ads can earn. Quality and trust come before volume.

## Hard rules (never break these)
1. **No invented numbers.** Never write a fee, exchange rate, margin, visa cost, tax rate, threshold or processing
   time unless you read it this week on the official source and cite it with a link and "checked <date>".
   If you can't reach the source, write the guide without the figure and link the official page instead.
2. **General information only.** Visa, tax and super content explains public rules in general terms and says
   "for advice on your situation, see a registered migration agent (MARA) / registered tax agent". Never tell a
   reader what they personally should apply for or claim.
3. **GorkhaPay never takes, holds or moves money.** Never suggest otherwise. Always discourage hundi.
4. **Nothing in the owner's name.** No signups, payments, ad or affiliate accounts, contracts, emails to third
   parties, or social posts. Draft posts for the owner to paste instead.
5. **No major changes without the owner.** Don't change the business model, remove disclaimers, add paid tools,
   rename the site or change domains. Put these under "Decisions for you" in the report.
6. Keep `python tests/test_build.py` passing. Never skip or weaken a test.

## Each week
1. **Health.** Read the latest "Weekly health check" Actions run and any open "Site health" issue. Run the offline
   tests for this repo (and `uniquepoudell/newsnepal` if reachable). Fix small breakages; report the rest.
2. **Publish one guide.** Take the top unchecked topic in `autopilot/content-queue.md` (or a better one you can
   justify). Write `content/guides/<slug>.html` (same plain HTML style as the others, 400 to 900 words, internal
   links to the comparison page and related guides, official sources linked). Add it to `guides` in `config.json`
   and tick it off in the queue with the date. Add one or two new topic ideas to the bottom of the queue.
3. **One small SEO improvement.** For example: a clearer title or meta description, internal links from older
   guides to the new one, an FAQ section, or structured data in `scripts/build.py`. Small and safe.
4. **Facebook drafts.** Write `marketing/facebook/<YYYY-MM-DD>.md` with 2 or 3 ready-to-paste posts for
   Nepali-Australian community groups (mix English and simple Nepali, helpful first, one link each,
   no hype, no promises of rates). Note which group type each suits (students, families, workers).
5. **Publish.** Work on a branch, open a pull request, make sure tests pass, then merge it to `main` (the owner
   pre-approved publishing routine content). If anything is uncertain, leave the PR open for the owner instead.
6. **Weekly report.** Append a row to `autopilot/log.md`, then open a GitHub issue titled
   `Weekly report <YYYY-MM-DD>` assigned to `uniquepoudell` (so it arrives by email) with:
   - What was published (links to the live pages once deployed)
   - Site health (both sites)
   - Facebook posts ready to paste (link to the file)
   - Decisions for you (only real ones, at most 3)
   Close last week's report issue. Keep it short.

## Waiting on the owner (repeat in the report until done)
- GitHub Pages: Settings > Pages > Source = GitHub Actions, for both repos. Until then the sites aren't live.
- Affiliate signups (Wise, Remitly) and pasting the links into `config.json` `affiliate_url`.
- AdSense, once the site has a custom domain and some content.
- gorkhapay.com.np approval, then set the `CUSTOM_DOMAIN` Actions variable.
