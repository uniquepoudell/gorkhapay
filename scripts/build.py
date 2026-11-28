#!/usr/bin/env python3
"""Build the GorkhaPay site.

GorkhaPay is a guide and comparison site. It never takes, holds or moves money.
It reads config.json and content/guides/*.html, fetches today's mid-market
AUD/NPR rate (falling back to the config value if offline), and writes a static
site to ./public:

  index.html            comparison table and estimate calculator (Australia to Nepal)
  send-money.html       both directions, with links to licensed providers
  guides/index.html     list of how-to guides, plus one page per guide
  about.html            disclaimer, how the site earns money, contact
  products/             sales pages for GorkhaPay's own checklist packs (Stripe for AUD, Nepal QR for NPR)
  rates.json, sitemap.xml, robots.txt, ads.txt (with AdSense), CNAME (with a domain)

Python standard library only.   Usage: python scripts/build.py [--config config.json] [--out public]
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))
USER_AGENT = "Mozilla/5.0 (compatible; GorkhaPayBot/1.0)"

DISCLAIMER = (
    "GorkhaPay is an independent information and comparison site. We are not a remittance provider, "
    "bank or money transfer agent, and we never take, hold or move your money. Fees and rates shown are "
    "estimates and change daily, so always confirm the final amount with the provider before you pay. "
    "Some links are affiliate links, which means we may earn a referral fee at no extra cost to you."
)


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


# --------------------------------------------------------------------------- data

def fetch_rate(cfg: dict) -> dict:
    """Return {"aud_npr": float, "source": str, "as_of": str, "live": bool}."""
    r = cfg.get("rate", {})
    fallback = float(r.get("fallback_aud_npr", 88.0))
    url = r.get("live_url", "")
    if url and not os.environ.get("OFFLINE"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            rate = float(data["rates"]["NPR"])
            if 20 < rate < 500:  # sanity check
                as_of = data.get("time_last_update_utc", "")
                return {"aud_npr": round(rate, 4), "source": "open.er-api.com", "as_of": as_of, "live": True}
        except Exception as exc:  # network down, API changed, etc.
            print(f"warning: live rate unavailable ({exc}); using fallback {fallback}")
    return {"aud_npr": fallback, "source": "fallback value in config.json", "as_of": "", "live": False}


def provider_link(p: dict) -> str:
    """Affiliate link if set, else the official page."""
    return (p.get("affiliate_url") or "").strip() or (p.get("official_url") or "").strip()


def estimate_receive(p: dict, amount_aud: float, rate: float) -> float:
    fee = float(p.get("fee_aud", 0)) + amount_aud * float(p.get("fee_pct", 0)) / 100
    after_fee = max(amount_aud - fee, 0)
    return after_fee * rate * (1 - float(p.get("margin_pct", 0)) / 100)


# --------------------------------------------------------------------------- page parts

def ad_unit(m: dict, slot: str, label: str) -> str:
    client = (m.get("adsense_client") or "").strip()
    if client and slot:
        return (f'<div class="ad"><span class="ad-label">Advertisement</span>'
                f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(client)}" '
                f'data-ad-slot="{esc(slot)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')
    if os.environ.get("SHOW_AD_PLACEHOLDERS"):
        return f'<div class="ad ad-placeholder"><span class="ad-label">Ad slot</span>{esc(label)}</div>'
    return ""


def featured_box(m: dict) -> str:
    f = m.get("featured_agent") or {}
    if f.get("text") and f.get("url"):
        return (f'<aside class="box featured"><span class="ad-label">Featured agent</span>'
                f'<p>{esc(f["text"])}</p><a class="btn" href="{esc(f["url"])}" rel="sponsored noopener" '
                f'target="_blank">Visit</a></aside>')
    if os.environ.get("SHOW_AD_PLACEHOLDERS"):
        return '<aside class="box featured ad-placeholder"><span class="ad-label">Featured agent</span>Paid listing for a local remittance agent</aside>'
    return ""


# --------------------------------------------------------------------------- shop (our own digital products)

def npr_contact(cfg: dict) -> str:
    shop = cfg.get("shop") or {}
    return (shop.get("npr_contact") or cfg["site"].get("contact_email") or "").strip()


def sells_aud(p: dict) -> bool:
    return bool(p.get("price_aud")) and (p.get("stripe_link") or "").strip().startswith("https://")


def sells_npr(cfg: dict, p: dict) -> bool:
    qr = (p.get("npr_qr_image") or "").strip()
    return bool(p.get("price_npr")) and bool(qr) and (ROOT / qr).is_file() and bool(npr_contact(cfg))


def on_sale(cfg: dict, p: dict) -> bool:
    return sells_aud(p) or sells_npr(cfg, p)


def products_on_sale(cfg: dict) -> list[dict]:
    return [p for p in (cfg.get("shop") or {}).get("products", []) if on_sale(cfg, p)]


def money(amount, currency: str) -> str:
    a = float(amount)
    txt = f"{a:,.0f}" if a == int(a) else f"{a:,.2f}"
    return f"A${txt}" if currency == "AUD" else f"NPR {txt}"


def contact_link(c: str) -> str:
    if "@" in c:
        return f'<a href="mailto:{esc(c)}">{esc(c)}</a>'
    if c.startswith("https://"):
        return f'<a href="{esc(c)}" rel="noopener" target="_blank">{esc(c)}</a>'
    return esc(c)


def product_promo(cfg: dict, guide_slug: str, up: str) -> str:
    for p in products_on_sale(cfg):
        if guide_slug in p.get("related_guides", []):
            return (f'<aside class="box promo"><span class="ad-label">From GorkhaPay</span>'
                    f'<h2>{esc(p["title"])}</h2><p>{esc(p["summary"])}</p>'
                    f'<a class="btn" href="{up}products/{esc(p["slug"])}.html">See what\'s inside</a></aside>')
    return ""


def page_shell(cfg: dict, title: str, body: str, *, description: str, path: str, depth: int = 0,
               noindex: bool = False, head_extra: str = "") -> str:
    s, m = cfg["site"], cfg.get("monetization", {})
    up = "../" * depth
    full_title = f"{title} | {s['name']}" if title != s["name"] else f"{s['name']}: {s['tagline']}"
    canonical = s.get("base_url", "").rstrip("/") + "/" + path
    adsense = ""
    if (m.get("adsense_client") or "").strip():
        adsense = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
                   f'{esc(m["adsense_client"].strip())}" crossorigin="anonymous"></script>')
    nav = [("index.html", "Compare"), ("send-money.html", "Send money"), ("guides/index.html", "Guides"), ("https://uniquepoudell.github.io/takehome/", "Pay calculator"),
           ("about.html", "About")]
    if products_on_sale(cfg):
        nav.insert(3, ("products/index.html", "Shop"))
    current = ' aria-current="page"'
    nav_html = "".join(
        f'<a href="{href if href.startswith("http") else up + href}"{current if href == path else ""}>{label}</a>' for href, label in nav)
    contact = ""
    if s.get("contact_email"):
        contact = f' · <a href="mailto:{esc(s["contact_email"])}">{esc(s["contact_email"])}</a>'
    sister = s.get("sister_site") or {}
    sister_html = f' · <a href="{esc(sister["url"])}">{esc(sister["name"])}</a>' if sister.get("url") else ""
    newsletter = ""
    if m.get("newsletter_url"):
        newsletter = f' · <a href="{esc(m["newsletter_url"])}">Weekly rate email</a>'
    year = datetime.now(NEPAL_TZ).year
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{'<meta name="robots" content="noindex">' if noindex else ''}{head_extra}
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="icon" href="{up}static/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}static/style.css">
{adsense}
</head>
<body>
<header class="masthead"><div class="wrap">
  <a class="brand" href="{up}index.html"><img src="{up}static/favicon.svg" alt="" width="32" height="32">{esc(s['name'])}</a>
  <nav>{nav_html}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">
  <p class="disclaimer"><strong>Important:</strong> {esc(DISCLAIMER)}</p>
  <p>&copy; {year} {esc(s['name'])}{contact}{newsletter}{sister_html} · <a href="{up}about.html">Disclaimer</a></p>
</div></footer>
<script src="{up}static/app.js"></script>
</body>
</html>
"""


