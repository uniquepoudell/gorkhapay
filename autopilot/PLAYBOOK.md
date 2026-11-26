# GorkhaPay weekly autopilot playbook

A scheduled Claude session follows this file once a week (Sundays). Daily runs on the other days follow [DAILY.md](DAILY.md) and cover News Nepal too; the weekly report should summarise the daily rows in log.md since last week. Humans can edit it to change what the routine does.

## Goal
Grow useful, trustworthy traffic to GorkhaPay (Nepalis in Australia sending money home, and families in Nepal),
so that affiliate links, the featured-agent spot, ads and GorkhaPay's own checklist packs can earn.
Quality and trust come before volume.

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
7. **Products: never set or change a price, payment link, QR image or contact** in `config.json` `shop`.
   Only the owner does that. Never put a download link, PDF or API key in this repo (it is public).

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
5. **Products (see SELLING.md).** One small step for the checklist packs each week, in this order of priority:
   - If a pack's facts are more than 90 days old (`facts_checked`), recheck every figure in the PDF source
     (`/mnt/project-files/products/src/*.html`, or ask for it in the report if unreachable) against the official
     sources listed at its end. Fix, rebuild the PDF, bump the version and `facts_checked`, and tell the owner to
     re-upload it.
   - Make sure each published guide that fits a pack lists it in that product's `related_guides`.
   - Improve one thing on a sales page: clearer "what's inside", an FAQ, a sample page image, Nepali wording.
     Never add testimonials, sales counts, "limited time" claims or discounts that aren't real.
   - Write one free guide that helps the same reader (the queue has some) and links to the pack.
   - At most once a month, propose one new pack idea under "Decisions for you", with who it's for and why.
   In Facebook drafts, at most one post a week may mention a pack, and only once it is on sale.
6. **Publish.** Work on a branch, open a pull request, make sure tests pass, then merge it to `main` (the owner
   pre-approved publishing routine content). If anything is uncertain, leave the PR open for the owner instead.
7. **Weekly report.** Append a row to `autopilot/log.md`, then open a GitHub issue titled
   `Weekly report <YYYY-MM-DD>` assigned to `uniquepoudell` (so it arrives by email) with:
   - What was published (links to the live pages once deployed)
   - Site health (both sites)
   - Facebook posts ready to paste (link to the file)
   - Decisions for you (only real ones, at most 3)
   Close last week's report issue. Keep it short.

## Waiting on the owner (repeat in the report until done)
- Products: Stripe account and Payment Links, PDFs on Drive, prices in `config.json` `shop`, Nepal merchant QR
  (steps in SELLING.md). Until then the checklist pages stay hidden.
- Google Search Console for both sites, so the runs can see real search queries.
- Affiliate signups (Wise, Remitly) and pasting the links into `config.json` `affiliate_url`.
- AdSense, once the site has a custom domain and some content.
- gorkhapay.com.np approval, then set the `CUSTOM_DOMAIN` Actions variable.
