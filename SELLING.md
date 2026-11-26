# Selling on GorkhaPay: Stripe, Nepal QR, delivery and tax

GorkhaPay sells **its own** products: printable checklists now, and paid "featured" listings and sponsorships later.
GorkhaPay is paid for its own product. It never collects, holds or passes on money for anyone else, because that
would be remittance (AUSTRAC registration in Australia, a Nepal Rastra Bank licence in Nepal).

Facts below were checked on official pages on 26 November 2026. Fees and rules change, so recheck before you rely on them.

## What is built

| Product | Who pays | How they pay | How it's delivered |
| --- | --- | --- | --- |
| Leaving Australia Money Checklist (PDF) | People in Australia | Stripe Payment Link (AUD) | Stripe sends them straight to the download after paying |
| Arriving in Australia Starter Checklist (PDF) | Students and parents in Nepal, or people already in Australia | Nepal QR (NPR) or Stripe (AUD) | NPR: you email the PDF after checking the payment. AUD: as above |
| Featured agent listing (monthly) | Licensed agents and Nepali businesses in Australia | Stripe subscription Payment Link, sent privately after you vet them | You add their box in `config.json` |
| Sponsorship (one-off) | Businesses | Stripe invoice | You add their ad or mention |

The PDFs and their source files are in the project files folder `products/` (not in this public repo, so nobody can
download them for free). Sales pages are at `/products/` on the site. **A product only appears in the menu, the sitemap
and on guide pages once its price and payment details are filled in.** Until then its page is hidden from search.

## Step 1. Create your Stripe account (about 20 minutes)