def provider_rows(providers: list[dict]) -> str:
    rows = []
    for p in providers:
        link = provider_link(p)
        rel = "sponsored noopener" if p.get("affiliate_url") else "noopener"
        name = esc(p["name"])
        cta = (f'<a class="btn" href="{esc(link)}" rel="{rel}" target="_blank">Go to {name}</a>' if link
               else '<span class="muted">Link coming soon</span>')
        payout = "".join(f'<span class="pill">{esc(x)}</span>' for x in p.get("payout", []))
        rows.append(f"""<article class="prov" data-fee="{float(p.get('fee_aud', 0))}" data-fee-pct="{float(p.get('fee_pct', 0))}" data-margin="{float(p.get('margin_pct', 0))}">
  <div class="prov-head"><h3>{name}</h3><div class="receive" aria-live="polite"></div></div>
  <dl>
    <div><dt>Fees</dt><dd>{esc(p.get('fee_text'))}</dd></div>
    <div><dt>Speed</dt><dd>{esc(p.get('speed'))}</dd></div>
    <div><dt>Best for</dt><dd>{esc(p.get('best_for'))}</dd></div>
    <div><dt>Regulation</dt><dd>{esc(p.get('licensed'))}</dd></div>
  </dl>
  <div class="payout">{payout}</div>
  <div class="prov-cta">{cta}</div>
</article>""")
    return "\n".join(rows)


