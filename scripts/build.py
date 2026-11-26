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


def page_shell(cfg: dict, title: str, body: str, *, description: str, path: str, depth: int = 0) -> str:
    s, m = cfg["site"], cfg.get("monetization", {})
    up = "../" * depth
    full_title = f"{title} | {s['name']}" if title != s["name"] else f"{s['name']}: {s['tagline']}"
    canonical = s.get("base_url", "").rstrip("/") + "/" + path
    adsense = ""
    if (m.get("adsense_client") or "").strip():
        adsense = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
                   f'{esc(m["adsense_client"].strip())}" crossorigin="anonymous"></script>')
    nav = [("index.html", "Compare"), ("send-money.html", "Send money"), ("guides/index.html", "Guides"),
           ("about.html", "About")]
    current = ' aria-current="page"'
    nav_html = "".join(
        f'<a href="{up}{href}"{current if href == path else ""}>{label}</a>' for href, label in nav)
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
<p>We list licensed agents serving Nepali communities in Australia. Get in touch to be featured.</p></section>
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
This never changes the price you pay. We also show ads and paid listings, which are always labelled.
Rankings are not for sale.</p>
<h2>This is not financial advice</h2>
<p>Information here is general and may be out of date. Check with the provider, your bank, or a licensed adviser
before making decisions.</p>
{contact}</article>"""
    return page_shell(cfg, "About and disclaimer", body, path="about.html",
                      description="About GorkhaPay, how we earn money, and our disclaimer.")


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
    shutil.copytree(ROOT / "static", out / "static")

    pages = {
        "index.html": render_index(cfg, rate),
        "send-money.html": render_send(cfg),
        "about.html": render_about(cfg),
        "guides/index.html": render_guides_index(cfg),
    }
    for g in cfg.get("guides", []):
        pages[f"guides/{g['slug']}.html"] = render_guide(cfg, g)
    for rel, content in pages.items():
        (out / rel).write_text(content, encoding="utf-8")

    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (out / "rates.json").write_text(json.dumps({**rate, "built_at": built}, indent=2), encoding="utf-8")
    b = cfg["site"].get("base_url", "").rstrip("/")
    urls = "".join(f"<url><loc>{esc(b + '/' + rel.replace('index.html', ''))}</loc></url>" for rel in pages)
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
