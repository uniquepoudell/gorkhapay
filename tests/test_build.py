#!/usr/bin/env python3
"""Offline build test: python tests/test_build.py"""
import json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ["OFFLINE"] = "1"
import build  # noqa: E402


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "public"
        os.environ["CUSTOM_DOMAIN"] = "gorkhapay.com.np"
        build.build(ROOT / "config.json", out)
        for rel in ["index.html", "send-money.html", "about.html", "guides/index.html", "rates.json",
                    "sitemap.xml", "robots.txt", "CNAME", "static/style.css", "static/app.js"]:
            assert (out / rel).exists(), f"missing {rel}"
        for g in cfg["guides"]:
            assert (ROOT / "content/guides" / f"{g['slug']}.html").exists(), f"guide body missing: {g['slug']}"
            assert (out / "guides" / f"{g['slug']}.html").exists()
        index = (out / "index.html").read_text(encoding="utf-8")
        assert "never take, hold or move your money" in index, "disclaimer missing"
        for p in cfg["providers"]:
            if "au-np" in p["directions"]:
                assert p["name"] in index, f"{p['name']} not on home page"
        rate = json.loads((out / "rates.json").read_text())
        assert rate["live"] is False and rate["aud_npr"] == cfg["rate"]["fallback_aud_npr"]
        # estimate maths
        p = {"fee_aud": 6, "margin_pct": 0}
        assert round(build.estimate_receive(p, 1000, 88.0)) == 87472
        assert round(build.estimate_receive({"fee_aud": 1, "fee_pct": 1, "margin_pct": 0}, 1000, 100.0)) == 98900
        # affiliate link wins over the official link
        assert build.provider_link({"affiliate_url": "https://a", "official_url": "https://o"}) == "https://a"
        assert not (out / "ads.txt").exists()
        # shop: nothing on sale yet, so product pages exist but are hidden from search, menu and sitemap
        for prod in cfg["shop"]["products"]:
            page = (out / "products" / f"{prod['slug']}.html").read_text(encoding="utf-8")
            assert 'name="robots" content="noindex"' in page and "Buy now" not in page
            assert "not tax, legal or migration advice" in page
        assert "products/" not in (out / "sitemap.xml").read_text() and "Checklists" not in index

    # shop: once the owner fills in prices, a Stripe link and a QR, the product goes on sale
    sale = json.loads(json.dumps(cfg))
    sale["site"]["contact_email"] = "hello@example.com"
    prod = sale["shop"]["products"][0]
    prod.update(price_aud=9, stripe_link="https://buy.stripe.com/test_123", price_npr=800,
                npr_qr_image="static/favicon.svg")
    sale["shop"]["products"][1].update(price_aud=9, stripe_link="not-a-link")  # bad link stays off sale
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.json"
        cfg_path.write_text(json.dumps(sale), encoding="utf-8")
        out = Path(tmp) / "public"
        build.build(cfg_path, out)
        page = (out / "products" / f"{prod['slug']}.html").read_text(encoding="utf-8")
        assert "noindex" not in page and 'href="https://buy.stripe.com/test_123"' in page
        assert "A$9" in page and "NPR 800" in page and "hello@example.com" in page
        assert '"priceCurrency": "AUD"' in page and (out / "static/favicon.svg").exists()
        other = (out / "products" / f"{sale['shop']['products'][1]['slug']}.html").read_text(encoding="utf-8")
        assert "noindex" in other and "Buy now" not in other
        assert "Checklists" in (out / "index.html").read_text(encoding="utf-8")
        sitemap = (out / "sitemap.xml").read_text()
        assert prod["slug"] in sitemap and sale["shop"]["products"][1]["slug"] not in sitemap
        related = (out / "guides" / f"{prod['related_guides'][0]}.html").read_text(encoding="utf-8")
        assert prod["title"] in related, "product promo missing on related guide"
    print("ok")


if __name__ == "__main__":
    main()