HOME_FAQ = [
    ("What is the cheapest way to send money from Australia to Nepal?",
     "It changes day to day. Compare how many rupees your family will receive, not just the fee, because a zero-fee "
     "service can still cost more through a weaker exchange rate. Use the calculator above, then check the final quote "
     "with the provider before you pay."),
    ("How long does a transfer to Nepal take?",
     "Cash pickup and wallet transfers often arrive the same day. Bank deposits can take one to a few business days. "
     "Each provider shows its expected delivery time before you pay."),
    ("Is hundi legal?",
     "No. Sending money outside licensed channels is illegal in Nepal, and remittance businesses in Australia must be "
     "registered with AUSTRAC. If hundi money goes missing you have no protection."),
    ("Can my family receive money without a bank account?",
     "Yes. Many providers pay out as cash at an agent, where the receiver shows ID and the tracking number, or into a "
     "mobile wallet such as eSewa, Khalti or IME Pay."),
    ("Does GorkhaPay send the money?",
     "No. GorkhaPay is a free comparison and guide site. We never take, hold or move your money. You send directly "
     "with a licensed provider."),
]


def faq_section(items) -> str:
    """Visible FAQ plus FAQPage structured data for search engines."""
    qa = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in items)
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}
    ld = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (f'<section class="faq"><h2>Common questions</h2>{qa}</section>'
            f'<script type="application/ld+json">{ld}</script>')


