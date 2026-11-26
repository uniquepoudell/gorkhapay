# GorkhaPay: setup, domains and income guide

The site is built. These are the steps only you can do, in order.

## Part 1. Put it online (about 10 minutes)

### Step 1. Create the repository
1. Go to <https://github.com/new> signed in as **uniquepoudell**.
2. Name: `gorkhapay`. Choose **Public**. Leave "Add a README" unticked. Click **Create repository**.
3. Tell Claude in the project thread. Claude will push the code.

### Step 2. Turn on GitHub Pages
1. In the repo: **Settings > Pages > Build and deployment > Source**: choose **GitHub Actions**.
2. **Actions** tab > **Build and publish** > **Run workflow**.
3. About a minute later the site is at **https://uniquepoudell.github.io/gorkhapay/**. It rebuilds every day with a fresh exchange rate.

### Step 3. Connect gorkhapay.com.np (once it is approved)
Your DNS is already on Cloudflare. In Cloudflare, open **gorkhapay.com.np > DNS > Records** and add:

| Type | Name | Content | Proxy status |
|---|---|---|---|
| A | `@` | `185.199.108.153` | DNS only (grey cloud) |
| A | `@` | `185.199.109.153` | DNS only |
| A | `@` | `185.199.110.153` | DNS only |
| A | `@` | `185.199.111.153` | DNS only |
| CNAME | `www` | `uniquepoudell.github.io` | DNS only |

Keep the cloud **grey** until GitHub has issued the HTTPS certificate (step 5), otherwise it can fail.

4. In the repo: **Settings > Secrets and variables > Actions > Variables > New variable**: name `CUSTOM_DOMAIN`, value `gorkhapay.com.np`.
5. **Settings > Pages > Custom domain**: enter `gorkhapay.com.np`, save. When the check passes, tick **Enforce HTTPS**.
6. Optional, afterwards: you can switch the records to orange (proxied) and set Cloudflare **SSL/TLS** to **Full**.

### Step 4. Point gorkhapay.com and gorkhapay.com.au at it
GitHub Pages serves one domain per site, so make the others forward to the main one. For each domain in Cloudflare:
1. Add the domain to Cloudflare (if bought elsewhere, change its name servers to the two Cloudflare gives you).
2. Add an **A** record `@` → `192.0.2.1` and a **CNAME** `www` → `@`, both **Proxied** (orange cloud). The address is a placeholder; Cloudflare answers before it.
3. **Rules > Redirect Rules > Create rule** (or "Redirect from root to www" template): when *All incoming requests*,
   redirect to **Dynamic** `concat("https://gorkhapay.com.np", http.request.uri.path)`, status **301**, keep query string.

If you later prefer `gorkhapay.com.au` as the main address for Australian readers (it can rank better in Google Australia),
just swap: set `CUSTOM_DOMAIN` to that and point `.com.np` at it instead.

### Step 5. Tell Google
Add the domain in [Google Search Console](https://search.google.com/search-console) and submit `https://gorkhapay.com.np/sitemap.xml`.

## Part 2. Affiliate signups (this is where the first money comes from)

Apply to each program, then paste your personal link into `affiliate_url` for that provider in `config.json`
(edit on github.com with the pencil icon). Links switch over automatically; empty ones fall back to the official site.

| Provider | Where to apply | Notes |
|---|---|---|
| Wise | Wise Partner / affiliate program (search "Wise affiliate program") | Usually approved for content sites. Pays per new customer. |
| Remitly | Remitly affiliate program (via its affiliate network, search "Remitly affiliate") | Pays per first transfer. Often wants some traffic first. |
| Western Union | Western Union affiliate program (search "Western Union affiliate Australia") | Availability varies by country. |
| IME, Prabhu, City Express | Email their Australian offices and ask for a referral or agent deal | Smaller firms often agree to a per-transfer referral fee or a paid listing. |

When you apply, describe the site honestly: "an independent comparison and guide site for the Nepali community in Australia".
Apply after the site is live on your domain, because most programs check it.

Also fill in `site.contact_email` (a separate address like hello@gorkhapay.com.np is fine), and check every provider's
fees against their live quote, then update `data_checked`. Add official links for IME and Prabhu in `official_url`
once you confirm their Australian sites.

## Part 3. Other income (once readers arrive)

- **Ads:** apply to Google AdSense after you have the domain and some guides. Put the ids in `monetization.adsense_*`. The build adds `ads.txt`.
- **Featured agent:** sell the "Featured agent" spot to a local licensed remittance agent, for example A$50 to 150 a month. Put their text and link in `monetization.featured_agent`.
- **Weekly rate email:** start a free newsletter on Beehiiv or Substack and set `monetization.newsletter_url`.
- **Becoming an agent yourself:** IME, Prabhu and City Express recruit agents in Australia. They hold the licences and you earn per transfer. You would still need to meet AUSTRAC rules as their agent, so ask them what's required.

## Part 4. Getting readers
- Share the guides in Nepali-Australian Facebook groups, student associations (NRNA Australia, university Nepali societies) and Telegram groups.
- Link GorkhaPay from News Nepal, and News Nepal from GorkhaPay (already done in the footer).
- Post a short "this week's AUD to NPR rate" update every week; that's what people search for.
- Translate the top guides into Nepali. Claude can add a Nepali version when you want it.

## Stay legal
GorkhaPay must only inform and refer. Don't accept money from users, hold funds, or arrange transfers for people, even for
friends, because that is remittance and needs AUSTRAC registration and an NRB licence. Never promote hundi.
Label affiliate links and paid listings (the site already does).