1. Go to <https://dashboard.stripe.com/register>, sign up with your email, country **Australia**.
2. Business type: **Individual / sole trader**. Use your **ABN** (get a free one at <https://www.abr.gov.au> if you don't have one yet).
3. Describe the business honestly, for example: *"Information website. We sell printable PDF checklists and advertising listings. We do not transfer money for customers."* Website: your GorkhaPay URL.
4. Add your Australian bank account for payouts, and turn on two-factor sign-in.
5. **Stay in test mode (a sandbox) first.** Do every step below in test mode, buy your own product with Stripe's test card `4242 4242 4242 4242`, then repeat in live mode.

Stripe's standard Australian pricing (support.stripe.com, checked 26 Nov 2026): domestic cards **1.65% + A$0.30** per
online payment since 1 October 2026; international cards **3.5% + A$0.30**, dropping to **2.8% + A$0.30** from 1 April 2027.
No monthly fee for Payment Links. Stripe Tax and Billing add their own fees, so check stripe.com/au/pricing before turning them on.

**Never paste API keys into chat, the website, or this repo.** None of the steps below need a key.

## Step 2. Upload the PDFs somewhere private-ish

1. Upload both PDFs to Google Drive. Share each as **Anyone with the link can view**.
2. Copy the two links. These are the download links. Only Stripe and you should ever see them.

(Anyone who gets the link could share it. For a low-price checklist that is an accepted trade-off. When sales
grow, step 7 replaces this with expiring links.)

## Step 3. Make a Payment Link for each checklist (Payments)

In the Stripe Dashboard: **Product catalogue > Add product**.
1. Name: `Leaving Australia Money Checklist`. Price: one-off, AUD, your price. Tick **"Price includes tax"** (Australian prices are shown GST-inclusive, which matters once you register for GST).
2. Product tax code: **General - Electronically Supplied Services** (it is a download).
3. **Payment Links > New**, choose that product.
4. **After payment**: choose **Don't show confirmation page, redirect customers to your website** and paste the Google Drive link from step 2. If Stripe won't accept it, use **Show confirmation page** with a custom message that contains the link.
5. Options: collect email (on by default), turn on **email receipts** in Settings > Customer emails.
6. Create the link (it starts with `https://buy.stripe.com/`). Repeat for the Arriving checklist.

Then in this repo's `config.json`, under `shop.products`, fill in for each product:
```json
"price_aud": 9,
"stripe_link": "https://buy.stripe.com/..."
```
Commit to `main` (or ask Claude). The page goes live on the next build.

## Step 4. Nepal QR for NPR payments

What the providers ask for (checked 26 Nov 2026):
- **Fonepay merchant QR** (fonepay.com): a registered business with a PAN/VAT certificate, the proprietor's citizenship,
  a photo, and an account at a Fonepay partner bank. Usually free, 2 to 5 working days.
- **eSewa business QR** (blog.esewa.com.np): for a sole proprietor taking under NPR 1 lakh a year, eSewa lists
  a ward-office or local-authority letter confirming the business, address proof, citizenship and a **personal PAN**,
  plus business registration if you have one. Above NPR 1 lakh it wants full business registration, PAN/VAT and tax clearance.

Simplest path: ask a family member in Nepal (or yourself on your next visit) to apply through your Nepali bank's
merchant QR form or eSewa business QR with your personal PAN. Avoid using a personal "receive money" QR for sales:
merchant QR is the proper route for business income and keeps records clean.

Then:
1. Save the QR image as `static/qr/npr-qr.png` in this repo.
2. In `config.json`: set `price_npr` and `npr_qr_image: "static/qr/npr-qr.png"` on each product, and set
   `shop.npr_contact` to the email (or a `https://wa.me/...` WhatsApp link) where buyers send their payment screenshot.
3. When a screenshot arrives, check the money is in your account, then email the Drive link. Keep a simple
   spreadsheet: date, buyer, amount, reference.

## Step 5. Featured listings as a subscription (Billing)

1. **Product catalogue > Add product**: `Featured agent listing`, recurring **monthly** price in AUD, "Price includes tax" ticked, and the closest advertising-services tax code.
2. **Payment Links > New** with that price. Don't publish it. Send it privately to each business **after** you check them:
   remittance businesses must be on AUSTRAC's remittance sector register; migration agents must be registered (OMARA/MARA).
3. **Settings > Billing > Customer portal**: turn it on, allow cancelling and updating cards, and copy the portal login link. Send it to subscribers so they can manage or cancel themselves.
4. Settings > Billing > Subscriptions and emails: turn on emails for failed payments and card updates (Stripe retries failed payments automatically).
5. When someone subscribes, add their box under `monetization.featured_agent` in `config.json`. If they cancel, remove it.

Rankings are never for sale: the featured box is always labelled and sits outside the comparison table.

## Step 6. Sponsors (Invoicing)

**Invoices > Create invoice**: add the customer, a line item (for example "Sponsored guide, December 2026"), due in 14 days,
then **Send**. Stripe emails a hosted invoice page they can pay by card or bank transfer, and sends reminders.
No code needed.

## Step 7. Later, when sales are regular: a small webhook

Stripe recommends webhooks for every payment integration, and they are required to automate subscriptions.
While sales are a handful a week, Stripe's emails to you plus the Dashboard are enough. When volume grows, add a
free **Cloudflare Worker** (your domain is already on Cloudflare) that:
- listens for `checkout.session.completed` and `checkout.session.async_payment_succeeded` and emails an
  expiring download link (replaces the shared Drive link);
- listens for `customer.subscription.deleted` and `invoice.payment_failed` to flag listings to remove;
- uses a **restricted API key** (`rk_...`, read-only on Checkout Sessions and Subscriptions) and the webhook
  signing secret, both stored as Cloudflare Worker secrets that **you** add. Never in this repo.
Ask Claude to build it when you're ready.

## Stripe Tax and GST

- The ATO says you **must register for GST when your GST turnover reaches A$75,000** (this month plus the previous 11,
  or projected for the next 12), within 21 days. Below that it's optional, and if you register you generally stay
  registered for at least 12 months. You need an ABN first. Source: ato.gov.au "Registering for GST", checked 26 Nov 2026.
- **Until you register for GST, don't charge GST and don't turn on automatic tax.** Stripe Tax only collects tax where
  you have an active registration, so turning it on without one collects nothing while looking switched on.
- Do set it up now so you're ready: **Tax > Settings**: head office address in Australia, default tax behaviour
  **inclusive**, product tax codes as above. When you register for GST, add an **Australia registration** in
  Stripe Tax, then turn on automatic tax for the Payment Links, subscriptions and invoices. Your existing prices stay
  the same and GST becomes 1/11 of them.
- Income tax: what you earn from Stripe **and** from the Nepal QR is business income. If you're an Australian tax
  resident you generally declare worldwide income, so keep records of NPR sales too. Ask a registered tax agent how
  to report it. This is general information, not tax advice.

## Why not Stripe Connect

Connect is for platforms that take payments **for other businesses** (marketplaces, booking platforms).
GorkhaPay doesn't do that and shouldn't: collecting money on behalf of agents, especially remittance agents, risks
looking like a money service, which Stripe restricts and Australian law regulates. Featured listings are paid to
GorkhaPay as GorkhaPay's own advertising product, so plain Payments + Billing covers them. Leave Connect off.

## Stripe planner (optional)

The Stripe CLI and Stripe's agent plugin are installed in Claude's cloud workspace, and Stripe's servers are now
allowed there. Stripe's own planner (`stripe tools plan`) needs a Stripe test key to run. This guide already follows
Stripe's published best practices. If you want the planner's output too: create a **restricted test key** in the
Dashboard and add it as a secret in your Claude cloud environment settings (never in chat). Then ask Claude to run it.

## Checklist for you

- [ ] Stripe account in test mode, ABN, bank account, 2FA
- [ ] PDFs uploaded to Drive (links kept private)
- [ ] Two products + Payment Links (redirect to the download), tested with 4242 card
- [ ] Prices and links in `config.json`, then live mode
- [ ] Merchant QR from your bank or eSewa, saved to `static/qr/npr-qr.png`, contact set
- [ ] Customer Portal on, featured listing product ready (send privately after vetting)
- [ ] Tax settings: head office, inclusive pricing, tax codes (automatic tax stays off until GST registration)
- [ ] Ask a Nepali speaker to proofread the Nepali summaries in the PDFs