def render_index(cfg: dict, rate: dict) -> str:
    s, m = cfg["site"], cfg.get("monetization", {})
    au_np = [p for p in cfg["providers"] if "au-np" in p.get("directions", [])]
    as_of = f" (updated {esc(rate['as_of'])})" if rate.get("as_of") else ""
    guides = "".join(f'<li><a href="guides/{esc(g["slug"])}.html">{esc(g["title"])}</a></li>'
                     for g in cfg.get("guides", [])[:4])
    body = f"""
<section class="hero">
  <h1>Send money to Nepal for less</h1>
  <p class="lead">{esc(s['tagline'])}. Free and independent. We never handle your money.</p>
  <form class="calc" id="calc" data-rate="{rate['aud_npr']}" onsubmit="return false">
    <label for="amount">You send (AUD)</label>
    <div class="calc-row"><input id="amount" type="number" min="1" step="1" value="500" inputmode="decimal">
    <span class="rate">Mid-market rate today: <strong>1 AUD = {rate['aud_npr']:.2f} NPR</strong>{as_of}</span></div>
  </form>
</section>
{ad_unit(m, m.get('adsense_slot_top', ''), 'Top banner ad (AdSense or a direct sponsor)')}
<section>
  <h2>Australia to Nepal: compare providers</h2>
  <p class="muted small">Estimated NPR received uses each provider's typical fee and exchange rate margin. Promotions and
  payment methods change the real figure, so check the final quote before you pay. Data last checked {esc(s.get('data_checked'))}.</p>
  <div class="provs" id="provs">
{provider_rows(au_np)}
  </div>
</section>
{featured_box(m)}
<section class="split">
  <div class="box">
    <h2>Sending from Nepal to Australia?</h2>
    <p>Nepal Rastra Bank only lets you send money abroad for approved reasons, such as tuition or medical bills, through a licensed bank.
    <a href="guides/send-money-nepal-to-australia.html">Read how it works</a>.</p>
  </div>
  <div class="box">
    <h2>Popular guides</h2><ul>{guides}</ul>
  </div>
</section>
{ad_unit(m, m.get('adsense_slot_inline', ''), 'Inline ad (AdSense or a direct sponsor)')}
{faq_section(HOME_FAQ)}
"""
    return page_shell(cfg, s["name"], body, description=s["description"], path="index.html")


def render_send(cfg: dict) -> str:
    s, m = cfg["site"], cfg.get("monetization", {})
    au_np = [p for p in cfg["providers"] if "au-np" in p.get("directions", [])]
    np_au = [p for p in cfg["providers"] if "np-au" in p.get("directions", [])]

    def cards(ps):
        out = []
        for p in ps:
            link = provider_link(p)
            rel = "sponsored noopener" if p.get("affiliate_url") else "noopener"
            btn = (f'<a class="btn" href="{esc(link)}" rel="{rel}" target="_blank">Start with {esc(p["name"])}</a>'
                   if link else '<span class="muted">Link coming soon</span>')
            out.append(f'<li class="box"><h3>{esc(p["name"])}</h3><p>{esc(p.get("best_for"))}. {esc(p.get("speed"))}.</p>{btn}</li>')
        return "".join(out)

    body = f"""
<section class="hero"><h1>Send money</h1>
<p class="lead">Pick a licensed provider below. You sign up and pay on their website, and they deliver the money.
GorkhaPay never takes or moves money itself.</p></section>

<section id="au-np"><h2>Australia to Nepal</h2>
<ol class="steps"><li>Choose a provider below (compare costs on the <a href="index.html">home page</a>).</li>
<li>Sign up and verify your ID (passport or Australian driver licence).</li>
<li>Add your family's bank account, wallet (eSewa, Khalti, IME Pay) or cash pickup details.</li>
<li>Pay by bank transfer, PayID or card, and share the tracking number with the receiver.</li></ol>
<ul class="cards">{cards(au_np)}</ul></section>

{ad_unit(m, m.get('adsense_slot_inline', ''), 'Inline ad (AdSense or a direct sponsor)')}

<section id="np-au"><h2>Nepal to Australia</h2>
<p>Under Nepal Rastra Bank rules, individuals can send money abroad only for approved purposes, through a licensed
bank or financial institution, with supporting documents. Common cases are tuition and living costs for students,
medical treatment and visa or migration fees. Ask your bank which documents it needs before you go in.</p>
<ul class="cards">{cards(np_au)}</ul>
<p><a href="guides/send-money-nepal-to-australia.html">Full guide: sending money from Nepal to Australia</a></p></section>

{featured_box(m)}

<section class="box notice"><h2>Never use hundi</h2>
<p>Informal "hundi" transfers are illegal in Nepal and Australia. If the money goes missing you have no protection,
and both sender and receiver can face penalties. <a href="guides/why-avoid-hundi.html">Why it matters</a>.</p></section>

<section class="box"><h2>Are you a licensed remittance agent?</h2>
<p>We list licensed agents serving Nepali communities in Australia. Get in touch to be featured.
We check your AUSTRAC registration before any listing goes live.</p></section>
"""
    return page_shell(cfg, "Send money", body, path="send-money.html",
                      description="Send money between Australia and Nepal safely through licensed providers.")


