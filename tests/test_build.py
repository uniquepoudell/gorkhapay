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
        assert '"@type": "FAQPage"' in index and "Common questions" in index, "home FAQ missing"
        ld = index.split('<script type="application/ld+json">')[1].split("</script>")[0]
        assert len(json.loads(ld)["mainEntity"]) == len(build.HOME_FAQ)
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
    print("ok")


if __name__ == "__main__":
    main()