def load_guide(slug: str) -> str:
    f = ROOT / "content" / "guides" / f"{slug}.html"
    return f.read_text(encoding="utf-8") if f.exists() else "<p>This guide is coming soon.</p>"


def render_guides_index(cfg: dict) -> str:
    items = "".join(f'<li class="box"><h2><a href="{esc(g["slug"])}.html">{esc(g["title"])}</a></h2>'
                    f'<p>{esc(g["summary"])}</p></li>' for g in cfg.get("guides", []))
    body = f'<section class="hero"><h1>Guides</h1><p class="lead">Plain-English help for sending money between Australia and Nepal.</p></section><ul class="cards one">{items}</ul>'
    return page_shell(cfg, "Guides", body, path="guides/index.html", depth=1,
                      description="How-to guides for sending money between Australia and Nepal.")


def render_guide(cfg: dict, g: dict) -> str:
    m = cfg.get("monetization", {})
    body = f"""<article class="guide"><p class="crumbs"><a href="index.html">Guides</a></p>
<h1>{esc(g['title'])}</h1><p class="lead">{esc(g['summary'])}</p>
{load_guide(g['slug'])}
{product_promo(cfg, g['slug'], '../')}
{ad_unit(m, m.get('adsense_slot_inline', ''), 'In-article ad')}
<p class="muted small">Last checked {esc(cfg['site'].get('data_checked'))}. Rules and fees change, so confirm with your provider or bank.</p>
<p><a class="btn" href="../index.html">Compare providers</a></p></article>"""
    return page_shell(cfg, g["title"], body, path=f"guides/{g['slug']}.html", depth=1, description=g["summary"])


def render_about(cfg: dict) -> str:
    s = cfg["site"]
    contact = (f'<p>Contact: <a href="mailto:{esc(s["contact_email"])}">{esc(s["contact_email"])}</a></p>'
               if s.get("contact_email") else "")
    body = f"""<article class="guide"><h1>About GorkhaPay</h1>
<p>GorkhaPay helps Nepalis in Australia and their families at home find safe, low-cost ways to send money.
We compare licensed providers and explain the rules in plain language.</p>
<h2>What we are not</h2>
<p>{esc(DISCLAIMER)}</p>
<p>Any transfer is a contract between you and the provider you choose. Their terms, fees and customer support apply.
Providers serving Australia must be registered with AUSTRAC, and money paid out in Nepal must go through institutions
licensed by Nepal Rastra Bank.</p>
<h2>How we earn money</h2>
<p>Some provider links are affiliate links: if you sign up through them, the provider may pay us a referral fee.
This never changes the price you pay. We also show ads and paid listings, which are always labelled,
and sell our own printable checklists. Everything on the free guides stays free.
Rankings are not for sale.</p>
<h2>This is not financial advice</h2>
<p>Information here is general and may be out of date. Check with the provider, your bank, or a licensed adviser
before making decisions.</p>
{contact}</article>"""
    return page_shell(cfg, "About and disclaimer", body, path="about.html",
                      description="About GorkhaPay, how we earn money, and our disclaimer.")


DEFAULT_NOTICE = ("This is a checklist of general information, not tax, legal or migration advice. Every official service it "
                  "points to (tax file number, tax return, super claim, bond refund) is free from the government. You are paying for "
                  "a clear, printable plan in one place. For advice on your own situation, see a registered tax agent or a registered "
                  "migration agent.")


def render_product(cfg: dict, p: dict) -> str:
    s = cfg["site"]
    includes = "".join(f"<li>{esc(x)}</li>" for x in p.get("includes", []))
    related = {g["slug"]: g for g in cfg.get("guides", [])}
    free = "".join(f'<li><a href="../guides/{esc(slug)}.html">{esc(related[slug]["title"])}</a></li>'
                   for slug in p.get("related_guides", []) if slug in related)
    buy = []
    if sells_aud(p):
        buy.append(f"""<div class="box buy">
  <h3>Pay in Australian dollars</h3>
  <p class="price">{money(p['price_aud'], 'AUD')}</p>
  <p>Card, Apple Pay or Google Pay through Stripe. Your download link appears straight after payment and Stripe emails you a receipt.</p>
  <a class="btn" href="{esc(p['stripe_link'].strip())}" rel="noopener">Buy now</a>
</div>""")
    if sells_npr(cfg, p):
        c = npr_contact(cfg)
        buy.append(f"""<div class="box buy">
  <h3>नेपालबाट रुपैयाँमा तिर्नुहोस् · Pay in Nepal (NPR)</h3>
  <p class="price">{money(p['price_npr'], 'NPR')}</p>
  <img class="qr" src="../{esc(p['npr_qr_image'].strip())}" alt="Nepal payment QR code" width="220" height="220">
  <ol class="small">
    <li>Scan with your bank app, eSewa, Khalti or any Fonepay app and pay {money(p['price_npr'], 'NPR')}.</li>
    <li>Send a screenshot of the payment and your email address to {contact_link(c)}.</li>
    <li>We email you the PDF, usually within one day.</li>
  </ol>
</div>""")
    if not buy:
        buy.append('<div class="box buy"><h3>Coming soon</h3><p>This is not on sale yet.</p></div>')
    sample = (p.get("free_sample_url") or "").strip()
    if sample:
        buy.append(f'<div class="box"><h3>Try it free first</h3><p>{esc(p.get("free_sample_text") or "Try a free sample before you buy.")}</p>'
                   f'<a class="btn secondary" href="{esc(sample)}" rel="noopener">Try the free sample</a></div>')
    jsonld = ""
    if sells_aud(p):
        data = {"@context": "https://schema.org", "@type": "Product", "name": p["title"],
                "description": p["summary"], "brand": {"@type": "Brand", "name": s["name"]},
                "offers": {"@type": "Offer", "price": f"{float(p['price_aud']):.2f}", "priceCurrency": "AUD",
                           "availability": "https://schema.org/InStock", "url": p["stripe_link"].strip()}}
        jsonld = f'\n<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'
    body = f"""<article class="product">
<p class="crumbs"><a href="index.html">Shop</a></p>
<h1>{esc(p['title'])}</h1>
<p class="ne-title">{esc(p.get('title_ne'))}</p>
<p class="lead">{esc(p['summary'])}</p>
<div class="product-grid">
  <div>
    <h2>What's inside</h2>
    <ul class="ticks">{includes}</ul>
    <dl>
      <div><dt>Format</dt><dd>{esc(p.get('format'))}</dd></div>
      <div><dt>Who it's for</dt><dd>{esc(p.get('for_who'))}</dd></div>
      <div><dt>Facts checked</dt><dd>{esc(p.get('facts_checked'))} on official Australian government websites</dd></div>
    </dl>
  </div>
  <div class="buy-col">{''.join(buy)}</div>
</div>
<section class="box notice">
  <h2>Please read before you buy</h2>
  <p>{esc(p.get('notice') or DEFAULT_NOTICE)} Because this is a digital download, please ask us before you buy if
  you're unsure it suits you. Your rights under Australian Consumer Law still apply.</p>
</section>
{f'<section><h2>Free guides on this topic</h2><ul>{free}</ul></section>' if free else ''}
</article>"""
    return page_shell(cfg, p["title"], body, path=f"products/{p['slug']}.html", depth=1,
                      description=p["summary"], noindex=not on_sale(cfg, p), head_extra=jsonld)


def render_shop(cfg: dict) -> str:
    items = []
    for p in (cfg.get("shop") or {}).get("products", []):
        status = "" if on_sale(cfg, p) else ' <span class="pill">Coming soon</span>'
        price = f'<p class="price">{money(p["price_aud"], "AUD")}</p>' if sells_aud(p) else ""
        items.append(f'<li class="box"><h2><a href="{esc(p["slug"])}.html">{esc(p["title"])}</a>{status}</h2>'
                     f'<p class="muted small">{esc(p.get("title_ne"))}</p><p>{esc(p["summary"])}</p>{price}</li>')
    body = ('<section class="hero"><h1>Shop</h1><p class="lead">Printable checklists and practice packs for Nepalis moving to, '
            'living in or leaving Australia, made by GorkhaPay. English with Nepali explanations.</p></section>'
            f'<ul class="cards one">{"".join(items)}</ul>')
    return page_shell(cfg, "Shop", body, path="products/index.html", depth=1, noindex=not products_on_sale(cfg),
                      description="Printable checklists and practice packs for Nepalis moving to, living in or leaving Australia.")


# --------------------------------------------------------------------------- build

def build(cfg_path: Path, out: Path) -> None:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    base = os.environ.get("SITE_BASE_URL", "").strip()
    if base:
        cfg["site"]["base_url"] = base.rstrip("/")
    rate = fetch_rate(cfg)

    if out.exists():
        shutil.rmtree(out)
    (out / "guides").mkdir(parents=True)
    (out / "products").mkdir()
    shutil.copytree(ROOT / "static", out / "static")

    pages = {
        "index.html": render_index(cfg, rate),
        "send-money.html": render_send(cfg),
        "about.html": render_about(cfg),
        "guides/index.html": render_guides_index(cfg),
    }
    for g in cfg.get("guides", []):
        pages[f"guides/{g['slug']}.html"] = render_guide(cfg, g)
    hidden = set()
    products = (cfg.get("shop") or {}).get("products", [])
    if products:
        pages["products/index.html"] = render_shop(cfg)
        if not products_on_sale(cfg):
            hidden.add("products/index.html")
    for p in products:
        rel = f"products/{p['slug']}.html"
        pages[rel] = render_product(cfg, p)
        if not on_sale(cfg, p):
            hidden.add(rel)
        qr = (p.get("npr_qr_image") or "").strip()
        if qr and sells_npr(cfg, p):
            (out / qr).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / qr, out / qr)
    for rel, content in pages.items():
        (out / rel).write_text(content, encoding="utf-8")

    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (out / "rates.json").write_text(json.dumps({**rate, "built_at": built}, indent=2), encoding="utf-8")
    b = cfg["site"].get("base_url", "").rstrip("/")
    urls = "".join(f"<url><loc>{esc(b + '/' + rel.replace('index.html', ''))}</loc></url>" for rel in pages if rel not in hidden)
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {b}/sitemap.xml\n", encoding="utf-8")
    client = (cfg.get("monetization", {}).get("adsense_client") or "").strip()
    if client:
        pub = client.replace("ca-", "")
        (out / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    domain = os.environ.get("CUSTOM_DOMAIN", "").strip()
    if domain:
        (out / "CNAME").write_text(domain + "\n", encoding="utf-8")
    print(f"built {len(pages)} pages into {out} (rate {rate['aud_npr']} from {rate['source']})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config.json"))
    ap.add_argument("--out", default=str(ROOT / "public"))
    a = ap.parse_args()
    build(Path(a.config), Path(a.out))


if __name__ == "__main__":
    main()
